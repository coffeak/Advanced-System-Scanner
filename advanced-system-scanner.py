import os
import json
import socket
import psutil
import datetime
import winreg
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Supported languages
LANGUAGES = {
    "English": {
        "title": "SpyScan - Advanced System Scanner",
        "startup_tab": "Startup Programs",
        "process_tab": "Running Processes",
        "network_tab": "Network Connections",
        "services_tab": "Windows Services",
        "ports_tab": "Open Ports",
        "about_tab": "About",
        "log_button": "Save Log",
        "file_saved": "Log saved successfully: ",
        "about_text": "SpyScan - Developed by Coffeak\nWebsite: coffeak.com",
    },
    "Türkçe": {
        "title": "SpyScan - Gelişmiş Sistem Tarayıcı",
        "startup_tab": "Başlangıç Programları",
        "process_tab": "Çalışan İşlemler",
        "network_tab": "Ağ Bağlantıları",
        "services_tab": "Windows Servisleri",
        "ports_tab": "Açık Portlar",
        "about_tab": "Hakkında",
        "log_button": "Log Kaydet",
        "file_saved": "Log başarıyla kaydedildi: ",
        "about_text": "SpyScan - Coffeak tarafından geliştirildi\nWeb sitesi: coffeak.com",
    }
}

current_language = LANGUAGES["English"]  # Default language


class SpyScanApp:
    def __init__(self, root):
        self.root = root
        self.root.title(current_language["title"])
        self.root.geometry("850x600")

        self.tabControl = ttk.Notebook(root)

        self.frame_startup = ttk.Frame(self.tabControl)
        self.frame_processes = ttk.Frame(self.tabControl)
        self.frame_network = ttk.Frame(self.tabControl)
        self.frame_services = ttk.Frame(self.tabControl)
        self.frame_ports = ttk.Frame(self.tabControl)
        self.frame_about = ttk.Frame(self.tabControl)

        self.tabControl.add(self.frame_startup, text=current_language["startup_tab"])
        self.tabControl.add(self.frame_processes, text=current_language["process_tab"])
        self.tabControl.add(self.frame_network, text=current_language["network_tab"])
        self.tabControl.add(self.frame_services, text=current_language["services_tab"])
        self.tabControl.add(self.frame_ports, text=current_language["ports_tab"])
        self.tabControl.add(self.frame_about, text=current_language["about_tab"])
        self.tabControl.pack(expand=1, fill="both")

        self.tree_startup = self.create_treeview(self.frame_startup, ["Name", "File Path"])
        self.tree_processes = self.create_treeview(self.frame_processes, ["PID", "Name", "Path", "CPU %"])
        self.tree_network = self.create_treeview(self.frame_network, ["Address", "Port", "Status"])
        self.tree_services = self.create_treeview(self.frame_services, ["Service Name", "Status"])
        self.tree_ports = self.create_treeview(self.frame_ports, ["Port", "Status"])

        self.label_about = tk.Label(self.frame_about, text=current_language["about_text"], font=("Arial", 12))
        self.label_about.pack(pady=20)

        self.load_all_data()

        ttk.Button(root, text=current_language["log_button"], command=self.save_log).pack(pady=5)

    def create_treeview(self, parent, columns):
        tree = ttk.Treeview(parent, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        return tree

    def load_all_data(self):
        self.startup_programs = self.load_startup_items()
        self.running_processes = self.load_process_list()
        self.network_connections = self.load_network_connections()
        self.windows_services = self.load_services()
        self.open_ports = self.load_open_ports()

    def load_startup_items(self):
        self.tree_startup.delete(*self.tree_startup.get_children())
        programs = []
        registry_paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
        ]
        for hive, path in registry_paths:
            try:
                with winreg.OpenKey(hive, path) as reg_key:
                    index = 0
                    while True:
                        try:
                            name, value, _ = winreg.EnumValue(reg_key, index)
                            programs.append({"name": name, "path": value})
                            self.tree_startup.insert("", "end", values=(name, value))
                            index += 1
                        except OSError:
                            break
            except Exception:
                continue
        return programs

    def load_process_list(self):
        self.tree_processes.delete(*self.tree_processes.get_children())
        processes = []
        for proc in psutil.process_iter(attrs=['pid', 'name', 'exe', 'cpu_percent']):
            try:
                data = {"pid": proc.info['pid'], "name": proc.info['name'], "path": proc.info['exe'], "cpu": f"{proc.info['cpu_percent']}%"}
                processes.append(data)
                self.tree_processes.insert("", "end", values=(data["pid"], data["name"], data["path"], data["cpu"]))
            except Exception:
                continue
        return processes

    def load_network_connections(self):
        self.tree_network.delete(*self.tree_network.get_children())
        connections = []
        for conn in psutil.net_connections(kind="inet"):
            try:
                address = conn.laddr.ip
                port = conn.laddr.port
                status = conn.status
                connections.append({"address": address, "port": port, "status": status})
                self.tree_network.insert("", "end", values=(address, port, status))
            except Exception:
                continue
        return connections

    def load_services(self):
        self.tree_services.delete(*self.tree_services.get_children())
        services = []
        for service in psutil.win_service_iter():
            try:
                name = service.name()
                status = service.status()
                services.append({"name": name, "status": status})
                self.tree_services.insert("", "end", values=(name, status))
            except Exception:
                continue
        return services

    def load_open_ports(self):
        self.tree_ports.delete(*self.tree_ports.get_children())
        open_ports = []
        for conn in psutil.net_connections(kind="inet"):
            try:
                if conn.status == "LISTEN":
                    port = conn.laddr.port
                    open_ports.append({"port": port, "status": "Listening"})
                    self.tree_ports.insert("", "end", values=(port, "Listening"))
            except Exception:
                continue
        return open_ports

    def save_log(self):
        log_data = {
            "timestamp": str(datetime.datetime.now()),
            "startup_programs": self.startup_programs,
            "running_processes": self.running_processes,
            "network_connections": self.network_connections,
            "windows_services": self.windows_services,
            "open_ports": self.open_ports,
        }

        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(log_data, file, indent=4)
            messagebox.showinfo("Success", current_language["file_saved"] + file_path)


if __name__ == "__main__":
    root = tk.Tk()
    app = SpyScanApp(root)
    root.mainloop()
