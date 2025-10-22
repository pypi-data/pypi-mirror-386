History
=======

Changes for version 0.39

  * Dropping support for Python 3.8 (was already not installable)
  * Use version number from project.toml
  * Fix Dialog widget toplevel preview in designer.
  * Disable layout options for scrollbarhelper child in designer.
  * Editabletreeview: Add minimal padding.
  * Treeview: fix code generation for header images.
  * PathChooserInput: Update old value before user selection.
  * Fix issue when scrolling in tk 9.
  * ColorInput: reduce entry size. Fix issue setting frame color.
  * Add ColorInput in pygubu forms.
  * Internal iter_parents function, fix issue when mouse is over menu, from menubutton.
  * Builder: Add helper function to avoid calling get_object for every widget. refs #302
  * New theming.iconset module (feature preview).
  * Fix code generation issues for pygubu.widgets.dialog
  * Update tkinterweb plugin to support tkinterweb version 4.4.4

Changes for version 0.38.2

  * Fix errors with tk 8.5

Changes for version 0.38.1

  * Fix adding columns to Editabletreeview from old version xml. refs alejandroautalan/pygubu-designer#301

Changes for version 0.38

  * StockImage: Add default not found image.
  * Builder: Avoid raising error and use default not found image.
  * Treeview BO, fix missing command properties.
  * Treeview BO, fix incorrect code generated for yscroll and xscroll commands.
  * Fix code generation for treeview column command.
  * Notebook: Fix setting image in tab.
  * ColorInput: Fix error when setting textvariable.
  * Fix: Do not show layout properties for Notebook.Tab child.
  * Fix: setting minsize and maxsize on toplevels. hotfix
  * Theming: Fix error when pbs theme is selected again.

Changes for version 0.37.1

  * Fix: Use dimension values for minsize, maxsize properties. refs alejandroautalan/pygubu-designer#295

Changes for version 0.37

  * New property registry to manage custom properties
  * Allow pygubu bootstrap themes (pbs) on multiple roots.
  * Refactored simple tooltip module. Changed Tooltip class and added
    new Tooltipttk class.
  * New simple tooltip builders. Allows to use simple tooltips on designer.
  * New IStyleDefinition class to make easy custom styles definitions and
    management.
  * New font input widget.


Changes for version 0.36.3

  * Fix python 3.8, 3.9 compatibility. refs #301, alejandroautalan/pygubu-designer#288

Changes for version 0.36.2

  * Fix issue with setgrid tk.Text property. refs alejandroautalan/pygubu-designer#287
  * Fix showing unsupported font property for ttk.Button.  refs #300

Changes for version 0.36.1

  * Fix TypeError, scroll_rs not subscriptable exception.

Changes for version 0.36:

  * BuilderObject class: Store reference to parent.
  * BuilderObject class: Add option to override children layout.
  * Initial support for TKinterModernThemes package.
  * Clean tkinterweb plugin. Add tkinterweb Notebook widget.  refs alejandroautalan/pygubu-designer#278

Changes for version 0.35.6

  * Fix issue when setting menu for Menubutton. refs alejandroautalan/pygubu-designer#276

Changes for version 0.35.5

  * Fix menu code generation. refs #296
  * Fix issue with CTKEntry text property. refs alejandroautalan/pygubu-designer#266

Changes for version 0.35.4

  * Fix from, to properties on customtkinter CTKSlide.

Changes for version 0.35.3

  * Fix container layout on customtkinter CTKFrame.

Changes for version 0.35.2

  * Drop support for python 3.6 and 3.7 (was already not working)
  * Update pyinstaller hooks

Changes for version 0.35.1

  * Fix error in customtkinter Ctk builder

Changes for version 0.35

  * New theming module. Adds bootstrap like themes, based on ttkbootstrap.  Initial draft. TODO: improve graphics, draw with pillow if available.
  * Modified ApplicationLevelBindManager, methods are now class methods and not static methods.
    Added parameter master to the init_mousewheel_binding method.
  * Modified UI definition. Added project options section.
    Options saved: general options, code generation options, style definition, custom widgets.
  * New widgets:
      - New Hideable Frame widget.
      - New PathChooserButton widget.
      - New ColorInput widget.
      - New docking widgets: DockFrame, DockWidget, DockPane. In alpha status, although pygubu designer uses them.
      - New form widgets in alpha status.
      - Expose accordion widget hidden in pygubu code (Maybe it will be useful).
  * New emit_close_event for pygubu Dialog
  * Grid container options, fixed bug: process "all" index first, so specific row/col props are configured correctly.
  * New classmethods in Builder object canbe_parent_of, canbe_child_of.
  * Added copy_custom_property function
  * Added "public" argument to function register_widget
  * Added new method Builder.add_resource_paths(path_list: list)

