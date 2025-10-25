#    Copyright © 2021 Andrei Puchko
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import sys


import q2gui.q2app as q2app
from configparser import ConfigParser

# from q2gui.q2window import Q2Window
from q2gui.q2utils import num

import re
import io
import time
import os
import codecs
import logging


q2_app = None
engine = ""
Q2Form = None

ASK_REMOVE_RECORD_TEXT = "You are about to remove current record! Are You Sure?"
ASK_REMOVE_RECORDS_TEXT = "You are about to remove records<b>(%s)</b>! Are You Sure?"
REMOVE_RECORD_ERROR_TEXT = "Remove record error"

DATE_FORMAT_STRING = "%d.%m.%Y"


ACTION_HIDDEN_ROW_TEXT = "Rows"
ACTION_HIDDEN_ROW_ICON = "eye.svg"

ACTION_HIDE_ROW_TEXT = "Hide row"
ACTION_HIDE_ROW_ICON = "list-minus.svg"

ACTION_SHOW_ROW_TEXT = "Show row"
ACTION_SHOW_ROW_ICON = "list-plus.svg"

ACTION_SHOW_NOTHIDDEN_TEXT = "Show not hidden"
ACTION_SHOW_NOTHIDDEN_ICON = "list-chevrons-down-up.svg"

ACTION_SHOW_ALL_TEXT = "Show all"
ACTION_SHOW_ALL_ICON = "list-chevrons-up-down.svg"

ACTION_SHOW_HIDDEN_TEXT = "Show hidden"
ACTION_SHOW_HIDDEN_ICON = "eye-off.svg"

ACTION_VIEW_TEXT = "View"
ACTION_VIEW_ICON = "row-view.png"
ACTION_VIEW_HOTKEY = "F12"

ACTION_NEW_TEXT = "New"
ACTION_NEW_ICON = "row-new.png"
ACTION_NEW_HOTKEY = "Ins"

ACTION_COPY_TEXT = "Copy"
ACTION_COPY_ICON = "row-copy.png"
ACTION_COPY_HOTKEY = "Ctrl+Ins"

ACTION_EDIT_TEXT = "Edit"
ACTION_EDIT_ICON = "row-edit.png"
ACTION_EDIT_HOTKEY = "Spacebar"

ACTION_REMOVE_TEXT = "Remove"
ACTION_REMOVE_ICON = "row-remove.png"
ACTION_REMOVE_HOTKEY = "Delete"


ACTION_FIRST_ROW_TEXT = "First"
ACTION_FIRST_ROW_ICON = "go-top.png"
ACTION_FIRST_ROW_HOTKEY = "Ctrl+Up"

ACTION_PREVIOUS_ROW_TEXT = "Previous"
ACTION_PREVIOUS_ROW_ICON = "go-up.png"

ACTION_REFRESH_TEXT = "Refresh"
ACTION_REFRESH_ICON = "refresh.png"
ACTION_REFRESH_HOTKEY = "F5"

ACTION_RENUMBER_TEXT = "Renumber"
ACTION_RENUMBER_ICON = ""
ACTION_RENUMBER_HOTKEY = ""

ACTION_NEXT_ROW_TEXT = "Next"
ACTION_NEXT_ROW_ICON = "go-down.png"

ACTION_LAST_ROW_TEXT = "Last"
ACTION_LAST_ROW_ICON = "go-bottom.png"
ACTION_LAST_ROW_HOTKEY = "Ctrl+Down"

ACTION_TOOLS_TEXT = "Tools"
ACTION_TOOLS_ICON = "tools.png"

ACTION_TOOLS_COLOR_TEXT = "Set color"
# ACTION_TOOLS_ICON = "tools.png"

ACTION_TOOLS_EXPORT_TEXT = "Export"
ACTION_TOOLS_EXPORT_ICON = "export.png"

ACTION_TOOLS_IMPORT_TEXT = "Import"
ACTION_TOOLS_IMPORT_ICON = "import.png"

ACTION_TOOLS_IMPORT_CLIPBOARD_TEXT = "Paste clipboard"
ACTION_TOOLS_IMPORT_CLIPBOARD_ICON = "paste-csv.png"

