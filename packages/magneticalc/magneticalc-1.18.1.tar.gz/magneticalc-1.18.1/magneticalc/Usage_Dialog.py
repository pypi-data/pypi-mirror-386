""" Usage_Dialog module. """

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

from magneticalc.QtWidgets2.QDialog2 import QDialog2
from magneticalc.QtWidgets2.QTextBrowser2 import QTextBrowser2
from magneticalc.Debug import Debug
from magneticalc.Theme import Theme


class Usage_Dialog(QDialog2):
    """ Usage_Dialog class. """

    # HTML content
    HTML = f"""
        <h3 style="color: {Theme.MainColor};">First Steps</h3>
        <h4>
            MagnetiCalc loads a very simple magnetic setup by default.<br>
            Follow these steps to turn it into your own custom setup:
        </h4>
        <ul>
            <li>
                Go to <i>Wire</i> › <i>Load Preset</i> to select a basic wire shape.<br>
                (But you could also import/export wire points from/to a TXT file.)
            </li>
        </ul>
        <ul>
            <li>
                Customize the wire's base points inside the spreadsheet.<br>
                Apply some transformations to your basic wire; stretch its shape, rotate or duplicate it.<br>
                Reduce the slicer limit to improve the field calculation accuracy.<br>
                Set the electrical current flowing through your wire.
            </li>
        </ul>
        <ul>
            <li>
                The sampling volume is the grid over which the field is calculated;<br>
                increase its resolution to the desired level to show every detail of the field.<br>
                <i>Warning:</i> Detailed sampling volumes can take a considerable amount of time to compute.<br>
                <b>Please note that you can disable Auto-Calculation at any time.<br>
                You can and hit F5 or ESC to start or stop the calculation on demand.</b>
            </li>
        </ul>
        <ul>
            <li>
                By default, the cuboid sampling volume covers the wire completely;<br>
                however, you can symmetrically adjust its bounding box by adding (subtracting) some padding.<br>
                By setting a <i>negative</i> padding, you can reduce the sampling volume to a plane, line or point.<br>
                <i>Experimental Feature:</i>
                Use the constraint editor to create regions of relative permeability µ<sub>r</sub> ≠ 1.<br>
                Constraints can also be used to selectively <i>disable</i> calculation over some regions.
            </li>
        </ul>
        <ul>
            <li>
                Select the type of field to calculate: A-field (vector potential) or B-field (flux density).<br>
                <i>Note:</i> Current element center points may be located very close to sampling volume points;<br>
                as this distance approaches zero, the field magnitude approaches infinity (singular behaviour).<br>
                Therefore, some distance limit must be set to cut off (skip) these infinities during calculation.
            </li>
        </ul>
        <ul>
            <li>
                Select a color/alpha metric to adjust the field's hue/transparency individually.<br>
                Because all metrics are normalized, changes in DC current do not affect the field color/alpha;<br>
                however, the displayed metric limits linearly scale with the DC current.
            </li>
        </ul>
        <ul>
            <li>
                Take a look at the minimum and maximum magnetic flux densities reached in each metric.<br>
                <i>Note:</i> To achieve an accurate coil energy and self-inductance calculation,<br>
                ensure that the sampling volume encloses a large, non-singular portion of the field.
            </li>
        </ul>
        <ul>
            <li>
                Use the scroll wheel to zoom in and out of the 3D scene.<br>
                Click and drag into the 3D scene to rotate.<br>
                Press SHIFT while dragging to <i>move</i> the entire 3D scene.<br>
                If you like the result, press CTRL+I to save a screenshot.<br>
                You can also export the fields, wire and current to an HDF5 container for use in post-processing.<br>
                Finally, make sure to save your project!
            </li>
        </ul>

        <h3 style="color: {Theme.MainColor};">What does MagnetiCalc do?</h3>

        MagnetiCalc calculates the static magnetic flux density, vector potential, energy, self-inductance
        and magnetic dipole moment of arbitrary coils.
        Inside an OpenGL-accelerated GUI, the magnetic flux density
        (B-field, in units of <i>Tesla</i>)
        or the magnetic vector potential (A-field, in units of <i>Tesla-meter</i>)
        is displayed in interactive 3D, using multiple metrics for highlighting the field properties.<br><br>

        <i>Experimental feature:</i> To calculate the energy and self-inductance of permeable (i.e. ferrous)
        materials, different core media can be modeled as regions of variable relative permeability;
        however, core saturation is currently not modeled, resulting in excessive flux density values.

        <h3 style="color: {Theme.MainColor};">Who needs MagnetiCalc?</h3>

        MagnetiCalc does its job for hobbyists, students, engineers and researchers of magnetic phenomena.
        I designed MagnetiCalc from scratch, because I didn't want to mess around with expensive and/or
        overly complex simulation software whenever I needed to solve a magnetostatic problem.

        <h3 style="color: {Theme.MainColor};">How does it work?</h3>

        The B-field calculation is implemented using the Biot-Savart law [<b>1</b>],
        employing multiprocessing techniques;
        MagnetiCalc uses just-in-time compilation (JIT) and, if available, GPU-acceleration (CUDA)
        to achieve high-performance calculations.
        Additionally, the use of easily constrainable "sampling volumes"
        allows for selective calculation over grids of arbitrary shape and arbitrary relative permeabilities
        <i>(experimental)</i>.<br><br>

        The shape of any wire is modeled as a 3D piecewise linear curve.
        Arbitrary loops of wire are sliced into differential current elements, each of which
        contributes to the total field magnitude at some fixed 3D grid point,
        summing over the positions of all current elements.<br><br>

        At each grid point, the field is displayed using colored arrows and/or dots;
        field color and alpha transparency are individually mapped using one of the various available metrics.<br><br>

        The coil's energy [<b>2</b>] and self-inductance [<b>3</b>]
        are calculated by summing the squared B-field over the entire sampling volume;
        ensure that the sampling volume encloses a large, non-singular portion of the field.<br><br>

        Additionally, the scalar magnetic dipole moment [<b>4</b>]
        is calculated by summing over all current elements.<br><br>

        [<b>1</b>]: Jackson, Klassische Elektrodynamik, 5. Auflage, S. 204, (5.4).<br>
        [<b>2</b>]: Kraus, Electromagnetics, 4th Edition, p. 269, 6-9-1.<br>
        [<b>3</b>]: Jackson, Klassische Elektrodynamik, 5. Auflage, S. 252, (5.157).<br>
        [<b>4</b>]: Jackson, Klassische Elektrodynamik, 5. Auflage, S. 216, (5.54).<br>

        <br><br><span style="color: {Theme.MainColor};">
            This and more information about MagnetiCalc can be found in the <code>README.md</code> file and on GitHub.
        </span><br>
        """

    def __init__(self) -> None:
        """
        Initializes "Usage" dialog.
        """
        QDialog2.__init__(self, title="Usage", width=850)
        Debug(self, ": Init", init=True)

        text_browser = QTextBrowser2(html=self.HTML)
        text_browser.setMinimumHeight(600)
        self.addWidget(text_browser)
        self.addButtons({
            "OK": ("fa.check", self.accept)
        })
