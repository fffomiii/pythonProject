from queue import Queue
import tkinter as tk
from tkinter import ttk
import socketserver
import re
import threading
import subprocess
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
import json
import sys
import os
from datetime import datetime, timedelta
from tkinter import messagebox
import importlib.resources as pkg_resources
import appdirs

class TCPSyslogHandler(socketserver.BaseRequestHandler):
    def __init__(self, request, client_address, server, log_queue):
        self.log_queue = log_queue
        super().__init__(request, client_address, server)


    def handle(self):
        data = self.request.recv(1024).strip().decode("utf-8")
        logs = data.split('\n')
        for log in logs:
            if log:
                print("tcp_2:", log)
                log_data = self.parse_log_message(log)
                if log_data is not None:
                    self.log_queue.put(log_data)

    def parse_log_message(self, log_message):
        regex_pattern = r'<(\d+)>(\d+) (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+[\+-]\d{2}:\d{2}) (\S+|-) (\S+|-) (\d+|-) (\S+|-) (\[.*?\]|-)?\s*(.*)'

        match = re.match(regex_pattern, log_message)
        if match:
            priority = match.group(1)
            version = match.group(2)
            timestamp = match.group(3)
            hostname = match.group(4) if match.group(4) and match.group(4) != '-' else ""
            appname = match.group(5) if match.group(5) and match.group(5) != '-' else ""
            process_id = match.group(6) if match.group(6) and match.group(6) != '-' else ""
            message_id = match.group(7) if match.group(7) and match.group(7) != '-' else ""
            structured_data = match.group(8) if match.group(8) and match.group(8) != '-' else ""
            message = match.group(9)
            return {
                'log': log_message,
                'priority': priority,
                'version': version,
                'timestamp': timestamp,
                'hostname': hostname,
                'appname': appname,
                'process_id': process_id,
                'message_id': message_id,
                'structured_data': structured_data,
                'message': message
            }
        else:
            print(log_message)
            return None


class UDPSyslogHandler(socketserver.BaseRequestHandler):
    def __init__(self, request, client_address, server, log_queue):
        self.log_queue = log_queue
        super().__init__(request, client_address, server)


    def handle(self):
        data = self.request[0].strip().decode("utf-8")
        print("udp:", data)
        log_data = self.parse_log_message(data)
        if log_data is not None:
            self.log_queue.put(log_data)

    def parse_log_message(self, log_message):
        regex_pattern = r'<(\d+)>(\d+) (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+[\+-]\d{2}:\d{2}) (\S+|-) (\S+|-) (\d+|-) (\S+|-) (\[.*?\]|-)?\s*(.*)'

        match = re.match(regex_pattern, log_message)
        if match:
            priority = match.group(1)
            version = match.group(2)
            timestamp = match.group(3)
            hostname = match.group(4) if match.group(4) and match.group(4) != '-' else ""
            appname = match.group(5) if match.group(5) and match.group(5) != '-' else ""
            process_id = match.group(6) if match.group(6) and match.group(6) != '-' else ""
            message_id = match.group(7) if match.group(7) and match.group(7) != '-' else ""
            structured_data = match.group(8) if match.group(8) and match.group(8) != '-' else ""
            message = match.group(9)

            return {
                'log': log_message,
                'priority': priority,
                'version': version,
                'timestamp': timestamp,
                'hostname': hostname,
                'appname': appname,
                'process_id': process_id,
                'message_id': message_id,
                'structured_data': structured_data,
                'message': message
            }
        else:
            return None




