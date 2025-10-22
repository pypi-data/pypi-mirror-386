#!/usr/bin/python3
import pathlib
import tkinter as tk
import pygubu

PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "allwidgets.ui"
RESOURCE_PATHS = [PROJECT_PATH]


class AppUI:
    def __init__(
        self,
        master=None,
        translator=None,
        on_first_object_cb=None,
        data_pool=None,
    ):
        self.builder = pygubu.Builder(
            translator=translator,
            on_first_object=on_first_object_cb,
            data_pool=data_pool,
        )
        self.builder.add_resource_paths(RESOURCE_PATHS)
        self.builder.add_from_file(PROJECT_UI)
        # Main widget
        self.mainwindow = self.builder.get_object("themedtkinterframe1", master)

        self.var_checkbox1: tk.BooleanVar = None
        self.var_checkbox2: tk.BooleanVar = None
        self.var_radiobutton: tk.StringVar = None
        self.var_togglebutton: tk.BooleanVar = None
        self.var_textinput: tk.StringVar = None
        self.var_spinboxnum: tk.IntVar = None
        self.var_spinboxcolor: tk.StringVar = None
        self.var_combobox: tk.StringVar = None
        self.var_optionmenu: tk.StringVar = None
        self.var_slider: tk.IntVar = None
        self.builder.import_variables(self)

        self.builder.connect_callbacks(self)

    def run(self):
        self.mainwindow.mainloop()

    def printcheckboxvars(self):
        pass

    def handleButtonClick(self):
        pass

    def validateText(self):
        pass

    def optionmenu_clicked(self, value):
        pass


if __name__ == "__main__":
    root = tk.Tk()
    app = AppUI(root)
    app.run()
