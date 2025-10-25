from django.forms import widgets

from .base import CarbonWidgetMixin


class CarbonTextarea(CarbonWidgetMixin, widgets.Textarea):
    """
    Carbon Design System textarea widget for Django forms.

    Supports all cds-textarea attributes, including validation,
    state management, and visual customisation.
    """

    template_name = "django_zooy/carbon/widgets/textarea.html"
