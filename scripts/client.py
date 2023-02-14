import requests
from cosmpy.aerial.config import NetworkConfig
from cosmpy.aerial.urls import Protocol, parse_url
from cosmpy.aerial.client import LedgerClient
from cosmpy.mint.rest_client import MintRestClient
from cosmpy.common.rest_client import RestClient
from cosmpy.cosmwasm.rest_client import CosmWasmRestClient
from cosmpy.staking.rest_client import StakingRestClient

from scripts.costants import COSMOS_DIR_API, COSMOS_DIR_REST_PROXY


class LedgerClientV2(LedgerClient):
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


def get_chain_info(chain):
    url = f"{COSMOS_DIR_API}/{chain}"
    resp = requests.get(url)
    resp.raise_for_status()

    return resp.json()


def get_network_config_args(chain_info):
    chain = chain_info["chain"]
    chain_name = chain["chain_name"]

    try:
        fee_token = chain["fees"]["fee_tokens"][0]
        fee_denom = fee_token["denom"]
        min_gas_price = fee_token["fixed_min_gas_price"]
    except KeyError as ex:
        fee_denom = chain["denom"]
        min_gas_price = 0

    return {
        "chain_id": chain["chain_id"],
        "url": f"rest+{COSMOS_DIR_REST_PROXY}/{chain_name}",
        "fee_minimum_gas_price": min_gas_price,
        "fee_denomination": fee_denom,
        "staking_denomination": "",
    }
