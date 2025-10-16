"""

_국"
"""



import requests

import hashlib

import json

from typing import Dict, List, Optional

from datetime import datetime, timedelta

from decimal import Decimal

import logging



from services.brokerage_connector import BrokerageAPIBase, AccountInfo, StockPrice

from models.trading_schemas import Order, TradeResult



logger = logging.getLogger(__name__)





class KoreaInvestmentAPI(BrokerageAPIBase):

    """

    _국"
    """

    

    # API Base URLs

    BASE_URL_REAL = "https://openapi.koreainvestment.com:9443"

    BASE_URL_VIRTUAL = "https://openapivts.koreainvestment.com:29443"

    

    def __init__(

        self,

        app_key: str,

        app_secret: str,

        account_number: str,

        account_product_code: str = "01",

        use_virtual: bool = True

    ):

        """

        Initialize Korea Investment API client

        

        Args:

            app_key: Application key from Korea Investment

            app_secret: Application secret key

            account_number: Trading account number (8 digits)

            account_product_code: Account product code (default: "01")

            use_virtual: Use virtual trading server (default: True)

        """

        credentials = {

            "app_key": app_key,

            "app_secret": app_secret,

            "account_number": account_number,

            "account_product_code": account_product_code

        }

        super().__init__(credentials)

        

        self.base_url = self.BASE_URL_VIRTUAL if use_virtual else self.BASE_URL_REAL

        self.use_virtual = use_virtual

        

    def authenticate(self) -> bool:

        """

        OAuth 2.0 authentication with Korea Investment API

        

        Returns:

            bool: True if authentication successful

            

        Requirements: 11.1

        """

        try:

            url = f"{self.base_url}/oauth2/tokenP"

            

            headers = {

                "content-type": "application/json"

            }

            

            body = {

                "grant_type": "client_credentials",

                "appkey": self.credentials["app_key"],

                "appsecret": self.credentials["app_secret"]

            }

            

            response = requests.post(url, headers=headers, json=body, timeout=10)

            response.raise_for_status()

            

            data = response.json()

            

            self.access_token = data.get("access_token")

            expires_in = data.get("expires_in", 86400)  # Default 24 hours

            

            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)

            self.is_authenticated = True

            

            logger.info(

                f"Korea Investment API authenticated successfully. "

                f"Token expires at {self.token_expires_at}"

            )

            

            return True

            

        except requests.exceptions.RequestException as e:

            logger.error(f"Authentication failed: {e}")

            self.is_authenticated = False

            return False

    

    def get_stock_price(self, symbol: str) -> StockPrice:

        """

        Get real-time stock price information

        

        Args:

            symbol: Stock code (e.g., "005930" for Samsung Electronics)

            

        Returns:

            StockPrice: Current price information

            

        Requirements: 11.2

        """

        self._ensure_authenticated()

        self._refresh_token_if_needed()

        

        try:

            url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"

            

            headers = self._get_headers(tr_id="FHKST01010100")

            

            params = {

                "FID_COND_MRKT_DIV_CODE": "J",  # Market division (J: KOSPI/KOSDAQ)

                "FID_INPUT_ISCD": symbol

            }

            

            response = requests.get(url, headers=headers, params=params, timeout=10)

            response.raise_for_status()

            

            data = response.json()

            

            if data.get("rt_cd") != "0":

                raise ValueError(f"API Error: {data.get('msg1', 'Unknown error')}")

            

            output = data.get("output", {})

            

            return StockPrice(

                symbol=symbol,

                price=Decimal(output.get("stck_prpr", "0")),  # _재가"

                volume=int(output.get("acml_vol", "0")),  # _적 거래"
                open_price=Decimal(output.get("stck_oprc", "0")),  # _�"
                high_price=Decimal(output.get("stck_hgpr", "0")),  # 고�?

                low_price=Decimal(output.get("stck_lwpr", "0")),  # _가"

                timestamp=datetime.now()

            )

            

        except Exception as e:

            logger.error(f"Failed to get stock price for {symbol}: {e}")

            raise



    def get_account_balance(self) -> AccountInfo:

        """

        Get account balance and total assets

        

        Returns:

            AccountInfo: Account information

            

        Requirements: 11.6

        """

        self._ensure_authenticated()

        self._refresh_token_if_needed()

        

        try:

            url = f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-psbl-order"

            

            headers = self._get_headers(

                tr_id="VTTC8908R" if self.use_virtual else "TTTC8908R"

            )

            

            params = {

                "CANO": self.credentials["account_number"],

                "ACNT_PRDT_CD": self.credentials["account_product_code"],

                "PDNO": "",  # Empty for account inquiry

                "ORD_UNPR": "",

                "ORD_DVSN": "01",

                "CMA_EVLU_AMT_ICLD_YN": "Y",

                "OVRS_ICLD_YN": "N"

            }

            

            response = requests.get(url, headers=headers, params=params, timeout=10)

            response.raise_for_status()

            

            data = response.json()

            

            if data.get("rt_cd") != "0":

                raise ValueError(f"API Error: {data.get('msg1', 'Unknown error')}")

            

            output = data.get("output", {})

            

            return AccountInfo(

                account_number=self.credentials["account_number"],

                balance=Decimal(output.get("dnca_tot_amt", "0")),
                available_cash=Decimal(output.get("ord_psbl_cash", "0")),
                total_assets=Decimal(output.get("tot_evlu_amt", "0"))
            )
        except Exception as e:
            logger.error(f"Failed to get account balance: {e}")

            raise

    

    def get_account_holdings(self) -> List[Dict]:

        """

        Get list of currently held stocks

        

        Returns:

            List[Dict]: Holdings information

            

        Requirements: 11.6

        """

        self._ensure_authenticated()

        self._refresh_token_if_needed()

        

        try:

            url = f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-balance"

            

            headers = self._get_headers(

                tr_id="VTTC8434R" if self.use_virtual else "TTTC8434R"

            )

            

            params = {

                "CANO": self.credentials["account_number"],

                "ACNT_PRDT_CD": self.credentials["account_product_code"],

                "AFHR_FLPR_YN": "N",

                "OFL_YN": "",

                "INQR_DVSN": "02",

                "UNPR_DVSN": "01",

                "FUND_STTL_ICLD_YN": "N",

                "FNCG_AMT_AUTO_RDPT_YN": "N",

                "PRCS_DVSN": "01",

                "CTX_AREA_FK100": "",

                "CTX_AREA_NK100": ""

            }

            

            response = requests.get(url, headers=headers, params=params, timeout=10)

            response.raise_for_status()

            

            data = response.json()

            

            if data.get("rt_cd") != "0":

                raise ValueError(f"API Error: {data.get('msg1', 'Unknown error')}")

            

            holdings = []
            for item in data.get("output1", []):
                holdings.append({
                    "symbol": item.get("pdno", ""),
                    "name": item.get("prdt_name", ""),
                    "quantity": int(item.get("hldg_qty", "0")),
                    "average_price": Decimal(item.get("pchs_avg_pric", "0")),
                    "current_price": Decimal(item.get("prpr", "0")),
                    "evaluation_amount": Decimal(item.get("evlu_amt", "0")),
                    "profit_loss": Decimal(item.get("evlu_pfls_amt", "0")),
                    "profit_loss_rate": Decimal(item.get("evlu_pfls_rt", "0"))
                })
            return holdings
        except Exception as e:
            logger.error(f"Failed to get account holdings: {e}")

            raise



    def place_order(self, order: Order) -> TradeResult:

        """

        Place a buy or sell order

        

        Args:

            order: Order details

            

        Returns:

            TradeResult: Order execution result

            

        Requirements: 11.1

        """

        self._ensure_authenticated()

        self._refresh_token_if_needed()

        

        try:

            url = f"{self.base_url}/uapi/domestic-stock/v1/trading/order-cash"

            

            # Determine transaction ID based on order type

            if order.trade_type == "BUY":

                tr_id = "VTTC0802U" if self.use_virtual else "TTTC0802U"

            else:  # SELL

                tr_id = "VTTC0801U" if self.use_virtual else "TTTC0801U"

            

            headers = self._get_headers(tr_id=tr_id)

            

            # Order division code

            # 00: 지_�"
            ord_dvsn = "01" if order.order_type == "MARKET" else "00"

            

            body = {

                "CANO": self.credentials["account_number"],

                "ACNT_PRDT_CD": self.credentials["account_product_code"],

                "PDNO": order.symbol,

                "ORD_DVSN": ord_dvsn,

                "ORD_QTY": str(order.quantity),

                "ORD_UNPR": str(order.price) if order.price else "0"

            }

            

            response = requests.post(url, headers=headers, json=body, timeout=10)

            response.raise_for_status()

            

            data = response.json()

            

            if data.get("rt_cd") != "0":

                # Order failed - use minimal valid price to satisfy Pydantic validation

                return TradeResult(

                    order_id="",

                    symbol=order.symbol,

                    trade_type=order.trade_type,

                    quantity=order.quantity,

                    executed_price=Decimal("0.01"),  # Minimal valid price for failed orders

                    total_amount=Decimal("0"),

                    executed_at=datetime.now(),

                    status="FAILED",

                    message=data.get("msg1", "Order failed")

                )

            

            output = data.get("output", {})

            order_id = output.get("KRX_FWDG_ORD_ORGNO", "") + output.get("ODNO", "")

            

            # For market orders, we need to query the execution price

            executed_price = order.price if order.price else Decimal("0")

            

            return TradeResult(

                order_id=order_id,

                symbol=order.symbol,

                trade_type=order.trade_type,

                quantity=order.quantity,

                executed_price=executed_price,

                total_amount=executed_price * order.quantity,

                executed_at=datetime.now(),

                status="SUCCESS",

                message=data.get("msg1", "Order placed successfully")

            )

            

        except Exception as e:

            logger.error(f"Failed to place order: {e}")

            return TradeResult(

                order_id="",

                symbol=order.symbol,

                trade_type=order.trade_type,

                quantity=order.quantity,

                executed_price=Decimal("0.01"),  # Minimal valid price for failed orders

                total_amount=Decimal("0"),

                executed_at=datetime.now(),

                status="FAILED",

                message=str(e)

            )

    

    def cancel_order(self, order_id: str) -> bool:

        """

        Cancel a pending order

        

        Args:

            order_id: Order identifier

            

        Returns:

            bool: True if cancellation successful

        """

        self._ensure_authenticated()

        self._refresh_token_if_needed()

        

        try:

            url = f"{self.base_url}/uapi/domestic-stock/v1/trading/order-rvsecncl"

            

            tr_id = "VTTC0803U" if self.use_virtual else "TTTC0803U"

            headers = self._get_headers(tr_id=tr_id)

            

            # Parse order_id (format: KRX_FWDG_ORD_ORGNO + ODNO)

            orgno = order_id[:5] if len(order_id) >= 5 else ""

            odno = order_id[5:] if len(order_id) > 5 else order_id

            

            body = {

                "CANO": self.credentials["account_number"],

                "ACNT_PRDT_CD": self.credentials["account_product_code"],

                "KRX_FWDG_ORD_ORGNO": orgno,

                "ORGN_ODNO": odno,

                "ORD_DVSN": "00",

                "RVSE_CNCL_DVSN_CD": "02",  # 02: 취소

                "ORD_QTY": "0",

                "ORD_UNPR": "0"

            }

            

            response = requests.post(url, headers=headers, json=body, timeout=10)

            response.raise_for_status()

            

            data = response.json()

            

            return data.get("rt_cd") == "0"

            

        except Exception as e:

            logger.error(f"Failed to cancel order {order_id}: {e}")

            return False



    def get_order_status(self, order_id: str) -> Dict:

        """

        Get status of a specific order

        

        Args:

            order_id: Order identifier

            

        Returns:

            Dict: Order status information

        """

        self._ensure_authenticated()

        self._refresh_token_if_needed()

        

        try:

            url = f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-daily-ccld"

            

            tr_id = "VTTC8001R" if self.use_virtual else "TTTC8001R"

            headers = self._get_headers(tr_id=tr_id)

            

            # Parse order_id

            orgno = order_id[:5] if len(order_id) >= 5 else ""

            odno = order_id[5:] if len(order_id) > 5 else order_id

            

            params = {

                "CANO": self.credentials["account_number"],

                "ACNT_PRDT_CD": self.credentials["account_product_code"],

                "INQR_STRT_DT": datetime.now().strftime("%Y%m%d"),

                "INQR_END_DT": datetime.now().strftime("%Y%m%d"),

                "SLL_BUY_DVSN_CD": "00",  # 00: _체"

                "INQR_DVSN": "00",

                "PDNO": "",

                "CCLD_DVSN": "00",

                "ORD_GNO_BRNO": orgno,

                "ODNO": odno,

                "INQR_DVSN_3": "00",

                "INQR_DVSN_1": "",

                "CTX_AREA_FK100": "",

                "CTX_AREA_NK100": ""

            }

            

            response = requests.get(url, headers=headers, params=params, timeout=10)

            response.raise_for_status()

            

            data = response.json()

            

            if data.get("rt_cd") != "0":

                return {

                    "order_id": order_id,

                    "status": "UNKNOWN",

                    "message": data.get("msg1", "Failed to get order status")

                }

            

            output = data.get("output1", [])

            if not output:

                return {

                    "order_id": order_id,

                    "status": "NOT_FOUND",

                    "message": "Order not found"

                }

            

            order_info = output[0]

            

            return {

                "order_id": order_id,

                "symbol": order_info.get("pdno", ""),

                "order_type": order_info.get("sll_buy_dvsn_cd_name", ""),

                "quantity": int(order_info.get("ord_qty", "0")),

                "executed_quantity": int(order_info.get("tot_ccld_qty", "0")),

                "order_price": Decimal(order_info.get("ord_unpr", "0")),

                "executed_price": Decimal(order_info.get("avg_prvs", "0")),

                "status": order_info.get("ord_dvsn_name", ""),

                "order_time": order_info.get("ord_tmd", ""),

                "message": "Order status retrieved successfully"

            }

            

        except Exception as e:

            logger.error(f"Failed to get order status for {order_id}: {e}")

            return {

                "order_id": order_id,

                "status": "ERROR",

                "message": str(e)

            }

    

    def _get_headers(self, tr_id: str) -> Dict[str, str]:

        """

        Generate request headers for Korea Investment API

        

        Args:

            tr_id: Transaction ID for the specific API call

            

        Returns:

            Dict: Request headers

        """

        headers = {

            "content-type": "application/json; charset=utf-8",

            "authorization": f"Bearer {self.access_token}",

            "appkey": self.credentials["app_key"],

            "appsecret": self.credentials["app_secret"],

            "tr_id": tr_id

        }

        

        return headers

    

    def _generate_hash_key(self, body: Dict) -> str:

        """

        Generate hash key for websocket authentication

        

        Args:

            body: Request body

            

        Returns:

            str: Hash key

        """

        try:

            url = f"{self.base_url}/uapi/hashkey"

            

            headers = {

                "content-type": "application/json",

                "appkey": self.credentials["app_key"],

                "appsecret": self.credentials["app_secret"]

            }

            

            response = requests.post(url, headers=headers, json=body, timeout=10)

            response.raise_for_status()

            

            data = response.json()

            return data.get("HASH", "")

            

        except Exception as e:

            logger.error(f"Failed to generate hash key: {e}")

            return ""

