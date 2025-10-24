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


from threading import Thread, current_thread
import time
import json
from q2gui.q2form import Q2Form
import q2gui.q2app as q2app


def center_window(form: Q2Form):
    w, h = q2app.q2_app.get_size()
    h -= q2app.q2_app.get_stdout_height()

    form.form_stack[0].set_size(int(w * 0.5), int(h * 0.5))
    form.form_stack[0].set_position(int(w * 0.25), int(h * 0.15))


def q2Mess(mess="", title="Message", html=True):
    form = Q2Form(title)
    form.do_not_save_geometry = True
    form.add_control("/v")
    if isinstance(mess, dict) or isinstance(mess, list):
        mess = "<pre>" + json.dumps(mess, indent=2, ensure_ascii=False) + "</pre>"
    elif html is not True:
        mess = "<pre>" + mess + "</pre>"
    form.add_control("mess", control="text", data=f"{mess}", readonly=True)
    if form.add_control("/h"):
        form.add_control("/s")
        form.add_control(
            "_ok_button",
            "Ok",
            control="button",
            eat_enter=True,
            hotkey="PgDown",
            valid=form.close,
            tag="_ok_button",
        )

        form.add_control("/s")
        form.add_control("/")

    def after_form_show(form=form):
        center_window(form)
        form.w._ok_button.set_focus()

    form.after_form_show = after_form_show

    form.show_app_modal_form()
    q2app.q2_app.process_events()


q2_mess = q2mess = q2Mess


def q2AskYN(mess, title="Question", buttons=["Cancel", "Ok"]):
    form = Q2Form(title)
    form.do_not_save_geometry = True
    form.choice = 0
    form.add_control("/")

    form.controls.add_control("mess", control="text", data=f"{mess}", readonly="*", disabled="")

    if form.add_control("/h"):
        form.add_control("/s")

        def buttonPressed(form=form, answer=0):
            def worker():
                form.choice = answer
                form.close()

            return worker

        for index, x in enumerate(buttons):
            form.add_control(
                f"button_{index+1}",
                x,
                control="button",
                valid=buttonPressed(form, index + 1),
                eat_enter="*",
                tag="ok" if x == "Ok" else "",
            )
        form.add_control("/s")
        form.add_control("/")

    def after_form_show(form=form):
        center_window(form)
        form.w.button_1.set_focus()

    form.after_form_show = after_form_show
    form.show_app_modal_form()
    q2app.q2_app.process_events()
    return form.choice


q2_ask = q2ask = q2_ask_yn = q2askyn = q2AskYN


class Q2Thread(Thread):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._target = target
        self._args = args
        self.min = 0
        self.max = 0
        self.shadow_value = 0
        self.value = 0
        self._return = None
        self._exc = None
        self.start_time = time.time()

    @staticmethod
    def set_min(value):
        current_thread().min = value

    @staticmethod
    def set_max(value):
        current_thread().max = value

    @staticmethod
    def get_max():
        c_thread = current_thread()
        if hasattr(c_thread, "max"):
            return c_thread.max
        else:
            return 0

    @staticmethod
    def step(step_value=1):
        current_thread().shadow_value += 1
        sv = current_thread().shadow_value
        if sv % step_value == 0:
            current_thread().value = sv

    @staticmethod
    def get_current():
        return current_thread().value

    def time(self):
        return time.time() - self.start_time

    def run(self):
        try:
            self._return = self._target(*self._args)
        except Exception as e:
            self._exc = e


