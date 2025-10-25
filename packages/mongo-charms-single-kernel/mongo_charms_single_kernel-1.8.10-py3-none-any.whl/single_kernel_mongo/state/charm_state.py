#!/usr/bin/env python3
# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""The general charm state."""

from __future__ import annotations

import json
import logging
from ipaddress import IPv4Address, IPv6Address
from typing import TYPE_CHECKING, TypeVar
from urllib.parse import quote

from data_platform_helpers.advanced_statuses.protocol import StatusesState, StatusesStateProtocol
from ops import ModelError, Object, Relation, SecretNotFoundError, Unit
from pymongo.errors import (
    AutoReconnect,
    NotPrimaryError,
    OperationFailure,
    ServerSelectionTimeoutError,
)

from single_kernel_mongo.config.literals import (
    SECRETS_UNIT,
    CharmKind,
    MongoPorts,
    Scope,
    Substrates,
)
from single_kernel_mongo.config.models import CharmSpec
from single_kernel_mongo.config.relations import (
    ExternalRequirerRelations,
    PeerRelationNames,
    RelationNames,
)
from single_kernel_mongo.core.secrets import SecretCache
from single_kernel_mongo.core.structured_config import (
    ExposeExternal,
    MongoConfigModel,
    MongoDBRoles,
)
from single_kernel_mongo.core.workload import MongoPaths
from single_kernel_mongo.exceptions import MissingCredentialsError
from single_kernel_mongo.lib.charms.data_platform_libs.v0.data_interfaces import (
    DatabaseProviderData,
    DatabaseRequirerData,
    DataPeerData,
    DataPeerOtherUnitData,
    DataPeerUnitData,
)
from single_kernel_mongo.managers.k8s import K8sManager
from single_kernel_mongo.state.app_peer_state import (
    AppPeerDataKeys,
    AppPeerReplicaSet,
)
from single_kernel_mongo.state.cluster_state import ClusterState, ClusterStateKeys
from single_kernel_mongo.state.config_server_state import (
    SECRETS_FIELDS,
    AppShardingComponentKeys,
    AppShardingComponentState,
    UnitShardingComponentState,
)
from single_kernel_mongo.state.ldap_state import LdapState
from single_kernel_mongo.state.tls_state import TLSState
from single_kernel_mongo.state.unit_peer_state import (
    UnitPeerReplicaSet,
)
from single_kernel_mongo.utils.helpers import (
    generate_relation_departed_key,
)
from single_kernel_mongo.utils.mongo_config import MongoConfiguration
from single_kernel_mongo.utils.mongo_connection import MongoConnection
from single_kernel_mongo.utils.mongo_error_codes import MongoErrorCodes
from single_kernel_mongo.utils.mongodb_users import (
    CharmedBackupUser,
    CharmedLogRotateUser,
    CharmedOperatorUser,
    CharmedStatsUser,
    InternalUsers,
    MongoDBUser,
    RoleNames,
)

if TYPE_CHECKING:
    from single_kernel_mongo.abstract_charm import AbstractMongoCharm
    from single_kernel_mongo.core.operator import OperatorProtocol

    T = TypeVar("T", bound=MongoConfigModel)
    U = TypeVar("U", bound=OperatorProtocol)

logger = logging.getLogger()


