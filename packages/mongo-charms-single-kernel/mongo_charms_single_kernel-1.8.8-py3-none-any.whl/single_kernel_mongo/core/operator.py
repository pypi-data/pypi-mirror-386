#!/usr/bin/python3
# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""Abstract Operator for Mongo Related Charms.

The Charm operator defines the minimal interface that should be specified when
defining an operator. This is a Mongo manager for all mongodb related
operations, a TLS manager since all charms should be able to support TLS, a
main workload (MongoDBWorkload or MongosWorkload) and some client events.

To that, each operator can add some extra event handlers that are specific to
this operator like backups or cluster event handlers, etc.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from logging import getLogger
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, TypeAlias

import charm_refresh
import jinja2
from data_platform_helpers.advanced_statuses.models import StatusObject
from data_platform_helpers.advanced_statuses.protocol import ManagerStatusProtocol
from ops.charm import RelationDepartedEvent
from ops.framework import Object
from ops.model import Relation, Unit

from single_kernel_mongo.config.literals import (
    OS_REQUIREMENTS,
    TRUST_STORE_PATH,
    Scope,
    Substrates,
    TrustStoreFiles,
)
from single_kernel_mongo.config.models import SNAP_NAME, THP_CONFIG, CharmSpec, LogRotateConfig
from single_kernel_mongo.events.ldap import LDAPEventHandler
from single_kernel_mongo.exceptions import (
    DeferrableFailedHookChecksError,
    NonDeferrableFailedHookChecksError,
)
from single_kernel_mongo.lib.charms.operator_libs_linux.v0 import sysctl
from single_kernel_mongo.lib.charms.operator_libs_linux.v1.systemd import (
    SystemdError,
    daemon_reload,
    service_disable,
    service_enable,
    service_start,
)
from single_kernel_mongo.managers.config import FileBasedConfigManager
from single_kernel_mongo.managers.mongo import MongoManager
from single_kernel_mongo.state.charm_state import CharmState
from single_kernel_mongo.workload.mongodb_workload import MongoDBWorkload
from single_kernel_mongo.workload.mongos_workload import MongosWorkload

if TYPE_CHECKING:
    from single_kernel_mongo.abstract_charm import AbstractMongoCharm
    from single_kernel_mongo.events.database import DatabaseEventsHandler
    from single_kernel_mongo.events.tls import TLSEventsHandler
    from single_kernel_mongo.lib.charms.operator_libs_linux.v0.sysctl import Config
    from single_kernel_mongo.managers.ldap import LDAPManager
    from single_kernel_mongo.managers.tls import TLSManager
    from single_kernel_mongo.managers.upgrade_v3 import MongoDBUpgradesManager
    from single_kernel_mongo.managers.upgrade_v3_status import MongoDBUpgradesStatusManager

logger = getLogger(__name__)

MainWorkloadType: TypeAlias = MongoDBWorkload | MongosWorkload


