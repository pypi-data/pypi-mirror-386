# encoding: utf-8
import tkinter as tk
import tkinter.ttk as ttk
from collections import OrderedDict

from pygubu.i18n import _
from pygubu.api.v1 import BuilderObject, register_widget
from pygubu.component.builderobject import (
    EntryBaseBO,
    PanedWindowBO,
    PanedWindowPaneBO,
    OptionMenuBaseMixin,
    CB_TYPES,
)


has_tk_version_9 = tk.TkVersion >= 9


#
# ttk widgets
#
class TTKWidgetBO(BuilderObject):
    OPTIONS_LABEL = (
        "compound",
        "font",
        "image",
        "padding",
        "text",
        "textvariable",
        "underline",
        "width",
    )
    OPTIONS_COMPATIBILITY = ("state",)
    OPTIONS_STANDARD = ("class_", "cursor", "takefocus", "style")
    OPTIONS_SPECIFIC = tuple()
    OPTIONS_CUSTOM = tuple()
    ro_properties = ("class_",)


class TTKFrame(TTKWidgetBO):
    OPTIONS_SPECIFIC = ("borderwidth", "relief", "padding", "height", "width")
    class_ = ttk.Frame
    container = True
    container_layout = True
    properties = TTKWidgetBO.OPTIONS_STANDARD + OPTIONS_SPECIFIC


register_widget("ttk.Frame", TTKFrame, "ttk.Frame", (_("Containers"), "ttk"))


class TTKLabel(TTKWidgetBO):
    OPTIONS_STANDARD = (
        TTKWidgetBO.OPTIONS_STANDARD
        + TTKWidgetBO.OPTIONS_LABEL
        + ("borderwidth",)
    )
    OPTIONS_SPECIFIC = (
        "anchor",
        "background",
        "font",
        "foreground",
        "justify",
        "padding",
        "relief",
        "state",
        "wraplength",
    )
    class_ = ttk.Label
    container = False
    properties = OPTIONS_STANDARD + OPTIONS_SPECIFIC


register_widget(
    "ttk.Label", TTKLabel, "ttk.Label", (_("Control & Display"), "ttk")
)


class TTKButton(TTKWidgetBO):
    OPTIONS_STANDARD = (
        TTKWidgetBO.OPTIONS_STANDARD
        + tuple(set(TTKWidgetBO.OPTIONS_LABEL) - set(("font",)))
        + TTKWidgetBO.OPTIONS_COMPATIBILITY
    )
    OPTIONS_SPECIFIC = ("command", "default")
    class_ = ttk.Button
    container = False
    properties = (
        OPTIONS_STANDARD + OPTIONS_SPECIFIC + TTKWidgetBO.OPTIONS_CUSTOM
    )
    command_properties = ("command",)


register_widget(
    "ttk.Button", TTKButton, "ttk.Button", (_("Control & Display"), "ttk")
)


class TTKCheckbutton(TTKWidgetBO):
    OPTIONS_STANDARD = (
        TTKWidgetBO.OPTIONS_STANDARD
        + TTKWidgetBO.OPTIONS_LABEL
        + TTKWidgetBO.OPTIONS_COMPATIBILITY
    )
    OPTIONS_SPECIFIC = ("command", "offvalue", "onvalue", "variable")
    class_ = ttk.Checkbutton
    container = False
    properties = (
        OPTIONS_STANDARD + OPTIONS_SPECIFIC + TTKWidgetBO.OPTIONS_CUSTOM
    )
    command_properties = ("command",)


register_widget(
    "ttk.Checkbutton",
    TTKCheckbutton,
    "ttk.Checkbutton",
    (_("Control & Display"), "ttk"),
)


class TTKRadiobutton(TTKWidgetBO):
    OPTIONS_STANDARD = (
        TTKWidgetBO.OPTIONS_STANDARD
        + TTKWidgetBO.OPTIONS_LABEL
        + TTKWidgetBO.OPTIONS_COMPATIBILITY
    )
    OPTIONS_SPECIFIC = ("command", "value", "variable")
    class_ = ttk.Radiobutton
    container = False
    properties = (
        OPTIONS_STANDARD + OPTIONS_SPECIFIC + TTKWidgetBO.OPTIONS_CUSTOM
    )
    ro_properties = ("class_",)
    command_properties = ("command",)


