import importlib.util
import os
import shutil
import subprocess
import sys
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import filedialog, ttk

import ttkthemes

from . import file_loader, gui_canvas, gui_tree, icon_data, svg_writer, time_format
from .gui_parts import Combobox

IS_DARWIN = sys.platform.startswith("darwin")


class App(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        master.title("Timeline-kun")

        head_frame = ttk.Frame(master)
        head_frame.pack(padx=10, pady=(15, 5), fill=tk.X)
        create_file_btn = ttk.Button(
            head_frame, text="Create CSV", width=13, command=self.create_file
        )
        create_file_btn.pack(padx=5, side=tk.LEFT)
        load_file_btn = ttk.Button(
            head_frame, text="Load CSV", width=13, command=self.select_file
        )
        load_file_btn.pack(padx=5, side=tk.LEFT)
        self.file_path_label = ttk.Label(head_frame, text="No file selected")
        self.file_path_label.pack(padx=5, side=tk.LEFT)

        self.timer_btn = ttk.Button(
            head_frame, text="Send to timer", command=self.open_timer
        )
        self.timer_btn.pack(padx=5, side=tk.RIGHT)
        self.timer_btn["state"] = "disabled"

        values = ["orange", "cyan", "lightgreen"]
        self.timer_color_combobox = Combobox(head_frame, "Color:", values, width=12)
        self.timer_color_combobox.pack_horizontal(padx=5, side=tk.RIGHT)

        send_timer_frame = ttk.Frame(master)
        send_timer_frame.pack(padx=10, pady=(5, 10), fill=tk.X)

        excel_btn = ttk.Button(
            send_timer_frame, text="Send to Excel", width=13, command=self.open_excel
        )
        excel_btn.pack(padx=5, side=tk.LEFT)
        reload_btn = ttk.Button(send_timer_frame, text="Reload", command=self.load_file)
        reload_btn.pack(padx=5, side=tk.LEFT)

        values = ["mm:ss", "h:mm:ss"]
        self.time_format_combobox = Combobox(
            send_timer_frame, "Format", values, width=10
        )
        self.time_format_combobox.pack_horizontal(padx=(70, 5), side=tk.LEFT)
        self.time_format_combobox.set_selected_bind(lambda e: self.draw_stages())

        values = ["tiny", "small", "normal"]
        self.font_size_combobox = Combobox(
            send_timer_frame, "Font size", values, width=10, current=1
        )
        self.font_size_combobox.pack_horizontal(padx=5, side=tk.LEFT, anchor=tk.E)
        self.font_size_combobox.set_selected_bind(lambda e: self.draw_stages())

        values = ["vertical", "horizontal"]
        self.direction_combobox = Combobox(
            send_timer_frame, "Direction", values, width=10
        )
        self.direction_combobox.pack_horizontal(padx=5, side=tk.LEFT, anchor=tk.E)
        self.direction_combobox.set_selected_bind(lambda e: self.draw_stages())

        export_svg_btn = ttk.Button(
            send_timer_frame, text="Export SVG", command=self.export_svg
        )
        export_svg_btn.pack(padx=5, side=tk.LEFT)

        # error message frame
        msg_frame = ttk.Frame(send_timer_frame)
        msg_frame.pack(padx=10, fill=tk.X, side=tk.LEFT)
        self.msg_label = ttk.Label(msg_frame, text="")
        self.msg_label.pack()

        # body frame
        body_frame = ttk.Frame(master)
        body_frame.pack(fill=tk.BOTH, expand=True)
        # tree
        tree_frame = ttk.Frame(body_frame, width=400)
        tree_frame.pack(side=tk.LEFT, fill=tk.Y)
        cols = [
            {"name": "title", "width": 200},
            {"name": "member", "width": 100},
            {"name": "start", "width": 50},
            {"name": "end", "width": 50},
            {"name": "duration", "width": 50},
            {"name": "fixed", "width": 60},
            {"name": "instruction", "width": 200},
        ]
        self.tree = gui_tree.Tree(tree_frame, columns=cols)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.tree.bind("<<TreeviewSelect>>", lambda e: self.select_row())
        self.tree.add_menu("Set start point", self.draw_start_line)
        self.tree.add_menu("Insert", self.insert_row)
        self.tree.add_menu("Edit", self.edit_row)
        self.tree.add_menu("Remove", self.remove_row)
        # canvas
        canvas_frame = ttk.Frame(body_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        self.canvas = gui_canvas.Canvas(canvas_frame, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # ctrl+z shortcut control
        master.bind("<Control-z>", self.undo)

        self.csv_path = None
        self.start_index = 0
        self.prev_end_time_sec = None
        self.next_start_time_sec = None

    def edit_row(self):
        if self._check_csv_file_locked(self.csv_path) is True:
            return

        is_ok = self.tree.edit(self.prev_end_time_sec)
        if is_ok:
            self.tree.tree_to_csv_file(self.csv_path)
            self.load_file()

    def insert_row(self):
        if self._check_csv_file_locked(self.csv_path) is True:
            return
        is_ok = self.tree.insert()
        if is_ok:
            self.tree.tree_to_csv_file(self.csv_path)
            self.load_file()

    def remove_row(self):
        if self._check_csv_file_locked(self.csv_path) is True:
            return
        # confirm remove
        current_row = self.tree.get_selected_index()
        if current_row is None:
            return
        current_title = self.stage_list[current_row]["title"]
        is_ok = tk.messagebox.askyesno(
            "Confirm",
            f"Do you want to remove the row ({current_title})?.",
        )
        if is_ok is False:
            return
        is_ok = self.tree.remove()

        if is_ok:
            self.tree.tree_to_csv_file(self.csv_path)
            self.load_file()

    def _check_csv_file_locked(self, file_path):
        if self.tree.check_csv_file_locked(self.csv_path) is True:
            tk.messagebox.showinfo(
                "Info",
                f"The file is currently locked by another application, such as Excel.\n{self.csv_path}",
            )
            return True
        return False

    def select_row(self):
        idx = self.tree.get_selected_index()
        if idx is None:
            return
        prev_fixed_code, next_fixed_code = self._get_prev_next_fixed_code(idx)

        # preview event
        if prev_fixed_code is None:
            self.prev_end_time_sec = self._get_prev_start_time(idx)
        elif prev_fixed_code == "start":
            prev_end_sec = self.stage_list[idx - 1]["end_sec"]
            prev_duration_sec = self.stage_list[idx - 1]["duration_sec"]
            # end_sec and duration_sec are 0 -> prevprev
            if prev_end_sec == "0" and prev_duration_sec == "0":
                self.prev_end_time_sec = self._get_prev_start_time(idx) + 1
            else:
                self.prev_end_time_sec = self._get_prev_end_time(idx)
        elif prev_fixed_code == "duration":
            self.prev_end_time_sec = self._get_prev_end_time(idx)

        # next event
        if next_fixed_code == "start":
            self.next_start_time_sec = self._get_next_start_time(idx)
        elif next_fixed_code == "duration":
            self.next_start_time_sec = self._get_next_end_time(idx) - 1
        elif next_fixed_code is None:
            self.next_start_time_sec = self._get_next_end_time(idx)

        self.highlight_selected_row()

    def draw_start_line(self):
        self.start_index = self.tree.get_selected_index()
        if self.start_index is None:
            self.start_index = 0

        stage = self.stage_list[self.start_index]
        total_duration = self.stage_list[-1]["end_dt"].total_seconds()
        self.canvas.draw_start_line(stage["start_dt"], total_duration)

        for s in self.stage_list:
            caption = self._minus_timedelta(s["start_dt"], stage["start_dt"])
            self.canvas.create_time(s["start_dt"], text=caption)
        total_end_dt = self.stage_list[-1]["end_dt"]
        time_caption = self._minus_timedelta(total_end_dt, stage["start_dt"])
        self.canvas.create_time(total_end_dt, text=time_caption)

    def highlight_selected_row(self):
        idx = self.tree.get_selected_index()
        if idx is None:
            return
        start = self.stage_list[idx]["start_dt"]
        duration = self.stage_list[idx]["duration"]
        self.canvas.delete("highlight")
        self.canvas.create_rect(start, duration, "#dd7777", tag="highlight")

    def _get_prev_next_fixed_code(self, index):
        if index == 0:
            prev_fixed_code = None
        else:
            prev_fixed_code = self.stage_list[index - 1]["fixed"]
        if index == len(self.stage_list) - 1:
            next_fixed_code = None
        else:
            next_fixed_code = self.stage_list[index + 1]["fixed"]
        return prev_fixed_code, next_fixed_code

    def _get_prev_end_time(self, index):
        if index <= 0:
            return 0
        else:
            return self.stage_list[index - 1]["end_dt"].total_seconds()

    def _get_prev_start_time(self, index):
        if index <= 0:
            return 0
        else:
            return self.stage_list[index - 1]["start_dt"].total_seconds()

    def _get_next_start_time(self, index):
        if index >= len(self.stage_list) - 1:
            return 1000000
        else:
            return self.stage_list[index + 1]["start_dt"].total_seconds()

    def _get_next_end_time(self, index):
        if index >= len(self.stage_list) - 1:
            return 1000000
        else:
            return self.stage_list[index + 1]["end_dt"].total_seconds()

    def _minus_timedelta(self, td_1, td_2):
        include_hour = self.time_format_combobox.get() == "h:mm:ss"
        if td_1 < td_2:
            total_seconds = td_2 - td_1
            return f"-{time_format.timedelta_to_str(total_seconds, include_hour)}"
        else:
            total_seconds = td_1 - td_2
            return time_format.timedelta_to_str(total_seconds, include_hour)

    def draw_stages(self):
        self.canvas.delete("all")
        self.canvas.set_font(self.font_size_combobox.get())
        self.canvas.set_direction(self.direction_combobox.get())
        total_duration = self.stage_list[-1]["end_dt"].total_seconds()
        self.canvas.set_scale(total_duration)

        past_rect_height = 10000
        include_hour = self.time_format_combobox.get() == "h:mm:ss"

        past_start_dt = timedelta(seconds=0)
        for stage in self.stage_list:
            if stage["start_dt"].total_seconds() == 0:
                start_dt = past_start_dt
            else:
                start_dt = stage["start_dt"]
            rect_height = self.canvas.create_rect(
                start_dt, stage["duration"], stage["color"]
            )
            label_title = f"{stage['title']}"
            label_time = (
                f"{time_format.timedelta_to_str(stage['duration'], include_hour)}"
            )
            self.canvas.create_label(
                start_dt, stage["duration"], label_title, label_time, stage["has_error"]
            )
            if past_rect_height > 10:
                time_caption = time_format.timedelta_to_str(start_dt, include_hour)
                self.canvas.create_time(stage["start_dt"], text=time_caption)
            past_start_dt = stage["start_dt"]
            past_rect_height = rect_height
        time_caption = time_format.timedelta_to_str(
            self.stage_list[-1]["end_dt"], include_hour
        )
        self.canvas.create_time(self.stage_list[-1]["end_dt"], text=time_caption)

    def create_file(self):
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        dir_path = filedialog.askdirectory(initialdir=desktop_path)
        if not dir_path:
            return
        today = datetime.now().strftime("%Y-%m-%d")
        file_path = os.path.join(dir_path, f"{today}_new.csv")
        if os.path.exists(file_path):
            tk.messagebox.showinfo("Info", "File already exists.")
            return
        with open(file_path, "w") as f:
            f.write("title,member,start,duration,fixed,instruction\n")
            f.write("TASK A,MEMBER1,,0:01:00,duration,The first task.\n")
            f.write("TASK B,MEMBER1,0:01:10,0:01:30,start,The second task.\n")
            f.write("TASK C,MEMBER1,,0:01:00,duration,The third task.\n")
            f.write("TASK D,MEMBER1,,0:01:00,duration,The 4th task.\n")
            f.write("TASK E,MEMBER1,0:05:00,0:01:00,start,The final task.\n")

        self.csv_path = file_path
        self.load_file()

    def select_file(self):
        self.msg_label.config(text="")
        csv_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not csv_path:
            return
        self.csv_path = csv_path
        self.load_file()

    def load_file(self):
        self.start_index = 0
        self.file_path_label.config(text=self.csv_path)

        fl = file_loader.FileLoader()
        try:
            warn_msg, timetable = fl.load_file_for_preview(self.csv_path)
        except Exception as e:
            self.timer_btn["state"] = "disabled"
            self.msg_label.config(text=f"[ERROR]{e}")
            return

        self.stage_list = []
        for row in timetable.get_timetable():
            self.stage_list.append(
                {
                    "title": row["title"],
                    "member": row["member"],
                    "start_dt": row["start"],
                    "end_dt": row["end"],
                    "duration": row["end"] - row["start"],
                    "start_sec": row["start_sec"],
                    "end_sec": row["end_sec"],
                    "duration_sec": row["duration_sec"],
                    "fixed": row["fixed"],
                    "instruction": row["instruction"],
                    "has_error": row["has_error"],
                }
            )
        self.asign_rect_color()
        self.tree.set_stages(self.stage_list)
        self.draw_stages()

        if warn_msg != "":
            self.msg_label.config(text=f"[ERROR]{warn_msg}")
            self.timer_btn["state"] = "disabled"
        else:
            self.msg_label.config(text="Successfully loaded.")
            self.timer_btn["state"] = "normal"

        self.csv_encoding = fl.get_encoding()
        if self.csv_encoding is not None:
            self.tree.set_write_encoding(self.csv_encoding)

    def asign_rect_color(self):
        title_list = list(set([s["title"] for s in self.stage_list]))
        title_list.sort()
        for i, title in enumerate(title_list):
            for stage in self.stage_list:
                if stage["title"] == title:
                    if i >= len(gui_canvas.rect_colors):
                        stage["color"] = "#aaaaaa"
                    else:
                        stage["color"] = gui_canvas.rect_colors[i]

    def open_timer(self):
        # has_error check
        has_error_list = [s["has_error"] for s in self.stage_list]
        if True in has_error_list:
            tk.messagebox.showinfo("Error", "Timer can't start because of error.")
            return

        if self.time_format_combobox.get() == "h:mm:ss":
            hmmss = "hmmss"
        else:
            hmmss = "mmss"

        # frozen exe
        if getattr(sys, "frozen", False):
            current_dir = os.path.dirname(sys.executable)
            tar_path = os.path.join(current_dir, "TimelinekunTimer.exe")
            color = self.timer_color_combobox.get()

            subprocess.Popen(
                [
                    tar_path,
                    "--file_path",
                    self.csv_path,
                    "--fg_color",
                    color,
                    "--start_index",
                    str(self.start_index),
                    "--hmmss",
                    hmmss,
                ]
            )
        elif (
            importlib.util.find_spec(
                f"{__package__}.app_timer" if __package__ else "app_timer"
            )
            is not None
        ):
            color = self.timer_color_combobox.get()
            module = f"{__package__}.app_timer" if __package__ else "app_timer"
            subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    module,
                    "--file_path",
                    self.csv_path,
                    "--fg_color",
                    color,
                    "--start_index",
                    str(self.start_index),
                    "--hmmss",
                    hmmss,
                ]
            )

    def open_excel(self):
        is_sjis = file_loader.utf8_to_sjis(self.csv_path)
        if is_sjis:
            self.csv_encoding = "shift-jis"
        if IS_DARWIN:
            os.system(f"open -a /Applications/Microsoft/ Excel.app {self.csv_path}")
        else:
            os.system(f'start excel "{self.csv_path}"')

    def export_svg(self):
        init_file_name = os.path.basename(self.csv_path).split(".")[0]
        file_path = filedialog.asksaveasfilename(
            filetypes=[("SVG files", "*.svg")],
            defaultextension=".svg",
            initialfile=init_file_name,
        )
        if not file_path:
            return

        svg_writer.save_as_svg(self.canvas, file_path)

    def undo(self, event):
        backup_dir = "backup"
        # move file backup to tar_path
        backup_file = os.path.join(backup_dir, os.path.basename(self.csv_path))
        if os.path.exists(backup_file):
            shutil.move(backup_file, self.csv_path)
            self.load_file()


def quit(root):
    root.quit()
    root.destroy()


def main():
    bg_color = "#e8e8e8"
    root = ttkthemes.ThemedTk(theme="breeze")
    root.geometry("1400x700+50+50")
    root.configure(background=bg_color)
    root.option_add("*background", bg_color)
    root.option_add("*Canvas.background", bg_color)
    root.option_add("*Text.background", "#fcfcfc")
    root.tk.call("wm", "iconphoto", root._w, tk.PhotoImage(data=icon_data.icon_data))
    s = ttk.Style(root)
    s.configure(".", background=bg_color)
    app = App(root)
    root.protocol("WM_DELETE_WINDOW", lambda: quit(root))
    app.mainloop()


if __name__ == "__main__":
    main()
