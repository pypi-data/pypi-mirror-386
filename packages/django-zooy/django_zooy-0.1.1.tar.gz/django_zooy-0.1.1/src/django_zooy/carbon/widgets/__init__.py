"""
Carbon Design System widgets for Django forms.

These widgets integrate Carbon Design Web Components with Django forms,
providing a seamless integration with the Zooy UI framework.

Documentation:
https://web-components.carbondesignsystem.com/
"""

from .text_input import (
    CarbonTextInput,
    CarbonEmailInput,
    CarbonPasswordInput,
    CarbonURLInput,
    CarbonTelInput,
    CarbonNumberInput,
    CarbonSearchInput,
)
from .textarea_input import CarbonTextarea

__all__ = [
    'CarbonTextInput',
    'CarbonEmailInput',
    'CarbonPasswordInput',
    'CarbonURLInput',
    'CarbonTelInput',
    'CarbonNumberInput',
    'CarbonSearchInput',
    'CarbonTextarea',
]
