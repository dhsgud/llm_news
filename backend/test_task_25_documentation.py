"""

Task 25: 문서?_"
"""

import os

import pytest

from pathlib import Path





class TestDocumentation:

    """문서 존재 및 내용 검증"""

    

    def test_task_25_summary_exists(self):

        """Task 25 요약 문서 존재 확인"""

        assert os.path.exists("TASK_25_SUMMARY.md")

    

    def test_system_architecture_exists(self):

        """시스템 아키텍처 문서 존재 확인"""

        assert os.path.exists("SYSTEM_ARCHITECTURE.md")

        

        with open("SYSTEM_ARCHITECTURE.md", "r", encoding="utf-8") as f:

            content = f.read()

            assert "시스템 아키텍처" in content

            assert "Frontend Layer" in content

            assert "Backend Layer" in content

            assert "Service Layer" in content

    

    def test_deployment_guide_exists(self):

        """배포 가이드 문서 존재 확인"""

        assert os.path.exists("DEPLOYMENT_GUIDE.md")

        

        with open("DEPLOYMENT_GUIDE.md", "r", encoding="utf-8") as f:

            content = f.read()

            assert "배포 가이드" in content

            assert "시스템 요구사항" in content

            assert "환경 설정" in content

            assert "배포 프로세스" in content

    

    def test_operations_manual_exists(self):

        """운영 매뉴얼 문서 존재 확인"""

        assert os.path.exists("OPERATIONS_MANUAL.md")

        

        with open("OPERATIONS_MANUAL.md", "r", encoding="utf-8") as f:

            content = f.read()

            assert "운영 매뉴얼" in content
            assert "일일 운영" in content

            assert "장애 대응" in content
    
    def test_api_documentation_exists(self):
        """API 문서 존재 확인"""

        assert os.path.exists("API_DOCUMENTATION.md")

        

        with open("API_DOCUMENTATION.md", "r", encoding="utf-8") as f:

            content = f.read()

            assert "API 문서" in content

            assert "주식 API" in content

            assert "자동 매매 API" in content

            assert "보안 API" in content

            assert "모니터링 API" in content

    

    def test_developer_guide_exists(self):

        """개발자 가이드 문서 존재 확인"""

        assert os.path.exists("DEVELOPER_GUIDE.md")

        

        with open("DEVELOPER_GUIDE.md", "r", encoding="utf-8") as f:

            content = f.read()

            assert "개발자 가이드" in content

            assert "개발 환경 설정" in content

            assert "코딩 규칙" in content
            assert "테스트" in content
    
    def test_user_guide_exists(self):
        """사용자 가이드 문서 존재 확인"""

        assert os.path.exists("USER_GUIDE.md")

        

        with open("USER_GUIDE.md", "r", encoding="utf-8") as f:

            content = f.read()

            assert "사용자 가이드" in content

            assert "시작하기" in content

            assert "주식 분석" in content

            assert "자동 매매" in content

    

    def test_changelog_exists(self):

        """변경 이력 문서 존재 확인"""

        assert os.path.exists("CHANGELOG.md")

        

        with open("CHANGELOG.md", "r", encoding="utf-8") as f:

            content = f.read()

            assert "Changelog" in content

            assert "[1.0.0]" in content

    

    def test_readme_updated(self):

        """README 업데이트 확인"""

        assert os.path.exists("README.md")

        

        with open("README.md", "r", encoding="utf-8") as f:

            content = f.read()

            assert "Market Sentiment Analyzer" in content

            assert "주요 기능" in content

            assert "빠른 시작" in content





class TestDeploymentReadiness:

    """배포 준비 상태 검증"""

    

    def test_requirements_file_exists(self):

        """requirements.txt 존재 확인"""

        assert os.path.exists("requirements.txt")

        

        with open("requirements.txt", "r") as f:

            content = f.read()

            assert "fastapi" in content

            assert "sqlalchemy" in content

            assert "alembic" in content

    

    def test_config_file_exists(self):

        """설정 파일 존재 확인"""

        assert os.path.exists("config.py")

    

    def test_main_file_exists(self):

        """메인 애플리케이션 파일 존재 확인"""

        assert os.path.exists("main.py")

    

    def test_alembic_config_exists(self):

        """Alembic 설정 존재 확인"""

        assert os.path.exists("alembic.ini")

        assert os.path.exists("alembic/")

    

    def test_env_example_exists(self):

        """환경 변수 예제 파일 존재 확인"""

        # .env.example은 배포 가이드에 언급되어야 함
        with open("DEPLOYMENT_GUIDE.md", "r", encoding="utf-8") as f:

            content = f.read()

            assert "환경 변수" in content or "ENVIRONMENT" in content





