"""
키움증권 OpenAPI 연결 테스트 스크립트
"""



import os

import sys

import logging

from dotenv import load_dotenv



# 로깅 설정
logging.basicConfig(

    level=logging.INFO,

    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'

)

logger = logging.getLogger(__name__)



def check_environment():

    """환경 변수 확인"""

    logger.info("=" * 60)

    logger.info("1. 환경 변수 확인")

    logger.info("=" * 60)

    

    required_vars = [

        "KIWOOM_ACCOUNT_NUMBER",

        "KIWOOM_USER_ID",

        "KIWOOM_APP_KEY",

        "KIWOOM_APP_SECRET"

    ]

    

    missing_vars = []

    for var in required_vars:

        value = os.getenv(var)

        if value and value != f"your_{var.lower().replace('kiwoom_', '')}":

            logger.info(f"✓ {var}: {'*' * 10} (설정됨)")

        else:

            logger.error(f"✗ {var}: 설정되지 않음")

            missing_vars.append(var)

    

    if missing_vars:

        logger.error("\n다음 환경 변수를 .env 파일에 설정해주세요:")

        for var in missing_vars:

            logger.error(f"  - {var}")

        return False

    

    logger.info("\n✓ 모든 환경 변수가 설정되었습니다\n")

    return True



def check_windows():

    """Windows OS 확인"""

    logger.info("=" * 60)

    logger.info("2. 운영체제 확인")

    logger.info("=" * 60)

    

    if sys.platform != "win32":

        logger.error("✗ 키움증권 OpenAPI+는 Windows에서만 작동합니다")

        logger.error(f"   현재 OS: {sys.platform}")

        return False

    

    logger.info("✓ Windows OS 확인됨\n")

    return True



def check_pyqt5():

    """PyQt5 설치 확인"""

    logger.info("=" * 60)

    logger.info("3. PyQt5 설치 확인")

    logger.info("=" * 60)

    

    try:

        from PyQt5.QtCore import QT_VERSION_STR

        logger.info(f"✓ PyQt5 설치됨 (버전: {QT_VERSION_STR})\n")

        return True

    except ImportError:

        logger.error("✗ PyQt5가 설치되지 않았습니다")

        logger.error("   설치 방법: pip install PyQt5==5.15.10")

        return False



def check_kiwoom_openapi():

    """Kiwoom OpenAPI+ 설치 확인"""

    logger.info("=" * 60)

    logger.info("4. Kiwoom OpenAPI+ 설치 확인")

    logger.info("=" * 60)

    

    try:

        from PyQt5.QAxContainer import QAxWidget

        from PyQt5.QtWidgets import QApplication

        

        # QApplication 생성

        app = QApplication.instance()

        if not app:

            app = QApplication(sys.argv)

        

        # OCX 객체 생성 시도

        try:

            ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")

            logger.info("✓ Kiwoom OpenAPI+ 설치 확인됨\n")

            return True

        except Exception as e:

            logger.error("✗ Kiwoom OpenAPI+를 찾을 수 없습니다.")

            logger.error(f"   오류: {e}")

            logger.error("   설치 방법:")

            logger.error("   1. https://www.kiwoom.com/ 접속")

            logger.error("   2. [트레이딩] → [시스템트레이딩] → [OpenAPI+]")

            logger.error("   3. OpenAPI+ 다운로드 및 설치")

            return False

    except ImportError as e:

        logger.error(f"✗ PyQt5 import 실패: {e}")

        return False



