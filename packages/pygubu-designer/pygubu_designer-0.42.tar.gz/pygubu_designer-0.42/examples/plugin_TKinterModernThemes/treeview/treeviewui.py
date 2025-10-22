#!/usr/bin/python3
import pathlib
import tkinter as tk
import pygubu

PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "treeview.ui"
RESOURCE_PATHS = [PROJECT_PATH]


class AppUI:
    def __init__(self, master=None, data_pool=None):
        self.builder = pygubu.Builder(data_pool=data_pool)
        self.builder.add_resource_paths(RESOURCE_PATHS)
        self.builder.add_from_file(PROJECT_UI)
        # Main widget
        self.mainwindow = self.builder.get_object("themedtkinterframe1", master)
        self.builder.connect_callbacks(self)

    def run(self):
        self.mainwindow.mainloop()

    def print_selected_cmd(self):
        pass


if __name__ == "__main__":
    root = tk.Tk()
    app = AppUI(root)
    app.run()
