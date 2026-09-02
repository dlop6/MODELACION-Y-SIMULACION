"""Modelo de inventario de revisión continua (s, Q)."""

from __future__ import annotations

import heapq
from dataclasses import dataclass
from random import Random
from typing import Any

from .distributions import (
    Distribution,
    distribution_from_dict,
    positive_integer_sample,
    positive_sample,
)


def _required(data: dict[str, Any], key: str, expected: type | tuple[type, ...]) -> Any:
    value = data.get(key)
    if isinstance(value, bool) or not isinstance(value, expected):
        names = expected.__name__ if isinstance(expected, type) else " o ".join(
            item.__name__ for item in expected
        )
        raise ValueError(f"inventario.{key} debe ser {names}")
    return value


@dataclass(frozen=True)
class InventoryConfig:
    horizon: float
    initial_units: int
    product_limit: int
    shortage_threshold: int
    reorder_point: int
    order_quantity: int
    max_open_orders: int
    shortage_policy: str
    demand_interarrival: Distribution
    demand_size: Distribution
    order_lead_time: Distribution
    unit_order_cost: float
    fixed_order_cost: float
    holding_cost_per_unit_time: float
    sale_price: float

    @classmethod
    def from_dict(cls, data: Any) -> "InventoryConfig":
        if not isinstance(data, dict):
            raise ValueError("'inventory' debe ser un objeto")
        config = cls(
            horizon=float(_required(data, "horizon", (int, float))),
            initial_units=_required(data, "initial_units", int),
            product_limit=_required(data, "product_limit", int),
            shortage_threshold=_required(data, "shortage_threshold", int),
            reorder_point=_required(data, "reorder_point", int),
            order_quantity=_required(data, "order_quantity", int),
            max_open_orders=_required(data, "max_open_orders", int),
            shortage_policy=_required(data, "shortage_policy", str),
            demand_interarrival=distribution_from_dict(
                data.get("demand_interarrival"),
                "inventory.demand_interarrival",
                require_positive=True,
            ),
            demand_size=distribution_from_dict(
                data.get("demand_size"),
                "inventory.demand_size",
                require_positive=True,
                require_integer=True,
            ),
            order_lead_time=distribution_from_dict(
                data.get("order_lead_time"),
                "inventory.order_lead_time",
                require_positive=True,
            ),
            unit_order_cost=float(_required(data, "unit_order_cost", (int, float))),
            fixed_order_cost=float(_required(data, "fixed_order_cost", (int, float))),
            holding_cost_per_unit_time=float(
                _required(data, "holding_cost_per_unit_time", (int, float))
            ),
            sale_price=float(_required(data, "sale_price", (int, float))),
        )
        config.validate()
        return config

    def validate(self) -> None:
        if self.horizon <= 0:
            raise ValueError("inventory.horizon debe ser mayor que cero")
        integer_values = {
            "initial_units": self.initial_units,
            "product_limit": self.product_limit,
            "shortage_threshold": self.shortage_threshold,
            "reorder_point": self.reorder_point,
            "order_quantity": self.order_quantity,
            "max_open_orders": self.max_open_orders,
        }
        if any(value < 0 for value in integer_values.values()):
            raise ValueError("los conteos de inventario no pueden ser negativos")
        if self.product_limit == 0 or self.order_quantity == 0 or self.max_open_orders == 0:
            raise ValueError("product_limit, order_quantity y max_open_orders deben ser > 0")
        if self.initial_units > self.product_limit:
            raise ValueError("initial_units no puede superar product_limit")
        if self.shortage_threshold > self.product_limit:
            raise ValueError("shortage_threshold no puede superar product_limit")
        if self.reorder_point >= self.product_limit:
            raise ValueError("reorder_point debe ser menor que product_limit")
        if self.shortage_policy not in {"lost_sales", "backorder"}:
            raise ValueError("shortage_policy debe ser 'lost_sales' o 'backorder'")
        costs = (
            self.unit_order_cost,
            self.fixed_order_cost,
            self.holding_cost_per_unit_time,
            self.sale_price,
        )
        if any(value < 0 for value in costs):
            raise ValueError("costos y precio no pueden ser negativos")


@dataclass(order=True, frozen=True)
class _Event:
    time: float
    priority: int
    sequence: int
    kind: str
    quantity: int = 0


