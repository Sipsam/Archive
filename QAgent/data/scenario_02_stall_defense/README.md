# Scenario 02 - Stall Defense Overpower

Evan/Rin/Darius 조합이 방어력과 회복량 상승으로 장기전에서 비정상적 승률을 보이는 시나리오입니다.

## 예상 분석 포인트

Evan/Rin/Darius + Guardian 조합이 전투 시간을 과도하게 늘리고 승률이 높아지는지 확인하세요.

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
