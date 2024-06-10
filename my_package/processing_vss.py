import json
import tkinter as tk
from tkinter import ttk
from tkinter import colorchooser
from tkinter import filedialog
import os
import pygame
from pygame import mixer

class HighlightingSettings(tk.Tk):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Настройка реагирования")
        self.geometry("1070x420")
        self.resizable(False, False)

        self.color_mapping = {}

        self.facility_values = ["Все", "Kernel", "User", "Mail", "Daemon", "Auth", "Syslog", "LPR", "News", "UUCP", "Cron", "Authpriv", "FTP", "NTP", "Log Audit", "Log Alert", "Clock Daemon", "Local0", "Local1", "Local2", "Local3", "Local4", "Local5", "Local6", "Local7"]
        self.severity_values = ["Все", "Emergency", "Alert", "Critical", "Error", "Warning", "Notice", "Informational", "Debug"]

        self.create_widgets()
        self.allow_alert_var.set(True)
        self.load_color_mapping()

    def create_widgets(self):
        input_frame = ttk.Frame(self)
        input_frame.pack(side="top", fill="x", expand=True, padx=10, pady=0)

        ext_frame = ttk.LabelFrame(input_frame, text="Список действий")
        ext_frame.pack(side="left", fill="both", expand=True, padx=5, pady=0)

        i = ttk.Frame(ext_frame)
        i.grid(row=0, column=0, sticky="nsew", padx=(5,0), pady=(0,5))

        facility_label = ttk.Label(i, text="Категория", anchor="w")
        facility_label.pack(side="left", padx=(0,5))

        self.facility_var = tk.StringVar()
        self.facility_var.set("Все")
        self.facility_combobox = ttk.Combobox(i, textvariable=self.facility_var, values=self.facility_values)
        self.facility_combobox.pack(side="left", padx=(0,5))

        severity_label = ttk.Label(i, text="Важность", anchor="w")
        severity_label.pack(side="left", padx=(0,5))

        self.severity_var = tk.StringVar()
        self.severity_var.set("Все")
        self.severity_combobox = ttk.Combobox(i, textvariable=self.severity_var, values=self.severity_values)
        self.severity_combobox.pack(side="left", padx=(0,5))

        a = ttk.Frame(ext_frame)
        a.grid(row=1, column=0, sticky="nsew", padx=(5,0))

        self.color_button = ttk.Button(a, text="Добавить", command=self.add)
        self.color_button.grid(row=0, column=4)

        self.tlabel = ttk.Label(a, text="", anchor="w", width=2)
        self.tlabel.grid(row=0, column=2)

        self.text_contains_label = ttk.Label(a, text="Текст содержит", anchor="w")
        self.text_contains_label.grid(row=0, column=0, padx=(0,5))

        self.text_contains_entry = ttk.Entry(a, width=47)
        self.text_contains_entry.grid(row=0, column=1)

        e = ttk.Frame(ext_frame)
        e.grid(row=2, column=0, sticky="nsew")

        self.color_table_frame = ttk.LabelFrame(e, text="Таблица соответствий")
        self.color_table_frame.pack(fill="both", expand=True, padx=0, pady=0)

        self.color_table = ttk.Treeview(self.color_table_frame, columns=("Категория", "Важность", "Текст содержит", "Действие"), show="headings")
        self.color_table.heading("Категория", text="Категория")
        self.color_table.column("Категория", width=120, minwidth=50, stretch=tk.NO)
        self.color_table.heading("Важность", text="Важность")
        self.color_table.column("Важность", width=120, minwidth=50, stretch=tk.NO)
        self.color_table.heading("Текст содержит", text="Текст содержит")
        self.color_table.column("Текст содержит", width=300, minwidth=50, stretch=tk.NO)
        self.color_table.heading("Действие", text="Действие")
        self.color_table.column("Действие", width=180, minwidth=50, stretch=tk.NO)
        self.color_table.grid(row=0,column=0, sticky="nsew")

        self.color_scrollbar = ttk.Scrollbar(self.color_table_frame, orient="vertical", command=self.color_table.yview)
        self.color_scrollbar.grid(row=0,column=1, sticky="ns")
        self.color_table.configure(yscrollcommand=self.color_scrollbar.set)

        self.colo_scrollbar = ttk.Scrollbar(self.color_table_frame, orient="horizontal", command=self.color_table.xview)
        self.colo_scrollbar.grid(row=1, column=0, sticky="ew")
        self.color_table.configure(xscrollcommand=self.colo_scrollbar.set)

        # Новый фрейм с дополнительными опциями настройки
        new_frame = ttk.LabelFrame(input_frame, text="Действие")
        new_frame.pack(side="right", fill="both",expand=True, padx=0, pady=0)



        # Флаг разрешения создания окна тревоги
        self.allow_alert_var = tk.BooleanVar()
        self.allow_alert_check = ttk.Checkbutton(new_frame, text="Создание окна\nпредупреждения", variable=self.allow_alert_var)
        self.allow_alert_check.pack(anchor="w", padx=3)

        frame0 = ttk.Frame(new_frame)
        frame0.pack(side="right", fill="both", expand=True, padx=(0, 0), pady=5)

        self.allow_sound_var = tk.BooleanVar()
        self.allow_sound_check = ttk.Checkbutton(frame0, text="Воспроизведение  \nаудиофайла", variable=self.allow_sound_var)
        self.allow_sound_check.grid(row=0,column=0, padx=3)

        sound_file_button = ttk.Button(frame0, text="Слушать", width=8, command=self.listen_sound_file)
        sound_file_button.grid(row=0,column=1)

        # Поле выбора звукового файла
        self.sound_file_var = tk.StringVar()
        self.sound_file_entry = ttk.Entry(frame0, textvariable=self.sound_file_var, width=15)
        self.sound_file_entry.grid(row=1, column=0, padx=(20,5))
        sound_file_button = ttk.Button(frame0, text="Файл", width=8, command=self.browse_sound_file)
        sound_file_button.grid(row=1, column=1, pady=(5,5))

        # Поле указания количества раз проигрывания звукового файла
        self.sound_repeat_var = tk.IntVar()
        self.sound_repeat_label = ttk.Label(frame0, text="Количество повторов")
        self.sound_repeat_label.grid(row=2, column=0)
        self.sound_repeat_spinbox = ttk.Spinbox(frame0, from_=1, to=10, textvariable=self.sound_repeat_var, width=5)
        self.sound_repeat_spinbox.grid(row=2, column=1, padx=(5,0))
        self.sound_repeat_spinbox.set(1)

        # Флаг разрешения запуска внешней программы
        self.allow_external_var = tk.BooleanVar()
        self.allow_external_check = ttk.Checkbutton(frame0, text="Запуск программы", variable=self.allow_external_var)
        self.allow_external_check.grid(row=3, column=0, padx=0)

        self.program_var = tk.StringVar()
        self.program_entry = ttk.Entry(frame0, textvariable=self.program_var, width=15)
        self.program_entry.grid(row=4, column=0, padx=(20, 5))
        program_button = ttk.Button(frame0, text="Файл", width=8, command=self.browse_program)
        program_button.grid(row=4, column=1, pady=(5, 5))

        ok_button = ttk.Button(self, text="OK", command=self.save_and_quit)
        ok_button.pack(side="left", padx=10, pady=10)

        cancel_button = ttk.Button(self, text="Отмена", command=self.destroy)
        cancel_button.pack(side="right", padx=10, pady=10)

        remove_button = ttk.Button(self, text="Удалить", command=self.remove_selected_row)
        remove_button.pack(side="right", padx=10, pady=10)

        move_up_button = ttk.Button(self, text="Вверх", command=self.move_selected_row_up)
        move_up_button.pack(side="right", padx=10, pady=10)

        move_down_button = ttk.Button(self, text="Вниз", command=self.move_selected_row_down)
        move_down_button.pack(side="right", padx=10, pady=10)