Changes for version 0.34

  * Add missing container layout options for ScrolledFrame widget. Fixes alejandroautalan/pygubu#293

Changes for version 0.33

  * Update to support customtkinter 5.2.2

Changes for version 0.32

  * New builder for create a tkinter.Tk widget. (use it with caution)
  * Rewrite StockImage class. Allow to pass a user specific tkroot to create images.
  * Set widget tcl name for named widgets in designer. refs alejandroautalan/pygubu#287
  * Editabletreeview, allow a column to have multiple editors per row.
  * New FilterableTreeview widget.
  * Fix callback argument for code generation in designer. refs alejandroautalan/pygubu-designer#205
  * Fix for issue #284
  * Fix for missed update of 'activeoutline' color in CalendarFrame widget alejandroautalan/pygubu#285 (BloodyRain2k)
  * New "linewidth" option and visual fixes for CalendarFrame widget alejandroautalan/pygubu#286 (BloodyRain2k)

Changes for version 0.31:

  * Allow to setup values for option database after first window created. refs alejandroautalan/pygubu#282
  * Fix for widget highlighter offsets in preview, refs alejandroautalan/pygubu-designer#203

Changes for version 0.30:

  * Editabletreeview: Hide editors when user clicks inside treeview area
    with no rows. This generates \<\<TreeviewEditorsUnfocused\>\> event. refs alejandroautalan/pygubu#279
  * Editabletreeview: Add method get_value(col, item) to quicky
    access tree data. refs alejandroautalan/pygubu#279
  * Fix error on ttkwidgets plugin (autocomplete widgets)
  * Add support to customtkinter 5.
    Customtkinter changed a lot from 4.6 to 5.
    The plugin will support only the latest version.

Changes for version 0.29

  * Fixes for PathChooserInput. refs alejandroautalan/pygubu#278, alejandroautalan/pygubu-designer#145
  * Fixes for ToplevelPreviewBaseBO (for plugins)

