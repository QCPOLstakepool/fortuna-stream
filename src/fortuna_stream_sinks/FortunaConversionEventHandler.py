from fortuna_stream_sinks.Cardano import Cardano
from fortuna_stream_sinks.FortunaMintEventHandler import FortunaMintEventHandler
from fortuna_stream_sinks.FortunaV1ToV2ConvertedEvent import FortunaV1ToV2ConvertedEvent


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
    def process_conversion(post_body_json) -> FortunaV1ToV2ConvertedEvent:
        address = FortunaConversionEventHandler._get_conversion_output_address(post_body_json)
        conversion_amount = FortunaConversionEventHandler._get_conversion_amount(post_body_json)

        return FortunaV1ToV2ConvertedEvent(address, conversion_amount)

    @staticmethod
    def _get_conversion_output_address(post_body_json) -> str:
        outputs = list(filter(lambda output: "assets" in output and Cardano.get_bech32_address(output["address"]) != "addr1wye5g0txzw8evz0gddc5lad6x5rs9ttaferkun96gr9wd9sj5y20t", post_body_json["outputs"]))

        for output in outputs:
            outputs_assets = list(filter(lambda _output: "assets" in _output and _output["policyId"] == "yYH8mOdh47tErjXn2XrmIn9oS8tvUKY2dT2kjg==", output["assets"]))

            for outputs_asset in outputs_assets:
                outputs_assets_assets = list(filter(lambda _output: "name" in _output and _output["name"] == "VFVOQQ==", outputs_asset["assets"]))

                if len(outputs_assets_assets) == 1:
                    return Cardano.get_bech32_address(output["address"])

        return "unknown address"

    @staticmethod
    def _get_conversion_amount(post_body_json) -> int:
        mint_assets_policy = list(filter(lambda mint: mint["policyId"] == "yYH8mOdh47tErjXn2XrmIn9oS8tvUKY2dT2kjg==", post_body_json["mint"]))  # TODO decode to asset1up3fehe0dwpuj4awgcuvl0348vnsexd573fjgq
        mint_assets = list(filter(lambda mint: mint["name"] == "VFVOQQ==", mint_assets_policy[0]["assets"]))

        return int(mint_assets[0]["mintCoin"])
