"""Interfaz de línea de comandos."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .bank import BankConfig, BankSimulator
from .comparison import compare_metrics
from .inventory import InventoryConfig, InventorySimulator
from .repairs import RepairConfig, RepairSystemSimulator


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ValueError(f"no existe el archivo: {path}") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"JSON inválido en {path}: {error}") from error
    if not isinstance(data, dict):
        raise ValueError(f"la raíz de {path} debe ser un objeto JSON")
    return data


def run(
    config_data: dict[str, Any], actual_data: dict[str, Any] | None = None
) -> dict[str, Any]:
    seed = config_data.get("seed")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("'seed' debe ser un entero")
    bank = BankSimulator(BankConfig.from_dict(config_data.get("bank"))).run(seed)
    inventory = InventorySimulator(
        InventoryConfig.from_dict(config_data.get("inventory"))
    ).run(seed)
    repair_system = RepairSystemSimulator(
        RepairConfig.from_dict(config_data.get("repair_system"))
    ).run(seed)
    result: dict[str, Any] = {
        "seed": seed,
        "bank": bank,
        "inventory": inventory,
        "repair_system": repair_system,
    }
    if actual_data is not None:
        unknown = set(actual_data) - {"bank", "inventory", "repair_system"}
        if unknown:
            raise ValueError(f"modelos reales desconocidos: {', '.join(sorted(unknown))}")
        result["comparison"] = {
            model: compare_metrics(result[model], metrics)
            for model, metrics in actual_data.items()
        }
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Simula un banco, inventario y máquinas con repuestos."
    )
    parser.add_argument("config", type=Path, help="configuración JSON")
    parser.add_argument("--actual", type=Path, help="valores reales JSON para comparar")
    parser.add_argument("--output", type=Path, help="guarda el resultado JSON en esta ruta")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config_data = _read_json(args.config)
        actual_data = _read_json(args.actual) if args.actual else None
        result = run(config_data, actual_data)
        rendered = json.dumps(result, ensure_ascii=False, indent=2)
        if args.output:
            args.output.write_text(rendered + "\n", encoding="utf-8")
        else:
            print(rendered)
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    return 0