class CharmState(Object, StatusesStateProtocol):
    """The Charm State object.

    This object represents the charm state, including the different relations
    the charm is bound to, and the model information.
    It is parametrized by the substrate and the CharmKind.

    The substrate will allow to compute the right hosts.
    The CharmSpec allows selection of the right peer relation name and also the
    generation of the correct mongo uri.
    The charm is passed as an argument to build the secret storage, and provide
    an access to the charm configuration.
    """

    def __init__(
        self,
        charm: AbstractMongoCharm[T, U],
        substrate: Substrates,
        charm_role: CharmSpec,
    ):
        super().__init__(parent=charm, key="charm_state")
        self.charm_role = charm_role
        self.charm = charm
        self.substrate: Substrates = substrate
        self.secrets = SecretCache(charm)
        self.peer_relation_name = charm.peer_rel_name.value
        self.ldap_peer_relation_name = PeerRelationNames.LDAP_PEERS.value
        self.statuses_relation_name = PeerRelationNames.STATUS_PEERS.value

        self.statuses = StatusesState(self, self.statuses_relation_name)

        self.peer_app_interface = DataPeerData(
            self.model,
            relation_name=self.peer_relation_name,
        )
        self.peer_unit_interface = DataPeerUnitData(
            self.model,
            relation_name=self.peer_relation_name,
            additional_secret_fields=SECRETS_UNIT,
        )
        self.ldap_peer_interface = DataPeerData(
            self.model,
            self.ldap_peer_relation_name,
        )

        self.paths = MongoPaths(self.charm_role)

        self.k8s_manager = K8sManager(
            pod_name=self.pod_name,
            namespace=self.model.unit._backend.model_name,
        )

    @property
    def config(self) -> MongoConfigModel:
        """Returns the charm config."""
        return self.charm.parsed_config

    @property
    def pod_name(self) -> str:
        """K8S only: The pod name."""
        return self.model.unit.name.replace("/", "-")

    # BEGIN: Relations
    @property
    def peer_relation(self) -> Relation | None:
        """The replica set peer relation."""
        return self.model.get_relation(self.peer_relation_name)

    @property
    def ldap_peer_relation(self) -> Relation | None:
        """The LDAP peer relation."""
        return self.model.get_relation(self.ldap_peer_relation_name)

    @property
    def peers_units(self) -> set[Unit]:
        """Get peers units in a safe way."""
        if not self.peer_relation:
            return set()
        return self.peer_relation.units

    @property
    def reverse_order_peer_units(self) -> list[Unit]:
        """Units sorted in reverse order."""
        return sorted(
            self.peers_units, key=lambda unit: int(unit.name.split("/")[-1]), reverse=True
        )

    @property
    def client_relations(self) -> set[Relation]:
        """The set of client relations.

        Client relations exist on two separate interfaces, one for sharding,
        which is exposed for mongos charms, and one for replication which is
        exposed for mongodb charms.
        """
        if self.charm_role.name == CharmKind.MONGOS:
            return set(self.model.relations[RelationNames.MONGOS_PROXY.value])
        return set(self.model.relations[RelationNames.DATABASE.value])

    @property
    def mongos_cluster_relation(self) -> Relation | None:
        """The Mongos side of the cluster relation."""
        return self.model.get_relation(RelationNames.CLUSTER.value)

    @property
    def cluster_relations(self) -> set[Relation]:
        """The Config Server side of the cluster relation."""
        return set(self.model.relations[RelationNames.CLUSTER.value])

    @property
    def shard_relation(self) -> Relation | None:
        """The set of shard relations."""
        return self.model.get_relation(RelationNames.SHARDING.value)

    @property
    def config_server_relation(self) -> set[Relation]:
        """The config-server relation if it exists."""
        return set(self.model.relations[RelationNames.CONFIG_SERVER.value])

    @property
    def client_tls_relation(self) -> Relation | None:
        """The client TLS relation if it exists."""
        return self.model.get_relation(ExternalRequirerRelations.CLIENT_TLS.value)

    @property
    def peer_tls_relation(self) -> Relation | None:
        """The peer TLS relation if it exists."""
        return self.model.get_relation(ExternalRequirerRelations.PEER_TLS.value)

    @property
    def s3_relation(self) -> Relation | None:
        """The S3 relation if it exists."""
        return self.model.get_relation(ExternalRequirerRelations.S3_CREDENTIALS.value)

    @property
    def ldap_relation(self) -> Relation | None:
        """The LDAP relation if it exists."""
        return self.model.get_relation(ExternalRequirerRelations.LDAP.value)

    @property
    def ldap_cert_relation(self) -> Relation | None:
        """The certificate transfer relation for LDAP if it exists."""
        return self.model.get_relation(ExternalRequirerRelations.LDAP_CERT.value)

    # END: Relations

    # BEGIN: State Accessors

    @property
    def app_peer_data(self) -> AppPeerReplicaSet:
        """The app peer relation data."""
        return AppPeerReplicaSet(
            relation=self.peer_relation,
            data_interface=self.peer_app_interface,
            component=self.model.app,
            substrate=self.substrate,
            model=self.model,
        )

    @property
    def unit_peer_data(self) -> UnitPeerReplicaSet:
        """This unit peer relation data."""
        return UnitPeerReplicaSet(
            relation=self.peer_relation,
            data_interface=self.peer_unit_interface,
            component=self.model.unit,
            substrate=self.substrate,
            k8s_manager=self.k8s_manager,
            bind_address=str(self.bind_address),
        )

    def unit_peer_data_for(self, unit: Unit, relation: Relation) -> UnitPeerReplicaSet:
        """The provided unit peer relation data."""
        data_interface = DataPeerOtherUnitData(
            model=self.model,
            unit=unit,
            relation_name=relation.name,
        )
        return UnitPeerReplicaSet(
            relation=relation,
            data_interface=data_interface,
            component=unit,
            substrate=self.substrate,
            k8s_manager=self.k8s_manager,
        )

    @property
    def units(self) -> set[UnitPeerReplicaSet]:
        """Grabs all units in the current peer relation, including this unit.

        Returns:
            Set of UnitPeerReplicaSet in the current peer relation, including this unit.
        """
        _units = set()
        for unit, data_interface in self.peer_units_data_interfaces.items():
            _units.add(
                UnitPeerReplicaSet(
                    relation=self.peer_relation,
                    data_interface=data_interface,
                    component=unit,
                    substrate=self.substrate,
                    k8s_manager=self.k8s_manager,
                )
            )
        _units.add(self.unit_peer_data)

        return _units

    def peer_unit_data(self, unit: Unit) -> UnitPeerReplicaSet:
        """Returns the peer data for a peer unit."""
        if unit.name == self.model.unit.name:
            return self.unit_peer_data
        return UnitPeerReplicaSet(
            relation=self.peer_relation,
            data_interface=self.peer_units_data_interfaces[unit],
            component=unit,
            substrate=self.substrate,
            k8s_manager=self.k8s_manager,
        )

    @property
    def cluster_provider_data_interface(self) -> DatabaseProviderData:
        """The Requirer Data interface for the cluster relation (config-server side)."""
        return DatabaseProviderData(
            self.model,
            RelationNames.CLUSTER.value,
        )

    @property
    def cluster_requirer_data_interface(self) -> DatabaseRequirerData:
        """The Requirer Data interface for the cluster relation (mongos side)."""
        return DatabaseRequirerData(
            self.model,
            RelationNames.CLUSTER.value,
            database_name=self.app_peer_data.database,
            extra_user_roles=",".join(sorted(self.app_peer_data.extra_user_roles)),
            additional_secret_fields=[
                ClusterStateKeys.KEYFILE.value,
                ClusterStateKeys.CONFIG_SERVER_DB.value,
                ClusterStateKeys.INT_CA_SECRET.value,
            ],
        )

    @property
    def cluster(self) -> ClusterState:
        """The cluster state of the current running App."""
        return ClusterState(
            relation=self.mongos_cluster_relation,
            data_interface=self.cluster_requirer_data_interface,
            component=self.model.app,
        )

    @property
    def tls(self) -> TLSState:
        """A view of the TLS status from the local unit databag."""
        return TLSState(
            peer_relation=self.peer_tls_relation,
            client_relation=self.client_tls_relation,
            secrets=self.secrets,
        )

    @property
    def ldap(self) -> LdapState:
        """A view of the TLS status from the local unit databag."""
        return LdapState(
            self.charm,
            relation=self.ldap_peer_relation,
            data_interface=self.ldap_peer_interface,
            component=self.model.app,
        )

    # END: State Accessors

    # BEGIN: Helpers
    def is_role(self, role: MongoDBRoles) -> bool:
        """Is the charm in the correct role?"""
        return self.app_peer_data.role == role

    @property
    def is_sharding_component(self) -> bool:
        """Is the shard a sharding component?"""
        return self.is_role(MongoDBRoles.SHARD) or self.is_role(MongoDBRoles.CONFIG_SERVER)

    @property
    def has_sharding_integration(self) -> bool:
        """Has the sharding component a sharded deployment integration?"""
        return (self.shard_relation is not None) or bool(self.config_server_relation)

    @property
    def db_initialised(self) -> bool:
        """Is the DB initialised?"""
        return self.app_peer_data.db_initialised

    @db_initialised.setter
    def db_initialised(self, other: bool):
        self.app_peer_data.db_initialised = other

    @property
    def bind_address(self) -> IPv4Address | IPv6Address | str:
        """The network binding address from the peer relation."""
        bind_address = None
        if self.peer_relation:
            if binding := self.model.get_binding(self.peer_relation):
                bind_address = binding.network.bind_address

        return bind_address or ""

    def get_user_password(self, user: MongoDBUser) -> str:
        """Returns the user password for a system user."""
        return self.secrets.get_for_key(Scope.APP, user.password_key_name) or ""

    def set_user_password(self, user: MongoDBUser, content: str) -> str:
        """Sets the user password for a system user."""
        return self.secrets.set(user.password_key_name, content, Scope.APP).label

    def internal_user_passwords_are_initialized(self) -> bool:
        """Returns true if all the charmed users have a password."""
        return all(self.get_user_password(user) for user in InternalUsers)

    def get_user_credentials(self) -> tuple[str | None, str | None]:
        """Retrieve the user credentials."""
        return (
            self.secrets.get_for_key(Scope.APP, key=AppPeerDataKeys.USERNAME.value),
            self.secrets.get_for_key(Scope.APP, key=AppPeerDataKeys.PASSWORD.value),
        )

    def set_keyfile(self, keyfile_content: str) -> str:
        """Sets the keyfile content in the secret."""
        return self.secrets.set(AppPeerDataKeys.KEYFILE.value, keyfile_content, Scope.APP).label

    def get_keyfile(self) -> str | None:
        """Gets the keyfile content from the secret."""
        return self.secrets.get_for_key(Scope.APP, AppPeerDataKeys.KEYFILE.value)

    @property
    def planned_units(self) -> int:
        """Return the planned units for the charm."""
        return self.model.app.planned_units()

    @property
    def peer_units_data_interfaces(self) -> dict[Unit, DataPeerOtherUnitData]:
        """The cluster peer relation."""
        return {
            unit: DataPeerOtherUnitData(
                model=self.model, unit=unit, relation_name=self.peer_relation_name
            )
            for unit in self.peers_units
        }

    @property
    def formatted_socket_path(self) -> str:
        """URL encoded socket path.

        Explanation: On Mongos VM which is a subordinate charm, we'd rather
        share the connection with a socket in order to improve latency.
        """
        return quote(f"{self.paths.socket_path}", safe="")

    @property
    def app_hosts(self) -> set[str]:
        """Retrieve the hosts associated with MongoDB application."""
        if self.substrate == Substrates.K8S and self.charm_role.name == CharmKind.MONGOS:
            if self.config.expose_external == ExposeExternal.NODEPORT:
                return {f"{unit.node_ip}" for unit in self.units}
        return self.internal_hosts

    @property
    def unit_host(self) -> str | None:
        """The Unit host for mongos external clients."""
        assert self.charm_role.name == CharmKind.MONGOS
        if self.substrate == Substrates.K8S:
            return f"{self.unit_peer_data.node_ip}"
        return None

    @property
    def is_external_client(self) -> bool:
        """The universal external connectivity for mongos charms."""
        if self.charm_role.name == CharmKind.MONGOD:
            return False
        if self.substrate == Substrates.VM:
            return self.app_peer_data.external_connectivity
        return self.config.expose_external == ExposeExternal.NODEPORT

    @property
    def internal_hosts(self) -> set[str]:
        """Internal hosts for internal access."""
        if (
            self.substrate == Substrates.VM
            and self.charm_role.name == CharmKind.MONGOS
            and not self.app_peer_data.external_connectivity
        ):
            return {self.formatted_socket_path}
        return {unit.internal_address for unit in self.units}

    @property
    def host_port(self) -> int:
        """Retrieve the port associated with MongoDB application."""
        if self.is_role(MongoDBRoles.MONGOS):
            if self.is_external_client and self.substrate == Substrates.K8S:
                return self.unit_peer_data.node_port
            return MongoPorts.MONGOS_PORT.value
        return MongoPorts.MONGODB_PORT.value

    @property
    def config_server_data_interface(self) -> DatabaseProviderData:
        """The config server database interface."""
        return DatabaseProviderData(self.model, RelationNames.CONFIG_SERVER.value)

    @property
    def shard_state_interface(self) -> DatabaseRequirerData:
        """The shard database interface."""
        return DatabaseRequirerData(
            self.model,
            relation_name=RelationNames.SHARDING.value,
            additional_secret_fields=SECRETS_FIELDS,
            database_name="unused",  # Needed for relation events
        )

    @property
    def shard_state(self) -> AppShardingComponentState:
        """The app shard state."""
        return AppShardingComponentState(
            relation=self.shard_relation,
            data_interface=self.shard_state_interface,
            component=self.model.app,
        )

    @property
    def unit_shard_state(self) -> UnitShardingComponentState:
        """The unit shard state."""
        return UnitShardingComponentState(
            relation=self.shard_relation,
            data_interface=self.shard_state_interface,
            component=self.model.unit,
        )

    @property
    def config_server_name(self) -> str | None:
        """Gets the config server name."""
        if self.charm_role.name == CharmKind.MONGOS:
            if self.mongos_cluster_relation:
                return self.mongos_cluster_relation.app.name
            return None
        if self.is_role(MongoDBRoles.SHARD):
            if self.shard_relation:
                return self.shard_relation.app.name
            return None
        logger.info(
            "Component %s is not a shard, cannot be integrated to a config-server.",
            self.app_peer_data.role,
        )
        return None

    def get_subject_name(self) -> str:
        """Generate the subject name for CSR."""
        # In sharded MongoDB deployments it is a requirement that all subject names match across
        # all cluster components. The config-server name is the source of truth across mongos and
        # shard deployments.
        if self.is_role(MongoDBRoles.REPLICATION) or self.is_role(MongoDBRoles.CONFIG_SERVER):
            return self.model.app.name
        # until integrated with config-server use current app name as
        # subject name
        return self.config_server_name or self.model.app.name

    def generate_config_server_db(self) -> str:
        """Generates the config server DB URI."""
        replica_set_name = self.model.app.name
        hosts = sorted(f"{host}:{MongoPorts.MONGODB_PORT.value}" for host in self.internal_hosts)
        return f"{replica_set_name}/{','.join(hosts)}"

    # END: Helpers
    def _update_ca_secrets(self, new_ca: str | None, cluster_key: str, sharding_key: str) -> None:
        """Updates the CA secret for the right values on the right fields."""
        # Only the leader can update the databag
        if not self.charm.unit.is_leader():
            return
        if not self.is_role(MongoDBRoles.CONFIG_SERVER):
            return
        for relation in self.cluster_relations:
            if new_ca is None:
                self.cluster_provider_data_interface.delete_relation_data(
                    relation.id, [cluster_key]
                )
            else:
                self.cluster_provider_data_interface.update_relation_data(
                    relation.id, {cluster_key: new_ca}
                )
        for relation in self.config_server_relation:
            if new_ca is None:
                self.config_server_data_interface.delete_relation_data(relation.id, [sharding_key])
            else:
                self.config_server_data_interface.update_relation_data(
                    relation.id, {sharding_key: new_ca}
                )

    def update_peer_ca_secrets(self, new_ca: str | None) -> None:
        """Updates the peer CA secret in the cluster and config-server relations."""
        self._update_ca_secrets(
            new_ca=new_ca,
            cluster_key=ClusterStateKeys.INT_CA_SECRET.value,
            sharding_key=AppShardingComponentKeys.INT_CA_SECRET.value,
        )

    def update_client_ca_secrets(self, new_ca: str | None) -> None:
        """Updates the client CA secret in the cluster and config-server relations."""
        self._update_ca_secrets(
            new_ca=new_ca,
            cluster_key=ClusterStateKeys.EXT_CA_SECRET.value,
            sharding_key=AppShardingComponentKeys.EXT_CA_SECRET.value,
        )

    def is_scaling_down(self, rel_id: int) -> bool:
        """Returns True if the application is scaling down."""
        rel_departed_key = generate_relation_departed_key(rel_id)
        return json.loads(self.unit_peer_data.get(rel_departed_key, "false"))

    def has_departed_run(self, rel_id: int) -> bool:
        """Returns True if the relation departed event has run."""
        rel_departed_key = generate_relation_departed_key(rel_id)
        return self.unit_peer_data.get(rel_departed_key) != ""

    def set_scaling_down(self, rel_id: int, departing_unit_name: str) -> bool:
        """Sets whether or not the current unit is scaling down."""
        # check if relation departed is due to current unit being removed. (i.e. scaling down the
        # application.)
        rel_departed_key = generate_relation_departed_key(rel_id)
        scaling_down = departing_unit_name == self.unit_peer_data.name
        self.unit_peer_data.update({rel_departed_key: json.dumps(scaling_down)})
        return scaling_down

    def is_shard_added_to_cluster(self) -> bool:
        """Returns true if the shard has been added to the clusted."""
        # this information is required in order to check if we have been added
        if not self.config_server_name or not self.app_peer_data.mongos_hosts:
            return False

        # We can't check if we don't have a valid certificate
        if self.shard_state.external_ca_secret is not None and not self.tls.client_enabled:
            return False

        try:
            # check our ability to use connect to mongos
            with MongoConnection(self.remote_mongos_config) as mongos:
                members = mongos.get_shard_members()
        except OperationFailure as e:
            if e.code in (
                MongoErrorCodes.UNAUTHORIZED,
                MongoErrorCodes.AUTHENTICATION_FAILED,
                MongoErrorCodes.FAILED_TO_SATISFY_READ_PREFERENCE,
            ):
                return False
            raise
        except (ServerSelectionTimeoutError, AutoReconnect, NotPrimaryError):
            # Connection refused, - this occurs when internal membership is not in sync across the
            # cluster (i.e. TLS + KeyFile).
            return False

        return self.app_peer_data.replica_set in members

    # BEGIN: Configuration accessors

    def has_credentials(self) -> bool:
        """Checks if we have received credentials or not."""
        try:
            self.mongo_config
            return True
        except MissingCredentialsError:
            return False

    def mongodb_config_for_user(
        self,
        user: MongoDBUser,
        hosts: set[str] = set(),
        replset: str | None = None,
        standalone: bool = False,
    ) -> MongoConfiguration:
        """Returns a mongodb-specific MongoConfiguration object for the provided user.

        Either user.hosts or hosts should be a non empty set.

        Returns:
            A MongoDB configuration object.

        Raises:
            Exception if neither user.hosts nor hosts is non empty.
        """
        if not user.hosts and not hosts:
            raise Exception("Invalid call: no host in user nor as a parameter.")
        return MongoConfiguration(
            replset=replset or self.app_peer_data.replica_set,
            database=user.database_name,
            username=user.username,
            password=self.get_user_password(user),
            hosts=hosts or user.hosts,
            port=MongoPorts.MONGODB_PORT.value,
            roles=user.roles,
            tls_enabled=self.tls.client_enabled,
            tls_external_keyfile=self.paths.ext_pem_file,
            tls_external_ca=self.paths.ext_ca_file,
            standalone=standalone,
        )

    def mongos_config_for_user(
        self,
        user: MongoDBUser,
        hosts: set[str] = set(),
    ) -> MongoConfiguration:
        """Returns a mongos-specific MongoConfiguration object for the provided user.

        Either user.hosts or hosts should be a non empty set.

        Returns:
            A MongoDB configuration object.

        Raises:
            Exception if neither user.hosts nor hosts is non empty.
        """
        if not user.hosts and not hosts:
            raise Exception("Invalid call: no host in user nor as a parameter.")
        return MongoConfiguration(
            database=user.database_name,
            username=user.username,
            password=self.get_user_password(user),
            hosts=hosts or user.hosts,
            port=MongoPorts.MONGOS_PORT.value,
            roles=user.roles,
            tls_enabled=self.tls.client_enabled,
            tls_external_keyfile=self.paths.ext_pem_file,
            tls_external_ca=self.paths.ext_ca_file,
        )

    @property
    def backup_config(self) -> MongoConfiguration:
        """Mongo Configuration for the charmed-backup user."""
        return self.mongodb_config_for_user(CharmedBackupUser, standalone=True)

    @property
    def stats_config(self) -> MongoConfiguration:
        """Mongo Configuration for the charmed-stats user."""
        return self.mongodb_config_for_user(CharmedStatsUser, hosts=self.internal_hosts)

    @property
    def logrotate_config(self) -> MongoConfiguration:
        """Mongo Configuration for the charmed-logrotate user."""
        return self.mongodb_config_for_user(CharmedLogRotateUser, standalone=True)

    @property
    def operator_config(self) -> MongoConfiguration:
        """Mongo Configuration for the charmed-operator user."""
        return self.mongodb_config_for_user(CharmedOperatorUser, hosts=self.internal_hosts)

    @property
    def remote_mongos_config(self) -> MongoConfiguration:
        """Mongos Configuration for the remote mongos server."""
        mongos_hosts = self.app_peer_data.mongos_hosts
        return self.mongos_config_for_user(CharmedOperatorUser, set(mongos_hosts))

    @property
    def mongos_config(self) -> MongoConfiguration:
        """Mongos Configuration for the admin mongos user."""
        if self.charm_role.name == CharmKind.MONGOD:
            return self.mongos_config_for_user(CharmedOperatorUser, self.internal_hosts)
        username, password = self.get_user_credentials()
        database = self.app_peer_data.database
        port: int | None = MongoPorts.MONGOS_PORT.value
        if (
            self.charm_role.name == CharmKind.MONGOS
            and self.substrate == Substrates.VM
            and not self.app_peer_data.external_connectivity
        ):
            port = None
        if not username or not password:
            raise MissingCredentialsError("Missing credentials.")

        return MongoConfiguration(
            database=database,
            username=username,
            password=password,
            hosts=self.internal_hosts,
            # unlike the vm mongos charm, the K8s charm does not communicate with the unix socket
            port=port,
            roles={RoleNames.ADMIN},
            tls_enabled=self.tls.client_enabled,
            tls_external_keyfile=self.paths.ext_pem_file,
            tls_external_ca=self.paths.ext_ca_file,
        )

    @property
    def mongo_config(self) -> MongoConfiguration:
        """The mongo configuration to use by default for charm interactions."""
        if self.charm_role.name == CharmKind.MONGOD:
            return self.operator_config
        return self.mongos_config

    # END: Configuration accessors

    def get_secret_from_id(self, secret_id: str) -> dict[str, str]:
        """Resolve the given id of a Juju secret and return the content as a dict.

        Args:
            secret_id (str): The id of the secret.

        Returns:
            dict: The content of the secret.
        """
        if not secret_id.startswith("secret:"):
            raise ValueError(f"Invalid secret URI '{secret_id}'. It must start with 'secret:'")
        try:
            secret_content = self.charm.model.get_secret(id=secret_id).get_content(refresh=True)
        except SecretNotFoundError:
            raise SecretNotFoundError(f"The secret '{secret_id}' does not exist.")
        except ModelError:
            raise

        return secret_content