class SyslogServer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.display_real_time = tk.BooleanVar(value=True)
        self.display_file = False
        self.selected_file = None
        self.tcp_enabled = False
        self.upd_enabled = False
        self.server = None


        self.title("Визуальный сервер системного журнала от f0ma")
        self.geometry("800x600")

        self.toolbar_frame = ttk.Frame(self)
        self.toolbar_frame.pack(side="top", fill="x")

        self.start_server_button = ttk.Button(self.toolbar_frame, text="Запуск", command=self.start_server)
        self.start_server_button.pack(side="left", padx=5, pady=5)

        self.setup_button = ttk.Button(self.toolbar_frame, text="Настройка", command=self.setup_vss)
        self.setup_button.pack(side="left", padx=5, pady=5)

        self.processing_button = ttk.Button(self.toolbar_frame, text="Реагирование", command=self.processing_vss)
        self.processing_button.pack(side="left", padx=5, pady=5)

        self.highlighting_button = ttk.Button(self.toolbar_frame, text="Выделение", command=self.highlighting_vss)
        self.highlighting_button.pack(side="left", padx=5, pady=5)

        self.clear_logs_button = ttk.Button(self.toolbar_frame, text="Очистка", command=self.clear_logs)
        self.clear_logs_button.pack(side="left", padx=5, pady=5)

        self.terminate_button = ttk.Button(self.toolbar_frame, text="Выход", command=self.close)
        self.terminate_button.pack(side="left", padx=5, pady=5)

        self.display_frame = ttk.LabelFrame(self,text="Настройка отображения")
        self.display_frame.pack(side="top",fill="x",pady=10)

        self.filter_button = ttk.Button(self.display_frame, text="Фильтр", command=self.open_filter_windows)
        self.filter_button.pack(side="left", padx=5, pady=15)

        self.display_mode_frame = ttk.Frame(self.display_frame)
        self.display_mode_frame.pack(side="left", padx=20, pady=0)

        self.toggle_display_real_time_button = ttk.Checkbutton(self.display_mode_frame, text="Отображение в реальном времени",
                                                               command=self.toggle_display_mode)
        self.toggle_display_real_time_button.pack(side="top", padx=0, pady=0)
        self.toggle_display_real_time_button.invoke()  # Вызываем кнопку, чтобы она по умолчанию была выбрана

        self.toggle_display_file_button = ttk.Checkbutton(self.display_mode_frame, text="Отображение из лог-файла",
                                                          command=self.toggle_display_mode)
        self.toggle_display_file_button.pack(side="left", padx=0, pady=0)

        self.view_file_label = ttk.Label(self.display_frame, text="Файл:")
        self.view_file_label.pack(side="left", padx=10, pady=15)

        self.view_file_options = ["Не выбран"]
        self.load_files()
        self.view_file_combobox = ttk.Combobox(self.display_frame, values=self.view_file_options)
        self.view_file_combobox.pack(side="left", padx=5)
        self.view_file_combobox.current(0)

        self.display_message_frame = ttk.LabelFrame(self, text="Системные события:")
        self.display_message_frame.pack(side="top", fill="both", expand=True, pady=10)

        self.log_tree = ttk.Treeview(self.display_message_frame, columns=(
            "Приоритет", "Временная_метка", "Версия", "Хост", "Приложение", "ID_Процесса", "Сообщение", "Структурированные_данные",
            "ID_Сообщения"
        ), show="headings")

        for column in self.log_tree["columns"]:
            self.log_tree.heading(column, text=column, command=lambda col=column: self.sort_column(col))

        self.log_tree.column("Приоритет", minwidth=50, width=80, stretch=tk.NO)
        self.log_tree.column("Временная_метка", minwidth=50, width=350, stretch=tk.NO)
        self.log_tree.column("Версия", minwidth=50, width=80, stretch=tk.NO)
        self.log_tree.column("Хост", minwidth=50, width=120, stretch=tk.NO)
        self.log_tree.column("Приложение", minwidth=50, width=120, stretch=tk.NO)
        self.log_tree.column("ID_Процесса", minwidth=50, width=100, stretch=tk.NO)
        self.log_tree.column("Сообщение", minwidth=50, width=750, stretch=tk.NO)
        self.log_tree.column("Структурированные_данные", minwidth=50, width=200, stretch=tk.NO)
        self.log_tree.column("ID_Сообщения", minwidth=50, width=100, stretch=tk.NO)

        self.log_tree.grid(row=0, column=0, sticky="nsew")

        self.log_scroll = ttk.Scrollbar(self.display_message_frame, orient="vertical", command=self.log_tree.yview)
        self.log_scroll.grid(row=0,column=1, sticky="ns")
        self.log_tree.configure(yscrollcommand=self.log_scroll.set)

        self.log_scroll_g = ttk.Scrollbar(self.display_message_frame, orient="horizontal", command=self.log_tree.xview)
        self.log_scroll_g.grid(row=1, column=0, sticky="ew")
        self.log_tree.configure(xscrollcommand=self.log_scroll_g.set)

        self.log_tree.bind("<Configure>", lambda e: self.log_scroll_g.set(*self.log_tree.xview()))

        self.display_message_frame.grid_rowconfigure(0, weight=1)
        self.display_message_frame.grid_columnconfigure(0, weight=1)


        # Создание метки для отображения значений протокола
        self.protocol_label = ttk.Label(self, text="")
        self.protocol_label.pack(side="bottom", padx=10, pady=0, anchor="w")

        self.log_queue = Queue()
        self.file_log_queue = Queue()
        self.proc_queue = Queue()
        self.server_thread = None
        self.display_thread = None
        self.processing_thread = None
        self.file_thread = None
        self.rev = False
        self.sort_order = {col: False for col in self.log_tree["columns"]}
        self.server_settings_observer = Observer()

#        self.settings_dir = appdirs.user_data_dir("f0ma")


#        self.current_dir = os.path.dirname(os.path.abspath(__file__))
#        settings_path = os.path.join(self.current_dir, "server_settings.json")
#        self.server_settings_observer.schedule(ServerSettingsHandler(), path=settings_path, recursive=False)
        self.server_settings_observer.schedule(ServerSettingsHandler(self), path="server_settings.json", recursive=False)

