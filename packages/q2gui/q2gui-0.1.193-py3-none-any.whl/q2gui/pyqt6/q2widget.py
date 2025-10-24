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


from decimal import Decimal
from PyQt6.QtWidgets import QWidget, QSizePolicy
from PyQt6.QtGui import QFontMetrics, QFont
from PyQt6.QtCore import Qt

from q2gui import q2widget
from q2gui.q2utils import int_
from q2gui.pyqt6.q2window import q2_align


class Q2Widget(QWidget, q2widget.Q2Widget):
    def __init__(self, meta={}):
        super().__init__()
        q2widget.Q2Widget.__init__(self, meta)
        if self.meta.get("margins"):
            self.apply_meta_margins()
        else:
            self.set_content_margins(0)
        if self.meta.get("tag"):
            self.setObjectName(self.meta.get("tag"))
        if self.meta.get("dblclick") and hasattr(self, "doubleClicked"):
            self.doubleClicked.connect(self.meta.get("dblclick"))
        if self.meta.get("changed"):
            if hasattr(self, "textChanged"):
                self.textChanged.connect(self.meta.get("changed"))
            elif hasattr(self, "valueChanged"):
                self.valueChanged.connect(self.meta.get("changed"))
            elif hasattr(self, "stateChanged"):
                self.stateChanged.connect(self.meta.get("changed"))

    def apply_meta_margins(self):
        meta_margins = self.meta.get("margins")
        if isinstance(meta_margins, (int, Decimal)):
            meta_margins = [meta_margins]
        if not isinstance(meta_margins, list):
            meta_margins = [0]
        if len(meta_margins) == 1:
            self.set_content_margins(int(meta_margins[0]))
        elif len(meta_margins) == 2:
            self.set_content_margins(int(meta_margins[0]), meta_margins[1])
        elif len(meta_margins) == 3:
            self.set_content_margins(int(meta_margins[0]), meta_margins[1], meta_margins[2])
        else:
            self.set_content_margins(int(meta_margins[0]), meta_margins[1], meta_margins[2], meta_margins[3])

    # def mouseDoubleClickEvent(self, event):
    #     if self.meta.get("dblclick"):
    #         self.meta.get("dblclick")()
    #     return super().mouseDoubleClickEvent(event)

    def set_tooltip(self, mess):
        self.setToolTip(mess)

    def set_disabled(self, arg=True):
        self.setEnabled(True if not arg else False)

    def set_enabled(self, arg=True):
        self.setEnabled(True if arg else False)

    def set_text(self, text):
        if hasattr(self, "setText"):
            self.setText(f"{text}")

    def get_text(self):
        if hasattr(self, "text"):
            return self.text()
        return ""

    def set_readonly(self, arg):
        if hasattr(self, "setReadOnly"):
            self.setReadOnly(True if arg else False)

    def is_enabled(self):
        return self.isEnabled()

    def set_visible(self, arg=True):
        self.setVisible(arg)

    def is_visible(self):
        if hasattr(self, "isVisible"):
            return self.isVisible()

    def is_readonly(self):
        if hasattr(self, "isReadOnly"):
            return self.isReadOnly()

    def set_font(self, font_name="", font_size=12):
        self.setFont(QFont(font_name, font_size))

    def set_focus(self):
        self.setFocus()

    def has_focus(self):
        return self.hasFocus()

    def _check_min_width(self, width):
        width = int_(width)
        return width if width > 5 else width + 2

    def set_maximum_width(self, width, char="W"):
        width = self._check_min_width(width)
        if self.meta.get("control", "") not in ("radio", "check"):
            if char != "":
                # self.setMaximumWidth(QFontMetrics(self.font()).width(char) * width)
                self.setMaximumWidth(int(QFontMetrics(self.font()).horizontalAdvance(char) * width))
            else:
                self.setMaximumWidth(int(width))

    def set_minimum_width(self, width, char="W"):
        width = self._check_min_width(width)
        if self.meta.get("control", "") not in ("radio", "check"):
            if char != "":
                self.setMinimumWidth(int(QFontMetrics(self.font()).horizontalAdvance(char) * width))
            else:
                self.setMinimumWidth(int(width))

    def set_fixed_width(self, width, char="W"):
        width = self._check_min_width(width)
        if self.meta.get("control", "") not in ("radio", "check"):
            if char != "":
                self.setFixedWidth(int(QFontMetrics(self.font()).horizontalAdvance(char) * width))
            else:
                self.setFixedWidth(int(width))

    def set_fixed_height(self, height=1, char="O"):
        if self.meta.get("control", "") not in ("radio", "check"):
            if char != "":
                self.setFixedHeight(int(QFontMetrics(self.font()).height() * height * 1.6))
            else:
                self.setFixedHeight(int(height))

    def set_maximum_len(self, length):
        if hasattr(self, "setMaxLength"):
            return self.setMaxLength(int(length))

    def set_alignment(self, alignment):
        if hasattr(self, "setAlignment"):
            self.setAlignment(q2_align[f"{alignment}"])

    # def valid(self):
    #     if self.meta.get("valid"):
    #         return self.meta.get("valid", lambda: True)()
    #     else:
    #         return True

    # def when(self):
    #     if self.meta.get("when"):
    #         return self.meta.get("when", lambda: True)()
    #     else:
    #         return True

    def set_style_sheet(self, css: str):
        super().set_style_sheet(css)
        self.setStyleSheet(self.style_sheet)

    def add_style_sheet(self, css: str):
        last_style = " ".join([self.styleSheet(), f"; {css}"])
        super().set_style_sheet(last_style)
        self.setStyleSheet(self.style_sheet)

    def get_style_sheet(self):
        return self.styleSheet()

    # def fix_default_height(self):
    #     self.set_maximum_height(self.get_default_height())

    def get_default_height(self):
        return self.sizeHint().height()

    def set_maximum_height(self, height):
        self.setMaximumHeight(int(height))

    # def fix_default_width(self):
    #     self.set_maximum_width(self.get_default_width())

    def get_default_width(self):
        return self.sizeHint().width()

    def set_size_policy(self, horizontal, vertical):
        sp = {
            "fixed": QSizePolicy.Policy.Fixed,
            "minimum": QSizePolicy.Policy.Minimum,
            "maximum": QSizePolicy.Policy.Maximum,
            "preffered": QSizePolicy.Policy.Preferred,
            "expanding": QSizePolicy.Policy.Expanding,
            "minimumexpanding": QSizePolicy.Policy.MinimumExpanding,
            "ignored": QSizePolicy.Policy.Ignored,
        }

        self.setSizePolicy(
            sp.get(horizontal, QSizePolicy.Policy.Minimum), sp.get(vertical, QSizePolicy.Policy.Minimum)
        )

    def can_get_focus(self):
        if self.focusPolicy() == Qt.FocusPolicy.NoFocus:
            return False
        else:
            return True

    def set_content_margins(self, top=0, right=None, bottom=None, left=None):
        if right is None:
            right = top
        if bottom is None:
            bottom = top
        if left is None:
            left = right
        self.setContentsMargins(top, right, bottom, left)

    def get_next_focus_widget(self, pos=1):
        return self.nextInFocusChain()

    def get_next_widget(self, pos=1):
        return self.layout().widget()

    def add_widget_above(self, widget, pos=0):
        my_pos = self.parentWidget().layout().indexOf(self)
        self.parent().layout().insertWidget(my_pos - pos, widget)

    def add_widget_below(self, widget, pos=0):
        if pos == -1:
            self.parent().layout().addWidget(widget)
        else:
            my_pos = self.parentWidget().layout().indexOf(self)
            self.parent().layout().insertWidget(my_pos + pos + 1, widget)

    def remove(self):
        self.parentWidget().layout().removeWidget(self)
        self.setParent(None)

    def get_layout_position(self):
        return self.parentWidget().layout().indexOf(self)

    def get_layout_count(self):
        return self.parentWidget().layout().count()

    def get_layout_widget(self, pos):
        return self.parentWidget().layout().itemAt(pos).widget()

    def get_layout_widgets(self):
        return [self.get_layout_widget(x) for x in range(self.get_layout_count())]

    def move_up(self):
        pos = self.get_layout_position()
        if pos > 0:
            w = self.parentWidget().layout().takeAt(pos).widget()
            self.parentWidget().layout().insertWidget(pos - 1, w)

    def move_down(self):
        pos = self.get_layout_position()
        if pos < self.get_layout_count() - 1:
            w = self.parentWidget().layout().takeAt(pos + 1).widget()
            self.parentWidget().layout().insertWidget(pos, w)

    def action_set_visible(self, text, mode=True):
        for action in self.actions():
            if action.text().strip() == text:
                action.setVisible(mode)

    def action_set_enabled(self, text, mode=True):
        for action in self.actions():
            if action.text().strip() == text:
                action.setVisible(mode)
