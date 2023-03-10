import json
import os
from datetime import datetime
from pathlib import Path

import click
import tenacity
from cosmpy.aerial.config import NetworkConfig
from loguru import logger

from kleo_rewards.scripts.client import LedgerClient
from kleo_rewards.scripts.coingecko_client import Coingecko
from kleo_rewards.scripts.utils import get_chain_info, get_network_config_args, convert_assets_data

price_feed_folder = Path(__file__).parent / "price_feed_folder"


@click.command()
@click.option(
    "--lp_addr",
    default="juno1dpqgt3ja2kdxs94ltjw9ncdsexts9e3dx5qpnl20zvgdguzjelhqstf8zg",
    prompt="Liquidity Pool address",
)
@click.option("--chain_name", default="juno", prompt="Chain name [ex. juno]")
@click.option("--fiat-symbol", default="usd", prompt="FIAT symbol [ex. usd, eur]")
def compute_price_feed(lp_addr: str, chain_name: str, fiat_symbol: str):
    logger.info(f"Computing Price Feed for $KLEO on liquidity pool {lp_addr} rewards.")

    chain_info = get_chain_info(chain_name)
    network_cfg_kwargs = get_network_config_args(chain_info)
    network_cfg = NetworkConfig(**network_cfg_kwargs)
    client = LedgerClient(network_cfg)

    logger.info(f"Chain {chain_name} with native token {network_cfg.fee_denomination}")
    logger.info(f"Target FIAT selected {fiat_symbol}")

    try:
        resp_cum_prices_wynddao = client.query_liquidity_pool_wynddao(lp_addr)

        lp_amounts = convert_assets_data(resp_cum_prices_wynddao["assets"])
        logger.info(lp_amounts)
        try:
            price = lp_amounts["native"] / lp_amounts["cw20"]
        except ZeroDivisionError:
            logger.error(
                "There are 0 native token so no pricing calculation is possible...Abort!"
            )
            return

        logger.info(f"Price is {price} at timestamp {datetime.utcnow().timestamp()}")
        logger.info(
            f"In order to buy 1 uKLEO you need {price} {network_cfg.fee_denomination}"
        )

        cg = Coingecko()

        native_price_fiat = cg.pretty_prices()[chain_name.upper()]["prices"][
            fiat_symbol.lower()
        ]

        data_to_push = {
            "timestamp": int(datetime.utcnow().timestamp() * 1000),  # EPOCH millisecs,
            "kleo_price_in_juno": price,
            "kleo_price_in_dollars": price * native_price_fiat,
        }
        logger.debug(f"Data to push {data_to_push}")

        if not (os.path.isdir(price_feed_folder)):
            os.makedirs(price_feed_folder, exist_ok=True)

        filename = price_feed_folder / f"kleo_price_feed-{datetime.now()}.json"

        with open(filename, "w") as fp:
            # write data to file
            json.dump(data_to_push, fp, indent=4)

        logger.info(f"Data written to file {filename}")

    except tenacity.RetryError as e:
        print(
            f"Failed after {e.last_attempt.attempt_number} attempts: {e.last_attempt.result()}"
        )
    except Exception as e:
        logger.error(f"Error: {e}")


if __name__ == "__main__":
    compute_price_feed()
