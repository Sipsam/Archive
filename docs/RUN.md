# 실행 요약 — v2.8.0

```powershell
pip install -r requirements.txt
Copy-Item .env.example .env
streamlit run app.py
```

필수 환경변수는 `OPENAI_API_KEY`이며 Riot 데이터 신규 수집 시 `RIOT_API_KEY`도 필요합니다. 실제 키는 저장소에 커밋하지 않습니다.

권장 기본값:

- Model: `gpt-5.4`
- Reasoning effort: `none`
- API: `Responses API`

상세한 데이터 구조, 보안 주의사항, 테스트 및 기능 한계는 [README.md](../README.md)를 확인하십시오.
