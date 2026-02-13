from pydid.service import Service
from typing_extensions import Literal
from pydantic import AnyUrl, ConfigDict, StrictStr
from typing import Any, List, Optional, Union



SINGLETON_BEACON = Literal["SingletonBeacon"]
SMT_AGGREGATE_BEACON = Literal["SMTAggregateBeacon"]    
CID_AGGREGATE_BEACON = Literal["CIDAggregateBeacon"]

BeaconTypeNames = ["SingletonBeacon", "SMTAggregateBeacon", "CIDAggregateBeacon"]


class BeaconService(Service):
    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
        populate_by_name=True,
        discriminator='type'
    )
    
    service_endpoint: str
    type: str



    def address(self):
        return self.service_endpoint.replace('bitcoin:', '')
    
    # def add_funding_tx(self, funding_tx):
    #     print("Funding Tx", funding_tx)
    #     for index, tx_out in enumerate(funding_tx.tx_outs):
    #         if beacon_address == tx_out.script_pubkey.address(network=self.network):
    #             prev_index = index
    #             break

class SingletonBeaconService(BeaconService):
    type: Literal["SingletonBeacon"] = "SingletonBeacon"



class SMTAggregateBeaconService(BeaconService):
    type: Literal["SMTAggregateBeacon"] = "SMTAggregateBeacon"

class CIDAggregateBeaconService(BeaconService):
    type: Literal["CIDAggregateBeacon"] = "CIDAggregateBeacon"

ServiceBeaconTypes = Union[SingletonBeaconService, SMTAggregateBeaconService, CIDAggregateBeaconService]