ACTION_TOOLS_BULK_UPDATE_TEXT = "Bulk update"
ACTION_TOOLS_BULK_UPDATE_ICON = "bulk-update.png"

ACTION_TOOLS_INFO_TEXT = "Info"
ACTION_TOOLS_INFO_ICON = "info.png"

ACTION_SELECT_TEXT = "Select"
ACTION_SELECT_ICON = "select.png"

ACTION_CLOSE_TEXT = "Close"
ACTION_CLOSE_ICON = "exit.png"

CRUD_BUTTON_EDIT_TEXT = "Edit"
CRUD_BUTTON_EDIT_MESSAGE = "enable editing"

CRUD_BUTTON_OK_TEXT = "OK"
CRUD_BUTTON_OK_MESSAGE = "save data"

CRUD_BUTTON_CANCEL_TEXT = "Cancel"
CRUD_BUTTON_CANCEL_MESSAGE = "Do not save changes"

GRID_ACTION_TEXT = "☰"
GRID_ACTION_ICON = "menu.png"

ARROW_UP_ICON = "arrow-up.png"
ARROW_DOWN_ICON = "arrow-down.png"

FINANCIAL_FORMAT = r"{:,.%sf}"
GRID_COLUMN_WIDTH = 25

MESSAGE_SORTING = "Sorting..."
MESSAGE_SORTING = "Sorting..."
MESSAGE_ROWS_HIDING = "Toggle hide/show rows"
MESSAGE_ROWS_COLOR = "Colorizing rows"

MESSAGE_GRID_DATA_EXPORT_TITLE = "Export data"
MESSAGE_GRID_DATA_EXPORT_WAIT = "Export data to: %s"
MESSAGE_GRID_DATA_EXPORT_ERROR = "Export error: %s"
MESSAGE_GRID_DATA_EXPORT_DONE = "Export done:<br>Rows: %s<br>Time: %.2f sec."

MESSAGE_GRID_DATA_IMPORT_TITLE = "Import data"
MESSAGE_GRID_DATA_IMPORT_WAIT = "Import data to: %s"
MESSAGE_GRID_DATA_IMPORT_ERROR = "Import error: %s"
MESSAGE_GRID_DATA_IMPORT_DONE = "Import done:<br>Rows: %s<br>Time: %.2f sec."

GRID_DATA_INFO_TABLE = "Table/Query"
GRID_DATA_INFO_SQL = "Query"
GRID_DATA_INFO_ROWS = "Rows"
GRID_DATA_INFO_ORDER = "Order"
GRID_DATA_INFO_FILTER = "Filter"
GRID_DATA_INFO_COLUMNS = "Columns"

PASTE_CLIPBOARD_WAIT = "Paste rows"
PASTE_CLIPBOARD_TITLE = "Paste (Clipboard)"
PASTE_CLIPBOARD_FIRST_ROW = "First row is a header"
PASTE_CLIPBOARD_CLIPBOARD_DATA = "Clipboard data"
PASTE_CLIPBOARD_TARGET = "Target"
PASTE_CLIPBOARD_SOURCE = "Source"
PASTE_CLIPBOARD_TARGET_COLUMNS = "Target columns"
PASTE_CLIPBOARD_SOURCE_COLUMNS = "Source columns"

BULK_DATA_ENTRY_TITLE = "Bulk data"
BULK_DATA_MAIN_TITLE = "Bulk update selected rows"
BULK_DATA_WAIT = "Bulk update rows"
BULK_TARGET_TITLE = "Target"
BULK_TARGET_COLUMNS = "Columns"
BULK_TARGET_SELECTED = "Selected"

ASK_ROWS_REMOVING_ERRORS_SUPRESS = "Do not show next errors"
ASK_COPY_CHILD_DATA = "Copy %s?"

DIALOG_OPEN_FILE_TITLE = "Open file"
DIALOG_SAVE_FILE_TITLE = "Save file"

from q2gui.q2style import Q2Style


def load_q2engine(glo, engine="PyQt6"):
    from q2gui.pyqt6.q2app import Q2App as Q2App
    from q2gui.pyqt6.q2form import Q2Form as Q2Form
    from q2gui.pyqt6.q2style import Q2Style as Q2Style

    q2app.engine = engine
    Q2App.Q2Form = Q2Form

    glo["Q2App"] = Q2App
    glo["Q2Form"] = Q2Form
    glo["Q2Style"] = Q2Style