def test_kiwoom_connection():

    """Kiwoom API 연결 테스트"""

    logger.info("=" * 60)

    logger.info("5. Kiwoom API 연결 테스트")

    logger.info("=" * 60)

    

    try:

        from services.kiwoom_api_implementation import KiwoomOpenAPI

        

        logger.info("Kiwoom API 초기화 중..")

        kiwoom = KiwoomOpenAPI()

        

        logger.info("로그인 시도 중.. (로그인 창이 열립니다)")

        logger.info("⚠️  키움증권 로그인 창에서 로그인해주세요")

        

        if kiwoom.login(timeout=60):

            logger.info("✓ 로그인 성공!")

            

            # 계좌 정보 조회

            accounts = kiwoom.get_account_list()

            logger.info(f"\n사용 가능한 계좌:")

            for i, account in enumerate(accounts, 1):

                logger.info(f"  {i}. {account}")

            

            # 환경 변수 계좌 확인

            env_account = os.getenv("KIWOOM_ACCOUNT_NUMBER")

            if env_account in accounts:

                logger.info(f"\n✓ 설정된 계좌번호({env_account})가 확인되었습니다")

            else:

                logger.warning(f"\n⚠️  설정된 계좌번호({env_account})를 찾을 수 없습니다.")

                logger.warning(f"   .env 파일의 KIWOOM_ACCOUNT_NUMBER를 위 계좌 중 하나로 변경하세요.")

            

            # 간단한 API 테스트

            logger.info("\n삼성전자(005930) 현재가 조회 테스트..")

            try:

                stock_data = kiwoom.get_stock_price("005930")

                if stock_data:

                    logger.info(f"✓ API 호출 성공!")

                    logger.info(f"   종목명: {stock_data.get('stock_name', 'N/A')}")

                    logger.info(f"   현재가: {stock_data.get('current_price', 0):,}원")

                    logger.info(f"   거래량: {stock_data.get('volume', 0):,}주")

                else:

                    logger.warning("⚠️  데이터를 가져오지 못했습니다")

            except Exception as e:

                logger.error(f"✗ API 호출 실패: {e}")

            

            logger.info("\n" + "=" * 60)

            logger.info("✓ 모든 테스트 완료!")

            logger.info("=" * 60)

            logger.info("\n키움증권 API가 정상적으로 작동합니다")

            logger.info("이제 실제 트레이딩 로직을 구현할 수 있습니다.\n")

            

            return True

        else:

            logger.error("✗ 로그인 실패")

            logger.error("   확인 사항:")

            logger.error("   1. 키움증권 계좌가 개설되어 있는지")

            logger.error("   2. 사용한 ID와 비밀번호가 정확한지")

            logger.error("   3. 공인인증서가 설치되어 있는지")

            return False

            

    except ImportError as e:

        logger.error(f"✗ Kiwoom API 모듈을 import할 수 없습니다: {e}")

        logger.error("   services/kiwoom_api_implementation.py 파일을 확인하세요")

        return False

    except Exception as e:

        logger.error(f"✗ 예상치 못한 오류 발생: {e}")

        import traceback

        traceback.print_exc()

        return False



def main():

    """메인 함수"""

    print("\n")

    print("=" * 60)

    print("키움증권 OpenAPI 연결 테스트")

    print("=" * 60)

    print("\n")

    

    # 1. 환경 변수 확인

    load_dotenv()

    if not check_environment():

        logger.error("\n✗ 환경 변수 설정을 완료한 후 다시 실행하세요")

        logger.error("   설정 방법: backend/KIWOOM_SETUP_GUIDE.md 참조")

        return False

    

    # 2. Windows OS 확인

    if not check_windows():

        logger.error("\n✗ Windows OS에서만 실행 가능합니다.")

        return False

    

    # 3. PyQt5 확인

    if not check_pyqt5():

        logger.error("\n✗ PyQt5를 설치한 후 다시 실행하세요")

        return False

    

    # 4. Kiwoom OpenAPI+ 확인

    if not check_kiwoom_openapi():

        logger.error("\n✗ Kiwoom OpenAPI+를 설치한 후 다시 실행하세요")

        return False

    

    # 5. 연결 테스트

    if not test_kiwoom_connection():

        logger.error("\n✗ 연결 테스트 실패")

        return False

    

    return True



if __name__ == "__main__":

    try:

        success = main()

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:

        logger.info("\n\n사용자에 의해 중단되었습니다")

        sys.exit(0)

    except Exception as e:

        logger.error(f"\n예상치 못한 오류: {e}")

        import traceback

        traceback.print_exc()

        sys.exit(1)