class Q2WaitForm:
    def __init__(self, mess, worker_thread):
        self.tick = {}
        self.worker_thread = worker_thread
        self.wait_window = Q2Form("Wait...")
        self.wait_window.do_not_save_geometry = True
        self.wait_window.add_control("", label=mess, control="label")
        # self.wait_window.add_control("label", label="", data=mess)
        steps_count_separator = ""
        if Q2Thread.get_max() != 0:
            steps_count_separator = "/"

        if self.wait_window.add_control("/h"):
            self.wait_window.add_control("progressbar", "", control="progressbar")
            self.wait_window.add_control("min", "", control="label")
            self.wait_window.add_control("", steps_count_separator, control="label")
            self.wait_window.add_control("value", "", control="label")
            self.wait_window.add_control("", steps_count_separator, control="label")
            self.wait_window.add_control("max", "", control="label")
            self.wait_window.add_control("time", "", control="label")
        self.wait_window.add_control("/")
        self.show()

        if self.worker_thread.min != 0:
            self.wait_window.w.progressbar.set_min(self.worker_thread.min)
            self.wait_window.s.min = self.worker_thread.min
        if self.worker_thread.max != 0:
            self.wait_window.w.progressbar.set_max(self.worker_thread.max)
            self.wait_window.s.max = self.worker_thread.max

    def step(self):
        if self.worker_thread.value != 0:
            self.wait_window.w.progressbar.set_value(self.worker_thread.value)
            self.wait_window.s.value = self.worker_thread.value

        thread_time = int(self.worker_thread.time())
        sec = thread_time % 60
        min = (thread_time - sec) % 3600
        hours = thread_time - min * 3600 - sec
        sec = int(sec)
        self.wait_window.s.time = f" Time {hours:02}:{min:02}:{sec:02}"
        q2app.q2_app.process_events()

    def show(self):
        self.wait_window.show_mdi_form()
        q2app.q2_app.process_events()
        w = q2app.q2_app.get_size()[0]
        fh = self.wait_window.form_stack[0].get_size()[1]
        self.wait_window.form_stack[0].set_size(int(w * 0.9), fh)
        left, top = self.wait_window.form_stack[0].center_pos()
        self.wait_window.form_stack[0].set_position(left, top)
        q2app.q2_app.process_events()

    def close(self):
        self.wait_window.close()
        q2app.q2_app.process_events()


def q2WaitStep(step_value=1):
    Q2Thread.step(step_value)


def q2WaitMax(max_value=0):
    Q2Thread.set_max(max_value)


def q2working(worker, mess=""):
    wait_window = None
    wait_window_on = False
    last_focus_widget = q2app.q2_app.focus_widget()
    last_progressbar_value = 0
    last_progressbar_time = 0
    q2app.q2_app.lock()
    worker_thread = Q2Thread(target=worker)
    worker_thread.start()
    while worker_thread.is_alive():
        time.sleep(0.3)
        if worker_thread.time() > 1 and wait_window_on is not True:
            wait_window_on = True
            wait_window = Q2WaitForm(mess, worker_thread)
        if wait_window_on is True:
            if worker_thread.min < worker_thread.max:
                if worker_thread.value != 0 and last_progressbar_value != worker_thread.value:
                    wait_window.step()
            elif worker_thread.time() - last_progressbar_time > 1:
                wait_window.step()
                last_progressbar_time = worker_thread.time()
        last_progressbar_value = worker_thread.value
        q2app.q2_app.process_events()
    q2app.q2_app.unlock()
    if wait_window is not None:
        wait_window.close()
    if hasattr(last_focus_widget, "set_focus"):
        last_focus_widget.set_focus()

    q2app.q2_app.show_statusbar_mess(f"{worker_thread.time():.2f}")
    if worker_thread._exc:
        raise worker_thread._exc
    return worker_thread._return


q2Wait = q2working


