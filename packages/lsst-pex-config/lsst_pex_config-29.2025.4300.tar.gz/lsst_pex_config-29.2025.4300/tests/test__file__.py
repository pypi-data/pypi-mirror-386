# This file is part of pex_config.
#
# Developed for the LSST Data Management System.
# This product includes software developed by the LSST Project
# (http://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This software is dual licensed under the GNU General Public License and also
# under a 3-clause BSD license. Recipients may choose which of these licenses
# to use; please see the files gpl-3.0.txt and/or bsd_license.txt,
# respectively.  If you choose the GPL option then the following text applies
# (but note that there is still no warranty even if you opt for BSD instead):
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import unittest

import lsst.pex.config as pexConf

TESTDIR = os.path.dirname(os.path.abspath(__file__))


class FileConfig(pexConf.Config):
    """Config used for testing __file__."""

    number = pexConf.Field("FileConfig.number", int, default=0)
    filename = pexConf.Field("FileConfig.filename", str, default=None)


class FilenameTestCase(unittest.TestCase):
    """Check that __file__ can be used in a config file."""

    def test__file(self):
        c = FileConfig()
        confFile = os.path.join(TESTDIR, "config", "filename.py")
        c.load(confFile)
        self.assertEqual(c.filename, confFile)
        self.assertEqual(c.number, 5)


if __name__ == "__main__":
    unittest.main()
