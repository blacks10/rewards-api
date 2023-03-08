import json
from cosmpy.common.utils import json_encode
from cosmpy.protos.cosmwasm.wasm.v1.query_pb2 import QuerySmartContractStateRequest
from tenacity import retry
from cosmpy.aerial.client import LedgerClient as BaseLedgerClient, NetworkConfig
from cosmpy.aerial.urls import Protocol, parse_url
from cosmpy.mint.rest_client import MintRestClient
from cosmpy.common.rest_client import RestClient
from cosmpy.cosmwasm.rest_client import CosmWasmRestClient
from cosmpy.protos.cosmos.staking.v1beta1.query_pb2 import (
    QueryValidatorDelegationsRequest,
    QueryValidatorRequest,
)
from cosmpy.staking.rest_client import StakingRestClient
from tenacity import stop_after_delay


class LedgerClient(BaseLedgerClient):
    def __init__(self, cfg: NetworkConfig):
        super().__init__(cfg)

        parsed_url = parse_url(cfg.url)
        if parsed_url.protocol == Protocol.GRPC:
            super().__init__(cfg)
        else:
            actual_rest_url = cfg.url.split("+")[1]
            rest_client = RestClient(actual_rest_url)
            self._rest_client = rest_client
            self.mint = MintRestClient(rest_client)
            self.wasm = CosmWasmRestClient(rest_client)
            self.staking = StakingRestClient(rest_client)

    @property
    def rest_client(self):
        return self._rest_client

    @retry(stop=stop_after_delay(10))
    def query_validator(self, validator_address: str):
        req_validator = QueryValidatorRequest(validator_addr=validator_address)
        return self.staking.Validator(req_validator)

    @retry(stop=stop_after_delay(10))
    def query_validator_delegations(
        self, validator_address: str, pagination_limit: int
    ):
        req_delegators = QueryValidatorDelegationsRequest(
            validator_addr=validator_address, pagination={"limit": pagination_limit}
        )
        return self.staking.ValidatorDelegations(req_delegators)

    @retry(stop=stop_after_delay(10))
    def query_total_staked_at_height_dict(self, staking_contract: str):
        query_dict = {"total_staked_at_height": {}}
        query_data = json_encode(query_dict).encode("UTF8")

        req_total_staked_at_height = QuerySmartContractStateRequest(
            address=staking_contract, query_data=query_data
        )
        res_total_staked_at_height = self.wasm.SmartContractState(
            req_total_staked_at_height
        )
        return json.loads(res_total_staked_at_height.data.decode("utf-8"))

    @retry(stop=stop_after_delay(10))
    def query_staked_balance_at_height_dict(self, staking_contract: str, address: str):
        query_dict = {"staked_balance_at_height": {"address": address}}

        query_data = json_encode(query_dict).encode("UTF8")

        req_user_staked_at_height = QuerySmartContractStateRequest(
            address=staking_contract, query_data=query_data
        )
        res_user_staked_at_height = self.wasm.SmartContractState(
            req_user_staked_at_height
        )
        return json.loads(res_user_staked_at_height.data.decode("utf-8"))
