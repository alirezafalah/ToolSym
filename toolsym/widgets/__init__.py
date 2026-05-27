"""Shared PySide6 widgets used by both apps.

Keeping them here means the two apps stay visually consistent and the
``QSettings`` / data-root logic isn't duplicated. Modules here are the
*only* parts of ``toolsym/`` allowed to import Qt.
"""

from toolsym.widgets.clickable_preview import ClickablePreview
from toolsym.widgets.data_root_picker import DataRootPicker
from toolsym.widgets.image_popup import ImagePopup
from toolsym.widgets.progress import ProgressDialog
from toolsym.widgets.theme import apply_dark_theme, load_theme_qss

__all__ = [
    "ClickablePreview",
    "DataRootPicker",
    "ImagePopup",
    "ProgressDialog",
    "apply_dark_theme",
    "load_theme_qss",
]
