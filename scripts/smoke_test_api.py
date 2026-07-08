"""Minimal, non-destructive connectivity checks for OpenAI and Riot APIs.

The script performs at most one request per configured provider. It never prints
secret values and does not import or mutate the Streamlit application state.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass

import requests
from dotenv import load_dotenv


@dataclass(frozen=True)
class CheckResult:
    provider: str
    status: str
    detail: str


def _secret_exists(name: str) -> bool:
    return bool(os.getenv(name, "").strip())


def check_openai() -> CheckResult:
    if not _secret_exists("OPENAI_API_KEY"):
        return CheckResult(
            "OpenAI", "SKIP",
            "OPENAI_API_KEY가 없습니다. .env.example을 참고해 환경변수를 설정하세요.",
        )

    model = os.getenv("OPENAI_MODEL", "gpt-5.4").strip() or "gpt-5.4"
    try:
        from openai import APIConnectionError, APIStatusError, AuthenticationError, OpenAI, RateLimitError

        # Model metadata lookup validates network, authentication, and model access
        # without generating tokens or invoking the Responses API.
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"], timeout=10.0, max_retries=0)
        client.models.retrieve(model)
        return CheckResult("OpenAI", "SUCCESS", f"인증 및 모델 접근 확인 완료: {model}")
    except AuthenticationError:
        return CheckResult("OpenAI", "FAIL", "인증에 실패했습니다. 키의 유효성과 프로젝트 권한을 확인하세요.")
    except RateLimitError:
        return CheckResult("OpenAI", "FAIL", "Rate limit 또는 사용 한도에 도달했습니다. 잠시 후 한도를 확인하세요.")
    except APIConnectionError:
        return CheckResult("OpenAI", "FAIL", "네트워크 연결에 실패했습니다. DNS, 프록시, 방화벽을 확인하세요.")
    except APIStatusError as error:
        return CheckResult("OpenAI", "FAIL", f"API가 HTTP {error.status_code} 상태를 반환했습니다. 모델 접근 권한을 확인하세요.")
    except Exception as error:
        return CheckResult("OpenAI", "FAIL", f"예상하지 못한 오류가 발생했습니다({type(error).__name__}). 키 값은 출력하지 않았습니다.")


def check_riot() -> CheckResult:
    if not _secret_exists("RIOT_API_KEY"):
        return CheckResult(
            "Riot", "SKIP",
            "RIOT_API_KEY가 없습니다. Riot 데이터 신규 수집을 검증하려면 환경변수를 설정하세요.",
        )

    # One read-only platform-status request; no account or match identifiers are sent.
    url = "https://kr.api.riotgames.com/lol/status/v4/platform-data"
    try:
        response = requests.get(
            url,
            headers={"X-Riot-Token": os.environ["RIOT_API_KEY"], "Accept": "application/json"},
            timeout=10,
        )
    except requests.Timeout:
        return CheckResult("Riot", "FAIL", "요청 시간이 초과되었습니다. 네트워크 또는 Riot API 상태를 확인하세요.")
    except requests.ConnectionError:
        return CheckResult("Riot", "FAIL", "네트워크 연결에 실패했습니다. DNS, 프록시, 방화벽을 확인하세요.")
    except requests.RequestException as error:
        return CheckResult("Riot", "FAIL", f"요청 처리 오류가 발생했습니다({type(error).__name__}). 키 값은 출력하지 않았습니다.")

    if response.status_code == 200:
        return CheckResult("Riot", "SUCCESS", "KR 플랫폼 상태 API 연결 및 인증 확인 완료")
    if response.status_code in {401, 403}:
        return CheckResult("Riot", "FAIL", "인증에 실패했습니다. 키의 유효성, 만료 여부와 권한을 확인하세요.")
    if response.status_code == 429:
        return CheckResult("Riot", "FAIL", "Rate limit에 도달했습니다. Retry-After 이후 다시 실행하세요.")
    if response.status_code >= 500:
        return CheckResult("Riot", "FAIL", f"Riot 서버가 HTTP {response.status_code} 상태를 반환했습니다. 잠시 후 다시 실행하세요.")
    return CheckResult("Riot", "FAIL", f"Riot API가 HTTP {response.status_code} 상태를 반환했습니다.")


def main() -> int:
    load_dotenv()
    print("API smoke test 시작 (키 값은 출력하지 않습니다).")
    results = [check_openai(), check_riot()]
    for result in results:
        print(f"[{result.status}] {result.provider}: {result.detail}")

    failures = sum(result.status == "FAIL" for result in results)
    successes = sum(result.status == "SUCCESS" for result in results)
    skipped = sum(result.status == "SKIP" for result in results)
    print(f"요약: success={successes}, fail={failures}, skip={skipped}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
