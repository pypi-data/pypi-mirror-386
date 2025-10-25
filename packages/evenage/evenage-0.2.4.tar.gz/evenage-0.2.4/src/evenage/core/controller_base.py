"""
Compatibility shim: base Controller class re-export.

Tier 0 uses evenage.core.controller.Controller as the concrete base.
Tier 1 may import from evenage.core.controller_base.ControllerBase.
"""
from .controller import Controller as ControllerBase
