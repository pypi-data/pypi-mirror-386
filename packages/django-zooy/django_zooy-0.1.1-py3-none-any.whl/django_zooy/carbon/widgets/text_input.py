from django.forms import widgets
from django.utils.text import slugify
from django.utils.html import escape


class CarbonTextInput(widgets.TextInput):
    """
    Carbon Design System text input widget for Django forms.

    Supports all cds-text-input attributes, including validation,
    state management, and visual customisation.
    """

    template_name = "django_zooy/carbon/widgets/text_input.html"

    # Supported Carbon text input sizes
    SIZE_SMALL = 'sm'
    SIZE_MEDIUM = 'md'
    SIZE_LARGE = 'lg'

    # Supported tooltip alignments
    TOOLTIP_ALIGN_START = 'start'
    TOOLTIP_ALIGN_CENTER = 'center'
    TOOLTIP_ALIGN_END = 'end'

    # Supported tooltip directions
    TOOLTIP_DIR_TOP = 'top'
    TOOLTIP_DIR_RIGHT = 'right'
    TOOLTIP_DIR_BOTTOM = 'bottom'
    TOOLTIP_DIR_LEFT = 'left'

    def __init__(self, attrs=None):
        """
        Initialize the widget with optional Carbon-specific attributes.

        Carbon-specific attrs:
        - label: Field label text
        - helper_text: Helper text below the field
        - invalid: Boolean for invalid state
        - invalid_text: Invalid message text
        - warn: Boolean for warning state
        - warn_text: Warning message text
        - size: Input size (sm, md, lg)
        - hide_label: Boolean to visually hide label
        - inline: Boolean for inline version
        - show_password_visibility_toggle: Boolean for password toggle
        - hide_password_label: Tooltip text for hide password
        - show_password_label: Tooltip text for show password
        - enable_counter: Boolean to enable character counter
        - max_count: Maximum character count
        - required_validity_message: Custom required field message
        - tooltip_alignment: Tooltip alignment (start, center, end)
        - tooltip_direction: Tooltip direction (top, right, bottom, left)
        """
        super().__init__(attrs)

    def get_context(self, name, value, attrs):
        """
        Build the context for rendering the Carbon text input.

        Processes all Django and Carbon-specific attributes and creates
        an attribute string ready for HTML rendering.
        """
        context = super().get_context(name, value, attrs)

        # Preserve input type
        context['widget']['input_type'] = self.input_type

        # Build all attributes into a single string
        widget_attrs = context['widget']['attrs']
        attr_string = self._build_attr_string(widget_attrs, name, value)

        context['widget']['attr_string'] = attr_string

        return context

    def _build_attr_string(self, attrs, name, value):
        """
        Build HTML attribute string from attrs dict.

        Handles:
        - Boolean attributes (rendered without values)
        - Standard key-value attributes
        - Special Carbon attributes
        - Automatic kebab-case conversion
        """
        parts = []

        # Always include name attribute
        parts.append(f'name="{escape(name)}"')

        # Include value if present
        if value is not None and value != '':
            parts.append(f'value="{escape(value)}"')

        # Process all other attributes
        for key, val in attrs.items():
            # Skip 'name' and 'value' as we've already handled them
            if key in ('name', 'value'):
                continue

            # Convert Python naming to Carbon's kebab-case
            carbon_key = self._to_carbon_attribute(key)

            # Handle boolean attributes
            if val is True or val == '':
                parts.append(carbon_key)
            elif val is False or val is None:
                # Skip false/none boolean attributes
                continue
            else:
                # Regular key-value attribute
                parts.append(f'{carbon_key}="{escape(str(val))}"')

        return ' '.join(parts)

    def _to_carbon_attribute(self, attr_name):
        """
        Convert Python attribute names to Carbon's kebab-case format.

        Examples:
        - helper_text -> helper-text
        - invalid_text -> invalid-text
        - show_password_visibility_toggle -> show-password-visibility-toggle
        """
        # Handle special cases that shouldn't be slugified
        special_cases = {
            'type': 'type',
            'placeholder': 'placeholder',
            'id': 'id',
            'class': 'class',
        }

        if attr_name in special_cases:
            return special_cases[attr_name]

        # Convert underscores to hyphens and slugify
        return slugify(attr_name).replace('_', '-').lower()

    def build_attrs(self, base_attrs, extra_attrs=None):
        """
        Override to provide sensible defaults for Carbon attributes.
        """
        attrs = super().build_attrs(base_attrs, extra_attrs)

        # Set default size if not specified
        if 'size' not in attrs:
            attrs['size'] = self.SIZE_MEDIUM

        return attrs


class CarbonEmailInput(CarbonTextInput):
    """Carbon email input widget."""
    input_type = 'email'


class CarbonPasswordInput(CarbonTextInput):
    """
    Carbon password input widget.

    Automatically enables the password visibility toggle by default.
    """
    input_type = 'password'
    template_name = "django_zooy/carbon/widgets/password_input.html"

    def __init__(self, attrs=None, render_value=False):
        if attrs is None:
            attrs = {}

        # Enable password visibility toggle by default
        if 'show_password_visibility_toggle' not in attrs:
            attrs['show_password_visibility_toggle'] = True

        super().__init__(attrs)
        self.render_value = render_value

    def get_context(self, name, value, attrs):
        if not self.render_value:
            value = None
        return super().get_context(name, value, attrs)


class CarbonURLInput(CarbonTextInput):
    """Carbon URL input widget."""
    input_type = 'url'


class CarbonTelInput(CarbonTextInput):
    """Carbon telephone input widget."""
    input_type = 'tel'


class CarbonNumberInput(CarbonTextInput):
    """Carbon number input widget."""
    input_type = 'number'


class CarbonSearchInput(CarbonTextInput):
    """Carbon search input widget."""
    input_type = 'search'
