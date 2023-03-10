from pycoingecko import CoinGeckoAPI

from kleo_rewards.scripts.costants import IDS, CURRENCIES


class Coingecko:
    # https://www.coingecko.com/en/api/documentation
    def __init__(self):
        api_key = ""
        if len(api_key) > 0:
            self.cg = CoinGeckoAPI(api_key=api_key)
        else:
            self.cg = CoinGeckoAPI()

    def __get_symbols(self):
        values = {}
        for _id in IDS.split(","):
            data = self.cg.get_coin_by_id(_id)
            symbol = data.get("symbol", "")
            values[_id] = symbol
        return values

    def get_prices(self) -> dict:
        return self.cg.get_price(ids=IDS, vs_currencies=CURRENCIES)

    def pretty_prices(self):
        updated_coins = {}
        symbols = self.__get_symbols()
        for k, v in self.get_prices().items():
            symbol = str(symbols.get(k, k)).upper()
            updated_coins[symbol] = {"coingecko-id": k, "prices": v}
        return updated_coins
