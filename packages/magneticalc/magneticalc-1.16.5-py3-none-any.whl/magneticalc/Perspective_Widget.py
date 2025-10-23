""" Perspective_Widget module. """

#  ISC License
#
#  Copyright (c) 2020–2022, Paul Wilhelm, M. Sc. <anfrage@paulwilhelm.de>
#
#  Permission to use, copy, modify, and/or distribute this software for any
#  purpose with or without fee is hereby granted, provided that the above
#  copyright notice and this permission notice appear in all copies.
#
#  THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
#  WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
#  MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
#  ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
#  WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
#  ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
#  OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

from __future__ import annotations
from typing import Dict
from functools import partial
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout
from magneticalc.QtWidgets2.QGroupBox2 import QGroupBox2
from magneticalc.QtWidgets2.QHLine import QHLine
from magneticalc.QtWidgets2.QLabel2 import QLabel2
from magneticalc.QtWidgets2.QPushButton2 import QPushButton2
from magneticalc.Debug import Debug
from magneticalc.Perspective_Presets import Perspective_Presets
from magneticalc.Theme import Theme


class Perspective_Widget(QGroupBox2):
    """ Perspective_Widget class. """

    def __init__(
            self,
            gui: GUI  # type: ignore
    ) -> None:
        """
        Populates the widget.

        @param gui: GUI
        """
        QGroupBox2.__init__(self, "Perspective", color=Theme.DarkColor)
        Debug(self, ": Init", init=True)
        self.gui = gui

        planar_perspective_layout = QVBoxLayout()
        for preset in Perspective_Presets.List:
            button = QPushButton2(preset["id"], "", clicked=partial(self.set_perspective, preset))
            planar_perspective_layout.addWidget(button)
        self.addLayout(planar_perspective_layout)

        self.addWidget(QHLine())
        xyz_hint_layout = QHBoxLayout()
        xyz_hint_layout.addWidget(QLabel2("Axis Colors:", italic=True, color=Theme.LiteColor))
        xyz_hint_layout.addWidget(QLabel2("X", bold=True, color="#cc0000", align_right=True))
        xyz_hint_layout.addWidget(QLabel2("Y", bold=True, color="#00cc00", align_right=True))
        xyz_hint_layout.addWidget(QLabel2("Z", bold=True, color="#0000cc", align_right=True))
        self.addLayout(xyz_hint_layout)

    def reload(self) -> None:
        """
        Reloads the widget.
        """
        Debug(self, ".reload()", refresh=True)

    def set_perspective(self, preset: Dict) -> None:
        """
        Sets display perspective.

        @param preset: Perspective preset (parameters, see VisPyCanvas module)
        """
        Debug(self, ".set_perspective()")
        self.gui.project.set_float("azimuth", preset["azimuth"])
        self.gui.project.set_float("elevation", preset["elevation"])
        self.gui.vispy_canvas.view_main.camera.azimuth = preset["azimuth"]
        self.gui.vispy_canvas.view_main.camera.elevation = preset["elevation"]
        self.gui.redraw()