#        self.server_settings_observer.schedule(ServerSettingsHandler(), path="server_settings.json", recursive=False)
        self.server_settings_observer.start()

        self.update_server_settings()

        self.start_file_watcher()
        self.toggle_display_real_time_button.state(['selected'])
        self.toggle_display_mode()


    def sort_priority(self, reverse=False):
        data = [(int(self.log_tree.set(child, "Приоритет")), child) for child in self.log_tree.get_children('')]
        data.sort(reverse=reverse)
        for index, (val, child) in enumerate(data):
            self.log_tree.move(child, '', index)

    def sort_version(self, reverse=False):
        data = [(int(self.log_tree.set(child, "Версия")), child) for child in self.log_tree.get_children('')]
        data.sort(reverse=reverse)
        for index, (val, child) in enumerate(data):
            self.log_tree.move(child, '', index)

    def sort_process_id(self, reverse=False):
        data = [(self.log_tree.set(child, "ID_Процесса"), child) for child in self.log_tree.get_children('')]
        if not reverse:
            data.sort(key=lambda x: (1000000 if x[0] == '' else int(x[0])))
        else:
            data.sort(key=lambda x: (-1 if x[0] == '' else int(x[0])), reverse=True)
        for index, (val, child) in enumerate(data):
            self.log_tree.move(child, '', index)

    def sort_timestamp(self, reverse=False):
        data = [(self.log_tree.set(child, "Временная_метка"), child) for child in self.log_tree.get_children('')]
        if not reverse:
            data.sort(key=lambda x: datetime.fromisoformat(x[0]) if x[0] else datetime.min)
        else:
            data.sort(key=lambda x: datetime.fromisoformat(x[0]) if x[0] else datetime.min, reverse=True)
        for index, (val, child) in enumerate(data):
            self.log_tree.move(child, '', index)

    def sort_other(self, col, reverse=False):
        print(col)
        data = [(self.log_tree.set(child, col), child) for child in self.log_tree.get_children('')]
        print(data)
        if not reverse:
            data.sort(key=lambda x: (x[0].lower(), x[0]))
        else:
            data.sort(key=lambda x: (x[0].lower(), x[0]), reverse=True)
        for index, (val, child) in enumerate(data):
            self.log_tree.move(child, '', index)

    def sort_column(self, col):
        current_sort_order = self.sort_order[col]
        self.sort_order[col] = not current_sort_order
        reverse = self.sort_order[col]
        print(current_sort_order)
        if col == "Приоритет":
            self.sort_priority(reverse)
        elif col == "Версия":
            self.sort_version(reverse)
        elif col == "ID_Процесса":
            self.sort_process_id(reverse)
        elif col == "Временная_метка":
            self.sort_timestamp(reverse)
        else:
            self.sort_other(col, reverse)

    def load_files(self):
