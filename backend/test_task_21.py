"""

Task 21 _합 "
"""



import pytest

from fastapi.testclient import TestClient

from sqlalchemy import create_engine

from sqlalchemy.orm import sessionmaker

from datetime import datetime



from main import app

from app.database import Base, get_db

from models.auto_trade_config import AutoTradeConfig

from models.trade_history import TradeHistory



# _스"
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_task_21.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)



def override_get_db():

    try:

        db = TestingSessionLocal()

        yield db

    finally:

        db.close()



app.dependency_overrides[get_db] = override_get_db



# _스"
@pytest.fixture(scope="function", autouse=True)

def setup_database():

    """테스트용 데이터베이스 초기화"""

    Base.metadata.create_all(bind=engine)

    yield

    Base.metadata.drop_all(bind=engine)





class TestAutoTradingDashboardAPI:

    """자동 매매 대시보드 API 테스트"""



    def test_update_trading_config(self):

        """21.1: 설정 패널 - 자동 매매 설정 업데이트"""

        config_data = {

            "max_investment": 1000000,

            "risk_level": "medium",

            "stop_loss_threshold": 5.0,

            "trading_start_time": "09:00",

            "trading_end_time": "15:30"

        }

        

        response = client.post("/api/auto-trade/config", json=config_data)

        

        assert response.status_code == 200

        data = response.json()

        assert data["max_investment"] == 1000000

        assert data["risk_level"] == "medium"

        assert data["stop_loss_threshold"] == 5.0

        print("✓ 설정 업데이트 API 정상 동작")



    def test_start_auto_trading(self):

        """21.2: 제어 패널 - 자동 매매 시작"""

        # 먼저 설정 업데이트
            "max_investment": 1000000,

            "risk_level": "medium",

            "stop_loss_threshold": 5.0

        }

        client.post("/api/auto-trade/config", json=config_data)

        

        # _동 매매 "
        response = client.post("/api/auto-trade/start")

        

        assert response.status_code == 200

        data = response.json()

        assert data["status"] == "started"

        assert "message" in data

        print("✓ 자동 매매 시작 API 정상 동작")



    def test_stop_auto_trading(self):

        """21.2: 제어 패널 - 자동 매매 중지"""

        response = client.post("/api/auto-trade/stop")

        

        assert response.status_code == 200

        data = response.json()

        assert data["status"] == "stopped"

        assert "message" in data

        print("✓ 자동 매매 중지 API 정상 동작")



    def test_get_trade_history(self):

        """21.3: 거래 이력 조회"""

        # _스"
                symbol="AAPL",

                action="buy",

                quantity=10,

                price=150000,

                timestamp=datetime.now(),

                status="completed"

            )

            trade2 = TradeHistory(

                symbol="GOOGL",

                action="sell",

                quantity=5,

                price=200000,

                timestamp=datetime.now(),

                status="completed"

            )

            db.add(trade1)

            db.add(trade2)

            db.commit()

        finally:

            db.close()

        

        # 거래 _역 조회"

        response = client.get("/api/trades/history?limit=50")

        

        assert response.status_code == 200

        data = response.json()

        assert isinstance(data, list)

        assert len(data) == 2

        

        # �?번째 거래 _인"

        trade = data[0]

        assert "symbol" in trade

        assert "action" in trade

        assert "quantity" in trade

        assert "price" in trade

        assert "timestamp" in trade or "created_at" in trade

        print("✓ 거래 이력 조회 API 정상 동작")



    def test_get_account_holdings(self):

        """21.3: 현재 보유종목 조회"""

        response = client.get("/api/account/holdings")

        

        assert response.status_code == 200

        data = response.json()

        assert isinstance(data, list)

        

        # 보유 종목??_는 경우 구조 "
            assert "symbol" in holding

            assert "quantity" in holding

            assert "average_price" in holding or "current_price" in holding

        print("✓ 보유 종목 조회 API 정상 동작")



    def test_trading_config_validation(self):

        """설정 검증 테스트"""

        # 잘못된 설정 데이터
            "max_investment": 1000000,

            "risk_level": "invalid",

            "stop_loss_threshold": 5.0

        }

        

        response = client.post("/api/auto-trade/config", json=invalid_config)

        # 검증 실패 예상
        print("✓ 설정 검증 정상 동작")



    def test_trade_history_limit(self):

        """거래 이력 제한 테스트"""

        # 많은 거래 이력 추가
                    symbol=f"STOCK{i}",

                    action="buy" if i % 2 == 0 else "sell",

                    quantity=10,

                    price=100000 + i * 1000,

                    timestamp=datetime.now(),

                    status="completed"

                )

                db.add(trade)

            db.commit()

        finally:

            db.close()

        

        # _한"
        response = client.get("/api/trades/history?limit=20")

        

        assert response.status_code == 200

        data = response.json()

        assert len(data) <= 20

        print("✓ 거래 이력 제한 기능 정상 동작")



    def test_emergency_stop(self):

        """21.2: 긴급 중지 기능 테스트"""

        # _동 매매 "
            "max_investment": 1000000,

            "risk_level": "medium",

            "stop_loss_threshold": 5.0

        }

        client.post("/api/auto-trade/config", json=config_data)

        client.post("/api/auto-trade/start")

        

        # 긴급 중지 (stop 엔드포인트 사용)
        response = client.post("/api/auto-trade/stop")

        

        assert response.status_code == 200

        data = response.json()

        assert data["status"] == "stopped"

        print("??긴급 중�? 기능 ?�상 ?�동")





