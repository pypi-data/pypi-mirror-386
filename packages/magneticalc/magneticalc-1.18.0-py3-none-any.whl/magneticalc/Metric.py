""" Metric module. """

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
from magneticalc.Norm_Types import *
from typing import Dict, List, Callable, Tuple
import numpy as np
from numba import jit, prange
from magneticalc.Assert_Dialog import Assert_Dialog
from magneticalc.Backend_Types import get_jit_enabled
from magneticalc.ConditionalDecorator import ConditionalDecorator
from magneticalc.Debug import Debug
from magneticalc.Validatable import Validatable, require_valid, validator


@ConditionalDecorator(get_jit_enabled(), jit, nopython=True, parallel=False)
def metric_norm(norm_type: int, vector: np.ndarray) -> float:
    """
    Calculates the selected norm of some vector.

    Note: For JIT to work, this must be declared at the top level.

    @param norm_type: Norm type
    @param vector: 3D vector
    @return: Scalar if successful, np.inf on error
    """
    if norm_type == NORM_TYPE_X:
        value = vector[0]
    elif norm_type == NORM_TYPE_Y:
        value = vector[1]
    elif norm_type == NORM_TYPE_Z:
        value = vector[2]
    elif norm_type == NORM_TYPE_RADIUS:
        value = np.sqrt(vector[0] ** 2 + vector[1] ** 2 + vector[2] ** 2)
    elif norm_type == NORM_TYPE_RADIUS_X:
        value = np.abs(vector[0])
    elif norm_type == NORM_TYPE_RADIUS_Y:
        value = np.abs(vector[1])
    elif norm_type == NORM_TYPE_RADIUS_Z:
        value = np.abs(vector[2])
    elif norm_type == NORM_TYPE_RADIUS_XY:
        value = np.sqrt(vector[0] ** 2 + vector[1] ** 2)
    elif norm_type == NORM_TYPE_RADIUS_XZ:
        value = np.sqrt(vector[1] ** 2 + vector[2] ** 2)
    elif norm_type == NORM_TYPE_RADIUS_YZ:
        value = np.sqrt(vector[2] ** 2 + vector[0] ** 2)
    elif norm_type == NORM_TYPE_ANGLE_XY:
        value = (np.arctan2(vector[0], vector[1]) + np.pi) / np.pi / 2
    elif norm_type == NORM_TYPE_ANGLE_XZ:
        value = (np.arctan2(vector[0], vector[2]) + np.pi) / np.pi / 2
    elif norm_type == NORM_TYPE_ANGLE_YZ:
        value = (np.arctan2(vector[1], vector[2]) + np.pi) / np.pi / 2
    elif norm_type == NORM_TYPE_DIVERGENCE:
        # Invalid norm ID for metric_norm(); divergence must be calculated using metric_divergence()
        value = np.inf
    else:
        # Invalid norm ID
        value = np.inf

    return value


@ConditionalDecorator(get_jit_enabled(), jit, nopython=True, parallel=False)
def metric_divergence(neighborhood_vectors: np.ndarray, dL: float, polarity: int) -> float:
    """
    Calculates the divergence of a sampling volume neighborhood.

    Note: For JIT to work, this must be declared at the top level.

    @param neighborhood_vectors: Sampling volume neighborhood vectors (six 3D vectors)
    @param dL: Length element
    @param polarity: Polarity filter (-1: Keep values <= 0; 0: Keep all values; +1: Keep values >= 0)
    """
    dxp = neighborhood_vectors[0][0]
    dxn = neighborhood_vectors[3][0]

    dyp = neighborhood_vectors[1][1]
    dyn = neighborhood_vectors[4][1]

    dzp = neighborhood_vectors[2][2]
    dzn = neighborhood_vectors[5][2]

    value = (dxp - dxn + dyp - dyn + dzp - dzn) / 2 / dL

    if polarity == -1:
        if value > 0:
            return np.NaN
        else:
            return -value   # Keep divergence positive, especially for use as alpha metric
    elif polarity == +1:
        if value < 0:
            return np.NaN
        else:
            return value
    else:
        return value