register_widget(
    "ttk.Radiobutton",
    TTKRadiobutton,
    "ttk.Radiobutton",
    (_("Control & Display"), "ttk"),
)


_v9_entry_opts = (
    ("placeholder", "placeholderforeground") if has_tk_version_9 else tuple()
)


class TTKEntry(TTKWidgetBO, EntryBaseBO):
    OPTIONS_STANDARD = TTKWidgetBO.OPTIONS_STANDARD + ("xscrollcommand",)
    OPTIONS_SPECIFIC = (
        "exportselection",
        "font",
        "invalidcommand",
        "justify",
        "show",
        "state",
        "textvariable",
        "validate",
        "validatecommand",
        "width",
    ) + _v9_entry_opts
    OPTIONS_CUSTOM = ("text",)
    class_ = ttk.Entry
    container = False
    properties = OPTIONS_STANDARD + OPTIONS_SPECIFIC + OPTIONS_CUSTOM
    command_properties = ("validatecommand", "invalidcommand", "xscrollcommand")


register_widget(
    "ttk.Entry", TTKEntry, "ttk.Entry", (_("Control & Display"), "ttk")
)


class TTKCombobox(TTKWidgetBO):
    OPTIONS_SPECIFIC = (
        "exportselection",
        "justify",
        "height",
        "postcommand",
        "state",
        "textvariable",
        "values",
        "width",
        "validate",
        "validatecommand",
        "invalidcommand",
        "xscrollcommand",
    ) + _v9_entry_opts
    class_ = ttk.Combobox
    container = False
    properties = (
        TTKWidgetBO.OPTIONS_STANDARD
        + OPTIONS_SPECIFIC
        + TTKWidgetBO.OPTIONS_CUSTOM
    )
    command_properties = (
        "postcommand",
        "validatecommand",
        "invalidcommand",
        "xscrollcommand",
    )
    virtual_events = ("<<ComboboxSelected>>",)

    def _code_process_property_value(self, targetid, pname, value: str):
        if pname == "values":
            return self.code_escape_str(value)
        return super()._code_process_property_value(targetid, pname, value)


register_widget(
    "ttk.Combobox", TTKCombobox, "ttk.Combobox", (_("Control & Display"), "ttk")
)


class TTKScrollbar(TTKWidgetBO):
    OPTIONS_SPECIFIC = ("command", "orient")
    class_ = ttk.Scrollbar
    container = False
    properties = TTKWidgetBO.OPTIONS_STANDARD + OPTIONS_SPECIFIC
    command_properties = ("command",)


register_widget(
    "ttk.Scrollbar",
    TTKScrollbar,
    "ttk.Scrollbar",
    (_("Control & Display"), "ttk"),
)


class TTKSizegrip(TTKWidgetBO):
    class_ = ttk.Sizegrip
    container = False
    properties = TTKWidgetBO.OPTIONS_STANDARD + TTKWidgetBO.OPTIONS_SPECIFIC


register_widget(
    "ttk.Sizegrip", TTKSizegrip, "ttk.Sizegrip", (_("Control & Display"), "ttk")
)


_v9_pbar_options = (
    ("anchor", "font", "foreground", "justify", "text", "wraplength")
    if has_tk_version_9
    else tuple()
)


class TTKProgressbar(TTKWidgetBO):
    OPTIONS_SPECIFIC = (
        "orient",
        "length",
        "mode",
        "maximum",
        "value",
        "variable",
    ) + _v9_pbar_options
    class_ = ttk.Progressbar
    container = False
    properties = TTKWidgetBO.OPTIONS_STANDARD + OPTIONS_SPECIFIC


register_widget(
    "ttk.Progressbar",
    TTKProgressbar,
    "ttk.Progressbar",
    (_("Control & Display"), "ttk"),
)


