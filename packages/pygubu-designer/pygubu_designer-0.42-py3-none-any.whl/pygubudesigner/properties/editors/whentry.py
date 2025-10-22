#
# Copyright 2012-2022 Alejandro Autalán
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 3, as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranties of
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.

import tkinter as tk
import tkinter.ttk as ttk

from .propertyeditor import (
    PropertyEditor,
    register_editor,
)
from .dimensionentry import DimensionPropertyEditor


class WHPropertyEditor(PropertyEditor):
    def _create_ui(self):
        self._wlabel = w = ttk.Label(self, text="w:", font="TkSmallCaptionFont")
        w.grid(row=0, column=0)
        self._weditor = w = DimensionPropertyEditor(self)
        w.grid(row=0, column=1, sticky="we")
        w.parameters(width=4)

        self._wlabel = w = ttk.Label(self, text="h:", font="TkSmallCaptionFont")
        w.grid(row=0, column=2)
        self._heditor = w = DimensionPropertyEditor(self)
        w.grid(row=0, column=3, sticky="we")
        w.parameters(width=4)

        self._weditor.bind("<<PropertyChanged>>", self._on_variable_changed)
        self._heditor.bind("<<PropertyChanged>>", self._on_variable_changed)

        self.rowconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(3, weight=1)

    def _get_value(self):
        value = ""
        if self._weditor.value != "" and self._heditor.value != "":
            value = f"{self._weditor.value}|{self._heditor.value}"
        return value

    def _set_value(self, value):
        if "|" in value:
            width, heigth = value.split("|")
            self._weditor.edit(width)
            self._heditor.edit(heigth)
        else:
            self._weditor.edit("")
            self._heditor.edit("")

    def _validate(self):
        isvalid = False
        w = self._weditor.value
        h = self._heditor.value
        if w == "" and h == "":
            isvalid = True
        else:
            try:
                wpx = int(self.winfo_fpixels(w))
                hpx = int(self.winfo_fpixels(h))
                if wpx >= 0 and hpx >= 0:
                    isvalid = True
            except (ValueError, tk.TclError):
                pass
        self.show_invalid(not isvalid)
        return isvalid


register_editor("whentry", WHPropertyEditor)
