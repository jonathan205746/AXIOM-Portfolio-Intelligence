"""
Axiom UI Package v2.1
Institutional-grade design system for Streamlit.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .theme import (
        inject_theme, apply_plotly_theme, theme_toggle,
        get_active_theme, t, THEMES, generate_css,
        TOKENS, get_css_variables, get_color,
    )
    from .components import (
        sidebar_brand, sidebar_user, sidebar_nav_item,
        command_bar, ticker_tape, metric_grid, metric_card,
        section_header, info_card, badge, status_pill,
        glass_panel, render_glass_panel, data_table_header,
        data_table_row, live_dot, chart_container,
        page_sidebar, glass_container, loading_skeleton,
        toast_notification, modal_overlay,
        command_palette, command_palette_modal, sidebar_theme_toggle,
    )

__all__ = [
    # Theme
    "inject_theme", "apply_plotly_theme", "theme_toggle",
    "get_active_theme", "t", "THEMES", "generate_css",
    # Components
    "sidebar_brand", "sidebar_user", "sidebar_nav_item",
    "command_bar", "ticker_tape", "metric_grid", "metric_card",
    "section_header", "info_card", "badge", "status_pill",
    "glass_panel", "render_glass_panel", "data_table_header",
    "data_table_row", "live_dot", "chart_container",
    "page_sidebar", "glass_container", "loading_skeleton",
    "toast_notification", "modal_overlay",
    "command_palette", "command_palette_modal", "sidebar_theme_toggle",
    # Tokens
    "TOKENS", "get_css_variables", "get_color"
]

# ── Lazy loader (prevents circular-import deadlocks in Streamlit MPA) ──
_theme_names = {
    'inject_theme', 'apply_plotly_theme', 'theme_toggle',
    'get_active_theme', 't', 'THEMES', 'generate_css',
    'TOKENS', 'get_css_variables', 'get_color'
}
_component_names = {
    'sidebar_brand', 'sidebar_user', 'sidebar_nav_item',
    'command_bar', 'ticker_tape', 'metric_grid', 'metric_card',
    'section_header', 'info_card', 'badge', 'status_pill',
    'glass_panel', 'render_glass_panel', 'data_table_header',
    'data_table_row', 'live_dot', 'chart_container',
    'page_sidebar', 'glass_container', 'loading_skeleton',
    'toast_notification', 'modal_overlay',
    'command_palette', 'command_palette_modal', 'sidebar_theme_toggle'
}

def __getattr__(name: str):
    if name in _theme_names:
        from . import theme
        return getattr(theme, name)
    if name in _component_names:
        from . import components
        return getattr(components, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")