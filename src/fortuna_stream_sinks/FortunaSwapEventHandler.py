import json
from fortuna_stream_sinks.Cardano import Cardano
from fortuna_stream_sinks.Transaction import Transaction
from fortuna_stream_sinks.events.FortunaSundaeSwapV3OrderBuy import FortunaSundaeSwapV3OrderBuy


class FortunaSwapEventHandler:
    with open("dexes.json", "r") as dexes_file:
        dexes = json.load(dexes_file)

    @staticmethod
    def contains_sundae_v3_buy_order(post_body_json: dict) -> bool:
        if "outputs" not in post_body_json:
            return False

        for output in post_body_json["outputs"]:
            try:
                for sundae_swap_pool in FortunaSwapEventHandler.dexes["sundae_v3"]:
                    if Cardano.get_bech32_payment_address(output["address"]) == sundae_swap_pool["swap_order_script_address"]:
                        if output["datum"]["payload"]["constr"]["fields"][4]["constr"]["fields"][1]["array"]["items"][0]["boundedBytes"] == "yYH8mOdh47tErjXn2XrmIn9oS8tvUKY2dT2kjg==" and output["datum"]["payload"]["constr"]["fields"][4]["constr"]["fields"][1]["array"]["items"][1]["boundedBytes"] == "VFVOQQ==":
                            return True
            except (KeyError, IndexError):
                continue

        return False

    @staticmethod
    def get_sundae_v3_buy_orders(post_body_json: dict) -> list[FortunaSundaeSwapV3OrderBuy]:
        buy_orders = []

        transaction = Transaction(
            Cardano.get_transaction_hash(post_body_json["hash"]),
            post_body_json["validity"]["start"] if "start" in post_body_json["validity"] else -1,
            post_body_json["validity"]["ttl"] if "ttl" in post_body_json["validity"] else -1,
            Transaction.VERSION,
            json.dumps(post_body_json)
        )

        output_change = next(filter(lambda x: "datum" not in x or "hash" not in x["datum"], post_body_json["outputs"]))
        output_change_address = Cardano.get_bech32_address(output_change["address"])
        buy_order_script_addresses = list(map(lambda x: x["swap_order_script_address"], FortunaSwapEventHandler.dexes["sundae_v3"]))
        buy_order_outputs = list(filter(lambda x: Cardano.get_bech32_payment_address(x["address"]) in buy_order_script_addresses, post_body_json["outputs"]))

        for buy_order_output in buy_order_outputs:
            try:
                if buy_order_output["datum"]["payload"]["constr"]["fields"][4]["constr"]["fields"][1]["array"]["items"][0]["boundedBytes"] == "yYH8mOdh47tErjXn2XrmIn9oS8tvUKY2dT2kjg==" and buy_order_output["datum"]["payload"]["constr"]["fields"][4]["constr"]["fields"][1]["array"]["items"][1]["boundedBytes"] == "VFVOQQ==":
                    in_amount_lovelace = int(buy_order_output["datum"]["payload"]["constr"]["fields"][4]["constr"]["fields"][0]["array"]["items"][2]["bigInt"]["int"])
                    min_out_amount_tuna = int(buy_order_output["datum"]["payload"]["constr"]["fields"][4]["constr"]["fields"][1]["array"]["items"][2]["bigInt"]["int"])

                    buy_orders.append(FortunaSundaeSwapV3OrderBuy(transaction, output_change_address, in_amount_lovelace, min_out_amount_tuna))
            except (KeyError, IndexError):
                continue

        return buy_orders
