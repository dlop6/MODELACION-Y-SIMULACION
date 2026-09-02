"""Banco con una cola FIFO compartida y cajeros paralelos."""

from __future__ import annotations

import heapq
from collections import deque
from dataclasses import dataclass
from random import Random
from typing import Any

from .distributions import Distribution, distribution_from_dict, positive_sample


def _required(data: dict[str, Any], key: str, expected: type | tuple[type, ...]) -> Any:
    value = data.get(key)
    if isinstance(value, bool) or not isinstance(value, expected):
        names = expected.__name__ if isinstance(expected, type) else " o ".join(
            item.__name__ for item in expected
        )
        raise ValueError(f"bank.{key} debe ser {names}")
    return value


@dataclass(frozen=True)
class BankConfig:
    horizon: float
    tellers: int
    customer_interarrival: Distribution
    service_time: Distribution

    @classmethod
    def from_dict(cls, data: Any) -> "BankConfig":
        if not isinstance(data, dict):
            raise ValueError("'bank' debe ser un objeto")
        config = cls(
            horizon=float(_required(data, "horizon", (int, float))),
            tellers=_required(data, "tellers", int),
            customer_interarrival=distribution_from_dict(
                data.get("customer_interarrival"),
                "bank.customer_interarrival",
                require_positive=True,
            ),
            service_time=distribution_from_dict(
                data.get("service_time"),
                "bank.service_time",
                require_positive=True,
            ),
        )
        config.validate()
        return config

    def validate(self) -> None:
        if self.horizon <= 0:
            raise ValueError("bank.horizon debe ser mayor que cero")
        if self.tellers <= 0:
            raise ValueError("bank.tellers debe ser mayor que cero")


@dataclass(order=True, frozen=True)
class _Event:
    time: float
    priority: int
    sequence: int
    kind: str
    customer_id: int = 0


class BankSimulator:
    """Ejecuta una réplica del banco sin conservar estado entre corridas."""

    def __init__(self, config: BankConfig) -> None:
        self.config = config

    def run(self, seed: int) -> dict[str, int | float]:
        cfg = self.config
        rng = Random(seed)
        events: list[_Event] = []
        waiting: deque[int] = deque()
        active_arrivals: dict[int, float] = {}
        sequence = 0

        def schedule(time: float, priority: int, kind: str, customer_id: int = 0) -> None:
            nonlocal sequence
            sequence += 1
            heapq.heappush(events, _Event(time, priority, sequence, kind, customer_id))

        busy_tellers = 0
        arrivals = completed = service_starts = 0
        total_wait_started = total_sojourn_completed = 0.0
        observed_queue_time = 0.0
        last_time = queue_area = system_area = busy_area = 0.0

        def start_services(now: float) -> None:
            nonlocal busy_tellers, service_starts, total_wait_started
            nonlocal observed_queue_time
            while waiting and busy_tellers < cfg.tellers:
                customer_id = waiting.popleft()
                wait = now - active_arrivals[customer_id]
                observed_queue_time += wait
                total_wait_started += wait
                service_starts += 1
                busy_tellers += 1
                duration = positive_sample(cfg.service_time, rng, "service_time")
                schedule(now + duration, 0, "departure", customer_id)

        first_arrival = positive_sample(
            cfg.customer_interarrival, rng, "customer_interarrival"
        )
        schedule(first_arrival, 1, "arrival")

        while events:
            event = heapq.heappop(events)
            if event.time > cfg.horizon:
                break
            elapsed = event.time - last_time
            queue_area += len(waiting) * elapsed
            system_area += len(active_arrivals) * elapsed
            busy_area += busy_tellers * elapsed
            last_time = event.time

            if event.kind == "departure":
                busy_tellers -= 1
                completed += 1
                arrival_time = active_arrivals.pop(event.customer_id)
                total_sojourn_completed += event.time - arrival_time
                start_services(event.time)
                continue

            arrivals += 1
            customer_id = arrivals
            active_arrivals[customer_id] = event.time
            waiting.append(customer_id)
            start_services(event.time)
            next_arrival = event.time + positive_sample(
                cfg.customer_interarrival, rng, "customer_interarrival"
            )
            schedule(next_arrival, 1, "arrival")

        remaining = cfg.horizon - last_time
        queue_area += len(waiting) * remaining
        system_area += len(active_arrivals) * remaining
        busy_area += busy_tellers * remaining

        observed_system_time = total_sojourn_completed + sum(
            cfg.horizon - arrival_time for arrival_time in active_arrivals.values()
        )
        observed_queue_time += sum(
            cfg.horizon - active_arrivals[customer_id] for customer_id in waiting
        )
        arrival_rate = arrivals / cfg.horizon
        observed_time_in_system = observed_system_time / arrivals if arrivals else 0.0
        observed_wait = observed_queue_time / arrivals if arrivals else 0.0
        average_in_system = system_area / cfg.horizon
        average_in_queue = queue_area / cfg.horizon
        little_system_rhs = arrival_rate * observed_time_in_system
        little_queue_rhs = arrival_rate * observed_wait

        return {
            "horizon": cfg.horizon,
            "tellers": cfg.tellers,
            "arrivals": arrivals,
            "customers_served": completed,
            "customers_in_queue_at_end": len(waiting),
            "customers_in_system_at_end": len(active_arrivals),
            "average_customers_in_queue": average_in_queue,
            "average_customers_in_system": average_in_system,
            "average_wait_for_started_services": (
                total_wait_started / service_starts if service_starts else 0.0
            ),
            "average_time_for_completed_customers": (
                total_sojourn_completed / completed if completed else 0.0
            ),
            "teller_utilization": busy_area / (cfg.tellers * cfg.horizon),
            "little_arrival_rate": arrival_rate,
            "little_observed_time_in_system": observed_time_in_system,
            "little_system_lambda_times_w": little_system_rhs,
            "little_system_absolute_error": abs(average_in_system - little_system_rhs),
            "little_observed_wait_in_queue": observed_wait,
            "little_queue_lambda_times_w": little_queue_rhs,
            "little_queue_absolute_error": abs(average_in_queue - little_queue_rhs),
        }
