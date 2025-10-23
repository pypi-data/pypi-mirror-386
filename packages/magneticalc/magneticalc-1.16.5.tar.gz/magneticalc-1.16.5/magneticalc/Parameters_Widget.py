""" Parameters_Widget module. """

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
import numpy as np
from si_prefix import si_format
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout
from magneticalc.QtWidgets2.QGroupBox2 import QGroupBox2
from magneticalc.QtWidgets2.QLabel2 import QLabel2
from magneticalc.Debug import Debug
from magneticalc.Field_Types import FIELD_TYPE_A, FIELD_TYPE_B
from magneticalc.Theme import Theme


class Parameters_Widget(QGroupBox2):
    """ Parameters_Widget class. """

    # Formatting settings
    ValuePrecision = 1

    def __init__(
            self,
            gui: GUI  # type: ignore
    ) -> None:
        """
        Populates the widget.

        @param gui: GUI
        """
        QGroupBox2.__init__(self, "Parameters", color=Theme.DarkColor)
        Debug(self, ": Init", init=True)
        self.gui = gui

        self.gui.model.set_parameters(invalidate=False)

        results_layout = QHBoxLayout()
        results_left = QVBoxLayout()
        results_middle = QVBoxLayout()
        results_right = QVBoxLayout()
        results_layout.addLayout(results_left)
        results_layout.addLayout(results_middle)
        results_layout.addLayout(results_right)
        self.addLayout(results_layout)

        results_left.addWidget(QLabel2("Wire length:"))
        self.wire_length_value_label = QLabel2("", color=Theme.MainColor, align_right=True)
        results_middle.addWidget(self.wire_length_value_label)
        self.wire_length_units_label = QLabel2("N/A", color=Theme.MainColor, expand=False)
        results_right.addWidget(self.wire_length_units_label)

        results_left.addWidget(QLabel2("Magnetic Dipole Moment:"))
        self.magnetic_dipole_moment_value_label = QLabel2("", color=Theme.MainColor, align_right=True)
        results_middle.addWidget(self.magnetic_dipole_moment_value_label)
        self.magnetic_dipole_moment_units_label = QLabel2("N/A", color=Theme.MainColor, expand=False)
        results_right.addWidget(self.magnetic_dipole_moment_units_label)

        results_left.addWidget(QLabel2("Energy:"))
        self.energy_value_label = QLabel2("", color=Theme.MainColor, align_right=True)
        results_middle.addWidget(self.energy_value_label)
        self.energy_units_label = QLabel2("N/A", color=Theme.MainColor, expand=False)
        results_right.addWidget(self.energy_units_label)

        results_left.addWidget(QLabel2("Self-inductance:"))
        self.self_inductance_value_label = QLabel2("", color=Theme.MainColor, align_right=True)
        results_middle.addWidget(self.self_inductance_value_label)
        self.self_inductance_units_label = QLabel2("N/A", color=Theme.MainColor, expand=False)
        results_right.addWidget(self.self_inductance_units_label)

        self.update()

    def reload(self) -> None:
        """
        Reloads the widget.
        """
        Debug(self, ".reload()", refresh=True)

    # ------------------------------------------------------------------------------------------------------------------

    def update(self) -> None:
        """
        Updates the widget.
        """
        Debug(self, ".update()", refresh=True)

        self.update_labels()
        self.update_controls()

    def update_labels(self) -> None:
        """
        Updates the labels.
        """
        Debug(self, ".update_labels()", refresh=True)

        if self.gui.model.parameters.valid:

            self.wire_length_value_label.set(
                f"{self.gui.model.wire.length:.2f}", color=Theme.MainColor, bold=True
            )
            self.wire_length_units_label.set("cm", color=Theme.MainColor, bold=True)

            if self.gui.model.field.type == FIELD_TYPE_A:

                self.energy_value_label.set("", color=Theme.MainColor)
                self.energy_units_label.set("N/A", color=Theme.MainColor)

                self.self_inductance_value_label.set("", color=Theme.MainColor)
                self.self_inductance_units_label.set("N/A", color=Theme.MainColor)

                self.magnetic_dipole_moment_value_label.set("", color=Theme.MainColor)
                self.magnetic_dipole_moment_units_label.set("N/A", color=Theme.MainColor)

            elif self.gui.model.field.type == FIELD_TYPE_B:

                energy_value = self.gui.model.parameters.energy
                if np.isnan(energy_value):
                    energy_value = "NaN NaN"
                else:
                    energy_value = si_format(
                        energy_value,
                        precision=self.ValuePrecision,
                        exp_format_str="{value}e{expof10} "
                    ) + "J"
                self.energy_value_label.set(energy_value.split(" ")[0], color=Theme.MainColor, bold=True)
                self.energy_units_label.set(energy_value.split(" ")[1], color=Theme.MainColor, bold=True)

                self_inductance_value = self.gui.model.parameters.self_inductance
                if np.isnan(self_inductance_value):
                    self_inductance_value = "NaN NaN"
                else:
                    self_inductance_value = si_format(
                        self_inductance_value,
                        precision=self.ValuePrecision,
                        exp_format_str="{value}e{expof10} "
                    ) + "H"
                self.self_inductance_value_label.set(
                    self_inductance_value.split(" ")[0], color=Theme.MainColor, bold=True
                )
                self.self_inductance_units_label.set(
                    self_inductance_value.split(" ")[1], color=Theme.MainColor, bold=True
                )

                magnetic_dipole_moment_value = self.gui.model.parameters.magnetic_dipole_moment
                if np.isnan(magnetic_dipole_moment_value):
                    magnetic_dipole_moment_value = "NaN NaN"
                else:
                    magnetic_dipole_moment_value = si_format(
                        magnetic_dipole_moment_value,
                        precision=self.ValuePrecision,
                        exp_format_str="{value}e{expof10} "
                    ) + "A·m²"
                self.magnetic_dipole_moment_value_label.set(
                    magnetic_dipole_moment_value.split(" ")[0], color=Theme.MainColor, bold=True
                )
                self.magnetic_dipole_moment_units_label.set(
                    magnetic_dipole_moment_value.split(" ")[1], color=Theme.MainColor, bold=True
                )

        else:

            self.wire_length_value_label.set("", color=Theme.MainColor)
            self.wire_length_units_label.set("N/A", color=Theme.MainColor)

            self.energy_value_label.set("", color=Theme.MainColor)
            self.energy_units_label.set("N/A", color=Theme.MainColor)

            self.self_inductance_value_label.set("", color=Theme.MainColor)
            self.self_inductance_units_label.set("N/A", color=Theme.MainColor)

            self.magnetic_dipole_moment_value_label.set("", color=Theme.MainColor)
            self.magnetic_dipole_moment_units_label.set("N/A", color=Theme.MainColor)

    def update_controls(self) -> None:
        """
        Updates the controls.
        """
        Debug(self, ".update_controls()", refresh=True)

        self.set_color(Theme.MainColor if self.gui.model.parameters.valid else Theme.FailureColor)