class TTKScale(TTKWidgetBO):
    OPTIONS_SPECIFIC = (
        "command",
        "from_",
        "length",
        "orient",
        "state",
        "to",
        "value",
        "variable",
    )
    class_ = ttk.Scale
    container = False
    properties = TTKWidgetBO.OPTIONS_STANDARD + OPTIONS_SPECIFIC
    command_properties = ("command",)


register_widget(
    "ttk.Scale", TTKScale, "ttk.Scale", (_("Control & Display"), "ttk")
)


class TTKSeparator(TTKWidgetBO):
    OPTIONS_SPECIFIC = ("orient",)
    class_ = ttk.Separator
    container = False
    properties = TTKWidgetBO.OPTIONS_STANDARD + OPTIONS_SPECIFIC


register_widget(
    "ttk.Separator",
    TTKSeparator,
    "ttk.Separator",
    (_("Control & Display"), "ttk"),
)


class TTKLabelframe(TTKWidgetBO):
    OPTIONS_STANDARD = TTKFrame.OPTIONS_STANDARD
    OPTIONS_SPECIFIC = TTKFrame.OPTIONS_SPECIFIC + (
        "labelanchor",
        "text",
        "underline",
    )
    class_ = ttk.Labelframe
    container = True
    container_layout = True
    properties = OPTIONS_STANDARD + OPTIONS_SPECIFIC


register_widget(
    "ttk.Labelframe", TTKLabelframe, "ttk.Labelframe", (_("Containers"), "ttk")
)


class TTKPanedwindow(TTKWidgetBO, PanedWindowBO):
    OPTIONS_SPECIFIC = ("orient", "height", "width")
    class_ = ttk.Panedwindow
    allowed_children = ("ttk.Panedwindow.Pane",)
    properties = TTKWidgetBO.OPTIONS_STANDARD + OPTIONS_SPECIFIC
    ro_properties = ("class_", "orient")
    virtual_events = ("<<EnteredChild>>",)


register_widget(
    "ttk.Panedwindow",
    TTKPanedwindow,
    "ttk.Panedwindow",
    (_("Containers"), "ttk"),
)


class TTKNotebook(TTKWidgetBO):
    OPTIONS_SPECIFIC = ("height", "padding", "width")
    class_ = ttk.Notebook
    container = True
    allowed_children = ("ttk.Notebook.Tab",)
    properties = TTKWidgetBO.OPTIONS_STANDARD + OPTIONS_SPECIFIC
    virtual_events = ("<<NotebookTabChanged>>",)


register_widget(
    "ttk.Notebook", TTKNotebook, "ttk.Notebook", (_("Containers"), "ttk")
)


class TTKMenubuttonBO(TTKWidgetBO):
    OPTIONS_STANDARD = (
        TTKWidgetBO.OPTIONS_STANDARD
        + TTKWidgetBO.OPTIONS_LABEL
        + TTKWidgetBO.OPTIONS_COMPATIBILITY
    )
    OPTIONS_SPECIFIC = ("direction",)  # 'menu'
    class_ = ttk.Menubutton
    container = True
    properties = OPTIONS_STANDARD + OPTIONS_SPECIFIC
    allowed_children = ("tk.Menu",)
    maxchildren = 1

    def add_child(self, bobject):
        self.widget.configure(menu=bobject.widget)

    def code_child_add(self, childid):
        lines = [f"{self.code_identifier()}.configure(menu={childid})"]
        return lines


register_widget(
    "ttk.Menubutton",
    TTKMenubuttonBO,
    "ttk.Menubutton",
    (
        _("Menu"),
        _("Control & Display"),
        "ttk",
    ),
)


