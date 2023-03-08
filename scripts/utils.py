import requests
from bip_utils import Bech32Decoder, Bech32Encoder

from scripts.costants import COSMOS_DIR_API, COSMOS_DIR_REST_PROXY


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


def convert_to_juno_address(chain: str, address: str) -> str:
    decoded_juno = Bech32Decoder.Decode(chain, address)
    return Bech32Encoder.Encode("juno", decoded_juno)
