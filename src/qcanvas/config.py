"""Runtime configuration and design defaults for QCanvas."""

from __future__ import annotations

from qcanvas.utility.attr_dict import AttrDict

# The exporter used when none is explicitly requested (e.g. ``qcanvas.view``).
DEFAULT_EXPORTER = "mpl"

# Design-wide default variables (referenced by component options).
DESIGN_DEFAULTS = AttrDict(
    units="um",
    variables=AttrDict(
        cpw_width="10um",
        cpw_gap="6um",
    ),
)

# Default chip metadata: a single planar die centred at the origin.
CHIP_DEFAULTS = AttrDict(
    main=AttrDict(
        material="Si",
        size=AttrDict(center_x=0.0, center_y=0.0, size_x=9000.0, size_y=6000.0),
        z=AttrDict(thickness="300um"),
    )
)

# -----------------------------------------------------------------------------
# Preset Scientific Theme Definitions (4 Core + 5 Article Instances)
# -----------------------------------------------------------------------------
PRESET_THEMES = AttrDict(
    # --- 4 Core Academic Themes ---
    cyber=AttrDict(
        key="cyber",
        name="Cyber Quantum (Default)",
        description="Nature Electronics & IBM Cyan/Ruby cyber quantum style",
        canvas_bg="#12151C",
        grid_color="#1E2330",
        axis_color="#262C3C",
        text_color="#F1F5F9",
        crosshair_color="#00D2D3",
        scale_color="#00D2D3",
        is_dark=True,
        styles=AttrDict(
            default=AttrDict(facecolor="#00ADB5", edgecolor="#00D2D3"),
            metal=AttrDict(facecolor="#00ADB5", edgecolor="#00D2D3"),
            junction=AttrDict(facecolor="#FF4757", edgecolor="#FF6B81"),
            cutout=AttrDict(facecolor="#12151C", edgecolor="#505D78"),
            ground=AttrDict(facecolor="#2A354D", edgecolor="#3F4E70"),
            chip_outline=AttrDict(facecolor="none", edgecolor="#3D4B66"),
        ),
    ),
    nordic=AttrDict(
        key="nordic",
        name="Nordic Amber (Science Gold)",
        description="Science & PRL Nordic slate and sunset amber gold style",
        canvas_bg="#0D1117",
        grid_color="#21262D",
        axis_color="#30363D",
        text_color="#F0F6FC",
        crosshair_color="#F4A261",
        scale_color="#F4A261",
        is_dark=True,
        styles=AttrDict(
            default=AttrDict(facecolor="#F4A261", edgecolor="#E76F51"),
            metal=AttrDict(facecolor="#F4A261", edgecolor="#E76F51"),
            junction=AttrDict(facecolor="#E63946", edgecolor="#D90429"),
            cutout=AttrDict(facecolor="#0D1117", edgecolor="#4F6367"),
            ground=AttrDict(facecolor="#264653", edgecolor="#3D6473"),
            chip_outline=AttrDict(facecolor="none", edgecolor="#4F6367"),
        ),
    ),
    aurora=AttrDict(
        key="aurora",
        name="Sycamore Aurora (Google Purple)",
        description="Google Quantum AI Sycamore violet and neon aurora style",
        canvas_bg="#131320",
        grid_color="#232338",
        axis_color="#3A3B5C",
        text_color="#EDE7F6",
        crosshair_color="#FF6F91",
        scale_color="#845EC2",
        is_dark=True,
        styles=AttrDict(
            default=AttrDict(facecolor="#845EC2", edgecolor="#B39CD0"),
            metal=AttrDict(facecolor="#845EC2", edgecolor="#B39CD0"),
            junction=AttrDict(facecolor="#FF6F91", edgecolor="#FF9671"),
            cutout=AttrDict(facecolor="#131320", edgecolor="#595B83"),
            ground=AttrDict(facecolor="#2C2D4A", edgecolor="#484A77"),
            chip_outline=AttrDict(facecolor="none", edgecolor="#484A77"),
        ),
    ),
    paper=AttrDict(
        key="paper",
        name="Nature Clean Light (Publication)",
        description="Classic PRX / Nature clean white paper publication style",
        canvas_bg="#FFFFFF",
        grid_color="#E2E8F0",
        axis_color="#CBD5E1",
        text_color="#1E293B",
        crosshair_color="#1F77B4",
        scale_color="#1F77B4",
        is_dark=False,
        styles=AttrDict(
            default=AttrDict(facecolor="#1F77B4", edgecolor="#0F4C81"),
            metal=AttrDict(facecolor="#1F77B4", edgecolor="#0F4C81"),
            junction=AttrDict(facecolor="#D62728", edgecolor="#8B0000"),
            cutout=AttrDict(facecolor="#FFFFFF", edgecolor="#94A3B8"),
            ground=AttrDict(facecolor="#E2E8F0", edgecolor="#64748B"),
            chip_outline=AttrDict(facecolor="none", edgecolor="#475569"),
        ),
    ),

    # --- 5 Extended Palette Instances ---
    no002=AttrDict(
        key="no002",
        name="Prussian & Coral (普鲁士蓝与珊瑚橙)",
        description="Classic high-contrast Prussian Blue and vibrant Coral Orange",
        canvas_bg="#0B0F19",
        grid_color="#1A2234",
        axis_color="#243048",
        text_color="#F1F5F9",
        crosshair_color="#60A5FA",
        scale_color="#60A5FA",
        is_dark=True,
        styles=AttrDict(
            default=AttrDict(facecolor="#3B82F6", edgecolor="#60A5FA"),
            metal=AttrDict(facecolor="#3B82F6", edgecolor="#60A5FA"),
            junction=AttrDict(facecolor="#F97316", edgecolor="#FB923C"),
            cutout=AttrDict(facecolor="#0B0F19", edgecolor="#334155"),
            ground=AttrDict(facecolor="#1E293B", edgecolor="#334155"),
            chip_outline=AttrDict(facecolor="none", edgecolor="#334155"),
        ),
    ),
    no005=AttrDict(
        key="no005",
        name="Morandi Sage & Rose (莫兰迪灰绿与烟粉)",
        description="Elegant low-saturation Morandi sage green and dusty rose",
        canvas_bg="#151E24",
        grid_color="#212F38",
        axis_color="#2F424E",
        text_color="#ECEFF1",
        crosshair_color="#8EBAA3",
        scale_color="#8EBAA3",
        is_dark=True,
        styles=AttrDict(
            default=AttrDict(facecolor="#76A08A", edgecolor="#8EBAA3"),
            metal=AttrDict(facecolor="#76A08A", edgecolor="#8EBAA3"),
            junction=AttrDict(facecolor="#D97A8F", edgecolor="#E89FB0"),
            cutout=AttrDict(facecolor="#151E24", edgecolor="#354F52"),
            ground=AttrDict(facecolor="#2F3E46", edgecolor="#354F52"),
            chip_outline=AttrDict(facecolor="none", edgecolor="#354F52"),
        ),
    ),
    no008=AttrDict(
        key="no008",
        name="Titanium & Gold (深钛黑与电光赭金)",
        description="High-contrast heavy-metal titanium grey and electric ochre gold",
        canvas_bg="#101118",
        grid_color="#1E202C",
        axis_color="#2D3042",
        text_color="#F8F9FA",
        crosshair_color="#E5A93B",
        scale_color="#E5A93B",
        is_dark=True,
        styles=AttrDict(
            default=AttrDict(facecolor="#E5A93B", edgecolor="#F5BE59"),
            metal=AttrDict(facecolor="#E5A93B", edgecolor="#F5BE59"),
            junction=AttrDict(facecolor="#E63946", edgecolor="#FF4D5A"),
            cutout=AttrDict(facecolor="#101118", edgecolor="#3E415E"),
            ground=AttrDict(facecolor="#2B2D42", edgecolor="#3E415E"),
            chip_outline=AttrDict(facecolor="none", edgecolor="#3E415E"),
        ),
    ),
    no009=AttrDict(
        key="no009",
        name="Teal Lake & Crimson (碧湖清青与落日绯红)",
        description="Luminous cyan lake teal and vivid sunset crimson",
        canvas_bg="#081C1B",
        grid_color="#103331",
        axis_color="#1B4D4A",
        text_color="#E6FFFA",
        crosshair_color="#22D3EE",
        scale_color="#22D3EE",
        is_dark=True,
        styles=AttrDict(
            default=AttrDict(facecolor="#06B6D4", edgecolor="#22D3EE"),
            metal=AttrDict(facecolor="#06B6D4", edgecolor="#22D3EE"),
            junction=AttrDict(facecolor="#F43F5E", edgecolor="#FB7185"),
            cutout=AttrDict(facecolor="#081C1B", edgecolor="#115E59"),
            ground=AttrDict(facecolor="#134E4A", edgecolor="#115E59"),
            chip_outline=AttrDict(facecolor="none", edgecolor="#115E59"),
        ),
    ),
    no013=AttrDict(
        key="no013",
        name="Indigo & Vermilion (琉璃绀青与洗朱红)",
        description="Traditional oriental deep indigo blue and vermilion red",
        canvas_bg="#0A131F",
        grid_color="#152438",
        axis_color="#203652",
        text_color="#F0F4F8",
        crosshair_color="#457B9D",
        scale_color="#457B9D",
        is_dark=True,
        styles=AttrDict(
            default=AttrDict(facecolor="#2A6F97", edgecolor="#457B9D"),
            metal=AttrDict(facecolor="#2A6F97", edgecolor="#457B9D"),
            junction=AttrDict(facecolor="#C84B31", edgecolor="#D96B54"),
            cutout=AttrDict(facecolor="#0A131F", edgecolor="#457B9D"),
            ground=AttrDict(facecolor="#1D3557", edgecolor="#457B9D"),
            chip_outline=AttrDict(facecolor="none", edgecolor="#457B9D"),
        ),
    ),
)

# Aliases for convenience
PRESET_THEMES.dark = PRESET_THEMES.cyber
PRESET_THEMES.light = PRESET_THEMES.paper

# Legacy backward compatibility mappings
DISPLAY_STYLES = PRESET_THEMES.paper.styles
DARK_DISPLAY_STYLES = PRESET_THEMES.cyber.styles


def get_theme(theme_name: str | None = None) -> AttrDict:
    """Retrieve theme dictionary by name (falls back to 'cyber')."""
    if not theme_name:
        return PRESET_THEMES.cyber
    key = theme_name.lower().strip()
    return PRESET_THEMES.get(key, PRESET_THEMES.cyber)
