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


from q2gui import q2app
from q2gui.q2app import Q2Actions
from q2gui.q2app import GRID_ACTION_TEXT, GRID_ACTION_ICON

from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QToolBar, QSizePolicy, QToolButton, QMenu
from PyQt6.QtGui import QIcon, QColor, QFont
from PyQt6.QtCore import Qt

from q2gui.pyqt6.q2widget import Q2Widget
from q2gui.pyqt6.q2window import q2_align


class q2toolbar(QFrame, Q2Widget):
    def __init__(self, meta):
        super().__init__(meta)
        self.setLayout(QVBoxLayout() if "v" in meta.get("control") else QHBoxLayout())
        # self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum)
        self.layout().setAlignment(q2_align["7"])
        self.layout().setSpacing(-1)
        self.layout().setContentsMargins(0, 0, 0, 0)

        self.icon_size = 24
        tmp_icon = q2app.q2_app.get_icon(GRID_ACTION_ICON)
        if tmp_icon:
            self.icon_size = QIcon(tmp_icon).availableSizes()[0].width()

        self.toolBarPanel = QToolBar(self)
        self.toolBarPanel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        action_list = []
        if isinstance(meta.get("actions"), Q2Actions):
            action_list.extend(meta.get("actions"))
            actions = meta.get("actions")
        elif isinstance(meta.get("actions"), list):
            for x in meta.get("actions"):
                if isinstance(x, Q2Actions):
                    action_list.extend(x)
            actions = meta.get("actions")[0]

        if action_list is []:
            return

        self.show_main_button = actions.show_main_button
        self.show_actions = actions.show_actions
        self.tool_bar_qt_actions = QMenu()
        self.cascade_action = {"": self.tool_bar_qt_actions}

        for action in action_list:
            if action.get("text", "").startswith("/"):
                continue
            worker = action.get("worker", None)
            action_text_list = action["text"].split("|")
            for x in range(len(action_text_list)):
                action_key = "|".join(action_text_list[:x])
                action_text = action_text_list[x]
                if action_text == "-":
                    action["engineAction"] = self.cascade_action[action_key].addSeparator()
                else:
                    if x + 1 == len(action_text_list) and (
                        action.get("worker") or (action.get("child_where") and action.get("child_form"))
                    ):  # real action
                        action["engineAction"] = self.cascade_action[action_key].addAction(action_text)
                        action["parent_action"] = self.cascade_action[action_key]
                        action["parent_action_text"] = action_key

                        action["_set_visible_parent_action"] = lambda mode=True, act=action[
                            "parent_action"
                        ]: act.setVisible(mode)

                        action["_set_visible"] = lambda mode=True, act=action["engineAction"]: act.setVisible(
                            mode
                        )
                        action["_set_enabled"] = lambda mode=True, act=action["engineAction"]: act.setEnabled(
                            mode
                        )
                        action["_set_disabled"] = lambda mode=True, act=action[
                            "engineAction"
                        ]: act.setDisabled(mode)
                        action["engineAction"].setToolTip(action.get("mess", ""))
                        action["engineAction"].setStatusTip(action.get("mess", ""))
                        action["engineAction"].setObjectName(action.get("tag", ""))

                        action["engineAction"].setIcon(q2app.q2_app.get_engine_icon(action.get("icon", "")))

                        if worker:
                            action["_worker"] = worker
                            action["engineAction"].triggered.connect(worker)
                        elif action.get("child_where") and action.get("child_form"):

                            def getChildForm(action):
                                def rd():
                                    self.meta["form"].show_child_form(action)

                                return rd

                            action["_worker"] = getChildForm(action)
                            action["engineAction"].triggered.connect(getChildForm(action))

                        action["engineAction"].setShortcut(
                            action["hotkey"] if not action["hotkey"] == "Spacebar" else Qt.Key.Key_Space
                        )
                        action["engineAction"].setShortcutContext(
                            Qt.ShortcutContext.WidgetWithChildrenShortcut
                        )
                    else:  # cascade
                        subMenu = "|".join(action_text_list[: x + 1])
                        if subMenu not in self.cascade_action:
                            self.cascade_action[subMenu] = self.cascade_action[action_key].addMenu(
                                f"{action_text}  {'' if '|' in subMenu else '  '}"
                            )
                            if action.get("icon", ""):
                                self.cascade_action[subMenu].setIcon(
                                    q2app.q2_app.get_engine_icon(action.get("icon", ""))
                                )

        self.main_button = QToolBar(self)

        self.main_button_action = QToolButton(self)
        self.main_button_action.setText(GRID_ACTION_TEXT)

        self.main_button_action.setIcon(q2app.q2_app.get_engine_icon(GRID_ACTION_ICON))

        self.main_button_action.setToolTip(self.meta.get("mess", ""))
        self.main_button_action.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.main_button_action.setMenu(self.tool_bar_qt_actions)

        font_size = q2app.q2_app.q2style.font_size
        font_name = q2app.q2_app.q2style.font_name
        if q2app.q2_app.get_color_mode() != "clean":
            background_control = q2app.q2_app.q2style.get_styles()["background_control"]
            toolbutton_background = q2app.q2_app.q2style.get_styles()["toolbutton_background"]
            background_menu_selection = q2app.q2_app.q2style.get_styles()["background_menu_selection"]
            color = q2app.q2_app.q2style.get_styles()["color"]
            self.main_button_action.menu().setStyleSheet(
                f"""
                    QMenu {{
                            border:1px solid palette(Mid);
                            color: black;
                            background-color: {background_control};
                            font-size:{font_size}pt;
                            font-family:'{font_name}'
                            }}
                    QMenu::separator {{height: 1px;background: {color};}}
                    QMenu{{
                        border:1px solid {color};
                    }}
                    QMenu::item, QMenu:disabled
                        {{
                            color: black;
                            background-color: {toolbutton_background};
                            selection-color: palette(HighlightedText);
                            selection-background-color: {background_menu_selection};
                        }}
                    QMenu::item:disabled
                        {{
                            color: gray;
                        }}
                    """
            )
        else:
            self.main_button_action.menu().setStyleSheet(
                f"""
                    QMenu {{
                            border:1px solid palette(Mid);
                            color: black;
                            font-size:{font_size}pt;
                            font-family:'{font_name}'
                            }}
                    """
            )

        self.main_button.addWidget(self.main_button_action)

        self.layout().addWidget(self.main_button)
        if not self.show_main_button:
            self.main_button.setVisible(False)

        self.toolBarPanel.addSeparator()
        self.toolBarPanel.addActions(self.tool_bar_qt_actions.actions())

        for x in self.toolBarPanel.actions():
            action_widget = self.toolBarPanel.widgetForAction(x)
            if hasattr(action_widget, "setPopupMode"):
                action_widget.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        if self.show_actions:
            self.layout().addWidget(self.toolBarPanel)

        self.set_background_color()

    def set_background_color(self):
        if q2app.q2_app.get_color_mode() != "clean":
            disabled_background_color = QColor(
                q2app.q2_app.q2style.get_styles()["background_disabled"]
            ).name()
            background_color = QColor(q2app.q2_app.q2style.get_styles()["toolbutton_background"]).name()
            hover_color = QColor(q2app.q2_app.q2style.get_styles()["background_menu_selection"]).name()
        else:
            disabled_background_color = "palette(window)"
            background_color = "palette(window)"
            hover_color = "palette(active)"
        for action in self.toolBarPanel.actions():
            action_widget = self.toolBarPanel.widgetForAction(action)
            if action_widget is None:
                continue
            base_background_color = background_color
            object_name = action.objectName()
            if object_name == "edit":
                object_name = "#41a7fa"
            elif object_name == "select":
                object_name = "#74d484"

            if object_name:
                tmp_color = QColor(object_name).lighter(140).name()
                if tmp_color != "#000000":
                    base_background_color = tmp_color
            action_widget.setStyleSheet(
                f"""QToolButton {{background: {base_background_color}; margin: 0 2; color:black}}
                    QToolButton:hover {{background: {hover_color}}}
                    QToolButton:disabled {{background: {disabled_background_color}}}
                    """
            )

    def set_context_menu(self, widget):
        widget.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
        widget.addActions(self.toolBarPanel.actions())

    def showEvent(self, ev):
        if not (self.show_main_button or self.show_actions):
            self.hide()
            return
        button_height = self.main_button.sizeHint().height()
        self.setFixedHeight(button_height + 1)
        for x in self.toolBarPanel.actions():
            action_widget = self.toolBarPanel.widgetForAction(x)
            if isinstance(action_widget, QToolButton):
                if action_widget.icon().availableSizes() == []:
                    font = action_widget.font()
                    font.setWeight(QFont.Weight.Medium)
                    action_widget.setFont(font)
                    action_widget.setFixedHeight(button_height)

        return super().showEvent(ev)