class TTKTreeviewBO(TTKWidgetBO):
    OPTIONS_STANDARD = TTKWidgetBO.OPTIONS_STANDARD + (
        "xscrollcommand",
        "yscrollcommand",
    )
    OPTIONS_SPECIFIC = ("height", "padding", "selectmode", "show")
    class_ = ttk.Treeview
    container = True
    allowed_children = ("ttk.Treeview.Column",)
    properties = OPTIONS_STANDARD + OPTIONS_SPECIFIC
    command_properties = ("xscrollcommand", "yscrollcommand")
    virtual_events = (
        "<<TreeviewSelect>>",
        "<<TreeviewOpen>>",
        "<<TreeviewClose>>",
    )

    def __init__(self, builder, wdescr):
        super(TTKTreeviewBO, self).__init__(builder, wdescr)
        self._columns = None
        self._headings = None
        self._dcolumns = None

    def configure_children(self):
        self.__configure_columns()

    def __configure_columns(self):
        if self._columns:
            columns = list(self._columns.keys())
            if "#0" in columns:
                columns.remove("#0")
            displaycolumns = self._dcolumns
            self.widget.configure(
                columns=columns, displaycolumns=displaycolumns
            )
            for col in self._columns:
                self.widget.column(col, **self._columns[col])
        if self._headings:
            for col in self._headings:
                self.widget.heading(col, **self._headings[col])

    def set_column(self, col_id, attrs, visible=True):
        if self._columns is None:
            self._columns = OrderedDict()
            self._dcolumns = list()
        self._columns[col_id] = attrs
        if visible and col_id != "#0":
            self._dcolumns.append(col_id)

    def set_heading(self, col_id, attrs):
        if self._headings is None:
            self._headings = OrderedDict()
        self._headings[col_id] = attrs

    #
    # Code generation methods
    #
    def code_configure_children(self, targetid=None):
        if targetid is None:
            targetid = self.code_identifier()
        lines = []
        if self._columns:
            columns = list(self._columns.keys())
            if "#0" in columns:
                columns.remove("#0")
            displaycolumns = self._dcolumns
            line = f"{targetid}_cols = {repr(columns)}"
            lines.append(line)
            line = f"{targetid}_dcols = {repr(displaycolumns)}"
            lines.append(line)
            line = "{0}.configure(columns={0}_cols, displaycolumns={0}_dcols)"
            line = line.format(targetid)
            lines.append(line)
            for col in self._columns:
                code_bag, kwp, _ = self._code_process_properties(
                    self._columns[col], targetid
                )
                bag = []
                for pname in kwp:
                    s = f"{pname}={code_bag[pname]}"
                    bag.append(s)
                kwargs = ",".join(bag)
                line = f'{targetid}.column("{col}", {kwargs})'
                lines.append(line)
        if self._headings:
            for col in self._headings:
                code_bag, kwp, _ = self._code_process_properties(
                    self._headings[col], targetid
                )
                bag = []
                for pname in kwp:
                    s = f"{pname}={code_bag[pname]}"
                    bag.append(s)
                kwargs = ",".join(bag)
                line = f'{targetid}.heading("{col}", {kwargs})'
                lines.append(line)

        return lines


register_widget(
    "ttk.Treeview",
    TTKTreeviewBO,
    "ttk.Treeview",
    (_("Control & Display"), "ttk"),
)


#
# Helpers for Standard ttk widgets
#


class TTKPanedwindowPane(TTKWidgetBO, PanedWindowPaneBO):
    OPTIONS_STANDARD = tuple()
    OPTIONS_SPECIFIC = ("weight",)
    class_ = None
    container = True
    allowed_parents = ("ttk.Panedwindow",)
    maxchildren = 1
    properties = OPTIONS_STANDARD + OPTIONS_SPECIFIC


register_widget(
    "ttk.Panedwindow.Pane",
    TTKPanedwindowPane,
    "ttk.Panedwindow.Pane",
    (_("Pygubu Helpers"), "ttk"),
)