#        self.update_color_table()


    def browse_sound_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Sound files", "*.wav *.mp3")])
        if file_path:
            self.sound_file_entry.delete(0, tk.END)
            self.sound_file_entry.insert(0,file_path)
        return

    def listen_sound_file(self):
        sound_file = self.sound_file_var.get()
        if sound_file:
            pygame.mixer.init()
            pygame.mixer.music.load(sound_file)
            pygame.mixer.music.play()
        return

    def browse_program(self):
        file_path = filedialog.askopenfilename(filetypes=[("Program files", "*.sh *.bin")])
        if file_path:
            self.program_entry.delete(0, tk.END)
            self.program_entry.insert(0, file_path)
        return



    def load_color_mapping(self):
        try:
            with open("processing.json", "r") as file:
                self.color_mapping = json.load(file)
                self.update_color_table()
        except FileNotFoundError:
            pass

    def update_color_table(self):
        self.color_table.delete(*self.color_table.get_children())
        for facility_severity, action_str in self.color_mapping.items():
            facility, severity, text_contains = facility_severity.split("_") if "_" in facility_severity else (facility_severity, "", "")
            facility = facility if facility else ""
            if "All" in facility:
                facility = "Все"
            severity = severity if severity else ""
            if "All" in severity:
                severity = "Все"
            text_contains = text_contains if text_contains else ""
