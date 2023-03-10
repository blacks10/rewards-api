@click.command()
@click.option("--lp_addr", prompt="Liquidity Pool address")
@click.option("--chain_name", prompt="Chain name [ex. juno]")
def compute_price_feed(lp_addr: str, chain_name: str):
    logger.info(f"Computing Price Feed for $KLEO {total_rewards} rewards.")

    chain_info = get_chain_info(chain_name)
    network_cfg_kwargs = get_network_config_args(chain_info)
    network_cfg = NetworkConfig(**network_cfg_kwargs)
    client = LedgerClient(network_cfg)

    try:
        resp_cum_prices_wynddao = client.rest_client.get(
            f"/cosmwasm/wasm/v1/contract/{lp_addr}/state"
        )

        encoded_resp = json.loads(resp_cum_prices_wynddao.decode("utf-8"))

        logging.info(f"resp: {encoded_resp}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    lp_addr = "juno1dpqgt3ja2kdxs94ltjw9ncdsexts9e3dx5qpnl20zvgdguzjelhqstf8zg"
    chain_name = "juno"
    compute_price_feed(lp_addr, chain_name)()