#!/usr/bin/env python3

""" MagnetiCalc main module. """

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

import os
import sys
from sty import ef
from PyQt5.QtWidgets import QApplication
from magneticalc.Backend_Types import get_jit_enabled, get_cuda_available
from magneticalc.GUI import GUI
from magneticalc.Version import Version


def main() -> None:
    """ MagnetiCalc main function. """

    if sys.platform == "win32":
        os.system("color")

    print()
    print(ef.bold + Version.String + ef.rs)
    print(Version.Copyright)
    print(Version.License)
    print()
    print("Performance Options: JIT " + ("Enabled" if get_jit_enabled() else "Disabled") + ", ", end="")
    print("CUDA " + (("Available" if get_cuda_available() else "Not Available") if get_jit_enabled() else "Disabled"))
    print()

    app = QApplication(sys.argv)

    gui = GUI()

    gui.show()

    rc = app.exec()

    sys.exit(rc)


if __name__ == "__main__":
    main()
