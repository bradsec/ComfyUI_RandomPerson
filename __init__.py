"""ComfyUI_RandomPerson: randomised structured person descriptions.

Exports the V3 entrypoint when available, otherwise V1 mappings. WEB_DIRECTORY
ships the sex-aware widget extension.
"""

from . import nodes as _nodes

WEB_DIRECTORY = "./js"

if hasattr(_nodes, "comfy_entrypoint"):
    comfy_entrypoint = _nodes.comfy_entrypoint
    __all__ = ["comfy_entrypoint", "WEB_DIRECTORY"]
else:
    NODE_CLASS_MAPPINGS = _nodes.NODE_CLASS_MAPPINGS
    NODE_DISPLAY_NAME_MAPPINGS = _nodes.NODE_DISPLAY_NAME_MAPPINGS
    __all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
