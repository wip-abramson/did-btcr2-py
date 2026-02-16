from typing import Literal

from pydantic import ConfigDict
from pydid.service import Service

from .constants import BEACON_TYPE_NAMES

SINGLETON_BEACON = Literal["SingletonBeacon"]
SMT_AGGREGATE_BEACON = Literal["SMTAggregateBeacon"]
CID_AGGREGATE_BEACON = Literal["CIDAggregateBeacon"]

BeaconTypeNames = BEACON_TYPE_NAMES


class BeaconService(Service):
    model_config = ConfigDict(
        extra="forbid", from_attributes=True, populate_by_name=True, discriminator="type"
    )

    service_endpoint: str
    type: str

    def address(self):
        return self.service_endpoint.replace("bitcoin:", "")


class SingletonBeaconService(BeaconService):
    type: Literal["SingletonBeacon"] = "SingletonBeacon"


class SMTAggregateBeaconService(BeaconService):
    type: Literal["SMTAggregateBeacon"] = "SMTAggregateBeacon"


class CIDAggregateBeaconService(BeaconService):
    type: Literal["CIDAggregateBeacon"] = "CIDAggregateBeacon"


ServiceBeaconTypes = SingletonBeaconService | SMTAggregateBeaconService | CIDAggregateBeaconService
