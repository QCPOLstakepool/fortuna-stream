from fortuna_stream_sinks.Cardano import Cardano
from fortuna_stream_sinks.FortunaMintEventHandler import FortunaMintEventHandler
from fortuna_stream_sinks.FortunaConversion import FortunaConversion
from fortuna_stream_sinks.Transaction import Transaction


class FortunaConversionEventHandler:
    @staticmethod
    def is_conversion(post_body_json) -> bool:
        if "mint" not in post_body_json:
            return False

        mint_assets_policy = list(filter(lambda mint: mint["policyId"] == "yYH8mOdh47tErjXn2XrmIn9oS8tvUKY2dT2kjg==", post_body_json["mint"]))  # TODO decode to asset1up3fehe0dwpuj4awgcuvl0348vnsexd573fjgq
        if len(mint_assets_policy) != 1:
            return False

        mint_assets = list(filter(lambda mint: mint["name"] == "VFVOQQ==", mint_assets_policy[0]["assets"]))
        if len(mint_assets) != 1:
            return False

        return not FortunaMintEventHandler.is_mint(post_body_json)
    
    @staticmethod
    def process_conversion(post_body_json) -> FortunaConversion:
        transaction = Transaction(Cardano.get_transaction_hash(post_body_json["hash"]), post_body_json["validity"]["start"] if "start" in post_body_json["validity"] else -1, post_body_json["validity"]["ttl"] if "ttl" in post_body_json["validity"] else -1)
        address = FortunaConversionEventHandler._get_address(post_body_json)
        amount = FortunaConversionEventHandler._get_amount(post_body_json)

        return FortunaConversion(transaction, address, amount, 1, 2)

    @staticmethod
    def _get_address(post_body_json) -> str:
        outputs = list(filter(lambda output: "assets" in output and Cardano.get_bech32_address(output["address"]) != "addr1wye5g0txzw8evz0gddc5lad6x5rs9ttaferkun96gr9wd9sj5y20t", post_body_json["outputs"]))

        for output in outputs:
            outputs_assets = list(filter(lambda _output: "assets" in _output and _output["policyId"] == "yYH8mOdh47tErjXn2XrmIn9oS8tvUKY2dT2kjg==", output["assets"]))

            for outputs_asset in outputs_assets:
                outputs_assets_assets = list(filter(lambda _output: "name" in _output and _output["name"] == "VFVOQQ==", outputs_asset["assets"]))

                if len(outputs_assets_assets) == 1:
                    return Cardano.get_bech32_address(output["address"])

        return "unknown address"

    @staticmethod
    def _get_amount(post_body_json) -> int:
        mint_assets_policy = list(filter(lambda mint: mint["policyId"] == "yYH8mOdh47tErjXn2XrmIn9oS8tvUKY2dT2kjg==", post_body_json["mint"]))  # TODO decode to asset1up3fehe0dwpuj4awgcuvl0348vnsexd573fjgq
        mint_assets = list(filter(lambda mint: mint["name"] == "VFVOQQ==", mint_assets_policy[0]["assets"]))

        return int(mint_assets[0]["mintCoin"])