class TestDashboardDataFlow:

    """?�?�보???�이???�름 ?�합 ?�스??""



    def test_complete_trading_flow(self):

        """?�전??거래 ?�름 ?�스??""

        # 1. _정 "
            "max_investment": 2000000,

            "risk_level": "low",

            "stop_loss_threshold": 3.0

        }

        config_response = client.post("/api/auto-trade/config", json=config_data)

        assert config_response.status_code == 200

        print("??1?�계: ?�정 ?�???�료")

        

        # 2. _동 매매 "
        start_response = client.post("/api/auto-trade/start")

        assert start_response.status_code == 200

        print("??2?�계: ?�동 매매 ?�작 ?�료")

        

        # 3. 거래 _역 "
        history_response = client.get("/api/trades/history")

        assert history_response.status_code == 200

        print("??3?�계: 거래 ?�역 조회 ?�료")

        

        # 4. 보유 종목 _인"

        holdings_response = client.get("/api/account/holdings")

        assert holdings_response.status_code == 200

        print("??4?�계: 보유 종목 조회 ?�료")

        

        # 5. _동 매매 중�"
        stop_response = client.post("/api/auto-trade/stop")

        assert stop_response.status_code == 200

        print("??5?�계: ?�동 매매 중�? ?�료")

        

        print("\n???�체 거래 ?�름 ?�스???�공")



    def test_dashboard_performance_data(self):

        """?�과 ?�이??계산 ?�스??""

        # _스"
                symbol="AAPL",

                action="buy",

                quantity=10,

                price=100000,

                timestamp=datetime.now(),

                status="completed"

            )

            sell1 = TradeHistory(

                symbol="AAPL",

                action="sell",

                quantity=10,

                price=110000,

                timestamp=datetime.now(),

                status="completed"

            )

            

            # _실 거래"

            buy2 = TradeHistory(

                symbol="GOOGL",

                action="buy",

                quantity=5,

                price=200000,

                timestamp=datetime.now(),

                status="completed"

            )

            sell2 = TradeHistory(

                symbol="GOOGL",

                action="sell",

                quantity=5,

                price=190000,

                timestamp=datetime.now(),

                status="completed"

            )

            

            db.add_all([buy1, sell1, buy2, sell2])

            db.commit()

        finally:

            db.close()

        

        # 거래 _역 조회"

        response = client.get("/api/trades/history")

        assert response.status_code == 200

        

        trades = response.json()

        assert len(trades) == 4

        

        # _익 계산 ("
        total_buy = sum(t["quantity"] * t["price"] for t in trades if t["action"] == "buy")

        total_sell = sum(t["quantity"] * t["price"] for t in trades if t["action"] == "sell")

        profit = total_sell - total_buy

        

        assert profit == 50000  # (110000-100000)*10 + (190000-200000)*5 = 100000 - 50000

        print(f"??_과 "
    """모든 ?�스???�행"""

    print("\n" + "="*60)

    print("Task 21: _동 매매 "
    print("="*60 + "\n")

    

    # pytest _행"

    pytest.main([__file__, "-v", "-s"])





if __name__ == "__main__":

    run_tests()

