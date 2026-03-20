import importlib
import inspect
import os
import traceback

# ============================================================================
# ComfyUI LoRA Pipeline
# Automatic node loader (Python-only, no frontend/JS)
#
# - Nodes are loaded ONLY from the "nodes/" directory
# - Helper modules should live in the plugin root (this directory)
# - Nothing in the root is auto-imported as a node
# ============================================================================

# Color codes for terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

BASE_DIR = os.path.dirname(__file__)
NODES_DIR = os.path.join(BASE_DIR, "nodes")


def log(msg):
    print(f"[comfyui-lora-pipeline] {msg}")


def log_warning(msg):
    """Print warning message in yellow"""
    print(f"{YELLOW}[comfyui-lora-pipeline] WARNING: {msg}{RESET}")


def log_error(msg):
    """Print error message in red"""
    print(f"{RED}[comfyui-lora-pipeline] ERROR: {msg}{RESET}")


def log_success(msg):
    """Print success message in green"""
    print(f"{GREEN}[comfyui-lora-pipeline] {msg}{RESET}")


# If the nodes directory does not exist, fail gracefully
if not os.path.isdir(NODES_DIR):
    log("No 'nodes' directory found. No nodes were loaded.")
else:
    # Deterministic loading order (important across OSs)
    for filename in sorted(os.listdir(NODES_DIR)):
        # Only load valid Python modules
        if not filename.endswith(".py") or filename.startswith("_"):
            continue

        module_name = f".nodes.{filename[:-3]}"

        try:
            # CRITICAL: Use importlib.import_module() with package parameter
            # This maintains the proper package context required for relative imports
            module = importlib.import_module(module_name, package=__name__)
        except Exception as e:
            log_error(f"importing {filename}: {e}")
            traceback.print_exc()
            continue

        # Inspect classes defined in the module
        for _, obj in inspect.getmembers(module, inspect.isclass):
            # Ignore imported classes
            if obj.__module__ != module.__name__:
                continue

            # Must look like a ComfyUI node
            input_types = getattr(obj, "INPUT_TYPES", None)
            if not callable(input_types):
                continue

            try:
                # Node ID (internal)
                node_id = getattr(obj, "NODE_ID", obj.__name__)

                # Node name (UI)
                node_name = getattr(
                    obj,
                    "NODE_NAME",
                    obj.__name__.replace("_", " "),
                )

                # Minimal required attributes
                for attr in ("RETURN_TYPES", "FUNCTION"):
                    if not hasattr(obj, attr):
                        raise ValueError(f"Missing required attribute: {attr}")

                # Prevent accidental overrides
                if node_id in NODE_CLASS_MAPPINGS:
                    raise ValueError(f"Duplicate NODE_ID: {node_id}")

                # Register node
                NODE_CLASS_MAPPINGS[node_id] = obj
                NODE_DISPLAY_NAME_MAPPINGS[node_id] = node_name

            except Exception as e:
                log(f"Invalid node '{obj.__name__}' in {filename}: {e}")
                traceback.print_exc()

    log_success(f"Loaded {len(NODE_CLASS_MAPPINGS)} nodes successfully.")

    # UI label override: keep internal node id/class unchanged for compatibility.
    if "ScheduledLoRALoader" in NODE_DISPLAY_NAME_MAPPINGS:
        NODE_DISPLAY_NAME_MAPPINGS["ScheduledLoRALoader"] = "Load LoRA (Scheduled)"


# Explicit exports for ComfyUI
__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