class Q2WaitShow:
    def __init__(self, *args):
        self.interrupted = False
        mess = "Working... \t"
        max_range = 0
        for x in args:
            x = str(x)
            if x.isdigit():
                max_range = int(x)
            else:
                mess = x
        self.mess = mess
        self.interval = 0.5 if max_range > 100 or max_range == 0 else 0

        self.i_am_first_wait = True
        self.window_size = None
        self.main_wait_widget = None
        self.widget_stack = []
        self.widget_height = []

        self.prev_q2_form = q2app.q2_app.get_current_q2_form()
        if self.prev_q2_form and self.prev_q2_form.name == "Wait...":
            self.i_am_first_wait = False

        self.wait_window = Q2Form("Wait...")
        self.wait_window.do_not_save_geometry = True
        self.wait_window.add_control("mess", label=self.mess, control="label", alignment=5)
        steps_count_separator = "⇒"

        self.wait_window.add_control("/")
        if self.wait_window.add_control("/h", tag="bar"):
            self.wait_window.add_control("progressbar", "", control="progressbar")
            self.wait_window.add_control("value", "", control="label")
            self.wait_window.add_control("", steps_count_separator, control="label")
            self.wait_window.add_control("max", "", control="label")
            self.wait_window.add_control("time", "", control="label")
        self.wait_window.add_control("/")
        # self.wait_window.add_control("/s")
        self.bar_count = 1

        self.show()
        self.start_time = time.time()
        self.last_time = time.time()

        self.value = -1
        self.step()
        self.wait_window.w.progressbar.set_min(self.value)
        self.wait_window.s.min = 0
        self.wait_window.w.progressbar.set_max(max_range)
        self.wait_window.s.max = max_range if max_range else "?"
        q2app.q2_app.process_events()
        self.last_focus_widget = q2app.q2_app.focus_widget()
        self.wait_window.after_form_closed = self.wait_windows_after_form_closed

    def wait_windows_after_form_closed(self):
        q2app.q2_app.disable_toolbar(False)
        q2app.q2_app.disable_menubar(False)
        q2app.q2_app.disable_tabbar(False)
        self.interrupted = True

    def step(self, *args):
        """ """
        if self.interrupted:
            return True
        text = ""
        for x in args:
            x = str(x)
            if x.isdigit():
                self.interval = int(x) / 1000
            else:
                text = x

        self.value += 1
        if self.wait_window.w.progressbar:
            if self.interval and (time.time() - self.last_time) < self.interval:
                return
            else:
                self.last_time = time.time()

            self.wait_window.w.progressbar.set_value(self.value)
            self.wait_window.s.value = self.value
            self.wait_window.s.mess = f"{self.mess}{text}"

            thread_time = int(time.time() - self.start_time)
            sec = thread_time % 60
            min = int((thread_time - sec) / 60)
            sec = int(sec)
            self.wait_window.s.time = f" {min}:{sec:02}"

            q2app.q2_app.process_events()
        else:
            q2app.q2_app.process_events()

    def show(self):
        if self.i_am_first_wait:
            q2app.q2_app.disable_toolbar(True)
            q2app.q2_app.disable_menubar(True)
            q2app.q2_app.disable_tabbar(True)
            q2app.q2_app.disable_current_form()
            self.wait_window.show_mdi_form()
            q2app.q2_app.process_events()
            w = q2app.q2_app.get_size()[0]
            self.main_wait_widget = self.wait_window.form_stack[-1]
            h = self.main_wait_widget.get_size()[1]
            self.main_wait_widget.set_size(int(w * 0.9), h)

            left, top = self.main_wait_widget.center_pos()
            self.main_wait_widget.set_position(left, top)

            q2app.q2_app.process_events()
            self.window_size = self.main_wait_widget.get_size()
            self.main_wait_widget.heap.q2wait = self
            self.main_wait_widget.heap.q2wait.widget_stack.append(self.wait_window.w.bar)
            self.main_wait_widget.heap.q2wait.widget_height.append(self.window_size[1])
        else:
            self.main_wait_widget = self.prev_q2_form.form_stack[-1]

            self.wait_window.form_stack.append(self.wait_window.get_form_widget())
            self.main_wait_widget.heap.q2wait.widget_stack[-1].add_widget_below(
                self.wait_window.form_stack[-1]
            )
            q2app.q2_app.process_events()

            self.main_wait_widget.heap.q2wait.widget_stack.append(self.wait_window.form_stack[-1])
            self.main_wait_widget.heap.q2wait.widget_height.append(
                self.wait_window.form_stack[-1].sizeHint().height()
            )
            self.main_wait_widget.set_size(
                self.main_wait_widget.heap.q2wait.window_size[0],
                sum(self.main_wait_widget.heap.q2wait.widget_height),
            )
        q2app.q2_app.process_events()

    def close(self):
        if self.i_am_first_wait:
            if not self.interrupted:
                self.wait_window.close()
                q2app.q2_app.disable_current_form(False)
                if hasattr(self.last_focus_widget, "set_focus"):
                    self.last_focus_widget.set_focus()
            q2app.q2_app.disable_toolbar(False)
            q2app.q2_app.disable_menubar(False)
            q2app.q2_app.disable_tabbar(False)
        else:
            self.wait_window.form_stack[-1].remove()
            self.main_wait_widget.heap.q2wait.widget_stack.pop()
            self.main_wait_widget.heap.q2wait.widget_height.pop()
            q2app.q2_app.process_events()

        q2app.q2_app.process_events()
        return self.value, time.time() - self.start_time


q2_wait_show = q2waitshow = q2wait = q2_wait = Q2WaitShow
