# django-zooy

Django form widgets for Carbon Design System and Zooy UI framework.

## Installation

```bash
pip install django-zooy
```

```python
# settings.py
INSTALLED_APPS = [
    'django_zooy',
]
```

## Quick Start

```python
from django import forms
from django_zooy import CarbonFormMixin
from django_zooy.carbon import CarbonTextInput, CarbonEmailInput

class ContactForm(CarbonFormMixin, forms.Form):
    name = forms.CharField(widget=CarbonTextInput())
    email = forms.EmailField(widget=CarbonEmailInput())
```

The `CarbonFormMixin` automatically injects field labels, help text, validation states, and required attributes into Carbon widgets.

## Widgets

### Carbon Design System

```python
from django_zooy.carbon import (
    CarbonTextInput,      # <cds-text-input>
    CarbonEmailInput,     # <cds-text-input type="email">
    CarbonPasswordInput,  # <cds-password-input>
    CarbonURLInput,       # <cds-text-input type="url">
    CarbonTelInput,       # <cds-text-input type="tel">
    CarbonNumberInput,    # <cds-text-input type="number">
    CarbonSearchInput,    # <cds-text-input type="search">
    CarbonTextarea,       # <cds-textarea>
)
```

### Widget Configuration

Python `snake_case` attributes are automatically converted to Carbon's `kebab-case`:

```python
CarbonTextInput(attrs={
    'label': 'Username',
    'helper_text': 'Enter your username',
    'placeholder': 'johndoe',
    'invalid': False,
    'invalid_text': 'Username is required',
    'size': 'md',  # sm, md, lg
    'enable_counter': True,
    'max_count': 50,
})
```

Boolean attributes render without values:
- `required=True` → `required`
- `disabled=True` → `disabled`
- `invalid=True` → `invalid`

## Form Mixins

### CarbonFormMixin

Automatically configures Carbon widgets with form field metadata:

```python
class MyForm(CarbonFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': CarbonTextInput(),
            'email': CarbonEmailInput(),
        }
```

**Auto-injected attributes:**
- `label` from `field.label`
- `required` from `field.required`
- `helper-text` from `field.help_text`
- `disabled` from `field.disabled`
- `invalid` and `invalid-text` from validation errors

Works with `Form`, `ModelForm`, and custom form classes. Only affects Carbon widgets.

### ZooyFormMixin

Base mixin for Zooy UI integration. Use `CarbonFormMixin` for Carbon widgets.

## Carbon Icons

Server-side SVG rendering of Carbon Design System icons. No JavaScript required.

### Setup

```python
# settings.py
CARBON_ICONS_PATH = BASE_DIR / 'carbon-icons'
```

```bash
python manage.py fetch_carbon_icons
```

Downloads 2,000+ icons from Carbon's CDN to `CARBON_ICONS_PATH`.

### Usage

```django
{% load carbon %}
{% carbon_icon "save" %}
{% carbon_icon "edit" 20 %}
{% carbon_icon "delete" 16 slot="icon" class="text-red-500" %}
```

**Arguments:**
- `name` (required) - Icon name from [Carbon icons library](https://carbondesignsystem.com/guidelines/icons/library/)
- `size` (optional) - 16, 20, 24, or 32. Default: 16
- `**attrs` (optional) - HTML attributes (slot, class, data-*, etc.)

Missing icons render nothing and log: `CARBON ICON MISSING: "icon-name" size=16 at /path/to/icon.svg`

### Management Command Options

```bash
# Download specific sizes only
python manage.py fetch_carbon_icons --sizes 16 20

# Use custom CDN
python manage.py fetch_carbon_icons --cdn https://cdn.example.com/@carbon/icons

# Pin to specific version
python manage.py fetch_carbon_icons --icon-version 11.0.0

# Force re-download
python manage.py fetch_carbon_icons --force
```

Add to deployment pipeline:

```dockerfile
RUN python manage.py fetch_carbon_icons
```

## API Reference

### CarbonWidgetMixin

Base class for all Carbon widgets. Provides:
- Automatic snake_case → kebab-case attribute conversion
- Boolean attribute handling
- Default size (`md`)
- Size constants: `SIZE_SMALL`, `SIZE_MEDIUM`, `SIZE_LARGE`

### CarbonTextInput

**Tooltip constants:**
- Alignment: `TOOLTIP_ALIGN_START`, `TOOLTIP_ALIGN_CENTER`, `TOOLTIP_ALIGN_END`
- Direction: `TOOLTIP_DIR_TOP`, `TOOLTIP_DIR_RIGHT`, `TOOLTIP_DIR_BOTTOM`, `TOOLTIP_DIR_LEFT`

**Supported attributes:**
- Standard: `label`, `placeholder`, `required`, `disabled`, `readonly`
- Validation: `invalid`, `invalid_text`, `warn`, `warn_text`
- Display: `size`, `hide_label`, `inline`
- Counter: `enable_counter`, `max_count`
- Tooltip: `tooltip_alignment`, `tooltip_direction`

### CarbonPasswordInput

Same as `CarbonTextInput` with `show_password_visibility_toggle=True` by default.

**Additional attributes:**
- `hide_password_label` - Tooltip text for hide password
- `show_password_label` - Tooltip text for show password

### CarbonTextarea

Same attributes as `CarbonTextInput` plus:
- `rows` - Number of visible text lines
- `cols` - Visible width of the text control

## Development

```bash
git clone https://github.com/trinity-telecomms/django-zooy
cd django-zooy
uv sync --all-extras --all-groups
pytest
ruff check .
```

### Build and Publish

```bash
# Update version in pyproject.toml
uv sync --upgrade --all-extras --all-groups
pytest
rm -rf dist/ build/ *.egg-info/
uv build
uv publish
```

## License

MIT License. See [LICENCE](LICENCE) for details.

## Links

- [GitHub](https://github.com/trinity-telecomms/django-zooy)
- [Issues](https://github.com/trinity-telecomms/django-zooy/issues)
- [Zooy UI Framework](https://github.com/trinity-telecomms/zooy)
- [Carbon Design System](https://web-components.carbondesignsystem.com/)