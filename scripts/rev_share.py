import base64
import json
import os
from datetime import datetime
from pathlib import Path

import click
from loguru import logger
from cosmpy.aerial.config import NetworkConfig
from cosmpy.common.utils import json_encode
from cosmpy.protos.cosmwasm.wasm.v1.query_pb2 import QuerySmartContractStateRequest
from scripts.client import get_chain_info, get_network_config_args, LedgerClientV2
from scripts.costants import STAKING_CONTRACT

rev_share_folder = Path(__file__).parent / "rev_share_json"


# rev share formula
# (users_staked/total_staked)*total_rewards


@click.command()
@click.option("--total_rewards", prompt="Total rewards of this month")
@click.option("--chain_name", prompt="Chain name [ex. juno]")
def compute_rev_share(total_rewards: int, chain_name: str):
    logger.info(f"Computing rev share for {total_rewards} rewards.")

    chain_info = get_chain_info(chain_name)
    network_cfg_kwargs = get_network_config_args(chain_info)
    network_cfg = NetworkConfig(**network_cfg_kwargs)
    client = LedgerClientV2(network_cfg)

    # TOTAL STAKED
    query_dict = {"total_staked_at_height": {}}
    query_data = json_encode(query_dict).encode("UTF8")

    req_total_staked_at_height = QuerySmartContractStateRequest(
        address=STAKING_CONTRACT, query_data=query_data
    )
    res_total_staked_at_height = client.wasm.SmartContractState(
        req_total_staked_at_height
    )
    res_total_staked_at_height_dict = json.loads(
        res_total_staked_at_height.data.decode("utf-8")
    )

    total_staked = res_total_staked_at_height_dict["total"]
    logger.info(f"TOTAL STAKED: {total_staked}")

    # USERS STAKED
    resp_all_accounts_kleo = client.rest_client.get(
        f"/cosmwasm/wasm/v1/contract/{STAKING_CONTRACT}/state"
    )
    encoded_resp = json.loads(resp_all_accounts_kleo.decode("utf-8"))

    stakers = []
    for model in encoded_resp["models"]:
        address_long = bytes.fromhex((model["key"])).decode("utf-8")[2:]
        if address_long.startswith("staked"):
            balance = base64.b64decode(model["value"]).decode("utf-8").strip('"')
            address = address_long[15:]

            query_dict = {"staked_balance_at_height": {"address": address}}

            query_data = json_encode(query_dict).encode("UTF8")

            req_user_staked_at_height = QuerySmartContractStateRequest(
                address=STAKING_CONTRACT, query_data=query_data
            )
            res_user_staked_at_height = client.wasm.SmartContractState(
                req_user_staked_at_height
            )
            res_user_staked_at_height_dict = json.loads(
                res_user_staked_at_height.data.decode("utf-8")
            )
            user_staked = res_user_staked_at_height_dict["balance"]

            stakers_dict = {
                "address": address,
                # "balance": balance,
                "reward": str(
                    (int(user_staked) / int(total_staked)) * int(total_rewards)
                ),
            }
            stakers.append(stakers_dict)

    logger.info(f"Computed rev share for {len(stakers)} stakers.")

    if not (os.path.isdir(rev_share_folder)):
        os.makedirs(rev_share_folder, exist_ok=True)

    filename = rev_share_folder / f"rev_share-{datetime.now()}.json"
    with open(filename, "w") as json_file:
        json.dump(stakers, json_file, indent=4)

    logger.info(f"Rev share file is ready: {filename}")


if __name__ == "__main__":
    compute_rev_share()
