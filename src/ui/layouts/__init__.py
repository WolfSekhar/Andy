# src/ui/layouts package
from .base_layout import BaseLayout
from .workstation_layout import WorkstationLayout
from .modular_hub_layout import ModularHubLayout

from .classic_layout import ClassicLayout
from .compact_inspector_layout import CompactInspectorLayout
from .action_assistant_layout import ActionAssistantLayout

from .studio_deck_layout import StudioDeckLayout
from .layout_manager import (
    LayoutManager,
    LAYOUT_CLASSIC,
    LAYOUT_WORKSTATION,
    LAYOUT_STUDIO,
    LAYOUT_INSPECTOR,
    LAYOUT_MODULAR_HUB,
    LAYOUT_ACTION_ASSISTANT,
    LAYOUT_ORDER,
    LAYOUT_METADATA,
)

__all__ = [
    "BaseLayout",
    "WorkstationLayout",
    "StudioDeckLayout",
    "ModularHubLayout",
    "ClassicLayout",
    "CompactInspectorLayout",
    "ActionAssistantLayout",
    "LayoutManager",
    "LAYOUT_CLASSIC",
    "LAYOUT_WORKSTATION",
    "LAYOUT_STUDIO",
    "LAYOUT_INSPECTOR",
    "LAYOUT_MODULAR_HUB",
    "LAYOUT_ACTION_ASSISTANT",
    "LAYOUT_ORDER",
    "LAYOUT_METADATA",
]
