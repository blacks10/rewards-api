import click
import json
from cosmpy.aerial.config import NetworkConfig
from loguru import logger

from scripts.client import LedgerClient
from scripts.utils import get_chain_info, get_network_config_args


@click.command()
@click.option("--lp_addr", prompt="Liquidity Pool address")
@click.option("--chain_name", prompt="Chain name [ex. juno]")
def compute_price_feed(lp_addr: str, chain_name: str):
    logger.info(f"Computing Price Feed for $KLEO on liquidity pool {lp_addr} rewards.")

    chain_info = get_chain_info(chain_name)
    network_cfg_kwargs = get_network_config_args(chain_info)
    network_cfg = NetworkConfig(**network_cfg_kwargs)
    client = LedgerClient(network_cfg)

    try:
        resp_cum_prices_wynddao = client.rest_client.get(
            f"/cosmwasm/wasm/v1/contract/{lp_addr}/state"
        )

        encoded_resp = json.loads(resp_cum_prices_wynddao.decode("utf-8"))

        logger.info(f"resp: {encoded_resp}")
        val = bytes.fromhex((model["key"])).decode(
                "utf-8", errors="ignore"
            )[2:]
        logger.info(f"value = {}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    lp_addr = "juno1dpqgt3ja2kdxs94ltjw9ncdsexts9e3dx5qpnl20zvgdguzjelhqstf8zg"
    chain_name = "juno"
    compute_price_feed(lp_addr, chain_name)()
