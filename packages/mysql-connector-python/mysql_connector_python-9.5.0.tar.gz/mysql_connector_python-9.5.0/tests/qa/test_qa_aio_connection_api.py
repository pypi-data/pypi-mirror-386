# Copyright (c) 2024, 2025, Oracle and/or its affiliates.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License, version 2.0, as
# published by the Free Software Foundation.
#
# This program is designed to work with certain software (including
# but not limited to OpenSSL) that is licensed under separate terms,
# as designated in a particular file or component or in included license
# documentation. The authors of MySQL hereby grant you an
# additional permission to link the program and your derivative works
# with the separately licensed software that they have either included with
# the program or referenced in the documentation.
#
# Without limiting anything contained in the foregoing, this file,
# which is part of MySQL Connector/Python, is also subject to the
# Universal FOSS Exception, version 1.0, a copy of which can be found at
# http://oss.oracle.com/licenses/universal-foss-exception.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License, version 2.0, for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA

"""Public properties and methods are tested.

This module is expected to include mostly integration tests.
"""

import unittest

import tests

import mysql.connector.aio as cpy

from mysql.connector.charsets import MYSQL_CHARACTER_SETS, MYSQL_CHARACTER_SETS_57
from mysql.connector.constants import (
    MYSQL_DEFAULT_CHARSET_ID_57,
    MYSQL_DEFAULT_CHARSET_ID_80,
)


