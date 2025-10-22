# -*- coding: utf-8 -*-

# Copyright (c) 2016, 2024, Oracle and/or its affiliates.
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

""" BUG21879859
"""

import tests

from tests import cnx_config, foreach_cnx

import mysql.connector

from mysql.connector import Error

try:
    from mysql.connector.connection_cext import CMySQLConnection
except ImportError:
    # Test without C Extension
    CMySQLConnection = None


class Bug21879859(tests.MySQLConnectorTests):
    def setUp(self):
        self.table = "Bug21879859"
        self.proc = "Bug21879859_proc"

        cnx = mysql.connector.connect(**tests.get_mysql_config())
        cur = cnx.cursor()
        cur.execute(f"DROP TABLE IF EXISTS {self.table}")
        cur.execute(f"DROP PROCEDURE IF EXISTS {self.proc}")
        cur.execute(
            f"""
            CREATE TABLE {self.table}
            (id INT AUTO_INCREMENT PRIMARY KEY, c1 VARCHAR(1024))
            """
        )
        cur.execute(
            f"""
            CREATE PROCEDURE {self.table}() BEGIN SELECT 1234;
            SELECT t from {self.proc}; SELECT '' from {self.table}; END
            """
        )

    def tearDown(self):
        cnx = mysql.connector.connect(**tests.get_mysql_config())
        cur = cnx.cursor()
        cur.execute(f"DROP TABLE IF EXISTS {self.table}")
        cur.execute(f"DROP PROCEDURE IF EXISTS {self.proc}")

    @cnx_config(consume_results=True)
    @foreach_cnx()
    def test_consume_after_callproc(self):
        cur = self.cnx.cursor()

        cur.execute(f"INSERT INTO {self.table} (c1) VALUES ('a'),('b'),('c')")

        # expected to fail
        self.assertRaises(Error, cur.callproc, self.proc)
        try:
            cur.close()
        except mysql.connector.Error as exc:
            self.fail("Failed closing: " + str(exc))