Changes for version 0.28

  * Added ttk.OptionMenu and ttk.LabeledScale
    (alejandroautalan/pygubu-designer#178)
  * Fixed issues when working with Notebook tabs.
  * Restrict customtkinter plugin to customtkinter < 5
    (next version will only support customtkinter >= 5)

Changes for version 0.27

  * Builder object, REMOVED configure_for_preview method.
  * Added support for: customtkinter, tkintermapview

Changes for version 0.26.2

  * Fix for issues alejandroautalan/pygubu-designer#154, alejandroautalan/pygubu-designer#155

Changes for version 0.26.1

  * Hotfix for alejandroautalan/pygubu-designer#153

Changes for version 0.26

  * Allow pygubu to use importlib.resources module.  refs alejandroautalan/pygubu#269
  * Code generation: Fix callback registration arguments.
  * Builder object, new static method configure_for_preview.

Changes for version 0.25.1

  * Fix Menubutton code generation. refs alejandroautalan/pygubu-designer#151
  * Fix pyinstaller hook for python 3.8  refs alejandroautalan/pygubu#270

Changes for version 0.25

  * Modified ui definition file to allow decluttering of widget ids in designer (alejandroautalan/pygubu-designer#117)
  * Fix initial value for boolean tkvariables (issue alejandroautalan/pygubu#268)
  * Improved  menu code generation (refs alejandroautalan/pygubu-designer#103)

Changes for version 0.24.2

  * Fix loading of custom widgets

Changes for version 0.24.1

  * Hotfix: Fix error loading tkcalendar DateEntry
  * Added pyinstaller hook (thanks to @gwelch-contegix)

Changes for version 0.24

  * New plugin engine and API (alpha state)
  * Added support for: AwesomeTkinter, tkintertable, tksheet, ttkwidgets,
    tkinterweb, tkcalendar.
  * Changed project structure to use src folder.

Changes for version 0.23.1

  * Fix: Generate regular treeview properties in the Code Script alejandroautalan/pygubu#264 (jrezai)

Changes for version 0.23

  * Translations for pygubu strings in pygubu-designer (larryw3i)

Changes for version 0.22

  * Code generation: mark translatable text in code. issue alejandroautalan/pygubu-designer#120
  * Code generation: generate keyword arguments as integers when posible. issue alejandroautalan/pygubu-designer#114
  * Code generation: Fix OptionMenu. issue alejandroautalan/pygubu-designer#125

Changes for version 0.21

  * Editabletreeview: Add InplaceEditor abstract class for better management of column data editors.
  * Improve argument names for entry validate callback.
  * Fix: Generate escaped strings on code generation.
  * Other minor fixes.

Changes for version 0.20

  * Removed Python 2.7 support, Minimum Python version required is now 3.6
  * Added support to configure grid with 'all' index
  * Change in xml specification. Interface version is now 1.2. This includes reorganization of grid row/column properties.

Changes for version 0.19

  * Fix generating redundant code for grid properties
  * Fix install error on python 2.7
  * This is the last version with python 2.7 support

Changes for version 0.9.8

  * Use entry_points field for installing a startup script with setuptools
  * Fixed issues #66, #86

Changes for version 0.9.7.9

  * Fixed issues #72, #74, #78, #81

Changes for version 0.9.7.8

  * Added wheel support.
  * Fixed issues #64, #65

Changes for version 0.9.7.7

  * Improved ui tester.
  * Fixed issues #54, #58, #59, #60

Changes for version 0.9.7.5

  * Allow to specify variable names when importing tk variables.
  * Allow to register an already created tk image.
  * Allow to specify loggin level from console command.
  * Added new pathchooser input widget.
  * Improved README (thanks to Nelson Brochado)
  * Fixed issue #52

Changes for version 0.9.7.3

  * Added custom widgets preference option.
  * Added appdirs dependency.
  * New sticky property editor.
  * Fixed issues #40, #45

Changes for version 0.9.7

  * Fixed issues #39, #41

Changes for version 0.9.6.7

  * Remove old pygubu.py script for old installations.
    Create pybugu-designer.bat file for windows platform. Fixes #38

Changes for version 0.9.6.6

  * Fixed bug: color value setting to None when presing Cancel on color selector.
  * Add '.png' format to Stockimage if tk version support it. fixes #36
  * Minor changes to main UI.

Changes for version 0.9.6.5

  * Fixed bug on menu creation.
  * Fixed issues #14 and #22
  * Added helper method to avoid call get_variable for every variable. refs #29

Changes for version 0.9.6.4

  * Fixed bug #33 "Wrong textvariable format when create ui file"

Changes for version 0.9.6.3

  * Use old menu preview on platforms other than linux  (new preview does not work on windows)

Changes for version 0.9.6.2

  * Property editors rewritten from scratch
  * Improved menu preview
  * Added font property editor
  * Fixed menu issues

Changes for version 0.9.5.1

  * Add select hotkey to widget tree. (i - select previous item, k - select next item)
  * Copied menu example from wiki to examples folder.

Changes for version 0.9.5

  * Renamed designer startup script to pygubu-designer (see [#20](/../../issues/20))
  * Fixed bugs.

Changes for version 0.9.4

  * Added Toplevel widget
  * Added generic Dialog widget
  * Rewrited scrolledframe widget internals, ideas and code taken from tkinter wiki.
  * Added more widget icons.
  * Fixed bugs.

Changes for version 0.9.3

  * Allow to select control variable type
  * Fixed some bugs.

Changes for version 0.9.2

  * Added more wiki pages.
  * Fixed issues #3, #4

Changes for version 0.9.1

  * Separate designer module from main package
  * Added menu to select current ttk theme
  * Fix color selector issues.

Changes for version 0.9

  * Add validator for pax and pady properties.
  * Improved ScrolledFrame widget.
  * Added more wiget icons.
  * Fix cursor type on preview panel.

Changes for version 0.8

  * Added translation support
  * Translated pygubu designer to Spanish

Changes for version 0.7

  * Added python 2.7 support
  * Added initial TkApplication class
  * Fixed some bugs.

First public version 0.6
