""" Parameters module. """

#  ISC License
#
#  Copyright (c) 2020–2022, Paul Wilhelm <anfrage@paulwilhelm.de>
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
from typing import Callable
import numpy as np
from numba import jit, prange
from magneticalc.Backend_Types import get_jit_enabled
from magneticalc.ConditionalDecorator import ConditionalDecorator
from magneticalc.Constants import Constants
from magneticalc.Debug import Debug
from magneticalc.Field_Types import FIELD_TYPE_A, FIELD_TYPE_B
from magneticalc.Metric import Metric
from magneticalc.Validatable import Validatable, require_valid, validator


class Parameters(Validatable):
    """ Parameters class. """

    def __init__(self) -> None:
        """
        Initializes parameters class.
        """
        Validatable.__init__(self)
        Debug(self, ": Init", init=True)

        self._energy: float = 0.0
        self._self_inductance: float = 0.0
        self._magnetic_dipole_moment: float = 0.0

    def set(self, *args, **kwargs):
        """
        Sets the parameters
        """

    # ------------------------------------------------------------------------------------------------------------------

    def _get_squared_field(
            self,
            sampling_volume: SamplingVolume,  # type: ignore
            field: Field  # type: ignore
    ) -> float:
        """
        Returns the "squared" field scalar.

        @param sampling_volume: SamplingVolume
        @param field: B-field
        @return: Float
        """
        return self._get_squared_field_worker(sampling_volume.permeabilities, field.vectors)

    @staticmethod
    @ConditionalDecorator(get_jit_enabled(), jit, nopython=True, parallel=True)
    def _get_squared_field_worker(sampling_volume_permeabilities: np.ndarray, field_vectors: np.ndarray) -> float:
        """
        Returns the "squared" field scalar.

        @param sampling_volume_permeabilities: Ordered list of sampling volume's relative permeabilities µ_r
        @param field_vectors: Ordered list of 3D vectors (B-field)
        @return: Float
        """
        squared = 0
        for i in prange(len(field_vectors)):
            squared += np.dot(field_vectors[i], field_vectors[i] / sampling_volume_permeabilities[i])
        return squared

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _get_magnetic_dipole_moment(
            self, wire: Wire,  # type: ignore
            length_scale: float
    ) -> float:
        """
        Returns the magnetic dipole moment scalar.

        @param wire: Wire
        @param length_scale: Length scale (m)
        @return: Float
        """
        elements_center = np.array([element[0] for element in wire.elements])
        elements_direction = np.array([element[1] for element in wire.elements])
        vector = self._get_magnetic_dipole_moment_worker(elements_center, elements_direction, length_scale)
        return np.abs(wire.dc * np.linalg.norm(vector) / 2)

    @staticmethod
    @ConditionalDecorator(get_jit_enabled(), jit, nopython=True, parallel=True)
    def _get_magnetic_dipole_moment_worker(
            elements_center: np.ndarray,
            elements_direction: np.ndarray,
            length_scale: float
    ):
        """
        Returns the (unscaled) magnetic dipole moment vector.

        @param elements_center: Current element centers
        @param elements_direction: Current element directions
        @param length_scale: Length scale (m)
        @return: Magnetic dipole moment vector
        """
        squared = np.zeros(3)
        for i in prange(len(elements_center)):
            squared += np.cross(elements_center[i] * length_scale, elements_direction[i] * length_scale)
        return squared

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    @validator
    def recalculate(
            self,
            wire: Wire,  # type: ignore
            sampling_volume: SamplingVolume,  # type: ignore
            field: Field,  # type: ignore
            progress_callback: Callable
    ) -> bool:
        """
        Recalculates parameters.

        @param wire: Wire
        @param sampling_volume: SamplingVolume
        @param field: Field
        @param progress_callback: Progress callback
        @return: True (currently non-interruptable)
        """
        Debug(self, ".recalculate()")

        progress_callback(0)

        self._magnetic_dipole_moment = self._get_magnetic_dipole_moment(wire, Metric.LengthScale)

        progress_callback(33)

        if field.type == FIELD_TYPE_A:

            pass

        elif field.type == FIELD_TYPE_B:

            dV = (Metric.LengthScale / sampling_volume.resolution) ** 3  # Sampling volume element
            self._energy = self._get_squared_field(sampling_volume, field) * dV / Constants.mu_0

            progress_callback(66)

            self._self_inductance = self._energy / np.square(wire.dc)

        progress_callback(100)

        return True

    @property
    @require_valid
    def energy(self) -> float:
        """
        Returns calculated energy.

        @return: Float
        """
        return self._energy

    @property
    @require_valid
    def self_inductance(self) -> float:
        """
        Returns calculated self-inductance.

        @return: Float
        """
        return self._self_inductance

    @property
    @require_valid
    def magnetic_dipole_moment(self) -> float:
        """
        Returns calculated magnetic dipole moment.

        @return: Float
        """
        return self._magnetic_dipole_moment
