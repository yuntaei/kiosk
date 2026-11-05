from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .models import MenuItem, Order, OrderIn, OrderStatus, StatusUpdate
from .store import OrderError, store

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="Kiosk API", version="0.1.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.exception_handler(OrderError)
async def order_error_handler(_: Request, exc: OrderError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/menu", response_model=list[MenuItem])
def list_menu(category: str | None = None) -> list[MenuItem]:
    items = store.menu()
    if category:
        items = [m for m in items if m.category == category]
    return items


@app.get("/api/menu/{menu_id}", response_model=MenuItem)
def get_menu_item(menu_id: int) -> MenuItem:
    item = store.menu_item(menu_id)
    if item is None:
        raise HTTPException(status_code=404, detail="존재하지 않는 메뉴입니다.")
    return item


@app.post("/api/orders", response_model=Order, status_code=201)
def create_order(data: OrderIn) -> Order:
    return store.create_order(data)


@app.get("/api/orders", response_model=list[Order])
def list_orders(status: OrderStatus | None = None) -> list[Order]:
    return store.list_orders(status)


@app.get("/api/orders/{order_id}", response_model=Order)
def get_order(order_id: int) -> Order:
    order = store.get_order(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="주문을 찾을 수 없습니다.")
    return order


@app.patch("/api/orders/{order_id}/status", response_model=Order)
def update_order_status(order_id: int, body: StatusUpdate) -> Order:
    return store.update_status(order_id, body.status)
