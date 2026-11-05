# Kiosk

FastAPI로 만든 주문 키오스크입니다. 터치 화면용 주문 UI와 REST API를 함께 제공합니다.

## 실행

```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows(Git Bash). PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

- 키오스크 화면: http://127.0.0.1:8000/
- API 문서(Swagger): http://127.0.0.1:8000/docs

## API

| Method | Path | 설명 |
| --- | --- | --- |
| GET | `/api/menu?category=` | 메뉴 목록 (카테고리 필터) |
| GET | `/api/menu/{id}` | 메뉴 상세 |
| POST | `/api/orders` | 주문 생성 (금액은 서버가 계산) |
| GET | `/api/orders?status=` | 주문 목록 |
| GET | `/api/orders/{id}` | 주문 조회 |
| PATCH | `/api/orders/{id}/status` | 주문 상태 변경 |

주문 상태 흐름: `received → preparing → ready → completed` (`received`/`preparing`에서는 `cancelled` 가능)

## 테스트

```bash
pytest
```

## 참고

주문은 인메모리로 저장되므로 서버를 재시작하면 초기화됩니다. 메뉴는 `app/store.py`의 `MENU`에서 수정합니다.
