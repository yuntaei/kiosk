"""인메모리 저장소. 서버를 재시작하면 주문 내역은 초기화됩니다."""

from datetime import datetime, timezone
from threading import Lock

from .models import MenuItem, Order, OrderIn, OrderLine, OrderStatus

MENU: list[MenuItem] = [
    MenuItem(id=1, name="불고기 버거", category="버거", price=6500),
    MenuItem(id=2, name="치즈 버거", category="버거", price=5500),
    MenuItem(id=3, name="치킨 버거", category="버거", price=6000),
    MenuItem(id=4, name="감자튀김", category="사이드", price=2500),
    MenuItem(id=5, name="치킨 너겟", category="사이드", price=3500),
    MenuItem(id=6, name="콜라", category="음료", price=2000),
    MenuItem(id=7, name="사이다", category="음료", price=2000),
    MenuItem(id=8, name="아이스 아메리카노", category="음료", price=2500, available=False),
]

# 허용되는 상태 전이
TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.RECEIVED: {OrderStatus.PREPARING, OrderStatus.CANCELLED},
    OrderStatus.PREPARING: {OrderStatus.READY, OrderStatus.CANCELLED},
    OrderStatus.READY: {OrderStatus.COMPLETED},
    OrderStatus.COMPLETED: set(),
    OrderStatus.CANCELLED: set(),
}

NUMBER_LIMIT = 100  # 호출 번호는 1..99 순환


class OrderError(Exception):
    """주문 처리 중 발생한 비즈니스 오류."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class Store:
    def __init__(self) -> None:
        self._lock = Lock()
        self._orders: dict[int, Order] = {}
        self._next_id = 1

    def menu(self) -> list[MenuItem]:
        return MENU

    def menu_item(self, menu_id: int) -> MenuItem | None:
        return next((m for m in MENU if m.id == menu_id), None)

    def create_order(self, data: OrderIn) -> Order:
        # 가격은 항상 서버의 메뉴 정보로 계산한다 (클라이언트 값을 신뢰하지 않음)
        lines: list[OrderLine] = []
        for line in data.items:
            item = self.menu_item(line.menu_id)
            if item is None:
                raise OrderError(f"존재하지 않는 메뉴입니다: {line.menu_id}", 404)
            if not item.available:
                raise OrderError(f"품절된 메뉴입니다: {item.name}", 409)
            lines.append(
                OrderLine(
                    menu_id=item.id,
                    name=item.name,
                    unit_price=item.price,
                    quantity=line.quantity,
                    subtotal=item.price * line.quantity,
                )
            )

        with self._lock:
            order_id = self._next_id
            self._next_id += 1
            order = Order(
                id=order_id,
                number=(order_id - 1) % (NUMBER_LIMIT - 1) + 1,
                items=lines,
                total=sum(l.subtotal for l in lines),
                created_at=datetime.now(timezone.utc),
            )
            self._orders[order_id] = order
            return order

    def get_order(self, order_id: int) -> Order | None:
        return self._orders.get(order_id)

    def list_orders(self, status: OrderStatus | None = None) -> list[Order]:
        orders = list(self._orders.values())
        if status is not None:
            orders = [o for o in orders if o.status == status]
        return orders

    def update_status(self, order_id: int, new_status: OrderStatus) -> Order:
        with self._lock:
            order = self._orders.get(order_id)
            if order is None:
                raise OrderError("주문을 찾을 수 없습니다.", 404)
            if new_status not in TRANSITIONS[order.status]:
                raise OrderError(
                    f"{order.status.value} 상태에서 {new_status.value} 상태로 변경할 수 없습니다.",
                    409,
                )
            order.status = new_status
            return order


store = Store()
