# Scenario 03 - Advanced Segment Meta

Noah/Kain/Evan 조합이 특히 advanced 유저 구간에서 과성능을 보이는 시나리오입니다.

## 예상 분석 포인트

Noah/Kain/Evan + Vanguard 조합의 전체 이상 여부와 advanced 세그먼트 집중 여부를 확인하세요.

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