class InventorySimulator:
    """Ejecuta una réplica sin conservar estado entre ejecuciones."""

    def __init__(self, config: InventoryConfig) -> None:
        self.config = config

    def run(self, seed: int) -> dict[str, int | float]:
        cfg = self.config
        rng = Random(seed)
        events: list[_Event] = []
        sequence = 0

        def schedule(time: float, priority: int, kind: str, quantity: int = 0) -> None:
            nonlocal sequence
            sequence += 1
            heapq.heappush(events, _Event(time, priority, sequence, kind, quantity))

        on_hand = cfg.initial_units
        backlog = 0
        pending_orders: list[int] = []
        last_time = 0.0
        inventory_area = 0.0
        ordered_area = 0.0
        backlog_area = 0.0
        units_demanded = units_sold = units_lost = 0
        orders_placed = units_ordered = shortage_notifications = 0
        ordering_cost = revenue = 0.0
        low_stock_active = False

        def on_order() -> int:
            return sum(pending_orders)

        def update_shortage_notification() -> None:
            nonlocal low_stock_active, shortage_notifications
            is_low = on_hand <= cfg.shortage_threshold
            if is_low and not low_stock_active:
                shortage_notifications += 1
            low_stock_active = is_low

        def reorder(now: float) -> None:
            nonlocal orders_placed, units_ordered, ordering_cost
            while (
                on_hand + on_order() - backlog <= cfg.reorder_point
                and len(pending_orders) < cfg.max_open_orders
            ):
                available_capacity = cfg.product_limit - on_hand - on_order()
                quantity = min(cfg.order_quantity, available_capacity)
                if quantity <= 0:
                    break
                pending_orders.append(quantity)
                orders_placed += 1
                units_ordered += quantity
                ordering_cost += cfg.fixed_order_cost + quantity * cfg.unit_order_cost
                lead_time = positive_sample(cfg.order_lead_time, rng, "order_lead_time")
                schedule(now + lead_time, 0, "delivery", quantity)

        update_shortage_notification()
        reorder(0.0)
        first_demand = positive_sample(cfg.demand_interarrival, rng, "demand_interarrival")
        schedule(first_demand, 1, "demand")

        while events:
            event = heapq.heappop(events)
            if event.time > cfg.horizon:
                break
            elapsed = event.time - last_time
            inventory_area += on_hand * elapsed
            ordered_area += on_order() * elapsed
            backlog_area += backlog * elapsed
            last_time = event.time

            if event.kind == "delivery":
                pending_orders.remove(event.quantity)
                delivered = event.quantity
                if cfg.shortage_policy == "backorder" and backlog:
                    filled = min(delivered, backlog)
                    backlog -= filled
                    units_sold += filled
                    revenue += filled * cfg.sale_price
                    delivered -= filled
                on_hand += delivered
                update_shortage_notification()
                reorder(event.time)
                continue

            demand = positive_integer_sample(cfg.demand_size, rng, "demand_size")
            units_demanded += demand
            sold_now = min(on_hand, demand)
            on_hand -= sold_now
            units_sold += sold_now
            revenue += sold_now * cfg.sale_price
            unmet = demand - sold_now
            if cfg.shortage_policy == "backorder":
                backlog += unmet
            else:
                units_lost += unmet
            update_shortage_notification()
            reorder(event.time)
            next_time = event.time + positive_sample(
                cfg.demand_interarrival, rng, "demand_interarrival"
            )
            schedule(next_time, 1, "demand")

        remaining = cfg.horizon - last_time
        inventory_area += on_hand * remaining
        ordered_area += on_order() * remaining
        backlog_area += backlog * remaining
        holding_cost = inventory_area * cfg.holding_cost_per_unit_time
        fill_rate = units_sold / units_demanded if units_demanded else 1.0
        return {
            "horizon": cfg.horizon,
            "ending_units_now": on_hand,
            "ending_units_ordered": on_order(),
            "ending_backlog": backlog,
            "units_demanded": units_demanded,
            "units_sold": units_sold,
            "units_lost": units_lost,
            "orders_placed": orders_placed,
            "total_units_ordered": units_ordered,
            "shortage_notifications": shortage_notifications,
            "fill_rate": fill_rate,
            "average_units_now": inventory_area / cfg.horizon,
            "average_units_ordered": ordered_area / cfg.horizon,
            "average_backlog": backlog_area / cfg.horizon,
            "C_ordering_cost": ordering_cost,
            "H_holding_cost": holding_cost,
            "R_sales_revenue": revenue,
            "net_result": revenue - ordering_cost - holding_cost,
        }