#        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        # Путь к файлу, расположенному в той же папке
#        file_path = os.path.join(self.current_dir, 'files.json')
        try:
            with open("files.json", "r") as file:
                files_data = json.load(file)
                if isinstance(files_data, list):
                    for item in files_data:
                        file_name = os.path.splitext(item['file'])[0]
                        self.view_file_options.append(file_name)

                else:
                    print("Invalid file")
        except FileNotFoundError:
            print("File not found")
    def toggle_display_mode(self):
        if self.display_real_time:
            self.display_real_time = False
            self.display_file = True
            self.toggle_display_real_time_button.state(['!selected'])  # Убираем выбор с флага "Display in Real Time"

        else:
            self.display_real_time = True
            self.display_file = False
            self.toggle_display_file_button.state(['!selected'])
            # Убираем выбор с флага "Display from File"

    def close_server(self):
        try:
            if self.server:
                self.server.shutdown()
                self.server.server_close()
        except Exception as e:
            print("Error while closing server:", e)

    def close(self):
        self.close_server()
        sys.exit()
    def get_log_highlight_color(self, priority, message):
        color = "white"
        severity = priority & 0x07
        facility = (priority >> 3) & 0x1F
        facility_mapping = {
            "All": -1,
            "Kernel": 0,
            "User": 1,
            "Mail": 2,
            "Daemon": 3,
            "Auth": 4,
            "Syslog": 5,
            "LPR": 6,
            "News": 7,
            "UUCP": 8,
            "Cron": 9,
            "Authpriv": 10,
            "FTP": 11,
            "NTP": 12,
            "Log Audit": 13,
            "Log Alert": 14,
            "Clock Daemon": 15,
            "Local0": 16,
            "Local1": 17,
            "Local2": 18,
            "Local3": 19,
            "Local4": 20,
            "Local5": 21,
            "Local6": 22,
            "Local7": 23
        }
        severity_mapping = {
            "All": -1,
            "Emergency": 0,
            "Alert": 1,
            "Critical": 2,
            "Error": 3,
            "Warning": 4,
            "Notice": 5,
            "Informational": 6,
            "Debug": 7
        }
        with open("highlighting_settings.json", "r") as file:
            settings = json.load(file)
        for key, value in settings.items():
            f, s, g = key.split('_')
            s_value = severity_mapping[s]
            f_value = facility_mapping[f]


            if f_value == -1 or f_value == facility:  # 8 соответствует "All" фасилити
                if s_value == -1 or s_value == severity:  # 8 соответствует "All" северити
                    if g:
                        tokens, operands = self.parse_expression(g)
                        if self.apply_expression(message, tokens, operands):
                            color = value
                            break
                    else:
                        color = value
                        break
        return color
    def start_file_watcher(self):
        event_handler = HighlightingSettingsHandler(self)
        observer = Observer()
        observer.schedule(event_handler, ".", recursive=False)
        observer.start()

    def extract_rotation_details(self, rotation):
        size_pattern = r"by size (\d+)\s*(KBs|MBs|GBs),\s*(.*?)\[(\d+)(?:\.\.(\d+))?\]"
        time_pattern = r"by (Week|Month|Day|Year) (\d+)\s*hour,\s*(.*?)\[(\d+)(?:\.\.(\d+))?\]"
        if rotation.startswith("by size"):
            match = re.match(size_pattern, rotation)
            if match:
                size_value = int(match.group(1))
                size_unit = match.group(2)
                file_name = match.group(3)
                start_index = int(match.group(4))
                end_index = int(match.group(5)) if match.group(5) else start_index
                return {"type": "by size", "size_value": size_value, "size_unit": size_unit,
                        "file_name": file_name, "start_index": start_index, "end_index": end_index}
        elif rotation.startswith("by"):
            match = re.match(time_pattern, rotation)
            if match:
                time_unit = match.group(1)
                hours = int(match.group(2))
                file_name = match.group(3)
                start_index = int(match.group(4))
                end_index = int(match.group(5)) if match.group(5) else start_index
                return {"type": "by data", "time_unit": time_unit, "hours": hours,
                        "file_name": file_name, "start_index": start_index, "end_index": end_index}
        return None

    def convert(self,size_value, size_unit):
        if size_unit == "KBs":
            return size_value*1024
        elif size_unit == "MBs":
            return size_value*1024*1024
        elif size_unit == "GBs":
            return size_value*1024*1024*1024
        else:
            return size_value

    def rotate_by_size(self, rotation_settings):
        a = self.extract_rotation_details(rotation_settings)
        size_value = a.get("size_value",0)
        size_unit = a.get("size_unit", "KBs")
        name_new = a.get("file_name")
        start_index = a.get("start_index")
        end_index = a.get("end_index")
        max_size = self.convert(size_value, size_unit)
        return max_size, name_new, start_index, end_index

    def rotate_by_time(self, rotation_settings):
        rotation_details = self.extract_rotation_details(rotation_settings)
        print(rotation_details)
        if rotation_details["type"] == "by data":
            time_unit = rotation_details["time_unit"]
            hours = rotation_details["hours"]
            file_name = rotation_details["file_name"]
            start_index = rotation_details["start_index"]
            end_index = rotation_details["end_index"]
            if time_unit == "Week":
                rotation_period = hours * 7 * 24 * 60 * 60
            elif time_unit == "Month":
                rotation_period = hours * 30 * 24 * 60 * 60
            elif time_unit == "Day":
                rotation_period = hours * 24 * 60 * 60
            elif time_unit == "Year":
                rotation_period = hours * 365 * 24 * 60 * 60
            else:
                rotation_period = 0  # Default to 0 if time unit is not recognized

            return rotation_period, file_name, start_index, end_index
        else:
            return None

    def generate_new_file_name(self, file_name, index):
        file_name, file_extension = os.path.splitext(file_name)
        if '_' in file_name:
            part = file_name.rsplit('_',1)
            try:
                number = int(part[-1])
                if number < index:
                    return f"{part[0]}_{index}{file_extension}"
            except ValueError:
                pass
        return f"{file_name}_{index}{file_extension}"




    def start_server(self):
        if self.display_real_time and self.view_file_combobox.get() == "Не выбран":
            self.run_server()
            if self.display_thread is None or not self.display_thread.is_alive():
                self.display_thread = threading.Thread(target=self.display_logs)
                self.display_thread.daemon = True
                self.display_thread.start()


            if self.processing_thread is None or not self.processing_thread.is_alive():
                self.processing_thread = threading.Thread(target=self.processing)
                self.processing_thread.daemon = True
                self.processing_thread.start()



        elif self.display_real_time and self.view_file_combobox.get() != "Не выбран":

            self.run_server()
            if self.display_thread is None or not self.display_thread.is_alive():
                self.display_thread = threading.Thread(target=self.display_logs)
                self.display_thread.daemon = True
                self.display_thread.start()

            if self.processing_thread is None or not self.processing_thread.is_alive():
                self.processing_thread = threading.Thread(target=self.processing)
                self.processing_thread.daemon = True
                self.processing_thread.start()

                rotation_settings = {}
                try:
                    with open("files.json", "r") as file:
                        rotation_settings_list = json.load(file)
                        for item in rotation_settings_list:
                            file_name = item.get("file", "")
                            rotation = item.get("rotation", "")
                            rotation_settings[file_name] = rotation
                except FileNotFoundError:
                    print("File not found.")

                file_name = self.view_file_combobox.get() + ".json"
                rotation = rotation_settings.get(file_name, {})
                print(rotation)
                if rotation.startswith("by size"):
                    print("size")
                    max_size, name_new, start_index, end_index = self.rotate_by_size(rotation)
                    self.file_thread = threading.Thread(target=self.write_logs_to_file_size,
                                                        args=(
                                                        self.file_log_queue, file_name, max_size, name_new, start_index,
                                                        end_index))
                    self.file_thread.daemon = True
                    self.file_thread.start()
                elif rotation.startswith("by"):
                    print("data")
                    rotation_period, name_new, start_index, end_index = self.rotate_by_time(rotation)
                    print("ss")
                    self.file_thread = threading.Thread(target=self.write_logs_to_file_time,
                                                        args=(self.file_log_queue, file_name, rotation_period, name_new, start_index, end_index))
                    self.file_thread.daemon = True
                    self.file_thread.start()
                else:
                    self.file_thread = threading.Thread(target=self.write_logs_to_file,
                                                        args=(self.file_log_queue,))
                    self.file_thread.daemon = True
                    self.file_thread.start()

        elif not self.display_real_time and self.view_file_combobox.get() != "Не выбран":
            self.display_logs_from_file()
            if self.display_thread is None or not self.display_thread.is_alive():
                self.display_thread = threading.Thread(target=self.display_logs)
                self.display_thread.daemon = True
                self.display_thread.start()

    def write_logs_to_file_size(self, file_log_queue, file_name, max_size, name_new, start_index, end_index):
        if start_index == end_index:
            i=end_index-1
        else:
            i=0
        while True:
            if not self.log_queue.empty():
                if os.path.getsize(file_name) > max_size:
                    i = i + 1
                    if i>end_index:
                        break
                    if start_index == end_index:
                        file_name = self.generate_new_file_name(name_new, i)
                    else:
                        file_name = self.generate_new_file_name(file_name, i)
                with open(file_name, "a") as file:
                    file.write(json.dumps(file_log_queue.get()) + "\n")

    def write_logs_to_file_time(self, file_log_queue, file_name, rotation_period, name_new, start_index, end_index):
        if start_index == end_index:
            i=end_index-1
        else:
            i=0
        rotation_time = datetime.now()
        while True:
            if not self.log_queue.empty():
                current_time = datetime.now()
                time_difference = current_time - rotation_time
                if time_difference >= timedelta(seconds=rotation_period):
                    rotation_time = datetime.now()
                    i = i +1
                    print(i, current_time, time_difference, rotation_time)
                    if i>end_index:
                        print("breK")
                        break
                    if start_index == end_index:
                        print("new")
                        file_name = self.generate_new_file_name(name_new, i)
                        print(file_name)
                    else:
                        print("old")
                        file_name = self.generate_new_file_name(file_name, i)
                        print(file_name)
                with open(file_name, "a") as file:
                    file.write(json.dumps(file_log_queue.get()) + "\n")

    def write_logs_to_file(self, file_log_queue):
        selected_file = self.view_file_combobox.get()
        file_name = f"{selected_file}.json"
        while True:
            if not self.log_queue.empty():
                with open(file_name, "a") as file:
                    file.write(json.dumps(file_log_queue.get()) + "\n")

    def parse_lg_message(self, log_message):
        regex_pattern = r'<(\d+)>(\d+) (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+[\+-]\d{2}:\d{2}) (\S+|-) (\S+|-) (\d+|-) (\S+|-) (\[.*?\]|-)?\s*(.*)'

        match = re.match(regex_pattern, log_message)
        if match:
            priority = match.group(1)
            version = match.group(2)
            timestamp = match.group(3)
            hostname = match.group(4) if match.group(4) and match.group(4) != '-' else ""
            appname = match.group(5) if match.group(5) and match.group(5) != '-' else ""
            process_id = match.group(6) if match.group(6) and match.group(6) != '-' else ""
            message_id = match.group(7) if match.group(7) and match.group(7) != '-' else ""
            structured_data = match.group(8) if match.group(8) and match.group(8) != '-' else ""
            message = match.group(9)

            return {
                'log': log_message,
                'priority': priority,
                'version': version,
                'timestamp': timestamp,
                'hostname': hostname,
                'appname': appname,
                'process_id': process_id,
                'message_id': message_id,
                'structured_data': structured_data,
                'message': message
            }
        else:
            return None

    # Добавьте вашу логику для записи логов в выбранный файл в формате JSON
    def display_logs_from_file(self):
        selected_file = self.view_file_combobox.get()
        file_name = f"{selected_file}.json"
        with open(file_name, "r") as file:
            for line in file:
                log_data = json.loads(line.strip())
                lg_data = self.parse_lg_message(log_data)
                print(lg_data)
                self.log_queue.put(lg_data)

    # Добавьте вашу логику для отображения логов из выбранного файла на дисплей
    def run_server(self):
        self.update_server_settings()
        print("TCP Enabled:", self.tcp_enabled)
        print("UDP Enabled:", self.udp_enabled)
        print(self.tcp_enabled,self.udp_enabled, self.tcp_address, self.tcp_port, self.udp_address, self.udp_port)
        if self.server_thread is None or not self.server_thread.is_alive():
            if self.tcp_enabled and self.udp_enabled:
                print("oba")
                self.server = threading.Thread(target=self.run_tcp_udp_server)
            elif self.tcp_enabled:
                print("tcp")
                self.server = threading.Thread(target=self.run_tcp_server)
            elif self.udp_enabled:
                print("udp")
                self.server = threading.Thread(target=self.run_udp_server)
            else:
                print("Both TCP and UDP are disabled in server_settings.json")
            self.server.daemon = True
            self.server.start()
        else:
            self.server.shutdown()
            self.server.join()
            if self.tcp_enabled and self.udp_enabled:
                print("oba")
                self.server = threading.Thread(target=self.run_tcp_udp_server)
            elif self.tcp_enabled:
                print("tcp")
                self.server = threading.Thread(target=self.run_tcp_server)
            elif self.udp_enabled:
                print("udp")
                self.server = threading.Thread(target=self.run_udp_server)
            else:
                print("Both TCP and UDP are disabled in server_settings.json")
            self.server.daemon = True
            self.server.start()

    def run_tcp_udp_server(self):
        tcp_server = socketserver.TCPServer((self.tcp_address, self.tcp_port),
                                            lambda *args: TCPSyslogHandler(*args, self.log_queue))

        udp_server = socketserver.UDPServer((self.udp_address, self.udp_port),
                                            lambda *args: UDPSyslogHandler(*args, self.log_queue))

        tcp_thread = threading.Thread(target=tcp_server.serve_forever)
        udp_thread = threading.Thread(target=udp_server.serve_forever)

        tcp_thread.start()
        udp_thread.start()

        tcp_thread.join()
    def run_tcp_server(self):
        print("Starting TCP")
        self.server = socketserver.TCPServer((self.tcp_address, self.tcp_port),
                                             lambda *args: TCPSyslogHandler(*args, self.log_queue))

        self.server.serve_forever()

    def run_udp_server(self):
        print("Starting UDP")
        self.server = socketserver.UDPServer((self.udp_address, self.udp_port),
                                             lambda *args: UDPSyslogHandler(*args, self.log_queue))

        self.server.serve_forever()

    # Функция для чтения файла settings.json и парсинга значений
    def parse_settings(self):
        with open("settings.json", "r") as file:
            settings = json.load(file)
            priority_values = [index for index, value in enumerate(settings["priority_vars"]) if value]
            facility_values = [index for index, value in enumerate(settings["facility_vars"]) if value]
            custom_text = settings.get("custom_text","")
        return priority_values, facility_values, custom_text


    def parse_expression(self, expression):
        patterns_to_exclude = [
            r'\)\s*&\s*~\s*\(',
            r'\)\s*\|\s*~\s*\(',
            r'\)\s*&\s*\(',
            r'\)\s*\|\s*\(',
            r'\)\s*&\s*~',
            r'\)\s*\|\s*~',
            r'\)\s*&',
            r'\)\s*\|',
            r'&\s*~\s*\(',
            r'\|\s*~\s*\(',
            r'&\s*\(\s*~',
            r'\|\s*\(\s*~',
            r'&\s*~',
            r'\|\s*~',
            r'&',
            r'\|',
            r'~\s*\(',
            r'\(\s*~',
            r'~\s*\(',
            r'\(\s*~',
            r'\(',
            r'\)'
        ]
        t = r'(^~\s*\(\s*~|^~\s*\(|^\(\s*~|^\()|(\)\s*$)|(\)\s*&\s*~\s*\()|(\)\s*\|\s*~\s*\()|(\)\s*&\s*\()|(\)\s*\|\s*\()|(\)\s*&\s*~)|(\)\s*\|\s*~)|(\)\s*&\s*)|(\)\s*\|\s*)|(&\s*~\s*\()|(\|\s*~\s*\()|(&\s*\()|(\|\s*\()|(&\s*~)|(\|\s*~)|(&)|(\|)'
        operands = [operand for operand in re.split(t, expression) if operand]
        operands = [x.strip() for x in operands]
        non_special_operands = []
        for operand in operands:
            if not any (re.match(pattern, operand) for pattern in patterns_to_exclude):
