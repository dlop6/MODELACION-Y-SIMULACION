"""asignar la mayor cantidad de pasajeros diarios de guatemala a xela gastando lo menos en combustible."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from algoritmos.min_cost_flow import FlowNetwork, FlowResult, min_cost_max_flow
from algoritmos.validation import require_int

ORIGIN = "Ciudad de Guatemala"
DESTINATION = "Quetzaltenango"


@dataclass(frozen=True)
class BusRoute:
    origin: str
    destination: str
    buses_per_day: int
    seats_per_bus: int
    fuel_cost_per_passenger: int  # quetzales

    def __post_init__(self) -> None:
        require_int(self.buses_per_day, "buses_per_day", minimum=1)
        require_int(self.seats_per_bus, "seats_per_bus", minimum=1)

    @property
    def capacity(self) -> int:
        return self.buses_per_day * self.seats_per_bus


# datos inventados pero con rutas reales: la interamericana (ca-1) y la costera (ca-2)
ROUTES = (
    BusRoute(ORIGIN, "Chimaltenango", 10, 40, 8),
    BusRoute("Chimaltenango", "Tecpán", 8, 40, 6),
    BusRoute("Tecpán", "Los Encuentros", 7, 40, 7),
    BusRoute("Los Encuentros", "Cuatro Caminos", 6, 40, 9),
    BusRoute("Cuatro Caminos", DESTINATION, 5, 40, 4),
    BusRoute("Cuatro Caminos", "Totonicapán", 4, 30, 3),
    BusRoute("Totonicapán", DESTINATION, 3, 30, 5),
    BusRoute(ORIGIN, "Escuintla", 6, 45, 7),
    BusRoute("Escuintla", "Mazatenango", 4, 45, 15),
    BusRoute("Mazatenango", DESTINATION, 3, 45, 14),
)


def plan_passengers(routes: Sequence[BusRoute], origin: str, destination: str) -> FlowResult:
    network = FlowNetwork()
    for route in routes:
        network.add_arc(
            route.origin, route.destination, route.capacity, route.fuel_cost_per_passenger
        )
    return min_cost_max_flow(network, origin, destination)


def main() -> None:
    result = plan_passengers(ROUTES, ORIGIN, DESTINATION)
    print(f"pasajeros diarios de {ORIGIN} a {DESTINATION}: {result.total_flow}")
    print(f"costo total de combustible: Q{result.total_cost}\n")
    for arc, passengers in result.arc_flows:
        print(f"{arc.source} -> {arc.target}: {passengers}/{arc.capacity} pasajeros")


if __name__ == "__main__":
    main()
