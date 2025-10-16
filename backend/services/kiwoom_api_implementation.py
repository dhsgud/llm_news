"""

_�"
"""



import sys

import logging

from typing import Dict, List, Optional, Callable

from datetime import datetime

from decimal import Decimal

from collections import defaultdict



try:

    from PyQt5.QAxContainer import QAxWidget

    from PyQt5.QtCore import QEventLoop, QTimer

    from PyQt5.QtWidgets import QApplication

    PYQT5_AVAILABLE = True

except ImportError:

    PYQT5_AVAILABLE = False

    logging.warning("PyQt5 not installed. Kiwoom API will not be available.")



from services.brokerage_connector import BrokerageAPIBase, AccountInfo, StockPrice

from models.trading_schemas import Order, TradeResult



logger = logging.getLogger(__name__)





class KiwoomOpenAPI:

    """

    _�"
    """

    

    # TR 코드 _의"

    TR_OPT10001 = "opt10001"  # 주식기본_보"

    TR_OPT10081 = "opt10081"  # 주식_봉차트"

    TR_OPW00001 = "opw00001"  # _수금상"
    TR_OPW00018 = "opw00018"  # 계좌_�"
    TR_OPT10075 = "opt10075"  # 미체결요�?
    

    # 주문 _"
    HOGA_LIMIT = "00"           # 지_�"
    HOGA_MARKET = "03"          # _장가"

    HOGA_CONDITION = "05"       # 조건부지_�"
    HOGA_BEST = "06"            # 최유리�?_�"
    HOGA_IMMEDIATE = "07"       # 최우_�"
        """Initialize Kiwoom OpenAPI"""

        if not PYQT5_AVAILABLE:

            raise ImportError("PyQt5 is required for Kiwoom API. Install with: pip install PyQt5")

        

        # QApplication _스"
        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")

        

        # _벤"
        logger.info("Kiwoom OpenAPI initialized")

    

    def _connect_events(self):

        """?�벤???�들???�결"""

        self.ocx.OnEventConnect.connect(self._on_event_connect)

        self.ocx.OnReceiveTrData.connect(self._on_receive_tr_data)

        self.ocx.OnReceiveRealData.connect(self._on_receive_real_data)

        self.ocx.OnReceiveChejanData.connect(self._on_receive_chejan_data)

        self.ocx.OnReceiveMsg.connect(self._on_receive_msg)

    

    def _on_event_connect(self, err_code: int):

        """

        로그??_벤"
        """

        if err_code == 0:

            logger.info("Kiwoom login successful")

            self.is_connected = True

            

            # 계좌 _보 가"
            account_cnt = self.ocx.dynamicCall("GetLoginInfo(QString)", "ACCOUNT_CNT")

            accounts = self.ocx.dynamicCall("GetLoginInfo(QString)", "ACCNO")

            self.account_list = accounts.split(';')[:-1] if accounts else []

            

            logger.info(f"Available accounts: {self.account_list}")

        else:

            logger.error(f"Kiwoom login failed with error code: {err_code}")

            self.is_connected = False

        

        if self.login_event_loop:

            self.login_event_loop.exit()

    

    def _on_receive_tr_data(

        self,

        screen_no: str,

        rqname: str,

        trcode: str,

        record_name: str,

        prev_next: str,

        *args

    ):

        """

        TR _이"
        """

        logger.debug(f"Received TR data: {rqname} ({trcode})")

        

        self.tr_remained = (prev_next == "2")

        

        # TR 코드�?_이"
        """

        _시�"
        """

        if code in self.real_callbacks:

            for callback in self.real_callbacks[code]:

                callback(code, real_type, real_data)

    

    def _on_receive_chejan_data(self, gubun: str, item_cnt: int, fid_list: str):

        """

        체결 _이"
        """

        logger.info(f"Chejan data received: gubun={gubun}, item_cnt={item_cnt}")

        

        if gubun == "0":  # 주문체결

            order_no = self.ocx.dynamicCall("GetChejanData(int)", 9203)

            stock_code = self.ocx.dynamicCall("GetChejanData(int)", 9001)

            order_status = self.ocx.dynamicCall("GetChejanData(int)", 913)

            

            logger.info(f"Order status: {order_no} - {stock_code} - {order_status}")

        

        elif gubun == "1":  # _고"

            stock_code = self.ocx.dynamicCall("GetChejanData(int)", 9001)

            quantity = self.ocx.dynamicCall("GetChejanData(int)", 930)

            

            logger.info(f"Balance update: {stock_code} - {quantity}")

    

    def _on_receive_msg(

        self,

        screen_no: str,

        rqname: str,

        trcode: str,

        msg: str

    ):

        """

        메시지 _신 "
        """

        logger.info(f"Message received: {msg}")

    

    def login(self, timeout: int = 30) -> bool:

        """

        _�"
        """

        if self.is_connected:

            logger.info("Already connected")

            return True

        

        self.login_event_loop = QEventLoop()

        

        # 로그??_청"

        self.ocx.dynamicCall("CommConnect()")

        

        # _"
        """

        TR _력�"
        """

        self.ocx.dynamicCall("SetInputValue(QString, QString)", key, value)

    

    def _comm_rq_data(

        self,

        rqname: str,

        trcode: str,

        prev_next: int,

        screen_no: str

    ) -> bool:

        """

        TR _청

        

        Args:

            rqname: "
        """

        self.tr_event_loop = QEventLoop()

        

        ret = self.ocx.dynamicCall(

            "CommRqData(QString, QString, int, QString)",

            rqname,

            trcode,

            prev_next,

            screen_no

        )

        

        if ret == 0:

            # _"
            logger.error(f"CommRqData failed with code: {ret}")

            self.tr_event_loop = None

            return False

    

    def _get_comm_data(

        self,

        trcode: str,

        rqname: str,

        index: int,

        item_name: str

    ) -> str:

        """

        TR _이"
        """

        data = self.ocx.dynamicCall(

            "GetCommData(QString, QString, int, QString)",

            trcode,

            rqname,

            index,

            item_name

        )

        return data.strip()

    

    def _get_repeat_cnt(self, trcode: str, rqname: str) -> int:

        """

        반복 _이"
        """

        return self.ocx.dynamicCall(

            "GetRepeatCnt(QString, QString)",

            trcode,

            rqname

        )

    

    def _parse_opt10001(self):

        """주식기본?�보 ?�싱 (opt10001)"""

        stock_code = self._get_comm_data(self.TR_OPT10001, "주식기본?�보", 0, "종목코드")

        stock_name = self._get_comm_data(self.TR_OPT10001, "주식기본?�보", 0, "종목�?)

        current_price = self._get_comm_data(self.TR_OPT10001, "주식기본?�보", 0, "?�재가")

        volume = self._get_comm_data(self.TR_OPT10001, "주식기본?�보", 0, "거래??)

        open_price = self._get_comm_data(self.TR_OPT10001, "주식기본?�보", 0, "?��?")

        high_price = self._get_comm_data(self.TR_OPT10001, "주식기본?�보", 0, "고�?")

        low_price = self._get_comm_data(self.TR_OPT10001, "주식기본?�보", 0, "?�가")

        

        self.tr_data = {

            "stock_code": stock_code,

            "stock_name": stock_name,

            "current_price": abs(int(current_price)),

            "volume": int(volume),

            "open_price": abs(int(open_price)),

            "high_price": abs(int(high_price)),

            "low_price": abs(int(low_price)),

        }

    

    def _parse_opt10081(self):

        """주식?�봉차트 ?�싱 (opt10081)"""

        cnt = self._get_repeat_cnt(self.TR_OPT10081, "주식?�봉차트")

        

        data_list = []

        for i in range(cnt):

            date = self._get_comm_data(self.TR_OPT10081, "주식?�봉차트", i, "?�자")

            open_price = self._get_comm_data(self.TR_OPT10081, "주식?�봉차트", i, "?��?")

            high_price = self._get_comm_data(self.TR_OPT10081, "주식?�봉차트", i, "고�?")

            low_price = self._get_comm_data(self.TR_OPT10081, "주식?�봉차트", i, "?�가")

            close_price = self._get_comm_data(self.TR_OPT10081, "주식?�봉차트", i, "?�재가")

            volume = self._get_comm_data(self.TR_OPT10081, "주식?�봉차트", i, "거래??)

            

            data_list.append({

                "date": date,

                "open": abs(int(open_price)),

                "high": abs(int(high_price)),

                "low": abs(int(low_price)),

                "close": abs(int(close_price)),

                "volume": int(volume)

            })

        

        self.tr_data = {"chart_data": data_list}

    

    def _parse_opw00001(self):

        """?�수금상?�현???�싱 (opw00001)"""

        deposit = self._get_comm_data(self.TR_OPW00001, "?�수금상?�현??, 0, "_수�"
        available_amount = self._get_comm_data(self.TR_OPW00001, "?�수금상?�현??, 0, "출금가_금"
            "deposit": int(deposit),

            "available_amount": int(available_amount)

        }

    

    def _parse_opw00018(self):

        """계좌?��??�고?�역 ?�싱 (opw00018)"""

        cnt = self._get_repeat_cnt(self.TR_OPW00018, "계좌?��??�고")

        

        holdings = []

        for i in range(cnt):

            stock_code = self._get_comm_data(self.TR_OPW00018, "계좌?��??�고", i, "종목번호")

            stock_name = self._get_comm_data(self.TR_OPW00018, "계좌?��??�고", i, "종목�?)

            quantity = self._get_comm_data(self.TR_OPW00018, "계좌?��??�고", i, "보유?�량")

            purchase_price = self._get_comm_data(self.TR_OPW00018, "계좌?��??�고", i, "매입가")

            current_price = self._get_comm_data(self.TR_OPW00018, "계좌?��??�고", i, "?�재가")

            profit_loss = self._get_comm_data(self.TR_OPW00018, "계좌?��??�고", i, "?�익금액")

            profit_rate = self._get_comm_data(self.TR_OPW00018, "계좌?��??�고", i, "?�익�?%)")

            

            holdings.append({

                "stock_code": stock_code.strip(),

                "stock_name": stock_name.strip(),

                "quantity": int(quantity),

                "purchase_price": abs(int(purchase_price)),

                "current_price": abs(int(current_price)),

                "profit_loss": int(profit_loss),

                "profit_rate": float(profit_rate)

            })

        

        self.tr_data = {"holdings": holdings}

    

    def _parse_opt10075(self):

        """미체결요�??�싱 (opt10075)"""

        cnt = self._get_repeat_cnt(self.TR_OPT10075, "미체결요�?)

        

        orders = []

        for i in range(cnt):

            order_no = self._get_comm_data(self.TR_OPT10075, "미체결요�?, i, "주문번호")

            stock_code = self._get_comm_data(self.TR_OPT10075, "미체결요�?, i, "종목코드")

            stock_name = self._get_comm_data(self.TR_OPT10075, "미체결요�?, i, "종목�?)

            order_type = self._get_comm_data(self.TR_OPT10075, "미체결요�?, i, "주문구분")

            order_quantity = self._get_comm_data(self.TR_OPT10075, "미체결요�?, i, "주문?�량")

            order_price = self._get_comm_data(self.TR_OPT10075, "미체결요�?, i, "주문가�?)

            unfilled_quantity = self._get_comm_data(self.TR_OPT10075, "미체결요�?, i, "미체결수??)

            

            orders.append({

                "order_no": order_no,

                "stock_code": stock_code.strip(),

                "stock_name": stock_name.strip(),

                "order_type": order_type.strip(),

                "order_quantity": int(order_quantity),

                "order_price": int(order_price),

                "unfilled_quantity": int(unfilled_quantity)

            })

        

        self.tr_data = {"orders": orders}

    

    def get_stock_price(self, stock_code: str) -> Dict:

        """

        주식 _재가 조회"

        

        Args:

            stock_code: 종목코드 (?? "005930")

            

        Returns:

            Dict: 주식 가�?_보"

        """

        self._set_input_value("종목코드", stock_code)

        

        if self._comm_rq_data("주식기본?�보", self.TR_OPT10001, 0, "0101"):

            return self.tr_data

        else:

            return {}

    

    def get_stock_chart(

        self,

        stock_code: str,

        date: str = "",

        count: int = 100

    ) -> Dict:

        """

        주식 _봉 차트 조회

        

        Args:

            stock_code: 종목코드

            date: 기�"
        """

        self._set_input_value("종목코드", stock_code)

        self._set_input_value("기�??�자", date)

        self._set_input_value("?�정주�?구분", "1")

        

        if self._comm_rq_data("주식?�봉차트", self.TR_OPT10081, 0, "0102"):

            return self.tr_data

        else:

            return {}

    

    def get_deposit(self, account_no: str) -> Dict:

        """

        _수�"
        """

        self._set_input_value("계좌번호", account_no)

        self._set_input_value("비�?번호", "")

        self._set_input_value("비�?번호?�력매체구분", "00")

        self._set_input_value("조회구분", "2")

        

        if self._comm_rq_data("?�수금상?�현??, self.TR_OPW00001, 0, "0103"):

            return self.tr_data

        else:

            return {}

    

    def get_holdings(self, account_no: str) -> Dict:

        """

        보유 종목 조회

        

        Args:

            account_no: 계좌번호

            

        Returns:

            Dict: 보유 종목 _보"

        """

        self._set_input_value("계좌번호", account_no)

        self._set_input_value("비�?번호", "")

        self._set_input_value("비�?번호?�력매체구분", "00")

        self._set_input_value("조회구분", "2")

        

        if self._comm_rq_data("계좌?��??�고", self.TR_OPW00018, 0, "0104"):

            return self.tr_data

        else:

            return {}

    

    def get_unfilled_orders(self, account_no: str) -> Dict:

        """

        미체�?주문 조회

        

        Args:

            account_no: 계좌번호

            

        Returns:

            Dict: 미체�?주문 _보"

        """

        self._set_input_value("계좌번호", account_no)

        self._set_input_value("?�체종목구분", "0")

        self._set_input_value("매매구분", "0")

        self._set_input_value("종목코드", "")

        self._set_input_value("체결구분", "1")

        

        if self._comm_rq_data("미체결요�?, self.TR_OPT10075, 0, "0105"):

            return self.tr_data

        else:

            return {}

    

    def send_order(

        self,

        rqname: str,

        screen_no: str,

        account_no: str,

        order_type: int,

        stock_code: str,

        quantity: int,

        price: int,

        hoga_type: str,

        origin_order_no: str = ""

    ) -> int:

        """

        주문 _송

        

        Args:

            rqname: "
            hoga_type: ?��??�형 ("00": 지?��?, "03": _장가)

            origin_order_no: "
        """

        ret = self.ocx.dynamicCall(

            "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",

            [

                rqname,

                screen_no,

                account_no,

                order_type,

                stock_code,

                quantity,

                price,

                hoga_type,

                origin_order_no

            ]

        )

        

        if ret == 0:

            logger.info(f"Order sent successfully: {stock_code} x {quantity}")

        else:

            logger.error(f"Order failed with code: {ret}")

        

        return ret

    

    def register_real(

        self,

        screen_no: str,

        code_list: str,

        fid_list: str,

        opt_type: str

    ):

        """

        _시�"
            opt_type: ?�록?�??("0": 추�?, "1": ?_�)"

        """

        self.ocx.dynamicCall(

            "SetRealReg(QString, QString, QString, QString)",

            screen_no,

            code_list,

            fid_list,

            opt_type

        )

    

    def disconnect_real(self, screen_no: str):

        """

        _시�"
        """

        self.ocx.dynamicCall("DisconnectRealData(QString)", screen_no)

    

    def get_account_list(self) -> List[str]:

        """

        계좌 목록 조회

        

        Returns:

            List[str]: 계좌번호 리스??
        """

        return self.account_list





# _용 "
if __name__ == "__main__":

    # 로깅 _정

    logging.basicConfig(

        level=logging.INFO,

        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    )

    

    # Kiwoom API 초기"
        print("로그???�공!")

        print(f"계좌 목록: {kiwoom.get_account_list()}")

        

        # _성"
        stock_data = kiwoom.get_stock_price("005930")

        print(f"?�성?�자 ?�재가: {stock_data}")

        

        # 계좌 _보 조회 (�"
            print(f"?�수�? {deposit}")

            

            # 보유 종목 조회

            holdings = kiwoom.get_holdings(account_no)

            print(f"보유 종목: {holdings}")

    else:

        print("로그???�패!")