class TestDocumentationQuality:

    """문서 품질 검증"""

    

    def test_all_tasks_documented(self):

        """모든 주요 작업이 문서화되었는지 확인"""

        with open("TASK_25_SUMMARY.md", "r", encoding="utf-8") as f:

            content = f.read()

            # Task 12-25까지 언급되어야 함
            assert "Task 12" in content or "주식 데이터 수집" in content

            assert "Task 23" in content or "보안" in content

            assert "Task 24" in content or "모니터링" in content

    

    def test_api_endpoints_documented(self):

        """주요 API 엔드포인트가 문서화되었는지 확인"""

        with open("API_DOCUMENTATION.md", "r", encoding="utf-8") as f:

            content = f.read()

            assert "/api/v1/stock" in content

            assert "/api/v1/trading" in content

            assert "/api/v1/security" in content

            assert "/api/v1/monitoring" in content

    

    def test_deployment_steps_documented(self):

        """배포 단계가 문서화되었는지 확인"""

        with open("DEPLOYMENT_GUIDE.md", "r", encoding="utf-8") as f:

            content = f.read()

            assert "배포 프로세스" in content or "배포 단계" in content

            assert "데이터베이스" in content

            assert "마이그레이션" in content

    

    def test_security_guidelines_documented(self):

        """보안 가이드라인이 문서화되었는지 확인"""

        # SECURITY_GUIDE.md _는 "
            "SECURITY_GUIDE.md",

            "DEPLOYMENT_GUIDE.md",

            "OPERATIONS_MANUAL.md"

        ]

        

        security_content_found = False

        for doc in security_docs:

            if os.path.exists(doc):

                with open(doc, "r", encoding="utf-8") as f:

                    content = f.read()

                    if "보안" in content or "암호화" in content or "인증" in content:

                        security_content_found = True

                        break

        

        assert security_content_found, "보안 관련 문서를 찾을 수 없습니다"





class TestDocumentationCompleteness:

    """문서 완성도 검증"""

    

    def test_architecture_diagrams_present(self):

        """아키텍처 다이어그램 존재 확인"""

        with open("SYSTEM_ARCHITECTURE.md", "r", encoding="utf-8") as f:

            content = f.read()

            # ASCII _이"
            assert "```" in content or "?? in content or "?? in content

    

    def test_code_examples_present(self):

        """코드 예제 존재 확인"""

        with open("DEVELOPER_GUIDE.md", "r", encoding="utf-8") as f:

            content = f.read()

            assert "```python" in content or "```bash" in content

    

    def test_troubleshooting_section_present(self):

        """트러블슈팅 섹션 존재 확인"""

        docs_with_troubleshooting = [

            "OPERATIONS_MANUAL.md",

            "DEPLOYMENT_GUIDE.md",

            "USER_GUIDE.md"

        ]

        

        troubleshooting_found = False

        for doc in docs_with_troubleshooting:

            if os.path.exists(doc):

                with open(doc, "r", encoding="utf-8") as f:

                    content = f.read()

                    if "트러블슈팅" in content or "문제 해결" in content:

                        troubleshooting_found = True

                        break

        

        assert troubleshooting_found, "트러블슈팅 섹션을 찾을 수 없습니다"

    

    def test_contact_information_present(self):

        """연락처 정보 존재 확인"""

        with open("README.md", "r", encoding="utf-8") as f:

            content = f.read()

            assert "지원" in content or "연락" in content or "support" in content





def test_task_25_completion():

    """Task 25 전체 완료 확인"""

    required_docs = [

        "TASK_25_SUMMARY.md",

        "SYSTEM_ARCHITECTURE.md",

        "DEPLOYMENT_GUIDE.md",

        "OPERATIONS_MANUAL.md",

        "API_DOCUMENTATION.md",

        "DEVELOPER_GUIDE.md",

        "USER_GUIDE.md",

        "CHANGELOG.md",

        "README.md"

    ]

    

    missing_docs = []

    for doc in required_docs:

        if not os.path.exists(doc):

            missing_docs.append(doc)

    

    assert len(missing_docs) == 0, f"누락된 문서: {missing_docs}"

    

    print("\n" + "="*60)

    print("✅ Task 25: 문서화 및 배포 준비 완료!")

    print("="*60)

    print("\n작성된 문서:")

    for doc in required_docs:

        if os.path.exists(doc):

            size = os.path.getsize(doc)

            print(f"  ??{doc} ({size:,} bytes)")

    print("\n" + "="*60)





if __name__ == "__main__":

    pytest.main([__file__, "-v", "--tb=short"])

