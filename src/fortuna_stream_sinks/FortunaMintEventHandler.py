from fortuna_stream_sinks.Cardano import Cardano
from fortuna_stream_sinks.FortunaBlockMintedEvent import FortunaBlockMintedEvent


class FortunaMintEventHandler:
    @staticmethod
    def is_mint(post_body_json) -> bool:
        if "mint" not in post_body_json:
            return False

        mint_assets_policy = list(filter(lambda mint: mint["policyId"] == "yYH8mOdh47tErjXn2XrmIn9oS8tvUKY2dT2kjg==", post_body_json["mint"]))  # TODO decode to asset1up3fehe0dwpuj4awgcuvl0348vnsexd573fjgq
        if len(mint_assets_policy) != 1:
            return False

        mint_assets = list(filter(lambda mint: mint["name"] == "VFVOQQ==", mint_assets_policy[0]["assets"]))
        if len(mint_assets) != 1:
            return False

        if "outputs" not in post_body_json:
            return False

        outputs_datum = list(filter(lambda output: "datumHash" in output, post_body_json["outputs"]))
        if len(outputs_datum) != 1:
            return False

        output_datum = outputs_datum[0]

        return "datum" in output_datum and \
            "constr" in output_datum["datum"] and \
            "fields" in output_datum["datum"]["constr"] and \
            len(output_datum["datum"]["constr"]["fields"]) == 7 and \
            "bigInt" in output_datum["datum"]["constr"]["fields"][0] and \
            "int" in output_datum["datum"]["constr"]["fields"][0]["bigInt"] and \
            "boundedBytes" in output_datum["datum"]["constr"]["fields"][1] and \
            "bigInt" in output_datum["datum"]["constr"]["fields"][2] and \
            "int" in output_datum["datum"]["constr"]["fields"][2]["bigInt"] and \
            "bigInt" in output_datum["datum"]["constr"]["fields"][3] and \
            "int" in output_datum["datum"]["constr"]["fields"][3]["bigInt"] and \
            "bigInt" in output_datum["datum"]["constr"]["fields"][4] and \
            "int" in output_datum["datum"]["constr"]["fields"][4]["bigInt"] and \
            "bigInt" in output_datum["datum"]["constr"]["fields"][5] and \
            "int" in output_datum["datum"]["constr"]["fields"][5]["bigInt"] and \
            "boundedBytes" in output_datum["datum"]["constr"]["fields"][6]
    
    @staticmethod
    def process_mint(post_body_json) -> FortunaBlockMintedEvent:
        address = FortunaMintEventHandler._get_mint_miner_address(post_body_json)
        mint_amount = FortunaMintEventHandler._get_mint_amount(post_body_json)
        block_number, leading_zeroes, difficulty = FortunaMintEventHandler._get_mint_data(post_body_json)

        return FortunaBlockMintedEvent(block_number, address, mint_amount, leading_zeroes, difficulty)

    @staticmethod
    def _get_mint_miner_address(post_body_json) -> str:
        outputs = list(filter(lambda output: "assets" in output, post_body_json["outputs"]))

        for output in outputs:
            outputs_assets = list(filter(lambda _output: "assets" in _output, output["assets"]))

            for outputs_asset in outputs_assets:
                outputs_assets_assets = list(filter(lambda _output: "name" in _output and _output["name"] == "VFVOQQ==", outputs_asset["assets"]))

                if len(outputs_assets_assets) == 1:
                    return Cardano.get_bech32_address(output["address"])

        return "unknown address"

    @staticmethod
    def _get_mint_amount(post_body_json) -> int:
        mint_assets_policy = list(filter(lambda mint: mint["policyId"] == "yYH8mOdh47tErjXn2XrmIn9oS8tvUKY2dT2kjg==", post_body_json["mint"]))  # TODO decode to asset1up3fehe0dwpuj4awgcuvl0348vnsexd573fjgq
        mint_assets = list(filter(lambda mint: mint["name"] == "VFVOQQ==", mint_assets_policy[0]["assets"]))  # TODO decode

        return int(mint_assets[0]["mintCoin"])

    @staticmethod
    def _get_mint_data(post_body_json) -> (int, int, int):
        outputs_datum = list(filter(lambda output: "datumHash" in output, post_body_json["outputs"]))

        return int(outputs_datum[0]["datum"]["constr"]["fields"][0]["bigInt"]["int"]), \
            int(outputs_datum[0]["datum"]["constr"]["fields"][2]["bigInt"]["int"]), \
            int(outputs_datum[0]["datum"]["constr"]["fields"][3]["bigInt"]["int"])