class TestCharsetAndCollation(tests.MySQLConnectorAioTestCase):
    """Testing charset-related and collation-related properties.

    * charset
    * collation
    * charset_id
    """

    @tests.foreach_cnx(cpy.MySQLConnection)
    async def test_default(self):
        """User does not provide charset or collation. Using default charset_id."""
        if tests.MYSQL_VERSION >= (8, 0, 0):
            exp_charset_and_collation, exp_charset_id = (
                MYSQL_CHARACTER_SETS[MYSQL_DEFAULT_CHARSET_ID_80][:2],
                MYSQL_DEFAULT_CHARSET_ID_80,
            )
        else:
            exp_charset_and_collation, exp_charset_id = (
                MYSQL_CHARACTER_SETS_57[MYSQL_DEFAULT_CHARSET_ID_57][:2],
                MYSQL_DEFAULT_CHARSET_ID_57,
            )

        config = tests.get_mysql_config()
        config["use_pure"] = not self.cnx.__class__.__name__.startswith("C")
        async with await cpy.connect(**config) as cnx:
            # check the connector is returning the rigth charset ID
            self.assertEqual(exp_charset_id, cnx.charset_id)
            async with await cnx.cursor() as cur:
                await cur.execute(
                    "SELECT @@character_set_client, @@collation_connection"
                )
                # check the server is returning the expected charset and collation
                self.assertTupleEqual(exp_charset_and_collation, await cur.fetchone())
            # check the connector is returning the expected charset and collation
            self.assertTupleEqual(
                exp_charset_and_collation, (cnx.charset, cnx.collation)
            )

    @tests.foreach_cnx(cpy.MySQLConnection)
    async def test_charset_and_collation(self):
        """User provides both the charset and collation."""
        config = tests.get_mysql_config()
        config["use_pure"] = not self.cnx.__class__.__name__.startswith("C")

        cases = (2, 5, 8, 11, 14, 18, 40, 49, 57, 66, 84)
        for exp_charset_id in cases:
            config["charset"], config["collation"] = (
                MYSQL_CHARACTER_SETS[exp_charset_id][:2]
                if tests.MYSQL_VERSION >= (8, 0, 0)
                else MYSQL_CHARACTER_SETS_57[exp_charset_id][:2]
            )
            async with await cpy.connect(**config) as cnx:
                # check the connector is returning the rigth charset ID
                self.assertEqual(exp_charset_id, cnx.charset_id)
                async with await cnx.cursor() as cur:
                    await cur.execute(
                        "SELECT @@character_set_client, @@collation_connection"
                    )
                    # check the server is returning the expected charset and collation
                    self.assertTupleEqual(
                        (config["charset"], config["collation"]), await cur.fetchone()
                    )
                # check the connector is returning the expected charset and collation
                self.assertTupleEqual(
                    (config["charset"], config["collation"]),
                    (cnx.charset, cnx.collation),
                )

    @unittest.skipIf(
        tests.MYSQL_VERSION < (8, 0, 0),
        "MySQL Server should be 8.0 or newer. Using late charsets.",
    )
    @tests.foreach_cnx(cpy.MySQLConnection)
    async def test_charset_only(self):
        """User provides the charset but not the collation."""
        config = tests.get_mysql_config()
        config["use_pure"] = not self.cnx.__class__.__name__.startswith("C")

        collations = (
            "utf8mb4_0900_ai_ci",
            "latin7_general_ci",
            "cp1250_general_ci",
            "binary",
            "cp1257_general_ci",
        )
        charsets = ("utf8mb4", "latin7", "cp1250", "binary", "cp1257")
        exp_charset_ids = (255, 41, 26, 63, 59)

        for exp_charset_id, charset, collation in zip(
            exp_charset_ids, charsets, collations
        ):
            config["charset"] = charset
            async with await cpy.connect(**config) as cnx:
                # check the connector is returning the rigth charset ID
                self.assertEqual(exp_charset_id, cnx.charset_id)
                async with await cnx.cursor() as cur:
                    await cur.execute(
                        "SELECT @@character_set_client, @@collation_connection"
                    )
                    res = await cur.fetchone()

                    if charset == "binary":
                        res = tuple([x.decode("utf8") for x in res])

                    # check the server is returning the expected charset and collation
                    self.assertTupleEqual((config["charset"], collation), res)

                # check the connector is returning the expected charset and collation
                self.assertTupleEqual(
                    (config["charset"], collation), (cnx.charset, cnx.collation)
                )

    @unittest.skipIf(
        tests.MYSQL_VERSION < (8, 0, 0),
        "MySQL Server should be 8.0 or newer. Using late collations.",
    )
    @tests.foreach_cnx(cpy.MySQLConnection)
    async def test_collation_only(self):
        """User provides the collation but not the charset."""
        config = tests.get_mysql_config()
        config["use_pure"] = not self.cnx.__class__.__name__.startswith("C")

        collations = (
            "utf8mb4_ja_0900_as_cs",
            "utf8mb4_bin",
            "utf8mb4_general_ci",
            "binary",
            "cp1257_lithuanian_ci",
        )
        charsets = ("utf8mb4", "utf8mb4", "utf8mb4", "binary", "cp1257")
        exp_charset_ids = (303, 46, 45, 63, 29)

        for exp_charset_id, charset, collation in zip(
            exp_charset_ids, charsets, collations
        ):
            config["collation"] = collation
            async with await cpy.connect(**config) as cnx:
                # check the connector is returning the rigth charset ID
                self.assertEqual(exp_charset_id, cnx.charset_id)
                async with await cnx.cursor() as cur:
                    await cur.execute(
                        "SELECT @@character_set_client, @@collation_connection"
                    )
                    res = await cur.fetchone()

                    if collation == "binary":
                        res = tuple([x.decode("utf8") for x in res])

                    # check the server is returning the expected charset and collation
                    self.assertTupleEqual((charset, config["collation"]), res)

                # check the connector is returning the expected charset and collation
                self.assertTupleEqual(
                    (charset, config["collation"]), (cnx.charset, cnx.collation)
                )

    @tests.foreach_cnx_aio()
    async def test_cmd_change_user(self):
        """Switch user and provide a different charset_id."""
        config = tests.get_mysql_config()
        if tests.MYSQL_VERSION >= (8, 0, 0):
            charset_data, exp_charset_id_before = (
                MYSQL_CHARACTER_SETS,
                MYSQL_DEFAULT_CHARSET_ID_80,
            )
        else:
            charset_data, exp_charset_id_before = (
                MYSQL_CHARACTER_SETS_57,
                MYSQL_DEFAULT_CHARSET_ID_57,
            )
        exp_charset_before = charset_data[exp_charset_id_before][0]
        exp_collation_before = charset_data[exp_charset_id_before][1]

        exp_charset_id_after = 63
        exp_charset_after = charset_data[exp_charset_id_after][0]
        exp_collation_after = charset_data[exp_charset_id_after][1]

        # It should be the default
        self.assertEqual(exp_charset_id_before, self.cnx.charset_id)
        self.assertEqual(exp_charset_before, self.cnx.charset)
        self.assertEqual(exp_collation_before, self.cnx.collation)

        # do switch without setting charset and check that it matches 'exp_charset_id_before'
        await self.cnx.cmd_change_user(
            username=config["user"],
            password=config["password"],
            database=config["database"],
        )
        self.assertEqual(exp_charset_id_before, self.cnx.charset_id)
        self.assertEqual(exp_charset_before, self.cnx.charset)
        self.assertEqual(exp_collation_before, self.cnx.collation)

        # do switch and check that it matches `exp_charset_id_after`
        await self.cnx.cmd_change_user(
            username=config["user"],
            password=config["password"],
            database=config["database"],
            charset=exp_charset_id_after,
        )
        self.assertEqual(exp_charset_id_after, self.cnx.charset_id)
        self.assertEqual(exp_charset_after, self.cnx.charset)
        self.assertEqual(exp_collation_after, self.cnx.collation)
