import tkinter as tk
from tkinter import ttk
import json
import os

class SyslogFilter(tk.Tk):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        self.title("Фильтр")
        self.geometry("590x320")
        self.resizable(False, False)

        self.init_ui()
        self.load_settings()

    def save_settings(self):
        settings = {
            "priority_vars": [var.get() for var in self.priority_vars],
            "facility_vars": [var.get() for var in self.facility_vars],
            "custom_text": self.custom_text_entry.get()
        }
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, 'settings.json')
        with open(file_path, "w") as f:
            json.dump(settings, f)

    def load_settings(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, 'settings.json')
        try:
            with open(file_path, "r") as f:
                settings = json.load(f)

                for var, value in zip(self.priority_vars, settings["priority_vars"]):
                    var.set(value)
                for var, value in zip(self.facility_vars, settings["facility_vars"]):
                    var.set(value)
                self.custom_text_entry.insert(0, settings["custom_text"])
        except FileNotFoundError:
                # Если файл настроек не найден, используйте значения по умолчанию или оставьте флаги пустыми
            pass

    def init_ui(self):
        main_frame = ttk.Frame(self)

        main_frame.pack(fill=tk.BOTH, expand=True)

        # Frame for priority checkboxes
        priority_frame = ttk.LabelFrame(main_frame, text="Важность")
#        priority_frame.pack(side=tk.LEFT, padx=5, pady=5)
        priority_frame.grid(row=0, column=0, columnspan=1, padx=5, pady=5, sticky="nsew")
        self.init_priority_checkboxes(priority_frame)

        # Frame for select/deselect all priority checkboxes
        priority_control_frame = ttk.Frame(main_frame)
#        priority_control_frame.pack(side=tk.LEFT, padx=5, pady=5)
        priority_control_frame.grid(row=0, column=1, columnspan=1, padx=5, pady=5, sticky="w")
        self.init_priority_control_buttons(priority_control_frame)

        # Frame for facility checkboxes
        facility_frame = ttk.LabelFrame(main_frame, text="Категория")
#        facility_frame.pack(side=tk.LEFT, padx=5, pady=5)
        facility_frame.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
        self.init_facility_checkboxes(facility_frame)

        # Frame for select/deselect all facility checkboxes
        facility_control_frame = ttk.Frame(main_frame)
#        facility_control_frame.pack(side=tk.LEFT, padx=5, pady=5)
        facility_control_frame.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        self.init_facility_control_buttons(facility_control_frame)

        custom_text_container = ttk.Frame(main_frame)
        custom_text_container.grid(row=1, column=0, columnspan=4, padx=5, pady=5, sticky="ew")
        custom_text_container.columnconfigure(0, weight=1)

        entry_label = ttk.Label(custom_text_container, text="Текст содержит (И=&, ИЛИ=|, НЕТ=~):")
        entry_label.pack(side="top", fill="x")

        custom_text_frame = ttk.Frame(custom_text_container)
        custom_text_frame.pack(fill=tk.X, expand=True)

#        custom_text_frame.grid(row=1, column=0, columnspan=1, padx=5, pady=5, sticky="ew")
        self.custom_text_entry = ttk.Entry(custom_text_frame, width=50)
        self.custom_text_entry.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)

        panel_knopok = ttk.Frame(self)
        panel_knopok.pack(side="bottom", fill="x")

        left = ttk.Frame(panel_knopok)
        left.pack(side="left")

        right = ttk.Frame(panel_knopok)
        right.pack(side="left")

#        ttk.Label(panel_knopok).pack(side=tk.LEFT, fill='both', expand=True)
        # Buttons
        ok_button = ttk.Button(left, text="OK", command=self.ok_click)
        ok_button.pack(side="left", padx=110, pady=5)

        exit_button = ttk.Button(right, text="Отмена", command=self.quit)
        exit_button.pack(side="left", padx=0, pady=5)


    def init_priority_checkboxes(self, parent):
        priority_values = ["Emergency", "Alert", "Critical", "Error", "Warning", "Notice", "Informational", "Debug"]
        self.priority_vars = []
        for value in priority_values:
            var = tk.BooleanVar()
            self.priority_vars.append(var)
            ttk.Checkbutton(parent, text=value, variable=var).pack(anchor=tk.W)

    def init_priority_control_buttons(self, parent):
        select_all_var = tk.BooleanVar()

        select_all_cb = ttk.Checkbutton(parent, text="Все", variable=select_all_var, command=lambda: self.select_all(self.priority_vars, select_all_var))
        select_all_cb.pack(anchor=tk.W)

        deselect_all_var = tk.BooleanVar()
        deselect_all_cb = ttk.Checkbutton(parent, text="X", variable=deselect_all_var, command=lambda: self.deselect_all(self.priority_vars))
        deselect_all_cb.pack(anchor=tk.W)

    def init_facility_checkboxes(self, parent):
        facility_values = [
            "Kernel", "User", "Mail", "Daemon", "Auth", "Syslog", "LPR", "News", "UUCP", "Cron",
            "Authpriv", "FTP", "NTP", "Log Audit", "Log Alert", "Clock Daemon", "Local0", "Local1",
            "Local2", "Local3", "Local4", "Local5", "Local6", "Local7"
        ]

        rows = 9
        cols = 3
        self.facility_vars = []
        for i in range(rows):
            for j in range(cols):
                index = i * cols + j
                if index < len(facility_values):
                    value = facility_values[index]
                    var = tk.BooleanVar()
                    self.facility_vars.append(var)
                    ttk.Checkbutton(parent, text=value, variable=var).grid(row=i, column=j, sticky="w")

    def init_facility_control_buttons(self, parent):
        select_all_var = tk.BooleanVar()
        select_all_cb = ttk.Checkbutton(parent, text="Все", variable=select_all_var, command=lambda: self.select_all(self.facility_vars, select_all_var))
        select_all_cb.pack(anchor=tk.W)

        deselect_all_var = tk.BooleanVar()
        deselect_all_cb = ttk.Checkbutton(parent, text="X", variable=deselect_all_var, command=lambda: self.deselect_all(self.facility_vars))
        deselect_all_cb.pack(anchor=tk.W)

    def select_all(self, vars_list, select_all_var):
        select_all_state = select_all_var.get()
        if select_all_state:
            for var in vars_list:
                var.set(select_all_state)
        else:
            for var in vars_list:
                if not var.get():
                    var.set(True)

    def deselect_all(self, vars_list):
        for var in vars_list:
            var.set(False)

    def ok_click(self):
        facility_values = [
            "Kernel", "User", "Mail", "Daemon", "Auth", "Syslog", "LPR", "News", "UUCP", "Cron",
            "Authpriv", "FTP", "NTP", "Log Audit", "Log Alert", "Clock Daemon", "Local0", "Local1",
            "Local2", "Local3", "Local4", "Local5", "Local6", "Local7"
        ]
        priority_values = ["Emergency", "Alert", "Critical", "Error", "Warning", "Notice", "Informational", "Debug"]

        selected_priorities = [value for value, var in zip(priority_values, self.priority_vars) if var.get()]
        selected_facilities = [value for value, var in zip(facility_values, self.facility_vars) if var.get()]
        print(selected_facilities, selected_priorities)
        custom_text = self.custom_text_entry.get()
        if self.callback:
            self.callback(selected_priorities, selected_facilities, custom_text)
        self.save_settings()
        self.quit()

if __name__ == "__main__":

    app = SyslogFilter(None)
    app.mainloop()