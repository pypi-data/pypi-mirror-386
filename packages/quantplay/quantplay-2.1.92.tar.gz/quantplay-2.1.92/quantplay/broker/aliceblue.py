import codecs
import copy
import json
import pickle
import threading
import time
import traceback
from queue import Queue
from typing import Any, Literal

import polars as pl
import requests
import websocket  # type: ignore
from pya3 import Aliceblue as Alice
from pya3 import OrderType as AliceOrderType
from pya3 import ProductType as AliceProductType
from pya3 import TransactionType as AliceTransactionType
from retrying import retry  # type: ignore

from quantplay.broker.generics.broker import Broker
from quantplay.exception.exceptions import (
    InvalidArgumentException,
    QuantplayOrderPlacementException,
    RetryableException,
    TokenException,
    retry_exception,
)
from quantplay.model.broker import (
    MarginsResponse,
    ModifyOrderRequest,
    UserBrokerProfileResponse,
)
from quantplay.model.generics import (
    ExchangeType,
    OrderTypeType,
    ProductType,
    TransactionType,
)
from quantplay.model.order_event import OrderUpdateEvent
from quantplay.utils.constant import Constants, OrderType
from quantplay.utils.pickle_utils import InstrumentData
from quantplay.wrapper.aws.s3 import S3Utils

logger = Constants.logger