class Q2Heap:
    pass


class Q2Actions(list):
    def __init__(self, action=None):
        self.show_main_button = True
        self.show_actions = True
        self.main_button_text = GRID_ACTION_TEXT
        if isinstance(action, list):
            # self.action_list = action[:]
            self.extend(action[:])
        # else:
        #     self.action_list = []

    def run(self, text):
        for action in self:
            if text == action["text"]:
                action["_worker"]()

    def set_visible(self, text, mode=True):
        for action in self:
            if text == action["text"]:
                action["_set_visible"](mode)
            # elif text == action.get("parent_action_text"):
            #     action["_set_visible_parent_action"](mode)

    def set_disabled(self, text="", mode=True):
        for action in self:
            if text == action["text"]:
                action["_set_disabled"](mode)

    def set_enabled(self, text="", mode=True):
        for action in self:
            if text == action["text"]:
                action["_set_enabled"](mode)

    def add_action(
        self,
        text,
        worker=None,
        icon="",
        mess="",
        hotkey="",
        tag="",
        eof_disabled="",
        child_form=None,
        child_where="",
        child_copy_mode=1,
        child_noshow=0,
    ):
        """ "/view", "/crud" """
        for x in range(len(self)):
            # if text in self[x]["text"] and text.strip()[-1] != "-":
            if text == self[x]["text"] and text.strip()[-1] != "-":
                self[x]["worker"] = worker
                self[x]["hotkey"] = hotkey
                return True
        action = {}
        action["text"] = text
        action["worker"] = worker
        action["child_copy_mode"] = child_copy_mode
        action["child_noshow"] = child_noshow

        if tag == "select":
            icon = ACTION_SELECT_ICON

        # icon = q2_app.get_icon(icon)

        # action["icon"] = icon if os.path.isfile(icon) else ""
        action["icon"] = icon if icon else ""
        action["mess"] = mess
        action["hotkey"] = hotkey
        action["tag"] = tag
        action["eof_disabled"] = eof_disabled
        action["child_form"] = child_form
        action["child_where"] = child_where
        self.append(action)
        return True

    # def insertAction(
    #     self, before, text, worker=None, icon="", mess="", key="", **kvargs
    # ):
    #     for x in self.addAction.__code__.co_varnames:
    #         if x not in ["kvargs", "self"]:
    #             kvargs[x] = locals()[x]
    #     self.action_list.insert(before, kvargs)

    # def removeAction(self, text):
    #     actionIndex = safe_index([x["text"] for x in self.action_list], text)
    #     if actionIndex is not None:
    #         self.action_list.pop(actionIndex)
    pass


