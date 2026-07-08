# Scenario 04 - Luna Vanguard Combo

Luna/Arthur/Kain 조합이 Moon Slash, Critical Order, Vanguard 상향이 중첩되어 과성능을 보이는 시나리오입니다.

## 예상 분석 포인트

Luna/Arthur/Kain + Vanguard 조합에서 스킬 계수, 치명타 버프, 공격 세트 효과가 중첩되는지 확인하세요.

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
