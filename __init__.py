"""ComfyUI_RandomPerson: randomised structured person descriptions.

Exports V1 NODE_CLASS_MAPPINGS (authoritative on the 0.25.0 if/elif loader) and
comfy_entrypoint for builds whose loader prefers the V3 schema API. WEB_DIRECTORY
ships the sex-aware widget extension.
"""

from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

WEB_DIRECTORY = "./js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]

try:
    from .nodes import comfy_entrypoint  # noqa: F401
    __all__.append("comfy_entrypoint")
except ImportError:
    pass