class Q2Controls(list):
    class _C:
        def __init__(self, controls):
            self.controls = controls

        def __getattr__(self, name):
            for line in self.controls:
                if line.get("column") == name or line.get("tag") == name:
                    return line
            return None
            # return [line["column"] for line in self.controls]

    def __init__(self):
        self.c = self._C(self)

    def get(self, name):
        return self.c.__getattr__(name)

    def delete(self, name):
        c = self.get(name)
        self.pop(self.index(c))

    def get_names(self):
        return [line["column"] for line in self]

    # def __getitem__(self, list_index):
    #     if isinstance(list_index, str):  # not index but name - return index for name
    #         for x in range(len(self)):
    #             if list_index == self[x].get("column"):
    #                 return x
    #         return None
    #     else:
    #         return super().__getitem__(list_index)

    def add_control(
        self,
        column="",
        label="",
        gridlabel="",
        control="",
        pic="",
        data="",
        datatype="char",
        datalen=0,
        datadec=0,
        pk="",
        ai="",
        migrate="*",
        actions=[],
        alignment=-1,
        to_table="",
        to_column="",
        to_form=None,
        related="",
        db=None,
        mask="",
        opts="",
        when=None,
        show=None,
        valid=None,
        changed=None,
        dblclick=None,
        readonly=None,
        disabled=None,
        check=None,
        noform=None,
        nogrid=None,
        widget=None,
        margins=None,
        stretch=0,
        mess="",
        tag="",
        eat_enter=None,
        hotkey="",
        style="",
        **args,
    ):
        meta = locals().copy()
        del meta["self"]
        meta["_control"] = None
        # meta = self.validate(meta)
        self.append(meta)
        return True

    @staticmethod
    def validate(meta):
        if meta.get("margins") is None:
            if q2app.q2_app:
                meta["margins"] = [
                    q2app.q2_app.content_margin_top,
                    q2app.q2_app.content_margin_right,
                    q2app.q2_app.content_margin_bottom,
                    q2app.q2_app.content_margin_left,
                ]
            else:
                meta["margins"] = [1, 1, 1, 1]

        if meta.get("datatype") == "char":
            if re.match(".*code.*|.*text.*", meta.get("control", ""), re.RegexFlag.IGNORECASE):
                meta["datatype"] = "text"

        if meta.get("datatype", "").lower() == "date":
            meta["control"] = "date"
            meta["datalen"] = 16

        if meta.get("datatype", "").lower() == "time":
            meta["control"] = "time"
            meta["datalen"] = 10

        if meta.get("column").startswith("/"):
            meta["control"] = ""
        elif not meta.get("control") and not meta.get("widget") and meta.get("column"):
            meta["control"] = "line"
            # meta["control"] = ""

        if num(meta.get("datalen", 0)) == 0 and meta.get("control", "") in ("line", "radio"):
            if meta.get("datatype", "").lower()[:3] == "int":
                meta["datalen"] = 9
            elif meta.get("datatype", "").lower() == "bigint":
                meta["datalen"] = 17
            else:
                meta["datalen"] = 100

        if (
            re.match(".*text.*", meta.get("datatype", ""), re.RegexFlag.IGNORECASE)
            and "code" not in meta["control"]
            and "image" not in meta["control"]
        ):
            meta["datalen"] = 0
            meta["control"] = "text"

        if "***" == "".join(["*" if meta.get(x) else "" for x in ("to_table", "to_column", "related")]):
            meta["relation"] = True

        if re.match(".*int.*|.*dec.*|.*num.*", meta.get("datatype", ""), re.RegexFlag.IGNORECASE):
            meta["num"] = True
            if meta.get("pic", "") == "":
                meta["pic"] = "9" * int(num(meta["datalen"]) - num(meta["datadec"])) + (
                    "" if num(meta["datadec"]) == 0 else "." + "9" * int(num(meta["datadec"]))
                )
            if num(meta.get("alignment", -1)) in (
                -1,
                0,
            ):
                meta["alignment"] = 9

        if not meta["column"].startswith("/"):
            if "char" in meta.get("datatype", "") and num(meta.get("datalen")) == 0:
                if meta.get("control") in ("check"):
                    meta["datalen"] = 1
                elif meta.get("control") in ("line"):
                    meta["datalen"] = 100
        return meta


class Q2Settings:
    def __init__(self, filename=""):
        self.filename = filename if filename else "q2gui.ini"
        self.config = ConfigParser()
        self.read()

    def read(self):
        if self.filename in ("none", "memory"):
            self.filename = io.StringIO("")
        if isinstance(self.filename, io.StringIO):
            self.config.read_file(self.filename)
        else:
            if not os.path.isfile(self.filename):
                self.write()
            try:
                self.config.read_file(codecs.open(self.filename, "r", "utf8"))
            except Exception as read_error:
                logging.error(f"Error reading {self.filename}:\n{read_error}")
                self.fix_ini_headers()
                self.config.read_file(codecs.open(self.filename, "r", "utf8"))
            except Exception as recovery_error:
                logging.error(f"Error while trying recover {self.filename}:\n{recovery_error}")
                raise

    def write(self):
        if self.filename == "none":
            return
        if isinstance(self.filename, io.StringIO):
            self.config.write(self.filename)
        else:
            with codecs.open(self.filename, "w", "utf8") as configfile:
                self.config.write(configfile)

    def prepSection(self, section):
        return re.sub(r"\[.*\]", "", section).strip().split("\n")[0].replace("\n", "").strip()

    def get(self, section="", key="", defaultValue=""):
        section = self.prepSection(section)
        key = self.prepSection(key)
        try:
            return self.config.get(section, key)
        except Exception:
            return defaultValue

    def set(self, section="", key="", value=""):
        if section == "":
            return
        section = self.prepSection(section)
        key = self.prepSection(key)
        value = "%(value)s" % locals()
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, value)

    def fix_ini_headers(self):
        with open(self.filename, "r", encoding="utf-8") as file:
            content = file.read()

        # fix section headers with sections with hyphens
        pattern = r"\[(.+?)\n\.(.*?)\]"
        fixed_content = re.sub(pattern, r"[\1 \2]", content)

        with open(self.filename, "w", encoding="utf-8") as file:
            file.write(fixed_content)


