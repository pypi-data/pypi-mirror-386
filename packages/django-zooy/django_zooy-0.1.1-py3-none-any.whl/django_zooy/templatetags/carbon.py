# ============================================================================
# Carbon Design System Icons
# ============================================================================
from django import template
from django.utils.safestring import mark_safe

from ..carbon.icons import render_carbon_icon_svg, Icon

register = template.Library()


@register.simple_tag
def carbon_icon(name, size=16, **kwargs):
    """
    Render a Carbon Design System icon as inline SVG.

    This reads the SVG file from @carbon/icons and renders it directly
    in your template. No JavaScript, no CDN, no placeholders.

    Usage in template:
        {% load carbon %}
        {% carbon_icon "edit" size=16 slot="icon" %}
        {% carbon_icon "add" 20 class="my-icon" %}
        {% carbon_icon "save" %}  {# defaults to size 16 #}

    Args:
        name: Icon name (e.g., 'edit', 'add', 'close')
        size: Icon size (16, 20, 24, or 32)
        **kwargs: Additional HTML attributes (slot, class, data-*, etc.)

    Browse icons: https://carbondesignsystem.com/guidelines/icons/library/
    """
    svg_markup = render_carbon_icon_svg(name, size, **kwargs)
    return mark_safe(svg_markup)


@register.simple_tag
def carbon_icon_const(icon_const, size=16, **kwargs):
    """
    Render a Carbon icon using a constant from Icon class.

    Usage:
        {% load carbon %}
        {% carbon_icon_const "ADD" size=16 slot="icon" %}
        {% carbon_icon_const "EDIT" 16 class="my-icon" %}
    """
    icon_name = getattr(Icon, icon_const.upper(), icon_const)
    svg_markup = render_carbon_icon_svg(icon_name, size, **kwargs)
    return mark_safe(svg_markup)