#                non_special_operands.append(operand.strip())
                non_special_operands.append(operand)
#        print(non_special_operands)
#        print(tokens)
#        print(operands)
        return non_special_operands,operands
    def apply_expression(self, message, expression, operands):
        logical_expressions = {") & ~ (": ") and not ( ",
                                ")& ~ (": ") and not ( ",
                                ")&~ (": ") and not ( ",
                                ")& ~(": ") and not ( ",
                                ") &~ (": ") and not ( ",
                                ") & ~(": ") and not ( ",
                                ") &~(": ") and not ( ",
                                ")&~(": ") and not ( ",
                                ") | ~ (": " ) or not ( ",
                                ")| ~ (": " ) or not ( ",
                                ")|~ (": " ) or not ( ",
                                ")| ~(": " ) or not ( ",
                                ")|~(": " ) or not ( ",
                                ") |~ (": " ) or not ( ",
                                ") |~(": " ) or not ( ",
                                ") | ~(": " ) or not ( ",
                                ") & (": " ) and ( ",
                                ")& (": " ) and ( ",
                                ") &(": " ) and ( ",
                                ")&(": " ) and ( ",
                                ") | (": " ) or ( ",
                               ")| (": " ) or ( ",
                               ") |(": " ) or ( ",
                               ")|(": " ) or ( ",
                                ") & ~": " ) and not ",
                               ")& ~": " ) and not ",
                               ") &~": " ) and not ",
                               ")&~": " ) and not ",
                                ") | ~": " ) or not ",
                               ")| ~": " ) or not ",
                               ") |~": " ) or not ",
                               ")|~": " ) or not ",
                                ") &": " ) and ",
                               ")&": " ) and ",
                                ") |": " ) or ",
                               ")|": " ) or ",
                                "& ~ (": " and not ( ",
                               "&~ (": " and not ( ",
                               "& ~(": " and not ( ",
                               "&~(": " and not ( ",
                                "| ~ (": " or not ( ",
                               "|~ (": " or not ( ",
                               "| ~(": " or not ( ",
                               "|~(": " or not ( ",
                                "& (": " and ( ",
                               "&(": " and ( ",
                                "| (": " or ( ",
                               "|(": " or ( ",
                                "& ~": " and not ",
                               "&~": " and not ",
                                "| ~": " or not ",
                               "|~": " or not ",
                                "&": " and ",
                                "|": " or ",
                                "~ ( ~": " not ( not ",
                               "~( ~": " not ( not ",
                               "~ (~": " not ( not ",
                               "~(~": " not ( not ",
                                "~ (": " not ( ",
                               "~(": " not ( ",
                                "( ~": " ( not ",
                               "(~": " ( not ",
                               "(": " ( ",
                               ")": " ) "
        }
        result = [operand in message for operand in expression]
