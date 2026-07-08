# Scenario 01 - Burst Meta Overpower

Mira/Selene/Iris 조합이 패치 이후 과도한 순간 화력으로 높은 승률을 기록하는 시나리오입니다.

## 예상 분석 포인트

Mira/Selene/Iris + Assassin 조합의 순간 화력 과상승 여부를 중점적으로 확인하세요.

## 포함 파일

- battle_logs.csv
- characters.csv
- skills.csv
- equipment_sets.csv
- patch_notes.csv
- agent_prompt_v2.txt

## 사용 방법

1. Battle Balance Analyst Generative AI Agent v2 실행
2. 이 폴더의 CSV 5개를 각각 업로드
3. agent_prompt_v2.txt 내용을 Agent 목표 입력창에 붙여넣기
4. OpenAI API Key 입력
5. 생성형 AI Agent 실행

## 기대되는 Tool 호출 흐름

- get_dataset_overview
- detect_anomalies
- analyze_patch_impact
- analyze_segment_performance
- retrieve_related_knowledge
- simulate_stat_impact
- calculate_adjustment_options
- assess_balance_risk
- generate_retest_plan
