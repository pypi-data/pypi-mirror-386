""" Field_Widget module. """

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
from typing import Optional
from functools import partial
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QSizePolicy
from PyQt5.QtWidgets import QButtonGroup, QCheckBox, QRadioButton
from magneticalc.QtWidgets2.QDoubleSpinBox2 import QDoubleSpinBox2
from magneticalc.QtWidgets2.QGroupBox2 import QGroupBox2
from magneticalc.QtWidgets2.QHLine import QHLine
from magneticalc.QtWidgets2.QIconLabel import QIconLabel
from magneticalc.QtWidgets2.QLabel2 import QLabel2
from magneticalc.Debug import Debug
from magneticalc.Field_Types import Field_Types_Names_Map
from magneticalc.Metric import Metric
from magneticalc.ModelAccess import ModelAccess
from magneticalc.Theme import Theme


class Field_Widget(QGroupBox2):
    """ Field_Widget class. """

    # Spinbox limits
    DistanceLimitMin = 0.0001
    DistanceLimitMax = 1
    DistanceLimitStep = 0.0001
    DistanceLimitPrecision = 4

    def __init__(
            self,
            gui: GUI  # type: ignore
    ) -> None:
        """
        Populates the widget.

        @param gui: GUI
        """
        QGroupBox2.__init__(self, "Field", color=Theme.DarkColor)
        Debug(self, ": Init", init=True)
        self.gui = gui

        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

        self.addLayout(QIconLabel("Type", "mdi.tune-variant", color=Theme.DarkColor))

        field_type_layout_left = QVBoxLayout()
        field_type_layout_right = QVBoxLayout()

        self.field_type_group = QButtonGroup()
        field_type_radiobuttons = {}
        self.field_type_checkboxes = {}
        for field_type, field_name in Field_Types_Names_Map.items():
            field_type_radiobuttons[field_type] = QRadioButton(" " + field_name)
            field_type_layout_left.addWidget(field_type_radiobuttons[field_type])
            self.field_type_checkboxes[field_type] = QCheckBox(" Cached")
            self.field_type_checkboxes[field_type].setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
            self.field_type_checkboxes[field_type].setEnabled(False)
            field_type_layout_right.addWidget(self.field_type_checkboxes[field_type])
            self.field_type_group.addButton(field_type_radiobuttons[field_type])

        field_type_layout = QHBoxLayout()
        field_type_layout.addLayout(field_type_layout_left)
        field_type_layout.addLayout(field_type_layout_right)
        self.addLayout(field_type_layout)

        for i, button in enumerate(self.field_type_group.buttons()):
            button.toggled.connect(partial(self.on_field_type_changed, i))

        total_calculations_layout = QHBoxLayout()
        self.total_calculations_label = QLabel2("N/A", color=Theme.MainColor, align_right=True)
        total_calculations_layout.addWidget(QLabel2("Total calculations:", italic=True, color=Theme.LiteColor))
        total_calculations_layout.addWidget(self.total_calculations_label)
        self.addLayout(total_calculations_layout)

        # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

        self.addWidget(QHLine())

        self.addLayout(QIconLabel("Distance Limit", "mdi.ruler", color=Theme.DarkColor))
        self.distance_limit_spinbox = QDoubleSpinBox2(
            gui=self.gui,
            minimum=self.DistanceLimitMin,
            maximum=self.DistanceLimitMax,
            step=self.DistanceLimitStep,
            precision=self.DistanceLimitPrecision,
            value=0,
            value_changed=lambda: self.set_field(_distance_limit_=self.distance_limit_spinbox.value())
        )
        distance_limit_layout = QHBoxLayout()
        distance_limit_layout.addWidget(self.distance_limit_spinbox)
        distance_limit_layout.addWidget(QLabel2("cm", expand=False))
        self.addLayout(distance_limit_layout)

        total_skipped_calculations_layout = QHBoxLayout()
        self.total_skipped_calculations_label = QLabel2("N/A", color=Theme.MainColor, align_right=True)
        total_skipped_calculations_layout.addWidget(
            QLabel2("Total skipped calculations:", italic=True, color=Theme.LiteColor)
        )
        total_skipped_calculations_layout.addWidget(self.total_skipped_calculations_label)
        self.addLayout(total_skipped_calculations_layout)

    def reload(self) -> None:
        """
        Reloads the widget.
        """
        Debug(self, ".reload()", refresh=True)

        self.blockSignals(True)

        field_type = self.gui.project.get_int("field_type")
        for i, button in enumerate(self.field_type_group.buttons()):
            button.setChecked(i == field_type)

        self.distance_limit_spinbox.setValue(self.gui.project.get_float("field_distance_limit"))

        self.blockSignals(False)

        # Initially load field from project
        self.set_field(recalculate=False, invalidate=False)

        self.update()

    def update(self) -> None:
        """
        Updates this widget.
        """
        Debug(self, ".update()", refresh=True)

        self.update_labels()
        self.update_controls()

    def update_labels(self) -> None:
        """
        Updates the labels.
        """
        if self.gui.model.field.valid:
            self.total_calculations_label.setText(str(self.gui.model.field.total_calculations))
            self.total_skipped_calculations_label.setText(str(self.gui.model.field.total_skipped_calculations))
        else:
            self.total_calculations_label.setText("N/A")
            self.total_skipped_calculations_label.setText("N/A")

    def update_controls(self) -> None:
        """
        Updates the controls.
        """
        for field_type in Field_Types_Names_Map:
            self.field_type_checkboxes[field_type].setChecked(self.gui.model.get_valid_field(field_type) is not None)

        self.set_color(Theme.MainColor if self.gui.model.field.valid else Theme.FailureColor)

    # ------------------------------------------------------------------------------------------------------------------

    def on_field_type_changed(self, field_type: int, checked: bool) -> None:
        """
        Gets called when the field type changed.

        @param field_type: Field type
        @param checked: Boolean
        """
        if self.signalsBlocked():
            return

        if not checked:
            return

        self.set_field(_field_type_=field_type, invalidate=False)

    # ------------------------------------------------------------------------------------------------------------------

    def set_field(
            self,
            _field_type_: Optional[int] = None,
            _distance_limit_: Optional[float] = None,
            invalidate: bool = True,
            recalculate: bool = True
    ) -> None:
        """
        Sets the field. This will replace the currently set field in the model.
        Any underscored parameter may be left set to None in order to load its default value.

        @param _field_type_: Field type
        @param _distance_limit_: Distance limit
        @param invalidate: Enable to invalidate this model hierarchy level
        @param recalculate: Enable to trigger final recalculation
        """
        if self.signalsBlocked():
            return

        Debug(self, ".set_field()")

        with ModelAccess(self.gui, recalculate):

            field_type = self.gui.project.set_get_int("field_type", _field_type_)
            distance_limit = self.gui.project.set_get_float("field_distance_limit", _distance_limit_)

            self.gui.model.set_field(
                invalidate=invalidate,
                field_type=field_type,
                distance_limit=distance_limit,
                length_scale=Metric.LengthScale
            )
