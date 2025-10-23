# This file is part of daf_butler.
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

"""Unit tests for daf_butler CLI query-collections command."""

import unittest

from astropy.table import Table as AstropyTable
from numpy import array

from lsst.daf.butler.cli.butler import cli
from lsst.daf.butler.cli.cmd import query_dataset_types
from lsst.daf.butler.cli.utils import LogCliRunner, clickResultMsg
from lsst.daf.butler.tests import CliCmdTestBase
from lsst.daf.butler.tests.utils import ButlerTestHelper, readTable


class QueryDatasetTypesCmdTest(CliCmdTestBase, unittest.TestCase):
    """Test the query-dataset-types command line."""

    mockFuncName = "lsst.daf.butler.cli.cmd.commands.script.queryDatasetTypes"

    @staticmethod
    def defaultExpected():
        return dict(repo=None, verbose=False, glob=(), collections=())

    @staticmethod
    def command():
        return query_dataset_types

    def test_minimal(self):
        """Test only required parameters."""
        self.run_test(["query-dataset-types", "here"], self.makeExpected(repo="here"))

    def test_requiredMissing(self):
        """Test that if the required parameter is missing it fails"""
        self.run_missing(["query-dataset-types"], r"Error: Missing argument ['\"]REPO['\"].")

    def test_all(self):
        """Test all parameters."""
        self.run_test(
            ["query-dataset-types", "here", "--verbose", "foo*"],
            self.makeExpected(repo="here", verbose=True, glob=("foo*",)),
        )
        self.run_test(
            ["query-dataset-types", "here", "--verbose", "foo*"],
            self.makeExpected(repo="here", verbose=True, glob=("foo*",)),
        )


class QueryDatasetTypesScriptTest(ButlerTestHelper, unittest.TestCase):
    """Test the query-dataset-types script interface."""

    def testQueryDatasetTypes(self):
        self.maxDiff = None
        datasetName = "test"
        instrumentDimension = "instrument"
        visitDimension = "visit"
        storageClassName = "StructuredDataDict"
        expectedNotVerbose = AstropyTable((("test",),), names=("name",))
        runner = LogCliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["create", "here"])
            self.assertEqual(result.exit_code, 0, clickResultMsg(result))
            # Create the dataset type.
            result = runner.invoke(
                cli,
                [
                    "register-dataset-type",
                    "here",
                    datasetName,
                    storageClassName,
                    instrumentDimension,
                    visitDimension,
                ],
            )
            self.assertEqual(result.exit_code, 0, clickResultMsg(result))
            # Okay to create it again identically.
            result = runner.invoke(
                cli,
                [
                    "register-dataset-type",
                    "here",
                    datasetName,
                    storageClassName,
                    instrumentDimension,
                    visitDimension,
                ],
            )
            self.assertEqual(result.exit_code, 0, clickResultMsg(result))
            # Not okay to create a different version of it.
            result = runner.invoke(
                cli, ["register-dataset-type", "here", datasetName, storageClassName, instrumentDimension]
            )
            self.assertNotEqual(result.exit_code, 0, clickResultMsg(result))
            # Not okay to try to create a component dataset type.
            result = runner.invoke(
                cli, ["register-dataset-type", "here", "a.b", storageClassName, instrumentDimension]
            )
            self.assertNotEqual(result.exit_code, 0, clickResultMsg(result))
            # check not-verbose output:
            result = runner.invoke(cli, ["query-dataset-types", "here"])
            self.assertEqual(result.exit_code, 0, clickResultMsg(result))
            self.assertAstropyTablesEqual(readTable(result.output), expectedNotVerbose)
            # check glob output:
            result = runner.invoke(cli, ["query-dataset-types", "here", "t*"])
            self.assertEqual(result.exit_code, 0, clickResultMsg(result))
            self.assertAstropyTablesEqual(readTable(result.output), expectedNotVerbose)
            # check verbose output:
            result = runner.invoke(cli, ["query-dataset-types", "here", "--verbose"])
            self.assertEqual(result.exit_code, 0, clickResultMsg(result))
            expected = AstropyTable(
                array(
                    (
                        "test",
                        "['band', 'instrument', 'day_obs', 'physical_filter', 'visit']",
                        storageClassName,
                    )
                ),
                names=("name", "dimensions", "storage class"),
            )
            self.assertAstropyTablesEqual(readTable(result.output), expected)

            # Now remove and check that it was removed
            # First a non-existent one
            result = runner.invoke(cli, ["remove-dataset-type", "here", "unreal"])
            self.assertEqual(result.exit_code, 0, clickResultMsg(result))

            # Now one we now has been registered
            result = runner.invoke(cli, ["remove-dataset-type", "here", datasetName])
            self.assertEqual(result.exit_code, 0, clickResultMsg(result))

            # and check that it has gone
            result = runner.invoke(cli, ["query-dataset-types", "here"])
            self.assertEqual(result.exit_code, 0, clickResultMsg(result))
            self.assertIn("No results", result.output)

    def testRemoveDatasetTypes(self):
        self.maxDiff = None
        datasetName = "test"
        instrumentDimension = "instrument"
        visitDimension = "visit"
        storageClassName = "StructuredDataDict"
        runner = LogCliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["create", "here"])
            self.assertEqual(result.exit_code, 0, clickResultMsg(result))
            for name in (
                datasetName,
                "testA",
                "testB",
                "testC",
                "testD",
                "other",
                "another",
                "option",
                "option2",
                "placeholder",
            ):
                # Create the dataset type.
                result = runner.invoke(
                    cli,
                    [
                        "register-dataset-type",
                        "here",
                        name,
                        storageClassName,
                        instrumentDimension,
                        visitDimension,
                    ],
                )

            # Check wildcard / literal combination.
            result = runner.invoke(cli, ["remove-dataset-type", "here", "*other", "testA"])
            self.assertEqual(result.exit_code, 0, clickResultMsg(result))
            self.assertDatasetTypes(
                runner,
                "*",
                (
                    "option",
                    "option2",
                    "placeholder",
                    "test",
                    "testB",
                    "testC",
                    "testD",
                ),
            )

            # Check literal / literal combination.
            result = runner.invoke(cli, ["remove-dataset-type", "here", "option", "testB"])
            self.assertEqual(result.exit_code, 0, clickResultMsg(result))
            self.assertDatasetTypes(
                runner,
                "*",
                (
                    "option2",
                    "placeholder",
                    "test",
                    "testC",
                    "testD",
                ),
            )

            # Check wildcard.
            result = runner.invoke(cli, ["remove-dataset-type", "here", "test*"])
            self.assertEqual(result.exit_code, 0, clickResultMsg(result))
            self.assertDatasetTypes(
                runner,
                "*",
                (
                    "option2",
                    "placeholder",
                ),
            )

            # Check literal.
            result = runner.invoke(cli, ["remove-dataset-type", "here", "option2"])
            self.assertEqual(result.exit_code, 0, clickResultMsg(result))
            self.assertDatasetTypes(runner, "*", ("placeholder",))

    def assertDatasetTypes(self, runner: LogCliRunner, query: str, expected: tuple[str, ...]) -> None:
        result = runner.invoke(cli, ["query-dataset-types", "here", query])
        self.assertEqual(result.exit_code, 0, clickResultMsg(result))
        expected = AstropyTable(
            (expected,),
            names=("name",),
        )
        self.assertAstropyTablesEqual(readTable(result.output), expected)


if __name__ == "__main__":
    unittest.main()