class TTKNotebookTab(TTKWidgetBO):
    OPTIONS_STANDARD = tuple()
    OPTIONS_SPECIFIC = (
        "state",
        "sticky",
        "padding",
        "text",
        "image",
        "compound",
        "underline",
    )
    class_ = None
    container = True
    layout_required = False
    allow_bindings = False
    allowed_parents = ("ttk.Notebook",)
    children_layout_override = True
    maxchildren = 1
    properties = OPTIONS_STANDARD + OPTIONS_SPECIFIC

    def realize(self, parent, extra_init_args: dict = None):
        self.widget = parent.get_child_master()
        return self.widget

    def configure(self, target=None):
        pass

    def layout(self, target=None, *, forget=False):
        pass

    def add_child(self, bobject):
        properties = {
            pname: self._process_property_value(pname, value)
            for (pname, value) in self.wmeta.properties.items()
        }
        self.widget.add(bobject.widget, **properties)

    #
    # Code generation methods
    #
    def code_realize(self, boparent, code_identifier=None):
        self._code_identifier = boparent.code_child_master()
        return tuple()

    def code_configure(self, targetid=None):
        return tuple()

    def code_child_add(self, childid):
        targetid = self.code_identifier()
        code_bag, kw, _ = self._code_process_properties(
            self.wmeta.properties, targetid
        )
        kwbag = []
        for pname in kw:
            arg = f"{pname}={code_bag[pname]}"
            kwbag.append(arg)
        kwargs = ""
        if kwbag:
            kwargs = f", {', '.join(kwbag)}"
        line = f"{targetid}.add({childid}{kwargs})"
        return [line]


register_widget(
    "ttk.Notebook.Tab",
    TTKNotebookTab,
    "Notebook.Tab",
    (_("Pygubu Helpers"), "ttk"),
)


class TTKTreeviewColumnBO(TTKWidgetBO):
    OPTIONS_STANDARD = tuple()
    OPTIONS_SPECIFIC = (
        "text",
        "image",
        "command",
        "heading_anchor",
        "column_anchor",
        "minwidth",
        "stretch",
        "width",
    )
    OPTIONS_CUSTOM = (
        "tree_column",
        "visible",
    )
    class_ = None
    container = False
    layout_required = False
    allow_bindings = False
    allowed_parents = ("ttk.Treeview",)
    properties = OPTIONS_STANDARD + OPTIONS_SPECIFIC + OPTIONS_CUSTOM
    command_properties = ("command",)

    def realize(self, parent, extra_init_args: dict = None):
        self.widget = parent.get_child_master()
        col_props = dict(self.wmeta.properties)  # copy properties
        self._setup_column(parent, col_props)
        return self.widget

    def _get_heading_properties(self, props, code_gen=False):
        text = props.pop("text", None)
        if text is None:
            text = self.wmeta.identifier
        hprops = {"anchor": props.pop("heading_anchor", tk.W), "text": text}
        # Only add image if has value. Fix code generation
        imgvalue = props.pop("image", None)
        if imgvalue and code_gen:
            hprops["image"] = imgvalue
        elif imgvalue:
            hprops["image"] = self._process_property_value("image", imgvalue)
        return hprops

    def _get_column_properties(self, props):
        cprops = {
            "anchor": props.pop("column_anchor", ""),
            "stretch": props.pop("stretch", "1"),
            "width": props.pop("width", "200"),
            "minwidth": props.pop("minwidth", "20"),
        }
        return cprops

    def _setup_column(self, parent, col_props, code_gen=False):
        tree_column = col_props.pop("tree_column", "false")
        tree_column = tree_column.lower()
        tree_column = True if tree_column == "true" else False
        column_id = "#0" if tree_column else self.wmeta.identifier
        visible = col_props.pop("visible", "true")
        visible = visible.lower()
        is_visible = True if visible == "true" else False

        # configure heading properties
        col_props.pop("command", "")
        hprops = self._get_heading_properties(col_props, code_gen)
        parent.set_heading(column_id, hprops)

        # configure column properties
        cprops = self._get_column_properties(col_props)
        parent.set_column(column_id, cprops, is_visible)

    def configure(self, target=None):
        pass

    def layout(self, target=None, *, forget=False):
        pass

    def _connect_command(self, cpname, callback):
        tree_column = self.wmeta.properties.get("tree_column", "false")
        tree_column = tree_column.lower()
        tree_column = True if tree_column == "true" else False
        column_id = "#0" if tree_column else self.wmeta.identifier
        self.widget.heading(column_id, command=callback)

    #
    # Code generation methods
    #
    def code_realize(self, boparent, code_identifier=None):
        self.parent_bo = boparent
        self._code_identifier = boparent.code_child_master()
        col_props = dict(self.wmeta.properties)  # copy properties
        self._setup_column(boparent, col_props, code_gen=True)
        return tuple()

    def code_configure(self, targetid=None):
        return tuple()

    def _code_connect_command(self, cmd_pname, cmd, cbname):
        target = self.parent_bo.code_identifier()

        args = cmd.get("args", "")
        args = args.split() if args else None
        lines = []
        cmdtype = cmd["cbtype"]
        if cmdtype == CB_TYPES.WITH_WID:
            wid = self.wmeta.identifier
            fname = f"{wid}_cmd_"
            fdef = f"""def {fname}(): {cbname}("{wid}")\n"""
            cbname = fname
            lines.append(fdef)

        tree_column = self.wmeta.properties.get("tree_column", "false")
        tree_column = True if tree_column.lower() == "true" else False
        column_id = "#0" if tree_column else self.wmeta.identifier
        lines.append(
            f"""{target}.heading("{column_id}", {cmd_pname}={cbname})"""
        )
        return lines


