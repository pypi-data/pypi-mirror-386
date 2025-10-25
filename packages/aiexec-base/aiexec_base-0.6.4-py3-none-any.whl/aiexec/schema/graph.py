# Backwards compatibility module for aiexec.schema.graph
# This module redirects imports to the new wfx.schema.graph module

from wfx.schema.graph import InputValue, Tweaks

__all__ = ["InputValue", "Tweaks"]
