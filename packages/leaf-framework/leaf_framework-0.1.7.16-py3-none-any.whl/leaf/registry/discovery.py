import logging
import os
import importlib.util
import json
import os
from importlib.metadata import entry_points
from typing import Optional, Type, Any, List

from leaf.utility.logger.logger_utils import get_logger
from leaf.adapters.equipment_adapter import EquipmentAdapter
from leaf.modules.input_modules.external_event_watcher import ExternalEventWatcher
from leaf.modules.output_modules.output_module import OutputModule
from leaf.registry.loader import load_class_from_file
from leaf.registry.utils import ADAPTER_ID_KEY

# Base directories for discovery
root_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")
adapter_dir = os.path.join(root_dir, "adapters")
core_adapter_dir = os.path.join(adapter_dir, "core_adapters")
functional_adapter_dir = os.path.join(adapter_dir, "functional_adapters")
default_equipment_locations = [core_adapter_dir, functional_adapter_dir]

output_module_dir = os.path.join(root_dir, "modules", "output_modules")
input_module_dir = os.path.join(root_dir, "modules", "input_modules")

logger = get_logger(__name__, log_file="discovery.log")

def discover_entry_point_equipment(
    needed_codes: set[str] = None,
    group: str = "leaf.adapters",
) -> list[tuple[str, Any, Any]]:
    """
    Discover only necessary equipment adapters exposed via setuptools entry points.
    """
    discovered: list[tuple[str, Any, Any]] = []

    for entry_point in entry_points(group=group):
        logger.debug("Found entry point: %s", entry_point)
        try:
            module_path = entry_point.module
            spec = importlib.util.find_spec(module_path)
            if not spec or not spec.origin:
                continue

            module_dir = os.path.dirname(spec.origin)
            device_json_path = os.path.join(module_dir, "device.json")

            if not os.path.exists(device_json_path):
                logger.warning("Missing device.json for %s", module_path)
                continue

            with open(device_json_path, "r") as f:
                device_info = json.load(f)
                adapter_id: str = device_info.get("adapter_id")

                if needed_codes is not None and (
                    not adapter_id or adapter_id.lower() not in needed_codes
                ):
                    continue

                cls = entry_point.load()
                discovered.append((adapter_id, cls, entry_point))

        except Exception as e:
            logger.error("Failed loading adapter (%s) :: %s", entry_point.module, e)
            continue

    return discovered


def discover_local_equipment(
    needed_codes: set[str],
    base_dirs: Optional[list[str]] = None,
) -> list[tuple[str, Type[EquipmentAdapter], str]]:
    """
    Discover and load only the required equipment adapters from local paths.
    """
    discovered: list[tuple[str, Type[EquipmentAdapter], str]] = []
    search_dirs = list(set((base_dirs or []) + default_equipment_locations))

    for base in search_dirs:
        if not os.path.exists(base):
            continue

        for root, _, files in os.walk(base):
            if "device.json" in files and "adapter.py" in files:
                json_fp = os.path.join(root, "device.json")
                py_fp = os.path.join(root, "adapter.py")

                try:
                    with open(json_fp, "r") as f:
                        data = json.load(f)
                        code = data.get(ADAPTER_ID_KEY)

                    if code and code.lower() in needed_codes:
                        cls = load_class_from_file(py_fp, base_class=EquipmentAdapter)
                        discovered.append((code, cls, 'local'))

                except Exception:
                    continue

    return discovered


def discover_output_modules(
    needed_codes: set[str],
) -> list[tuple[str, Type[OutputModule]]]:
    """
    Discover only the required output modules in the output module directory.
    """
    discovered: list[tuple[str, Type[OutputModule]]] = []

    if not os.path.exists(output_module_dir):
        return discovered

    for file in os.listdir(output_module_dir):
        if file.endswith(".py"):
            module_name = file[:-3]
            if module_name.lower() not in needed_codes:
                continue

            path = os.path.join(output_module_dir, file)
            try:
                cls = load_class_from_file(path, base_class=OutputModule)
                discovered.append((module_name, cls))
            except Exception:
                continue

    return discovered


def discover_external_inputs(
    needed_codes: set[str],
) -> list[tuple[str, Type[ExternalEventWatcher]]]:
    """
    Discover only the required external input modules in the input module directory.
    """
    discovered: list[tuple[str, Type[ExternalEventWatcher]]] = []

    if not os.path.exists(input_module_dir):
        return discovered

    for file in os.listdir(input_module_dir):
        if file.endswith(".py"):
            module_name = file[:-3]  # strip .py
            if module_name.lower() not in needed_codes:
                continue

            path = os.path.join(input_module_dir, file)
            try:
                cls = load_class_from_file(path, base_class=ExternalEventWatcher)
                discovered.append((module_name, cls))
            except Exception:
                continue

    return discovered


def get_all_adapter_codes() -> list[dict[str, str]]:
    """
    Returns all the adapter info available.
    """
    available_equipment = discover_entry_point_equipment()
    # Dictionary with more information than just the name
    equipment: list[dict[str, str]] = []
    for code, cls, entry_point in available_equipment:
        module = {
            'code': code,
            'label': code,
            'name': entry_point.name,
            'class': cls,
            'group': entry_point.group,
            'module': entry_point.module
        }

        # Group, module, name
        # Add to the set
        equipment.append(module)

    # equipment_codes = [code for code, _, _ in available_equipment]
    return equipment # equipment_codes
