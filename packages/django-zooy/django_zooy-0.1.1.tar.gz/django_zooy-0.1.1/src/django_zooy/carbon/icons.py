"""
Carbon Design System Icons - Server-Side SVG Rendering

Reads SVG files from @carbon/icons package and renders them directly in templates.
No JavaScript, no CDN, no placeholders - just pure SVG markup.

Usage in template:
    {% carbon_icon "edit" 16 slot="icon" %}
"""
import os
from pathlib import Path
from django.conf import settings


def get_carbon_icons_path() -> Path:
    """
    Get the path to Carbon icons SVG directory.

    Checks Django settings for CARBON_ICONS_PATH, otherwise attempts to
    auto-detect common locations.

    Returns:
        Path to Carbon icons SVG directory

    Raises:
        FileNotFoundError: If Carbon icons path cannot be found
    """
    # Check Django settings first
    if hasattr(settings, 'CARBON_ICONS_PATH'):
        path = Path(settings.CARBON_ICONS_PATH)
        if path.exists():
            return path

    # Auto-detect: Look for zooy/node_modules/@carbon/icons/svg
    # Common locations relative to Django project
    base_dir = Path(settings.BASE_DIR)

    candidates = [
        # Adjacent to project (common structure: workspace/zooy, workspace/z2)
        base_dir.parent / 'zooy' / 'node_modules' / '@carbon' / 'icons' / 'svg',
        # Inside static directory
        base_dir / 'static' / 'js' / 'node_modules' / '@carbon' / 'icons' / 'svg',
        # Inside project
        base_dir / 'node_modules' / '@carbon' / 'icons' / 'svg',
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    # Not found
    raise FileNotFoundError(
        f"Carbon icons not found. Tried: {[str(c) for c in candidates]}. "
        f"Set CARBON_ICONS_PATH in Django settings."
    )


def read_carbon_icon_svg(name: str, size: int = 16) -> str:
    """
    Read Carbon icon SVG file from disk.

    Args:
        name: Icon name (e.g., 'edit', 'add', 'close')
        size: Icon size (16, 20, 24, or 32)

    Returns:
        SVG markup as string

    Raises:
        FileNotFoundError: If icon file doesn't exist
    """
    icons_path = get_carbon_icons_path()
    icon_file = icons_path / str(size) / f'{name}.svg'

    if not icon_file.exists():
        raise FileNotFoundError(
            f"Icon not found: {name}/{size}.svg. "
            f"Check https://carbondesignsystem.com/guidelines/icons/library/"
        )

    return icon_file.read_text()


def render_carbon_icon_svg(name: str, size: int = 16, **attrs) -> str:
    """
    Render Carbon icon as inline SVG with proper Carbon Design System attributes.

    Automatically adds Carbon-required attributes:
    - fill="currentColor" - Inherit color from CSS
    - focusable="false" - Remove from tab order
    - preserveAspectRatio="xMidYMid meet" - Proper scaling
    - aria-hidden="true" - Hide from screen readers (decorative)
    - width and height - Explicit dimensions

    Args:
        name: Icon name (e.g., 'edit', 'add', 'close')
        size: Icon size (16, 20, 24, or 32)
        **attrs: Additional HTML attributes to add to <svg> tag
                 (overrides defaults if provided)

    Returns:
        SVG markup with attributes injected

    Examples:
        >>> render_carbon_icon_svg('add', 16, slot='icon', class_='my-icon')
        '<svg fill="currentColor" width="16" height="16" slot="icon" class="my-icon" ...>...</svg>'
    """
    try:
        svg_markup = read_carbon_icon_svg(name, size)
    except FileNotFoundError as e:
        # Return a visible error indicator in development
        if settings.DEBUG:
            return f'<span style="color:red;" title="{str(e)}">[{name}]</span>'
        # In production, fail silently or log
        return f'<span aria-label="{name}"></span>'

    # Handle class_ -> class
    if 'class_' in attrs:
        attrs['class'] = attrs.pop('class_')

    # Carbon Design System standard attributes
    # These match what @carbon/icons ES modules provide
    carbon_attrs = {
        'fill': 'currentColor',
        'focusable': 'false',
        'preserveAspectRatio': 'xMidYMid meet',
        'aria-hidden': 'true',
        'width': str(size),
        'height': str(size),
    }

    # Merge user attrs (user attrs override defaults)
    carbon_attrs.update(attrs)

    # Build attribute string
    attr_parts = [f'{k}="{v}"' for k, v in carbon_attrs.items()]
    attr_string = ' ' + ' '.join(attr_parts)

    # Inject after <svg (replacing existing attributes)
    # SVG files come with xmlns and viewBox, we'll replace the opening tag entirely
    svg_markup = svg_markup.replace('<svg xmlns="http://www.w3.org/2000/svg" viewBox="',
                                     f'<svg xmlns="http://www.w3.org/2000/svg"{attr_string} viewBox="',
                                     1)

    return svg_markup


# Common icon names
class Icon:
    """Common Carbon icon names"""
    # Actions
    ADD = 'add'
    EDIT = 'edit'
    DELETE = 'trash-can'
    SAVE = 'save'
    CLOSE = 'close'
    SEARCH = 'search'
    FILTER = 'filter'
    SETTINGS = 'settings'

    # Navigation
    CHEVRON_LEFT = 'chevron--left'
    CHEVRON_RIGHT = 'chevron--right'
    CHEVRON_UP = 'chevron--up'
    CHEVRON_DOWN = 'chevron--down'
    ARROW_LEFT = 'arrow--left'
    ARROW_RIGHT = 'arrow--right'
    MENU = 'menu'

    # Status
    CHECKMARK = 'checkmark'
    ERROR = 'error'
    WARNING = 'warning'
    INFO = 'information'

    # Files
    FOLDER = 'folder'
    DOCUMENT = 'document'
    DOWNLOAD = 'download'
    UPLOAD = 'upload'

    # UI
    OVERFLOW_MENU = 'overflow-menu--vertical'
    VIEW = 'view'
    VIEW_OFF = 'view--off'
    COPY = 'copy'
    LINK = 'link'
    USER = 'user'
    NOTIFICATION = 'notification'
    FAVORITE = 'favorite'