class OperatorProtocol(ABC, Object, ManagerStatusProtocol):
    """Protocol for a charm operator.

    A Charm Operator must define the following elements:
     * charm: The Charm it is bound to.
     * name: The charm operator name, which is one value of the `CharmKind`
        enum. This is a class var defined in the operator.
     * tls_manager: The TLS manager for the mandatory tls events and handlers
     * state : The CharmState, object handling peer databag interactions, and model interactions.
     * mongo_manager: The manager for MongoD related interactions.
     * workload: The main workload of this Charm.
    """

    charm: AbstractMongoCharm
    name: ClassVar[str]
    substrate: Substrates
    role: CharmSpec
    config_manager: FileBasedConfigManager
    tls_manager: TLSManager
    state: CharmState
    refresh: charm_refresh.Common | None
    mongo_manager: MongoManager
    upgrades_manager: MongoDBUpgradesManager
    upgrades_status_manager: MongoDBUpgradesStatusManager
    ldap_manager: LDAPManager
    workload: MainWorkloadType
    client_events: DatabaseEventsHandler
    tls_events: TLSEventsHandler
    ldap_events: LDAPEventHandler
    sysctl_config: Config

    if TYPE_CHECKING:

        def __init__(self, dependent: AbstractMongoCharm): ...

    @property
    @abstractmethod
    def components(self) -> tuple[ManagerStatusProtocol, ...]:
        """The ordered list of components reporting statuses."""
        ...

    @abstractmethod
    def install_workloads(self) -> None:
        """Handles the install event."""
        ...

    @abstractmethod
    def prepare_for_startup(self) -> None:
        """Handles the start event."""
        ...

    @abstractmethod
    def update_secrets_and_restart(self, secret_label: str, secret_id: str) -> None:
        """Handles the secret changed events."""

    @abstractmethod
    def update_config_and_restart(self) -> None:
        """Handles the config changed events."""
        ...

    @abstractmethod
    def prepare_storage(self) -> None:
        """Handles the storage attached events."""
        ...

    @abstractmethod
    def prepare_storage_for_shutdown(self) -> None:
        """Handles the storage attached events."""
        ...

    @abstractmethod
    def new_leader(self) -> None:
        """Handles the leader elected events."""
        ...

    @abstractmethod
    def update_status(self) -> None:
        """Handle the status update events."""
        ...

    @abstractmethod
    def new_peer(self) -> None:
        """Handles the relation changed events."""
        ...

    @abstractmethod
    def peer_changed(self) -> None:
        """Handles the relation changed events."""
        ...

    @abstractmethod
    def peer_leaving(self, departing_unit: Unit | None) -> None:
        """Handles the relation departed events."""
        ...

    @abstractmethod
    def prepare_for_shutdown(self) -> None:
        """Handles the stop event."""
        ...

    @abstractmethod
    def start_charm_services(self) -> None:
        """Starts the relevant services."""
        ...

    @abstractmethod
    def stop_charm_services(self) -> None:
        """Stop the relevant services."""
        ...

    @abstractmethod
    def restart_charm_services(self, force: bool = False) -> None:
        """Restart the relevant services with updated config."""
        ...

    @abstractmethod
    def get_relation_feasible_status(self, name: str) -> StatusObject | None:
        """Checks if the relation is feasible in this context."""
        ...

    @abstractmethod
    def _configure_workloads(self) -> None:
        """Configures the workload."""
        ...

    @abstractmethod
    def get_statuses(self, scope: Scope, recompute: bool = False) -> Sequence[StatusObject]:
        """Recomputes the statuses for the given scope."""
        ...

    def assert_proceed_on_broken_event(self, relation: Relation) -> None:
        """Runs some checks on broken relation event."""
        if not self.state.has_departed_run(relation.id):
            raise DeferrableFailedHookChecksError(
                "must wait for relation departed hook to decide if relation should be removed"
            )

        if self.state.is_scaling_down(relation.id):
            raise NonDeferrableFailedHookChecksError(
                "Relation broken event occurring during scale down, do not proceed to remove users."
            )

    def check_relation_broken_or_scale_down(self, event: RelationDepartedEvent) -> None:
        """Checks relation departed event is the result of removed relation or scale down.

        Relation departed and relation broken events occur during scaling down or during relation
        removal, only relation departed events have access to metadata to determine which case.
        """
        departing_name = event.departing_unit.name if event.departing_unit else ""
        scaling_down = self.state.set_scaling_down(
            event.relation.id, departing_unit_name=departing_name
        )

        if scaling_down:
            logger.info(
                "Scaling down the application, no need to process removed relation in broken hook."
            )

    @property
    def refresh_in_progress(self) -> bool:
        """Check if charm-refresh is currently in progress."""
        # If charm_refresh.UnitTearDown or charm_refresh.PeerRelationNotReady
        # we consider a refresh to be in progress.
        return not self.refresh or self.refresh.in_progress

    def handle_licenses(self) -> None:
        """Pull / Push licenses.

        This function runs differently according to the substrate. We do not
        store the licenses at the same location, and we do not handle the same
        licenses.
        """
        licenses = [
            "snap",
            "mongodb-exporter",
            "percona-backup-mongodb",
            "percona-server",
        ]
        prefix = Path("./src/licenses") if self.substrate == Substrates.VM else Path("./")
        # Create the directory if needed.
        if self.substrate == Substrates.VM:
            prefix.mkdir(exist_ok=True)
            file = Path("./LICENSE")
            dst = prefix / "LICENSE-charm"
            self.workload.copy_to_unit(file, dst)
        else:
            name = "LICENSE-rock"
            file = Path(f"{self.workload.paths.licenses_path}/{name}")
            dst = prefix / name
            if not dst.is_file():
                self.workload.copy_to_unit(file, dst)

        for license in licenses:
            name = f"LICENSE-{license}"
            file = Path(f"{self.workload.paths.licenses_path}/{name}")
            dst = prefix / name
            if not dst.is_file():
                self.workload.copy_to_unit(file, dst)

    def set_permissions(self) -> None:
        """Ensure directories and make permissions.

        We must ensure that the log status directory for LogRotate is existing.
        We must also ensure that all data, log and log status directories have
        the correct permissions.
        """
        self.workload.mkdir(LogRotateConfig.log_status_dir, make_parents=True)

        for path in (
            self.workload.paths.data_path,
            self.workload.paths.logs_path,
            LogRotateConfig.log_status_dir,
        ):
            self.workload.exec(
                [
                    "chown",
                    "-R",
                    f"{self.workload.users.user}:{self.workload.users.group}",
                    f"{path}",
                ]
            )

        if self.substrate == Substrates.VM:
            self.workload.exec(
                [
                    "chown",
                    "-R",
                    f"{self.workload.users.user}:{self.workload.users.group}",
                    f"{self.workload.paths.common_path}",
                ]
            )

        for path in (
            self.workload.paths.config_file,
            self.workload.paths.mongos_config_file,
        ):
            self.workload.exec(["chmod", "600", f"{path}"])

    def save_ca_cert_to_trust_store(self, file: TrustStoreFiles, chain: list[str]) -> None:
        """Saves the certificate in the trust store.

        Raises:
            WorkloadExecError: In that case, we should let the charm go into error state.
        """
        # Convert the list of str to a str
        chain_str = "\n".join(chain)
        # Write the file with the right permissions
        full_path = TRUST_STORE_PATH / file.value
        self.workload.write(full_path, chain_str)
        self.workload.exec(["chown", "root:root", f"{full_path}"])
        self.workload.exec(["chmod", "644", f"{full_path}"])

        # Update ca certificates.
        self.workload.exec(["update-ca-certificates"])

    def remove_ca_cert_from_trust_store(self, file: TrustStoreFiles):
        """Removes the certificate from the trust store."""
        if not self.workload.exists(TRUST_STORE_PATH / file.value):
            return

        # Remove the file
        self.workload.delete(TRUST_STORE_PATH / file.value)
        # Update CA certificates to remove the certificate from the trust store
        self.workload.exec(["update-ca-certificates"])
        # Restart the service
        self.restart_charm_services(force=True)

    def write_thp_config_file(self):
        """Writes the unit file to enable Transparent Huge Pages."""
        data = THP_CONFIG.service_template.read_text()
        template = jinja2.Template(data)

        rendered_template = template.render(
            service_file=f"snap.{SNAP_NAME}.{self.workload.service}.service"
        )
        self.workload.write(path=THP_CONFIG.service_file_path, content=rendered_template)
        daemon_reload()
        service_enable(THP_CONFIG.service_name)
        service_start(THP_CONFIG.service_name)

    def _set_os_config(self) -> None:
        """Sets sysctl config for mongodb."""
        try:
            self.sysctl_config.configure(OS_REQUIREMENTS)
        except (sysctl.ApplyError, sysctl.ValidationError, sysctl.CommandError) as e:
            # we allow events to continue in the case that we are not able to correctly configure
            # sysctl config, since we can  still run the workload with wrong sysctl parameters
            # even if it is not optimal.
            logger.error(f"Error setting values on sysctl parameters: {e.message}")
            # containers share the kernel with the host system, and some sysctl parameters are
            # set at kernel level.
            logger.warning("sysctl params cannot be set. Is the machine running on a container?")
        try:
            self.write_thp_config_file()
        except SystemdError as e:
            # we allow events to continue in the case that we are not able to correctly configure
            # sysctl config, since we can  still run the workload with wrong kernel parameters
            # even if it is not optimal.
            logger.error(f"Error setting values on kernel parameters: {e.args}")
            # containers share the kernel with the host system, and some sysctl parameters are
            # set at kernel level.
            logger.warning("kernel params cannot be set. Is the machine running on a container?")
            service_disable(THP_CONFIG.service_name)

    def build_local_tls_directory(self) -> None:
        """On Kubernetes, we need the local configuration directory.

        This will store the certificates locally, which allows to construct the
        same URIS to connect locally and on the sidecar container running
        mongodb.
        """
        if self.substrate == Substrates.VM:
            return

        Path(self.state.paths.conf_path).mkdir(exist_ok=True)