#        print(result)
        final_logical_expression = ""
        for element in operands:
            if element in expression:
                final_logical_expression +=str(result[expression.index(element)])
            elif element in logical_expressions:
                final_logical_expression += logical_expressions[element]
        print(final_logical_expression)
#        print(eval(final_logical_expression))
        return eval(final_logical_expression)

    # Функция для фильтрации входного лога
    def filter_log(self, log_data, allowed_priorities, allowed_facilities, custom_text):
        priority = int(log_data["priority"])
        severity = priority & 0x07
        facility = (priority >> 3) & 0x1F
        if severity in allowed_priorities and facility in allowed_facilities:
            message = log_data["log"]
#            print("m",message)
            if custom_text:
                tokens, operands = self.parse_expression(custom_text)
                if self.apply_expression(message, tokens, operands):
                    return log_data
            else:
                return log_data
            return None



    def parse_proc(self, priority, message):
        severity = priority & 0x07
        facility = (priority >> 3) & 0x1F
        facility_mapping = {
            "All": -1,
            "Kernel": 0,
            "User": 1,
            "Mail": 2,
            "Daemon": 3,
            "Auth": 4,
            "Syslog": 5,
            "LPR": 6,
            "News": 7,
            "UUCP": 8,
            "Cron": 9,
            "Authpriv": 10,
            "FTP": 11,
            "NTP": 12,
            "Log Audit": 13,
            "Log Alert": 14,
            "Clock Daemon": 15,
            "Local0": 16,
            "Local1": 17,
            "Local2": 18,
            "Local3": 19,
            "Local4": 20,
            "Local5": 21,
            "Local6": 22,
            "Local7": 23
        }
        severity_mapping = {
            "All": -1,
            "Emergency": 0,
            "Alert": 1,
            "Critical": 2,
            "Error": 3,
            "Warning": 4,
            "Notice": 5,
            "Informational": 6,
            "Debug": 7
        }
        with open("processing.json", "r") as file:
            settings = json.load(file)
        for key, value in settings.items():
            f, s, g = key.split('_')
            s_value = severity_mapping[s]
            f_value = facility_mapping[f]
            print(value)
            if f_value == -1 or f_value == facility:  # 8 соответствует "All" фасилити
                if s_value == -1 or s_value == severity:  # 8 соответствует "All" северити
                    if g:
                        tokens, operands = self.parse_expression(g)
                        if self.apply_expression(message, tokens, operands):
                            return value
                    else:
                        return value
        return False

    def show_alarm(self, message):
        messagebox.showwarning("Alarm", message)

    def get_sound_path(self, value):
        sound_index = value.find("Play sound:") + len("Play sound:")
        comma_index = value.find(",", sound_index)
        sound_path = value[sound_index:comma_index].strip()
        return sound_path

    def play_sound(self, sound_path, play_count):
        for _ in range(play_count):
            subprocess.run(["aplay", sound_path], check=True)

    def get_program_path(self, value):
        program_index = value.find("Run program:") + len("Run program:")
        program_path = '"' + value[program_index:].strip() + '"'
        return program_path


    def run_program(self, program_path):
        subprocess.run([program_path], shell=True)
    def processing(self):
        while True:
            if not self.proc_queue.empty():
                log_data = self.proc_queue.get()
                if log_data is not None:
                    priority = int(log_data["priority"])
                value = self.parse_proc(priority, log_data["log"])
                print("dd", value)
                if value:
                    if "Show alarm" in value:
                        self.show_alarm(log_data["log"])
                    if "Play sound" in value:
                        sound_path = self.get_sound_path(value)
                        match = re.search(r'play count:\s*(\d+)', value)
                        if match:
                            play_value = int(match.group(1))
                        self.play_sound(sound_path, play_value)
                    if "Run program" in value:
                        program_path = self.get_program_path(value)
                        self.run_program(program_path)


    def display_logs(self):
        i =0
        while True:
            if not self.log_queue.empty():
                log_data = self.log_queue.get()
                if log_data is not None:
                    priority = int(log_data["priority"])
