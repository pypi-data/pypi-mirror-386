import tkinter as tk
import pygubu.plugins.pygubu.combobox_bo as cbb
import pygubu.plugins.pygubu.fontinputbo as fib
import pygubu.plugins.pygubu.colorinput_bo as cib
import pygubu.forms.pygubuwidget as pygubuwidget

from pygubu.api.v1 import (
    BuilderObject,
    register_widget,
    register_custom_property,
    copy_custom_property,
)
from .base import (
    WidgetBOMixin,
    _plugin_forms_uid,
    _tab_form_widgets_label,
)


_plugin_uid = f"{_plugin_forms_uid}.pygubuwidget"
_designer_tabs = ("tk", "ttk", _tab_form_widgets_label)


class PygubuComboboxBO(WidgetBOMixin, cbb.ComboboxBO):
    class_ = pygubuwidget.PygubuCombobox
    properties = cbb.ComboboxBuilder.properties + WidgetBOMixin.base_properties
    ro_properties = (
        cbb.ComboboxBuilder.ro_properties + WidgetBOMixin.base_properties
    )


_builder_uid = f"{_plugin_uid}.PygubuCombobox"
register_widget(
    _builder_uid,
    PygubuComboboxBO,
    "PygubuCombobox",
    _designer_tabs,
)


class FontInputFWBO(WidgetBOMixin, fib.FontInputBO):
    class_ = pygubuwidget.FontInputFW
    properties = fib.FontInputBO.properties + WidgetBOMixin.base_properties
    ro_properties = (
        fib.FontInputBO.ro_properties + WidgetBOMixin.base_properties
    )


_wname = "FontInput"
_builder_uid = f"{_plugin_uid}.{_wname}"
register_widget(
    _builder_uid,
    FontInputFWBO,
    _wname,
    _designer_tabs,
)


class ColorInputFWBO(WidgetBOMixin, cib.ColorInputBO):
    class_ = pygubuwidget.ColorInputFW
    properties = cib.ColorInputBO.properties + WidgetBOMixin.base_properties
    ro_properties = (
        cib.ColorInputBO.ro_properties + WidgetBOMixin.base_properties
    )


_wname = "ColorInput"
_builder_uid = f"{_plugin_uid}.{_wname}"
register_widget(
    _builder_uid,
    ColorInputFWBO,
    _wname,
    _designer_tabs,
)