class Aliceblue(Broker):
    websocket_url = "wss://ant.aliceblueonline.com/order-notify/websocket"
    create_websocket_url = "https://ant.aliceblueonline.com/order-notify/ws/createWsToken"

    @retry(
        wait_exponential_multiplier=3000,
        wait_exponential_max=10000,
        stop_max_attempt_number=2,
        retry_on_exception=retry_exception,
    )
    def __init__(
        self,
        user_id: str | None = None,
        api_key: str | None = None,
        order_updates: Queue[OrderUpdateEvent] | None = None,
        client: str | None = None,
        load_instrument: bool = True,
    ) -> None:
        super().__init__()
        self.order_updates = order_updates

        try:
            if client:
                self.set_client(client)
            else:
                if user_id is None or api_key is None:
                    raise InvalidArgumentException(
                        "Mandatory fields [user_id/api_key] are missing"
                    )
                self.alice = Alice(
                    user_id=user_id,
                    api_key=api_key,
                )
                response = self.alice.get_session_id()

                if response.get("sessionID") is None:
                    if "emsg" in response:
                        if response["emsg"].lower() == "invalid input":
                            response["emsg"] = "Invalid broker credentials"
                        raise InvalidArgumentException(response["emsg"])
                    raise InvalidArgumentException(f"Invalid API Key {api_key}")

        except (InvalidArgumentException, TokenException):
            raise

        except Exception as e:
            raise RetryableException(str(e))

        self.user_id = self.alice.user_id

        if load_instrument:
            self.load_instrument()

    def set_client(self, serialized_client: str):
        try:
            self.alice: Alice = pickle.loads(
                codecs.decode(serialized_client.encode(), "base64")
            )
        except Exception:
            raise TokenException("Session expired")

    def get_quantplay_symbol(self, symbol: str):
        if "-EQ" in symbol:
            return symbol.replace("-EQ", "")
        if symbol in self.broker_symbol_map:
            return self.broker_symbol_map[symbol]
        return symbol

    def get_symbol(self, symbol: str, exchange: ExchangeType | None = None):
        if exchange == "NSE":
            if "-EQ" not in symbol:
                return f"{symbol}-EQ"

        elif symbol not in self.quantplay_symbol_map:
            return symbol

        return self.quantplay_symbol_map[symbol]

    def load_instrument(self, file_name: str | None = None):
        try:
            instrument_data_instance = InstrumentData.get_instance()
            if instrument_data_instance is not None:
                self.symbol_data = instrument_data_instance.load_data(
                    "aliceblue_instruments"
                )
            Constants.logger.info("[LOADING_INSTRUMENTS] loading data from cache")
        except Exception:
            self.instrument_data = S3Utils.read_csv(
                "quantplay-market-data", "symbol_data/aliceblue_instruments.csv"
            )
            self.initialize_symbol_data(save_as="aliceblue_instruments")

        self.initialize_broker_symbol_map()

    def get_transaction_type(
        self,
        transaction_type: Literal[
            "BUY", "SELL", "B", "S", AliceTransactionType.Buy, AliceTransactionType.Sell
        ],
    ):
        if (
            transaction_type == "BUY"
            or transaction_type == AliceTransactionType.Buy
            or transaction_type == "B"
        ):
            return AliceTransactionType.Buy
        elif (
            transaction_type == "SELL"
            or transaction_type == AliceTransactionType.Sell
            or transaction_type == "S"
        ):
            return AliceTransactionType.Sell

        raise InvalidArgumentException(
            f"transaction type {transaction_type} not supported for trading"
        )

    def get_order_type(
        self,
        order_type: (
            OrderTypeType
            | Literal[
                AliceOrderType.Market,
                AliceOrderType.StopLossLimit,
                AliceOrderType.StopLossMarket,
                AliceOrderType.Limit,
            ]
        ),
    ):
        if order_type == OrderType.market or order_type == AliceOrderType.Market:
            return AliceOrderType.Market
        elif order_type == OrderType.sl or order_type == AliceOrderType.StopLossLimit:
            return AliceOrderType.StopLossLimit
        elif order_type == OrderType.slm or order_type == AliceOrderType.StopLossMarket:
            return AliceOrderType.StopLossMarket
        elif order_type == OrderType.limit or order_type == AliceOrderType.Limit:
            return AliceOrderType.Limit

        return order_type

    def get_product(self, product: ProductType):
        if product == "NRML":
            return AliceProductType.Normal
        elif product == "CNC":
            return AliceProductType.Delivery
        elif product == "MIS":
            return AliceProductType.Intraday
        elif product in [
            AliceProductType.BracketOrder,
            AliceProductType.CoverOrder,
            AliceProductType.Delivery,
            AliceProductType.Normal,
            AliceProductType.Intraday,
        ]:
            return product

        raise InvalidArgumentException(f"Product {product} not supported for trading")

    def place_order(
        self,
        tradingsymbol: str,
        exchange: ExchangeType,
        quantity: int,
        order_type: OrderTypeType,
        transaction_type: TransactionType,
        tag: str | None,
        product: ProductType,
        price: float,
        trigger_price: float | None = None,
    ):
        try:
            if trigger_price == 0:
                trigger_price = None
            if trigger_price is not None:
                trigger_price = float(trigger_price)

            aliceblue_order_type = self.get_order_type(order_type)
            aliceblue_product = self.get_product(product)
            tradingsymbol = self.get_symbol(tradingsymbol)

            instrument = self.alice.get_instrument_by_symbol(exchange, tradingsymbol)

            response = self.invoke_aliceblue_api(
                self.alice.place_order,
                transaction_type=self.get_transaction_type(transaction_type),
                product_type=aliceblue_product,
                instrument=instrument,
                order_type=aliceblue_order_type,
                quantity=quantity,
                price=float(price),
                trigger_price=trigger_price,
                order_tag=tag,
            )
            Constants.logger.info(f"[PLACE_ORDER_RESPONSE] {response}")
            return response["NOrdNo"]
        except Exception as e:
            traceback.print_exc()
            exception_message = f"Order placement failed [{str(e)}]"
            raise QuantplayOrderPlacementException(exception_message)

    def ltp(self, exchange: ExchangeType, tradingsymbol: str) -> float:
        tradingsymbol = self.get_symbol(tradingsymbol, exchange=exchange)
        try:
            inst = self.invoke_aliceblue_api(
                self.alice.get_instrument_by_symbol,
                exchange=exchange,
                symbol=tradingsymbol,
            )

        except Exception:
            inst = self.invoke_aliceblue_api(
                self.alice.get_instrument_by_symbol,
                exchange=exchange,
                symbol=tradingsymbol.replace("-EQ", ""),
            )
        info = self.invoke_aliceblue_api(self.alice.get_scrip_info, instrument=inst)

        return float(info["LTP"])

    @retry(
        wait_exponential_multiplier=3000,
        wait_exponential_max=10000,
        stop_max_attempt_number=3,
    )
    def modify_order(self, order: ModifyOrderRequest) -> str:
        data = copy.deepcopy(order)
        order_id = data["order_id"]
        try:
            order_history = self.invoke_aliceblue_api(
                self.alice.get_order_history,
                nextorder=order_id,
            )

            # TODO: None,str Raise
            exchange = order_history["Exchange"]
            token = int(order_history["token"])
            product_type = self.get_product(order_history["Pcode"])
            quantity = order_history["Qty"]

            order_type = order_history["Prctype"]
            if "order_type" in data:
                order_type = data["order_type"]

            aliceblue_order_type = (
                self.get_order_type(order_type)
                if order_type
                else order_history["Prctype"]
            )

            transaction_type = order_history["Trantype"]
            if "transaction_type" in data:
                transaction_type = data["transaction_type"]
            transaction_type = self.get_transaction_type(transaction_type)

            trigger_price = None
            if "trigger_price" in data and data["trigger_price"] is not None:
                trigger_price = float(data["trigger_price"])

            response = self.alice.modify_order(
                instrument=self.alice.get_instrument_by_token(exchange, token),
                transaction_type=transaction_type,
                order_id=order_id,
                product_type=product_type,
                order_type=aliceblue_order_type,
                price=float(data.get("price", 0)),
                trigger_price=trigger_price,
                quantity=quantity,
            )
            logger.info(f"[MODIFY_ORDER_RESPONSE] [{order_id}]  response [{response}]")
        except Exception as e:
            traceback.print_exc()
            Constants.logger.error(
                f"[MODIFY_ORDER_FAILED] {data} with exception {str(e)}"
            )
        return order_id

    def modify_price(
        self,
        order_id: str,
        price: float,
        trigger_price: float | None = None,
        order_type: OrderTypeType | None = None,
    ):
        data: ModifyOrderRequest = {
            "order_id": order_id,
            "price": price,
        }
        if order_type is not None:
            data["order_type"] = order_type

        if trigger_price is not None and trigger_price > 0:
            data["trigger_price"] = trigger_price
        else:
            data["trigger_price"] = None

        self.modify_order(data)

    def cancel_order(self, order_id: str, variety: str | None = None) -> None:
        self.invoke_aliceblue_api(self.alice.cancel_order, nestordernmbr=order_id)

    def profile(self):
        profile = self.invoke_aliceblue_api(self.alice.get_profile)
        response: UserBrokerProfileResponse = {
            "user_id": self.alice.user_id,
            "full_name": profile["accountName"],
            "email": profile["emailAddr"],
        }

        return response

    @retry(
        wait_exponential_multiplier=3000,
        wait_exponential_max=10000,
        stop_max_attempt_number=3,
    )
    def holdings(self, add_ltp: bool = True) -> pl.DataFrame:
        holdings_response = self.invoke_aliceblue_api(self.alice.get_holding_positions)

        if (
            holdings_response is None
            or "HoldingVal" not in holdings_response
            or len(holdings_response["HoldingVal"]) == 0
        ):
            return pl.DataFrame(schema=self.holidings_schema)

        holdings_response = holdings_response["HoldingVal"]

        holdings_df = pl.from_dicts(holdings_response)
        holdings_df = holdings_df.filter(pl.col("ExchSeg1") == "NSE")
        holdings_df = holdings_df.rename(
            {
                "Nsetsym": "tradingsymbol",
                "Token1": "token",
                "Price": "average_price",
                "HUqty": "quantity",
            },
        )
        holdings_df = holdings_df.with_columns(
            pl.col("tradingsymbol").str.replace("-EQ", "").alias("tradingsymbol")
        )
        holdings_df = holdings_df.with_columns(pl.lit("NSE").alias("exchange"))
        holdings_df = holdings_df.with_columns(
            pl.struct(["exchange", "tradingsymbol"])
            .map_elements(
                lambda x: int(self.ltp(x["exchange"], x["tradingsymbol"])),
                return_dtype=pl.Float64,
            )
            .alias("price")
        )
        holdings_df = holdings_df.with_columns(
            pl.col("quantity").cast(pl.Int64).alias("quantity"),
            pl.col("average_price").cast(pl.Float64).alias("average_price"),
            pl.lit(0).alias("pledged_quantity"),
            pl.col("tradingsymbol").str.replace("-EQ", "").alias("tradingsymbol"),
        )

        holdings_df = holdings_df.with_columns(
            (pl.col("quantity") * pl.col("price")).alias("value"),
            (pl.col("quantity") * pl.col("average_price")).alias("buy_value"),
            (pl.col("quantity") * pl.col("price")).alias("current_value"),
            ((pl.col("price") / pl.col("average_price") - 1) * 100).alias("pct_change"),
        )

        return holdings_df[list(self.holidings_schema.keys())].cast(self.holidings_schema)

    @retry(
        wait_exponential_multiplier=3000,
        wait_exponential_max=10000,
        stop_max_attempt_number=3,
    )
    def positions(self, drop_cnc: bool = True, add_ltp: bool = True) -> pl.DataFrame:
        positions_response = self.invoke_aliceblue_api(self.alice.get_netwise_positions)

        if not isinstance(positions_response, list):
            return pl.DataFrame(schema=self.positions_schema)

        positions_df = pl.from_dicts(positions_response)  # type: ignore

        positions_df = positions_df.with_columns(
            (
                pl.col("realisedprofitloss").cast(pl.Float64)
                + pl.col("unrealisedprofitloss").cast(pl.Float64)
            ).alias("pnl")
        )

        positions_df = positions_df.rename(
            {
                "LTP": "ltp",
                "Tsym": "tradingsymbol",
                "Opttype": "option_type",
                "Pcode": "product",
                "netsellqty": "sell_quantity",
                "netbuyqty": "buy_quantity",
                "Exchange": "exchange",
                "Token": "token",
                "netbuyamt": "buy_value",
                "netSellamt": "sell_value",
            }
        )

        positions_df = positions_df.with_columns(
            pl.col("ltp").cast(pl.Float64),
            pl.col("buy_quantity").cast(pl.Int32),
            pl.col("sell_quantity").cast(pl.Int32),
        )

        positions_df = positions_df.with_columns(
            (pl.col("buy_quantity") - pl.col("sell_quantity")).alias("quantity")
        )

        positions_df = positions_df.with_columns(
            pl.when(pl.col("quantity") > 0)
            .then(pl.col("NetBuyavgprc"))
            .otherwise(pl.col("NetSellavgprc"))
            .alias("average_price")
        )
        positions_df = positions_df.with_columns(
            pl.when(pl.col("quantity") == 0)
            .then(0)
            .otherwise(pl.col("average_price"))
            .alias("average_price")
        )

        return positions_df[list(self.positions_schema.keys())].cast(
            self.positions_schema
        )

    def get_exchange(self, exchange: ExchangeType) -> Any:
        return exchange

    def orders(self, tag: str | None = None, add_ltp: bool = True) -> pl.DataFrame:
        orders_response: list[dict[str, Any]] | Any = self.invoke_aliceblue_api(
            self.alice.order_data
        )

        if not isinstance(orders_response, list):
            return pl.DataFrame(schema=self.orders_schema)

        if len(orders_response) == 0:  # type: ignore
            return pl.DataFrame(schema=self.orders_schema)

        orders_df = pl.from_dicts(
            orders_response,  # type: ignore
            schema={
                "ltp": pl.Float64,
                "rorgqty": pl.Int32,
                "Fillshares": pl.Int32,
                "Avgprc": pl.Float64,
                "Trsym": pl.String,
                "Nstordno": pl.String,
                "accountId": pl.String,
                "Exchange": pl.String,
                "Pcode": pl.String,
                "Trantype": pl.String,
                "Qty": pl.String,
                "Trgprc": pl.String,
                "Prc": pl.String,
                "OrderedTime": pl.String,
                "orderentrytime": pl.String,
                "Prctype": pl.String,
                "Status": pl.String,
                "token": pl.String,
                "RejReason": pl.String,
                "remarks": pl.String,
            },
        ).rename(
            {
                "Trsym": "tradingsymbol",
                "Nstordno": "order_id",
                "accountId": "user_id",
                "Exchange": "exchange",
                "Pcode": "product",
                "Trantype": "transaction_type",
                "Qty": "quantity",
                "Trgprc": "trigger_price",
                "Prc": "price",
                "OrderedTime": "update_timestamp",
                "orderentrytime": "order_timestamp",
                "Prctype": "order_type",
                "Status": "status",
                "rorgqty": "pending_quantity",
                "Fillshares": "filled_quantity",
                "Avgprc": "average_price",
                "remarks": "tag",
                "RejReason": "status_message",
            }
        )

        if tag:
            orders_df = orders_df.filter(pl.col("tag") == tag)

        if add_ltp:
            positions = self.positions()
            positions = positions.sort("product").group_by("tradingsymbol").head(1)

            orders_df = orders_df.drop(["ltp"]).join(
                positions.select(["tradingsymbol", "ltp"]), on="tradingsymbol", how="left"
            )

        orders_df = orders_df.with_columns(
            pl.when(pl.col("transaction_type") == "S")
            .then(pl.lit("SELL"))
            .when(pl.col("transaction_type") == "B")
            .then(pl.lit("BUY"))
            .otherwise(pl.col("transaction_type"))
            .alias("transaction_type"),
            pl.col("order_timestamp")
            .str.to_datetime("%b %d %Y %H:%M:%S")
            .alias("order_timestamp"),
            pl.col("update_timestamp")
            .str.to_datetime("%d/%m/%Y %H:%M:%S")
            .alias("update_timestamp"),
            pl.when(pl.col("status") == "open")
            .then(pl.lit("OPEN"))
            .when(pl.col("status") == "trigger pending")
            .then(pl.lit("TRIGGER PENDING"))
            .when(pl.col("status") == "rejected")
            .then(pl.lit("REJECTED"))
            .when(pl.col("status") == "cancelled")
            .then(pl.lit("CANCELLED"))
            .when(pl.col("status") == "complete")
            .then(pl.lit("COMPLETE"))
            .otherwise(pl.col("status"))
            .alias("status"),
            pl.when(pl.col("order_type") == "MKT")
            .then(pl.lit(OrderType.market))
            .when(pl.col("order_type") == "L")
            .then(pl.lit(OrderType.limit))
            .when(pl.col("order_type") == "SL")
            .then(pl.lit(OrderType.sl))
            .otherwise(pl.col("order_type"))
            .alias("order_type"),
            pl.lit("regular").alias("variety"),
            (
                pl.col("ltp") * pl.col("filled_quantity")
                - pl.col("average_price") * pl.col("filled_quantity")
            )
            .mul(pl.when(pl.col("transaction_type") == "SELL").then(-1).otherwise(1))
            .alias("pnl"),
            pl.col("status_message").alias("status_message_raw"),
            pl.col("filled_quantity").fill_null(strategy="zero"),
            pl.col("pending_quantity").fill_null(strategy="zero"),
            pl.col("average_price").fill_null(strategy="zero"),
        )

        return orders_df.select(list(self.orders_schema.keys())).cast(self.orders_schema)

    def margins(self) -> MarginsResponse:
        margins = self.invoke_aliceblue_api(self.alice.get_balance)
        if margins is None:
            return {
                "margin_used": 0.0,
                "total_balance": 0.0,
                "margin_available": 0.0,
                "cash": 0,
            }

        margins = [a for a in margins if a["segment"] == "ALL"][0]

        return {
            "margin_used": float(margins["cncMarginUsed"]),
            "total_balance": float(margins["net"]) + float(margins["cncMarginUsed"]),
            "margin_available": float(margins["net"]),
            "cash": 0,
        }

    def invoke_aliceblue_api(self, fn: Any, *args: Any, **kwargs: Any) -> Any:
        try:
            response = fn(*args, **kwargs)

            if response is None:
                raise InvalidArgumentException(
                    "Invalid data response. Aliceblue sent incorrect data, Please check."
                )

            if "emsg" in response and "expired" in response["emsg"].lower():
                raise TokenException("Session expired")
            elif "emsg" in response and "unauthorized" in response["emsg"].lower():
                raise TokenException("Session expired")
            elif (
                "stat" in response
                and response["stat"].lower() == "not_ok"
                and (
                    "no data" in response["emsg"]
                    or "401" in response["emsg"]
                    or "404" in response["emsg"]
                )
            ):
                return None

            elif "stat" in response and response["stat"].lower() == "not_ok":
                raise InvalidArgumentException(response["emsg"])

            return response

        except (TokenException, InvalidArgumentException):
            raise

        except Exception:
            traceback.print_exc()
            raise RetryableException("Failed to fetch data from Aliceblue")

    def create_websocket_token(self):
        user_token = self.alice.get_session_id()
        session_ID = user_token["sessionID"]
        headers = {
            "Authorization": "Bearer Token" + " " + session_ID,
            "Content-Type": "application/json",
        }
        response = requests.request("GET", self.create_websocket_url, headers=headers)
        parse_data = response.json()
        websocket_Token = parse_data["result"][0]["orderToken"]
        return websocket_Token

    def handle_order_update(self, order: dict[str, str]):
        try:
            out_order: OrderUpdateEvent = {
                "placed_by": order["actid"],
                "tag": order["remarks"],
                "order_id": order["norenordno"],
                "exchange": order["exch"],
                "tradingsymbol": order["tsym"],
                "status": order["status"],
                "order_type": order["prctyp"],
                "price": float(order["prc"]),
                "exchange_order_id": order["norenordno"],
                "transaction_type": order["trantype"],
                "product": order["pcode"],
                "quantity": int(order["qty"]),
            }  # type: ignore

            if out_order["exchange"] == "NSE":
                out_order["tradingsymbol"] = out_order["tradingsymbol"].replace("-EQ", "")

            elif out_order["exchange"] in ["NFO", "MCX"]:
                out_order["tradingsymbol"] = self.broker_symbol_map[
                    out_order["tradingsymbol"]
                ]

            if order["prctyp"] == "LMT":
                out_order["order_type"] = "LIMIT"
            elif order["prctyp"] == "MKT":
                out_order["order_type"] = "MARKET"
            elif order["prctyp"] == "SL-LMT":
                out_order["order_type"] = "SL"

            if order["pcode"] == "M":
                out_order["product"] = "NRML"
            elif order["pcode"] == "C":
                out_order["product"] = "CNC"
            elif order["pcode"] == "I":
                out_order["product"] = "MIS"

            if order["trantype"] == "S":
                out_order["transaction_type"] = "SELL"
            elif order["trantype"] == "B":
                out_order["transaction_type"] = "BUY"
            else:
                logger.error(
                    "[UNKNOW_VALUE] Aliceblue transaction type {} not supported".format(
                        order["trantype"]
                    )
                )

            if "trgprc" in order:
                out_order["trigger_price"] = float(order["trgprc"])
            else:
                out_order["trigger_price"] = None

            if order["status"] == "TRIGGER_PENDING":
                out_order["status"] = "TRIGGER PENDING"
            elif order["status"] == "CANCELED":
                out_order["status"] = "CANCELLED"

            logger.info(f"[ORDER_FEED] {out_order}")
            if self.order_updates:
                self.order_updates.put(out_order)

        except Exception as e:
            logger.error("[ORDER_UPDATE_PROCESSING_FAILED] {}".format(e))
            traceback.print_exc()

    def start_order_websocket(self) -> None:
        ws_token = self.create_websocket_token()
        print(f"{self.user_id}: WebSocket connection established.")
        headers = {"Content-Type": "application/json"}
        payload = {"orderToken": ws_token, "userId": self.user_id}
        session_data = json.dumps(payload)

        stop_event = threading.Event()

        def on_message(ws: websocket.WebSocket, message: Any) -> None:
            order = json.loads(message)

            if order.get("status", "") == "Ok":
                return

            if order["t"] == "om":
                self.handle_order_update(order)

        def on_error(ws: websocket.WebSocket, error: Any) -> None:
            if type(ws) is not websocket.WebSocketApp:  # type: ignore
                error = ws

            traceback.print_exc()
            logger.error(f"{self.user_id}: WebSocket Error. Reason: {error}")

        def on_close(
            ws: websocket.WebSocket, close_status_code: int, close_msg: str
        ) -> None:
            traceback.print_exc()
            logger.error(
                f"{self.user_id}: WebSocket Closed. Status code: {close_status_code}, Reason: {close_msg}"
            )

            time.sleep(2)

            stop_event.set()
            self.stream_order_data()

            return

        def on_open(ws: websocket.WebSocket) -> None:
            print(f"{self.user_id}: WebSocket Connection Opened")
            ws.send(session_data)
            threading.Thread(
                target=heart_beat_connection, args=(ws,), daemon=True
            ).start()

        def heart_beat_connection(ws: websocket.WebSocket) -> None:
            while not stop_event.is_set():
                try:
                    payload = {"heartbeat": "h", "userId": self.user_id}
                    hearbeat_data = json.dumps(payload)
                    ws.send(hearbeat_data)
                    time.sleep(55)

                except websocket.WebSocketConnectionClosedException:
                    break

        # Create the WebSocket connection
        ws = websocket.WebSocketApp(
            self.websocket_url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open,
            header=headers,  # Pass headers if required
        )
        ws.run_forever()  # type: ignore

    def stream_order_data(self) -> None:
        thread = threading.Thread(target=self.start_order_websocket, daemon=True)
        thread.start()
