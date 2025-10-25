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


from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QFormLayout,
    QGridLayout,
    QApplication,
    QWIDGETSIZE_MAX,
)
from PyQt6.QtCore import Qt
from q2gui import q2window


q2_align = {
    "": Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
    "-1": Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
    "0": Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
    "1": Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom,
    "2": Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom,
    "3": Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom,
    "4": Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
    "5": Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
    "6": Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
    "7": Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
    "8": Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
    "9": Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop,
}


def layout(arg="h"):
    if arg.lower().startswith("v"):
        layout = QVBoxLayout()
        layout.setAlignment(q2_align["7"])
    elif arg.lower().startswith("f"):
        layout = QFormLayout()
        layout.setLabelAlignment(q2_align["6"])
        layout.setFormAlignment(q2_align["0"])
        layout.setFieldGrowthPolicy(layout.FieldGrowthPolicy.ExpandingFieldsGrow)
    elif arg.lower().startswith("g"):
        layout = QGridLayout()
    else:
        layout = QHBoxLayout()
        layout.setAlignment(q2_align["7"])
    layout.layout().setSpacing(3)
    layout.layout().setContentsMargins(0, 0, 0, 0)
    return layout


class Q2Frame(q2window.Q2Frame):
    def __init__(self, mode="v"):
        super().__init__(mode)
        self.setMaximumWidth(QWIDGETSIZE_MAX)
        self.setMaximumHeight(QWIDGETSIZE_MAX)

    def set_mode(self, mode="v"):
        self.splitter = None
        super().set_mode(mode=mode)
        if self.layout() is not None:
            return
        self.setLayout(layout(mode))

    def insert_widget(self, pos=None, widget=None):
        # if widget:
        #     # widget.setContentsMargins(0,20, 0, 0)
        #     if widget.label:
        #         print("--",widget, widget.label.get_text())
        if hasattr(widget, "meta"):
            stretch_factor = int(widget.meta.get("stretch", 0))
        else:
            stretch_factor = 0
        self.layout().addWidget(widget, stretch=stretch_factor)
        self.updateGeometry()

    def add_row(self, label=None, widget=None):
        # if widget:
        #     widget.setContentsMargins(0, 0, 0, 0)
        #     print("f", widget, widget.label.get_text())
        self.layout().addRow(label, widget)
        self.updateGeometry()


class Q2QtWindow(q2window.Q2Window, Q2Frame):
    def __init__(self, title=""):
        super().__init__()
        self.set_title(title)

    def set_position(self, left, top):
        if left == -9999 and top == -9999:
            self.center_position()
        else:
            self.move(int(left), int(top))

    def center_position(self):
        # sw, sh = (Q_DesktopWidget().size().width(), Q_DesktopWidget().size().height())
        screen = QApplication.screens()[0]

        sw, sh = (screen.size().width(), screen.size().height())

        ww, wh = self.get_size()

        left = int((sw - ww) / 2)
        top = int((sh - wh) / 2)
        self.move(left, top)

    def set_size(self, width, height):
        self.resize(int(width), int(height))

    def get_position(self):
        return (self.pos().x(), self.pos().y())

    def get_size(self):
        if hasattr(self, "parent") and self.parent() is not None:
            return (self.parent().size().width(), self.parent().size().height())
        else:
            return (self.size().width(), self.size().height())

    def set_disabled(self, arg=True):
        self.setEnabled(True if not arg else False)

    def set_enabled(self, arg=True):
        self.setEnabled(True if arg else False)

    def set_title(self, title):
        super().set_title(title)
        QWidget.setWindowTitle(self, title)

    def hide_border(self):
        super().hide_border()
        self.setObjectName("grb")
        # self.setStyleSheet("QGroupBox#grb {border:0}")
        self.parent().setWindowFlags(Qt.WindowType.CustomizeWindowHint | Qt.WindowType.FramelessWindowHint)

    def is_maximized(self):
        return 1 if QWidget.isMaximized(self) else 0

    def show_maximized(self):
        QWidget.showMaximized(self)
