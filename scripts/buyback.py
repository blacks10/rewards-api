import json
import os
from datetime import datetime
from pathlib import Path

import click
from bip_utils import (
    Bech32Decoder,
    Ed25519PublicKey,
    Ed25519PrivateKey,
    Bip44Coins,
    Bip32Slip10Secp256k1,
    Bech32Encoder,
    Hash160,
    Bip32Slip10Ed25519,
    Base58Encoder,
    Bip32KholawEd25519,
)
from bip_utils.addr.addr_key_validator import AddrKeyValidator
from cosmpy.crypto.address import Address
from cosmpy.protos.cosmos.staking.v1beta1.query_pb2 import (
    QueryValidatorDelegationsRequest,
    QueryValidatorRequest,
)
from loguru import logger
from cosmpy.aerial.config import NetworkConfig
from scripts.client import get_chain_info, get_network_config_args, LedgerClientV2
from scripts.utils import convert_to_juno_address

validator_info_folder = Path(__file__).parent / "validator_info"
buyback_folder = Path(__file__).parent / "buyback_folder"


# buyback formula
# (users_delegated_chain_token/total_delegated_chain_token)*kleo_allocated_to_chain


@click.command()
@click.option("--kleo_allocated_to_chain", prompt="Total kleo allocated to chain")
def compute_buyback(kleo_allocated_to_chain: int):
    logger.info(f"Computing buyback.")
    filename = validator_info_folder / "validator_info.json"
    with open(filename) as json_file:
        validator_info_dict = json.load(json_file)

    total_stakers = []
    for validator_info in validator_info_dict:
        chain_info = get_chain_info(validator_info["chain_name"])
        network_cfg_kwargs = get_network_config_args(chain_info)
        network_cfg = NetworkConfig(**network_cfg_kwargs)
        client = LedgerClientV2(network_cfg)

        # total_delegated_chain_token
        req_validator = QueryValidatorRequest(
            validator_addr=validator_info["validator_address"]
        )
        resp_validator = client.staking.Validator(req_validator)

        total_delegated_chain_token = resp_validator.validator.tokens
        logger.info(
            f"Total delegated token in the {validator_info['chain_name']} chain: {total_delegated_chain_token} "
        )

        req_delegators = QueryValidatorDelegationsRequest(
            validator_addr=validator_info["validator_address"]
        )
        res_delegators = client.staking.ValidatorDelegations(req_delegators)

        # users_delegated_chain_token
        stakers = []
        for delegation in res_delegators.delegation_responses:
            users_delegated_chain_token = delegation.balance.amount
            stakers_dict = {
                "address": convert_to_juno_address(
                    validator_info["chain_id"], delegation.delegation.delegator_address
                ),
                "amount": str(
                    int(
                        (
                            int(users_delegated_chain_token)
                            / int(total_delegated_chain_token)
                        )
                        * int(kleo_allocated_to_chain)
                    )
                ),
            }
            stakers.append(stakers_dict)

        logger.info(
            f"Computed buyback for {len(stakers)} stakers in the {validator_info['chain_name']} chain."
        )
        total_stakers.extend(stakers)

    logger.info(f"Computed buyback for {len(total_stakers)} stakers.")

    if not (os.path.isdir(buyback_folder)):
        os.makedirs(buyback_folder, exist_ok=True)

    filename = buyback_folder / f"buyback-{datetime.now()}.json"
    with open(filename, "w") as json_file:
        json.dump(total_stakers, json_file, indent=4)

    logger.info(f"Buyback file is ready: {filename}")


if __name__ == "__main__":
    compute_buyback()
