from bip_utils import Bech32Decoder, Bech32Encoder


def convert_to_juno_address(chain: str, address: str) -> str:
    decoded_juno = Bech32Decoder.Decode(chain, address)
    return Bech32Encoder.Encode("juno", decoded_juno)
