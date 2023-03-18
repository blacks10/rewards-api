import json
from collections import OrderedDict
from datetime import datetime
from pathlib import Path

import click
import tenacity
from cosmpy.aerial.config import NetworkConfig
from tqdm import tqdm

from kleo_rewards.scripts.costants import STAKING_CONTRACT

from kleo_rewards.scripts.client import LedgerClient

from kleo_rewards.scripts.utils import get_chain_info, get_network_config_args
from loguru import logger

biggest_stakers_folder = Path(__file__).parent / "bigger_staker_folder"


@click.command()
@click.option("--number", prompt="number of biggest stakers", default=50)
@click.option("--chain_name", default="juno", prompt="Chain name [ex. juno]")
def compute_biggest_stakers(chain_name: str, number: int):
    logger.info(f"Computing biggest stakers.")

    chain_info = get_chain_info(chain_name)
    network_cfg_kwargs = get_network_config_args(chain_info)
    network_cfg = NetworkConfig(**network_cfg_kwargs)
    client = LedgerClient(network_cfg)

    try:
        # TOTAL STAKED
        res_total_staked_at_height_dict = client.query_total_staked_at_height_dict(
            staking_contract=STAKING_CONTRACT
        )
        total_staked = res_total_staked_at_height_dict["total"]
        logger.info(f"TOTAL STAKED: {total_staked}")

        # USERS STAKED
        resp_all_accounts_kleo = client.rest_client.get(
            f"/cosmwasm/wasm/v1/contract/{STAKING_CONTRACT}/state?pagination.limit=10000"
        )
        encoded_resp = json.loads(resp_all_accounts_kleo.decode("utf-8"))
        logger.info(f"Loaded all staking users.")
        logger.info(f"Start revenue calculation..")

        stakes = {}

        for model in tqdm(encoded_resp["models"], "Computing.."):
            address_long = bytes.fromhex((model["key"])).decode(
                "utf-8", errors="ignore"
            )[2:]
            if address_long.startswith("staked") and not "changelog" in address_long:
                # balance = base64.b64decode(model["value"]).decode("utf-8").strip('"')
                address = address_long[15:]

                res_user_staked_at_height_dict = (
                    client.query_staked_balance_at_height_dict(
                        staking_contract=STAKING_CONTRACT, address=address
                    )
                )

                user_staked = res_user_staked_at_height_dict["balance"]
                stakes[address] = user_staked

        stakes = OrderedDict({k: v for k, v in sorted(stakes.items(), key=lambda item: item[1], reverse=True)})
        biggest_stakes = OrderedDict(**stakes)
        while len(biggest_stakes) > number:
            biggest_stakes.popitem()

        logger.info(f"Stakes: {stakes}")

        biggest_stakers_folder.mkdir(exist_ok=False)

        filename = (
                biggest_stakers_folder / f"biggest_stakers-{datetime.now().strftime('%B').lower()}.json"
        )
        with open(filename, "w") as json_file:
            json.dump(biggest_stakes, json_file, indent=4)

    except tenacity.RetryError as e:
        logger.error(
            f"Failed after {e.last_attempt.attempt_number} attempts: {e.last_attempt.result()}"
        )
    except Exception as e:
        logger.error(f"Error: {e}")


if __name__ == "__main__":
    compute_biggest_stakers()