@ConditionalDecorator(get_jit_enabled(), jit, nopython=True, parallel=False)
def color_map_divergent(color_normalized: float) -> np.ndarray:
    """
    Maps normalized value to color, divergent.

    Note: For JIT to work, this must be declared at the top level.

    @param color_normalized: Normalized color value
    @return: R, G, B
    """
    rgb_0 = np.array([0x00, 0xff, 0xfe]) / 255
    rgb_1 = np.array([0xff, 0x22, 0xf9]) / 255
    return rgb_0 + (rgb_1 - rgb_0) * color_normalized


@ConditionalDecorator(get_jit_enabled(), jit, nopython=True, parallel=False)
def color_map_cyclic(color_normalized: float) -> np.ndarray:
    """
    Maps normalized value to color, cyclic.

    Note: For JIT to work, this must be declared at the top level.

    @param color_normalized: Normalized color value
    @return: R, G, B
    """
    hue = (color_normalized + 1 / 6) % 1
    x = hue * 6
    r = 1 if 0 <= x <= 1 or 5 <= x <= 6 else x - 4 if 4 <= x <= 5 else 2 - x if 1 <= x <= 2 else 0
    g = 1 if 1 <= x <= 3 else x if 0 <= x <= 1 else 4 - x if 3 <= x <= 4 else 0
    b = 1 if 3 <= x <= 5 else x - 2 if 2 <= x <= 3 else 6 - x if 5 <= x <= 6 else 0
    return np.array([r, g, b])


