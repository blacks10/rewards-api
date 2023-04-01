import json
import os
from datetime import datetime
from pathlib import Path

import click
import requests
import tenacity
from loguru import logger
from cosmpy.aerial.config import NetworkConfig
from tqdm import tqdm

from kleo_rewards.scripts.client import LedgerClient
from kleo_rewards.scripts.utils import get_chain_info, get_network_config_args
from kleo_rewards.scripts.costants import STAKING_CONTRACT

rev_share_folder = Path(__file__).parent / "rev_share_folder"


# rev share formula
# (users_staked/total_staked)*total_rewards


@click.command()
@click.option("--total_rewards", prompt="Total rewards of this month")
@click.option("--month", prompt="Month")
@click.option("--height", prompt="Height block")
def compute_rev_share(total_rewards: int, month: str, height: str):
    logger.info(f"Computing rev share for {total_rewards} rewards.")

    chain_info = get_chain_info("juno")
    network_cfg_kwargs = get_network_config_args(chain_info)
    network_cfg = NetworkConfig(**network_cfg_kwargs)
    client = LedgerClient(network_cfg)

    stakers = []

    try:
        # TOTAL STAKED
        res_total_staked_at_height_dict = client.query_total_staked_at_height_dict(
            staking_contract=STAKING_CONTRACT,
            height=height
        )
        total_staked = res_total_staked_at_height_dict["total"]
        logger.info(f"TOTAL STAKED: {total_staked}")

        # USERS STAKED
        resp_all_accounts_kleo = client.rest_client.get(
            f"/cosmwasm/wasm/v1/contract/{STAKING_CONTRACT}/state?pagination.limit=10000"
        )
        # _session = requests.session()
        # height_header = {
        #     "x-cosmos-block-height": height,
        #     "Content-Type": "application/json"
        # }
        # kleo_state_url = f"https://rest.cosmos.directory/juno/cosmwasm/wasm/v1/contract/{STAKING_CONTRACT}/state?pagination.limit=10000"
        # resp_all_accounts_kleo = _session.get(kleo_state_url, headers=height_header)
        encoded_resp = json.loads(resp_all_accounts_kleo.decode("utf-8"))
        logger.info(f"Loaded all staking users.")
        logger.info(f"Start revenue calculation..")

        for model in tqdm(encoded_resp["models"], "Computing.."):

            address_long = bytes.fromhex((model["key"])).decode(
                "utf-8", errors="ignore"
            )[2:]
            if address_long.startswith("staked") and not "changelog" in address_long:
                # balance = base64.b64decode(model["value"]).decode("utf-8").strip('"')
                address = address_long[15:]

                res_user_staked_at_height_dict = (
                    client.query_staked_balance_at_height_dict(
                        staking_contract=STAKING_CONTRACT, address=address, height=height
                    )
                )

                user_staked = res_user_staked_at_height_dict["balance"]

                amount = int(
                    (int(user_staked) / int(total_staked)) * int(total_rewards)
                )

                if amount == 0:
                    continue

                stakers_dict = {
                    "address": address,
                    "amount": str(amount),
                }
                stakers.append(stakers_dict)

    except tenacity.RetryError as e:
        print(
            f"Failed after {e.last_attempt.attempt_number} attempts: {e.last_attempt.result()}"
        )
    except Exception as e:
        print(f"Error: {e}")

    logger.info(f"Computed rev share for {len(stakers)} stakers.")

    if not (os.path.isdir(rev_share_folder)):
        os.makedirs(rev_share_folder, exist_ok=True)

    filename = (
            rev_share_folder / f"rev_share-{month}.json"
    )
    with open(filename, "w") as json_file:
        json.dump(stakers, json_file, indent=4)

    logger.info(f"Rev share file is ready: {filename}")


if __name__ == "__main__":
    compute_rev_share()
    # from datetime import datetime, timedelta
    #
    # JUNO_GENESIS_TIME = datetime(2021, 10, 1, 17, 0, 0)  # Replace with actual Juno genesis time
    # BLOCK_TIME = timedelta(seconds=6.18)
    #
    # def juno_block_height_to_datetime(block_height):
    #     elapsed_time = block_height * BLOCK_TIME
    #     return JUNO_GENESIS_TIME + elapsed_time
    #
    # def datetime_to_juno_block_height(dt):
    #     time_diff = dt - JUNO_GENESIS_TIME
    #     num_blocks = int(time_diff / BLOCK_TIME)
    #     return num_blocks
    #
    #
    # block_height = 7627457
    # block_datetime = juno_block_height_to_datetime(block_height)
    #
    # date_now = datetime(2023, 3, 31, 7, 0, 0)
    # block_height_new = datetime_to_juno_block_height(date_now)
    # print(JUNO_GENESIS_TIME)
    # print(block_datetime)