register_widget(
    "ttk.Treeview.Column",
    TTKTreeviewColumnBO,
    "Treeview.Column",
    (_("Pygubu Helpers"), "ttk"),
)


class TTKSpinboxBO(TTKWidgetBO, EntryBaseBO):
    OPTIONS_STANDARD = TTKEntry.OPTIONS_STANDARD
    OPTIONS_SPECIFIC = (
        TTKEntry.OPTIONS_SPECIFIC
        + (
            "from_",
            "to",
            "increment",
            "values",
            "wrap",
            "format",
            "command",
        )
        + _v9_entry_opts
    )
    OPTIONS_CUSTOM = TTKEntry.OPTIONS_CUSTOM
    class_ = None
    container = False
    properties = OPTIONS_STANDARD + OPTIONS_SPECIFIC + OPTIONS_CUSTOM
    command_properties = (
        "validatecommand",
        "invalidcommand",
        "xscrollcommand",
        "command",
    )
    virtual_events = ("<<Increment>>", "<<Decrement>>")


if tk.TkVersion >= 8.5:
    # Note:
    # ttk::Spinbox was added in tk 8.5.9 so it may fail in lower 8.5 patch versions

    if not hasattr(ttk, "Spinbox"):
        from pygubu.widgets.ttkspinbox import Spinbox

        ttk.Spinbox = Spinbox

    TTKSpinboxBO.class_ = ttk.Spinbox

    register_widget(
        "ttk.Spinbox",
        TTKSpinboxBO,
        "ttk.Spinbox",
        (_("Control & Display"), "ttk"),
    )


class OptionMenuBO(OptionMenuBaseMixin, BuilderObject):
    class_ = ttk.OptionMenu
    properties = (
        "style",
        "direction",
        "command",
        "variable",
        "value",
        "values",
    )
    command_properties = ("command",)
    ro_properties = ("variable", "value", "values")

    def _create_option_menu(self, master, variable, value, values, command):
        return self.class_(master, variable, value, *values, command=command)

    def _code_create_optionmenu(
        self,
        identifier,
        classname,
        master,
        value_arg,
        variable_arg,
        command_arg,
    ):
        return (
            f"{identifier} = {classname}({master}, {variable_arg},"
            + f" {value_arg}, *__values, command={command_arg})"
        )


register_widget(
    "ttk.OptionMenu",
    OptionMenuBO,
    "ttk.OptionMenu",
    (_("Control & Display"), "ttk"),
)


class LabeledScaleBO(BuilderObject):
    class_ = ttk.LabeledScale
    properties = (
        "compound",
        "variable",
        "from_",
        "to",
    )
    ro_properties = ("compound", "from_", "to", "variable")
    virtual_events = ("<<RangeChanged>>",)

    def _connect_binding(self, sequence: str, callback, add):
        self.widget.scale.bind(sequence, callback, add)

    def _code_connect_binding(
        self, target: str, sequence: str, callback: str, add_arg: str
    ):
        scale = f"{target}.scale"
        return super()._code_connect_binding(scale, sequence, callback, "+")


register_widget(
    "ttk.LabeledScale",
    LabeledScaleBO,
    "ttk.LabeledScale",
    (_("Control & Display"), "ttk"),
)