#            print(action_str)
            actions = []
            if "Show alarm" in action_str:
                actions.append("Создание окна предупреждения")
            if "Play sound" in action_str:
                actions.append("Воспроизведение аудиофайла")
            if "Run program" in action_str:
                actions.append("Запуск программы")
            action_display= " И ".join(actions)
            self.color_table.insert("", "end", values=(facility, severity, text_contains, action_display))


    def add(self):
        flags = []
        if self.allow_alert_var.get():
            print(self.allow_alert_var.get())
            flags.append("Создание окна предупреждения")
        if self.allow_sound_var.get():
            sound_file = self.sound_file_var.get()
            if sound_file:
                flags.append("Воспроизведение аудиофайла")
        if self.allow_external_var.get():
            program = self.program_var.get()
            if program:
                flags.append("Запуск программы")
        # Сформируем строку для столбца действия
        action_str = " И ".join(flags) if flags else ""
        # Получаем значения для других столбцов
        facility = self.facility_combobox.get()
        severity = self.severity_combobox.get()
        text_contains = self.text_contains_entry.get()

        for item_id in self.color_table.get_children():
            values = self.color_table.item(item_id)['values']
            values2 = [facility, severity, text_contains]
            if values[:3] == values2:
                self.color_table.item(item_id, values=(facility, severity, text_contains, action_str))
                return
        self.color_table.insert("", "end", values=(facility, severity, text_contains, action_str))

    def save_and_quit(self):
        self.save_table_data()
        self.destroy()

    def save_table_data(self):
        self.color_mapping = {}
        for item_id in self.color_table.get_children():
            values = self.color_table.item(item_id)['values']
            facility, severity, text_contains, action_str = values
            if "Все" in facility:
                facility = "All"
            if "Все" in severity:
                severity = "All"
            flags = []
            if "Создание окна предупреждения" in action_str:
                flags.append("Show alarm")
            if "Воспроизведение аудиофайла" in action_str:
                sound_file = self.sound_file_var.get()
                repeat_count = self.sound_repeat_var.get()
                flags.append(f"Play sound: {sound_file}, play count: {repeat_count} ")
            if "Запуск программы" in action_str:
                program = self.program_var.get()
                flags.append(f"Run program: {program}")

            action_str = " AND ".join(flags)
            facility_severity = f"{facility}_{severity}_{text_contains}" if facility and severity else facility or severity
            self.color_mapping[facility_severity] = action_str

        with open("processing.json", "w") as file:
            json.dump(self.color_mapping, file, indent=4)

    def remove_selected_row(self):
        selected_item = self.color_table.selection()[0]
        self.color_table.delete(selected_item)

    def move_selected_row_up(self):
        selected_item = self.color_table.selection()[0]
        current_index = int(self.color_table.index(selected_item))
        if current_index > 0:
            self.color_table.move(selected_item, "", current_index - 1)
#            self.update_color_mapping_order()

    def move_selected_row_down(self):
        selected_item = self.color_table.selection()[0]
        current_index = int(self.color_table.index(selected_item))
        if current_index < len(self.color_table.get_children()) - 1:
            self.color_table.move(selected_item, "", current_index + 1)
#            self.update_color_mapping_order()

if __name__ == "__main__":
    app = HighlightingSettings(None)
    app.mainloop()