#                else:
#                    print(log_data)
#                priority = int(log_data["priority"])
                allowed_priorities, allowed_facilities, custom_text = self.parse_settings()
                filtered_log_data = self.filter_log(log_data, allowed_priorities, allowed_facilities, custom_text)
                if filtered_log_data:
                    color_tag = self.get_log_highlight_color(priority, log_data["log"])
                    item_id = self.log_tree.insert("", "end", values=(
                        log_data['priority'],
                        log_data['timestamp'],
                        log_data['version'],
                        log_data['hostname'],
                        log_data['appname'],
                        log_data['process_id'],
                        log_data['message'],
                        log_data['structured_data'],
                        log_data['message_id']
                    ))
                    self.log_tree.item(item_id, tags=(color_tag,))
                    self.log_tree.tag_configure(color_tag, background=color_tag)
                    self.log_tree.update_idletasks()
                    self.update()

                    self.file_log_queue.put(log_data["log"])
                    self.proc_queue.put(log_data)

                    i = i+1

    def clear_logs(self):
        for child in self.log_tree.get_children():
            self.log_tree.delete(child)

    def setup_vss(self):
        subprocess.run(["python3", "setup_vss.py"])

    def processing_vss(self):
        subprocess.run(["python3", "processing_vss.py"])

    def highlighting_vss(self):
        subprocess.run(["python3", "highlighting_vss.py"])

    def open_filter_windows(callback):
        subprocess.run(["python3", "filter.py"])

    def update_highlighting_settings(self, settings):
        print("Update Highlighting Settings", settings)
    def update_server_settings(self):
        try:
            with open("server_settings.json", "r") as f:
                settings = json.load(f)
                self.udp_enabled = settings.get("UDP", {}).get("enabled", False)
                self.tcp_enabled = settings.get("TCP", {}).get("enabled", False)
                self.udp_settings = settings.get("UDP", {})
                self.udp_address = self.udp_settings.get("ip_address", "0.0.0.0") if self.udp_settings.get("ip_address") else "0.0.0.0"
                self.udp_port = int(self.udp_settings.get("port", 1514)) if self.udp_settings.get("port") else 1514
                self.tcp_settings = settings.get("TCP", {})
                self.tcp_address = self.tcp_settings.get("ip_address", "0.0.0.0") if self.tcp_settings.get("ip_address") else "0.0.0.0"
                self.tcp_port = int(self.tcp_settings.get("port", 1514)) if self.tcp_settings.get("port") else 1514

                # Форматирование и обновление текста метки
                protocol_text = ""
                if self.tcp_enabled:
                    protocol_text += f"TCP: {self.tcp_address}:{self.tcp_port}     "
                else:
                    protocol_text += "TCP: Сервер отключен       "
                if self.udp_enabled:
                    protocol_text += f"UDP: {self.udp_address}:{self.udp_port}      "
                else:
                    protocol_text += "UDP: Сервер отключен       "
                self.protocol_label.config(text=protocol_text)
        except FileNotFoundError:
            print("File 'server_settings.json' not found.")

class HighlightingSettingsHandler(FileSystemEventHandler):
    def __init__(self,app):
        self.app = app

    def on_modified(self, event):
        if event.src_path == "highlighting_settings.json":
            with open("highlighting_settings.json", "r") as file:
                settings = json.load(file)
                self.app.update_highlighting_settings(settings)


class ServerSettingsHandler(FileSystemEventHandler):

    def __init__(self,app):
        self.app = app
    def on_modified(self, event):
        if event.src_path == "server_settings.json":
            self.app.update_server_settings()
        if event.src_path == "files.json":
            self.app.load_files()

    def on_created(self, event):
        if event.src_path == "server_settings.json":
            self.app.update_server_settings()
        if event.src_path == "files.json":
            self.app.load_files()

    def on_deleted(self, event):
        if event.src_path == "server_settings.json":
            self.app.update_server_settings()
        if event.src_path == "files.json":
            self.app.load_files()

    def on_moved(self, event):
        if event.src_path == "server_settings.json":
            self.app.update_server_settings()
        if event.src_path == "files.json":
            self.app.load_files()


def main_entry():
    app = SyslogServer()
    app.mainloop()

if __name__ == "__main__":
    main_entry()