class Q2Stdout:
    def __init__(self, q2_app):
        self.q2_app = q2_app

    def write(self, output):
        if self.q2_app.dev_mode and hasattr(self.q2_app.stdout_widget, "write"):
            self.q2_app.stdout_widget.write(output)
        else:
            try:
                sys.__stdout__.write(output)
            except Exception as e:
                logging.warning(f"{e}")

    def flush(self):
        sys.__stdout__.flush()


class Q2App:
    Q2Style = Q2Style
    Q2Form = None

    def __init__(self, title=""):
        q2app.q2_app = self
        self.window_title = title
        self.heap = Q2Heap()
        self.db = None
        self.style_file = ""
        self.settings_file = ""
        self.dev_mode = None
        self.settings_file = self.get_argv("ini")
        self.icon = None
        sys.stdout = Q2Stdout(self)

        self.menu_list = []
        self._main_menu = {}

        self.settings = Q2Settings(self.settings_file)

        self.style_file = self.get_argv("style")
        if self.style_file == "":
            self.style_file = "q2gui.qss"

        self.q2style: Q2Style = self.Q2Style(self)
        # print(self.q2style)
        # self.q2style._font_size = 25
        # self.q2style._font_name = "Arial"
        # self.q2style.set_style_sheet(self, "light")
        # self.set_color_mode("light")

        self.menu_list = []
        self.content_margin_top = 0
        self.content_margin_right = None
        self.content_margin_bottom = None
        self.content_margin_left = None
        self.assets_folder = "assets"
        self.set_icon(f"{self.assets_folder}/q2gui.ico")

        self.on_init()

    def set_clipboard(self, text):
        pass

    def get_stdout_height(self):
        pass

    def subwindow_count_changed(self):
        pass

    def disable_menu(self, menu_path=""):
        pass

    def enable_menu(self, menu_path=""):
        pass

    def set_color_mode(self, color_mode=None):
        self.q2style.set_color_mode(self, color_mode)

    def get_color_mode(self):
        return self.q2style.get_color_mode()

    def set_font(self, font_name, font_size):
        pass

    def set_style_sheet(self):
        pass

    def get_icon(self, icon):
        icon_path = f"{self.assets_folder}/{icon}"
        if os.path.isfile(icon_path):
            return icon_path

    def get_argv(self, argtext: str):
        for x in sys.argv:
            if x.startswith(f"/{argtext}:") or x.startswith(f"-{argtext}:"):
                file_name = x[(len(argtext) + 2) :]  # noqa: E203
                return file_name
        return ""

    def add_menu(self, text="", worker=None, before=None, toolbar=None, icon=None, tag=""):
        if text.endswith("|"):
            text = text[:-1]
        if text.startswith("|"):
            text = text[1:]
        self.menu_list.append(
            {"TEXT": text, "WORKER": worker, "BEFORE": before, "TOOLBAR": toolbar, "ICON": icon, "TAG": tag}
        )

    def clear_menu(self):
        self.menu_list = []

    def get_autocompletition_list(self):
        return [
            "test_autocompletion",
            "test_table",
            "test_table.column1",
            "test_table.column2",
        ]

    def build_menu(self):
        self.menu_list = self.reorder_menu(self.menu_list)

    def reorder_menu(self, menu):
        tmp_list = [x["TEXT"] for x in menu]
        tmp_dict = {x["TEXT"]: x for x in menu}
        re_ordered_list = []
        for x in tmp_list:
            # add node element for menu
            menu_node = "|".join(x.split("|")[:-1])
            if menu_node not in re_ordered_list:
                re_ordered_list.append(menu_node)
                tmp_dict[menu_node] = {
                    "TEXT": menu_node,
                    "WORKER": None,
                    "BEFORE": None,
                    "TOOLBAR": None,
                }
            if tmp_dict[x].get("BEFORE") in re_ordered_list:
                re_ordered_list.insert(re_ordered_list.index(tmp_dict[x].get("BEFORE")), x)
            else:
                re_ordered_list.append(x)
        return [tmp_dict[x] for x in re_ordered_list]

    def close(self):
        self.save_geometry(self.settings)

    def save_geometry(self, settings):
        pass

    def restore_geometry(self, settings):
        pass

    def show_statusbar_mess(self, text=""):
        pass

    def clear_statusbar(self):
        pass

    def get_statusbar_mess(self):
        pass

    def show_form(self, form=None, modal="modal"):
        pass

    def get_dpi(self):
        pass

    def focus_changed(self, from_widget, to_widget):
        if not (hasattr(from_widget, "meta") and hasattr(to_widget, "meta")):
            return
        if from_widget.__class__.__name__ in (
            "q2line",
            "q2text",
            "q2relation",
            "q2ScriptEdit",
            "q2ScriptSqlEdit",
        ):
            if from_widget.meta.get("form") == to_widget.meta.get("form"):
                if from_widget.valid() is False:
                    from_widget.set_focus()
        if to_widget.__class__.__name__ in (
            "q2line",
            "q2text",
            "q2relation",
            "q2ScriptEdit",
            "q2ScriptSqlEdit",
        ):
            if from_widget.meta.get("form") == to_widget.meta.get("form"):
                if to_widget:
                    to_widget.when()

    def get_clipboard_text(self):
        pass

    def set_clipboard_text(self):
        pass

    def lock(self):
        pass

    def unlock(self):
        pass

    def set_icon(self):
        pass

    def process_events(self):
        pass

    def on_init(self):
        self.set_icon(f"{self.assets_folder}/q2gui.ico")

    def on_start(self):
        pass

    def on_new_tab(self):
        pass

    def show_menubar(self, mode=True):
        pass

    def hide_menubar(self, mode=True):
        if mode:
            self.show_menubar(False)
        else:
            self.show_menubar(True)

    def is_menubar_visible(self):
        pass

    def is_menubar_enabled(self):
        pass

    def show_toolbar(self, mode=True):
        pass

    def hide_toolbar(self, mode=True):
        if mode:
            self.show_toolbar(False)
        else:
            self.show_toolbar(True)

    def is_toolbar_visible(self):
        pass

    def is_toolbar_enabled(self):
        pass

    def disable_toolbar(self, mode=True):
        pass

    def enable_toolbar(self, mode=True):
        self.disable_toolbar(not mode)
        pass

    def disable_menubar(self, mode=True):
        pass

    def enable_menubar(self, mode=True):
        self.disable_menubar(not mode)

    def disable_tabbar(self, mode=True):
        pass

    def enable_tabbar(self, mode=True):
        self.disable_tabbar(not mode)

    def show_tabbar(self, mode=True):
        pass

    def get_current_q2_form(self):
        pass

    def disable_current_form(self, mode=True):
        pass

    def get_tabbar_text(self):
        pass

    def set_tabbar_text(self, text=""):
        pass

    def hide_tabbar(self, mode=True):
        if mode:
            self.show_tabbar(False)
        else:
            self.show_tabbar(True)

    def is_tabbar_visible(self):
        pass

    def is_tabbar_enabled(self):
        pass

    def show_statusbar(self, mode=True):
        pass

    def keyboard_modifiers(self):
        pass

    def hide_statusbar(self, mode=True):
        if mode:
            self.show_statusbar(False)
        else:
            self.show_statusbar(True)

    def is_statusbar_visible(self):
        pass

    def get_char_width(self, char="W"):
        return 9

    def get_char_height(self):
        return 9

    def sleep(self, seconds=0):
        time.sleep(seconds)

    @staticmethod
    def get_open_file_dialoq(header="Open file", path="", filter=""):
        pass

    @staticmethod
    def get_save_file_dialoq(header="Save file", path="", filter="", confirm_overwrite=True):
        pass

    def add_new_tab(self):
        pass

    def run(self):
        self.build_menu()

    def click_submenu(menu, submenu_text):
        pass
