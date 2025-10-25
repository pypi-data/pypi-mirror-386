#!/usr/bin/env python3
# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.

"""The Config Server / Shard state."""

import json
from enum import Enum

from ops import Application
from ops.model import Relation, Unit

from single_kernel_mongo.lib.charms.data_platform_libs.v0.data_interfaces import Data
from single_kernel_mongo.state.abstract_state import AbstractRelationState


class AppShardingComponentKeys(str, Enum):
    """Config Server State Model for the application."""

    DATABASE = "database"
    OPERATOR_PASSWORD = "charmed-operator-password"
    BACKUP_PASSWORD = "charmed-backup-password"
    HOST = "host"
    KEY_FILE = "key-file"
    INT_CA_SECRET = "int-ca-secret"
    EXT_CA_SECRET = "ext-ca-secret"
    BACKUP_CA_SECRET = "backup-ca-secret"

    # We don't use those except to check if we've received credentials
    USERNAME = "username"
    PASSWORD = "password"


SECRETS_FIELDS = [
    "charmed-operator-password",
    "charmed-backup-password",
    "key-file",
    "int-ca-secret",
    "ext-ca-secret",
    "backup-ca-secret",
]


class AppShardingComponentState(AbstractRelationState[Data]):
    """The stored state for the ConfigServer Relation."""

    component: Application

    def __init__(self, relation: Relation | None, data_interface: Data, component: Application):
        super().__init__(relation, data_interface=data_interface, component=component)
        self.data_interface = data_interface

    @property
    def mongos_hosts(self) -> list[str]:
        """The mongos hosts in the relation."""
        return json.loads(self.relation_data.get(AppShardingComponentKeys.HOST.value, "[]"))

    @mongos_hosts.setter
    def mongos_hosts(self, value: list[str]):
        self.update({AppShardingComponentKeys.HOST.value: json.dumps(sorted(value))})

    def has_received_credentials(self) -> bool:
        """Checks if the config-server has sent credentials."""
        if not self.relation:
            return False
        return (
            self.relation_data.get(AppShardingComponentKeys.OPERATOR_PASSWORD.value, None)
            is not None
            and self.relation_data.get(AppShardingComponentKeys.BACKUP_PASSWORD.value, None)
            is not None
        )

    @property
    def internal_ca_secret(self) -> str | None:
        """Returns the internal CA secret."""
        if not self.relation:
            return None
        return self.relation_data.get(AppShardingComponentKeys.INT_CA_SECRET.value, None)

    @property
    def external_ca_secret(self) -> str | None:
        """Returns the external CA secret."""
        if not self.relation:
            return None
        return self.relation_data.get(AppShardingComponentKeys.EXT_CA_SECRET.value, None)

    @property
    def keyfile(self) -> str | None:
        """Returns the keyfile."""
        if not self.relation:
            return None
        return self.relation_data.get(AppShardingComponentKeys.KEY_FILE.value, None)

    @property
    def operator_password(self) -> str | None:
        """Returns the charmed-operator password."""
        if not self.relation:
            return None
        return self.relation_data.get(AppShardingComponentKeys.OPERATOR_PASSWORD.value, None)

    @property
    def backup_password(self) -> str | None:
        """Returns the charmed-backup password."""
        if not self.relation:
            return None
        return self.relation_data.get(AppShardingComponentKeys.BACKUP_PASSWORD.value, None)

    @property
    def backup_ca_secret(self) -> list[str] | None:
        """Returns the backup ca secret."""
        if not self.relation:
            return None
        return json.loads(
            self.relation_data.get(AppShardingComponentKeys.BACKUP_CA_SECRET.value, "null")
        )


class UnitShardingComponentState(AbstractRelationState[Data]):
    """The stored state for the ConfigServer Relation."""

    component: Unit

    def __init__(self, relation: Relation | None, data_interface: Data, component: Unit):
        super().__init__(relation, data_interface=data_interface, component=component)
        self.data_interface = data_interface
