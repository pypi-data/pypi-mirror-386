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

import sys
import platform
import tkinter as tk
import tkinter.font


# in-place prettyprint formatter
def indent(elem, level=0):
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def treeview_print(tree, root=""):
    def tree_print(tree, root):
        children = tree.get_children(root)
        if root != "" and children:
            print(root)
        for item in children:
            tree_print(tree, item)

    tree_print(tree, root)


class BraceMessage:
    """Helper class to use braces {} in log messages"""

    def __init__(self, fmt, *args, **kwargs):
        self.fmt = fmt
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        return self.fmt.format(*self.args, **self.kwargs)


# Helper to translate log messages with braces
trlog = BraceMessage


def virtual_event(event_name):
    """Generate virtual event event_name"""

    def virtual_event_gen(event):
        event.widget.event_generate(event_name)

    return virtual_event_gen


def menu_iter_children(menu):
    """Iterates all menu items (including submenus).
    Returns (menu, itemtype, index)"""
    count = menu.index(tk.END)
    if count is not None:
        cascades = []
        for i in range(0, count + 1):
            itemtype = menu.type(i)
            if itemtype == "cascade":
                cascade = menu.nametowidget(menu.entrycget(i, "menu"))
                cascades.append(cascade)
            yield (menu, itemtype, i)
        for m in cascades:
            yield from menu_iter_children(m)


def enable_dpi():
    """Enable DPI Awareness."""

    if platform.system() == "Windows":
        import ctypes

        if platform.release() == "7":
            ctypes.windll.user32.SetProcessDPIAware()
        else:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)


def get_linespace(root=None, *, font_name=None, scale_factor=1) -> int:
    family = "TkDefaultFont" if font_name is None else font_name
    if sys.version_info >= (3, 10):
        font = tk.font.nametofont(family, root)
    else:
        font = tk.font.nametofont(family)
    linespace = font.metrics()["linespace"]
    return int(linespace * scale_factor)
