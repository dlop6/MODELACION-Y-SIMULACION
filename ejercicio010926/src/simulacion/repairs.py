"""Sistema de máquinas, repuestos fríos y exactamente un mecánico."""

from __future__ import annotations

import heapq
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
        raise ValueError(f"repair_system.{key} debe ser {names}")
    return value


@dataclass(frozen=True)
class RepairConfig:
    horizon: float
    working_machines: int
    available_spares: int
    machine_lifetime: Distribution
    repair_time: Distribution

    @classmethod
    def from_dict(cls, data: Any) -> "RepairConfig":
        if not isinstance(data, dict):
            raise ValueError("'repair_system' debe ser un objeto")
        config = cls(
            horizon=float(_required(data, "horizon", (int, float))),
            working_machines=_required(data, "working_machines", int),
            available_spares=_required(data, "available_spares", int),
            machine_lifetime=distribution_from_dict(
                data.get("machine_lifetime"),
                "repair_system.machine_lifetime",
                require_positive=True,
            ),
            repair_time=distribution_from_dict(
                data.get("repair_time"),
                "repair_system.repair_time",
                require_positive=True,
            ),
        )
        config.validate()
        return config

    def validate(self) -> None:
        if self.horizon <= 0:
            raise ValueError("repair_system.horizon debe ser mayor que cero")
        if self.working_machines <= 0:
            raise ValueError("working_machines debe ser mayor que cero")
        if self.available_spares < 0:
            raise ValueError("available_spares no puede ser negativo")


@dataclass(order=True, frozen=True)
class _Event:
    time: float
    priority: int
    sequence: int
    kind: str


class RepairSystemSimulator:
    """Simula repuestos fríos: un repuesto no falla hasta entrar a trabajar."""

    def __init__(self, config: RepairConfig) -> None:
        self.config = config

    def run(self, seed: int) -> dict[str, int | float | None]:
        cfg = self.config
        rng = Random(seed)
        events: list[_Event] = []
        sequence = 0

        def schedule(time: float, priority: int, kind: str) -> None:
            nonlocal sequence
            sequence += 1
            heapq.heappush(events, _Event(time, priority, sequence, kind))

        def schedule_failure(now: float) -> None:
            lifetime = positive_sample(cfg.machine_lifetime, rng, "machine_lifetime")
            schedule(now + lifetime, 1, "failure")

        working = cfg.working_machines
        spares = cfg.available_spares
        broken = 0
        mechanic_busy = False
        target_working = cfg.working_machines
        initial_total = working + spares
        last_time = 0.0
        working_area = spares_area = broken_area = busy_area = 0.0
        failures = repairs_completed = replacements = 0
        first_system_failure: float | None = None

        def start_repair(now: float) -> None:
            nonlocal mechanic_busy
            if broken > 0 and not mechanic_busy:
                mechanic_busy = True
                duration = positive_sample(cfg.repair_time, rng, "repair_time")
                schedule(now + duration, 0, "repair_complete")

        for _ in range(working):
            schedule_failure(0.0)

        while events:
            event = heapq.heappop(events)
            if event.time > cfg.horizon:
                break
            elapsed = event.time - last_time
            working_area += working * elapsed
            spares_area += spares * elapsed
            broken_area += broken * elapsed
            busy_area += int(mechanic_busy) * elapsed
            last_time = event.time

            if event.kind == "failure":
                working -= 1
                broken += 1
                failures += 1
                if spares > 0:
                    spares -= 1
                    working += 1
                    replacements += 1
                    schedule_failure(event.time)
                if working == 0 and first_system_failure is None:
                    first_system_failure = event.time
                start_repair(event.time)
                continue

            broken -= 1
            repairs_completed += 1
            mechanic_busy = False
            if working < target_working:
                working += 1
                schedule_failure(event.time)
            else:
                spares += 1
            start_repair(event.time)

            if working + spares + broken != initial_total:
                raise RuntimeError("se violó la conservación de máquinas")

        remaining = cfg.horizon - last_time
        working_area += working * remaining
        spares_area += spares * remaining
        broken_area += broken * remaining
        busy_area += int(mechanic_busy) * remaining
        availability = min(1.0, max(0.0, working_area / (target_working * cfg.horizon)))
        mechanic_utilization = min(1.0, max(0.0, busy_area / cfg.horizon))
        average_working = min(float(target_working), max(0.0, working_area / cfg.horizon))
        return {
            "horizon": cfg.horizon,
            "ending_working_machines": working,
            "ending_available_spares": spares,
            "ending_broken_machines": broken,
            "mechanic_busy_at_end": int(mechanic_busy),
            "failures": failures,
            "repairs_completed": repairs_completed,
            "replacements": replacements,
            "average_working_machines": average_working,
            "average_available_spares": spares_area / cfg.horizon,
            "average_broken_machines": broken_area / cfg.horizon,
            "machine_availability": availability,
            "mechanic_utilization": mechanic_utilization,
            "time_to_first_total_stoppage": first_system_failure,
        }
