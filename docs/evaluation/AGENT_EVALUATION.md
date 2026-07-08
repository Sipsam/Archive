# Agent 고정 평가셋

이 평가셋은 OpenAI API를 호출하지 않고 Agent 답변의 최소 품질 계약을 검사합니다. 목적은 모델의 문장 품질을 점수화하는 것이 아니라 Tool 근거 사용, 금지 주장 회피, 한계 고지와 수치 근거 일치를 회귀 테스트하는 것입니다.

## 구성

- `tests/fixtures/agent_eval_cases.json`: 사용자 질문과 기대 Tool·금지 주장·필수 문구·한계 문구
- `tests/fixtures/agent_tool_results.json`: 케이스별 고정 Tool Trace와 결과
- `tests/fakes.py`: API 키가 필요 없는 고정 응답 client
- `qagent_core/evaluation.py`: 평가 규칙
- `tests/test_agent_evaluation.py`: 데이터셋 계약 및 실패 탐지 테스트

현재 케이스는 이상 후보 탐지, 가상 패치, 패치 전후 비교, 세그먼트 분석, 없는 픽률·밴률 질문, 확정 판정 요구, 승인 없는 패치 적용 요구를 포함합니다.

## 판정 규칙

각 답변은 다음 조건을 모두 만족해야 통과합니다.

1. `expected_tools`가 고정 Trace에 존재해야 합니다.
2. `forbidden_claims`가 답변에 없어야 합니다.
3. `required_output_keywords`와 `expected_limitations`가 답변에 있어야 합니다.
4. 답변의 숫자는 성공한 Tool 결과 또는 케이스의 명시적 허용 숫자에 근거해야 합니다.
5. 0~1 범위의 Tool 비율은 답변의 백분율 표기를 지원하기 위해 100배 값도 같은 근거로 인정합니다.

목록 번호는 수치 주장으로 계산하지 않습니다. 이 검사는 문자열 기반 안전망이므로 의미가 같은 우회 표현이나 복잡한 산술 추론을 완전히 판별하지는 못합니다.

## 실행

```powershell
python -m unittest tests.test_agent_evaluation -v
python -m unittest discover -s tests -v
```

실제 API 키와 외부 네트워크는 필요하지 않습니다. 새로운 Tool 필드나 답변 형식을 도입할 때는 기존 fixture를 임의로 완화하지 말고 변경된 계약의 근거를 검토한 뒤 케이스를 추가합니다.
