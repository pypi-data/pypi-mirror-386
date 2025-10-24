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


from PyQt6.QtWidgets import QGroupBox, QSplitter
from PyQt6.QtCore import Qt
from PyQt6.QtCore import QSize


from q2gui.pyqt6.q2window import Q2Frame
from q2gui.pyqt6.q2widget import Q2Widget
from q2gui.q2utils import int_


class q2frame(QGroupBox, Q2Widget, Q2Frame):
    def __init__(self, meta):
        super().__init__(meta)
        Q2Frame.__init__(self, meta.get("column", "/v")[1])
        self.meta = meta
        self.splitter = None
        self.scroller = None
        if meta.get("column", "")[2:3] == "s":  # Splitter!
            self.splitter = q2splitter()
            if meta.get("column").startswith("/v"):
                self.splitter.setOrientation(Qt.Orientation.Vertical)
            self.layout().addWidget(self.splitter)
        if meta.get("label") not in ("", "-") and not meta.get("check"):
            self.set_title(meta.get("label"))
            self.setObjectName("title")
        if meta.get("label", "") == "":
            self.hide_border()
        elif meta.get("label", "") == "-":
            self.setStyleSheet("QGroupBox {border:1px solid lightgray}")

    def hide_border(self):
        self.setObjectName("grb")
        self.set_title("")
        self.add_style_sheet(" QGroupBox#grb {border:0} ")

    def set_title(self, title):
        self.setTitle(title)

    def can_get_focus(self):
        return False

    def get_widget_count(self):
        return self.layout().count()

    def add_widget(self, widget=None, label=None):
        if self.splitter is not None:
            self.splitter.addWidget(widget)
            if hasattr(widget, "meta"):
                self.splitter.setStretchFactor(self.splitter.count() - 1, int_(widget.meta.get("stretch", 0)))
        else:
            return super().add_widget(widget=widget, label=label)


class q2splitter(QSplitter):
    def __init__(self):
        super().__init__()
        # self.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding))

    def get_sizes(self):
        return ",".join([f"{x}" for x in self.sizes()])

    def set_sizes(self, sizes):
        if sizes == "":
            init_sizes = [int_(self.widget(x).meta.get("stretch", 1)) for x in range(self.count())]
            init_sizes = [x if x > 0 else 1 for x in init_sizes]
            if sum(init_sizes):
                widget_size = (
                    self.width() if self.orientation() is Qt.Orientation.Horizontal else self.height()
                )
                init_sizes = [str(int(x * widget_size / sum(init_sizes))) for x in init_sizes]
                for x in range(self.count()):
                    widgget = self.widget(x)
                    if widgget.meta.get("control") == "toolbar":
                        init_sizes[x] = str(widgget.sizeHint().height())
                sizes = ",".join(init_sizes)
        if sizes:
            sizes = [int(x) for x in sizes.split(",")]
            self.setSizes(sizes)

    def showEvent(self, ev):
        self.updateGeometry()
        return super().showEvent(ev)

    def sizeHint(self):
        if self.isVisible():
            return QSize(99999, 99999)
        else:
            return super().sizeHint()