class Metric(Validatable):
    """
    Provides different metrics, used for mapping some field vector properties to some color and alpha range.
    """

    # Length scale
    LengthScale = 1e-2  # m  (1 cm)

    # Minimum argument limit for logarithmic scaling
    LogNormMin = 1e-12

    def __init__(self) -> None:
        """
        Initializes an empty metric.

        This class holds a pair of metric presets.
        Using these metric presets, colors (including alpha channel) and field limits are calculated.
        """
        Validatable.__init__(self)
        Debug(self, ": Init", init=True)

        # Parameters
        self.color_preset = {}
        self.alpha_preset = {}

        # Results
        self._colors: np.ndarray = np.array([])
        self._limits: Dict = {}

    def set(
            self,
            color_preset: Dict,
            alpha_preset: Dict
    ) -> None:
        """
        Sets the parameters.

        @param color_preset: Color metric preset (dictionary)
        @param alpha_preset: Alpha metric preset (dictionary)
        """
        self.color_preset = color_preset
        self.alpha_preset = alpha_preset

    # ------------------------------------------------------------------------------------------------------------------

    @staticmethod
    @ConditionalDecorator(get_jit_enabled(), jit, nopython=True, parallel=True)
    def _norm_worker(norm_type: int, vectors: np.ndarray) -> np.ndarray:
        """
        Calculates the norm values of a list of vectors.

        @param norm_type: Norm type
        @param vectors: Ordered list of 3D vectors
        @return: Norm values
        """
        values = np.zeros(len(vectors))

        for i in prange(len(vectors)):
            values[i] = metric_norm(norm_type, vectors[i])

        return values

    @staticmethod
    @ConditionalDecorator(get_jit_enabled(), jit, nopython=True, parallel=True)
    def _divergence_worker(
            sampling_volume_neighborhood_indices: List[np.ndarray],
            vectors: np.ndarray,
            dL: int,
            polarity: int
    ) -> np.ndarray:
        """
        Calculates the divergence values of a list of vectors.

        @param sampling_volume_neighborhood_indices: Ordered list of sampling volume neighborhood indices
        @param vectors: Ordered list of 3D vectors
        @param dL: Length element
        @param polarity: Polarity filter (-1: Keep values <= 0; 0: Keep all values; +1: Keep values >= 0)
        @return: Norm values
        """
        values = np.zeros(len(vectors))

        for i in prange(len(vectors)):

            neighbor_vectors = []
            for index in sampling_volume_neighborhood_indices[i]:
                if index != -1:
                    neighbor_vectors.append(vectors[index])
                else:
                    neighbor_vectors = None
                    break

            if neighbor_vectors is None:
                values[i] = np.nan  # At least one neighbor is out of bounds
            else:
                values[i] = metric_divergence(neighbor_vectors, dL, polarity)

        return values

    @staticmethod
    @ConditionalDecorator(get_jit_enabled(), jit, nopython=True, parallel=True)
    def _normalize_worker(
            color_map_id: str,
            color_is_log: bool,
            color_norm_values,
            color_norm_min: float,
            color_norm_max: float,
            alpha_is_log: bool,
            alpha_norm_values: np.ndarray,
            alpha_norm_min: float,
            alpha_norm_max: float,
            colors: np.ndarray
    ) -> np.ndarray:
        """
        Normalizes color and alpha norm values, populates final color values.

        @param color_map_id: Color map ID
        @param color_is_log: Selects logarithmic normalizer for color
        @param color_norm_values: Color norm values
        @param color_norm_min: Minimum color norm value
        @param color_norm_max: Maximum color norm value
        @param alpha_is_log: Selects logarithmic normalizer for alpha
        @param alpha_norm_values: Alpha norm values
        @param alpha_norm_min: Minimum alpha norm value
        @param alpha_norm_max: Maximum alpha norm value
        @param colors: Color value list to populate (list of 4D vectors)
        @return: Color values (list of 4D vectors)
        """

        # (1) Calculate color and alpha normalization
        # (2) Calculate colormap and assemble final color/alpha values
        #     Note: Of course, the alpha metric colormap is ignored

        for i in prange(len(color_norm_values)):

            color_normalized = color_norm_values[i]

            if np.isnan(color_normalized):
                # Replace NaN by minimum value
                color_normalized = color_norm_min
            else:
                # Clip before normalizing, needed for logarithmic normalization
                if color_normalized < color_norm_min:
                    color_normalized = color_norm_min
                elif color_normalized < color_norm_min:
                    color_normalized = color_norm_min

            color_normalized = (color_normalized - color_norm_min) / (color_norm_max - color_norm_min)
            if color_is_log:
                color_normalized = np.exp(color_normalized) / np.exp(1)

            if color_map_id == 0:
                # Divergent colormap
                rgb = color_map_divergent(color_normalized)
            else:
                # Cyclic colormap
                rgb = color_map_cyclic(color_normalized)

            # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

            alpha_normalized = alpha_norm_values[i]

            if np.isnan(alpha_normalized):
                # Replace NaN by minimum value
                alpha_normalized = alpha_norm_min
            else:
                # Clip before normalizing, needed for logarithmic normalization
                if alpha_normalized < alpha_norm_min:
                    alpha_normalized = alpha_norm_min
                elif alpha_normalized > alpha_norm_max:
                    alpha_normalized = alpha_norm_max

            alpha_normalized = (alpha_normalized - alpha_norm_min) / (alpha_norm_max - alpha_norm_min)
            if alpha_is_log:
                alpha_normalized = np.exp(alpha_normalized) / np.exp(1)

            colors[i] = np.array([rgb[0], rgb[1], rgb[2], alpha_normalized])

        return colors

    @validator
    def recalculate(
            self,
            sampling_volume: SamplingVolume,  # type: ignore
            field: Field,  # type: ignore
            progress_callback: Callable
    ) -> bool:
        """
        Recalculates color and alpha values for field.

        @param sampling_volume: SamplingVolume
        @param field: Field
        @param progress_callback: Progress callback
        @return: True (currently non-interruptable)
        """
        Debug(self, ".recalculate()")

        n = field.vectors_count

        progress_callback(0)

        # Sampling volume length element (only needed for divergence metric)
        dL = Metric.LengthScale / sampling_volume.resolution

        # Calculate color metric values
        if self.color_preset["norm_type"] == NORM_TYPE_DIVERGENCE:
            # Calculate divergence
            color_norm_values = self._divergence_worker(
                sampling_volume.neighbor_indices,
                field.vectors,
                dL,
                self.color_preset["polarity"]
            )
        else:
            # Calculate other norm
            color_norm_values = self._norm_worker(
                self.color_preset["norm_type"],
                field.vectors
            )

        progress_callback(25)

        # Calculate alpha metric values
        if self.alpha_preset["norm_type"] == NORM_TYPE_DIVERGENCE:
            # Calculate divergence
            alpha_norm_values = self._divergence_worker(
                sampling_volume.neighbor_indices,
                field.vectors,
                dL,
                self.alpha_preset["polarity"]
            )
        else:
            # Calculate other norm
            alpha_norm_values = self._norm_worker(
                self.alpha_preset["norm_type"],
                field.vectors
            )

        progress_callback(50)

        # Select color range
        if self.color_preset["is_angle"]:
            color_norm_min, color_norm_max = 0.0, 1.0
        elif all(np.isnan(color_norm_values)):
            color_norm_min, color_norm_max = np.nan, np.nan
        else:
            color_norm_min, color_norm_max = np.nanmin(color_norm_values), np.nanmax(color_norm_values)

        # Select alpha range
        if self.alpha_preset["is_angle"]:
            alpha_norm_min, alpha_norm_max = 0.0, 1.0
        elif all(np.isnan(alpha_norm_values)):
            alpha_norm_min, alpha_norm_max = np.nan, np.nan
        else:
            alpha_norm_min, alpha_norm_max = np.nanmin(alpha_norm_values), np.nanmax(alpha_norm_values)

        # Select color normalizer
        if self.color_preset["is_log"]:
            # Logarithmic normalization

            Assert_Dialog(not self.color_preset["is_angle"], "Logarithmic angles don't make any sense")

            # Adjust range for logarithm (out-of-range values will be clipped in the loop below)
            color_norm_min_ = max(color_norm_min, Metric.LogNormMin)    # avoiding ValueError: min must be positive
            color_norm_max_ = max(color_norm_min_, color_norm_max)          # avoiding ValueError: min must be <= max
        else:
            # Linear normalization
            color_norm_min_ = color_norm_min
            color_norm_max_ = color_norm_max

        # Select alpha normalizer
        if self.alpha_preset["is_log"]:
            # Logarithmic normalization

            Assert_Dialog(not self.alpha_preset["is_angle"], "Logarithmic angles don't make any sense")

            # Adjust range for logarithm (out-of-range values will be clipped in the loop below)
            alpha_norm_min_ = max(alpha_norm_min, Metric.LogNormMin)    # avoiding ValueError: min must be positive
            alpha_norm_max_ = max(alpha_norm_min_, alpha_norm_max)          # avoiding ValueError: min must be <= max
        else:
            # Linear normalization
            alpha_norm_min_ = alpha_norm_min
            alpha_norm_max_ = alpha_norm_max

        colors = np.zeros([n, 4])

        # Calculate final color values
        # Note: If using logarithmic scaling, out-of-range values (still exceeding [0…1] here) may be clipped
        colors = self._normalize_worker(
            self.color_preset["colormap"],
            self.color_preset["is_log"],
            color_norm_values,
            color_norm_min_,
            color_norm_max_,
            self.alpha_preset["is_log"],
            alpha_norm_values,
            alpha_norm_min_,
            alpha_norm_max_,
            colors
        )

        self._colors = colors

        self._limits = {
            "color_min": color_norm_min,
            "color_max": color_norm_max,
            "alpha_min": alpha_norm_min,
            "alpha_max": alpha_norm_max
        }

        progress_callback(100)

        return True

    @property
    @require_valid
    def colors(self) -> np.ndarray:
        """
        Returns calculated colors.

        @return: Ordered list of color values (4-tuples)
        """
        return self._colors

    @property
    @require_valid
    def limits(self) -> Dict:
        """
        Returns calculated limits.

        @return: Dictionary
        """
        return self._limits

    # ------------------------------------------------------------------------------------------------------------------

    @staticmethod
    @ConditionalDecorator(get_jit_enabled(), jit, nopython=True, parallel=True)
    def boost_colors(boost: float, direction: float, colors: np.ndarray) -> np.ndarray:
        """
        "Boosts" an array of color values.

        @param boost: Boost value
        @param direction: Boost direction
        @param colors: Colors (ordered list of 4-tuples)
        @return: Colors (ordered list of 4-tuples)
        """
        for i in prange(len(colors)):
            r = np.max(np.array([0.0, np.min(np.array([1.0, colors[i][0] + boost * direction]))]))
            g = np.max(np.array([0.0, np.min(np.array([1.0, colors[i][1] + boost * direction]))]))
            b = np.max(np.array([0.0, np.min(np.array([1.0, colors[i][2] + boost * direction]))]))
            a = np.max(np.array([0.0, np.min(np.array([1.0, colors[i][3] + boost]))]))
            colors[i] = np.array([r, g, b, a])

        return colors
