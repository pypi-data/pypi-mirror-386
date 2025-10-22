# -*- coding: utf-8 -*-

# Copyright (c) 2009, 2025, Oracle and/or its affiliates.
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

"""Test module for bugs.

Bug test cases specific to a particular Python (major) version are loaded
from py2.bugs or py3.bugs.

This module was originally located in python2/tests and python3/tests. It
should contain bug test cases which work for both Python v2 and v3.

Whenever a bug is bout to a specific Python version, put the test cases
in tests/py2/bugs.py or tests/py3/bugs.py. It might be that these files need
to be created first.
"""

import collections
import gc
import os
import pickle
import platform
import sys
import tempfile
import traceback
import unittest

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from threading import Thread
from time import sleep

import tests

import mysql.connector.aio

if tests.SSL_AVAILABLE:
    import ssl

from tests import cnx_config, foreach_cnx, foreach_cnx_aio

import mysql.connector

from mysql.connector import (
    MySQLConnection,
    connection,
    constants,
    conversion,
    cursor,
    errors,
    network,
    pooling,
    protocol,
)
from mysql.connector.optionfiles import read_option_files
from mysql.connector.pooling import PooledMySQLConnection

from . import check_tls_versions_support

try:
    from _mysql_connector import MySQL

    from mysql.connector.connection_cext import CMySQLConnection, MySQLInterfaceError
except ImportError:
    # Test without C Extension
    CMySQLConnection = None
    MySQLInterfaceError = None
    MySQL = None

ERR_NO_CEXT = "C Extension not available"


def setUpModule() -> None:
    with MySQLConnection(**tests.get_mysql_config()) as cnx:
        global NATIVE_PASSWORD_INSTALLED

        user = {
            "user": "_bugs",
            "host": "%",
            "auth_plugin": "mysql_native_password",
            "password": "s3cr3t",
        }
        stmt = (
            "CREATE USER IF NOT EXISTS '{user}'@'{host}' IDENTIFIED "
            "WITH {auth_plugin} BY '{password}'"
        ).format(**user)
        with cnx.cursor() as cur:
            try:
                cur.execute("DROP USER IF EXISTS '{user}'@'{host}'".format(**user))
                cur.execute(stmt)
                cur.execute("DROP USER IF EXISTS '{user}'@'{host}'".format(**user))
                NATIVE_PASSWORD_INSTALLED = True
            except mysql.connector.errors.DatabaseError:
                try:
                    cur.execute("INSTALL COMPONENT 'file://mysql_native_password'")
                    NATIVE_PASSWORD_INSTALLED = True
                except mysql.connector.errors.DatabaseError:
                    NATIVE_PASSWORD_INSTALLED = False


class Bug437972Tests(tests.MySQLConnectorTests):
    def test_windows_tcp_connection(self):
        """lp:437972 TCP connection to Windows"""
        if os.name != "nt":
            pass

        cnx = None
        try:
            cnx = connection.MySQLConnection(**tests.get_mysql_config())
        except errors.InterfaceError:
            self.fail()

        if cnx:
            cnx.close()


class Bug441430Tests(tests.MySQLConnectorTests):
    @foreach_cnx()
    def test_execute_return(self):
        """lp:441430 cursor.execute*() should return the cursor.rowcount"""

        cur = self.cnx.cursor()
        tbl = "buglp44130"
        cur.execute(f"DROP TABLE IF EXISTS {tbl}")
        cur.execute(f"CREATE TABLE {tbl} (id INT AUTO_INCREMENT PRIMARY KEY)")
        cur.execute(f"INSERT INTO {tbl} VALUES (%s),(%s)", (1, 2))
        self.assertEqual(2, cur.rowcount)
        stmt = f"INSERT INTO {tbl} VALUES (%s)"
        cur.executemany(stmt, [(3,), (4,), (5,), (6,), (7,), (8,)])
        self.assertEqual(6, cur.rowcount)
        cur.execute(f"UPDATE {tbl} SET id = id + %s", (10,))
        self.assertEqual(8, cur.rowcount)

        cur.execute(f"DROP TABLE IF EXISTS {tbl}")
        cur.close()
        self.cnx.close()


class Bug454790(tests.MySQLConnectorTests):
    """lp:454790 pyformat / other named parameters broken"""

    @foreach_cnx()
    def test_pyformat(self):
        cur = self.cnx.cursor()

        data = {"name": "Geert", "year": 1977}
        cur.execute("SELECT %(name)s,%(year)s", data)
        self.assertEqual(("Geert", 1977), cur.fetchone())

        data = [
            {"name": "Geert", "year": 1977},
            {"name": "Marta", "year": 1980},
        ]
        cur.executemany("SELECT %(name)s,%(year)s", data)
        self.assertEqual(2, cur.rowcount)
        cur.close()
        self.cnx.close()


class Bug480360(tests.MySQLConnectorTests):
    """lp:480360: fetchall() should return [] when no result"""

    @foreach_cnx()
    def test_fetchall(self):
        cur = self.cnx.cursor()

        # Trick to get empty result not needing any table
        cur.execute("SELECT * FROM (SELECT 1) AS t WHERE 0 = 1")
        self.assertEqual([], cur.fetchall())
        cur.close()
        self.cnx.close()


@unittest.skipIf(
    tests.MYSQL_VERSION >= (5, 6, 6),
    "Bug380528 not tested with MySQL version >= 5.6.6",
)
class Bug380528(tests.MySQLConnectorTests):
    """lp:380528: we do not support old passwords"""

    @foreach_cnx()
    def test_old_password(self):
        cur = self.cnx.cursor()

        if self.config["unix_socket"] and os.name != "nt":
            user = "'myconnpy'@'localhost'"
        else:
            user = "'myconnpy'@'%s'" % (config["host"])

        try:
            cur.execute("GRANT SELECT ON %s.* TO %s" % (self.config["database"], user))
            cur.execute("SET PASSWORD FOR %s = OLD_PASSWORD('fubar')" % (user))
        except:
            self.fail("Failed executing grant.")
        cur.close()

        # Test using the newly created user
        test_config = self.config.copy()
        test_config["user"] = "myconnpy"
        test_config["password"] = "fubar"

        self.assertRaises(errors.NotSupportedError, self.cnx.__class__, **test_config)

        self.cnx = self.cnx.__class__(**self.config)
        cur = self.cnx.cursor()
        try:
            cur.execute(
                "REVOKE SELECT ON %s.* FROM %s" % (self.config["database"], user)
            )
            cur.execute("DROP USER %s" % (user))
        except mysql.connector.Error as exc:
            self.fail("Failed cleaning up user {0}: {1}".format(user, exc))
        cur.close()


class Bug499362(tests.MySQLConnectorTests):
    """lp:499362 Setting character set at connection fails"""

    @cnx_config(charset="latin1")
    @foreach_cnx()
    def test_charset(self):
        cur = self.cnx.cursor()

        ver = self.cnx.server_version

        varlst = [
            "character_set_client",
            "character_set_connection",
            "character_set_results",
        ]

        if ver < (5, 1, 12):
            exp1 = [
                ("character_set_client", "latin1"),
                ("character_set_connection", "latin1"),
                ("character_set_database", "utf8"),
                ("character_set_filesystem", "binary"),
                ("character_set_results", "latin1"),
                ("character_set_server", "utf8"),
                ("character_set_system", "utf8"),
            ]
            exp2 = [
                ("character_set_client", "latin2"),
                ("character_set_connection", "latin2"),
                ("character_set_database", "utf8"),
                ("character_set_filesystem", "binary"),
                ("character_set_results", "latin2"),
                ("character_set_server", "utf8"),
                ("character_set_system", "utf8"),
            ]
            varlst = []
            stmt = r"SHOW SESSION VARIABLES LIKE 'character\_set\_%%'"

            exp1 = [
                ("CHARACTER_SET_CONNECTION", "latin1"),
                ("CHARACTER_SET_CLIENT", "latin1"),
                ("CHARACTER_SET_RESULTS", "latin1"),
            ]
            exp2 = [
                ("CHARACTER_SET_CONNECTION", "latin2"),
                ("CHARACTER_SET_CLIENT", "latin2"),
                ("CHARACTER_SET_RESULTS", "latin2"),
            ]

        elif ver >= (5, 7, 6):
            # INFORMATION_SCHEMA is deprecated
            exp1 = [
                ("character_set_client", "latin1"),
                ("character_set_connection", "latin1"),
                ("character_set_results", "latin1"),
            ]
            exp2 = [
                ("character_set_client", "latin2"),
                ("character_set_connection", "latin2"),
                ("character_set_results", "latin2"),
            ]
            stmt = (
                "SELECT * FROM performance_schema.session_variables "
                "WHERE VARIABLE_NAME IN (%s,%s,%s)"
            )

        else:
            exp1 = [
                ("CHARACTER_SET_CONNECTION", "latin1"),
                ("CHARACTER_SET_CLIENT", "latin1"),
                ("CHARACTER_SET_RESULTS", "latin1"),
            ]
            exp2 = [
                ("CHARACTER_SET_CONNECTION", "latin2"),
                ("CHARACTER_SET_CLIENT", "latin2"),
                ("CHARACTER_SET_RESULTS", "latin2"),
            ]

            stmt = (
                "SELECT * FROM INFORMATION_SCHEMA.SESSION_VARIABLES "
                "WHERE VARIABLE_NAME IN (%s,%s,%s)"
            )

        cur.execute(stmt, varlst)
        res1 = cur.fetchall()

        self.cnx.set_charset_collation("latin2")
        cur.execute(stmt, varlst)
        res2 = cur.fetchall()

        cur.close()
        self.cnx.close()

        self.assertTrue(tests.cmp_result(exp1, res1))
        self.assertTrue(tests.cmp_result(exp2, res2))


class Bug501290(tests.MySQLConnectorTests):
    """lp:501290 Client flags are set to None when connecting"""

    def _setup(self):
        self.capabilities = self.cnx._handshake["capabilities"]

        self.default_flags = constants.ClientFlag.get_default()
        if self.capabilities & constants.ClientFlag.PLUGIN_AUTH:
            self.default_flags |= constants.ClientFlag.PLUGIN_AUTH

    @foreach_cnx()
    def test_default(self):
        self._setup()
        flags = constants.ClientFlag.default
        for flag in flags:
            self.assertTrue(self.cnx.client_flags & flag)

    @foreach_cnx()
    def test_set_unset(self):
        self._setup()
        orig = self.cnx.client_flags

        exp = self.default_flags | constants.ClientFlag.COMPRESS
        if tests.MYSQL_VERSION < (5, 7):
            exp = exp & ~constants.ClientFlag.CONNECT_ARGS
        self.cnx.client_flags = [constants.ClientFlag.COMPRESS]
        for flag in constants.ClientFlag.default:
            self.assertTrue(self.cnx.client_flags & flag)

        self.cnx.client_flags = [-constants.ClientFlag.COMPRESS]
        self.assertEqual(self.cnx.client_flags, orig)

    @foreach_cnx()
    def test_isset_client_flag(self):
        self._setup()
        flag = constants.ClientFlag.COMPRESS
        data = self.default_flags | flag

        self.cnx.client_flags = data
        self.assertEqual(True, self.cnx.isset_client_flag(flag))


class Bug507466(tests.MySQLConnectorTests):
    """lp:507466 BIT values are not converted correctly to Python"""

    def tearDown(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        try:
            cur = cnx.cursor()
            cur.execute("DROP TABLE IF EXISTS myconnpy_bits")
        except:
            pass
        cnx.close()

    @foreach_cnx()
    def test_bits(self):
        cur = self.cnx.cursor()

        cur.execute("DROP TABLE IF EXISTS myconnpy_bits")
        cur.execute(
            """CREATE TABLE `myconnpy_bits` (
          `id` int NOT NULL AUTO_INCREMENT,
          `c1` bit(8) DEFAULT NULL,
          `c2` bit(16) DEFAULT NULL,
          `c3` bit(24) DEFAULT NULL,
          `c4` bit(32) DEFAULT NULL,
          `c5` bit(40) DEFAULT NULL,
          `c6` bit(48) DEFAULT NULL,
          `c7` bit(56) DEFAULT NULL,
          `c8` bit(64) DEFAULT NULL,
          PRIMARY KEY (id)
        )
        """
        )

        insert = """insert into myconnpy_bits (c1,c2,c3,c4,c5,c6,c7,c8)
            values (%s,%s,%s,%s,%s,%s,%s,%s)"""
        select = "SELECT c1,c2,c3,c4,c5,c6,c7,c8 FROM myconnpy_bits ORDER BY id"

        data = []
        data.append((0, 0, 0, 0, 0, 0, 0, 0))
        data.append(
            (
                1 << 7,
                1 << 15,
                1 << 23,
                1 << 31,
                1 << 39,
                1 << 47,
                1 << 55,
                (1 << 63) - 1,
            )
        )
        cur.executemany(insert, data)
        cur.execute(select)
        rows = cur.fetchall()

        self.assertEqual(rows, data)

        self.cnx.close()


@unittest.skipIf(
    tests.MYSQL_VERSION >= (8, 4, 0), "mysql_native_password is deprecated"
)
class Bug519301(tests.MySQLConnectorTests):
    """lp:519301 Temporary connection failures with 2 exceptions"""

    @foreach_cnx()
    def test_auth(self):
        config = self.config.copy()
        config.pop("unix_socket")
        config["user"] = "ham"
        config["password"] = "spam"

        for _ in range(1, 100):
            try:
                cnx = self.cnx.__class__(**config)
            except errors.ProgrammingError:
                pass
            except errors.Error as err:
                self.fail("Failing authenticating: {0}".format(str(err)))
            except:
                raise
            else:
                cnx.close()


class Bug524668(tests.MySQLConnectorTests):
    """lp:524668 Error in server handshake with latest code"""

    def test_handshake(self):
        handshake = bytearray(
            b"\x47\x00\x00\x00\x0a\x35\x2e\x30\x2e\x33\x30\x2d\x65"
            b"\x6e\x74\x65\x72\x70\x72\x69\x73\x65\x2d\x67\x70\x6c"
            b"\x2d\x6c\x6f"
            b"\x67\x00\x09\x01\x00\x00\x68\x34\x69\x36\x6f\x50\x21\x4f\x00"
            b"\x2c\xa2\x08\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            b"\x00"
            b"\x00\x00\x4c\x6e\x67\x39\x26\x50\x44\x40\x57\x72\x59\x48\x00"
        )

        prtcl = protocol.MySQLProtocol()
        try:
            prtcl.parse_handshake(handshake)
        except:
            self.fail("Failed handling handshake")


class Bug571201(tests.MySQLConnectorTests):
    """lp:571201 Problem with more than one statement at a time"""

    def setUp(self):
        self.tbl = "Bug571201"

    def tearDown(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        try:
            cur = cnx.cursor()
            cur.execute("DROP TABLE IF EXISTS {0}".format(self.tbl))
        except:
            pass
        cnx.close()

    @foreach_cnx()
    def test_multistmts(self):
        cur = self.cnx.cursor()
        cur.execute(f"DROP TABLE IF EXISTS {self.tbl}")
        cur.execute(
            f"CREATE TABLE {self.tbl} (id INT AUTO_INCREMENT PRIMARY KEY, c1 INT)"
        )

        stmts = [
            f"SELECT * FROM {self.tbl}",
            f"INSERT INTO {self.tbl} (c1) VALUES (10),(20)",
            f"SELECT * FROM {self.tbl}",
        ]
        exp_result_sets = collections.deque(
            [
                # result set, row count
                ([], 0),
                ([], 2),
                ([(1, 10), (2, 20)], 2),
            ]
        )

        cur.execute(";".join(stmts))
        for statement, result_set in cur.fetchsets():
            exp_res, _ = exp_result_sets.popleft()
            self.assertEqual(exp_res, result_set)
            self.assertEqual(";".join(stmts), statement)
        self.assertEqual(0, len(exp_result_sets))

        self.cnx.close()


class Bug551533and586003(tests.MySQLConnectorTests):
    """lp: 551533 as 586003: impossible to retrieve big result sets"""

    def setUp(self):
        self.tbl = "Bug551533"

    def tearDown(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        cnx.cmd_query("DROP TABLE IF EXISTS {table}".format(table=self.tbl))
        cnx.close()

    @cnx_config(connection_timeout=10)
    @foreach_cnx()
    def test_select(self):
        cur = self.cnx.cursor()

        cur.execute(f"DROP TABLE IF EXISTS {self.tbl}")
        cur.execute(
            f"""
            CREATE TABLE {self.tbl} (id INT AUTO_INCREMENT PRIMARY KEY,
            c1 VARCHAR(100) DEFAULT 'abcabcabcabcabcabcabcabcabcabc') ENGINE=INNODB
            """
        )

        insert = f"INSERT INTO {self.tbl} (id) VALUES (%s)"
        exp = 20000
        cur.executemany(insert, [(None,)] * exp)
        self.cnx.commit()

        cur.execute(f"SELECT * FROM {self.tbl} LIMIT 20000")
        try:
            rows = cur.fetchall()
        except errors.Error as err:
            self.fail(f"Failed retrieving big result set: {err}")
        else:
            self.assertEqual(exp, cur.rowcount)
            self.assertEqual(exp, len(rows))


class Bug675425(tests.MySQLConnectorTests):
    """lp: 675425: Problems with apostrophe"""

    def setUp(self):
        self.tbl = "Bug675425"

    def tearDown(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        cur = cnx.cursor()
        cur.execute("DROP TABLE IF EXISTS {0}".format(self.tbl))
        cnx.close()

    @foreach_cnx()
    def test_executemany_escape(self):
        cur = self.cnx.cursor()

        cur.execute(f"DROP TABLE IF EXISTS {self.tbl}")
        cur.execute(
            f"""
            CREATE TABLE {self.tbl}
            (id INT AUTO_INCREMENT PRIMARY KEY, c1 VARCHAR(30), c2 VARCHAR(30))
            """
        )
        data = [
            (
                "ham",
                "spam",
            ),
            (
                "spam",
                "ham",
            ),
            (
                "ham \\' spam",
                "spam ' ham",
            ),
        ]
        sql = f"INSERT INTO {self.tbl} (c1, c2) VALUES (%s, %s)"
        try:
            cur.executemany(sql, data)
        except Exception as exc:
            self.fail(str(exc))

        self.cnx.close()


class Bug695514(tests.MySQLConnectorTests):
    """lp: 695514: Infinite recursion when setting connection client_flags"""

    @foreach_cnx()
    def test_client_flags(self):
        try:
            config = tests.get_mysql_config()
            config["connection_timeout"] = 2
            config["client_flags"] = constants.ClientFlag.get_default()
            self.cnx = self.cnx.__class__(**config)
        except:
            self.fail("Failed setting client_flags using integer")


class Bug809033(tests.MySQLConnectorTests):
    """lp: 809033: Lost connection causes infinite loop"""

    def setUp(self):
        self.table_name = "Bug809033"

    def _setup(self):
        self.cnx.cmd_query("DROP TABLE IF EXISTS {0}".format(self.table_name))
        table = (
            "CREATE TABLE {table} ("
            " id INT UNSIGNED NOT NULL AUTO_INCREMENT,"
            " c1 VARCHAR(255) DEFAULT '{default}',"
            " PRIMARY KEY (id)"
            ")"
        ).format(table=self.table_name, default="a" * 255)
        self.cnx.cmd_query(table)

        stmt = "INSERT INTO {table} (id) VALUES {values}".format(
            table=self.table_name, values=",".join(["(NULL)"] * 1024)
        )
        self.cnx.cmd_query(stmt)

    def tearDown(self):
        try:
            cnx = connection.MySQLConnection(**tests.get_mysql_config())
            cnx.cmd_query("DROP TABLE IF EXISTS {0}".format(self.table_name))
            cnx.close()
        except:
            pass

    @unittest.skipIf(platform.machine() == "arm64", "Test not available for ARM64")
    @foreach_cnx()
    def test_lost_connection(self):
        self._setup()

        def kill(connection_id):
            """Kill connection using separate connection"""
            killer = connection.MySQLConnection(**tests.get_mysql_config())
            sleep(1)
            killer.cmd_query("KILL {0}".format(connection_id))
            killer.close()

        def sleepy_select(cnx):
            """Execute a SELECT statement which takes a while to complete"""
            cur = cnx.cursor()
            # Ugly query ahead!
            stmt = "SELECT x1.*, x2.* from {table} as x1, {table} as x2".format(
                table=self.table_name
            )
            cur.execute(stmt)
            # Save the error so we can check in the calling thread
            cnx.test_error = None
            try:
                cur.fetchall()
            except errors.Error as err:
                cnx.test_error = err

        worker = Thread(target=sleepy_select, args=[self.cnx])
        killer = Thread(target=kill, args=[self.cnx.connection_id])
        worker.start()
        killer.start()
        worker.join()
        killer.join()

        self.assertTrue(
            isinstance(
                self.cnx.test_error,
                (errors.InterfaceError, errors.OperationalError),
            )
        )

        self.cnx.close()


class Bug865859(tests.MySQLConnectorTests):
    """lp: 865859: sock.recv fails to return in some cases (infinite wait)"""

    def setUp(self):
        self.table_name = "Bug865859"

    @cnx_config(connection_timeout=1)
    @foreach_cnx()
    def test_reassign_connection(self):
        cur = self.cnx.cursor()
        cur.execute(f"DROP TABLE IF EXISTS {self.table_name}")
        cur.execute(
            f"""
            CREATE TABLE {self.table_name}
            (id INT AUTO_INCREMENT PRIMARY KEY, c1 INT)
            """
        )
        cur.execute(f"INSERT INTO {self.table_name} (c1) VALUES (1)")

        try:
            # We create a new cnx, replacing current
            self.cnx = self.cnx.__class__(**self.config)
            cur = self.cnx.cursor()
            cur.execute("DROP TABLE IF EXISTS {0}".format(self.table_name))
        except errors.InterfaceError as err:
            self.fail("Connection was not closed, we got timeout: {0}".format(err))
        else:
            cur.close()
            self.cnx.close()


class BugOra13395083(tests.MySQLConnectorTests):
    """BUG#13395083: Using time zones"""

    def setUp(self):
        self.table_name = "BugOra13395083"

    def tearDown(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        cur = cnx.cursor()

        cur.execute("DROP TABLE IF EXISTS {0}".format(self.table_name))

    @cnx_config(time_zone="+00:00")
    @foreach_cnx()
    def test_time_zone(self):
        utc = tests.UTCTimeZone()
        testzone = tests.TestTimeZone(+2)

        # Store a datetime in UTC into a TIMESTAMP column
        now_utc = datetime.utcnow().replace(microsecond=0, tzinfo=utc)

        cur = self.cnx.cursor()
        cur.execute(f"DROP TABLE IF EXISTS {self.table_name}")
        cur.execute(
            f"""
            CREATE TABLE {self.table_name}
            (id INT AUTO_INCREMENT PRIMARY KEY, c1 TIMESTAMP)
            """
        )
        cur.execute(f"INSERT INTO {self.table_name} (c1) VALUES (%s)", (now_utc,))
        self.cnx.commit()

        cur.execute(f"SELECT c1 FROM {self.table_name}")
        row = cur.fetchone()
        self.assertEqual(now_utc, row[0].replace(tzinfo=utc))

        self.cnx.time_zone = "+02:00"
        cur.execute(f"SELECT c1 FROM {self.table_name}")
        row = cur.fetchone()
        self.assertEqual(now_utc.astimezone(testzone), row[0].replace(tzinfo=testzone))

        self.cnx.close()


class BugOra13392739(tests.MySQLConnectorTests):
    """BUG#13392739: MySQLConnection.ping()"""

    @cnx_config(connection_timeout=2, unix_socket=None)
    @foreach_cnx()
    def test_ping(self):
        cnx = self.cnx.__class__()
        self.assertRaises(errors.InterfaceError, cnx.ping)

        try:
            self.cnx.ping()
        except Exception as e:
            self.fail("Error raised although connection should be available (%s)." % e)

        self.cnx.close()
        self.assertRaises(errors.InterfaceError, self.cnx.ping)

        try:
            self.cnx.ping(reconnect=True)
        except Exception as e:
            self.fail("Error raised although ping should reconnect. (%s)" % e)

        # Temper with the host to which we reconnect to simulate the
        # MySQL not being available.
        self.cnx.disconnect()
        self.cnx._host = "some-unknown-host-somwhere-on.mars"
        self.assertRaises(errors.InterfaceError, self.cnx.ping, reconnect=True)

    @cnx_config(connection_timeout=2, unix_socket=None)
    @foreach_cnx()
    def test_reconnect(self):
        self.cnx.disconnect()
        self.assertRaises(errors.InterfaceError, self.cnx.ping)
        try:
            self.cnx.reconnect()
        except:
            self.fail("Errors raised although connection should have been reconnected.")

        self.cnx.disconnect()
        # Temper with the host to which we reconnect to simulate the
        # MySQL not being available.
        self.cnx._host = "some-unknown-host-somwhere-on-mars.example.com"
        self.assertRaises(errors.InterfaceError, self.cnx.reconnect)
        try:
            self.cnx.reconnect(attempts=3)
        except errors.InterfaceError as exc:
            self.assertTrue("3 attempt(s)" in str(exc))


@unittest.skipIf(sys.version_info < (3, 5), "Objects not collected by GC.")
class BugOra13435186(tests.MySQLConnectorTests):
    def setUp(self):
        self.sample_size = 100
        self.tolerate = 5
        self._reset_samples()
        self.samples = [
            0,
        ] * self.sample_size
        gc.collect()

    def _reset_samples(self):
        self.samples = [
            0,
        ] * self.sample_size

    def _assert_flat_line(self, samples):
        counters = {}
        for value in samples:
            try:
                counters[value] = counters[value] + 1
            except KeyError:
                counters[value] = 1

        if len(counters) > self.tolerate:
            self.fail(
                "Counters {} of collected object higher than tolerated."
                "".format(len(counters))
            )

    def test_converter(self):
        for i in range(0, self.sample_size):
            conversion.MySQLConverter()
            self.samples[i] = len(gc.get_objects())

        self._assert_flat_line(self.samples)

    @foreach_cnx()
    def test_connection(self):
        # Create a connection and close using close()-method
        for i in range(0, self.sample_size):
            cnx = self.cnx.__class__(**self.config)
            cnx.close()
            self.samples[i] = len(gc.get_objects())

        self._assert_flat_line(self.samples)

        self._reset_samples()
        # Create a connection and rely on destructor to close
        for i in range(0, self.sample_size):
            cnx = self.cnx.__class__(**self.config)
            self.samples[i] = len(gc.get_objects())

        self._assert_flat_line(self.samples)

    @foreach_cnx()
    def test_cursor(self):
        # Create a cursor and close using close()-method
        for i in range(0, self.sample_size):
            cursor = self.cnx.cursor()
            cursor.close()
            self.samples[i] = len(gc.get_objects())

        self._assert_flat_line(self.samples)

        self._reset_samples()
        # Create a cursor and rely on destructor to close
        for i in range(0, self.sample_size):
            cursor = self.cnx.cursor()
            self.samples[i] = len(gc.get_objects())

        self._assert_flat_line(self.samples)


class BugOra14184643(tests.MySQLConnectorTests):
    """BUG#14184643: cmd_query() disregards waiting results"""

    @foreach_cnx()
    def test_cmd_query(self):
        self.cnx.cmd_query("SELECT 1")
        self.assertRaises(errors.InternalError, self.cnx.cmd_query, "SELECT 2")

    @foreach_cnx(connection.MySQLConnection)
    def test_get_rows(self):
        self.cnx.cmd_query("SELECT 1")
        self.cnx.get_rows()
        self.assertRaises(errors.InternalError, self.cnx.get_rows)

        self.cnx.cmd_query("SELECT 1")
        self.cnx.get_row()
        self.assertEqual(None, self.cnx.get_row()[0])
        self.assertRaises(errors.InternalError, self.cnx.get_row)

    @unittest.skipIf(not CMySQLConnection, ERR_NO_CEXT)
    @foreach_cnx(CMySQLConnection)
    def test_get_rows(self):
        self.cnx.cmd_query("SELECT 1")
        while True:
            self.cnx.get_rows()
            if not self.cnx.next_result():
                break
            else:
                self.fail("Found multiple results where only 1 was expected")
        self.assertRaises(errors.InternalError, self.cnx.get_rows)

    @foreach_cnx()
    def test_cmd_statistics(self):
        self.cnx.cmd_query("SELECT 1")
        self.assertRaises(errors.InternalError, self.cnx.cmd_statistics)
        self.cnx.get_rows()


class BugOra14208326(tests.MySQLConnectorTests):
    """BUG#14208326: cmd_query() does not handle multiple statements."""

    def setUp(self):
        self.table = "BugOra14208326"

    def _setup(self):
        self.cnx.cmd_query(f"DROP TABLE IF EXISTS {self.table}")
        self.cnx.cmd_query(f"CREATE TABLE {self.table} (id INT PRIMARY KEY)")

    def tearDown(self):
        config = tests.get_mysql_config()
        self.cnx = connection.MySQLConnection(**config)

        self.cnx.cmd_query(f"DROP TABLE IF EXISTS {self.table}")

    @foreach_cnx()
    def test_get_rows_does_not_hang_when_cmd_query_runs_with_multi_stmts(self):
        """
        - Verify `cmd_query()` does not raise an error when passing a multi statement.
        - Verify `get_rows()` does not hang if called after executing a multi statement.
        """
        scripts = [
            (
                "set @x = 'hola'; SELECT 12; SELECT 13;",
                3,
                errors.InternalError,
            ),
            (
                "SELECT 1; SELECT 2",
                2,
                errors.InternalError,
            ),
            (
                "SELECT 1; SELECT 2; set @x = 'hola'; select 'bar'",
                4,
                errors.InternalError,
            ),
        ]

        config = {
            **self.get_clean_mysql_config(),
            **{"use_pure": isinstance(self.cnx, connection.MySQLConnection)},
        }
        for script, num_single_stmts, exp_err in scripts:
            with mysql.connector.connect(**config) as cnx:
                try:
                    cnx.cmd_query(script)
                except errors.InterfaceError as e:
                    self.fail("An unexpected exception was raised: {}".format(e))

                with self.assertRaises(exp_err):
                    for _ in range(num_single_stmts):
                        _ = cnx.get_rows()

    @unittest.skipIf(not CMySQLConnection, ERR_NO_CEXT)
    @foreach_cnx(CMySQLConnection)
    def test_cmd_query_iter(self):
        self._setup()
        stmt = "SELECT 1; INSERT INTO %s VALUES (1),(2); SELECT 3"
        results = []
        try:
            for result in self.cnx.cmd_query_iter(stmt % self.table):
                results.append(result)
                if "columns" in result:
                    results.append(self.cnx.get_rows())
        except NotImplementedError:
            # Some cnx are not implementing this
            if not isinstance(self.cnx, CMySQLConnection):
                raise


class BugOra14208326_async(tests.MySQLConnectorAioTestCase):
    """BUG#14208326: cmd_query() does not handle multiple statements."""

    @foreach_cnx_aio()
    async def test_get_rows_does_not_hang_when_cmd_query_runs_with_multi_stmts(self):
        """
        - Verify `cmd_query()` does not raise an error when passing a multi statement.
        - Verify `get_rows()` does not hang if called after executing a multi statement.
        """
        scripts = [
            (
                "set @x = 'hola'; SELECT 12; SELECT 13;",
                3,
                errors.InternalError,
            ),
            (
                "SELECT 1; SELECT 2",
                2,
                errors.InternalError,
            ),
            (
                "SELECT 1; SELECT 2; set @x = 'hola'; select 'bar'",
                4,
                errors.InternalError,
            ),
        ]

        config = {
            **self.get_clean_mysql_config(),
            **{
                "use_pure": isinstance(
                    self.cnx, mysql.connector.aio.connection.MySQLConnection
                )
            },
        }
        for script, num_single_stmts, exp_err in scripts:
            async with await mysql.connector.aio.connect(**config) as cnx:
                try:
                    await cnx.cmd_query(script)
                except errors.InterfaceError as e:
                    self.fail("An unexpected exception was raised: {}".format(e))

                with self.assertRaises(exp_err):
                    for _ in range(num_single_stmts):
                        _ = await cnx.get_rows()


class BugOra14201459(tests.MySQLConnectorTests):
    """BUG#14201459: Server error 1426 should raise ProgrammingError"""

    def setUp(self):
        self.tbl = "Bug14201459"

    def tearDown(self):
        config = tests.get_mysql_config()
        self.cnx = connection.MySQLConnection(**config)
        self._setup()

    def _setup(self):
        self.cnx.cmd_query(f"DROP TABLE IF EXISTS {self.tbl}")

    @foreach_cnx()
    def test_error1426(self):
        cur = self.cnx.cursor()
        self._setup()
        create = f"CREATE TABLE {self.tbl} (id INT PRIMARY KEY, c1 TIME(7))"
        try:
            cur.execute(create)
        except errors.ProgrammingError as exception:
            if tests.MYSQL_VERSION < (5, 6, 4) and exception.errno != 1064:
                self.fail("ProgrammingError is not Error 1064")
            elif tests.MYSQL_VERSION >= (5, 6, 4) and exception.errno != 1426:
                self.fail("ProgrammingError is not Error 1426")
        else:
            self.fail("ProgrammingError not raised")


class BugOra14231160(tests.MySQLConnectorTests):
    """BUG#14231160: lastrowid, description and rowcount read-only"""

    @foreach_cnx()
    def test_readonly_properties(self):
        cur = self.cnx.cursor()
        for attr in ("description", "rowcount", "lastrowid"):
            try:
                setattr(cur, attr, "spam")
            except AttributeError:
                # It's readonly, that's OK
                pass
            else:
                self.fail("Need read-only property: {0}".format(attr))


class BugOra14259954(tests.MySQLConnectorTests):
    """BUG#14259954: ON DUPLICATE KEY UPDATE VALUE FAILS REGEX"""

    def setUp(self):
        self.tbl = "Bug14259954"

    def _setup(self):
        cur = self.cnx.cursor()
        cur.execute("DROP TABLE IF EXISTS %s" % (self.tbl))
        create = (
            "CREATE TABLE %s ( "
            "`id` int(11) NOT NULL AUTO_INCREMENT, "
            "`c1` int(11) NOT NULL DEFAULT '0', "
            "PRIMARY KEY (`id`,`c1`))" % (self.tbl)
        )
        cur.execute(create)

    def tearDown(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        cur = cnx.cursor()
        cur.execute("DROP TABLE IF EXISTS {0}".format(self.tbl))

    @foreach_cnx()
    def test_executemany(self):
        self._setup()
        cur = self.cnx.cursor()
        query = (
            "INSERT INTO %s (id,c1) VALUES (%%s,%%s) "
            "ON DUPLICATE KEY UPDATE c1=VALUES(c1)"
        ) % self.tbl
        try:
            cur.executemany(query, [(1, 1), (2, 2)])
        except errors.ProgrammingError as err:
            self.fail("Regular expression fails with executemany(): %s" % err)


class BugOra14548043(tests.MySQLConnectorTests):
    """BUG#14548043: ERROR MESSAGE SHOULD BE IMPROVED TO DIAGNOSE THE PROBLEM"""

    @foreach_cnx()
    def test_unix_socket(self):
        config = self.config.copy()
        config["unix_socket"] = os.path.join(
            tempfile.gettempdir(), "a" * 100 + "myconnpy_bug14548043.test"
        )

        try:
            cnx = self.cnx.__class__(**config)
        except errors.InterfaceError as exc:
            self.assertEqual(2002, exc.errno)


class BugOra14754894(tests.MySQLConnectorTests):
    """BUG#14754894: MYSQLCURSOR.EXECUTEMANY() FAILS WHEN USING THE PYFOR..."""

    def setUp(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        self.tbl = "BugOra14754894"
        cnx.cmd_query(f"DROP TABLE IF EXISTS {self.tbl}")
        cnx.cmd_query(f"CREATE TABLE {self.tbl} (c1 INT AUTO_INCREMENT PRIMARY KEY)")

    def tearDown(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        cnx.cmd_query(f"DROP TABLE IF EXISTS {self.tbl}")

    @foreach_cnx()
    def test_executemany(self):
        self.cnx.cmd_query(f"TRUNCATE TABLE {self.tbl}")
        cur = self.cnx.cursor()

        insert = f"INSERT INTO {self.tbl} (c1) VALUES (%(c1)s)"
        data = [{"c1": 1}]

        try:
            cur.executemany(insert, [{"c1": 1}])
        except ValueError as err:
            self.fail(err)

        cur.execute(f"SELECT c1 FROM {self.tbl}")
        self.assertEqual(data[0]["c1"], cur.fetchone()[0])

        cur.close()


@unittest.skipIf(not tests.IPV6_AVAILABLE, "IPv6 testing disabled")
class BugOra15876886(tests.MySQLConnectorTests):
    """BUG#15876886: CONNECTOR/PYTHON CAN NOT CONNECT TO MYSQL THROUGH IPV6"""

    @foreach_cnx()
    def test_ipv6(self):
        config = self.config.copy()
        config["host"] = "::1"
        config["unix_socket"] = None
        try:
            cnx = self.cnx.__class__(**config)
        except errors.InterfaceError as err:
            self.fail("Can not connect using IPv6: {0}".format(str(err)))
        else:
            cnx.close()


class BugOra15915243(tests.MySQLConnectorTests):
    """BUG#15915243: PING COMMAND ALWAYS RECONNECTS TO THE DATABASE"""

    @foreach_cnx()
    def test_ping(self):
        cid = self.cnx.connection_id
        self.cnx.ping()
        # Do not reconnect
        self.assertEqual(cid, self.cnx.connection_id)
        self.cnx.close()
        # Do not reconnect
        self.assertRaises(errors.InterfaceError, self.cnx.ping)
        # Do reconnect
        self.cnx.ping(reconnect=True)
        self.assertNotEqual(cid, self.cnx.connection_id)
        self.cnx.close()


class BugOra15916486(tests.MySQLConnectorTests):
    """BUG#15916486: RESULTS AFTER STORED PROCEDURE WITH ARGUMENTS ARE NOT KEPT"""

    def setUp(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        cur = cnx.cursor()

        cur.execute("DROP PROCEDURE IF EXISTS sp1")
        cur.execute("DROP PROCEDURE IF EXISTS sp2")
        sp1 = (
            "CREATE PROCEDURE sp1(IN pIn INT, OUT pOut INT)"
            " BEGIN SELECT 1; SET pOut := pIn; SELECT 2; END"
        )
        sp2 = "CREATE PROCEDURE sp2 () BEGIN SELECT 1; SELECT 2; END"

        cur.execute(sp1)
        cur.execute(sp2)
        cnx.close()

    def tearDown(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        cur = cnx.cursor()
        try:
            cur.execute("DROP PROCEDURE IF EXISTS sp1")
            cur.execute("DROP PROCEDURE IF EXISTS sp2")
        except:
            pass  # Clean up fail is acceptable for this test

        cnx.close()

    @foreach_cnx()
    def test_callproc_with_args(self):
        cur = self.cnx.cursor()
        exp = (5, 5)
        self.assertEqual(exp, cur.callproc("sp1", (5, 0)))

        exp = [[(1,)], [(2,)]]
        results = []
        for result in cur.stored_results():
            results.append(result.fetchall())
        self.assertEqual(exp, results)

    @foreach_cnx()
    def test_callproc_without_args(self):
        cur = self.cnx.cursor()
        exp = ()
        self.assertEqual(exp, cur.callproc("sp2"))

        exp = [[(1,)], [(2,)]]
        results = []
        for result in cur.stored_results():
            results.append(result.fetchall())
        self.assertEqual(exp, results)


@unittest.skipIf(
    tests.MYSQL_EXTERNAL_SERVER,
    "Test not available for external MySQL servers",
)
@unittest.skipIf(
    os.name == "nt",
    "Cannot test error handling when doing handshake on Windows",
)
@unittest.skipIf(tests.MYSQL_VERSION > (8, 0, 4), "Revoked users can no more grant")
class BugOra15836979(tests.MySQLConnectorTests):
    """BUG#15836979: UNCLEAR ERROR MESSAGE CONNECTING USING UNALLOWED IP ADDRESS"""

    def setUp(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        cnx.cmd_query("DROP USER 'root'@'127.0.0.1'")
        try:
            cnx.cmd_query("DROP USER 'root'@'::1'")
        except errors.DatabaseError:
            # Some MySQL servers have no IPv6 entry
            pass
        cnx.close()

    def tearDown(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        cnx.cmd_query(
            "GRANT ALL PRIVILEGES ON *.* TO 'root'@'127.0.0.1' WITH GRANT OPTION"
        )
        cnx.cmd_query("GRANT ALL PRIVILEGES ON *.* TO 'root'@'::1' WITH GRANT OPTION")
        cnx.close()

    @foreach_cnx()
    def test_handshake(self):
        config = self.config.copy()
        config["host"] = "127.0.0.1"
        config["unix_socket"] = None
        try:
            self.cnx.__class__(**config)
        except errors.Error as exc:
            self.assertTrue(
                "Access denied" in str(exc) or "not allowed" in str(exc),
                "Wrong error message, was: {0}".format(str(exc)),
            )


class BugOra16217743(tests.MySQLConnectorTests):
    """BUG#16217743: CALLPROC FUNCTION WITH STRING PARAMETERS"""

    def setUp(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)

        cnx.cmd_query("DROP TABLE IF EXISTS bug16217743")
        cnx.cmd_query("DROP PROCEDURE IF EXISTS sp_bug16217743")
        cnx.cmd_query("CREATE TABLE bug16217743 (c1 VARCHAR(20), c2 INT PRIMARY KEY)")
        cnx.cmd_query(
            "CREATE PROCEDURE sp_bug16217743 (p1 VARCHAR(20), p2 INT) "
            "BEGIN INSERT INTO bug16217743 (c1, c2) "
            "VALUES (p1, p2); END;"
        )

    def tearDown(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        cnx.cmd_query("DROP TABLE IF EXISTS bug16217743")
        cnx.cmd_query("DROP PROCEDURE IF EXISTS sp_bug16217743")

    @foreach_cnx()
    def test_procedure(self):
        exp = ("ham", 42)
        cur = self.cnx.cursor()
        cur.callproc("sp_bug16217743", ("ham", 42))
        cur.execute("SELECT c1, c2 FROM bug16217743")
        self.assertEqual(exp, cur.fetchone())


@unittest.skipIf(
    tests.MYSQL_EXTERNAL_SERVER,
    "Test not available for external MySQL servers",
)
@unittest.skipIf(
    not tests.SSL_AVAILABLE,
    "BugOra16217667 test failed. Python lacks SSL support.",
)
class BugOra16217667(tests.MySQLConnectorTests):
    """BUG#16217667: PYTHON CONNECTOR 3.2 SSL CONNECTION FAILS"""

    def setUp(self):
        config = tests.get_mysql_config()
        self.admin_cnx = connection.MySQLConnection(**config)

        self.admin_cnx.cmd_query(
            "CREATE USER 'ssluser'@'{host}'".format(
                db=config["database"], host=tests.get_mysql_config()["host"]
            )
        )

        if tests.MYSQL_VERSION < (5, 7, 21):
            self.admin_cnx.cmd_query(
                "GRANT ALL ON {db}.* TO 'ssluser'@'{host}' REQUIRE X509"
                "".format(
                    db=config["database"],
                    host=tests.get_mysql_config()["host"],
                )
            )
        else:
            self.admin_cnx.cmd_query(
                "GRANT ALL ON {db}.* TO 'ssluser'@'{host}'"
                "".format(
                    db=config["database"],
                    host=tests.get_mysql_config()["host"],
                )
            )

            self.admin_cnx.cmd_query(
                "ALTER USER 'ssluser'@'{host}' REQUIRE X509"
                "".format(
                    db=config["database"],
                    host=tests.get_mysql_config()["host"],
                )
            )

    def tearDown(self):
        self.admin_cnx.cmd_query(
            "DROP USER 'ssluser'@'{0}'".format(tests.get_mysql_config()["host"])
        )

    @foreach_cnx()
    def test_sslauth(self):
        config = self.config.copy()
        config["user"] = "ssluser"
        config["password"] = ""
        config["unix_socket"] = None
        config["ssl_verify_cert"] = True
        config.update(
            {
                "ssl_ca": os.path.abspath(
                    os.path.join(tests.SSL_DIR, "tests_CA_cert.pem")
                ),
                "ssl_cert": os.path.abspath(
                    os.path.join(tests.SSL_DIR, "tests_client_cert.pem")
                ),
                "ssl_key": os.path.abspath(
                    os.path.join(tests.SSL_DIR, "tests_client_key.pem")
                ),
            }
        )

        try:
            self.cnx = self.cnx.__class__(**config)
        except errors.Error as exc:
            self.assertTrue("ssl" in str(exc).lower(), str(exc))

        self.cnx.cmd_query("SHOW STATUS LIKE 'Ssl_cipher'")
        self.assertTrue(self.cnx.get_rows()[0][0] != "")


@unittest.skipIf(
    tests.MYSQL_EXTERNAL_SERVER,
    "Test not available for external MySQL servers",
)
@unittest.skipIf(
    not tests.SSL_AVAILABLE,
    "BugOra16316049 test failed. Python lacks SSL support.",
)
class BugOra16316049(tests.MySQLConnectorTests):
    """SSL ERROR: [SSL: TLSV1_ALERT_UNKNOWN_CA] AFTER FIX 6217667"""

    def setUp(self):
        config = tests.get_mysql_config()
        self.host = config["host"]
        cnx = connection.MySQLConnection(**config)

        if tests.MYSQL_VERSION < (5, 7, 21):
            cnx.cmd_query(
                "GRANT ALL ON {db}.* TO 'ssluser'@'{host}' REQUIRE SSL".format(
                    db=config["database"],
                    host=tests.get_mysql_config()["host"],
                )
            )
        else:
            cnx.cmd_query(
                "CREATE USER 'ssluser'@'{host}'".format(
                    db=config["database"],
                    host=tests.get_mysql_config()["host"],
                )
            )

            cnx.cmd_query(
                "GRANT ALL ON {db}.* TO 'ssluser'@'{host}'".format(
                    db=config["database"],
                    host=tests.get_mysql_config()["host"],
                )
            )

            cnx.cmd_query(
                "ALTER USER 'ssluser'@'{host}' REQUIRE SSL".format(
                    db=config["database"],
                    host=tests.get_mysql_config()["host"],
                )
            )

        cnx.close()

    def tearDown(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        cnx.cmd_query("DROP USER 'ssluser'@'{host}'".format(host=self.host))
        cnx.close()

    @foreach_cnx()
    def test_ssl(self):
        ssl_ca = os.path.abspath(os.path.join(tests.SSL_DIR, "tests_CA_cert.pem"))
        ssl_cert = os.path.abspath(os.path.join(tests.SSL_DIR, "tests_client_cert.pem"))
        ssl_key = os.path.abspath(os.path.join(tests.SSL_DIR, "tests_client_key.pem"))

        config = self.config.copy()
        config.update(
            {
                "ssl_ca": None,
                "ssl_cert": None,
                "ssl_key": None,
            }
        )

        # Use wrong value for ssl_ca
        config["user"] = "ssluser"
        config["password"] = ""
        config["unix_socket"] = None
        config["ssl_ca"] = os.path.abspath(
            os.path.join(tests.SSL_DIR, "tests_casdfasdfdsaa_cert.pem")
        )
        config["ssl_cert"] = ssl_cert
        config["ssl_key"] = ssl_key
        config["ssl_verify_cert"] = True

        # An Exception should be raised
        try:
            self.cnx.__class__(**config)
        except errors.Error as exc:
            exc_str = str(exc).lower()
            self.assertTrue("ssl" in exc_str or "no such file" in exc_str)

        # Use correct value
        config["ssl_ca"] = ssl_ca
        config["host"] = "localhost"  # common name must be equal
        try:
            self.cnx = self.cnx.__class__(**config)
        except errors.Error as exc:
            if exc.errno == 1045 and ":" not in self.host:
                # For IPv4
                self.fail("Auth failed:" + str(exc))

        if ":" in self.host:
            # Special case for IPv6
            config["ssl_verify_cert"] = False
            config["host"] = self.host
            try:
                self.cnx = self.cnx.__class__(**config)
            except errors.Error as exc:
                if exc.errno == 1045 and not tests.IPV6_AVAILABLE:
                    self.fail("Auth failed:" + str(exc))

        self.cnx.cmd_query("SHOW STATUS LIKE 'Ssl_cipher'")
        self.assertTrue(self.cnx.get_rows()[0][0] != "")


class BugOra16662920(tests.MySQLConnectorTests):
    """BUG#16662920: FETCHALL() IGNORES NEXT_ROW FOR BUFFERED CURSORS"""

    def setUp(self):
        self.tbl = "BugOra16662920"
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        cur = cnx.cursor()

        cur.execute("DROP TABLE IF EXISTS {0}".format(self.tbl))
        cur.execute(
            "CREATE TABLE {0} (id INT AUTO_INCREMENT, c1 VARCHAR(20), "
            "PRIMARY KEY (id)) ENGINE=InnoDB".format(self.tbl)
        )

        data = [("a",), ("c",), ("e",), ("d",), ("g",), ("f",)]
        cur.executemany("INSERT INTO {0} (c1) VALUES (%s)".format(self.tbl), data)
        cur.close()
        cnx.commit()

    def tearDown(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        cur = cnx.cursor()
        cur.execute("DROP TABLE IF EXISTS {0}".format(self.tbl))
        cnx.close()

    @foreach_cnx()
    def test_buffered(self):
        cur = self.cnx.cursor(buffered=True)
        cur.execute("SELECT * FROM {0} ORDER BY c1".format(self.tbl))
        self.assertEqual((1, "a"), cur.fetchone())
        exp = [(2, "c"), (4, "d"), (3, "e")]
        self.assertEqual(exp, cur.fetchmany(3))
        exp = [(6, "f"), (5, "g")]
        self.assertEqual(exp, cur.fetchall())
        cur.close()

    @foreach_cnx()
    def test_buffered_raw(self):
        cur = self.cnx.cursor(buffered=True, raw=True)
        cur.execute("SELECT * FROM {0} ORDER BY c1".format(self.tbl))
        exp_one = (b"1", b"a")
        exp_many = [(b"2", b"c"), (b"4", b"d"), (b"3", b"e")]
        exp_all = [(b"6", b"f"), (b"5", b"g")]

        self.assertEqual(exp_one, cur.fetchone())
        self.assertEqual(exp_many, cur.fetchmany(3))
        self.assertEqual(exp_all, cur.fetchall())
        cur.close()


class BugOra17041412(tests.MySQLConnectorTests):
    """BUG#17041412: FETCHALL() DOES NOT RETURN SELF._NEXTROW IF AVAILABLE"""

    def setUp(self):
        self.table_name = "BugOra17041412"
        self.data = [(1,), (2,), (3,)]
        self.data_raw = [(b"1",), (b"2",), (b"3",)]

    def _setup(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        cur = cnx.cursor()
        cur.execute("DROP TABLE IF EXISTS %s" % self.table_name)
        cur.execute("CREATE TABLE %s (c1 INT PRIMARY KEY)" % self.table_name)
        cur.executemany("INSERT INTO %s (c1) VALUES (%%s)" % self.table_name, self.data)
        cnx.commit()

    def tearDown(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        cur = cnx.cursor()
        cur.execute("DROP TABLE IF EXISTS %s" % self.table_name)

    @foreach_cnx()
    def test_one_all(self):
        self._setup()
        cur = self.cnx.cursor()
        cur.execute("SELECT * FROM %s ORDER BY c1" % self.table_name)
        self.assertEqual(self.data[0], cur.fetchone())
        self.assertEqual(1, cur.rowcount)
        self.assertEqual(self.data[1:], cur.fetchall())
        self.assertEqual(3, cur.rowcount)

    @foreach_cnx()
    def test_many_all(self):
        self._setup()
        cur = self.cnx.cursor()
        cur.execute("SELECT * FROM %s ORDER BY c1" % self.table_name)
        self.assertEqual(self.data[0:2], cur.fetchmany(2))
        self.assertEqual(2, cur.rowcount)
        self.assertEqual(self.data[2:], cur.fetchall())
        self.assertEqual(3, cur.rowcount)

    @foreach_cnx()
    def test_many(self):
        self._setup()
        cur = self.cnx.cursor()
        cur.execute("SELECT * FROM %s ORDER BY c1" % self.table_name)
        self.assertEqual(self.data, cur.fetchall())
        self.assertEqual(3, cur.rowcount)

        cur.execute(
            "SELECT * FROM %s WHERE c1 > %%s" % self.table_name,
            (self.data[-1][0] + 100,),
        )
        self.assertEqual([], cur.fetchall())

    @foreach_cnx()
    def test_raw_one_all(self):
        self._setup()
        cur = self.cnx.cursor(raw=True)
        cur.execute("SELECT * FROM %s ORDER BY c1" % self.table_name)
        self.assertEqual(self.data_raw[0], cur.fetchone())
        self.assertEqual(1, cur.rowcount)
        self.assertEqual(self.data_raw[1:], cur.fetchall())
        self.assertEqual(3, cur.rowcount)

    @foreach_cnx()
    def test_raw_many_all(self):
        self._setup()
        cur = self.cnx.cursor(raw=True)
        cur.execute("SELECT * FROM %s ORDER BY c1" % self.table_name)
        self.assertEqual(self.data_raw[0:2], cur.fetchmany(2))
        self.assertEqual(2, cur.rowcount)
        self.assertEqual(self.data_raw[2:], cur.fetchall())
        self.assertEqual(3, cur.rowcount)

    @foreach_cnx()
    def test_raw_many(self):
        self._setup()
        cur = self.cnx.cursor(raw=True)
        cur.execute("SELECT * FROM %s ORDER BY c1" % self.table_name)
        self.assertEqual(self.data_raw, cur.fetchall())
        self.assertEqual(3, cur.rowcount)

        cur.execute("SELECT * FROM %s WHERE c1 > 1000" % self.table_name)
        self.assertEqual([], cur.fetchall())


class BugOra16819486(tests.MySQLConnectorTests):
    """BUG#16819486: ERROR 1210 TO BE HANDLED"""

    def setUp(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        cur = cnx.cursor()
        cur.execute("DROP TABLE IF EXISTS BugOra16819486")
        cur.execute("CREATE TABLE BugOra16819486 (c1 INT PRIMARY KEY, c2 INT)")
        cur.executemany(
            "INSERT INTO BugOra16819486 VALUES (%s, %s)",
            [(1, 10), (2, 20), (3, 30)],
        )
        cnx.commit()

    def tearDown(self):
        cnx = connection.MySQLConnection(**tests.get_mysql_config())
        cur = cnx.cursor()
        cur.execute("DROP TABLE IF EXISTS BugOra16819486")
        cnx.close()

    @foreach_cnx()
    def test_error1210(self):
        cur = self.cnx.cursor(prepared=True)
        prep_stmt = "SELECT * FROM BugOra16819486 WHERE c1 = %s AND c2 = %s"
        self.assertRaises(
            mysql.connector.ProgrammingError, cur.execute, prep_stmt, (1,)
        )

        prep_stmt = "SELECT * FROM BugOra16819486 WHERE c1 = %s AND c2 = %s"
        exp = [(1, 10)]
        cur.execute(prep_stmt, (1, 10))
        self.assertEqual(exp, cur.fetchall())


class BugOra16656621(tests.MySQLConnectorTests):
    """BUG#16656621: IMPOSSIBLE TO ROLLBACK WITH UNREAD RESULTS"""

    def setUp(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        cur = cnx.cursor()

        cur.execute("DROP TABLE IF EXISTS BugOra16656621")
        cur.execute(
            "CREATE TABLE BugOra16656621 "
            "(id INT AUTO_INCREMENT, c1 VARCHAR(20), "
            "PRIMARY KEY (id)) ENGINE=InnoDB"
        )

    def tearDown(self):
        cnx = connection.MySQLConnection(**tests.get_mysql_config())
        cur = cnx.cursor()
        cur.execute("DROP TABLE IF EXISTS BugOra16656621")

    @foreach_cnx()
    def test_rollback(self):
        cur = self.cnx.cursor()
        cur.execute("INSERT INTO BugOra16656621 (c1) VALUES ('a'),('b'),('c')")
        self.cnx.commit()

        cur.execute("SELECT * FROM BugOra16656621")
        try:
            self.cnx.rollback()
        except mysql.connector.InternalError:
            self.fail("Rollback not possible with unread results")


class BugOra16660356(tests.MySQLConnectorTests):
    """BUG#16660356: USING EXECUTEMANY WITH EMPTY DATA SHOULD DO NOTHING"""

    def setUp(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        cur = cnx.cursor()

        cur.execute("DROP TABLE IF EXISTS bug16660356")
        cur.execute(
            "CREATE TABLE bug16660356 (id INT AUTO_INCREMENT, c1 VARCHAR(20), "
            "PRIMARY KEY (id)) ENGINE=InnoDB"
        )
        cnx.close()

    def tearDown(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        cnx.cmd_query("DROP TABLE IF EXISTS bug16660356")
        cnx.close()

    @foreach_cnx()
    def test_executemany(self):
        cur = self.cnx.cursor()
        try:
            cur.executemany("INSERT INTO bug16660356 (c1) VALUES (%s)", [])
        except mysql.connector.ProgrammingError:
            self.fail("executemany raise ProgrammingError with empty data")


class BugOra17041240(tests.MySQLConnectorTests):
    """BUG#17041240: UNCLEAR ERROR CLOSING CURSOR WITH UNREAD RESULTS"""

    def setUp(self):
        self.table_name = "BugOra17041240"
        self.data = [(1,), (2,), (3,)]

    def _setup(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        cur = cnx.cursor()
        cur.execute(f"DROP TABLE IF EXISTS {self.table_name}")
        cur.execute(f"CREATE TABLE {self.table_name} (c1 INT PRIMARY KEY)")
        cur.executemany(
            f"INSERT INTO {self.table_name} (c1) VALUES (%s)",
            self.data,
        )
        cnx.commit()
        cnx.close()

    def tearDown(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        cur = cnx.cursor()
        cur.execute("DROP TABLE IF EXISTS {table}".format(table=self.table_name))
        cnx.close()

    @foreach_cnx()
    def test_cursor_close(self):
        self._setup()
        cur = self.cnx.cursor()
        cur.execute("SELECT * FROM {table} ORDER BY c1".format(table=self.table_name))
        self.assertEqual(self.data[0], cur.fetchone())
        self.assertEqual(self.data[1], cur.fetchone())
        self.assertRaises(mysql.connector.InternalError, cur.close)
        self.assertEqual(self.data[2], cur.fetchone())

    @foreach_cnx()
    def test_cursor_new(self):
        self._setup()
        cur = self.cnx.cursor()
        cur.execute("SELECT * FROM {table} ORDER BY c1".format(table=self.table_name))
        self.assertEqual(self.data[0], cur.fetchone())
        self.assertEqual(self.data[1], cur.fetchone())
        self.assertRaises(mysql.connector.InternalError, self.cnx.cursor)
        self.assertEqual(self.data[2], cur.fetchone())


class BugOra17065366(tests.MySQLConnectorTests):
    """BUG#17065366: EXECUTEMANY FAILS USING MYSQL FUNCTION FOR INSERTS"""

    def _setup(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        cur = cnx.cursor()
        self.table_name = "BugOra17065366"
        cur.execute("DROP TABLE IF EXISTS {table}".format(table=self.table_name))
        cur.execute(
            "CREATE TABLE {table} ( "
            "id INT UNSIGNED NOT NULL AUTO_INCREMENT KEY, "
            "c1 INT, c2 DATETIME) ENGINE=INNODB".format(table=self.table_name)
        )
        cnx.close()

    def tearDown(self):
        cnx = connection.MySQLConnection(**tests.get_mysql_config())
        cur = cnx.cursor()
        cur.execute("DROP TABLE IF EXISTS {table}".format(table=self.table_name))
        cnx.close()

    @foreach_cnx()
    def test_executemany(self):
        self._setup()
        cur = self.cnx.cursor()

        adate = datetime(2012, 9, 30)
        stmt = (
            "INSERT INTO {table} (id, c1, c2) "
            "VALUES (%s, %s, DATE('{date} 13:07:00'))"
            "/* Using DATE() */ ON DUPLICATE KEY UPDATE c1 = id"
        ).format(table=self.table_name, date=adate.strftime("%Y-%m-%d"))

        exp = [
            (1, 0, datetime(2012, 9, 30, 0, 0)),
            (2, 0, datetime(2012, 9, 30, 0, 0)),
        ]
        cur.executemany(stmt, [(None, 0), (None, 0)])
        self.cnx.commit()
        cur.execute("SELECT * FROM {table}".format(table=self.table_name))
        rows = cur.fetchall()
        self.assertEqual(exp, rows)

        exp = [
            (1, 1, datetime(2012, 9, 30, 0, 0)),
            (2, 2, datetime(2012, 9, 30, 0, 0)),
        ]
        cur.executemany(stmt, [(1, 1), (2, 2)])
        self.cnx.commit()
        cur.execute("SELECT * FROM {table}".format(table=self.table_name))
        rows = cur.fetchall()
        self.assertEqual(exp, rows)


class BugOra16933795(tests.MySQLConnectorTests):
    """BUG#16933795: ERROR.MSG ATTRIBUTE DOES NOT CONTAIN CORRECT VALUE"""

    def test_error(self):
        exp = "Some error message"
        error = mysql.connector.Error(msg=exp, errno=-1024)
        self.assertEqual(exp, error.msg)

        exp = "Unknown MySQL error"
        error = mysql.connector.Error(errno=2000)
        self.assertEqual(exp, error.msg)
        self.assertEqual("2000: " + exp, str(error))


class BugOra17022399(tests.MySQLConnectorTests):
    """BUG#17022399: EXECUTING AFTER CONNECTION CLOSED GIVES UNCLEAR ERROR"""

    @foreach_cnx()
    def test_execute(self):
        cur = self.cnx.cursor()
        self.cnx.close()
        try:
            cur.execute("SELECT 1")
        except (
            mysql.connector.OperationalError,
            mysql.connector.ProgrammingError,
        ) as exc:
            self.assertEqual(2055, exc.errno, "Was: " + str(exc))

    @cnx_config(client_flags=[constants.ClientFlag.COMPRESS])
    @foreach_cnx()
    def test_execute_compressed(self):
        cur = self.cnx.cursor()
        self.cnx.close()
        try:
            cur.execute("SELECT 1")
        except (
            mysql.connector.OperationalError,
            mysql.connector.ProgrammingError,
        ) as exc:
            self.assertEqual(2055, exc.errno, "Was: " + str(exc))


@unittest.skipIf(
    tests.MYSQL_EXTERNAL_SERVER,
    "Test not available for external MySQL servers",
)
class BugOra16369511(tests.MySQLConnectorTests):
    """BUG#16369511: LOAD DATA LOCAL INFILE IS MISSING"""

    def setUp(self):
        self.data_file = os.path.join("tests", "data", "local_data.csv")

    def _setup(self):
        cnx = connection.MySQLConnection(**tests.get_mysql_config())
        cnx.cmd_query("DROP TABLE IF EXISTS local_data")
        cnx.cmd_query(
            "CREATE TABLE local_data (id INT PRIMARY KEY, c1 VARCHAR(6), c2 VARCHAR(6))"
        )
        cnx.close()

    def tearDown(self):
        cnx = connection.MySQLConnection(**tests.get_mysql_config())
        cnx.cmd_query("DROP TABLE IF EXISTS local_data")
        cnx.close()

    @foreach_cnx(allow_local_infile=True)
    def test_load_csv(self):
        self._setup()
        cur = self.cnx.cursor()
        sql = "LOAD DATA LOCAL INFILE %s INTO TABLE local_data"
        cur.execute(sql, (self.data_file,))
        cur.execute("SELECT * FROM local_data")

        exp = [
            (1, "c1_1", "c2_1"),
            (2, "c1_2", "c2_2"),
            (3, "c1_3", "c2_3"),
            (4, "c1_4", "c2_4"),
            (5, "c1_5", "c2_5"),
            (6, "c1_6", "c2_6"),
        ]

        self.assertEqual(exp, cur.fetchall())

    @cnx_config(compress=True, allow_local_infile=True)
    @foreach_cnx()
    def test_load_csv_with_compress(self):
        self._setup()
        cur = self.cnx.cursor()
        sql = "LOAD DATA LOCAL INFILE %s INTO TABLE local_data"
        cur.execute(sql, (self.data_file,))
        cur.execute("SELECT * FROM local_data")

        exp = [
            (1, "c1_1", "c2_1"),
            (2, "c1_2", "c2_2"),
            (3, "c1_3", "c2_3"),
            (4, "c1_4", "c2_4"),
            (5, "c1_5", "c2_5"),
            (6, "c1_6", "c2_6"),
        ]
        self.assertEqual(exp, cur.fetchall())

    @foreach_cnx(allow_local_infile=True)
    def test_filenotfound(self):
        self._setup()
        cur = self.cnx.cursor()
        sql = "LOAD DATA LOCAL INFILE %s INTO TABLE local_data"
        try:
            cur.execute(sql, (self.data_file + "_spam",))
        except (errors.InterfaceError, errors.DatabaseError) as exc:
            self.assertTrue(
                "not found" in str(exc)
                or "could not be read" in str(exc)
                or "does not exist" in str(exc),
                "Was: " + str(exc),
            )


@unittest.skipIf(
    tests.MYSQL_EXTERNAL_SERVER,
    "Test not available for external MySQL servers",
)
class BugOra17002411(tests.MySQLConnectorTests):
    """BUG#17002411: LOAD DATA LOCAL INFILE FAILS WITH BIGGER FILES"""

    def setUp(self):
        self.data_file = os.path.join("tests", "data", "local_data_big.csv")
        self.exp_rows = 33000

        with open(self.data_file, "w") as fp:
            i = 0
            while i < self.exp_rows:
                fp.write("{0}\t{1}\n".format("a" * 255, "b" * 255))
                i += 1

    def _setup(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        cur = self.cnx.cursor()

        cur.execute("DROP TABLE IF EXISTS local_data")
        cur.execute(
            "CREATE TABLE local_data ("
            "id INT AUTO_INCREMENT PRIMARY KEY, "
            "c1 VARCHAR(255), c2 VARCHAR(255))"
        )

    def tearDown(self):
        cnx = connection.MySQLConnection(**tests.get_mysql_config())
        cnx.cmd_query("DROP TABLE IF EXISTS local_data")
        os.unlink(self.data_file)
        cnx.close()

    @foreach_cnx(allow_local_infile=True)
    def test_load_csv(self):
        self._setup()
        cur = self.cnx.cursor()
        sql = "LOAD DATA LOCAL INFILE %s INTO TABLE local_data (c1, c2)"
        cur.execute(sql, (self.data_file,))
        cur.execute("SELECT COUNT(*) FROM local_data")
        self.assertEqual(self.exp_rows, cur.fetchone()[0])


@unittest.skipIf(
    tests.MYSQL_EXTERNAL_SERVER,
    "Test not available for external MySQL servers",
)
@unittest.skipIf(
    tests.MYSQL_VERSION < (8, 0, 1),
    "The SQL command SHUTDOWN is only available as of MySQL 8.0.1",
)
class BugOra17422299(tests.MySQLConnectorTests):
    """BUG#17422299: cmd_shutdown fails with malformed connection packet"""

    def setUp(self):
        self.config = tests.get_mysql_config()
        self.mysql_server = tests.MYSQL_SERVERS[0]

    def tearDown(self):
        self.ensure_up()

    def ensure_up(self):
        # Start the MySQL server again
        if not self.mysql_server.check_running():
            self.mysql_server.start()

            if not self.mysql_server.wait_up():
                self.fail("Failed restarting MySQL server after test")

    def test_shutdown(self):
        for cnx_class in self.all_cnx_classes:
            self.ensure_up()
            cnx = cnx_class(**self.config)
            try:
                cnx.cmd_shutdown()
            except mysql.connector.DatabaseError as err:
                self.fail("COM_SHUTDOWN failed: {0}".format(err))

            if not self.mysql_server.wait_down():
                self.fail("MySQL not shut down after COM_SHUTDOWN")

    def test_shutdown__with_type(self):
        for cnx_class in self.all_cnx_classes:
            self.ensure_up()
            cnx = cnx_class(**self.config)
            try:
                cnx.cmd_shutdown(constants.ShutdownType.SHUTDOWN_WAIT_ALL_BUFFERS)
            except mysql.connector.DatabaseError as err:
                self.fail("COM_SHUTDOWN failed: {0}".format(err))

            if not self.mysql_server.wait_down():
                self.fail("MySQL not shut down after COM_SHUTDOWN")


class BugOra17215197(tests.MySQLConnectorTests):
    """BUG#17215197: MYSQLCONNECTION.CURSOR(PREPARED=TRUE) NOT POSSIBLE"""

    def _setup(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        cur = cnx.cursor()
        cur.execute("DROP TABLE IF EXISTS BugOra17215197")
        cur.execute("CREATE TABLE BugOra17215197 (c1 INT PRIMARY KEY, c2 INT)")
        cur.executemany(
            "INSERT INTO BugOra17215197 VALUES (%s, %s)",
            [(1, 10), (2, 20), (3, 30)],
        )
        cnx.commit()

    def tearDown(self):
        cnx = connection.MySQLConnection(**tests.get_mysql_config())
        cnx.cmd_query("DROP TABLE IF EXISTS BugOra17215197")

    @foreach_cnx()
    def test_prepared_argument(self):
        self._setup()
        cur = self.cnx.cursor(prepared=True)
        prep_stmt = "SELECT * FROM BugOra17215197 WHERE c1 = %s AND c2 = %s"
        exp = [(1, 10)]
        cur.execute(prep_stmt, (1, 10))
        self.assertEqual(exp, cur.fetchall())


@unittest.skipIf(
    tests.MYSQL_VERSION <= (5, 7, 2),
    "Pool not supported with with MySQL version 5.6",
)
class BugOra17414258(tests.MySQLConnectorTests):
    """BUG#17414258: IT IS ALLOWED TO CHANGE SIZE OF ACTIVE POOL"""

    def setUp(self):
        self.config = tests.get_mysql_config()
        self.config["pool_name"] = "test"
        self.config["pool_size"] = 3
        if tests.MYSQL_VERSION < (5, 7):
            self.config["client_flags"] = [-constants.ClientFlag.CONNECT_ARGS]

    def tearDown(self):
        # Remove pools created by test
        del mysql.connector.pooling._CONNECTION_POOLS[self.config["pool_name"]]

    def test_poolsize(self):
        cnx = mysql.connector.connect(**self.config)
        cnx.close()

        newconfig = self.config.copy()
        newconfig["pool_size"] = self.config["pool_size"] + 1
        self.assertRaises(
            mysql.connector.PoolError, mysql.connector.connect, **newconfig
        )


@unittest.skipIf(
    tests.MYSQL_EXTERNAL_SERVER,
    "Test not available for external MySQL servers",
)
@unittest.skipIf(
    tests.MYSQL_VERSION <= (5, 7, 2),
    "Pool not supported with with MySQL version 5.6",
)
class Bug17578937(tests.MySQLConnectorTests):
    """CONNECTION POOL DOES NOT HANDLE A NOT AVAILABLE MYSQL SERVER"""

    def setUp(self):
        self.mysql_server = tests.MYSQL_SERVERS[0]

    def tearDown(self):
        # Start the MySQL server again
        if not self.mysql_server.check_running():
            self.mysql_server.start()

            if not self.mysql_server.wait_up():
                self.fail("Failed restarting MySQL server after test")

    def test_get_connection(self):
        """Test reconnect once MySQL server is back

        To make the test case simpler, we create a pool which only has
        one connection in the queue. This way we can similuate getting a
        connection from a pool for which the MySQL server is not running.
        """
        config = tests.get_mysql_config().copy()
        if tests.MYSQL_VERSION < (5, 7):
            config["client_flags"] = [-constants.ClientFlag.CONNECT_ARGS]
        config["connection_timeout"] = 2
        cnxpool = pooling.MySQLConnectionPool(pool_name="test", pool_size=1, **config)

        pcnx = cnxpool.get_connection()
        self.assertTrue(isinstance(pcnx, pooling.PooledMySQLConnection))
        pcnx.close()
        self.mysql_server.stop()
        if not self.mysql_server.wait_down():
            self.fail("MySQL not shut down; can not continue test")
        self.assertRaises(errors.InterfaceError, cnxpool.get_connection)

        self.mysql_server.start()
        if not self.mysql_server.wait_up():
            self.fail("MySQL started; can not continue test")
        pcnx = cnxpool.get_connection()
        pcnx.close()


class BugOra17079344(tests.MySQLConnectorTests):
    """BUG#17079344: ERROR WITH GBK STRING WITH CHARACTERS ENCODED AS BACKSLASH"""

    def setUp(self):
        cnx = connection.MySQLConnection(**tests.get_mysql_config())
        cur = cnx.cursor()
        for charset in ("gbk", "sjis", "big5"):
            tablename = charset + "test"
            cur.execute("DROP TABLE IF EXISTS {0}".format(tablename))
            table = (
                "CREATE TABLE {table} ("
                "id INT AUTO_INCREMENT PRIMARY KEY, "
                "c1 VARCHAR(40)"
                ") CHARACTER SET '{charset}'"
            ).format(table=tablename, charset=charset)
            cur.execute(table)
            cnx.commit()
        cur.close()
        cnx.close()

    def tearDown(self):
        cnx = connection.MySQLConnection(**tests.get_mysql_config())
        for charset in ("gbk", "sjis", "big5"):
            tablename = charset + "test"
            cnx.cmd_query("DROP TABLE IF EXISTS {0}".format(tablename))
        cnx.close()

    def _test_charset(self, charset, data):
        config = tests.get_mysql_config()
        config["charset"] = charset
        config["use_unicode"] = True
        self.cnx = self.cnx.__class__(**config)
        tablename = charset + "test"
        cur = self.cnx.cursor()
        cur.execute("TRUNCATE {0}".format(tablename))
        self.cnx.commit()

        insert = "INSERT INTO {0} (c1) VALUES (%s)".format(tablename)
        for value in data:
            cur.execute(insert, (value,))
        self.cnx.commit()

        cur.execute("SELECT id, c1 FROM {0} ORDER BY id".format(tablename))
        for row in cur:
            self.assertEqual(data[row[0] - 1], row[1])

        cur.close()
        self.cnx.close()

    @foreach_cnx()
    def test_gbk(self):
        self._test_charset(
            "gbk",
            [
                "赵孟頫",
                "赵\孟\頫\\",
                "遜",
            ],
        )

    @foreach_cnx()
    def test_sjis(self):
        self._test_charset("sjis", ["\u005c"])

    @foreach_cnx()
    def test_big5(self):
        self._test_charset("big5", ["\u5C62"])


class BugOra17780576(tests.MySQLConnectorTests):
    """BUG#17780576: CHARACTER SET 'UTF8MB4' UNSUPPORTED"""

    def tearDown(self):
        cnx = connection.MySQLConnection(**tests.get_mysql_config())
        cur = cnx.cursor()
        cur.execute("DROP TABLE IF EXISTS utf8mb4test")
        cur.close()
        cnx.close()

    @foreach_cnx()
    def test_utf8mb4(self):
        if tests.MYSQL_VERSION < (5, 5, 0):
            # Test only valid for MySQL 5.5.0 and later.
            return

        config = tests.get_mysql_config()
        tablename = "utf8mb4test"
        self.cnx.set_charset_collation("utf8mb4", "utf8mb4_general_ci")
        cur = self.cnx.cursor()
        cur.execute("DROP TABLE IF EXISTS {0}".format(tablename))

        table = (
            "CREATE TABLE {table} ("
            "id INT AUTO_INCREMENT PRIMARY KEY, "
            "c1 VARCHAR(40) CHARACTER SET 'utf8mb4'"
            ") CHARACTER SET 'utf8mb4'"
        ).format(table=tablename)
        cur.execute(table)

        insert = "INSERT INTO {0} (c1) VALUES (%s)".format(tablename)
        data = [
            "😉😍",
            "😃😊",
            "😄😘😚",
        ]
        for value in data:
            cur.execute(insert, (value,))

        cur.execute("SELECT id, c1 FROM {0} ORDER BY id".format(tablename))
        for row in cur:
            self.assertEqual(data[row[0] - 1], row[1])

        cur.close()
        self.cnx.close()


class BugOra17573172(tests.MySQLConnectorTests):
    """BUG#17573172: MISSING SUPPORT FOR READ-ONLY TRANSACTIONS"""

    def setUp(self):
        config = tests.get_mysql_config()
        self.cnx = connection.MySQLConnection(**config)
        self.cur = self.cnx.cursor()
        self.cur.execute("DROP TABLE IF EXISTS BugOra17573172")
        self.cur.execute("CREATE TABLE BugOra17573172 (c1 INT PRIMARY KEY, c2 INT)")
        self.cur.executemany(
            "INSERT INTO BugOra17573172 VALUES (%s, %s)",
            [(1, 10), (2, 20), (3, 30)],
        )
        self.cnx.commit()

    def test_read_only(self):
        if self.cnx.server_version < (5, 6, 5):
            self.assertRaises(ValueError, self.cnx.start_transaction, readonly=True)
        else:
            self.cnx.start_transaction(readonly=True)
            self.assertTrue(self.cnx.in_transaction)
            self.assertRaises(errors.ProgrammingError, self.cnx.start_transaction)

            query = "INSERT INTO BugOra17573172 VALUES(4, 40)"
            self.assertRaises(errors.ProgrammingError, self.cur.execute, query)
            self.cnx.rollback()

    def tearDown(self):
        self.cur.execute("DROP TABLE IF EXISTS BugOra17573172")
        self.cur.close()


class BugOra17826833(tests.MySQLConnectorTests):
    """BUG#17826833: EXECUTEMANY() FOR INSERTS W/O VALUES"""

    def setUp(self):
        config = tests.get_mysql_config()
        self.cnx = connection.MySQLConnection(**config)
        self.cursor = self.cnx.cursor()

        self.emp_tbl = "Bug17826833_emp"
        self.cursor.execute("DROP TABLE IF EXISTS %s" % (self.emp_tbl))

        self.city_tbl = "Bug17826833_city"
        self.cursor.execute("DROP TABLE IF EXISTS %s" % (self.city_tbl))

        create = (
            "CREATE TABLE %s ( "
            "`id` int(11) NOT NULL, "
            "`name` varchar(20) NOT NULL , "
            "`phone` varchar(20), "
            "PRIMARY KEY (`id`))" % (self.emp_tbl)
        )
        self.cursor.execute(create)

        create = (
            "CREATE TABLE %s ( "
            "`id` int(11) NOT NULL, "
            "`name` varchar(20) NOT NULL, "
            "PRIMARY KEY (`id`))" % (self.city_tbl)
        )
        self.cursor.execute(create)

    def tearDown(self):
        self.cursor.execute("DROP TABLE IF EXISTS {0}".format(self.city_tbl))
        self.cursor.execute("DROP TABLE IF EXISTS {0}".format(self.emp_tbl))

    def test_executemany(self):
        stmt = "INSERT INTO {0} (id,name) VALUES (%s,%s)".format(self.city_tbl)
        self.cursor.executemany(stmt, [(1, "ABC"), (2, "CDE"), (3, "XYZ")])

        query = (
            "INSERT INTO %s (id, name, phone)"
            "SELECT id,name,%%s FROM %s WHERE name=%%s"
        ) % (self.emp_tbl, self.city_tbl)
        try:
            self.cursor.executemany(query, [("4567", "CDE"), ("1234", "XYZ")])
            stmt = "SELECT * FROM {0}".format(self.emp_tbl)
            self.cursor.execute(stmt)
            self.assertEqual(
                [(2, "CDE", "4567"), (3, "XYZ", "1234")],
                self.cursor.fetchall(),
                "INSERT ... SELECT failed",
            )
        except errors.ProgrammingError as err:
            self.fail("Regular expression fails with executemany(): %s" % err)


@unittest.skipIf(
    tests.MYSQL_VERSION <= (5, 7, 2),
    "Pool not supported with with MySQL version 5.6",
)
class BugOra18040042(tests.MySQLConnectorTests):
    """BUG#18040042: Reset session closing pooled Connection"""

    def test_clear_session(self):
        pool_config = tests.get_mysql_config()
        if tests.MYSQL_VERSION < (5, 7):
            pool_config["client_flags"] = [-constants.ClientFlag.CONNECT_ARGS]
        cnxpool = pooling.MySQLConnectionPool(
            pool_name="test", pool_size=1, **pool_config
        )

        pcnx = cnxpool.get_connection()
        exp_session_id = pcnx.connection_id
        pcnx.cmd_query("SET @ham = 2")
        pcnx.close()

        pcnx = cnxpool.get_connection()
        pcnx.cmd_query("SELECT @ham")
        self.assertEqual(exp_session_id, pcnx.connection_id)
        self.assertNotEqual(("2",), pcnx.get_rows()[0][0])

    def test_do_not_clear_session(self):
        cnxpool = pooling.MySQLConnectionPool(
            pool_name="test",
            pool_size=1,
            pool_reset_session=False,
            **tests.get_mysql_config(),
        )

        pcnx = cnxpool.get_connection()
        exp_session_id = pcnx.connection_id
        pcnx.cmd_query("SET @ham = 2")
        pcnx.close()

        pcnx = cnxpool.get_connection()
        pcnx.cmd_query("SELECT @ham")
        self.assertEqual(exp_session_id, pcnx.connection_id)
        self.assertEqual((2,), pcnx.get_rows()[0][0])


class BugOra17965619(tests.MySQLConnectorTests):
    """BUG#17965619: CALLPROC FUNCTION WITH BYTES PARAMETERS"""

    def setUp(self):
        self.cnx = connection.MySQLConnection(**tests.get_mysql_config())
        procedure = "DROP PROCEDURE IF EXISTS `proce_with_binary`"
        self.cnx.cmd_query(procedure)

        procedure = (
            "CREATE PROCEDURE `proce_with_binary` (data VARBINARY(512)) BEGIN END;"
        )
        self.cnx.cmd_query(procedure)

    def tearDown(self):
        procedure = "DROP PROCEDURE IF EXISTS `proce_with_binary`"
        self.cnx.cmd_query(procedure)
        self.cnx.close()

    def test_callproc(self):
        cur = self.cnx.cursor()

        data = b"\xf0\xf1\xf2"
        output = cur.callproc("proce_with_binary", ((data, "BINARY"),))
        self.assertEqual((data,), output)

        cur.close()


@unittest.skipIf(
    tests.MYSQL_EXTERNAL_SERVER,
    "Test not available for external MySQL servers",
)
class BugOra17054848(tests.MySQLConnectorTests):
    """BUG#17054848: USE OF SSL SHOULD NOT REQUIRE SSL_CERT AND SSL_KEY"""

    def setUp(self):
        config = tests.get_mysql_config()
        self.admin_cnx = connection.MySQLConnection(**config)

        if tests.MYSQL_VERSION < (5, 7, 21):
            self.admin_cnx.cmd_query(
                "GRANT ALL ON %s.* TO 'ssluser'@'%s' REQUIRE SSL"
                % (config["database"], config["host"])
            )
        else:
            self.admin_cnx.cmd_query(
                "CREATE USER 'ssluser'@'{host}'".format(
                    db=config["database"],
                    host=tests.get_mysql_config()["host"],
                )
            )

            self.admin_cnx.cmd_query(
                "GRANT ALL ON {db}.* TO 'ssluser'@'{host}'".format(
                    db=config["database"],
                    host=tests.get_mysql_config()["host"],
                )
            )

            self.admin_cnx.cmd_query(
                "ALTER USER 'ssluser'@'{host}' REQUIRE SSL".format(
                    db=config["database"],
                    host=tests.get_mysql_config()["host"],
                )
            )

    def tearDown(self):
        config = tests.get_mysql_config()
        self.admin_cnx.cmd_query("DROP USER 'ssluser'@'%s'" % (config["host"]))

    def test_ssl(self):
        if not tests.SSL_AVAILABLE:
            tests.MESSAGES["WARNINGS"].append(
                "BugOra16217667 test failed. Python lacks SSL support."
            )
            return

        ssl_ca = os.path.abspath(os.path.join(tests.SSL_DIR, "tests_CA_cert.pem"))
        ssl_key = os.path.abspath(os.path.join(tests.SSL_DIR, "tests_client_key.pem"))

        config = tests.get_mysql_config()
        config["user"] = "ssluser"
        config["password"] = ""
        config["unix_socket"] = None
        config["ssl_verify_cert"] = False
        config.update(
            {
                "ssl_ca": ssl_ca,
                "ssl_cipher": "AES256-SHA",
            }
        )

        try:
            cnx = connection.MySQLConnection(**config)
        except errors.ProgrammingError:
            self.fail("Failed authentication with SSL")

        cnx.cmd_query("SHOW STATUS LIKE 'Ssl_cipher'")
        res = cnx.get_rows()[0][0]
        self.assertTrue(res != "")


@unittest.skipIf(
    tests.MYSQL_EXTERNAL_SERVER,
    "Test not available for external MySQL servers",
)
@unittest.skipIf(
    tests.MYSQL_VERSION < (8, 0),
    "BugOra16217765 not tested with MySQL version < 5.6.7. "
    "Not working with cross version MySQL lib< 8.0.",
)
class BugOra16217765(tests.MySQLConnectorTests):
    """BUG#16217765: Fix authentication plugin support"""

    def _create_user(self, cnx, user, password, host, database, plugin):
        self._drop_user(cnx, user, host)
        create_user = "CREATE USER '{user}'@'{host}' IDENTIFIED WITH {plugin}"
        cnx.cmd_query(create_user.format(user=user, host=host, plugin=plugin))

        if tests.MYSQL_VERSION[0:3] < (8, 0, 5):
            if plugin == "sha256_password":
                cnx.cmd_query("SET old_passwords = 2")
            else:
                cnx.cmd_query("SET old_passwords = 0")

        if tests.MYSQL_VERSION < (5, 7, 5):
            passwd = (
                "SET PASSWORD FOR '{user}'@'{host}' = PASSWORD('{password}')"
            ).format(user=user, host=host, password=password)
        else:
            passwd = ("ALTER USER '{user}'@'{host}' IDENTIFIED BY '{password}'").format(
                user=user, host=host, password=password
            )
        cnx.cmd_query(passwd)

        grant = "GRANT ALL ON {database}.* TO '{user}'@'{host}'"
        cnx.cmd_query(grant.format(database=database, user=user, host=host))

    def _drop_user(self, cnx, user, host):
        try:
            self.admin_cnx.cmd_query(
                "DROP USER '{user}'@'{host}'".format(host=host, user=user)
            )
        except errors.DatabaseError:
            # It's OK when drop fails
            pass

    def setUp(self):
        self.users = {
            "sha256user": {
                "username": "sha256user",
                "password": "sha256P@ss",
                "auth_plugin": "sha256_password",
            },
            "sha256user_np": {
                "username": "sha256user_np",
                "password": "",
                "auth_plugin": "sha256_password",
            },
        }

        if NATIVE_PASSWORD_INSTALLED:
            self.users = {
                **self.users,
                **{
                    "nativeuser_np": {
                        "username": "nativeuser_np",
                        "password": "",
                        "auth_plugin": "mysql_native_password",
                    },
                    "nativeuser": {
                        "username": "nativeuser",
                        "password": "nativeP@ss",
                        "auth_plugin": "mysql_native_password",
                    },
                },
            }

        self.errmsg = "AuthPlugin {0} failed: {1}"
        config = tests.get_mysql_config()
        self.host = config["host"]
        self.admin_cnx = connection.MySQLConnection(**config)

        for key, user in self.users.items():
            self._create_user(
                self.admin_cnx,
                user["username"],
                user["password"],
                self.host,
                config["database"],
                plugin=user["auth_plugin"],
            )

    def tearDown(self):
        for key, user in self.users.items():
            self._drop_user(self.admin_cnx, user["username"], self.host)

    @unittest.skipIf(
        tests.MYSQL_EXTERNAL_SERVER,
        "Test not available for external MySQL servers",
    )
    @unittest.skipIf(
        tests.MYSQL_VERSION < (5, 6, 6),
        "MySQL {0} does not support sha256_password auth"
        "".format(tests.MYSQL_VERSION_TXT),
    )
    @unittest.skipUnless(
        tests.SSL_AVAILABLE,
        "BugOra16217765.test_sha256 test skipped: SSL support not available",
    )
    def test_sha256(self):
        config = tests.get_mysql_config()
        config["unix_socket"] = None
        config.update(
            {
                "ssl_ca": tests.SSL_CA,
                "ssl_cert": tests.SSL_CERT,
                "ssl_key": tests.SSL_KEY,
                "ssl_cipher": "AES256-SHA",
            }
        )

        user = self.users["sha256user"]
        config["user"] = user["username"]
        config["password"] = user["password"]
        config["client_flags"] = [
            constants.ClientFlag.PLUGIN_AUTH,
            -constants.ClientFlag.CONNECT_ARGS,
        ]
        config["auth_plugin"] = user["auth_plugin"]

        try:
            cnx = connection.MySQLConnection(**config)
        except Exception as exc:
            import traceback

            traceback.print_exc()
            self.fail(self.errmsg.format(config["auth_plugin"], exc))

        try:
            cnx.cmd_change_user(config["user"], config["password"])
        except:
            self.fail(
                "Changing user using sha256_password auth failed "
                "with pure Python connector. \nflags on cnx: {} \n"
                "".format(config["client_flags"])
            )

        if CMySQLConnection:
            try:
                cnx = CMySQLConnection(**config)
            except Exception as exc:
                import traceback

                traceback.print_exc()
                self.fail(self.errmsg.format(config["auth_plugin"], exc))
            try:
                cnx.cmd_change_user(config["user"], config["password"])
            except:
                self.fail(
                    "Changing user using sha256_password auth failed with CExtension"
                )

    @unittest.skipIf(
        tests.MYSQL_VERSION < (5, 6, 6),
        "MySQL {0} does not support sha256_password auth".format(
            tests.MYSQL_VERSION_TXT
        ),
    )
    def test_sha256_nonssl(self):
        config = tests.get_mysql_config()
        config["unix_socket"] = None
        config["ssl_disabled"] = True
        config["client_flags"] = [constants.ClientFlag.PLUGIN_AUTH]

        user = self.users["sha256user"]
        config["user"] = user["username"]
        config["password"] = user["password"]
        config["auth_plugin"] = user["auth_plugin"]
        self.assertRaises(errors.InterfaceError, connection.MySQLConnection, **config)
        if CMySQLConnection:
            self.assertRaises(errors.InterfaceError, CMySQLConnection, **config)

    @unittest.skipIf(
        tests.MYSQL_VERSION < (5, 5, 7),
        "MySQL {0} does not support authentication plugins".format(
            tests.MYSQL_VERSION_TXT
        ),
    )
    def test_native(self):
        if not NATIVE_PASSWORD_INSTALLED:
            self.skipTest("mysql_native_password isn't loaded")

        config = tests.get_mysql_config()
        config["unix_socket"] = None

        user = self.users["nativeuser"]
        config["user"] = user["username"]
        config["password"] = user["password"]
        config["client_flags"] = [constants.ClientFlag.PLUGIN_AUTH]
        config["auth_plugin"] = user["auth_plugin"]
        try:
            cnx = connection.MySQLConnection(**config)
        except Exception as exc:
            self.fail(self.errmsg.format(config["auth_plugin"], exc))

        if CMySQLConnection:
            try:
                cnx = CMySQLConnection(**config)
            except Exception as exc:
                self.fail(self.errmsg.format(config["auth_plugin"], exc))


class BugOra18144971(tests.MySQLConnectorTests):
    """BUG#18144971 ERROR WHEN USING UNICODE ARGUMENTS IN PREPARED STATEMENT"""

    def setUp(self):
        self.table = "Bug18144971"
        self.table_cp1251 = "Bug18144971_cp1251"

    def _setup(self):
        config = tests.get_mysql_config()
        config["use_unicode"] = True
        cnx = connection.MySQLConnection(**config)
        cur = cnx.cursor()

        cur.execute("DROP TABLE IF EXISTS {0}".format(self.table))

        create = (
            "CREATE TABLE {0} ( "
            "`id` int(11) NOT NULL, "
            "`name` varchar(40) NOT NULL , "
            "`phone` varchar(40), "
            "PRIMARY KEY (`id`))"
            " CHARACTER SET 'utf8'".format(self.table)
        )

        cur.execute(create)

        cur.execute("DROP TABLE IF EXISTS {0}".format(self.table_cp1251))

        create = (
            "CREATE TABLE {0} ( "
            "`id` int(11) NOT NULL, "
            "`name` varchar(40) NOT NULL , "
            "`phone` varchar(40), "
            "PRIMARY KEY (`id`))"
            " CHARACTER SET 'cp1251'".format(self.table_cp1251)
        )
        cur.execute(create)
        cnx.close()

    def tearDown(self):
        config = tests.get_mysql_config()
        config["use_unicode"] = True
        cnx = connection.MySQLConnection(**config)
        cur = cnx.cursor()

        cur.execute("DROP TABLE IF EXISTS {0}".format(self.table))
        cur.execute("DROP TABLE IF EXISTS {0}".format(self.table_cp1251))

    @cnx_config(use_unicode=True)
    @foreach_cnx()
    def test_prepared_statement(self):
        self._setup()
        cur = self.cnx.cursor(prepared=True)
        stmt = "INSERT INTO {0} VALUES (?,?,?)".format(self.table)
        data = [(1, b"bytes", "1234"), (2, "aaaаффф", "1111")]
        exp = [(1, "bytes", "1234"), (2, "aaaаффф", "1111")]
        cur.execute(stmt, data[0])
        self.cnx.commit()
        cur.execute("SELECT * FROM {0}".format(self.table))
        self.assertEqual(cur.fetchall(), [exp[0]])

        config = tests.get_mysql_config()
        config["charset"] = "cp1251"
        self.cnx = self.cnx.__class__(**config)
        cur = self.cnx.cursor(prepared=True)
        stmt = "INSERT INTO {0} VALUES (?,?,?)".format(self.table_cp1251)
        cur.execute(stmt, data[1])
        self.cnx.commit()
        cur.execute("SELECT * FROM {0}".format(self.table_cp1251))
        self.assertEqual(cur.fetchall(), [exp[1]])


class BugOra18389196(tests.MySQLConnectorTests):
    """BUG#18389196:  INSERTING PARAMETER MULTIPLE TIMES IN STATEMENT"""

    def setUp(self):
        self.tbl = "Bug18389196"

        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        cur = cnx.cursor()

        cur.execute("DROP TABLE IF EXISTS %s" % self.tbl)

        create = (
            "CREATE TABLE %s ( "
            "`id` int(11) NOT NULL, "
            "`col1` varchar(20) NOT NULL, "
            "`col2` varchar(20) NOT NULL, "
            "PRIMARY KEY (`id`))" % self.tbl
        )
        cur.execute(create)
        cnx.close()

    def tearDown(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        cnx.cmd_query("DROP TABLE IF EXISTS %s" % self.tbl)
        cnx.close()

    @foreach_cnx()
    def test_parameters(self):
        self.cnx.cmd_query("TRUNCATE {0}".format(self.tbl))
        cur = self.cnx.cursor()
        stmt = (
            "INSERT INTO {0} (id,col1,col2) VALUES "
            "(%(id)s,%(name)s,%(name)s)".format(self.tbl)
        )
        try:
            cur.execute(stmt, {"id": 1, "name": "ABC"})
        except errors.ProgrammingError as err:
            self.fail(
                "Inserting parameter multiple times in a statement failed: %s" % err
            )

        cur.close()


@unittest.skipIf(
    tests.MYSQL_VERSION >= (5, 7, 5),
    "MySQL {0} does not support old password auth".format(tests.MYSQL_VERSION_TXT),
)
class BugOra18415927(tests.MySQLConnectorTests):
    """BUG#18415927: AUTH_RESPONSE VARIABLE INCREMENTED WITHOUT BEING DEFINED"""

    user = {
        "username": "nativeuser",
        "password": "nativeP@ss",
    }

    def setUp(self):
        config = tests.get_mysql_config()
        host = config["host"]
        database = config["database"]
        cnx = connection.MySQLConnection(**config)
        try:
            cnx.cmd_query(
                "DROP USER '{user}'@'{host}'".format(
                    host=host, user=self.user["username"]
                )
            )
        except:
            pass

        create_user = "CREATE USER '{user}'@'{host}' "
        cnx.cmd_query(create_user.format(user=self.user["username"], host=host))

        passwd = ("SET PASSWORD FOR '{user}'@'{host}' = PASSWORD('{password}')").format(
            user=self.user["username"],
            host=host,
            password=self.user["password"],
        )

        cnx.cmd_query(passwd)

        grant = "GRANT ALL ON {database}.* TO '{user}'@'{host}'"
        cnx.cmd_query(
            grant.format(database=database, user=self.user["username"], host=host)
        )

    def tearDown(self):
        config = tests.get_mysql_config()
        host = config["host"]
        cnx = connection.MySQLConnection(**config)
        cnx.cmd_query(
            "DROP USER '{user}'@'{host}'".format(host=host, user=self.user["username"])
        )

    def test_auth_response(self):
        config = tests.get_mysql_config()
        config["unix_socket"] = None
        config["user"] = self.user["username"]
        config["password"] = self.user["password"]
        config["client_flags"] = [
            -constants.ClientFlag.SECURE_CONNECTION,
            -constants.ClientFlag.CONNECT_WITH_DB,
        ]
        try:
            cnx = connection.MySQLConnection(**config)
        except Exception as exc:
            self.fail("Connection failed: {0}".format(exc))


class BugOra18527437(tests.MySQLConnectorTests):
    """BUG#18527437: UNITTESTS FAILING WHEN --host=::1 IS PASSED AS ARGUMENT"""

    def test_poolname(self):
        config = tests.get_mysql_config()
        config["host"] = "::1"
        config["pool_size"] = 3

        exp = "{0}_{1}_{2}_{3}".format(
            config["host"], config["port"], config["user"], config["database"]
        )
        self.assertEqual(exp, pooling.generate_pool_name(**config))

    def test_custom_poolname(self):
        cnxpool = pooling.MySQLConnectionPool(
            pool_name="ham:spam", **tests.get_mysql_config()
        )
        self.assertEqual("ham:spam", cnxpool._pool_name)
        cnxpool._remove_connections()


class BugOra18694096(tests.MySQLConnectorTests):
    """BUG#18694096: INCORRECT CONVERSION OF NEGATIVE TIMEDELTA"""

    cases = [
        (
            timedelta(hours=0, minutes=0, seconds=1, microseconds=0),
            "00:00:01",
        ),
        (
            timedelta(hours=0, minutes=0, seconds=-1, microseconds=0),
            "-00:00:01",
        ),
        (timedelta(hours=0, minutes=1, seconds=1, microseconds=0), "00:01:01"),
        (
            timedelta(hours=0, minutes=-1, seconds=-1, microseconds=0),
            "-00:01:01",
        ),
        (timedelta(hours=1, minutes=1, seconds=1, microseconds=0), "01:01:01"),
        (
            timedelta(hours=-1, minutes=-1, seconds=-1, microseconds=0),
            "-01:01:01",
        ),
        (timedelta(days=3, seconds=86401), "96:00:01"),
        (timedelta(days=-3, seconds=86401), "-47:59:59"),
    ]

    # Cases for MySQL 5.6.4 and higher
    cases_564 = [
        (
            timedelta(hours=0, minutes=0, seconds=0, microseconds=1),
            "00:00:00.000001",
        ),
        (
            timedelta(hours=0, minutes=0, seconds=0, microseconds=-1),
            "-00:00:00.000001",
        ),
        (timedelta(days=2, hours=0, microseconds=1), "48:00:00.000001"),
        (
            timedelta(days=-3, seconds=86399, microseconds=999999),
            "-48:00:00.000001",
        ),
    ]

    def setUp(self):
        config = tests.get_mysql_config()
        self.cnx = mysql.connector.connect(**config)

        self.tbl = "times"
        self.cnx.cmd_query("DROP TABLE IF EXISTS {0}".format(self.tbl))
        if tests.MYSQL_VERSION >= (5, 6, 4):
            create = f"""
                CREATE TABLE {self.tbl}
                (id INT AUTO_INCREMENT PRIMARY KEY, c1 TIME(6))
                """
            self.cases += self.cases_564
        else:
            create = f"""
                CREATE TABLE {self.tbl}
                (id INT AUTO_INCREMENT PRIMARY KEY, c1 TIME)"
                """
        self.cnx.cmd_query(create)

    def tearDown(self):
        if self.cnx:
            self.cnx.cmd_query(f"DROP TABLE IF EXISTS {self.tbl}")

    def test_timedelta(self):
        # Note that both _timedelta_to_mysql and _TIME_to_python are
        # tested
        cur = self.cnx.cursor()

        # Following uses _timedelta_to_mysql to insert data
        data = [(case[0],) for case in self.cases]
        cur.executemany("INSERT INTO {0} (c1) VALUES (%s)".format(self.tbl), data)
        self.cnx.commit()

        # We use _TIME_to_python to convert back to Python
        cur.execute("SELECT c1 FROM {0}".format(self.tbl))
        for i, row in enumerate(cur.fetchall()):
            self.assertEqual(
                self.cases[i][0],
                row[0],
                "Incorrect timedelta for {0}, was {1!r}".format(
                    self.cases[i][1], row[0]
                ),
            )


class BugOra18220593(tests.MySQLConnectorTests):
    """BUG#18220593 MYSQLCURSOR.EXECUTEMANY() DOESN'T LIKE UNICODE OPERATIONS"""

    def setUp(self):
        config = tests.get_mysql_config()
        self.cnx = connection.MySQLConnection(**config)
        self.cur = self.cnx.cursor()
        self.table = "⽃⽄⽅⽆⽇⽈⽉⽊"
        self.cur.execute(f"DROP TABLE IF EXISTS {self.table}")
        self.cur.execute(
            f"""
            CREATE TABLE {self.table} (id INT AUTO_INCREMENT PRIMARY KEY, c1 VARCHAR(100))
            CHARACTER SET 'utf8'
            """
        )

    def test_unicode_operation(self):
        data = [
            ("database",),
            ("データベース",),
            ("데이터베이스",),
        ]
        self.cur.executemany(f"INSERT INTO {self.table} (c1) VALUES (%s)", data)
        self.cnx.commit()
        self.cur.execute(f"SELECT c1 FROM {self.table}")

        self.assertEqual(self.cur.fetchall(), data)

    def tearDown(self):
        self.cur.execute(f"DROP TABLE IF EXISTS {self.table}")
        self.cur.close()
        self.cnx.close()


@unittest.skipIf(
    tests.MYSQL_EXTERNAL_SERVER,
    "Test not available for external MySQL servers",
)
class BugOra14843456(tests.MySQLConnectorTests):
    """BUG#14843456: UNICODE USERNAME AND/OR PASSWORD FAILS"""

    def setUp(self):
        config = tests.get_mysql_config()
        self.cnx = connection.MySQLConnection(**config)
        self.cursor = self.cnx.cursor()

        if config["unix_socket"] and os.name != "nt":
            self.host = "localhost"
        else:
            self.host = config["host"]

        grant = "CREATE USER '{user}'@'{host}' IDENTIFIED BY '{password}'"

        self._credentials = [
            ("Herne", "Herne"),
            ("\u0141owicz", "\u0141owicz"),
        ]
        for user, password in self._credentials:
            try:
                self.cursor.execute(
                    "DROP USER '{user}'@'{host}'".format(user=user, host=self.host)
                )
            except errors.DatabaseError:
                pass
            self.cursor.execute(
                grant.format(user=user, host=self.host, password=password)
            )

    def tearDown(self):
        for user, password in self._credentials:
            self.cursor.execute(
                "DROP USER '{user}'@'{host}'".format(user=user, host=self.host)
            )

    def test_unicode_credentials(self):
        config = tests.get_mysql_config()
        for user, password in self._credentials:
            config["user"] = user
            config["password"] = password
            config["database"] = None
            try:
                cnx = connection.MySQLConnection(**config)
            except (UnicodeDecodeError, errors.InterfaceError):
                self.fail("Failed using unicode username or password")
            else:
                cnx.close()


class Bug499410(tests.MySQLConnectorTests):
    """lp:499410 Disabling unicode does not work"""

    def test_use_unicode(self):
        config = tests.get_mysql_config()
        config["use_unicode"] = False
        cnx = connection.MySQLConnection(**config)

        self.assertEqual(False, cnx.use_unicode)
        cnx.close()

    @cnx_config(use_unicode=False, charset="greek")
    @foreach_cnx()
    def test_charset(self):
        charset = "greek"
        cur = self.cnx.cursor()

        data = [b"\xe1\xed\xf4\xdf\xef"]  # Bye in Greek
        exp_unicode = [
            ("\u03b1\u03bd\u03c4\u03af\u03bf",),
        ]
        exp_nonunicode = [(data[0],)]

        tbl = f"{charset}test"
        try:
            cur.execute("DROP TABLE IF EXISTS {0}".format(tbl))
            cur.execute(
                f"CREATE TABLE {tbl} "
                f"(id INT AUTO_INCREMENT PRIMARY KEY, c1 VARCHAR(60)) charset={charset}"
            )
        except:
            self.fail("Failed creating test table.")

        stmt = f"INSERT INTO {tbl} (c1) VALUES (%s)"
        try:
            for line in data:
                cur.execute(stmt, (line,))
        except Exception as err:
            self.fail(f"Failed populating test table: {err}")

        cur.execute(f"SELECT c1 FROM {tbl}")
        res_nonunicode = cur.fetchall()
        self.cnx.use_unicode = True
        cur.execute(f"SELECT c1 FROM {tbl}")
        res_unicode = cur.fetchall()

        try:
            cur.execute(f"DROP TABLE IF EXISTS {tbl}")
        except:
            self.fail("Failed cleaning up test table.")

        self.assertEqual(exp_nonunicode, res_nonunicode)
        self.assertEqual(exp_unicode, res_unicode)


class BugOra18742429(tests.MySQLConnectorTests):
    """BUG#18742429:  CPY FAILS WHEN QUERYING LARGE NUMBER OF COLUMNS"""

    def setUp(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)

        self.tbl = "Bug18742429"
        cnx.cmd_query(f"DROP TABLE IF EXISTS {self.tbl}")

        create = "CREATE TABLE {0}(id INT PRIMARY KEY, {1})".format(
            self.tbl,
            ",".join(["col" + str(i) + " INT(10)" for i in range(1000)]),
        )

        cnx.cmd_query(create)
        cnx.close()

    def tearDown(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        cnx.cmd_query(f"DROP TABLE IF EXISTS {self.tbl}")
        cnx.close()

    @foreach_cnx(connection.MySQLConnection)
    def test_columns(self):
        cur = self.cnx.cursor()

        cur.execute(f"TRUNCATE TABLE {self.tbl}")

        stmt = "INSERT INTO {0} VALUES(1, {1})".format(
            self.tbl,
            ",".join([str(i) if i % 2 == 0 else "NULL" for i in range(1000)]),
        )
        exp = tuple(i if i % 2 == 0 else None for i in range(1000))
        cur.execute(stmt)

        cur = self.cnx.cursor(prepared=True)
        stmt = f"SELECT * FROM {self.tbl} WHERE col0=?"
        cur.execute(stmt, (0,))
        self.assertEqual((1,) + exp, cur.fetchone())


class BugOra19164627(tests.MySQLConnectorTests):
    """BUG#19164627: Cursor tries to decode LINESTRING data as utf-8"""

    def setUp(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)

        self.tbl = "BugOra19164627"
        cnx.cmd_query("DROP TABLE IF EXISTS %s" % self.tbl)

        cnx.cmd_query(
            "CREATE TABLE {0} ( "
            "id SERIAL PRIMARY KEY AUTO_INCREMENT NOT NULL, "
            "line LINESTRING NOT NULL "
            ") DEFAULT CHARSET=ascii".format(self.tbl)
        )
        cnx.close()

    def tearDown(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        cnx.cmd_query("DROP TABLE IF EXISTS {0}".format(self.tbl))
        cnx.close()

    @foreach_cnx()
    def test_linestring(self):
        cur = self.cnx.cursor()

        cur.execute("TRUNCATE TABLE {0}".format(self.tbl))

        cur.execute(
            "INSERT IGNORE INTO {0} (id, line) "
            "VALUES (0,LINESTRING(POINT(0, 0), POINT(0, 1)))".format(self.tbl)
        )

        cur.execute("SELECT * FROM {0} LIMIT 1".format(self.tbl))
        self.assertEqual(
            cur.fetchone(),
            (
                1,
                b"\x00\x00\x00\x00\x01\x02\x00\x00"
                b"\x00\x02\x00\x00\x00\x00\x00\x00"
                b"\x00\x00\x00\x00\x00\x00\x00\x00"
                b"\x00\x00\x00\x00\x00\x00\x00\x00"
                b"\x00\x00\x00\x00\x00\x00\x00\x00"
                b"\x00\x00\x00\xf0?",
            ),
        )
        cur.close()


class BugOra19225481(tests.MySQLConnectorTests):
    """BUG#19225481: FLOATING POINT INACCURACY WITH PYTHON v2"""

    def setUp(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)

        self.tbl = "Bug19225481"
        cnx.cmd_query(f"DROP TABLE IF EXISTS {self.tbl}")

        create = f"""
            CREATE TABLE {self.tbl}
            (id INT AUTO_INCREMENT PRIMARY KEY, col1 DOUBLE)
        """
        cnx.cmd_query(create)
        cnx.close()

    def tearDown(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        cnx.cmd_query(f"DROP TABLE IF EXISTS {self.tbl}")
        cnx.close()

    @foreach_cnx()
    def test_columns(self):
        self.cnx.cmd_query(f"TRUNCATE {self.tbl}")
        cur = self.cnx.cursor()
        values = [
            (123.123456789987,),
            (234.234,),
            (12.12,),
            (111.331,),
            (0.0,),
            (-99.99999900099,),
        ]
        stmt = f"INSERT INTO {self.tbl} (col1) VALUES(%s)"
        cur.executemany(stmt, values)

        stmt = f"SELECT col1 FROM {self.tbl}"
        cur.execute(stmt)
        self.assertEqual(values, cur.fetchall())


class BugOra19169990(tests.MySQLConnectorTests):
    """BUG#19169990: Issue with compressed cnx using Python 2"""

    @cnx_config(compress=True)
    @foreach_cnx()
    def test_compress(self):
        for charset in ("utf8", "latin1", "latin7"):
            self.config["charset"] = charset
            try:
                self.cnx = self.cnx.__class__(**self.config)
                cur = self.cnx.cursor()
                cur.execute("SELECT %s", ("mysql" * 10000,))
            except TypeError:
                traceback.print_exc()
                self.fail("Failed setting up compressed cnx using {0}".format(charset))
            except errors.Error:
                self.fail("Failed sending/retrieving compressed data")

            self.cnx.close()


class BugOra19184025(tests.MySQLConnectorTests):
    """BUG#19184025: FIRST NULL IN ROW RETURNS REST OF ROW AS NONE"""

    def setUp(self):
        self.tbl = "Bug19184025"
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)

        cnx.cmd_query(f"DROP TABLE IF EXISTS {self.tbl}")
        create = f"""
            CREATE TABLE {self.tbl}
            (c1 INT, c2 INT NOT NULL DEFAULT 2, PRIMARY KEY(c2))
        """
        cnx.cmd_query(create)

    def tearDown(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        cnx.cmd_query(f"DROP TABLE IF EXISTS {self.tbl}")
        cnx.close()

    @foreach_cnx()
    def test_row_to_python(self):
        self.cnx.cmd_query(f"TRUNCATE {self.tbl}")
        cur = self.cnx.cursor()
        cur.execute(f"INSERT INTO {self.tbl} (c1) VALUES (NULL)")
        cur.execute(f"SELECT * FROM {self.tbl}")
        self.assertEqual((None, 2), cur.fetchone())
        cur.close()


class BugOra19170287(tests.MySQLConnectorTests):
    """BUG#19170287: DUPLICATE OPTION_GROUPS RAISING ERROR WITH PYTHON 3"""

    def test_duplicate_groups(self):
        option_file_dir = os.path.join("tests", "data", "option_files")
        opt_file = os.path.join(option_file_dir, "dup_groups.cnf")

        exp = {
            "password": "mypass",
            "user": "mysql",
            "database": "duplicate_data",
            "port": 10000,
        }
        self.assertEqual(exp, read_option_files(option_files=opt_file))


class BugOra19169143(tests.MySQLConnectorTests):
    """BUG#19169143: FAILURE IN RAISING ERROR WITH DUPLICATE OPTION_FILES"""

    def test_duplicate_optionfiles(self):
        option_file_dir = os.path.join("tests", "data", "option_files")
        files = [
            os.path.join(option_file_dir, "include_files", "1.cnf"),
            os.path.join(option_file_dir, "include_files", "2.cnf"),
            os.path.join(option_file_dir, "include_files", "1.cnf"),
        ]
        self.assertRaises(ValueError, mysql.connector.connect, option_files=files)


class BugOra19282158(tests.MySQLConnectorTests):
    """BUG#19282158: NULL values with prepared statements"""

    def setUp(self):
        config = tests.get_mysql_config()
        self.cnx = connection.MySQLConnection(**config)
        self.cursor = self.cnx.cursor()

        self.tbl = "Bug19282158"
        self.cursor.execute("DROP TABLE IF EXISTS %s" % self.tbl)

        create = (
            "CREATE TABLE {0}(col1 INT NOT NULL, col2 INT NULL, "
            "col3 VARCHAR(10), col4 DECIMAL(4,2) NULL, "
            "col5 DATETIME NULL, col6 INT NOT NULL, col7 VARCHAR(10), "
            "PRIMARY KEY(col1))".format(self.tbl)
        )

        self.cursor.execute(create)

    def tearDown(self):
        self.cursor.execute("DROP TABLE IF EXISTS %s" % self.tbl)
        self.cursor.close()
        self.cnx.close()

    def test_null(self):
        cur = self.cnx.cursor(prepared=True)
        sql = (
            "INSERT INTO {0}(col1, col2, col3, col4, col5, col6, col7) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)".format(self.tbl)
        )
        params = (
            100,
            None,
            "foo",
            None,
            datetime(2014, 8, 4, 9, 11, 14),
            10,
            "bar",
        )
        exp = (
            100,
            None,
            "foo",
            None,
            datetime(2014, 8, 4, 9, 11, 14),
            10,
            "bar",
        )
        cur.execute(sql, params)

        sql = "SELECT * FROM {0}".format(self.tbl)
        cur.execute(sql)
        self.assertEqual(exp, cur.fetchone())
        cur.close()


@unittest.skipIf(
    tests.MYSQL_VERSION <= (5, 7, 2),
    "Pool not supported with with MySQL version 5.6",
)
class BugOra19168737(tests.MySQLConnectorTests):
    """BUG#19168737: UNSUPPORTED CONNECTION ARGUMENTS WHILE USING OPTION_FILES"""

    def test_unsupported_arguments(self):
        option_file_dir = os.path.join("tests", "data", "option_files")
        opt_file = os.path.join(option_file_dir, "pool.cnf")
        config = tests.get_mysql_config()
        if tests.MYSQL_VERSION < (5, 7):
            config["client_flags"] = [-constants.ClientFlag.CONNECT_ARGS]

        conn = mysql.connector.connect(
            option_files=opt_file, option_groups=["pooling"], **config
        )
        self.assertEqual("my_pool", conn.pool_name)
        mysql.connector.pooling._CONNECTION_POOLS = {}
        conn.close()

        new_config = read_option_files(
            option_files=opt_file, option_groups=["failover"], **config
        )

        exp = {
            "failover": (
                {"pool_name": "failA", "port": 3306},
                {"pool_name": "failB", "port": 3307},
            )
        }
        exp.update(config)
        self.assertEqual(exp, new_config)


class BugOra21530100(tests.MySQLConnectorTests):
    """BUG#21530100: CONNECT FAILS WHEN USING MULTIPLE OPTION_GROUPS WITH
    PYTHON 3.3
    """

    def test_option_files_with_option_groups(self):
        temp_cnf_file = os.path.join(os.getcwd(), "temp.cnf")
        temp_include_file = os.path.join(os.getcwd(), "include.cnf")

        try:
            cnf_file = open(temp_cnf_file, "w+")
            include_file = open(temp_include_file, "w+")

            config = tests.get_mysql_config()

            cnf = "[group32]\n"
            cnf += "\n".join(
                ["{0} = {1}".format(key, value) for key, value in config.items()]
            )

            cnf += "\n[group31]\n"
            cnf += "!include {0}\n".format(temp_include_file)

            include_cnf = "[group41]\n"
            include_cnf += "charset=utf8\n"

            cnf_file.write(cnf)
            include_file.write(include_cnf)

            cnf_file.close()
            include_file.close()

            conn = mysql.connector.connect(
                option_files=temp_cnf_file,
                option_groups=["group31", "group32", "group41"],
            )
        except Exception as exc:
            self.fail("Connection failed with option_files argument: {0}".format(exc))
        finally:
            os.remove(temp_cnf_file)
            os.remove(temp_include_file)


class BugOra19481761(tests.MySQLConnectorTests):
    """BUG#19481761: OPTION_FILES + !INCLUDE FAILS WITH TRAILING NEWLINE"""

    def test_option_files_with_include(self):
        temp_cnf_file = os.path.join(os.getcwd(), "temp.cnf")
        temp_include_file = os.path.join(os.getcwd(), "include.cnf")

        cnf_file = open(temp_cnf_file, "w+")
        include_file = open(temp_include_file, "w+")

        config = tests.get_mysql_config()

        cnf = "[connector_python]\n"
        cnf += "\n".join(
            ["{0} = {1}".format(key, value) for key, value in config.items()]
        )

        include_file.write(cnf)
        cnf_file.write("!include {0}\n".format(temp_include_file))

        cnf_file.close()
        include_file.close()

        try:
            conn = mysql.connector.connect(option_files=temp_cnf_file)
        except:
            self.fail("Connection failed with option_files argument.")

        self.assertEqual(config, read_option_files(option_files=temp_cnf_file))

        os.remove(temp_cnf_file)
        os.remove(temp_include_file)


class BugOra19584051(tests.MySQLConnectorTests):
    """BUG#19584051: TYPE_CODE DOES NOT COMPARE EQUAL"""

    def setUp(self):
        config = tests.get_mysql_config()
        self.cnx = connection.MySQLConnection(**config)
        self.cursor = self.cnx.cursor()

        self.tbl = "Bug19584051"
        self.cursor.execute("DROP TABLE IF EXISTS %s" % self.tbl)

        create = (
            "CREATE TABLE {0}(col1 INT NOT NULL, col2 BLOB, "
            "col3 VARCHAR(10), col4 DECIMAL(4,2), "
            "col5 DATETIME , col6 YEAR, "
            "PRIMARY KEY(col1))".format(self.tbl)
        )

        self.cursor.execute(create)

    def tearDown(self):
        self.cursor.execute("DROP TABLE IF EXISTS %s" % self.tbl)
        self.cursor.close()
        self.cnx.close()

    def test_dbapi(self):
        cur = self.cnx.cursor()
        sql = (
            "INSERT INTO {0}(col1, col2, col3, col4, col5, col6) "
            "VALUES (%s, %s, %s, %s, %s, %s)".format(self.tbl)
        )
        params = (
            100,
            "blob-data",
            "foo",
            1.2,
            datetime(2014, 8, 4, 9, 11, 14),
            2014,
        )

        exp = [
            mysql.connector.NUMBER,
            mysql.connector.BINARY,
            mysql.connector.STRING,
            mysql.connector.NUMBER,
            mysql.connector.DATETIME,
            mysql.connector.NUMBER,
        ]
        cur.execute(sql, params)

        sql = "SELECT * FROM {0}".format(self.tbl)
        cur.execute(sql)
        temp = cur.fetchone()
        type_codes = [row[1] for row in cur.description]
        self.assertEqual(exp, type_codes)
        cur.close()


class BugOra19522948(tests.MySQLConnectorTests):
    """BUG#19522948: DATA CORRUPTION WITH TEXT FIELDS"""

    def setUp(self):
        config = tests.get_mysql_config()
        self.cnx = connection.MySQLConnection(**config)
        self.cur = self.cnx.cursor()

        self.tbl = "Bug19522948"
        self.cur.execute(f"DROP TABLE IF EXISTS {self.tbl}")

        create = f"""
            CREATE TABLE {self.tbl}
            (id INT AUTO_INCREMENT PRIMARY KEY, c1 LONGTEXT NOT NULL)
            """
        self.cur.execute(create)

    def tearDown(self):
        self.cur.execute(f"DROP TABLE IF EXISTS {self.tbl}")
        self.cur.close()
        self.cnx.close()

    def test_row_to_python(self):
        cur = self.cnx.cursor(prepared=True)

        data = "test_data" * 10
        cur.execute(f"INSERT INTO {self.tbl} (c1) VALUES (?)", (data,))
        self.cur.execute(f"SELECT c1 FROM {self.tbl}")
        self.assertEqual((data,), self.cur.fetchone())
        self.cur.execute(f"TRUNCATE TABLE {self.tbl}")

        data = "test_data" * 1000
        cur.execute(f"INSERT INTO {self.tbl} (c1) VALUES (?)", (data,))
        self.cur.execute(f"SELECT c1 FROM {self.tbl}")
        self.assertEqual((data,), self.cur.fetchone())
        self.cur.execute(f"TRUNCATE TABLE {self.tbl}")

        data = "test_data" * 10000
        cur.execute(f"INSERT INTO {self.tbl} (c1) VALUES (?)", (data,))
        self.cur.execute(f"SELECT c1 FROM {self.tbl}")
        self.assertEqual((data,), self.cur.fetchone())


class BugOra19500097(tests.MySQLConnectorTests):
    """BUG#19500097: BETTER SUPPORT FOR RAW/BINARY DATA"""

    def setUp(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        cur = cnx.cursor()

        self.tbl = "Bug19500097"
        cur.execute(f"DROP TABLE IF EXISTS {self.tbl}")

        create = f"""
            CREATE TABLE {self.tbl}
            (id INT AUTO_INCREMENT PRIMARY KEY, col1 VARCHAR(10), col2 INT)
            DEFAULT CHARSET latin1
            """
        cur.execute(create)
        cur.close()
        cnx.close()

    def tearDown(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        cur = cnx.cursor()
        cur.execute(f"DROP TABLE IF EXISTS {self.tbl}")
        cur.close()
        cnx.close()

    @foreach_cnx()
    def test_binary_charset(self):
        sql = f"INSERT INTO {self.tbl} (col1, col2) VALUES(%s, %s)"
        cur = self.cnx.cursor()
        cur.execute(sql, ("foo", 1))
        cur.execute(sql, ("ëëë", 2))
        cur.execute(sql, ("ááá", 5))

        self.cnx.set_charset_collation("binary")
        cur.execute(sql, ("bar", 3))
        cur.execute(sql, ("ëëë", 4))
        cur.execute(sql, ("ááá", 6))

        exp = [
            (bytearray(b"foo"), 1),
            (bytearray(b"\xeb\xeb\xeb"), 2),
            (bytearray(b"\xe1\xe1\xe1"), 5),
            (bytearray(b"bar"), 3),
            (bytearray(b"\xc3\xab\xc3\xab\xc3\xab"), 4),
            (bytearray(b"\xc3\xa1\xc3\xa1\xc3\xa1"), 6),
        ]
        cur.execute(f"SELECT col1, col2 FROM {self.tbl}")
        self.assertEqual(exp, cur.fetchall())


@unittest.skipIf(
    tests.MYSQL_VERSION < (5, 7, 3),
    "MySQL {0} does not support COM_RESET_CONNECTION".format(tests.MYSQL_VERSION_TXT),
)
class BugOra19549363(tests.MySQLConnectorTests):
    """BUG#19549363: Compression does not work with Change User"""

    def setUp(self):
        self.config = tests.get_mysql_config()
        self.config["compress"] = True

        mysql.connector.pooling._CONNECTION_POOLS = {}
        self.config["pool_name"] = "mypool"
        self.config["pool_size"] = 3
        self.config["pool_reset_session"] = True

    def tearDown(self):
        # Remove pools created by test
        mysql.connector.pooling._CONNECTION_POOLS = {}

    def test_compress_reset_connection(self):
        self.config["use_pure"] = True
        cnx1 = mysql.connector.connect(**self.config)

        try:
            cnx1.close()
        except:
            self.fail("Reset session with compression test failed.")
        finally:
            mysql.connector.pooling._CONNECTION_POOLS = {}

    @unittest.skipIf(CMySQLConnection is None, ERR_NO_CEXT)
    def test_compress_reset_connection_cext(self):
        self.config["use_pure"] = False
        cnx1 = mysql.connector.connect(**self.config)

        try:
            cnx1.close()
        except:
            self.fail("Reset session with compression test failed.")
        finally:
            mysql.connector.pooling._CONNECTION_POOLS = {}


class BugOra19803702(tests.MySQLConnectorTests):
    """BUG#19803702: CAN'T REPORT ERRORS THAT HAVE NON-ASCII CHARACTERS"""

    def test_errors(self):
        config = tests.get_mysql_config()
        self.cnx = connection.MySQLConnection(**config)
        self.cur = self.cnx.cursor()

        self.tbl = "áááëëëááá"
        self.cur.execute("DROP TABLE IF EXISTS {0}".format(self.tbl))

        create = (
            "CREATE TABLE {0} (col1 VARCHAR(10), col2 INT) "
            "DEFAULT CHARSET latin1".format(self.tbl)
        )

        self.cur.execute(create)
        self.assertRaises(errors.DatabaseError, self.cur.execute, create)

    def tearDown(self):
        self.cur.execute("DROP TABLE IF EXISTS {0}".format(self.tbl))
        self.cur.close()
        self.cnx.close()


class BugOra19777815(tests.MySQLConnectorTests):
    """BUG#19777815:  CALLPROC() DOES NOT SUPPORT WARNINGS"""

    def setUp(self):
        config = tests.get_mysql_config()
        config["get_warnings"] = True
        cnx = connection.MySQLConnection(**config)
        cur = cnx.cursor()
        self.sp1 = "BUG19777815"
        self.sp2 = "BUG19777815_with_result"
        create1 = (
            "CREATE PROCEDURE {0}() BEGIN SIGNAL SQLSTATE '01000' "
            "SET MESSAGE_TEXT = 'TEST WARNING'; END;".format(self.sp1)
        )
        create2 = (
            "CREATE PROCEDURE {0}() BEGIN SELECT 1; SIGNAL SQLSTATE '01000' "
            "SET MESSAGE_TEXT = 'TEST WARNING'; END;".format(self.sp2)
        )

        cur.execute("DROP PROCEDURE IF EXISTS {0}".format(self.sp1))
        cur.execute("DROP PROCEDURE IF EXISTS {0}".format(self.sp2))
        cur.execute(create1)
        cur.execute(create2)
        cur.close()
        cnx.close()

    def tearDown(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        cur = cnx.cursor()
        cur.execute("DROP PROCEDURE IF EXISTS {0}".format(self.sp1))
        cur.execute("DROP PROCEDURE IF EXISTS {0}".format(self.sp2))
        cur.close()
        cnx.close()

    @foreach_cnx(get_warnings=True)
    def test_warning(self):
        cur = self.cnx.cursor()
        cur.callproc(self.sp1)
        exp = [("Warning", 1642, "TEST WARNING")]
        self.assertEqual(exp, cur.warnings)

    @foreach_cnx(get_warnings=True)
    def test_warning_with_rows(self):
        cur = self.cnx.cursor()
        cur.callproc(self.sp2)

        exp = [(1,)]
        self.assertEqual(exp, next(cur.stored_results()).fetchall())

        exp = [("Warning", 1642, "TEST WARNING")]
        self.assertEqual(exp, cur.warnings)


class BugOra20407036(tests.MySQLConnectorTests):
    """BUG#20407036:  INCORRECT ARGUMENTS TO MYSQLD_STMT_EXECUTE ERROR"""

    def setUp(self):
        config = tests.get_mysql_config()
        self.cnx = connection.MySQLConnection(**config)
        self.cur = self.cnx.cursor()

        self.tbl = "Bug20407036"
        self.cur.execute("DROP TABLE IF EXISTS {0}".format(self.tbl))

        create = (
            "CREATE TABLE {0} ( "
            "id int(10) unsigned NOT NULL AUTO_INCREMENT, "
            "text TEXT CHARACTER SET utf8 NOT NULL, "
            "rooms tinyint(3) unsigned NOT NULL, "
            "PRIMARY KEY (id)) "
            "ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 "
            "COLLATE=utf8_unicode_ci".format(self.tbl)
        )
        self.cur.execute(create)

    def tearDown(self):
        self.cur.execute("DROP TABLE IF EXISTS {0}".format(self.tbl))
        self.cur.close()
        self.cnx.close()

    def test_binary_charset(self):
        cur = self.cnx.cursor(prepared=True)
        sql = "INSERT INTO {0}(text, rooms) VALUES(%s, %s)".format(self.tbl)
        cur.execute(sql, ("a" * 252, 1))
        cur.execute(sql, ("a" * 253, 2))
        cur.execute(sql, ("a" * 255, 3))
        cur.execute(sql, ("a" * 251, 4))
        cur.execute(sql, ("a" * 65535, 5))

        exp = [
            (1, "a" * 252, 1),
            (2, "a" * 253, 2),
            (3, "a" * 255, 3),
            (4, "a" * 251, 4),
            (5, "a" * 65535, 5),
        ]

        self.cur.execute("SELECT * FROM {0}".format(self.tbl))
        self.assertEqual(exp, self.cur.fetchall())


class BugOra20301989(tests.MySQLConnectorTests):
    """BUG#20301989: SET DATA TYPE NOT TRANSLATED CORRECTLY WHEN EMPTY"""

    def setUp(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        cur = cnx.cursor()

        self.tbl = "Bug20301989"
        cur.execute(f"DROP TABLE IF EXISTS {self.tbl}")

        create = f"""
            CREATE TABLE {self.tbl}
            (id INT AUTO_INCREMENT PRIMARY KEY, col1 SET('val1', 'val2'))
            DEFAULT CHARSET latin1
            """
        cur.execute(create)
        cur.close()
        cnx.close()

    def tearDown(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        cur = cnx.cursor()
        cur.execute(f"DROP TABLE IF EXISTS {self.tbl}")
        cur.close()
        cnx.close()

    @foreach_cnx()
    def test_set(self):
        cur = self.cnx.cursor()
        sql = f"INSERT INTO {self.tbl} (col1) VALUES(%s)"
        cur.execute(sql, ("val1,val2",))
        cur.execute(sql, ("val1",))
        cur.execute(sql, ("",))
        cur.execute(sql, (None,))

        exp = [(set(["val1", "val2"]),), (set(["val1"]),), (set([]),), (None,)]

        cur.execute(f"SELECT col1 FROM {self.tbl}")
        self.assertEqual(exp, cur.fetchall())


@unittest.skipIf(
    tests.MYSQL_EXTERNAL_SERVER,
    "Test not available for external MySQL servers",
)
class BugOra20462427(tests.MySQLConnectorTests):
    """BUG#20462427: BYTEARRAY INDEX OUT OF RANGE"""

    def setUp(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        cur = cnx.cursor()

        self.tbl = "BugOra20462427"
        cur.execute("DROP TABLE IF EXISTS {0}".format(self.tbl))

        create = (
            "CREATE TABLE {0} ("
            "id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, "
            "a LONGTEXT "
            ") ENGINE=Innodb DEFAULT CHARSET utf8".format(self.tbl)
        )

        cur.execute(create)

    def tearDown(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        cur = cnx.cursor()
        cur.execute("DROP TABLE IF EXISTS {0}".format(self.tbl))
        cur.close()
        cnx.close()

    def _test_bigdata(self):
        temp = "a" * 16777210
        insert = "INSERT INTO {0} (a) VALUES ('{1}')".format(self.tbl, temp)

        cur = self.cnx.cursor()
        cur.execute(insert)
        cur.execute("SELECT a FROM {0}".format(self.tbl))
        res = cur.fetchall()
        self.assertEqual(16777210, len(res[0][0]))

        cur.execute("UPDATE {0} SET a = concat(a, 'a')".format(self.tbl))
        cur.execute("SELECT a FROM {0}".format(self.tbl))
        res = cur.fetchall()
        self.assertEqual(16777211, len(res[0][0]))

        cur.execute("UPDATE {0} SET a = concat(a, 'a')".format(self.tbl))
        cur.execute("SELECT a FROM {0}".format(self.tbl))
        res = cur.fetchall()
        self.assertEqual(16777212, len(res[0][0]))

        cur.execute("UPDATE {0} SET a = concat(a, 'a')".format(self.tbl))
        cur.execute("SELECT a FROM {0}".format(self.tbl))
        res = cur.fetchall()
        self.assertEqual(16777213, len(res[0][0]))

        cur.execute("UPDATE {0} SET a = concat(a, 'aaa')".format(self.tbl))
        cur.execute("SELECT a FROM {0}".format(self.tbl))
        res = cur.fetchall()
        self.assertEqual(16777216, len(res[0][0]))

        cur.close()

    @cnx_config(compress=False, connection_timeout=100)
    @foreach_cnx()
    def test_bigdata_compress(self):
        self._test_bigdata()

    @cnx_config(connection_timeout=100)
    @foreach_cnx()
    def test_bigdata_nocompress(self):
        self._test_bigdata()


class BugOra20811802(tests.MySQLConnectorTests):
    """BUG#20811802:  ISSUES WHILE USING BUFFERED=TRUE OPTION WITH CPY CEXT"""

    def setUp(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        cur = cnx.cursor()

        self.tbl = "Bug20811802"
        cur.execute("DROP TABLE IF EXISTS {0}".format(self.tbl))

        create = (
            "CREATE TABLE {0} (id INT PRIMARY KEY, name VARCHAR(5), dept VARCHAR(5)) "
            "DEFAULT CHARSET latin1".format(self.tbl)
        )
        cur.execute(create)
        cur.close()
        cnx.close()

    def tearDown(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        cur = cnx.cursor()
        cur.execute("DROP TABLE IF EXISTS {0}".format(self.tbl))
        cur.close()
        cnx.close()

    @foreach_cnx()
    def test_set(self):
        cur = self.cnx.cursor()
        sql = "INSERT INTO {0} VALUES(%s, %s, %s)".format(self.tbl)

        data = [
            (1, "abc", "cs"),
            (2, "def", "is"),
            (3, "ghi", "cs"),
            (4, "jkl", "it"),
        ]
        cur.executemany(sql, data)
        cur.close()

        cur = self.cnx.cursor(dictionary=True, buffered=True)
        cur.execute("SELECT * FROM {0}".format(self.tbl))
        i = 0
        for row in cur:
            self.assertEqual(row, dict(zip(("id", "name", "dept"), data[i])))
            i += 1

        cur = self.cnx.cursor(dictionary=True, buffered=False)
        cur.execute("SELECT * FROM {0}".format(self.tbl))
        i = 0
        for row in cur:
            self.assertEqual(row, dict(zip(("id", "name", "dept"), data[i])))
            i += 1


class BugOra20653441(tests.MySQLConnectorTests):
    """BUG#20653441: PYTHON CONNECTOR HANGS IF A QUERY IS KILLED (ERROR 1317)"""

    def setUp(self):
        self.table_name = "Bug20653441"
        self._setup()

    def _setup(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        cnx.cmd_query("DROP TABLE IF EXISTS {0}".format(self.table_name))
        table = (
            "CREATE TABLE {table} ("
            " id INT UNSIGNED NOT NULL AUTO_INCREMENT,"
            " c1 VARCHAR(255) DEFAULT '{default}',"
            " PRIMARY KEY (id)"
            ")"
        ).format(table=self.table_name, default="a" * 255)
        cnx.cmd_query(table)

        stmt = "INSERT INTO {table} (id) VALUES {values}".format(
            table=self.table_name, values=",".join(["(NULL)"] * 1024)
        )
        cnx.cmd_query(stmt)
        cnx.commit()
        cnx.close()

    def tearDown(self):
        try:
            cnx = connection.MySQLConnection(**tests.get_mysql_config())
            cnx.cmd_query("DROP TABLE IF EXISTS {0}".format(self.table_name))
            cnx.close()
        except:
            pass

    @unittest.skipIf(platform.machine() == "arm64", "Test not available for ARM64")
    @foreach_cnx()
    def test_kill_query(self):
        def kill(connection_id):
            """Kill query using separate connection"""
            killer_cnx = connection.MySQLConnection(**tests.get_mysql_config())
            sleep(1)
            killer_cnx.cmd_query("KILL QUERY {0}".format(connection_id))
            killer_cnx.close()

        def sleepy_select(cnx):
            """Execute a SELECT statement which takes a while to complete"""
            cur = cnx.cursor()
            # Ugly query ahead!
            stmt = "SELECT x1.*, x2.* from {table} as x1, {table} as x2".format(
                table=self.table_name
            )
            cur.execute(stmt)
            # Save the error so we can check in the calling thread
            cnx.test_error = None

            try:
                cur.fetchall()
            except errors.Error as err:
                cnx.test_error = err
                cur.close()

        worker = Thread(target=sleepy_select, args=[self.cnx])
        killer = Thread(target=kill, args=[self.cnx.connection_id])
        worker.start()
        killer.start()
        worker.join()
        killer.join()

        self.cnx.close()

        self.assertTrue(isinstance(self.cnx.test_error, errors.DatabaseError))
        self.assertEqual(
            str(self.cnx.test_error),
            "1317 (70100): Query execution was interrupted",
        )


class BugOra21535573(tests.MySQLConnectorTests):
    """BUG#21535573:  SEGFAULT WHEN TRY TO SELECT GBK DATA WITH C-EXTENSION"""

    def tearDown(self):
        cnx = connection.MySQLConnection(**tests.get_mysql_config())
        for charset in ("gbk", "sjis", "big5"):
            tablename = charset + "test"
            cnx.cmd_query("DROP TABLE IF EXISTS {0}".format(tablename))
        cnx.close()

    def _test_charset(self, charset, data):
        config = tests.get_mysql_config()
        config["charset"] = charset
        config["use_unicode"] = True
        self.cnx = self.cnx.__class__(**config)
        tablename = charset + "test"
        cur = self.cnx.cursor()

        cur.execute("DROP TABLE IF EXISTS {0}".format(tablename))
        column = data
        table = (
            "CREATE TABLE {table} ("
            " {col} INT AUTO_INCREMENT KEY, "
            "c1 VARCHAR(40)"
            ") CHARACTER SET '{charset}'"
        ).format(table=tablename, charset=charset, col=column)
        cur.execute(table)
        self.cnx.commit()

        cur.execute("TRUNCATE {0}".format(tablename))
        self.cnx.commit()

        insert = "INSERT INTO {0} (c1) VALUES (%s)".format(tablename)
        cur.execute(insert, (data,))
        self.cnx.commit()

        cur.execute("SELECT * FROM {0}".format(tablename))
        for row in cur:
            self.assertEqual(data, row[1])

        cur.close()
        self.cnx.close()

    @foreach_cnx()
    def test_gbk(self):
        self._test_charset("gbk", "海豚")

    @foreach_cnx()
    def test_sjis(self):
        self._test_charset("sjis", "シイラ")

    @foreach_cnx()
    def test_big5(self):
        self._test_charset("big5", "皿")


class BugOra21536507(tests.MySQLConnectorTests):
    """BUG#21536507:C/PYTHON BEHAVIOR NOT PROPER WHEN RAISE_ON_WARNINGS=TRUE"""

    @cnx_config(raw=False, get_warnings=True, raise_on_warnings=True)
    @foreach_cnx()
    def test_with_raw(self):
        cur = self.cnx.cursor()
        drop_stmt = "DROP TABLE IF EXISTS unknown"
        self.assertRaises(errors.DatabaseError, cur.execute, drop_stmt)
        exp = [("Note", 1051, "Unknown table 'myconnpy.unknown'")]
        res = cur.warnings
        self.assertEqual("Note", res[0][0])
        self.assertEqual(1051, res[0][1])
        self.assertTrue(res[0][2].startswith("Unknown table"))

        select_stmt = "SELECT 'a'+'b'"
        cur.execute(select_stmt)
        self.assertRaises(errors.DatabaseError, cur.fetchall)
        if tests.MYSQL_VERSION >= (8, 0, 23) or os.name != "nt":
            exp = [
                ("Warning", 1292, "Truncated incorrect DOUBLE value: 'a'"),
                ("Warning", 1292, "Truncated incorrect DOUBLE value: 'b'"),
            ]
        else:
            exp = [
                ("Warning", 1292, "Truncated incorrect DOUBLE value: 'b'"),
                ("Warning", 1292, "Truncated incorrect DOUBLE value: 'a'"),
            ]
        self.assertEqual(exp, cur.warnings)
        try:
            cur.close()
        except errors.InternalError as exc:
            self.fail("Closing cursor failed with: %s" % str(exc))


class BugOra21420633(tests.MySQLConnectorTests):
    """BUG#21420633: CEXTENSION CRASHES WHILE FETCHING LOTS OF NULL VALUES"""

    def setUp(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        cur = cnx.cursor()

        self.tbl = "Bug21420633"
        cur.execute("DROP TABLE IF EXISTS {0}".format(self.tbl))

        create = (
            "CREATE TABLE {0} (id INT PRIMARY KEY, dept VARCHAR(5)) "
            "DEFAULT CHARSET latin1".format(self.tbl)
        )
        cur.execute(create)
        cur.close()
        cnx.close()

    def tearDown(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        cur = cnx.cursor()
        cur.execute("DROP TABLE IF EXISTS {0}".format(self.tbl))
        cur.close()
        cnx.close()

    @foreach_cnx()
    def test_null(self):
        cur = self.cnx.cursor()
        sql = "INSERT INTO {0} VALUES(%s, %s)".format(self.tbl)

        data = [(i, None) for i in range(10000)]

        cur.executemany(sql, data)
        cur.close()

        cur = self.cnx.cursor()
        cur.execute("SELECT * FROM {0}".format(self.tbl))

        res = cur.fetchall()
        cur.close()


@unittest.skipIf(
    tests.MYSQL_EXTERNAL_SERVER,
    "Test not available for external MySQL servers",
)
class BugOra21492428(tests.MySQLConnectorTests):
    """BUG#21492428: CONNECT FAILS WHEN PASSWORD STARTS OR ENDS WITH SPACES"""

    def setUp(self):
        config = tests.get_mysql_config()
        self.cnx = connection.MySQLConnection(**config)
        self.cursor = self.cnx.cursor()

        if config["unix_socket"] and os.name != "nt":
            self.host = "localhost"
        else:
            self.host = config["host"]

        grant = "CREATE USER '{user}'@'{host}' IDENTIFIED BY '{password}'"

        self._credentials = [
            ("ABCD", " XYZ"),
            ("PQRS", " 1 2 3 "),
            ("XYZ1", "XYZ123    "),
            ("A B C D", "    ppppp    "),
        ]

        if self.cnx.server_version > (5, 6):
            self._credentials += [
                (" PQRSWITHSPACE", " 1 2 3 "),
                ("XYZ1WITHSPACE ", "XYZ123    "),
                (" S P A C E D ", "    ppppp    "),
            ]

        for user, password in self._credentials:
            try:
                self.cursor.execute(
                    "DROP USER '{user}'@'{host}'".format(user=user, host=self.host)
                )
            except errors.DatabaseError:
                pass
            self.cursor.execute(
                grant.format(user=user, host=self.host, password=password)
            )

    def tearDown(self):
        for user, password in self._credentials:
            self.cursor.execute(
                "DROP USER '{user}'@'{host}'".format(user=user, host=self.host)
            )

    def test_password_with_spaces(self):
        config = tests.get_mysql_config()
        for user, password in self._credentials:
            config["user"] = user
            config["password"] = password
            config["database"] = None
            try:
                cnx = connection.MySQLConnection(**config)
            except errors.ProgrammingError:
                self.fail("Failed using password with spaces for user %s" % user)
            else:
                cnx.close()


class BugOra21476495(tests.MySQLConnectorTests):
    """Bug 21476495 - CHARSET VALUE REMAINS INVALID AFTER FAILED
    SET_CHARSET_COLLATION() CALL
    """

    def setUp(self):
        config = tests.get_mysql_config()
        self.cnx = connection.MySQLConnection(**config)

    def test_bad_set_charset_number(self):
        old_val = self.cnx.charset_id
        self.assertRaises(mysql.connector.Error, self.cnx.set_charset_collation, 19999)

        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        cursor = cnx.cursor(raw="true", buffered="true")
        cursor.execute("SHOW VARIABLES LIKE 'character_set_connection'")
        row = cursor.fetchone()
        self.assertEqual(row[1], "utf8mb4")
        cursor.close()

        self.assertEqual(self.cnx.charset_id, old_val)


class BugOra21477493(tests.MySQLConnectorTests):
    """Bug 21477493 - EXECUTEMANY() API WITH INSERT INTO .. SELECT STATEMENT
    RETURNS INTERFACEERROR
    """

    def setUp(self):
        config = tests.get_mysql_config()
        self.cnx = connection.MySQLConnection(**config)
        cursor = self.cnx.cursor()
        cursor.execute("DROP TABLE IF EXISTS fun1")
        cursor.execute(
            "CREATE TABLE fun1(id INT AUTO_INCREMENT PRIMARY KEY, a CHAR(50), b INT)"
        )
        data = [("A", 1), ("B", 2)]
        cursor.executemany("INSERT INTO fun1 (a, b) VALUES (%s, %s)", data)
        cursor.close()

    def tearDown(self):
        cursor = self.cnx.cursor()
        cursor.execute("DROP TABLE IF EXISTS fun1")
        cursor.close()

    def test_insert_into_select_type1(self):
        data = [("A", 1), ("B", 2)]
        cursor = self.cnx.cursor()
        cursor.executemany(
            "INSERT INTO fun1 (a, b) SELECT CONCAT('VALUES', %s), b + %s FROM fun1",
            data,
        )
        cursor.close()

        cursor = self.cnx.cursor()
        cursor.execute("SELECT a, b FROM fun1")
        self.assertEqual(8, len(cursor.fetchall()))

    def test_insert_into_select_type2(self):
        data = [("A", 1), ("B", 2)]
        cursor = self.cnx.cursor()
        cursor.executemany(
            "INSERT INTO fun1 (a, b) "
            "SELECT CONCAT('VALUES(ab, cd)',%s), b + %s FROM fun1",
            data,
        )
        cursor.close()

        cursor = self.cnx.cursor()
        cursor.execute("SELECT * FROM fun1")
        self.assertEqual(8, len(cursor.fetchall()))

    def test_insert_into_select_type3(self):
        config = tests.get_mysql_config()
        data = [("A", 1), ("B", 2)]
        cursor = self.cnx.cursor()
        cursor.executemany(
            "INSERT INTO `{0}`.`fun1` (a, b) SELECT CONCAT('"
            "VALUES(ab, cd)', %s), b + %s FROM fun1"
            "".format(config["database"]),
            data,
        )
        cursor.close()

        cursor = self.cnx.cursor()
        cursor.execute("SELECT * FROM fun1")
        self.assertEqual(8, len(cursor.fetchall()))


class BugOra21492815(tests.MySQLConnectorTests):
    """BUG#21492815: CALLPROC() HANGS WHEN CONSUME_RESULTS=TRUE"""

    def setUp(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        cur = cnx.cursor()

        self.proc1 = "Bug20834643"
        self.proc2 = "Bug20834643_1"
        cur.execute("DROP PROCEDURE IF EXISTS {0}".format(self.proc1))

        create = "CREATE PROCEDURE {0}() BEGIN SELECT 1234; END".format(self.proc1)
        cur.execute(create)
        cur.execute("DROP PROCEDURE IF EXISTS {0}".format(self.proc2))

        create = (
            "CREATE PROCEDURE {0}() BEGIN SELECT 9876; "
            "SELECT CONCAT('','abcd'); END".format(self.proc2)
        )
        cur.execute(create)
        cur.close()
        cnx.close()

    def tearDown(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        cur = cnx.cursor()
        cur.execute("DROP PROCEDURE IF EXISTS {0}".format(self.proc1))
        cur.execute("DROP PROCEDURE IF EXISTS {0}".format(self.proc2))
        cur.close()
        cnx.close()

    @cnx_config(consume_results=True, raw=True)
    @foreach_cnx()
    def test_set(self):
        cur = self.cnx.cursor()
        cur.callproc(self.proc1)
        self.assertEqual((bytearray(b"1234"),), next(cur.stored_results()).fetchone())

        cur.callproc(self.proc2)
        exp = [[(bytearray(b"9876"),)], [(bytearray(b"abcd"),)]]
        results = []
        for result in cur.stored_results():
            results.append(result.fetchall())
        self.assertEqual(exp, results)
        cur.close()

    @cnx_config(consume_results=True, raw=False)
    @foreach_cnx()
    def test_set(self):
        cur = self.cnx.cursor()
        cur.callproc(self.proc1)
        self.assertEqual((1234,), next(cur.stored_results()).fetchone())

        cur.callproc(self.proc2)
        exp = [[(9876,)], [("abcd",)]]
        results = []
        for result in cur.stored_results():
            results.append(result.fetchall())
        self.assertEqual(exp, results)
        cur.close()


@unittest.skipIf(
    tests.MYSQL_EXTERNAL_SERVER,
    "Test not available for external MySQL servers",
)
@unittest.skipIf(not CMySQLConnection, ERR_NO_CEXT)
class BugOra21656282(tests.MySQLConnectorTests):
    """BUG#21656282: CONNECT FAILURE WITH C-EXT WHEN PASSWORD CONTAINS UNICODE
    CHARACTER
    """

    def setUp(self):
        config = tests.get_mysql_config()
        self.cnx = CMySQLConnection(**config)
        self.host = (
            "127.0.0.1" if config["unix_socket"] and os.name != "nt" else config["host"]
        )
        self.user = "unicode_user"
        self.password = "步"

        # Use utf8mb4 character set
        self.cnx.cmd_query("SET character_set_server='utf8mb4'")

        # Drop user if exists
        self._drop_user(self.host, self.user)

        # Create the user with unicode password
        create_user = "CREATE USER '{user}'@'{host}' IDENTIFIED BY '{password}'"
        self.cnx.cmd_query(
            create_user.format(user=self.user, host=self.host, password=self.password)
        )

        # Grant all to new user on database
        grant = "GRANT ALL ON {database}.* TO '{user}'@'{host}'"
        self.cnx.cmd_query(
            grant.format(database=config["database"], user=self.user, host=self.host)
        )

    def tearDown(self):
        self._drop_user(self.host, self.user)

    def _drop_user(self, host, user):
        try:
            drop_user = "DROP USER '{user}'@'{host}'"
            self.cnx.cmd_query(drop_user.format(user=user, host=host))
        except errors.DatabaseError:
            # It's OK when drop user fails
            pass

    def test_unicode_password(self):
        config = tests.get_mysql_config()
        config.pop("unix_socket")
        config["user"] = self.user
        config["password"] = self.password
        try:
            cnx = CMySQLConnection(**config)
        except Exception as err:
            self.fail(
                "Failed using password with unicode characters: "
                "e->{} t->{}".format(err, type(err))
            )
        else:
            cnx.close()


class BugOra21530841(tests.MySQLConnectorTests):
    """BUG#21530841: SELECT FAILS WITH ILLEGAL RESULT SET ERROR WHEN COLUMN
    COUNT IN RESULT > 4096
    """

    def setUp(self):
        config = tests.get_mysql_config()
        self.cnx = connection.MySQLConnection(**config)
        self.tbl = "Bug21530841"
        self.cnx.cmd_query("DROP TABLE IF EXISTS {0}".format(self.tbl))

    def tearDown(self):
        self.cnx.cmd_query("DROP TABLE IF EXISTS {0}".format(self.tbl))
        self.cnx.close()

    def test_big_column_count(self):
        cur = self.cnx.cursor(raw=False, buffered=False)
        # Create table with 512 Columns
        table = "CREATE TABLE {0} (id INT AUTO_INCREMENT PRIMARY KEY, {1})".format(
            self.tbl, ", ".join(["c{0} INT".format(idx) for idx in range(512)])
        )
        cur.execute(table)

        # Insert 1 record
        cur.execute("INSERT INTO {0}(c1) values (1) ".format(self.tbl))
        self.cnx.commit()

        # Select from 10 tables
        query = "SELECT * FROM {0} WHERE a1.c1 > 0".format(
            ", ".join(["{0} a{1}".format(self.tbl, idx) for idx in range(10)])
        )
        cur.execute(query)
        cur.fetchone()
        cur.close()


@unittest.skipIf(
    tests.MYSQL_EXTERNAL_SERVER,
    "Test not available for external MySQL servers",
)
@unittest.skipIf(sys.version_info < (2, 7, 9), "Python 2.7.9+ is required for SSL")
class BugOra25397650(tests.MySQLConnectorTests):
    """BUG#25397650: CERTIFICATE VALIDITY NOT VERIFIED"""

    def setUp(self):
        self.config = tests.get_mysql_config().copy()
        self.config.pop("unix_socket")
        self.config["host"] = "localhost"
        self.ca = os.path.abspath(os.path.join(tests.SSL_DIR, "tests_CA_cert.pem"))
        self.ca_1 = os.path.abspath(os.path.join(tests.SSL_DIR, "tests_CA_cert_1.pem"))

    def _verify_cert(self, config):
        # Test with a bad CA
        config["ssl_ca"] = self.ca_1
        config["ssl_verify_cert"] = True
        self.assertRaises(errors.InterfaceError, mysql.connector.connect, **config)
        config["ssl_verify_cert"] = False
        mysql.connector.connect(**config)

        # Test with the correct CA
        config["ssl_ca"] = self.ca
        config["ssl_verify_cert"] = True
        mysql.connector.connect(**config)
        config["ssl_verify_cert"] = False
        mysql.connector.connect(**config)

    def test_pure_verify_server_certificate(self):
        config = self.config.copy()
        config["use_pure"] = True

        self._verify_cert(config)

    @unittest.skipIf(not CMySQLConnection, ERR_NO_CEXT)
    def test_cext_verify_server_certificate(self):
        config = self.config.copy()
        config["use_pure"] = False

        self._verify_cert(config)


@unittest.skipIf(tests.MYSQL_VERSION < (5, 6, 39), "skip in older server")
@unittest.skipIf(not CMySQLConnection, ERR_NO_CEXT)
class Bug28133321(tests.MySQLConnectorTests):
    """BUG#28133321: FIX INCORRECT COLUMNS NAMES REPRESENTING AGGREGATE
    FUNCTIONS
    """

    tbl = "BUG28133321"

    def setUp(self):
        create_table = (
            "CREATE TABLE {} ("
            "  dish_id INT(11) UNSIGNED AUTO_INCREMENT UNIQUE KEY,"
            "  category TEXT,"
            "  dish_name TEXT,"
            "  price FLOAT,"
            "  servings INT,"
            "  order_time TIME) CHARACTER SET utf8"
            " COLLATE utf8_general_ci"
        )
        config = tests.get_mysql_config()
        cnx = CMySQLConnection(**config)

        try:
            cnx.cmd_query("DROP TABLE IF EXISTS {0}".format(self.tbl))
        except:
            pass
        cnx.cmd_query(create_table.format(self.tbl))

        cur = cnx.cursor(dictionary=True)
        insert_stmt = (
            "INSERT INTO {} ("
            "  category, dish_name, price, servings, order_time"
            ') VALUES ("{{}}", "{{}}", {{}}, {{}}, "{{}}")'
        ).format(self.tbl)
        values = [
            ("dinner", "lassanya", 10.53, "2", "00:10"),
            ("dinner", "hamburger", 9.35, "1", "00:15"),
            ("dinner", "hamburger whit fries", 10.99, "2", "00:20"),
            ("dinner", "Pizza", 9.99, "4", "00:30"),
            ("dessert", "cheescake", 4.95, "1", "00:05"),
            ("dessert", "cheescake special", 5.95, "2", "00:05"),
        ]

        for value in values:
            cur.execute(insert_stmt.format(*value))
        cnx.close()

    def tearDown(self):
        config = tests.get_mysql_config()
        cnx = CMySQLConnection(**config)
        try:
            cnx.cmd_query("DROP TABLE IF EXISTS {0}".format(self.tbl))
        except:
            pass
        cnx.close()

    @unittest.skipIf(
        tests.MYSQL_EXTERNAL_SERVER,
        "Test not available for external MySQL servers",
    )
    def test_columns_name_are_not_bytearray(self):
        sql_statement = [
            "SELECT",
            "  dish_id,",
            "  category,",
            "  JSON_OBJECTAGG(category, dish_name) as special,",
            "  JSON_ARRAYAGG(dish_name) as dishes,",
            "  GROUP_CONCAT(dish_name) as dishes2,",
            "  price,",
            "  servings,",
            "  ROUND(AVG(price)) AS round_avg_price,",
            "  AVG(price) AS avg_price,",
            "  MIN(price) AS min_price,",
            "  MAX(price) AS max_price,",
            "  MAX(order_time) AS preparation_time,",
            "  STD(servings) as deviation,",
            "  SUM(price) AS sum,",
            "  VARIANCE(price) AS var,",
            "  COUNT(DISTINCT servings) AS cd_servings,",
            "  COUNT(servings) AS c_servings ",
            "FROM {} ",
            "GROUP BY category",
        ]
        # Remove JSON functions when testing againsts server version < 5.7.22
        # JSON_OBJECTAGG JSON_ARRAYAGG were introduced on 5.7.22
        if tests.MYSQL_VERSION < (5, 7, 22):
            sql_statement.pop(3)
            sql_statement.pop(3)
        sql_statement = "".join(sql_statement)
        config = tests.get_mysql_config()
        cnx = CMySQLConnection(**config)

        cur = cnx.cursor(dictionary=True)
        cur.execute(sql_statement.format(self.tbl))
        rows = cur.fetchall()
        col_names = [x[0] for x in cur.description]

        for row in rows:
            for col, val in row.items():
                self.assertTrue(
                    isinstance(col, str),
                    "The columns name {} is not a string type".format(col),
                )
                self.assertFalse(
                    isinstance(col, (bytearray)),
                    "The columns name {} is a bytearray type".format(col),
                )
                self.assertFalse(
                    isinstance(val, (bytearray)),
                    "The value {} of column {} is a bytearray type".format(val, col),
                )

        for col_name in col_names:
            self.assertTrue(
                isinstance(col_name, str),
                "The columns name {} is not a string type".format(col_name),
            )
            self.assertFalse(
                isinstance(col_name, (bytearray)),
                "The columns name {} is a bytearray type".format(col_name),
            )


@unittest.skipIf(
    tests.MYSQL_EXTERNAL_SERVER,
    "Test not available for external MySQL servers",
)
class BugOra21947091(tests.MySQLConnectorTests):
    """BUG#21947091: PREFER TLS WHERE SUPPORTED BY MYSQL SERVER."""

    def setUp(self):
        self.config = tests.get_mysql_config()
        self.config.pop("unix_socket")
        self.server = tests.MYSQL_SERVERS[0]

    def _disable_ssl(self):
        self.server.stop()
        self.server.wait_down()

        self.server.start(ssl_ca="", ssl_cert="", ssl_key="", ssl=0)
        self.server.wait_up()
        sleep(1)

    def _enable_ssl(self):
        self.server.stop()
        self.server.wait_down()

        self.server.start(ssl=1)
        self.server.wait_up()
        sleep(1)

    def _verify_ssl(self, cnx, ssl_available=True):
        cur = cnx.cursor()
        cur.execute("SHOW STATUS LIKE 'Ssl_version'")
        result = cur.fetchall()[0]
        if ssl_available:
            self.assertNotEqual(result[1], "")
        else:
            self.assertEqual(result[1], "")

    def test_ssl_disabled_pure(self):
        self.config["use_pure"] = True
        self._test_ssl_modes()

    @unittest.skipIf(not CMySQLConnection, ERR_NO_CEXT)
    def test_ssl_disabled_cext(self):
        self.config["use_pure"] = False
        self._test_ssl_modes()

    def _test_ssl_modes(self):
        # SSL isn't disabled by default on the connector side,
        # however, it is disabled, on the custom bootstrapped server.
        config = self.config.copy()

        # disabled
        config["ssl_disabled"] = True
        cnx = mysql.connector.connect(**config)
        self._verify_ssl(cnx, ssl_available=False)

        # With SSL on server
        try:
            self._enable_ssl()
            config["ssl_ca"] = tests.SSL_CA
            config["ssl_disabled"] = False
            cnx = mysql.connector.connect(**config)
            self._verify_ssl(cnx, ssl_available=True)
        finally:
            self._disable_ssl()


class BugOra25589496(tests.MySQLConnectorTests):
    """BUG#25589496: COMMITS RELATED TO "BUG22529828" BROKE BINARY DATA
    HANDLING FOR PYTHON 2.7
    """

    def setUp(self):
        config = tests.get_mysql_config()
        self.cnx = connection.MySQLConnection(**config)
        self.tbl = "Bug25589496"
        self.cnx.cmd_query("DROP TABLE IF EXISTS {0}".format(self.tbl))

    def tearDown(self):
        self.cnx.cmd_query("DROP TABLE IF EXISTS {0}".format(self.tbl))
        self.cnx.close()

    def test_insert_binary(self):
        table = """
        CREATE TABLE {0} (
            `id` int(10) unsigned NOT NULL AUTO_INCREMENT PRIMARY KEY,
            `section` VARCHAR(50) NOT NULL,
            `pickled` LONGBLOB NOT NULL
        )
        """.format(
            self.tbl
        )
        cursor = self.cnx.cursor()
        cursor.execute(table)

        pickled = pickle.dumps({"a": "b"}, pickle.HIGHEST_PROTOCOL)
        add_row_q = (
            "INSERT INTO {0} (section, pickled) "
            "VALUES (%(section)s, %(pickled)s)".format(self.tbl)
        )

        new_row = cursor.execute(add_row_q, {"section": "foo", "pickled": pickled})
        self.cnx.commit()
        self.assertEqual(1, cursor.lastrowid)
        cursor.close()


@unittest.skipIf(
    tests.MYSQL_EXTERNAL_SERVER,
    "Test not available for external MySQL servers",
)
class BugOra25383644(tests.MySQLConnectorTests):
    """BUG#25383644: LOST SERVER CONNECTION LEAKS POOLED CONNECTIONS"""

    def setUp(self):
        self.sql = "SELECT * FROM dummy"
        self.mysql_server = tests.MYSQL_SERVERS[0]

    def run_test(self, cnxpool):
        i = 2
        while i > 0:
            cnx = cnxpool.get_connection()
            cur = cnx.cursor()
            try:
                self.mysql_server.stop()
                self.mysql_server.wait_down()
                cur.execute(self.sql)
            except (
                mysql.connector.errors.OperationalError,
                mysql.connector.errors.ProgrammingError,
                mysql.connector.errors.DatabaseError,
            ):
                try:
                    cur.close()
                    cnx.close()
                except mysql.connector.errors.OperationalError:
                    pass
            finally:
                i -= 1
                if not self.mysql_server.check_running():
                    self.mysql_server.start()
                    self.mysql_server.wait_up()

    def test_pool_exhaustion_pure(self):
        config = tests.get_mysql_config()
        config["pool_size"] = 1
        config["use_pure"] = True
        config["pool_name"] = "BugOra25383644-pure"
        cnxpool = pooling.MySQLConnectionPool(**config)
        self.run_test(cnxpool)

    @unittest.skipIf(not CMySQLConnection, ERR_NO_CEXT)
    def test_pool_exhaustion_cext(self):
        config = tests.get_mysql_config()
        config["pool_size"] = 1
        config["use_pure"] = False
        config["pool_name"] = "BugOra25383644-c-ext"
        cnxpool = pooling.MySQLConnectionPool(**config)
        self.run_test(cnxpool)


class BugOra25558885(tests.MySQLConnectorTests):
    """BUG#25558885: ERROR 2013 (LOST CONNECTION TO MYSQL SERVER) USING C
    EXTENSIONS
    """

    def setUp(self):
        pass

    def _long_query(self, config, cursor_class):
        db_conn = mysql.connector.connect(**config)
        cur = db_conn.cursor(cursor_class=cursor_class)
        cur.execute("select sleep(15)")
        cur.close()
        db_conn.disconnect()

    @unittest.skipIf(not CMySQLConnection, ERR_NO_CEXT)
    def test_cext_cnx(self):
        config = tests.get_mysql_config()
        config["use_pure"] = False
        del config["connection_timeout"]
        cursor_class = mysql.connector.cursor_cext.CMySQLCursorBufferedRaw
        self._long_query(config, cursor_class)

    def test_pure_cnx(self):
        config = tests.get_mysql_config()
        config["use_pure"] = True
        del config["connection_timeout"]
        cursor_class = mysql.connector.cursor.MySQLCursorBufferedRaw
        self._long_query(config, cursor_class)


class BugOra22564149(tests.MySQLConnectorTests):
    """BUG#22564149: CMD_QUERY_ITER ERRONEOUSLY CALLS ".ENCODE('UTF8')" ON
    BYTESTRINGS
    """

    def setUp(self):
        config = tests.get_mysql_config()
        self.tbl = "BugOra22564149"
        self.cnx = connection.MySQLConnection(**config)
        self.cnx.cmd_query(f"DROP TABLE IF EXISTS {self.tbl}")
        self.cnx.cmd_query(
            f"CREATE TABLE {self.tbl} (id INT PRIMARY KEY, name VARCHAR(50))"
        )

    def tearDown(self):
        self.cnx.cmd_query(f"DROP TABLE IF EXISTS {self.tbl}")
        self.cnx.close()

    def test_cmd_query_iter(self):
        stmt = "SELECT 1; INSERT INTO {0} VALUES (1, 'João'),(2, 'André'); SELECT 3"
        results = []
        for result in self.cnx.cmd_query_iter(stmt.format(self.tbl).encode("utf-8")):
            results.append(result)
            if "columns" in result:
                results.append(self.cnx.get_rows())


class BugOra24659561(tests.MySQLConnectorTests):
    """BUG#24659561: LOOKUPERROR: UNKNOWN ENCODING: UTF8MB4"""

    def setUp(self):
        config = tests.get_mysql_config()
        config["charset"] = "utf8mb4"
        config["collation"] = "utf8mb4_general_ci"
        self.tbl = "BugOra24659561"
        self.cnx = connection.MySQLConnection(**config)
        self.cur = self.cnx.cursor()
        self.cur.execute(f"DROP TABLE IF EXISTS {self.tbl}")
        self.cur.execute(
            f"CREATE TABLE {self.tbl} (id INT PRIMARY KEY, name VARCHAR(100))"
        )

    def tearDown(self):
        self.cur.execute(f"DROP TABLE IF EXISTS {self.tbl}")
        self.cur.close()

    def test_executemany_utf8mb4(self):
        self.cur.executemany(
            f"INSERT INTO {self.tbl} VALUES (%s, %s)",
            [(1, "Nuno"), (2, "Amitabh"), (3, "Rafael")],
        )


@unittest.skipIf(not CMySQLConnection, ERR_NO_CEXT)
class BugOra27991948(tests.MySQLConnectorTests):
    """BUG#27991948: UNREAD_RESULT IS NOT UNSET AFTER INVOKE GET_ROWS ON C-EXT"""

    test_sql_single_result = "show variables like '%port%'"
    cnx_cext = None
    cnx_cext_raw = None

    def setUp(self):
        config_cext = tests.get_mysql_config()
        config_cext["use_pure"] = False
        self.cnx_cext = mysql.connector.connect(**config_cext)

    def tearDown(self):
        self.cnx_cext.close()

    def test_automatically_set_of_unread_rows(self):
        """Test unread_rows is automatically set after fetchall()"""
        # Test get all the rows and execute a query without invoke free_result
        self.cnx_cext.cmd_query(self.test_sql_single_result)
        unread_result = self.cnx_cext.unread_result
        self.assertTrue(unread_result, "unread_rows is expected to be True")
        _ = self.cnx_cext.get_rows()
        unread_result = self.cnx_cext.unread_result
        self.assertFalse(unread_result, "unread_rows was not set to False")
        # Query execution must not raise InternalError: Unread result found
        self.cnx_cext.cmd_query(self.test_sql_single_result)
        _ = self.cnx_cext.get_rows()

        # Test cursor fetchall
        cur_cext = self.cnx_cext.cursor()
        cur_cext.execute(self.test_sql_single_result)
        unread_result = self.cnx_cext.unread_result
        self.assertTrue(unread_result, "unread_rows is expected to be True")
        _ = cur_cext.fetchall()
        unread_result = self.cnx_cext.unread_result
        self.assertFalse(unread_result, "unread_rows was not set to False")
        # Query execution must not raise InternalError: Unread result found
        cur_cext.execute(self.test_sql_single_result)
        _ = cur_cext.fetchall()

        cur_cext.close()


@unittest.skipIf(
    tests.MYSQL_VERSION < (8, 0, 1),
    "Collation utf8mb4_0900_ai_ci not available on 5.7.x",
)
class BugOra27277964(tests.MySQLConnectorTests):
    """BUG#27277964: NEW UTF8MB4 COLLATIONS NOT SUPPORTED"""

    def setUp(self):
        config = tests.get_mysql_config()
        config["charset"] = "utf8mb4"
        config["collation"] = "utf8mb4_0900_ai_ci"
        self.tbl = "BugOra27277964"
        self.cnx = connection.MySQLConnection(**config)
        self.cur = self.cnx.cursor()
        self.cur.execute(f"DROP TABLE IF EXISTS {self.tbl}")
        self.cur.execute(
            f"CREATE TABLE {self.tbl} (id INT PRIMARY KEY, name VARCHAR(100))"
        )

    def tearDown(self):
        self.cur.execute(f"DROP TABLE IF EXISTS {self.tbl}")
        self.cur.close()

    def test_execute_utf8mb4_collation(self):
        self.cur.execute(f"INSERT INTO {self.tbl} VALUES (1, 'Nuno')")


@unittest.skipIf(
    tests.MYSQL_VERSION < (8, 0, 11),
    "Not support for TLSv1.2 or not available by default",
)
class Bug26484601(tests.MySQLConnectorTests):
    """UNABLE TO CONNECT TO A MYSQL SERVER USING TLSV1.2"""

    def try_connect(self, tls_version, expected_ssl_version):
        config = tests.get_mysql_config().copy()
        config["tls_versions"] = tls_version
        config["ssl_ca"] = ""
        if "unix_socket" in config:
            del config["unix_socket"]
        cnx = connection.MySQLConnection(**config)
        query = "SHOW STATUS LIKE 'ssl_version%'"
        cur = cnx.cursor()
        cur.execute(query)
        res = cur.fetchall()

        if isinstance(expected_ssl_version, tuple):
            msg = (
                "Not using the expected or greater TLS version: {}, instead"
                " the connection used: {}."
            )
            # Get the version as tuple
            server_tls = tuple([int(d) for d in (res[0][1].split("v")[1].split("."))])
            self.assertGreaterEqual(
                server_tls,
                expected_ssl_version,
                msg.format(expected_ssl_version, res),
            )
        else:
            msg = (
                "Not using the expected TLS version: {}, instead the "
                "connection used: {}."
            )
            self.assertEqual(
                res[0][1],
                expected_ssl_version,
                msg.format(expected_ssl_version, res),
            )

    def test_get_connection_using_given_TLS_version(self):
        """Test connect using the given TLS version

        The system variable tls_version determines which protocols the
        server is permitted to use from those that are available (note#3).
        +---------------+-----------------------+
        | Variable_name | Value                 |
        +---------------+-----------------------+
        | tls_version   | TLSv1,TLSv1.1,TLSv1.2 |
        +---------------+-----------------------+

        To restrict and permit only connections with a specific version, the
        variable can be set with those specific versions that will be allowed,
        changing the configuration file.

        [mysqld]
        tls_version=TLSv1.1,TLSv1.2

        This test will take adventage of the fact that the connector can
        request to use a defined version of TLS to test that the connector can
        connect to the server using such version instead of changing the
        configuration of the server that will imply the stoping and restarting
        of the server incrementing the time to run the test. In addition the
        test relay in the default value of the 'tls_version' variable is set to
        'TLSv1,TLSv1.1,TLSv1.2' (note#2).

        On this test a connection will be
        attempted forcing to use a determined version of TLS, (all of them
        must be successfully) finally making sure that the connection was done
        using the given TLS_version using the ssl.version() method (note#3).

        Notes:
        1.- tls_version is only available on MySQL 5.7
        2.- 5.6.39 does not support TLSv1.2 so for test will be skip. Currently
            in 5.7.21 is set to default values TLSv1,TLSv1.1,TLSv1.2 same as in
            8.0.11+. This test will be only run in such versions and above.
        3.- The ssl.version() method returns the version of tls used in during
            the connection, however the version returned using ssl.cipher() is
            not correct on windows, only indicates the newer version supported.

        """
        test_tls_versions = check_tls_versions_support(["TLSv1.1", "TLSv1.2"])
        if not test_tls_versions:
            self.fail("No TLS version to test: {}".format(test_tls_versions))
        for tls_v_name in test_tls_versions:
            self.try_connect([tls_v_name], tls_v_name)

    def test_get_connection_using_servers_TLS_version(self):
        """Test connect using the servers default TLS version

        The TLS version used during the secured connection is chosen by the
        server at the time the ssl handshake is made if the connector does not
        specifies any specific version to use. The default value of the
        ssl_version is None, however this only mean to the connector that none
        specific version will be chosen by the server when the ssl handshake
        occurs.
        """
        # The default value for the connector 'ssl_version' is None
        # For the expected version, the server will use the latest version of
        # TLS available "TLSv1.2" or newer.
        tls_version = None
        self.try_connect(tls_version, (1, 2))


@unittest.skipIf(not CMySQLConnection, ERR_NO_CEXT)
class BugOra27650437(tests.MySQLConnectorTests):
    """BUG#27650437: DIFFERENCES PYTHON AND C-EXT FOR GET_ROW()/GET_ROWS()"""

    test_sql_single_result = "show variables like '%port%'"
    cnx_pure = None
    cnx_cext = None
    cnx_pure_raw = None
    cnx_cext_raw = None

    def setUp(self):
        config_pure = tests.get_mysql_config()
        config_pure["use_pure"] = True
        self.cnx_pure = mysql.connector.connect(**config_pure)

        config_cext = tests.get_mysql_config()
        config_cext["use_pure"] = False
        self.cnx_cext = mysql.connector.connect(**config_cext)

        config_pure_raw = tests.get_mysql_config()
        config_pure_raw["use_pure"] = True
        config_pure_raw["raw"] = True
        self.cnx_pure_raw = mysql.connector.connect(**config_pure_raw)

        config_cext_raw = tests.get_mysql_config()
        config_cext_raw["use_pure"] = False
        config_cext_raw["raw"] = True
        self.cnx_cext_raw = mysql.connector.connect(**config_cext_raw)

    def tearDown(self):
        self.cnx_pure.close()
        self.cnx_cext.close()
        self.cnx_pure_raw.close()
        self.cnx_cext_raw.close()

    def test_get_row(self):
        """Test result from get_row is the same in pure and using c-ext"""
        self.cnx_pure.cmd_query(self.test_sql_single_result)
        res_pure = self.cnx_pure.get_row()

        self.cnx_cext.cmd_query(self.test_sql_single_result)
        res_cext = self.cnx_cext.get_row()

        self.assertEqual(
            res_pure,
            res_cext,
            "Result using pure: {} differs"
            "from c-ext result {}".format(res_pure, res_cext),
        )

    def test_get_rows(self):
        """Test results from get_rows are the same in pure and using c-ext"""
        self.cnx_pure.cmd_query(self.test_sql_single_result)
        res_pure = self.cnx_pure.get_rows()

        self.cnx_cext.cmd_query(self.test_sql_single_result)
        res_cext = self.cnx_cext.get_rows()

        self.assertEqual(
            res_pure,
            res_cext,
            "Result using pure: {} differs"
            "from c-ext result {}".format(res_pure, res_cext),
        )

    def test_get_row_raw(self):
        """Test result from get_row is the same in pure and using c-ext"""
        self.cnx_pure_raw.cmd_query(self.test_sql_single_result)
        res_pure = self.cnx_pure_raw.get_row()

        self.cnx_cext_raw.cmd_query(self.test_sql_single_result)
        res_cext = self.cnx_cext_raw.get_row()

        self.assertEqual(
            res_pure,
            res_cext,
            "Result using pure: {} differs"
            "from c-ext result {}".format(res_pure, res_cext),
        )

    def test_get_rows_raw(self):
        """Test results from get_rows are the same in pure and using c-ext"""
        self.cnx_pure_raw.cmd_query(self.test_sql_single_result)
        res_pure = self.cnx_pure_raw.get_rows()

        self.cnx_cext_raw.cmd_query(self.test_sql_single_result)
        res_cext = self.cnx_cext_raw.get_rows()

        self.assertEqual(
            res_pure,
            res_cext,
            "Result using pure: {} differs"
            "from c-ext result {}".format(res_pure, res_cext),
        )

    def _test_fetchone(self, cur_pure, cur_cext):
        """Test result from fetchone is the same in pure and using c-ext"""
        cur_pure.execute(self.test_sql_single_result)
        res_pure = cur_pure.fetchone()
        _ = cur_pure.fetchall()

        cur_cext.execute(self.test_sql_single_result)
        res_cext = cur_cext.fetchone()
        _ = cur_cext.fetchall()
        self.cnx_cext.free_result()

        self.assertEqual(
            res_pure,
            res_cext,
            "Result using pure: {} differs"
            "from c-ext result {}".format(res_pure, res_cext),
        )

    def _test_fetchmany(self, cur_pure, cur_cext):
        """Test results from fetchmany are the same in pure and using c-ext"""
        cur_pure.execute(self.test_sql_single_result)
        res_pure = cur_pure.fetchmany()

        cur_cext.execute(self.test_sql_single_result)
        res_cext = cur_cext.fetchmany()

        self.assertEqual(
            res_pure,
            res_cext,
            "Result using pure: {} differs"
            "from c-ext result {}".format(res_pure, res_cext),
        )

        res_pure = cur_pure.fetchmany(2)
        res_cext = cur_cext.fetchmany(2)

        _ = cur_pure.fetchall()
        _ = cur_cext.fetchall()
        self.cnx_cext.free_result()

        self.assertEqual(
            res_pure,
            res_cext,
            "Result using pure: {} differs"
            "from c-ext result {}".format(res_pure, res_cext),
        )

    def _test_fetch_fetchall(self, cur_pure, cur_cext):
        """Test results from fetchall are the same in pure and using c-ext"""
        cur_pure.execute(self.test_sql_single_result)
        res_pure = cur_pure.fetchall()

        cur_cext.execute(self.test_sql_single_result)
        res_cext = cur_cext.fetchall()

        self.cnx_cext.free_result()

        self.assertEqual(
            res_pure,
            res_cext,
            "Result using pure: {} differs"
            "from c-ext result {}".format(res_pure, res_cext),
        )

    def test_cursor(self):
        """Test results from cursor are the same in pure and using c-ext"""
        cur_pure = self.cnx_pure.cursor()
        cur_cext = self.cnx_cext.cursor()
        self._test_fetchone(cur_pure, cur_cext)
        self._test_fetchmany(cur_pure, cur_cext)
        self._test_fetch_fetchall(cur_pure, cur_cext)
        cur_pure.close()
        cur_cext.close()

    def test_cursor_raw(self):
        """Test results from cursor raw are the same in pure and using c-ext"""
        raw = True
        cur_pure_raw = self.cnx_pure.cursor(raw=raw)
        cur_cext_raw = self.cnx_cext.cursor(raw=raw)
        self._test_fetchone(cur_pure_raw, cur_cext_raw)
        self._test_fetchmany(cur_pure_raw, cur_cext_raw)
        self._test_fetch_fetchall(cur_pure_raw, cur_cext_raw)
        cur_pure_raw.close()
        cur_cext_raw.close()

    def test_cursor_buffered(self):
        """Test results from cursor buffered are the same in pure or c-ext"""
        buffered = True
        cur_pure_buffered = self.cnx_pure.cursor(buffered=buffered)
        cur_cext_buffered = self.cnx_cext.cursor(buffered=buffered)
        self._test_fetchone(cur_pure_buffered, cur_cext_buffered)
        self._test_fetchmany(cur_pure_buffered, cur_cext_buffered)
        self._test_fetch_fetchall(cur_pure_buffered, cur_cext_buffered)
        cur_pure_buffered.close()
        cur_cext_buffered.close()

    def test_cursor_dictionary(self):
        """Test results from cursor buffered are the same in pure or c-ext"""
        cur_pure_dictionary = self.cnx_pure.cursor(dictionary=True)
        cur_cext_dictionary = self.cnx_cext.cursor(dictionary=True)
        self._test_fetchone(cur_pure_dictionary, cur_cext_dictionary)
        self._test_fetchmany(cur_pure_dictionary, cur_cext_dictionary)
        self._test_fetch_fetchall(cur_pure_dictionary, cur_cext_dictionary)
        cur_pure_dictionary.close()
        cur_cext_dictionary.close()

    def test_cursor_dictionary_buf(self):
        """Test results from cursor buffered are the same in pure or c-ext"""
        cur_pure = self.cnx_pure.cursor(dictionary=True, buffered=True)
        cur_cext = self.cnx_cext.cursor(dictionary=True, buffered=True)
        self._test_fetchone(cur_pure, cur_cext)
        self._test_fetchmany(cur_pure, cur_cext)
        self._test_fetch_fetchall(cur_pure, cur_cext)
        cur_pure.close()
        cur_cext.close()


class BugOra28239074(tests.MySQLConnectorTests):
    """BUG#28239074: CURSOR DICTIONARY DOES NOT RETURN DICTIONARY TYPE RESULTS"""

    table = "bug28239074"

    def setUp(self):
        config_pure = tests.get_mysql_config()
        config_pure["use_pure"] = True
        self.cnx = mysql.connector.connect(**config_pure)
        cur = self.cnx.cursor(dictionary=True)

        cur.execute("DROP TABLE IF EXISTS {0}".format(self.table))
        cur.execute(
            "CREATE TABLE {0}(a char(50) ,b int PRIMARY KEY) "
            "DEFAULT CHARSET utf8".format(self.table)
        )
        data = [
            (chr(1), 1),
            ("s", 2),
            (chr(120), 3),
            (chr(121), 4),
            (chr(127), 5),
        ]
        cur.executemany(
            "INSERT INTO {0} (a, b) VALUES (%s, %s)".format(self.table),
            data,
        )

    def tearDown(self):
        self.cnx.cmd_query("DROP TABLE IF EXISTS {}".format(self.table))
        self.cnx.close()

    def test_cursor_dict(self):
        exp = [
            {"a": "\x01", "b": 1},
            {"a": "s", "b": 2},
            {"a": "\x78", "b": 3},
            {"a": "\x79", "b": 4},
            {"a": "\x7f", "b": 5},
        ]
        cur = self.cnx.cursor(dictionary=True)

        # Test fetchone
        cur.execute("SELECT * FROM {}".format(self.table))
        i = 0
        row = cur.fetchone()
        while row is not None:
            self.assertTrue(isinstance(row, dict))
            self.assertEqual(
                exp[i],
                row,
                "row {} is not equal to expected row {}".format(row, exp[i]),
            )
            row = cur.fetchone()
            i += 1

        # Test fetchall
        cur.execute("SELECT * FROM {}".format(self.table))
        rows = cur.fetchall()
        self.assertEqual(exp, rows, "rows {} is not equal to expected row")

        # Test for each in cursor
        cur.execute("SELECT * FROM {}".format(self.table))
        i = 0
        for row in cur:
            self.assertTrue(isinstance(row, dict))
            self.assertEqual(
                exp[i],
                row,
                "row {} is not equal to expected row {}".format(row, exp[i]),
            )
            i += 1


class BugOra27364914(tests.MySQLConnectorTests):
    """BUG#27364914: CURSOR PREPARED STATEMENTS DO NOT CONVERT STRINGS"""

    charsets_list = ("gbk", "sjis", "big5", "utf8", "utf8mb4", "latin1")

    def setUp(self):
        cnx = connection.MySQLConnection(**tests.get_mysql_config())
        cur = cnx.cursor(cursor_class=cursor.MySQLCursorPrepared)

        for charset in self.charsets_list:
            tablename = "{0}_ps_test".format(charset)
            cur.execute("DROP TABLE IF EXISTS {0}".format(tablename))
            table = (
                "CREATE TABLE {table} ("
                "  id INT AUTO_INCREMENT KEY,"
                "  c1 VARCHAR(40),"
                "  val2 datetime"
                ") CHARACTER SET '{charset}'"
            ).format(table=tablename, charset=charset)
            cur.execute(table)
            cnx.commit()
        cur.close()
        cnx.close()

    def tearDown(self):
        cnx = connection.MySQLConnection(**tests.get_mysql_config())
        for charset in self.charsets_list:
            tablename = "{0}_ps_test".format(charset)
            cnx.cmd_query("DROP TABLE IF EXISTS {0}".format(tablename))
        cnx.close()

    def _test_charset(self, charset, data):
        config = tests.get_mysql_config()
        config["charset"] = charset
        config["use_unicode"] = True
        self.cnx = connection.MySQLConnection(**tests.get_mysql_config())
        cur = self.cnx.cursor(cursor_class=cursor.MySQLCursorPrepared)

        tablename = "{0}_ps_test".format(charset)
        cur.execute("TRUNCATE {0}".format(tablename))
        self.cnx.commit()

        insert = "INSERT INTO {0} (c1) VALUES (%s)".format(tablename)
        for value in data:
            cur.execute(insert, (value,))
        self.cnx.commit()

        cur.execute("SELECT id, c1 FROM {0} ORDER BY id".format(tablename))
        for row in cur.fetchall():
            self.assertTrue(
                isinstance(row[1], str), "The value is expected to be a string"
            )
            self.assertEqual(data[row[0] - 1], row[1])

        cur.close()
        self.cnx.close()

    @foreach_cnx()
    def test_cursor_prepared_statement_with_charset_gbk(self):
        self._test_charset("gbk", ["赵孟頫", "赵\孟\頫\\", "遜"])

    @foreach_cnx()
    def test_cursor_prepared_statement_with_charset_sjis(self):
        self._test_charset("sjis", ["\u005c"])

    @foreach_cnx()
    def test_cursor_prepared_statement_with_charset_big5(self):
        self._test_charset("big5", ["\u5C62"])

    @foreach_cnx()
    def test_cursor_prepared_statement_with_charset_utf8mb4(self):
        self._test_charset("utf8mb4", ["\u5C62"])

    @foreach_cnx()
    def test_cursor_prepared_statement_with_charset_utf8(self):
        self._test_charset("utf8", ["データベース", "데이터베이스"])

    @foreach_cnx()
    def test_cursor_prepared_statement_with_charset_latin1(self):
        self._test_charset("latin1", ["ñ", "Ñ"])


class BugOra27802700(tests.MySQLConnectorTests):
    """BUG#27802700: A BYTEARRAY IS RETURNED FROM USING get_rows METHOD"""

    table_name = "BugOra27802700"
    insert_stmt = "INSERT INTO {} ({}) values ({{value}})"

    def setUp(self):
        config = tests.get_mysql_config()
        config["charset"] = "utf8"
        config["use_unicode"] = True
        cnx = connection.MySQLConnection(**config)
        cur = cnx.cursor()
        cur.execute("DROP TABLE IF EXISTS {}".format(self.table_name))
        cur.execute(
            "CREATE TABLE IF NOT EXISTS {} ("
            "  id INT(11) UNSIGNED AUTO_INCREMENT UNIQUE KEY,"
            "  int_long INT,"
            "  time TIME,"
            "  date DATE,"
            "  datetime DATETIME,"
            "  var_char VARCHAR(50),"
            "  long_blob LONGBLOB,"
            "  str TEXT) CHARACTER SET utf8"
            "  COLLATE utf8_general_ci".format(self.table_name)
        )

    def tearDown(self):
        config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**config)
        cur = cnx.cursor()
        try:
            cur.execute("DROP TABLE IF EXISTS {}".format(self.table_name))
        except:
            pass

    def run_test_retrieve_stored_type(
        self, stm, test_values, expected_values, column, expected_type
    ):
        config = tests.get_mysql_config()
        config["charset"] = "utf8"
        config["use_unicode"] = True
        config["autocommit"] = True
        cnx = connection.MySQLConnection(**config)
        cur = cnx.cursor()

        for test_value in test_values:
            cnx.cmd_query(stm.format(value=test_value))

        qry = "SELECT {column} FROM {table} ORDER BY id"
        cur.execute(qry.format(column=column, table=self.table_name))

        rows = cnx.get_rows()[0][len(test_values) * (-1) :]
        for returned_val, expected_value in zip(rows, expected_values):
            self.assertEqual(returned_val[0], expected_value)
            self.assertTrue(isinstance(returned_val[0], expected_type))

        cur.close()
        cnx.close()

    @foreach_cnx()
    def test_retrieve_stored_int_long(self):
        column = "int_long"
        stm = self.insert_stmt.format(self.table_name, column)
        test_values = ["-12345", "0", "12345"]
        expected_values = [-12345, 0, 12345]

        expected_type = int
        self.run_test_retrieve_stored_type(
            stm, test_values, expected_values, column, expected_type
        )

    @foreach_cnx()
    def test_retrieve_stored_str(self):
        column = "str"
        stm = self.insert_stmt.format(self.table_name, column)
        test_values = ["' '", "'some text'", "'データベース'", "'\"12345\"'"]
        expected_values = [" ", "some text", "データベース", '"12345"']
        expected_type = str

        self.run_test_retrieve_stored_type(
            stm, test_values, expected_values, column, expected_type
        )

    @foreach_cnx()
    def test_retrieve_stored_blob(self):
        column = "long_blob"
        stm = self.insert_stmt.format(self.table_name, column)
        test_values = ["' '", "'some text'", "'データベース'", "\"'12345'\""]
        expected_values = [
            b" ",
            b"some text",
            "データベース".encode("utf-8"),
            b"'12345'",
        ]
        expected_type = bytes

        self.run_test_retrieve_stored_type(
            stm, test_values, expected_values, column, expected_type
        )

    @foreach_cnx()
    def test_retrieve_stored_varchar(self):
        column = "var_char"
        stm = self.insert_stmt.format(self.table_name, column)
        test_values = ["' '", "'some text'", "'データベース'", "'12345'"]
        expected_values = [" ", "some text", "データベース", "12345"]
        expected_type = str

        self.run_test_retrieve_stored_type(
            stm, test_values, expected_values, column, expected_type
        )

    @foreach_cnx()
    def test_retrieve_stored_datetime_types(self):
        column = "datetime"
        stm = self.insert_stmt.format(self.table_name, column)
        test_values = [
            "cast('1972-01-01 00:42:49.000000' as DATETIME)",
            "cast('2018-01-01 23:59:59.000000' as DATETIME)",
        ]
        expected_values = [
            datetime(1972, 1, 1, 0, 42, 49),
            datetime(2018, 1, 1, 23, 59, 59),
        ]

        expected_type = datetime
        self.run_test_retrieve_stored_type(
            stm, test_values, expected_values, column, expected_type
        )

    @foreach_cnx()
    def test_retrieve_stored_date_types(self):
        column = "date"
        stm = self.insert_stmt.format(self.table_name, column)
        test_values = ["DATE('1972-01-01')", "DATE('2018-12-31')"]
        expected_values = [date(1972, 1, 1), date(2018, 12, 31)]

        expected_type = date
        self.run_test_retrieve_stored_type(
            stm, test_values, expected_values, column, expected_type
        )

    @foreach_cnx()
    def test_retrieve_stored_time_types(self):
        column = "time"
        stm = self.insert_stmt.format(self.table_name, column)
        test_values = ["TIME('00:42:49.00000')", "TIME('23:59:59.00000')"]
        expected_values = [
            timedelta(hours=0, minutes=42, seconds=49),
            timedelta(hours=23, minutes=59, seconds=59),
        ]
        expected_type = timedelta
        self.run_test_retrieve_stored_type(
            stm, test_values, expected_values, column, expected_type
        )


class BugOra27277937(tests.MySQLConnectorTests):
    """BUG#27277937: CONFUSING ERROR MESSAGE WHEN SPECIFYING UNSUPPORTED
    COLLATION
    """

    def setUp(self):
        pass

    def test_invalid_collation(self):
        config = tests.get_mysql_config()
        config["charset"] = "utf8"
        config["collation"] = "foobar"
        self.cnx = connection.MySQLConnection()
        try:
            self.cnx.connect(**config)
        except errors.ProgrammingError as err:
            self.assertEqual(err.msg, "Collation 'foobar' unknown")
        else:
            self.fail("A ProgrammingError was expected")

    def tearDown(self):
        pass


class BugOra28188883(tests.MySQLConnectorTests):
    """BUG#27277937: DEPRECATED UTF8 IS THE DEFAULT CHARACTER SET IN 8.0"""

    def setUp(self):
        # Remove charset from the connection configuration if is set, so the
        # default charset 'utf8mb4' is used for each connection
        self.config = tests.get_mysql_config().copy()
        if "charset" in self.config:
            del self.config

    @foreach_cnx()
    def test_utf8mb4_default_charset(self):
        self.assertEqual(self.cnx.charset, "utf8mb4")
        data = [(1, "🐬"), (2, "🐍"), (3, "🐶")]
        tbl = "BugOra28188883"
        cur = self.cnx.cursor()
        cur.execute(f"DROP TABLE IF EXISTS {tbl}")
        cur.execute(
            f"""
            CREATE TABLE {tbl} (id INT PRIMARY KEY, name VARCHAR(100))
            DEFAULT CHARSET utf8mb4
            """
        )
        stmt = f"INSERT INTO {tbl} (id, name) VALUES (%s, %s)"
        cur.executemany(stmt, data)
        cur.execute(f"SELECT id, name FROM {tbl}")
        self.assertEqual(data, cur.fetchall())
        cur.execute(f"DROP TABLE IF EXISTS {tbl}")
        cur.close()
        self.cnx.close()


@unittest.skipIf(
    tests.MYSQL_EXTERNAL_SERVER,
    "Test not available for external MySQL servers",
)
@unittest.skipIf(
    tests.MYSQL_VERSION < (5, 7, 23),
    "MySQL 5.7.23+ is required for VERIFY_IDENTITY",
)
class BugOra27434751(tests.MySQLConnectorTests):
    """BUG#27434751: MYSQL.CONNECTOR HAS NO TLS/SSL OPTION TO VERIFY SERVER NAME"""

    def setUp(self):
        ssl_ca = os.path.abspath(os.path.join(tests.SSL_DIR, "tests_CA_cert.pem"))
        ssl_cert = os.path.abspath(os.path.join(tests.SSL_DIR, "tests_client_cert.pem"))
        ssl_key = os.path.abspath(os.path.join(tests.SSL_DIR, "tests_client_key.pem"))
        self.config = tests.get_mysql_config()
        self.config.pop("unix_socket")
        self.config["ssl_ca"] = ssl_ca
        self.config["ssl_cert"] = ssl_cert
        self.config["ssl_key"] = ssl_key
        self.config["ssl_verify_cert"] = True

    def _verify_server_name_cnx(self, use_pure=True):
        config = self.config.copy()
        config["use_pure"] = use_pure
        # Setting an invalid host name against a server certificate
        config["host"] = "127.0.0.1"

        # Should connect with ssl_verify_identity=False
        config["ssl_verify_identity"] = False
        cnx = mysql.connector.connect(**config)
        cnx.close()

        # Should fail to connect with ssl_verify_identity=True
        config["ssl_verify_identity"] = True
        self.assertRaises(errors.InterfaceError, mysql.connector.connect, **config)

        # Should connect with the correct host name and ssl_verify_identity=True
        config["host"] = "localhost"
        cnx = mysql.connector.connect(**config)
        cnx.close()

    @unittest.skipIf(not CMySQLConnection, ERR_NO_CEXT)
    def test_verify_server_name_cext_cnx(self):
        self._verify_server_name_cnx(use_pure=False)

    def test_verify_server_name_pure_cnx(self):
        self._verify_server_name_cnx(use_pure=True)


@unittest.skipIf(CMySQLConnection, "Test only available without C Extension")
class BugOra27794178(tests.MySQLConnectorTests):
    """BUG#27794178: USING USE_PURE=FALSE SHOULD RAISE AN ERROR WHEN CEXT IS NOT
    AVAILABLE
    """

    def test_connection_use_pure(self):
        config = tests.get_mysql_config().copy()
        if "use_pure" in config:
            del config["use_pure"]
        cnx = mysql.connector.connect(**config)
        cnx.close()

        # Force using C Extension should fail if not available
        config["use_pure"] = False
        self.assertRaises(ImportError, mysql.connector.connect, **config)


class Bug27897881(tests.MySQLConnectorTests):
    """BUG#27897881: Fix typo in BLOB data conversion"""

    def setUp(self):
        self.config = tests.get_mysql_config()
        cnx = connection.MySQLConnection(**self.config)
        cursor = cnx.cursor()

        self.tbl = "Bug27897881"
        cursor.execute("DROP TABLE IF EXISTS %s" % self.tbl)

        create = (
            "CREATE TABLE {0}(col1 INT NOT NULL, col2 LONGBLOB, "
            "PRIMARY KEY(col1))".format(self.tbl)
        )

        cursor.execute(create)
        cursor.close()
        cnx.close()

    def tearDown(self):
        cnx = connection.MySQLConnection(**self.config)
        cursor = cnx.cursor()
        cursor.execute("DROP TABLE IF EXISTS {}".format(self.tbl))
        cursor.close()
        cnx.close()

    @foreach_cnx()
    def test_retrieve_from_LONGBLOB(self):
        cnx_config = self.config.copy()
        cnx_config["charset"] = "utf8"
        cnx_config["use_unicode"] = True
        cnx = connection.MySQLConnection(**cnx_config)
        cur = cnx.cursor()

        # Empty blob produces index error.
        # "12345" handle as datetime in JSON produced index error.
        # LONGBLOB can store big data
        test_values = ["", "12345", '"54321"', "A" * (2**20)]
        expected_values = [b"", b"12345", b'"54321"', b"A" * (2**20)]
        stm = "INSERT INTO {} (col1, col2) VALUES ('{}', '{}')"

        for num, test_value in zip(range(len(test_values)), test_values):
            cur.execute(stm.format(self.tbl, num, test_value))

        stm = "SELECT * FROM {} WHERE col1 like '{}'"

        for num, expected_value in zip(range(len(test_values)), expected_values):
            cur.execute(stm.format(self.tbl, num))
            row = cur.fetchall()[0]
            self.assertEqual(
                row[1],
                expected_value,
                "value {} is not the expected {}".format(row[1], expected_value),
            )

        cur.close()
        cnx.close()


class BugOra29324966(tests.MySQLConnectorTests):
    """BUG#29324966: ADD MISSING USERNAME CONNECTION ARGUMENT FOR DRIVER
    COMPATIBILITY.
    """

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @foreach_cnx()
    def test_connection_args_compatibility(self):
        config = self.config.copy()
        config["username"] = config["user"]
        config["passwd"] = config["password"]
        config["db"] = config["database"]
        config["connect_timeout"] = config["connection_timeout"]

        config.pop("user")
        config.pop("password")
        config.pop("database")
        config.pop("connection_timeout")

        cnx = self.cnx.__class__(**config)
        cnx.close()


class Bug20811567(tests.MySQLConnectorTests):
    """BUG#20811567: Support use_pure option in config files."""

    def write_config_file(self, use_pure, test_file):
        temp_cnf_file = os.path.join(os.getcwd(), test_file)
        with open(temp_cnf_file, "w") as cnf_file:
            config = tests.get_mysql_config()
            config["use_pure"] = use_pure
            cnf = "[connector_python]\n"
            cnf += "\n".join(
                ["{0} = {1}".format(key, value) for key, value in config.items()]
            )
            cnf_file.write(cnf)

    @foreach_cnx()
    def test_support_use_pure_option_in_config_files(self):
        if self.cnx.__class__ == CMySQLConnection:
            temp_cnf_file = "temp_cnf_file_not_pure.cnf"
            use_pure = False
        else:
            temp_cnf_file = "temp_cnf_file_use_pure.cnf"
            use_pure = True
        # Prepare config file.
        self.write_config_file(use_pure, temp_cnf_file)
        # Get connection
        with mysql.connector.connect(option_files=temp_cnf_file) as cnx:
            self.assertEqual(self.cnx.__class__, cnx.__class__)
        # Remove config file
        os.remove(temp_cnf_file)


@unittest.skipIf(
    tests.MYSQL_VERSION < (8, 0, 17),
    "MySQL 8.0.17+ is required for utf8mb4_0900_bin collation",
)
class BugOra29855733(tests.MySQLConnectorTests):
    """BUG#29855733: ERROR DURING THE CLASSIC CONNECTION WITH CHARSET AND
    COLLATION SPECIFIED.
    """

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @foreach_cnx()
    def test_connection_collation_utf8mb4_0900_bin(self):
        config = self.config.copy()
        config["username"] = config["user"]
        config["passwd"] = config["password"]
        config["charset"] = "utf8mb4"
        config["collation"] = "utf8mb4_0900_bin"

        cnx = self.cnx.__class__(**config)
        cnx.close()


@unittest.skipIf(
    tests.MYSQL_VERSION <= (5, 7, 2),
    "Pool not supported with with MySQL version 5.6",
)
class BugOra25349794(tests.MySQLConnectorTests):
    """BUG#25349794: ADD READ_DEFAULT_FILE ARGUMENT FOR CONNECT()."""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @foreach_cnx()
    def test_read_default_file_alias(self):
        opt_file = os.path.join("tests", "data", "option_files", "pool.cnf")
        config = tests.get_mysql_config()

        if tests.MYSQL_VERSION < (5, 7):
            config["client_flags"] = [-constants.ClientFlag.CONNECT_ARGS]

        conn = mysql.connector.connect(
            read_default_file=opt_file, option_groups=["pooling"], **config
        )
        self.assertEqual("my_pool", conn.pool_name)
        mysql.connector.pooling._CONNECTION_POOLS = {}
        conn.close()


class Bug27358941(tests.MySQLConnectorTests):
    """BUG#27358941: INVALID TYPES FOR PARAMS SILENTLY IGNORED IN EXECUTE()"""

    @foreach_cnx()
    def test_invalid_types_not_get_ignored(self):
        test_cases = (123, 123.456, "456.789")

        for prepared in [False, True]:
            cursor = self.cnx.cursor(prepared=prepared)
            for params in test_cases:
                with self.assertRaises(errors.ProgrammingError) as contex:
                    cursor.execute("SELECT %s", params)
                self.assertIn(
                    f"{type(params).__name__}({params}), it must be of type",
                    contex.exception.msg,
                )

            with self.assertRaises(errors.ProgrammingError) as contex:
                cursor.executemany("SELECT %s", test_cases)
            self.assertIn("it must be of type", contex.exception.msg)


class Bug33486094(tests.MySQLConnectorTests):
    """BUG#33486094: Stored value in Decimal field returned as str instead of Decimal"""

    def setUp(self):
        self.config = tests.get_mysql_config()
        self.tbl = "Bug33486094"
        with connection.MySQLConnection(**self.config) as cnx:
            with cnx.cursor() as cursor:
                cursor.execute("DROP TABLE IF EXISTS %s" % self.tbl)

                create = f"""CREATE TABLE {self.tbl} (
                            col1 INT NOT NULL AUTO_INCREMENT,
                            decimals_def DECIMAL,
                            decimals_10 DECIMAL (10),
                            decimals_5_2 DECIMAL (5,2),
                            decimals_10_3 DECIMAL (10,3),
                            numerics NUMERIC(10,2),
                            PRIMARY KEY(col1)
                    )"""
                cursor.execute(create)

                self.test_cases = (
                    ("decimals_def", 1234567890),
                    ("decimals_10", 9999999999),
                    ("decimals_5_2", -999.99),
                    ("decimals_10_3", 123),
                    ("numerics", 12345678.90),
                )
                sql = f"INSERT INTO {self.tbl} ({{0}}) values ({{1}})"
                for col, value in self.test_cases:
                    cursor.execute(sql.format(col, value))
                cnx.commit()

    def tearDown(self):
        with connection.MySQLConnection(**self.config) as cnx:
            with cnx.cursor() as cursor:
                cursor.execute(f"DROP TABLE IF EXISTS {self.tbl}")

    @foreach_cnx()
    def test_decimal_column_returns_decimal_objects(self):
        for prepared in [False, True]:
            cursor = self.cnx.cursor(prepared=prepared)

            sql = f"select {{0}} from {self.tbl} where {{0}} IS NOT NULL"
            for col, value in self.test_cases:
                cursor.execute(sql.format(col))
                row = cursor.fetchall()[0]
                self.assertIsInstance(
                    row[0],
                    Decimal,
                    f"value: {row[0]} is not of Decimal type: "
                    f"{type(row[0]).__name__}",
                )
                self.assertAlmostEqual(
                    row[0],
                    Decimal(value),
                    3,
                    f"value: {row[0]} is not the expected: {value}",
                )


@unittest.skipIf(
    tests.MYSQL_EXTERNAL_SERVER,
    "Test not available for external MySQL servers",
)
@unittest.skipIf(tests.MYSQL_VERSION < (5, 7, 8), "No JSON support")
class BugOra29808262(tests.MySQLConnectorTests):
    """BUG#229808262: TEXT COLUMN WITH ONLY DIGITS READS IN AS INT."""

    table_name = "BugOra29808262"

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @foreach_cnx()
    def test_blob_fields(self):
        cur = self.cnx.cursor()
        cur.execute("DROP TABLE IF EXISTS {}".format(self.table_name))
        cur.execute(
            "CREATE TABLE {} ("
            "  my_blob BLOB,"
            "  my_longblob LONGBLOB,"
            "  my_json JSON,"
            "  my_text TEXT) CHARACTER SET utf8"
            "  COLLATE utf8_general_ci".format(self.table_name)
        )

        test_values = (
            "BLOB" * (2**10),
            "LONG_BLOB" * (2**20),
            '{"lat": "41.14961", "lon": "-8.61099", "name": "Porto"}',
            "My TEXT",
        )
        expected_values = (
            b"BLOB" * (2**10),
            b"LONG_BLOB" * (2**20),
            '{"lat": "41.14961", "lon": "-8.61099", "name": "Porto"}',
            "My TEXT",
        )
        cur = self.cnx.cursor()
        cur.execute(
            "INSERT INTO {} VALUES ('{}')"
            "".format(self.table_name, "', '".join(test_values))
        )
        cur.execute(
            "SELECT my_blob, my_longblob, my_json, my_text FROM {}"
            "".format(self.table_name)
        )
        res = cur.fetchall()
        self.assertEqual(res[0], expected_values)

        cur.execute("DROP TABLE IF EXISTS {}".format(self.table_name))
        cur.close()


class Bug27489937(tests.MySQLConnectorTests):
    """BUG#27489937: SUPPORT C EXTENSION FOR CONNECTION POOLS

    BUG#33203161: EXCEPTION IS THROWN ON CLOSE CONNECTION WITH POOLING
    """

    def _setUp(self, conn_class):
        self.config = tests.get_mysql_config()
        self.config["pool_name"] = "Bug27489937"
        self.config["pool_size"] = 3
        if self.cnx.__class__ == mysql.connector.connection.MySQLConnection:
            self.config["use_pure"] = True
        else:
            self.config["use_pure"] = False
        try:
            del mysql.connector.pooling._CONNECTION_POOLS[self.config["pool_name"]]
        except:
            pass

    def _tearDown(self):
        # Remove pools created by test
        del mysql.connector.pooling._CONNECTION_POOLS[self.config["pool_name"]]

    @foreach_cnx()
    def test_cext_pool_support(self):
        """Basic pool tests"""
        self._setUp(self.cnx.__class__)
        cnx_list = []
        session_ids = []
        for _ in range(self.config["pool_size"]):
            cnx = mysql.connector.connect(**self.config)
            self.assertIsInstance(
                cnx,
                PooledMySQLConnection,
                "Expected a CMySQLConnection instance",
            )
            self.assertIsInstance(
                cnx._cnx,
                self.cnx.__class__,
                f"Expected a {self.cnx.__class__} instance",
            )
            cnx_list.append(cnx)
            exp_session_id = cnx.connection_id
            session_ids.append(exp_session_id)
            cnx.cmd_query("SET @ham = 2")
            cnx.cmd_reset_connection()

            cnx.cmd_query("SELECT @ham")
            self.assertEqual(exp_session_id, cnx.connection_id)

            exp = (b"2",)
            self.assertNotEqual(exp, cnx.get_rows()[0][0])
        self.assertRaises(errors.PoolError, mysql.connector.connect, **self.config)

        for cnx in cnx_list:
            cnx.close()

        cnx = mysql.connector.connect(**self.config)
        cnx.cmd_query("SELECT @ham")
        self.assertIn(
            cnx.connection_id, session_ids, "Pooled connection was not reused."
        )

        exp = (b"2",)
        self.assertNotEqual(exp, cnx.get_rows()[0][0])
        self._tearDown()


class BugOra29195610(tests.MySQLConnectorTests):
    """BUG#29195610: CALLPROC() NOT SUPPORTED WITH NAMED TUPLE CURSOR AND FOR
    DICT CURSOR IS IGNORED
    """

    def setUp(self):
        config = tests.get_mysql_config()
        with connection.MySQLConnection(**config) as cnx:
            cnx.cmd_query("DROP TABLE IF EXISTS bug29195610")
            cnx.cmd_query("DROP PROCEDURE IF EXISTS sp_bug29195610")
            cnx.cmd_query(
                "CREATE TABLE bug29195610 (id INT PRIMARY KEY, name VARCHAR(5))"
            )
            cnx.cmd_query("INSERT INTO bug29195610 (id, name) VALUES (2020, 'Foo')")
            cnx.cmd_query(
                "CREATE PROCEDURE sp_bug29195610 (in_id INT) "
                "SELECT id, name FROM bug29195610 WHERE id = in_id;"
            )

    def tearDown(self):
        config = tests.get_mysql_config()
        with connection.MySQLConnection(**config) as cnx:
            cnx.cmd_query("DROP TABLE IF EXISTS bug29195610")
            cnx.cmd_query("DROP PROCEDURE IF EXISTS sp_bug29195610")

    @foreach_cnx()
    def test_callproc_cursor_types(self):
        cases = [
            ({}, [(2020, "Foo")]),
            ({"buffered": True}, [(2020, "Foo")]),
            ({"raw": True}, [(bytearray(b"2020"), bytearray(b"Foo"))]),
            (
                {"raw": True, "buffered": True},
                [(bytearray(b"2020"), bytearray(b"Foo"))],
            ),
            (
                {"raw": True, "buffered": True},
                [(bytearray(b"2020"), bytearray(b"Foo"))],
            ),
            ({"dictionary": True}, [{"id": 2020, "name": "Foo"}]),
            (
                {"dictionary": True, "buffered": True},
                [{"id": 2020, "name": "Foo"}],
            ),
        ]

        for cursor_type, exp in cases:
            with self.cnx.cursor(**cursor_type) as cur:
                cur.callproc("sp_bug29195610", (2020,))
                for res in cur.stored_results():
                    self.assertEqual(exp, res.fetchall())

        with self.cnx.cursor(prepared=True) as cur:
            self.assertRaises(
                errors.NotSupportedError,
                cur.callproc,
                "sp_bug29195610",
                (2020,),
            )


class BugOra24938411(tests.MySQLConnectorTests):
    """BUG#24938411: FIX MICROSECOND CONVERSION FROM MYSQL DATETIME TO PYTHON
    DATETIME.
    """

    @tests.foreach_cnx()
    def test_datetime_fractional(self):
        with self.cnx.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS bug24938411")
            cur.execute(
                "CREATE TABLE bug24938411 "
                "(id INT PRIMARY KEY, mydate datetime(3) DEFAULT NULL) ENGINE=InnoDB"
            )
            cur.execute(
                "INSERT INTO bug24938411 (id, mydate) "
                'VALUES (1, "2020-01-01 01:01:01.543")'
            )
            cur.execute(
                "SELECT mydate, CAST(mydate AS CHAR) AS mydate_char FROM bug24938411"
            )
            row = cur.fetchone()
            self.assertEqual(row[0], datetime(2020, 1, 1, 1, 1, 1, 543000))
            self.assertEqual(row[1], "2020-01-01 01:01:01.543")
            cur.execute("DROP TABLE IF EXISTS bug24938411")


class BugOra32165864(tests.MySQLConnectorTests):
    """BUG#32165864: SEGMENTATION FAULT WHEN TWO PREPARED STATEMENTS WITH
    INCORRECT SQL SYNTAX ARE EXECUTED CONSECUTIVELY.
    """

    @foreach_cnx()
    def test_segfault_prepared_statement(self):
        with self.cnx.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS bug32165864")
            cur.execute(
                "CREATE TABLE bug32165864 "
                "(id INT PRIMARY KEY, name VARCHAR(10), address VARCHAR(20))"
            )
            cur.execute(
                "INSERT INTO bug32165864 (id, name, address) VALUES "
                "(1, 'Joe', 'Street 1'), (2, 'John', 'Street 2')"
            )
            self.cnx.commit()

        stmt = "SELECT * FROM customer WHERE i = ? ?"

        with self.cnx.cursor(prepared=True) as cur:
            for _ in range(10):
                self.assertRaises(errors.Error, cur.execute, stmt, (10, "Gabriela"))

        with self.cnx.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS bug32165864")


class BugOra30416704(tests.MySQLConnectorTests):
    """BUG#30416704: BINARY COLUMNS RETURNED AS STRINGS."""

    table_name = "BugOra30416704"
    test_values = (
        "BLOB",
        '{"lat": "41.14961", "lon": "-8.61099", "name": "Porto"}',
        "My TEXT",
        "BIN",
    )
    exp_values = (
        b"BLOB",
        '{"lat": "41.14961", "lon": "-8.61099", "name": "Porto"}',
        "My TEXT",
        bytearray(b"BIN"),
    )

    exp_binary_values = (
        bytearray(b"BLOB"),
        bytearray(b'{"lat": "41.14961", "lon": "-8.61099", "name": "Porto"}'),
        bytearray(b"My TEXT"),
        bytearray(b"BIN"),
    )

    @classmethod
    def setUpClass(cls):
        config = tests.get_mysql_config()
        with mysql.connector.connection.MySQLConnection(**config) as cnx:
            cnx.cmd_query(f"DROP TABLE IF EXISTS {cls.table_name}")
            cnx.cmd_query(
                f"""
                CREATE TABLE {cls.table_name} (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    my_blob BLOB,
                    my_json JSON,
                    my_text TEXT,
                    my_binary BINARY(3)
                ) CHARACTER SET utf8 COLLATE utf8_general_ci
                """
            )
            values = "', '".join(cls.test_values)
            cnx.cmd_query(
                f"""
                INSERT INTO {cls.table_name}
                (my_blob, my_json, my_text, my_binary) VALUES ('{values}')
                """
            )
            cnx.commit()

    @classmethod
    def tearDownClass(cls):
        config = tests.get_mysql_config()
        with mysql.connector.connection.MySQLConnection(**config) as cnx:
            cnx.cmd_query(f"DROP TABLE IF EXISTS {cls.table_name}")

    def _test_result(self, cnx, exp_values, cursor=None, use_binary_charset=False):
        with cnx.cursor() as cur:
            cur = self.cnx.cursor(cursor)
            cur.execute(
                f"""
                SELECT my_blob, my_json, my_text, my_binary
                FROM {self.table_name}
                """
            )
            res = cur.fetchone()
            self.assertEqual(res, exp_values)

            cur.execute("SELECT BINARY 'ham'")
            res = cur.fetchone()
            self.assertEqual(res, (bytearray(b"ham"),))

    @foreach_cnx()
    def test_binary_columns(self):
        self._test_result(self.cnx, self.exp_values)

    @foreach_cnx()
    def test_binary_columns_cursor_prepared(self):
        self._test_result(
            self.cnx,
            self.exp_values,
            cursor=cursor.MySQLCursorPrepared,
        )

    @foreach_cnx()
    def test_binary_charset(self):
        self.cnx.set_charset_collation("binary")
        self._test_result(self.cnx, self.exp_binary_values, use_binary_charset=True)

    @foreach_cnx()
    def test_binary_charset_cursor_prepared(self):
        self.cnx.set_charset_collation("binary")
        self._test_result(
            self.cnx,
            self.exp_binary_values,
            cursor=cursor.MySQLCursorPrepared,
            use_binary_charset=True,
        )

    @foreach_cnx()
    def test_without_use_unicode(self):
        self.cnx.use_unicode = False
        self._test_result(self.cnx, self.exp_binary_values, use_binary_charset=True)

    @foreach_cnx()
    def test_without_use_unicode_cursor_prepared(self):
        self.cnx.use_unicode = False
        self._test_result(
            self.cnx,
            self.exp_binary_values,
            cursor=cursor.MySQLCursorPrepared,
            use_binary_charset=True,
        )


class Bug32496788(tests.MySQLConnectorTests):
    """BUG#32496788: PREPARED STATEMETS ACCEPTS ANY TYPE OF PARAMETERS."""

    table_name = "Bug32496788"
    test_values = ((1, "John", "", "Doe", 21, 77), [2, "Jane", "", "Doe", 19, 7])
    exp_values = ([(1, "John", "", "Doe", 21, 77)], [(2, "Jane", "", "Doe", 19, 7)])

    def setUp(self):
        config = tests.get_mysql_config()
        with mysql.connector.connection.MySQLConnection(**config) as cnx:
            cnx.cmd_query(f"DROP TABLE IF EXISTS {self.table_name}")
            cnx.cmd_query(
                f"""
                CREATE TABLE {self.table_name} (
                    id INT UNSIGNED NOT NULL AUTO_INCREMENT KEY,
                    column_first_name VARCHAR(30) DEFAULT '' NOT NULL,
                    column_midle_name VARCHAR(30) DEFAULT '' NOT NULL,
                    column_last_name VARCHAR(30) DEFAULT '' NOT NULL,
                    age INT DEFAULT 0 NOT NULL,
                    lucky_number INT DEFAULT 0 NOT NULL
                ) CHARACTER SET utf8 COLLATE utf8_general_ci
                """
            )
            cnx.commit()

    def tearDown(self):
        config = tests.get_mysql_config()
        with mysql.connector.connection.MySQLConnection(**config) as cnx:
            cnx.cmd_query(f"DROP TABLE IF EXISTS {self.table_name}")

    @foreach_cnx()
    def test_parameters_type(self):
        stmt = f"SELECT * FROM  {self.table_name} WHERE age = ? and lucky_number = ?"
        with self.cnx.cursor(prepared=True) as cur:
            # Test incorrect types must raise error
            for param in ["12", 12, 1.3, lambda: "1" + "2"]:
                self.assertRaises(errors.ProgrammingError, cur.execute, stmt, (param,))
                with self.assertRaises(errors.ProgrammingError) as contex:
                    cur.execute(stmt, param)
                self.assertIn(
                    f"Incorrect type of argument: {type(param).__name__}({param}),"
                    " it must be of type tuple or list",
                    contex.exception.msg,
                )

        with self.cnx.cursor(prepared=True) as cur:
            # Correct form with tuple
            cur.execute("SELECT ?, ?", ("1", "2"))
            self.assertEqual(cur.fetchall(), [("1", "2")])

            # Correct form with list
            cur.execute("SELECT ?, ?", ["1", "2"])
            self.assertEqual(cur.fetchall(), [("1", "2")])

        with self.cnx.cursor(prepared=True) as cur:
            insert_stmt = f"INSERT INTO {self.table_name} VALUES (?, ?, ?, ?, ?, ?)"
            cur.execute(insert_stmt)
            with self.assertRaises(errors.ProgrammingError) as contex:
                cur.execute(insert_stmt, "JD")
                self.assertIn(
                    f"Incorrect type of argument: {type('JD')}({'JD'}),"
                    "it must be of type tuple or list",
                    contex.exception.msg,
                )
            self.assertRaises(
                errors.ProgrammingError, cur.execute, insert_stmt, ("JohnDo")
            )
            cur.execute(insert_stmt, self.test_values[0])
            cur.execute(insert_stmt, self.test_values[1])

            select_stmt = f"SELECT * FROM {self.table_name} WHERE column_last_name=? and column_first_name=?"
            self.assertRaises(errors.ProgrammingError, cur.execute, select_stmt, ("JD"))
            with self.assertRaises(errors.ProgrammingError) as contex:
                cur.execute(select_stmt, "JD")
                self.assertIn(
                    "Incorrect type of argument: {type('JD')}({'JD'}),"
                    " it must be of type tuple or list",
                    contex.exception.msg,
                )
            cur.execute(select_stmt, ("Doe", "John"))
            self.assertEqual(cur.fetchall(), self.exp_values[0])
            cur.execute(select_stmt, ("Doe", "Jane"))
            self.assertEqual(cur.fetchall(), self.exp_values[1])


@unittest.skipIf(
    tests.MYSQL_EXTERNAL_SERVER,
    "Test not available for external MySQL servers",
)
class Bug32162928(tests.MySQLConnectorTests):
    """BUG#32162928: change user command fails with pure python implementation.

    The cmd_change_user() command fails with pure-python.
    """

    def setUp(self):
        self.connect_kwargs = tests.get_mysql_config()
        cnx = MySQLConnection(**self.connect_kwargs)
        self.users = [
            {
                "user": "user_native1",
                "host": self.connect_kwargs["host"],
                "port": self.connect_kwargs["port"],
                "database": self.connect_kwargs["database"],
                "password": "native1_pass",
                "auth_plugin": "mysql_native_password",
            },
            {
                "user": "user_native2",
                "host": self.connect_kwargs["host"],
                "port": self.connect_kwargs["port"],
                "database": self.connect_kwargs["database"],
                "password": "native2_pass",
                "auth_plugin": "mysql_native_password",
            },
            {
                "user": "user_sha2561",
                "host": self.connect_kwargs["host"],
                "port": self.connect_kwargs["port"],
                "database": self.connect_kwargs["database"],
                "password": "sha2561_pass",
                "auth_plugin": "sha256_password",
            },
            {
                "user": "user_sha2562",
                "host": self.connect_kwargs["host"],
                "port": self.connect_kwargs["port"],
                "database": self.connect_kwargs["database"],
                "password": "sha2562_pass",
                "auth_plugin": "sha256_password",
            },
            {
                "user": "user_caching1",
                "host": self.connect_kwargs["host"],
                "port": self.connect_kwargs["port"],
                "database": self.connect_kwargs["database"],
                "password": "caching1_pass",
                "auth_plugin": "caching_sha2_password",
            },
            {
                "user": "user_caching2",
                "host": self.connect_kwargs["host"],
                "port": self.connect_kwargs["port"],
                "database": self.connect_kwargs["database"],
                "password": "caching2_pass",
                "auth_plugin": "caching_sha2_password",
            },
        ]

        # create users
        if tests.MYSQL_VERSION < (8, 0, 0):
            self.new_users = self.users[0:4]
        else:
            self.new_users = (
                self.users if NATIVE_PASSWORD_INSTALLED else self.users[-4:]
            )
        for new_user in self.new_users:
            cnx.cmd_query("DROP USER IF EXISTS '{user}'@'{host}'".format(**new_user))

            stmt = (
                "CREATE USER IF NOT EXISTS '{user}'@'{host}' IDENTIFIED "
                "WITH {auth_plugin} BY '{password}'"
            ).format(**new_user)
            cnx.cmd_query(stmt)

            cnx.cmd_query(
                "GRANT ALL PRIVILEGES ON {database}.* TO "
                "'{user}'@'{host}'".format(**new_user)
            )

    @foreach_cnx()
    def test_change_user(self):
        # test users can connect
        for user in self.new_users:
            conn_args = user.copy()
            try:
                self.connect_kwargs.pop("auth_plugin")
            except:
                pass
            cnx_test = self.cnx.__class__(**conn_args)
            cnx_test.cmd_query("SELECT USER()")
            logged_user = cnx_test.get_rows()[0][0][0]
            self.assertEqual("{user}@{host}".format(**user), logged_user)
            cnx_test.close()

        # tests change user
        if tests.MYSQL_VERSION < (8, 0, 0):
            # 5.6 does not support caching_sha2_password auth plugin
            test_cases = [(0, 1), (1, 2), (2, 3), (3, 0)]
        else:
            test_cases = [
                (0, 1),
                (1, 2),
                (2, 3),
                (3, 0),
            ]
            if NATIVE_PASSWORD_INSTALLED:
                test_cases += [
                    (3, 4),
                    (4, 5),
                    (5, 3),
                    (5, 0),
                ]

        for user1, user2 in test_cases:
            conn_args_user1 = self.new_users[user1].copy()
            try:
                conn_args_user1.pop("auth_plugin")
            except:
                pass
            if tests.MYSQL_VERSION < (8, 0, 0):
                # change user does not work in 5.x with charset utf8mb4
                conn_args_user1["charset"] = "utf8"

            cnx_test = self.cnx.__class__(**conn_args_user1)
            cnx_test.cmd_query("SELECT USER()")
            first_user = cnx_test.get_rows()[0][0][0]
            self.assertEqual(
                "{user}@{host}".format(**self.new_users[user1]), first_user
            )

            cnx_test.cmd_change_user(
                self.new_users[user2]["user"],
                self.new_users[user2]["password"],
                self.new_users[user2]["database"],
            )
            cnx_test.cmd_query("SELECT USER()")
            rows = cnx_test.get_rows()
            current_user = rows[0][0][0]
            self.assertNotEqual(first_user, current_user)
            self.assertEqual(
                "{user}@{host}".format(**self.new_users[user2]), current_user
            )
            cnx_test.close()

    def tearDown(self):
        cnx = MySQLConnection(**self.connect_kwargs)
        # cleanup users
        for new_user in self.new_users:
            cnx.cmd_query("DROP USER IF EXISTS '{user}'@'{host}'".format(**new_user))


class BugOra32497631(tests.MySQLConnectorTests):
    """BUG#32497631: PREPARED STMT FAILS ON CEXT WHEN PARAMS ARE NOT GIVEN"""

    table_name = "BugOra32497631"

    @foreach_cnx()
    def test_prepared_statement_parameters(self):
        self.cnx.cmd_query(f"DROP TABLE IF EXISTS {self.table_name}")
        self.cnx.cmd_query(
            f"""
            CREATE TABLE {self.table_name}
            (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255))
            """
        )
        with self.cnx.cursor(prepared=True) as cur:
            query = f"INSERT INTO {self.table_name} (name) VALUES (?)"
            # If the query has placeholders and no parameters is given,
            # the statement is prepared but not executed
            cur.execute(query)

            # Test with parameters
            cur.execute(query, ("foo",))
            cur.execute(query, ("bar",))

            cur.execute(f"SELECT name FROM {self.table_name}")
            rows = cur.fetchall()
            self.assertEqual(2, len(rows))
        self.cnx.cmd_query(f"DROP TABLE IF EXISTS {self.table_name}")


class BugOra30203754(tests.MySQLConnectorTests):
    """BUG#30203754: PREPARED STMT FAILS ON CEXT with BIGINTS

    BUG#33481203: OverflowError for MySQL BIGINT supported value
                  9223372036854775807 on c-ext prep
    """

    table_name = "BugOra30203754"

    @foreach_cnx()
    def test_prepared_statement_bigints(self):
        self.cnx.cmd_query(f"DROP TABLE IF EXISTS {self.table_name}")
        self.cnx.cmd_query(
            f"CREATE TABLE {self.table_name}"
            " (indx INT key auto_increment, bigints BIGINT)"
        )
        test_cases = (
            -9223372036854775808,
            -9223372036854775807,
            -922337203685477580,
            -2147483648,
            0,
            2147483647,
            2147483648,
            922337203685477580,
            9223372036854775806,
            9223372036854775807,
        )

        prepared_options = [True, False]
        for prepared in prepared_options:
            with self.cnx.cursor(prepared=prepared) as cur:
                for tc in test_cases:
                    query = f"select %s"
                    cur.execute(query, (tc,))
                    rows = cur.fetchall()
                    self.assertEqual(tc, rows[0][0])

                for tc in test_cases:
                    query = f"INSERT INTO {self.table_name} (bigints) VALUES (%s)"
                    cur.execute(query, (tc,))
                    self.cnx.commit()

                for index, tc in enumerate(test_cases):
                    query = f"SELECT bigints FROM {self.table_name} WHERE indx = '{index+1}'"
                    cur.execute(query)
                    rows = cur.fetchall()
                    self.assertEqual(tc, rows[0][0])
        self.cnx.cmd_query(f"DROP TABLE IF EXISTS {self.table_name}")


class BugOra31528783(tests.MySQLConnectorTests):
    """BUG#31528783: ZEROFILL NOT HANDLED BY THE PYTHON CONNECTOR."""

    table_name = "BugOra31528783"

    @foreach_cnx()
    def test_number_zerofill(self):
        self.cnx.cmd_query(f"DROP TABLE IF EXISTS {self.table_name}")
        self.cnx.cmd_query(
            f"""
                CREATE TABLE {self.table_name} (
                    value INT(4) UNSIGNED ZEROFILL NOT NULL,
                    PRIMARY KEY(value)
                )
            """
        )
        with self.cnx.cursor() as cur:
            values = [1, 10, 100, 1000]
            # Insert data
            for value in values:
                cur.execute(f"INSERT INTO {self.table_name} (value) VALUES ({value})")

            # Test values
            for value in values:
                cur.execute(f"SELECT value FROM {self.table_name} WHERE value={value}")
                res = cur.fetchone()
                self.assertEqual(res[0], value)
        self.cnx.cmd_query(f"DROP TABLE IF EXISTS {self.table_name}")


class BugOra21528553(tests.MySQLConnectorTests):
    """BUG#21528553: INCONSISTENT BEHAVIOUR WITH C-EXT APIS WHEN
    CONSUME_RESULTS=TRUE."""

    table_name = "BugOra21528553"

    def setUp(self):
        config = tests.get_mysql_config()
        with mysql.connector.connect(**config) as cnx:
            cnx.cmd_query(f"DROP TABLE IF EXISTS {self.table_name}")
            cnx.cmd_query(
                f"""
                CREATE TABLE {self.table_name} (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    c1 CHAR(32),
                    c2 LONGBLOB
                ) CHARACTER SET utf8 COLLATE utf8_general_ci
                """
            )
            cnx.cmd_query(
                f"INSERT INTO {self.table_name} (c1, c2) "
                "VALUES ('1','1'),('2','2'),('3','3')"
            )
            cnx.commit()

    def tearDown(self):
        config = tests.get_mysql_config()
        with mysql.connector.connect(**config) as cnx:
            cnx.cmd_query(f"DROP TABLE IF EXISTS {self.table_name}")

    @cnx_config(consume_results=True)
    @foreach_cnx()
    def test_cmd_refresh_with_consume_results(self):
        with self.cnx.cursor() as cur:
            cur.execute(f"SELECT c1, c2 FROM {self.table_name}")
            res = cur.fetchone()
            self.assertEqual(len(res), 2)
            self.assertTrue(self.cnx.unread_result)
            refresh = constants.RefreshOption.LOG | constants.RefreshOption.STATUS
            self.cnx.cmd_refresh(refresh)
            self.assertFalse(self.cnx.unread_result)

    @cnx_config(consume_results=True)
    @foreach_cnx()
    def test_reset_session_with_consume_results(self):
        with self.cnx.cursor() as cur:
            cur.execute(f"SELECT c1, c2 FROM {self.table_name}")
            res = cur.fetchone()
            self.assertEqual(len(res), 2)
            self.assertTrue(self.cnx.unread_result)
            self.cnx.reset_session()
            self.assertFalse(self.cnx.unread_result)

    @cnx_config(consume_results=True)
    @foreach_cnx()
    def test_commit_with_consume_results(self):
        with self.cnx.cursor() as cur:
            cur.execute(f"SELECT c1, c2 FROM {self.table_name}")
            res = cur.fetchone()
            self.assertEqual(len(res), 2)
            self.assertTrue(self.cnx.unread_result)
            self.cnx.commit()
            self.assertFalse(self.cnx.unread_result)

    @cnx_config(consume_results=True)
    @foreach_cnx()
    def test_ping_with_consume_results(self):
        with self.cnx.cursor() as cur:
            cur.execute(f"SELECT c1, c2 FROM {self.table_name}")
            res = cur.fetchone()
            self.assertEqual(len(res), 2)
            self.assertTrue(self.cnx.unread_result)
            self.cnx.ping()
            self.assertFalse(self.cnx.unread_result)

    @cnx_config(consume_results=True)
    @foreach_cnx()
    def test_is_connected_with_consume_results(self):
        with self.cnx.cursor() as cur:
            cur.execute(f"SELECT c1, c2 FROM {self.table_name}")
            res = cur.fetchone()
            self.assertEqual(len(res), 2)
            self.assertTrue(self.cnx.unread_result)
            self.assertTrue(self.cnx.is_connected())
            self.assertFalse(self.cnx.unread_result)


class BugOra33747585(tests.MySQLConnectorTests):
    """BUG#33747585: Fix error when using an expression as a column without an
    alias (c-ext)."""

    @foreach_cnx()
    def test_expression_as_column_without_alias(self):
        with self.cnx.cursor() as cur:
            cur.execute(
                """
                SELECT datediff(
                  str_to_date((
                    SELECT variable_value FROM performance_schema.global_status
                    WHERE variable_name='Ssl_server_not_after'),
                    "%b %d %T %Y GMT"),
                  str_to_date((
                    SELECT variable_value FROM performance_schema.global_status
                    WHERE variable_name='Ssl_server_not_before'),
                    "%b %d %T %Y GMT"))
                """
            )
            _ = cur.fetchall()


class BugOra328821983(tests.MySQLConnectorTests):
    """BUG#328821983: Fix rounding errors when using decimal.Decimal."""

    @foreach_cnx()
    def test_decimal_update(self):
        table = "BugOra328821983"
        with self.cnx.cursor() as cur:
            cur.execute(f"DROP TABLE IF EXISTS {table}")
            cur.execute(
                f"""
                CREATE TABLE {table} (
                    id INT(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
                    value DECIMAL(32,8) NOT NULL
                )
                """
            )
            cur.execute(
                f"INSERT INTO {table} VALUES (NULL, %s)",
                (Decimal("100000000000.00000001"),),
            )
            cur.execute(f"SELECT value FROM {table}")
            res = cur.fetchall()[0][0]
            self.assertEqual(res, Decimal("100000000000.00000001"))

            # Use this value to increment the decimal field
            value = Decimal("0.00000101")

            # Test update with tuple as placeholders
            query = f"UPDATE {table} SET value=(value + %s) WHERE id=%s"
            cur.execute(query, (value, 1))

            cur.execute(f"SELECT value FROM {table}")
            res = cur.fetchall()[0][0]
            self.assertEqual(res, Decimal("100000000000.00000102"))

            # Test update with dictionary as placeholders
            query = f"UPDATE {table} SET value=(value + %(value)s) WHERE id=%(id)s"
            cur.execute(query, {"value": value, "id": 1})

            cur.execute(f"SELECT value FROM {table}")
            res = cur.fetchall()[0][0]
            self.assertEqual(res, Decimal("100000000000.00000203"))

            cur.execute(f"DROP TABLE IF EXISTS {table}")


class BugOra34228442(tests.MySQLConnectorTests):
    """BUG#34228442: Fix NO_BACKSLASH_ESCAPES SQL mode support in c-ext."""

    @foreach_cnx()
    def test_no_backslash_escapes(self):
        table = "BugOra34228442"
        self.cnx.sql_mode = [constants.SQLMode.NO_BACKSLASH_ESCAPES]
        with self.cnx.cursor() as cur:
            cur.execute(f"DROP TABLE IF EXISTS {table}")
            cur.execute(
                f"""
                CREATE TABLE {table} (
                    `id` INT(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
                    `text` VARCHAR(255)
                )
                """
            )
            cur.execute(f"INSERT INTO {table} (`text`) VALUES ('test')")
            cur.execute(f"SELECT text FROM {table} WHERE text = %s", ["test"])
            res = cur.fetchall()
            self.assertEqual(res[0][0], "test")
            self.assertEqual(self.cnx.sql_mode, "NO_BACKSLASH_ESCAPES")
            cur.execute(f"DROP TABLE IF EXISTS {table}")


class BugOra28491115(tests.MySQLConnectorTests):
    """BUG#28491115: MySQL-Connector-Python Crashes On 0 Time Value.

    a) The mysql-python-connector binary protocol appears to crash on
    time value of 0 because it does not deal with payload of size 0
    correctly.
    b) When querying a TIME field that is set to 00:00:00,
    mysql.connector throws an exception when trying to unpack the
    result.

    Also fixes BUG#34006512 (Mysql.Connector Throws Exception When Time Field Is 0).
    """

    @foreach_cnx()
    def test_crash_on_time_0value(self):
        table_name = "BugOra28491115"
        with self.cnx.cursor(prepared=True) as cur:
            cur.execute(f"DROP TABLE IF EXISTS {table_name}")
            cur.execute(
                f"CREATE TABLE {table_name} (id INT AUTO_INCREMENT PRIMARY KEY, a TIME)"
            )
            cur.execute(f"INSERT INTO {table_name} (a) VALUES (0)")
            cur.execute(f"SELECT a FROM {table_name}")
            res = cur.fetchall()
            self.assertEqual(res[0][0], timedelta(0))
            cur.execute(f"DROP TABLE IF EXISTS {table_name}")

    @foreach_cnx()
    def test_exception_when_time_field_is_0(self):
        table_name = "BugOra34006512"
        with self.cnx.cursor(prepared=True) as cur:
            cur.execute(f"DROP TABLE IF EXISTS {table_name}")
            cur.execute(f"CREATE TEMPORARY TABLE {table_name} (b TIME)")
            cur.execute(f"INSERT INTO {table_name} SET b='00:00'")
            cur.execute(f"SELECT * FROM {table_name}")
            res = cur.fetchall()
            self.assertEqual(res[0][0], timedelta(0))
            cur.execute(f"DROP TABLE IF EXISTS {table_name}")


class BugOra34283402(tests.MySQLConnectorTests):
    """BUG#34283402: Binary data starting with 0x00 are returned as empty string.

    This patch fixes an issue introduced by BUG#33747585 that fixed the
    UnicodeDecodeError raised in the c-ext implementation when using an
    expression as a column without an alias.
    """

    @foreach_cnx()
    def test_binary_data_started_with_0x00(self):
        table_name = "BugOra34283402"
        exp = [
            (bytearray(b'\x11"3DUfw\x88\x99\xaa\xbb\xcc\xdd\xee\xff\x00'),),
            (bytearray(b'\x11"\x003DUfw\x88\x99\xaa\xbb\xcc\xdd\xee\xff'),),
            (bytearray(b'\x00\x11"3DUfw\x88\x99\xaa\xbb\xcc\xdd\xee\xff'),),
        ]
        with self.cnx.cursor() as cur:
            cur.execute(f"DROP TABLE IF EXISTS {table_name}")
            cur.execute(
                f"""
                    CREATE TABLE `{table_name}` (
                        `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
                        `data` binary(16) DEFAULT NULL,
                        PRIMARY KEY (`id`)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8
                """
            )
            cur.execute(
                f"""
                    INSERT INTO {table_name} (data) VALUES
                    (0x112233445566778899aabbccddeeff00),
                    (0x11220033445566778899aabbccddeeff),
                    (0x00112233445566778899aabbccddeeff)
                """
            )
            cur.execute(f"SELECT data FROM {table_name}")
            res = cur.fetchall()
            self.assertEqual(exp, res)
            cur.execute(f"DROP TABLE IF EXISTS {table_name}")


class BugOra21463298(tests.MySQLConnectorTests):
    """BUG#21463298: Fix weakly-referenced object no longer exists exception.

    Connector/Python cursors contain a weak reference to the connection,
    and a weak reference to an object is not enough to keep the object
    alive. So when the connection object is destroyed and the cursor is
    used, a ReferenceError exception is raised saying that the
    weakly-referenced object no longer exists.

    With this patch a ProgrammingError exception is raised instead saying
    the cursor is not connected.
    """

    @foreach_cnx()
    def test_weakly_referenced_error(self):
        config = tests.get_mysql_config()

        def get_cursor():
            return self.cnx.__class__(**config).cursor()

        with self.assertRaises(errors.ProgrammingError) as context:
            get_cursor().execute("SELECT SLEEP(1)")
        self.assertEqual(context.exception.msg, "Cursor is not connected")


class BugOra33987119(tests.MySQLConnectorTests):
    """BUG#33987119: TEXT and with a _bin collation (e.g: utf8mb4_bin) are considered as bytes object.

    An unexpected behaviour happens when using a "_bin" suffixed
    collation type for the pure Connector/Python implementation.
    BLOB and BINARY fields are expected to be delivered as bytes
    objects as this is the expected behaviour, however, TEXT
    fields are being delivered the same way when using a "_bin"
    suffixed collation type. This latter is not correct.

    With this patch, the unexpected behaviour is corrected by
    updating the MySQLConverter._blob_to_python() method.
    The connector at decoding/delivery time submits TEXT
    fields to this latter method to determine the final conversion
    since there is no specific method to handle TEXT datatypes.
    An extra test is added, it is used the field charset description
    to cast the incoming field value to the right type.
    """

    @foreach_cnx(connection.MySQLConnection)
    def text_datatype_handled_as_binary_for_bin_suffix_collation(self):
        table_name = "BugOra33987119"
        tests = [
            ["TEXT", "VARCHAR(255)", "BLOB"],
            ["TINYTEXT", "CHAR(255)", "LONGBLOB"],
            ["MEDIUMTEXT", "TEXT", "TINYBLOB"],
            ["LONGTEXT", "MEDIUMTEXT", "MEDIUMBLOB"],
            ["VARCHAR(255)", "TINYTEXT", "BLOB"],
            ["CHAR(255)", "LONGTEXT", "TINYBLOB"],
        ]
        charcoll_map = {
            "utf8mb4": {
                "utf8mb4_bin",
                "utf8mb4_spanish2_ci",
                "utf8mb4_icelandic_ci",
            },
            "utf16": {
                "utf16_general_ci",
                "utf16_bin",
                "utf16_vietnamese_ci",
            },
            "greek": {
                "greek_bin",
                "greek_general_ci",
            },
        }
        data = ("webmaster@python.org", "very-secret", "I am a blob!")
        insert_stmt = f"INSERT INTO {table_name} (`email`, `password`, `dummy`) VALUES (%s, %s, %s)"
        with self.cnx.cursor() as cur:
            for charset, collation_set in charcoll_map.items():
                for collation in collation_set:
                    for t1, t2, t3 in tests:
                        cur.execute(f"DROP TABLE IF EXISTS {table_name}")
                        try:
                            cur.execute(
                                f"""
                            CREATE TABLE {table_name} (
                                `id` int(11) NOT NULL AUTO_INCREMENT,
                                `email` {t1} NOT NULL,
                                `password` {t2} NOT NULL,
                                `dummy` {t3} NOT NULL,
                                PRIMARY KEY (`id`)
                            ) ENGINE=InnoDB DEFAULT CHARSET={charset} COLLATE={collation}
                            AUTO_INCREMENT=1 ;
                            """
                            )
                            cur.execute(insert_stmt, data)
                            cur.execute(f"SELECT * from {table_name}")
                            res = cur.fetchall()
                        except:
                            self.fail("Something went wrong in the test body!")
                        else:
                            try:
                                for value, target_type in zip(
                                    res[0], (int, str, str, bytes)
                                ):
                                    self.assertEqual(type(value), target_type)
                            except IndexError as err:
                                self.fail(f"{err}")
                        finally:
                            # always executed
                            cur.execute(f"DROP TABLE IF EXISTS {table_name}")


class BugOra34689812(tests.MySQLConnectorTests):
    """BUG#34689812: Fix datetime conversion when using prepared cursors.

    When using a prepared cursor, if a datetime column contains 00:00:00 as
    time, a Python date object is returned instead of datetime.

    This patch inspects the column type instead of relying on the packet
    length and returns the proper object type.
    """

    table_name = "BugOra34689812"
    data = (
        date(2022, 10, 13),
        datetime(2022, 10, 13, 0, 0, 0),
        datetime(2022, 10, 13, 0, 0, 0, 0),
    )

    def setUp(self):
        config = tests.get_mysql_config()
        with mysql.connector.connect(**config) as cnx:
            with cnx.cursor(prepared=True) as cur:
                cur.execute(f"DROP TABLE IF EXISTS {self.table_name}")
                cur.execute(
                    f"""
                    CREATE TABLE {self.table_name} (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        my_date DATE,
                        my_datetime DATETIME,
                        my_timestamp TIMESTAMP
                    )
                    """
                )
                cur.execute(
                    f"""
                    INSERT INTO {self.table_name}
                    (my_date, my_datetime, my_timestamp) VALUES (?, ?, ?)
                    """,
                    self.data,
                )
            cnx.commit()

    def tearDown(self):
        config = tests.get_mysql_config()
        with mysql.connector.connect(**config) as cnx:
            cnx.cmd_query(f"DROP TABLE IF EXISTS {self.table_name}")

    @foreach_cnx()
    def test_datetime_with_prepared_cursor(self):
        with self.cnx.cursor(prepared=True) as cur:
            cur.execute(
                f"SELECT my_date, my_datetime, my_timestamp FROM {self.table_name}"
            )
            res = cur.fetchall()
            self.assertEqual(res[0], self.data)


class BugOra34499578(tests.MySQLConnectorTests):
    """BUG#34499578: MySQLCursor.executemany() fails to correctly identify BULK data loading ops.

    The MySQLCursor.executemany() method fails to batch insert data since
    the regular expression (RE) sentinel used does not detect batch cases
    correctly resulting in using the one-on-one insert, hence an overall
    performance issue.
    """

    table_name = "BugOra34499578"
    field1, field2 = "color", "country"

    def setUp(self):
        config = tests.get_mysql_config()
        with mysql.connector.connect(**config) as cnx:
            with cnx.cursor() as cur:
                cur.execute(f"DROP TABLE IF EXISTS {self.table_name}")
                cur.execute(
                    f"""
                    CREATE TABLE {self.table_name}(
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        {self.field1} char(32),
                        {self.field2} char(32)
                    )
                    """
                )
            cnx.commit()

    def tearDown(self):
        config = tests.get_mysql_config()
        with mysql.connector.connect(**config) as cnx:
            cnx.cmd_query(f"DROP TABLE IF EXISTS {self.table_name}")

    @foreach_cnx()
    def test_batch_insert_happens_in_executemany(self):
        seq_params = [["red", "portugal"], ["green", "mexico"], ["blue", "argentina"]]
        with self.cnx.cursor() as cur:
            cur.executemany(
                f"""
                INSERT INTO {self.table_name} (
                    {self.field1},
                    {self.field2})
                    VALUES(
                        %s,
                        %s
                    )
                """,
                seq_params,
            )
            # if batch insert happens, it means all parameters must be
            # somewhere in the executed statement, else just a parameters
            # subset is in, particularly the last parameter.
            self.assertTrue(
                all(
                    [
                        param.encode("utf8", errors="ignore") in cur._executed
                        for params in seq_params
                        for param in params
                    ]
                ),
                "Batch insert failed!",
            )


class BugOra34467201(tests.MySQLConnectorTests):
    """BUG#34467201: Add init_command connection option

    With this patch, support for the inti_command option is added as
    part of the connection settings. This new option allows the user to
    specify a command to be executed right after the connection is
    established, that's to say, as part of the connection initialization.
    """

    var_name = "test_var"
    var_value = "BugOra34467201"
    init_command = f"SET @{var_name}='{var_value}'"

    @foreach_cnx(init_command=init_command)
    def test_init_command(self):
        with self.cnx.cursor() as cur:
            cur.execute(f"SELECT @{self.var_name}")
            res = cur.fetchall()
            self.assertEqual((self.var_value,), res[0])


class BugOra20504804(tests.MySQLConnectorTests):
    """BUG#20504804: cursor.executemany() fails with INSERT IGNORE

    When using INSERT IGNORE with cursor.executemany(), not all parameters
    are added to the INSERT statement.

    This patch fixes this issue by adding IGNORE in the regular expression
    used to build the INSERT statement.
    """

    table_name = "BugOra20504804"

    def setUp(self):
        config = tests.get_mysql_config()
        with mysql.connector.connect(**config) as cnx:
            with cnx.cursor() as cur:
                cur.execute(f"DROP TABLE IF EXISTS {self.table_name}")
                cur.execute(
                    f"""
                    CREATE TABLE {self.table_name} (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(128)
                    )
                    """
                )
            cnx.commit()

    def tearDown(self):
        config = tests.get_mysql_config()
        with mysql.connector.connect(**config) as cnx:
            cnx.cmd_query(f"DROP TABLE IF EXISTS {self.table_name}")

    @foreach_cnx()
    def test_executemany_insert_ignore(self):
        with self.cnx.cursor() as cur:
            cur.executemany(
                f"INSERT IGNORE INTO {self.table_name} (name) VALUES (%s)",
                [("Foo",), ("Bar",)],
            )
            self.assertEqual(
                f"INSERT IGNORE INTO {self.table_name} (name) VALUES ('Foo'),('Bar')",
                cur.statement,
            )


class BugOra34984850(tests.MySQLConnectorTests):
    """BUG#34984850: Fix binary conversion with NO_BACKSLASH_ESCAPES mode

    The Connector/Python C extension converter truncates bytes containing
    the \x00 byte when using NO_BACKSLASH_ESCAPES mode in MySQL.
    The PyBytes_AsString() Python function interprets the \x00 as the end
    of the string, dropping the rest of the binary data.

    This patch fixes this issue by using the PyBytes_Concat() function to
    quote the resulting bytes.
    """

    table_name = "BugOra34984850"

    def setUp(self):
        config = tests.get_mysql_config()
        with mysql.connector.connect(**config) as cnx:
            with cnx.cursor() as cur:
                cur.execute(f"DROP TABLE IF EXISTS {self.table_name}")
                cur.execute(
                    f"""
                    CREATE TABLE {self.table_name} (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        data LONGBLOB,
                        text VARCHAR(50)
                    )
                    """
                )
            cnx.commit()

    def tearDown(self):
        config = tests.get_mysql_config()
        with mysql.connector.connect(**config) as cnx:
            cnx.cmd_query(f"DROP TABLE IF EXISTS {self.table_name}")

    def _run_test(self):
        data = (b"\x01\x02\x00\x01", "abc'cba")
        for use_backslash_escapes in (True, False):
            if use_backslash_escapes:
                self.cnx.sql_mode = [constants.SQLMode.NO_BACKSLASH_ESCAPES]
            with self.cnx.cursor() as cur:
                cur.execute(
                    f"INSERT INTO {self.table_name} (data, text) VALUES (%s, %s)", data
                )
                cur.execute(f"SELECT data, text FROM {self.table_name} LIMIT 1")
                res = cur.fetchone()
                self.assertEqual(data, res)

    @foreach_cnx()
    def test_no_backslash_escapes(self):
        self._run_test()

    @cnx_config(converter_class=conversion.MySQLConverter)
    @foreach_cnx()
    def test_no_backslash_escapes_with_converter_class(self):
        self._run_test()


class BugOra29115406(tests.MySQLConnectorTests):
    """BUG#29115406: CONTRIBUTION: FIX RECV COMPRESS BUG

    When switching to compressed mode while using the pure
    python implementation, there is a bug where a compressed
    packet may contain an incomplete MySQL packet at last.

    The bug report does not say much about the issue and
    does not even provide a test case that proves it,
    however, we managed to find the bug the contributor
    means while developing the work log WL#15591(improve
    the network module).

    Such a  work log provides a fix for the issue.
    """

    @cnx_config(compress=True)
    @foreach_cnx()
    def compressed_packet_incomplete_at_last(self):
        """When receiving a compressed packet as the first
        step we need to decompress the payload.

        After step 1, the payload might contain a sequence
        of plain packets:

        # `h` and `pl` stand for header and payload respectively
        ```
        uncompressed payload = pkt1 + pkt2 + pkt3 + ... + pktN
                             = (h1 + pl1) + (h2 + pl2) + (h3 + pl3) + ... + (hN + plN)
        ```

        , but sometimes it happens that the last payload is
        incomplete, by incomplete we mean that the payload
        length from the last header (`hN`) is bigger than the length
        of the last payload itself (len(plN)).

        ```
        header, payload = pktN[0:4], pktN[4:]
        payload_length, sequence_id = get_header(header)
        if payload_length > len(payload):
            raise BugError("Last packet is incomplete")
        ```

        This effect takes place when the input size is about the
        network.MAX_PAYLOAD_LENGTH, or bigger.
        """
        input_sizes = [
            network.MAX_PAYLOAD_LENGTH - 303,
            (network.MAX_PAYLOAD_LENGTH * 2) + 2,
            network.MAX_PAYLOAD_LENGTH * 3,
        ]
        with self.cnx.cursor() as cur:
            for input_size in input_sizes:
                data = "b" * input_size
                cur.execute("SELECT %s", (data,))
                res = cur.fetchone()
                self.assertEqual(data[:-5000], res[0][:-5000])
                self.assertEqual(len(data), len(res[0]))


class BugOra35212199(tests.MySQLConnectorTests):
    """BUG#35212199: Check for identifier quotes in the database name

    Connector/Python raises an error when setting the database name on a
    connection that includes non-alphanumeric characters and using the pure
    Python implementation.

    This patch fixes the issue by using `connection.cmd_init_db()` to set
    the database name.
    """

    database = "abc-abc|$%"

    def setUp(self):
        with mysql.connector.connect(**tests.get_mysql_config()) as cnx:
            try:
                cnx.cmd_query(f"DROP DATABASE `{self.database}`")
            except errors.DatabaseError:  # Database already exists
                pass
            cnx.cmd_query(f"CREATE DATABASE `{self.database}`")

    def tearDown(self):
        with mysql.connector.connect(**tests.get_mysql_config()) as cnx:
            cnx.cmd_query(f"DROP DATABASE `{self.database}`")

    @foreach_cnx()
    def test_set_database_name(self):
        """Test setting the database on an established connection."""
        self.cnx.database = self.database

    @foreach_cnx()
    def test_connect_database_name(self):
        """Test setting the database when establishing a connection."""
        config = tests.get_mysql_config()
        config["database"] = self.database
        with self.cnx.__class__(**config) as cnx:
            self.assertTrue(cnx.is_connected())


class BugOra35349093(tests.MySQLConnectorTests):
    """BUG#35349093: Compression doesn't work with C extension API

    Compression is not enabled when using the C API implementation directly
    with the connection option `compress=True`.

    This patch fixes this issue by adding CLIENT_COMPRESS to client flags.

    Thank you for your contribution.
    """

    def _get_compression_status(self):
        with self.cnx.cursor() as cur:
            cur.execute("SHOW SESSION STATUS LIKE 'Compression'")
            return cur.fetchone()

    @staticmethod
    def _test_compression_status_cext(compress):
        config = tests.get_mysql_config()
        del config["connection_timeout"]
        config["compress"] = compress
        cnx = MySQL()
        cnx.connect(**config)
        cnx.query("SHOW SESSION STATUS LIKE 'Compression'")
        res = cnx.fetch_row()
        cnx.close()
        return res

    @foreach_cnx()
    def test_set_compress_default(self):
        """Test default `compress` option."""
        res = self._get_compression_status()
        self.assertEqual(res, ("Compression", "OFF"))

    @cnx_config(compress=False)
    @foreach_cnx()
    def test_set_compress_false(self):
        """Test setting `compress=False`."""
        res = self._get_compression_status()
        self.assertEqual(res, ("Compression", "OFF"))

    @cnx_config(compress=True)
    @foreach_cnx()
    def test_set_compress_true(self):
        """Test setting `compress=True`."""
        res = self._get_compression_status()
        self.assertEqual(res, ("Compression", "ON"))

    @unittest.skipIf(not CMySQLConnection, ERR_NO_CEXT)
    def test_set_compress_cext_true(self):
        """Test setting `compress=True` in the C extension directly."""
        res = self._test_compression_status_cext(True)
        self.assertEqual(res, ("Compression", "ON"))

    @unittest.skipIf(not CMySQLConnection, ERR_NO_CEXT)
    def test_set_compress_cext_false(self):
        """Test setting `compress=False` in the C extension directly."""
        res = self._test_compression_status_cext(False)
        self.assertEqual(res, ("Compression", "OFF"))


class BugOra35278365(tests.MySQLConnectorTests):
    """BUG#35278365: Fix UnicodeDecodeError with a long field name alias (c-ext)

    An UnicodeDecodeError is raised when using a complex query that produces
    a long field name alias.
    It fails to create an Unicode object using `PyUnicode_Decode()` from the
    resulting `MYSQL_FIELD.name` returned by `mysql_fetch_fields()` MySQL
    C API.

    This patch uses "replace" in `PyUnicode_Decode()` to set how decoding
    errors are handled, which uses a replace marker.
    """

    tbl_prefix = "BugOra35278365"

    def setUp(self):
        config = tests.get_mysql_config()
        with mysql.connector.connect(**config) as cnx:
            with cnx.cursor() as cur:
                cnx.cmd_query(f"DROP TABLE IF EXISTS {self.tbl_prefix}_table1")
                cnx.cmd_query(f"DROP TABLE IF EXISTS {self.tbl_prefix}_table2")
                cnx.cmd_query(f"DROP TABLE IF EXISTS {self.tbl_prefix}_table3")
                cur.execute(
                    f"""
                    CREATE TABLE {self.tbl_prefix}_table1 (
                    id int(11) NOT NULL,
                    ort_id int(11) DEFAULT NULL
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
                    """
                )
                cur.execute(
                    f"""
                    CREATE TABLE {self.tbl_prefix}_table2 (
                    id int(11) NOT NULL
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
                    """
                )
                cur.execute(
                    f"""
                    CREATE TABLE {self.tbl_prefix}_table3 (
                    besuch_id int(11) NOT NULL,
                    taxon varchar(30) NOT NULL,
                    epitheton varchar(30) DEFAULT NULL,
                    rang int(1) NOT NULL
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
                    """
                )
                cnx.commit()

    def tearDown(self):
        config = tests.get_mysql_config()
        with mysql.connector.connect(**config) as cnx:
            cnx.cmd_query(f"DROP TABLE IF EXISTS {self.tbl_prefix}_table1")
            cnx.cmd_query(f"DROP TABLE IF EXISTS {self.tbl_prefix}_table2")
            cnx.cmd_query(f"DROP TABLE IF EXISTS {self.tbl_prefix}_table3")
            cnx.commit()

    @foreach_cnx()
    def test_long_field_names(self):
        with mysql.connector.connect(**tests.get_mysql_config()) as cnx:
            with cnx.cursor() as cur:
                query = f"""
                    SELECT (SELECT Group_concat(DISTINCT Concat_ws(' ', taxon,
                                                Ifnull(t3.epitheton, 'sp.'))
                        ORDER BY
                            t3.taxon, Isnull(t3.epitheton), t3.epitheton SEPARATOR ', ')
                            FROM   {self.tbl_prefix}_table3 t3
                            WHERE  t3.besuch_id = {self.tbl_prefix}_table1.id
                            AND t3.rang IN (1, 2)
                            AND NOT EXISTS(
                                SELECT 0 FROM {self.tbl_prefix}_table3 b3)), 1, 1
                    FROM   {self.tbl_prefix}_table1,{self.tbl_prefix}_table2
                    WHERE  {self.tbl_prefix}_table2.id = {self.tbl_prefix}_table1.ort_id
                    ORDER  BY {self.tbl_prefix}_table1.id
                """
                cur.execute(query)  # No error is success
                res = cur.fetchall()
                self.assertEqual(res, [])


class BugOra35503506(tests.MySQLConnectorTests):
    """BUG#35503506: Query on information_schema.columns returns bytes

    When querying information_schema.columns using the C extension, MySQL
    Connector/Python returns bytes instead of str in the result values.

    This patch fixes this issue by testing if the charset is binary.
    """

    table_name = "BugOra35503506"

    def setUp(self):
        config = tests.get_mysql_config()
        with mysql.connector.connect(**config) as cnx:
            cnx.cmd_query(f"DROP TABLE IF EXISTS {self.table_name}")
            cnx.cmd_query(
                f"""
                CREATE TABLE {self.table_name} (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    data LONGBLOB,
                    text VARCHAR(50)
                )
                """
            )

    def tearDown(self):
        config = tests.get_mysql_config()
        with mysql.connector.connect(**config) as cnx:
            cnx.cmd_query(f"DROP TABLE IF EXISTS {self.table_name}")

    @foreach_cnx()
    def test_information_schema_columns_result(self):
        config = tests.get_mysql_config()
        database = config["database"]
        exp = [
            (
                "id",
                "int",
                None,
                "int" if tests.MYSQL_VERSION > (8, 0) else "int(11)",
                10,
                0,
            )
        ]
        with mysql.connector.connect(**config) as cnx:
            with cnx.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH,
                    COLUMN_TYPE, NUMERIC_PRECISION, NUMERIC_SCALE
                    FROM information_schema.columns
                    WHERE TABLE_NAME = '{self.table_name}'
                    AND TABLE_SCHEMA = '{database}'
                    AND COLUMN_NAME = 'id'
                    ORDER BY ORDINAL_POSITION
                    """
                )
                res = cur.fetchall()
                self.assertEqual(exp, res)


class BugOra35710145(tests.MySQLConnectorTests):
    """BUG#35710145: Bad MySQLCursor.statement and result when query text contains \
    code comments

    Wrong query results provided by the connector, when the query contains code comments.
    The regex expression that splits a multi-statement query produces as many statements
    as semicolon-separated operations are found in the query.

    End-of-line (EOL) comments are treated as if they were normal statements by the
    connector but that leads to inconsistencies when reading results from the server
    and trying to map each result to a statement since it's assumed every statement
    will produce a result, but isn't always the case - eg for comments.

    Comments should be treated specially to avoid issues.
    """

    table_name = "BugOra35710145"
    ops = [
        f"# dropping table; \n DROP TABLE IF EXISTS {table_name};",
        f"CREATE TABLE {table_name} (id INT AUTO_INCREMENT PRIMARY KEY, city VARCHAR(20),country_id INT); -- create table",
        "-- i am a comment;\nSELECT 1;",
        "SELECT 2;-- A;",
        "SELECT 2 /* this is an in-line comment */ + 1;\nSELECT 4;",
        f"""INSERT INTO {table_name} (city, country_id) VALUES ('Guadalajara', '12'); \nSELECT 5;""",
        "SELECT 6;\n# A;#B;",
        "#hello;\n-- hello;\nSELECT 7; -- world",
        "#hello;\n-- hello;\nSELECT 8; -- world; \n SELECT 9;",
        "-- comment;#comment;  \nseLect 'foo'; -- comment",
        f"""# comment; \nINSERT INTO {table_name} (city, country_id) VALUES ('Monterrey', '32');-- insert; \nSELECT 'ham';""",
        f"""
            -- this is a test; \n
            SELECT 'test'; -- a comment; \n
            INSERT INTO {table_name} (city, country_id) VALUES ('Ciudad de Mexico', '38'); # added cdmx; \n
            -- now let read the result; \n
            SELECT * from {table_name} where city='Ciudad de Mexico'; \n
            -- final comment;
        """,
        "SELECT 10;-- A; \nSELECT 11;",
        "SELECT 12;\n-- ;",
        "SELECT 13;-- ;",
        f"# dropping table;\n -- lets drop table; \n DROP TABLE IF EXISTS {table_name}; # delete table",
        "SELECT 'Mr. Ham /* kkk */'",
        """
        -- Test1
        SELECT "Test1";

        /*
        BUG#36126909 "Unread result found" exception/bad MySQLCursor.statement when query text contains code comments
        */

        /**/

        -- Test2
        SELECT "Test2"; # BUG#36126909 "Unread result found" exception/bad MySQLCursor.statement when query text contains code comments
        """,  # BUG#36126909 "Unread result found" exception/bad MySQLCursor.statement when query text contains code comments
    ]

    exps = [
        [(f"DROP TABLE IF EXISTS {table_name}", [])],
        [
            (
                f"CREATE TABLE {table_name} (id INT AUTO_INCREMENT PRIMARY KEY, city VARCHAR(20),country_id INT)",
                [],
            )
        ],
        [("SELECT 1", [(1,)])],
        [("SELECT 2", [(2,)])],
        [
            ("SELECT 2 + 1", [(3,)]),
            ("SELECT 4", [(4,)]),
        ],
        [
            (
                f"""INSERT INTO {table_name} (city, country_id) VALUES ('Guadalajara', '12')""",
                [],
            ),
            ("SELECT 5", [(5,)]),
        ],
        [("SELECT 6", [(6,)])],
        [("SELECT 7", [(7,)])],
        [("SELECT 8", [(8,)]), ("SELECT 9", [(9,)])],
        [("seLect 'foo'", [("foo",)])],
        [
            (
                f"INSERT INTO {table_name} (city, country_id) VALUES ('Monterrey', '32')",
                [],
            ),
            ("SELECT 'ham'", [("ham",)]),
        ],
        [
            ("SELECT 'test'", [("test",)]),
            (
                f"INSERT INTO {table_name} (city, country_id) VALUES ('Ciudad de Mexico', '38')",
                [],
            ),
            (
                f"SELECT * from {table_name} where city='Ciudad de Mexico'",
                [(3, "Ciudad de Mexico", 38)],
            ),
        ],
        [("SELECT 10", [(10,)]), ("SELECT 11", [(11,)])],
        [("SELECT 12", [(12,)])],
        [("SELECT 13", [(13,)])],
        [(f"DROP TABLE IF EXISTS {table_name}", [])],
        [("SELECT 'Mr. Ham /* kkk */'", [("Mr. Ham /* kkk */",)])],
        [
            ('SELECT "Test1"', [("Test1",)]),
            ('SELECT "Test2"', [("Test2",)]),
        ],
    ]

    @foreach_cnx()
    def test_comments_with_execute_multi(self):
        with self.cnx.cursor() as cur:
            for op, exp in zip(self.ops, self.exps):
                cur.execute(op, map_results=True)
                for (statement, result_set), (stmt_exp, fetch_exp) in zip(
                    cur.fetchsets(), exp
                ):
                    self.assertEqual(statement, stmt_exp)
                    self.assertListEqual(result_set, fetch_exp)


class BugOra35710145_async(tests.MySQLConnectorAioTestCase):
    """BUG#35710145: Bad MySQLCursor.statement and result when query text contains \
    code comments

    For a description see `test_bugs.BugOra35710145`.
    """

    @foreach_cnx_aio()
    async def test_comments_with_execute_multi(self):
        async with await self.cnx.cursor() as cur:
            for op, exp in zip(BugOra35710145.ops, BugOra35710145.exps):
                i = 0
                await cur.execute(op, map_results=True)
                try:
                    async for statement, result_set in cur.fetchsets():
                        stmt_exp, fetch_exp = exp[i]
                        self.assertEqual(statement, stmt_exp)
                        self.assertListEqual(result_set, fetch_exp)
                        i += 1
                except IndexError:
                    self.fail(f"Got more results than expected for query `{op}`")


class BugOra21390859(tests.MySQLConnectorTests):
    """BUG#21390859: STATEMENTS GET OUT OF SYNCH WITH RESULT SETS

    When including callproc (calling stored procedures) statements as part of a
    multi-query string while executing `cursor.execute(multi_stmt_query, multi=True)`
    the statements get out of sync with the result, that's to say, the statement-result
    mapping isn't correct, especially when a procedure produces multiple results.

    This issue is fixed as part of BUG#35710145, however, no relevant tests for this
    use case were added during the fix of BUG#35710145.

    With this patch, we extend the unit tests to cover the scenario where multi-result
    `callproc` statements are included in a multi-statement query.

    Acronyms
        rop: read operation
        wop: write operation
        1: it means the gotten result set isn't empty
        0: it means the gotten result set is empty
    """

    table_name = "BugOra21390859"

    use_case, use_case_exp = {}, {}

    use_case[
        1
    ] = f"""
    -- rop  wrop  proc_milti_read  proc_multi_insert;
    --  1    0       1 1 1 0               0        ;
    SELECT 76;
    INSERT INTO {table_name} (city, country_id) VALUES ('Ciudad de Mexico', '38');
    call {table_name}_multi_read(2);
    call {table_name}_multi_insert();
    """
    use_case_exp[1] = [
        ("SELECT 76", [(76,)]),
        (
            f"INSERT INTO {table_name} (city, country_id) VALUES ('Ciudad de Mexico', '38')",
            [],
        ),
        (f"call {table_name}_multi_read(2)", [(2,)]),
        (f"call {table_name}_multi_read(2)", [(3,)]),
        (f"call {table_name}_multi_read(2)", [("bar",)]),
        (f"call {table_name}_multi_read(2)", []),
        (f"call {table_name}_multi_insert()", []),
    ]

    use_case[
        2
    ] = f"""
    SELECT 'foo';
    INSERT INTO {table_name} (city, country_id) VALUES ('Ciudad de Mexico', '38');
    call {table_name}_multi_read(4);
    #  rop  wrop  proc_milti_read;
    --  1    0       1 1 1 0     ;
    """
    use_case_exp[2] = [
        ("SELECT 'foo'", [("foo",)]),
        (
            f"INSERT INTO {table_name} (city, country_id) VALUES ('Ciudad de Mexico', '38')",
            [],
        ),
        (f"call {table_name}_multi_read(4)", [(4,)]),
        (f"call {table_name}_multi_read(4)", [(5,)]),
        (f"call {table_name}_multi_read(4)", [("bar",)]),
        (f"call {table_name}_multi_read(4)", []),
    ]

    use_case[3] = use_case[1] + use_case[2]
    use_case_exp[3] = use_case_exp[1] + use_case_exp[2]

    use_case[4] = use_case[2] + use_case[1]
    use_case_exp[4] = use_case_exp[2] + use_case_exp[1]

    use_case[
        5
    ] = f"""
    -- one;
    call {table_name}_single_read(1);
    -- two;
    call {table_name}_single_read(2);
    -- three;
    call {table_name}_single_read(3);
    """
    use_case_exp[5] = [
        (f"call {table_name}_single_read(1)", [(1,)]),
        (f"call {table_name}_single_read(1)", []),
        (f"call {table_name}_single_read(2)", [(2,)]),
        (f"call {table_name}_single_read(2)", []),
        (f"call {table_name}_single_read(3)", [(3,)]),
        (f"call {table_name}_single_read(3)", []),
    ]

    # same as 6, but ending the query with a EOL comment
    use_case[6] = use_case[5] + "\n -- end;"
    use_case_exp[6] = use_case_exp[5][:]

    use_case[
        7
    ] = f"""
    SELECT 'Hello MySQL';
    INSERT INTO {table_name} (city, country_id) VALUES ('Colima', '84');
    SELECT 10; -- ten;
    # testing
    -- comment;
    INSERT INTO {table_name} (city, country_id) VALUES ('Tabasco', '0'); # added tabasco;
    -- comment;
    -- comment;
    -- comment;
    -- two;
    call {table_name}_read_and_insert();
    -- three;
    call {table_name}_multi_insert();
    -- two;
    """
    use_case_exp[7] = [
        (f"SELECT 'Hello MySQL'", [("Hello MySQL",)]),
        (
            f"INSERT INTO {table_name} (city, country_id) VALUES ('Colima', '84')",
            [],
        ),
        (f"SELECT 10", [(10,)]),
        (
            f"INSERT INTO {table_name} (city, country_id) VALUES ('Tabasco', '0')",
            [],
        ),
        (f"call {table_name}_read_and_insert()", [("Oracle",)]),
        (f"call {table_name}_read_and_insert()", [("MySQL",)]),
        (f"call {table_name}_read_and_insert()", []),
        (f"call {table_name}_multi_insert()", []),
    ]

    use_case[8] = use_case[6] + use_case[7]
    use_case_exp[8] = use_case_exp[6] + use_case_exp[7]

    use_case[9] = use_case[1] + use_case[5]
    use_case_exp[9] = use_case_exp[1] + use_case_exp[5]

    use_case[10] = use_case[3] + use_case[6]
    use_case_exp[10] = use_case_exp[3] + use_case_exp[6]

    use_case[
        11
    ] = f"""
    INSERT INTO {table_name} (city, country_id) VALUES ('Sonora', '33');
    -- callproc invokes procedures internally;
    CALL {table_name}_callproc();
    """
    use_case_exp[11] = [
        (
            f"INSERT INTO {table_name} (city, country_id) VALUES ('Sonora', '33')",
            [],
        ),
        (f"CALL {table_name}_callproc()", [(1,)]),
        (f"CALL {table_name}_callproc()", [(2,)]),
        (f"CALL {table_name}_callproc()", [("bar",)]),
        (f"CALL {table_name}_callproc()", []),
    ]

    use_case[
        12
    ] = f"""
    INSERT INTO {table_name} (city, country_id) VALUES ('Tamaulipas', '82');
    INSERT INTO {table_name} (city, country_id) VALUES ('Chihuahua', '3');
    -- write operations;
    SELECT ':D';
    """
    use_case_exp[12] = [
        (
            f"INSERT INTO {table_name} (city, country_id) VALUES ('Tamaulipas', '82')",
            [],
        ),
        (
            f"INSERT INTO {table_name} (city, country_id) VALUES ('Chihuahua', '3')",
            [],
        ),
        ("SELECT ':D'", [(":D",)]),
    ]

    use_case[13] = use_case[12] + use_case[11]
    use_case_exp[13] = use_case_exp[12] + use_case_exp[11]

    def setUp(self):
        with connection.MySQLConnection(**tests.get_mysql_config()) as cnx:
            cnx.cmd_query(f"DROP PROCEDURE IF EXISTS {self.table_name}_multi_read")
            cnx.cmd_query(f"DROP PROCEDURE IF EXISTS {self.table_name}_multi_insert")
            cnx.cmd_query(f"DROP PROCEDURE IF EXISTS {self.table_name}_single_read")
            cnx.cmd_query(f"DROP PROCEDURE IF EXISTS {self.table_name}_read_and_insert")
            cnx.cmd_query(f"DROP PROCEDURE IF EXISTS {self.table_name}_callproc")
            cnx.cmd_query(f"DROP TABLE IF EXISTS {self.table_name}")
            cnx.cmd_query(
                f"""
                CREATE PROCEDURE {self.table_name}_single_read(val integer)
                BEGIN
                    SELECT val;
                END;
            """
            )
            cnx.cmd_query(
                f"""
                CREATE PROCEDURE {self.table_name}_multi_read(val integer)
                BEGIN
                    SELECT val;
                    SELECT val + 1;
                    SELECT 'bar';
                END;
            """
            )
            cnx.cmd_query(
                f"""
                CREATE PROCEDURE {self.table_name}_multi_insert()
                BEGIN
                    INSERT INTO {self.table_name} (city, country_id) VALUES ('Chiapas', '33');
                    INSERT INTO {self.table_name} (city, country_id) VALUES ('Yucatan', '28');
                    INSERT INTO {self.table_name} (city, country_id) VALUES ('Oaxaca', '13');
                END;
            """
            )
            cnx.cmd_query(
                f"""
                CREATE PROCEDURE {self.table_name}_read_and_insert()
                BEGIN
                    INSERT INTO {self.table_name} (city, country_id) VALUES ('CCC', '33');
                    SELECT 'Oracle';
                    INSERT INTO {self.table_name} (city, country_id) VALUES ('AAA', '44');
                    INSERT INTO {self.table_name} (city, country_id) VALUES ('BBB', '99');
                    SELECT 'MySQL';
                END;
            """
            )
            cnx.cmd_query(
                f"""
                CREATE PROCEDURE {self.table_name}_callproc()
                BEGIN
                    CALL {self.table_name}_multi_read(1);
                    CALL {self.table_name}_multi_insert();
                END;
            """
            )
            cnx.cmd_query(
                f"CREATE TABLE {self.table_name} (id INT AUTO_INCREMENT PRIMARY KEY, city VARCHAR(20),country_id INT)"
            )

    def tearDown(self) -> None:
        with connection.MySQLConnection(**tests.get_mysql_config()) as cnx:
            cnx.cmd_query(f"DROP PROCEDURE IF EXISTS {self.table_name}_multi_read")
            cnx.cmd_query(f"DROP PROCEDURE IF EXISTS {self.table_name}_multi_insert")
            cnx.cmd_query(f"DROP PROCEDURE IF EXISTS {self.table_name}_single_read")
            cnx.cmd_query(f"DROP PROCEDURE IF EXISTS {self.table_name}_read_and_insert")
            cnx.cmd_query(f"DROP PROCEDURE IF EXISTS {self.table_name}_callproc")
            cnx.cmd_query(f"DROP TABLE IF EXISTS {self.table_name}")

    @foreach_cnx()
    def test_multi_stmts_with_callproc_out_of_sync(self):
        with self.cnx.cursor() as cur:
            for i in self.use_case:
                cur.execute(self.use_case[i], map_results=True)
                for (statement, result_set), (stmt_exp, fetch_exp) in zip(
                    cur.fetchsets(), self.use_case_exp[i]
                ):
                    self.assertEqual(statement, stmt_exp)
                    self.assertListEqual(result_set, fetch_exp)


class BugOra21390859_async(tests.MySQLConnectorAioTestCase):
    """BUG#21390859: STATEMENTS GET OUT OF SYNCH WITH RESULT SETS

    For a description see `test_bugs.BugOra21390859`.
    """

    def setUp(self) -> None:
        self.bug_21390859 = BugOra21390859()
        self.bug_21390859.setUp()

    def tearDown(self) -> None:
        self.bug_21390859.tearDown()

    @foreach_cnx_aio()
    async def test_multi_stmts_with_callproc_out_of_sync(self):
        async with await self.cnx.cursor() as cur:
            for i in self.bug_21390859.use_case:
                exp_list = self.bug_21390859.use_case_exp[i]
                j = 0
                try:
                    await cur.execute(self.bug_21390859.use_case[i], map_results=True)
                    async for statement, result_set in cur.fetchsets():
                        stmt_exp, fetch_exp = exp_list[j]
                        self.assertEqual(statement, stmt_exp)
                        self.assertListEqual(result_set, fetch_exp)
                        j += 1
                except IndexError:
                    self.fail(
                        "Got more results than expected "
                        f"for query {self.bug_21390859.use_case[i]}"
                    )


class BugOra36476195(tests.MySQLConnectorTests):
    """BUG#36476195: Incorrect escaping in pure Python mode if sql_mode includes NO_BACKSLASH_ESCAPES

    When NO_BACKSLASH_ESCAPES is included with similar other options in the sql_mode parameter,
    the client escapes strings as if NO_BACKSLASH_ESCAPES mode was not active. This issue leads
    to SQL Injections from parameters in cursor execution methods.

    This patch fixes the issue by adding proper conditional checks during statement conversions
    to check if NO_BACKSLASH_ESCAPES is included with/without other options in the sql_mode
    parameter and ensure correct string escaping is being done during conversion.
    """

    table_name = "BugOra36476195"

    injected_param = "' UNION SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA #"

    injected_param_multi = "SELECT %s; select ''%s AS a_str"

    injected_param_batch_insert = (
        f"INSERT INTO {table_name} (val1, val2, val3) VALUES (%s, %s, %s)"
    )
    injected_param_batch_insert_values = [
        (1000, "def", "ghi"),
        (1001, "'SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA))'\\#'", "jkl"),
    ]

    # The expected result of the above statement which confirms the prevention of sql injection
    expected_result = [
        ("' UNION SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA #",)
    ]
    expected_result_multi = [expected_result, [("'A STRING",)]]
    expected_result_batch_insert = [
        (1000, "def", "ghi"),
        (1001, "'SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA))'\\#'", "jkl"),
    ]

    def setUp(self):
        with mysql.connector.connect(**tests.get_mysql_config()) as cnx:
            with cnx.cursor() as cur:
                cur.execute(
                    f"CREATE TABLE {self.table_name} (val1 INT, val2 VARCHAR(100), val3 VARCHAR(100))"
                )

    def tearDown(self):
        with mysql.connector.connect(**tests.get_mysql_config()) as cnx:
            with cnx.cursor() as cur:
                cur.execute(f"DROP TABLE IF EXISTS {self.table_name}")

    @foreach_cnx()
    def test_execute_with_default_sql_mode(self):
        with self.cnx.cursor() as cur:
            # basic check
            cur.execute("SELECT %s", (self.injected_param,))
            self.assertEqual(self.expected_result, cur.fetchall())
            # bytes passed in param check
            cur.execute("SELECT %s", (self.injected_param.encode(),))
            self.assertEqual(self.expected_result, cur.fetchall())
            # dict passed in param check
            cur.execute(
                "SELECT %(injected_param)s", {"injected_param": self.injected_param}
            )
            self.assertEqual(self.expected_result, cur.fetchall())
            # execute multi check
            cur.execute(self.injected_param_multi, (self.injected_param, "A STRING"))
            for idx, (_, result_set) in enumerate(cur.fetchsets()):
                self.assertEqual(self.expected_result_multi[idx], result_set)
            # batch insert check
            cur.executemany(
                self.injected_param_batch_insert,
                self.injected_param_batch_insert_values,
            )
            cur.execute(f"SELECT * FROM {self.table_name}")
            self.assertEqual(self.expected_result_batch_insert, cur.fetchall())

    @cnx_config(sql_mode="NO_BACKSLASH_ESCAPES")
    @foreach_cnx()
    def test_execute_with_only_no_backslash_escapes_in_sql_mode(self):
        with self.cnx.cursor() as cur:
            # basic check
            cur.execute("SELECT %s", (self.injected_param,))
            self.assertEqual(self.expected_result, cur.fetchall())
            # bytes passed in param check
            cur.execute("SELECT %s", (self.injected_param.encode(),))
            self.assertEqual(self.expected_result, cur.fetchall())
            # dict passed in param check
            cur.execute(
                "SELECT %(injected_param)s", {"injected_param": self.injected_param}
            )
            self.assertEqual(self.expected_result, cur.fetchall())
            # execute multi check
            cur.execute(self.injected_param_multi, (self.injected_param, "A STRING"))
            for idx, (_, result_set) in enumerate(cur.fetchsets()):
                self.assertEqual(self.expected_result_multi[idx], result_set)
            # batch insert check
            cur.executemany(
                self.injected_param_batch_insert,
                self.injected_param_batch_insert_values,
            )
            cur.execute(f"SELECT * FROM {self.table_name}")
            self.assertEqual(self.expected_result_batch_insert, cur.fetchall())

    @cnx_config(sql_mode="STRICT_TRANS_TABLES,NO_BACKSLASH_ESCAPES")
    @foreach_cnx()
    def test_execute_with_multiple_options_in_sql_mode(self):
        with self.cnx.cursor() as cur:
            # basic check
            cur.execute("SELECT %s", (self.injected_param,))
            self.assertEqual(self.expected_result, cur.fetchall())
            # bytes passed in param check
            cur.execute("SELECT %s", (self.injected_param.encode(),))
            self.assertEqual(self.expected_result, cur.fetchall())
            # dict passed in param check
            cur.execute(
                "SELECT %(injected_param)s", {"injected_param": self.injected_param}
            )
            self.assertEqual(self.expected_result, cur.fetchall())
            # execute multi check
            cur.execute(self.injected_param_multi, (self.injected_param, "A STRING"))
            for idx, (_, result_set) in enumerate(cur.fetchsets()):
                self.assertEqual(self.expected_result_multi[idx], result_set)
            # batch insert check
            cur.executemany(
                self.injected_param_batch_insert,
                self.injected_param_batch_insert_values,
            )
            cur.execute(f"SELECT * FROM {self.table_name}")
            self.assertEqual(self.expected_result_batch_insert, cur.fetchall())


class BugOra36476195_async(tests.MySQLConnectorAioTestCase):
    """BUG#36476195: Incorrect escaping in pure Python mode if sql_mode includes NO_BACKSLASH_ESCAPES

    For a description see `test_bugs.BugOra36476195`.
    """

    expected_result_bytes = [
        (b"' UNION SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA #",)
    ]
    expected_result_multi_bytes = [expected_result_bytes, [(b"'A STRING",)]]
    expected_result_batch_insert_bytes = [
        (1000, b"def", b"ghi"),
        (1001, b"'SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA))'\\#'", b"jkl"),
    ]

    def setUp(self):
        self.bug_36476195 = BugOra36476195()
        self.table_name = self.bug_36476195.table_name
        self.injected_param = self.bug_36476195.injected_param
        self.injected_param_multi = self.bug_36476195.injected_param_multi
        self.injected_param_batch_insert = self.bug_36476195.injected_param_batch_insert
        self.injected_param_batch_insert_values = (
            self.bug_36476195.injected_param_batch_insert_values
        )
        self.expected_result = self.bug_36476195.expected_result
        self.expected_result_multi = self.bug_36476195.expected_result_multi
        self.expected_result_batch_insert = (
            self.bug_36476195.expected_result_batch_insert
        )
        self.bug_36476195.setUp()

    def tearDown(self):
        self.bug_36476195.tearDown()

    @cnx_config(use_unicode=False)
    @foreach_cnx_aio()
    async def test_execute_with_default_sql_mode_unicode_as_false(self):
        async with await self.cnx.cursor() as cur:
            # basic check
            await cur.execute("SELECT %s", (self.injected_param,))
            self.assertEqual(self.expected_result_bytes, await cur.fetchall())
            # bytes passed in param check
            await cur.execute("SELECT %s", (self.injected_param.encode(),))
            self.assertEqual(self.expected_result_bytes, await cur.fetchall())
            # dict passed in param check
            await cur.execute(
                "SELECT %(injected_param)s", {"injected_param": self.injected_param}
            )
            self.assertEqual(self.expected_result_bytes, await cur.fetchall())
            # execute multi check
            await cur.executemulti(
                self.injected_param_multi, (self.injected_param, "A STRING")
            )
            idx = 0
            async for _, res in cur.fetchsets():
                self.assertEqual(self.expected_result_multi_bytes[idx], res)
                idx += 1
            # execute many check
            await cur.executemany(
                self.injected_param_batch_insert,
                self.injected_param_batch_insert_values,
            )
            await cur.execute(f"SELECT * FROM {self.table_name}")
            self.assertEqual(
                self.expected_result_batch_insert_bytes, await cur.fetchall()
            )

    @foreach_cnx_aio()
    async def test_execute_with_default_sql_mode(self):
        async with await self.cnx.cursor() as cur:
            # basic check
            await cur.execute("SELECT %s", (self.injected_param,))
            self.assertEqual(self.expected_result, await cur.fetchall())
            # bytes passed in param check
            await cur.execute("SELECT %s", (self.injected_param.encode(),))
            self.assertEqual(self.expected_result, await cur.fetchall())
            # dict passed in param check
            await cur.execute(
                "SELECT %(injected_param)s", {"injected_param": self.injected_param}
            )
            self.assertEqual(self.expected_result, await cur.fetchall())
            # execute multi check
            await cur.executemulti(
                self.injected_param_multi, (self.injected_param, "A STRING")
            )
            idx = 0
            async for _, res in cur.fetchsets():
                self.assertEqual(self.expected_result_multi[idx], res)
                idx += 1
            # execute many check
            await cur.executemany(
                self.injected_param_batch_insert,
                self.injected_param_batch_insert_values,
            )
            await cur.execute(f"SELECT * FROM {self.table_name}")
            self.assertEqual(self.expected_result_batch_insert, await cur.fetchall())

    @cnx_config(sql_mode="NO_BACKSLASH_ESCAPES")
    @foreach_cnx_aio()
    async def test_execute_with_only_no_backslash_escapes_in_sql_mode(self):
        async with await self.cnx.cursor() as cur:
            # basic check
            await cur.execute("SELECT %s", (self.injected_param,))
            self.assertEqual(self.expected_result, await cur.fetchall())
            # bytes passed in param check
            await cur.execute("SELECT %s", (self.injected_param.encode(),))
            self.assertEqual(self.expected_result, await cur.fetchall())
            # dict passed in param check
            await cur.execute(
                "SELECT %(injected_param)s", {"injected_param": self.injected_param}
            )
            self.assertEqual(self.expected_result, await cur.fetchall())
            # execute multi check
            await cur.executemulti(
                self.injected_param_multi, (self.injected_param, "A STRING")
            )
            idx = 0
            async for _, res in cur.fechsets():
                self.assertEqual(self.expected_result_multi[idx], res)
                idx += 1
            # execute many check
            await cur.executemany(
                self.injected_param_batch_insert,
                self.injected_param_batch_insert_values,
            )
            await cur.execute(f"SELECT * FROM {self.table_name}")
            self.assertEqual(self.expected_result_batch_insert, await cur.fetchall())

    @cnx_config(sql_mode="STRICT_TRANS_TABLES,NO_BACKSLASH_ESCAPES")
    @foreach_cnx_aio()
    async def test_execute_with_multiple_options_in_sql_mode(self):
        async with await self.cnx.cursor() as cur:
            # basic check
            await cur.execute("SELECT %s", (self.injected_param,))
            self.assertEqual(self.expected_result, await cur.fetchall())
            # bytes passed in param check
            await cur.execute("SELECT %s", (self.injected_param.encode(),))
            self.assertEqual(self.expected_result, await cur.fetchall())
            # dict passed in param check
            await cur.execute(
                "SELECT %(injected_param)s", {"injected_param": self.injected_param}
            )
            self.assertEqual(self.expected_result, await cur.fetchall())
            # execute multi check
            await cur.executemulti(
                self.injected_param_multi, (self.injected_param, "A STRING")
            )
            idx = 0
            async for _, res in cur.fetchsets():
                self.assertEqual(self.expected_result_multi[idx], res)
                idx += 1
            # execute many check
            await cur.executemany(
                self.injected_param_batch_insert,
                self.injected_param_batch_insert_values,
            )
            await cur.execute(f"SELECT * FROM {self.table_name}")
            self.assertEqual(self.expected_result_batch_insert, await cur.fetchall())


class BugOra36289767_async(tests.MySQLConnectorAioTestCase):
    """BUG#36289767: MySQLCursorBufferedRaw do not skip conversion

    When parameters raw with buffered as True are passed through the cursor, the
    results returned by the fetch statements doesnot skip type conversion. Due to
    this issue python type converted data is returned instead of bytestrings or
    bytes. This issue is observed in both synchronous cursor types.

    This patch fixes the issue by testing if the data returned is of bytes type
    when raw parameter is passed as True, this patch also improves data integrity
    throughout the cursor subtypes.
    """

    table_name = "BugOra36289767"

    # Expected results if raw param is passed as True through any cursor
    fetchone_exp_raw = (
        b"21474836",
        b"120",
        b"32333",
        b"8388605",
        b"92413262543",
        b"123.32",
        b"13.0",
        b"9339.8388607",
        b"abcd",
        b"MySQL \xf0\x9f\x90\xac",
        b"this is a BLOB data",
        b"TINYBLOB",
        b"medium BLOB data",
        b"this is a long BLOB data . . .",
        b"This is a simple TEXT input",
        b"This is a TINYTEXT",
        b"This is a MEDIUMTEXT input",
        b"This is a very LONGTEXT data . . .",
        b"\r",
        b"1234",
        b"1213",
        b"1999-06-16",
        b"36:13:14",
        b"2019-02-04 10:36:20",
        b"2023-03-06 09:36:20",
        b"2024",
        b"\x00\x00\x00\x00\x01\x01\x00\x00\x003333335@\x9a\x99\x99\x99\x99\x19A@",
    )

    def setUp(self) -> None:
        values = (
            "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s",
            "%s, %s, %s, %s, %s, %s, %s, %s, B'1101', %s",
            "%s, %s, %s, %s, %s, %s, POINT(21.2, 34.2)",
        )
        params = """
            My_Int, My_Tinyint, My_Smallint, My_Mediumint, My_Bigint, My_Decimal,
            My_Float, My_Double, My_Char, My_Varchar, My_Blob, My_Tinyblob, My_Mediumblob,
            My_Longblob, My_Text, My_Tinytext, My_Mediumtext, My_Longtext, My_Bit,
            My_Binary, My_Varbinary, My_Date, My_Time, My_Datetime, My_Timestamp,
            My_Year, My_Geometry
        """
        insert_stmt = (
            f"INSERT INTO {self.table_name} ({params}) VALUES ({', '.join(values)});"
        )
        data = [
            21474836,
            120,
            32333,
            8388605,
            92413262543,
            123.32,
            13.0,
            9339.8388607,
            "abcd",
            "MySQL 🐬",
            b"this is a BLOB data",
            b"TINYBLOB",
            b"medium BLOB data",
            b"this is a long BLOB data . . .",
            "This is a simple TEXT input",
            "This is a TINYTEXT",
            "This is a MEDIUMTEXT input",
            "This is a very LONGTEXT data . . .",
            "1234",
            b"1213",
            date(day=16, month=6, year=1999),
            timedelta(hours=12, minutes=13, seconds=14, days=1),
            datetime(2019, 2, 4, 10, 36, 20),
            datetime(2023, 3, 6, 9, 36, 20, tzinfo=timezone.utc),
            2024,
        ]

        with mysql.connector.connect(**tests.get_mysql_config()) as cnx:
            with cnx.cursor() as cur:
                cur.execute(f"DROP TABLE IF EXISTS {self.table_name}")
                cur.execute(
                    f"""
                    CREATE TABLE {self.table_name} (
                        My_Int INT,
                        My_Tinyint TINYINT,
                        My_Smallint SMALLINT,
                        My_Mediumint MEDIUMINT,
                        My_Bigint BIGINT,
                        My_Decimal DECIMAL(5,2),
                        My_Float FLOAT(3,1),
                        My_Double DOUBLE,
                        My_Char CHAR(5),
                        My_Varchar VARCHAR(100),
                        My_Blob BLOB,
                        My_Tinyblob TINYBLOB,
                        My_Mediumblob MEDIUMBLOB,
                        My_Longblob LONGBLOB,
                        My_Text TEXT,
                        My_Tinytext TINYTEXT,
                        My_Mediumtext MEDIUMTEXT,
                        My_Longtext LONGTEXT,
                        My_Bit BIT(4),
                        My_Binary BINARY(4),
                        My_Varbinary VARBINARY(4),
                        My_Date DATE,
                        My_Time TIME,
                        My_Datetime DATETIME,
                        My_Timestamp TIMESTAMP,
                        My_Year YEAR,
                        My_Geometry GEOMETRY
                    )"""
                )
                cur.execute(insert_stmt, data)
            cnx.commit()

    def tearDown(self) -> None:
        with mysql.connector.connect(**tests.get_mysql_config()) as cnx:
            cnx.cmd_query(f"DROP TABLE IF EXISTS {self.table_name}")

    @foreach_cnx_aio()
    async def test_buffered_raw_cursor(self) -> None:
        async with await self.cnx.cursor(buffered=True, raw=True) as cur:
            await cur.execute(f"SELECT * from {self.table_name}")
            self.assertEqual((self.fetchone_exp_raw), await cur.fetchone())
            await cur.execute(f"SELECT * from {self.table_name}")
            self.assertEqual(
                [
                    (self.fetchone_exp_raw),
                ],
                await cur.fetchall(),
            )


class BugOra37013057(tests.MySQLConnectorTests):
    """BUG#37013057: mysql-connector-python Parameterized query SQL injection

    Malicious strings can be injected when utilizing
    dictionary-based query parameterization via the
    `cursor.execute()` API command and the C-based
    implementation of the connector.

    This patch fixes the injection issue.
    """

    table_name = "BugOra37013057"

    cur_flavors = [
        {},
        {"prepared": True},
        {"raw": True},
        {"buffered": True},
        {"dictionary": True},
    ]

    sql_dict = f"INSERT INTO {table_name}(username, password, city) VALUES (%(username)s, %(password)s, %(city)s)"
    sql_tuple = (
        f"INSERT INTO {table_name}(username, password, city) VALUES (%s, %s, %s)"
    )

    cases = [
        {
            "values_dict": {
                "username": "%(password)s",
                "password": ", sleep(10));--",
                "city": "Montevideo",
            },
            "values_tuple": ("%(password)s", ", sleep(10));--", "Montevideo"),
        },
        {
            "values_dict": {
                "username": "%(password)s",
                "password": ", curdate());",
                "city": "Rio",
            },
            "values_tuple": ("%(password)s", ", curdate());", "Rio"),
        },
        {
            "values_dict": {
                "username": "%(password)s",
                "password": "%(city)s",
                "city": ", database());",
            },
            "values_tuple": ("%(password)s", "%(city)s", ", database());"),
        },
    ]

    def setUp(self):
        with mysql.connector.connect(**tests.get_mysql_config()) as cnx:
            with cnx.cursor() as cur:
                cur.execute(
                    f"CREATE TABLE {self.table_name}"
                    "(username varchar(50), password varchar(50), city varchar(50))"
                )

    def tearDown(self):
        with mysql.connector.connect(**tests.get_mysql_config()) as cnx:
            with cnx.cursor() as cur:
                cur.execute(f"DROP TABLE IF EXISTS {self.table_name}")

    def _prepare_cur_dict_res(self, case):
        if isinstance(case["values"], dict):
            return case["values_dict"]

    def _run_execute(self, dict_based=True, cur_config={}):
        sql = self.sql_dict if dict_based else self.sql_tuple
        for case in self.cases:
            if dict_based:
                values = case["values_dict"]
            else:
                values = case["values_tuple"]

            if "dictionary" in cur_config:
                exp_res = case["values_dict"].copy()
            elif "raw" in cur_config:
                exp_res = tuple([x.encode() for x in case["values_tuple"]])
            else:
                exp_res = case["values_tuple"]

            with self.cnx.cursor(**cur_config) as cur:
                cur.execute(sql, values)
                cur.execute(f"select * from {self.table_name}")
                res = cur.fetchone()
                cur.execute(f"TRUNCATE TABLE {self.table_name}")
            self.assertEqual(res, exp_res)

    @foreach_cnx()
    def test_execute_dict_based_injection(self):
        for cur_config in self.cur_flavors:
            self._run_execute(dict_based=True, cur_config=cur_config)

    @foreach_cnx()
    def test_execute_tuple_based_injection(self):
        for cur_config in self.cur_flavors:
            self._run_execute(dict_based=False, cur_config=cur_config)


class BugOra37013057_async(tests.MySQLConnectorAioTestCase):
    """BUG#37013057: mysql-connector-python Parameterized query SQL injection

    For a description see `test_bugs.BugOra37013057`.
    """

    def setUp(self) -> None:
        self.bug_37013057 = BugOra37013057()
        self.bug_37013057.setUp()

    def tearDown(self) -> None:
        self.bug_37013057.tearDown()

    async def _run_execute(self, dict_based=True, cur_config={}):
        sql = self.bug_37013057.sql_dict if dict_based else self.bug_37013057.sql_tuple
        for case in self.bug_37013057.cases:
            if dict_based:
                values = case["values_dict"]
            else:
                values = case["values_tuple"]

            if "dictionary" in cur_config:
                exp_res = case["values_dict"].copy()
            elif "raw" in cur_config:
                exp_res = tuple([x.encode() for x in case["values_tuple"]])
            else:
                exp_res = case["values_tuple"]

            async with await self.cnx.cursor(**cur_config) as cur:
                await cur.execute(sql, values)
                await cur.execute(f"select * from {self.bug_37013057.table_name}")
                res = await cur.fetchone()
                await cur.execute(f"TRUNCATE TABLE {self.bug_37013057.table_name}")
            self.assertEqual(res, exp_res)

    @foreach_cnx_aio()
    async def test_execute_dict_based_injection(self):
        for cur_config in self.bug_37013057.cur_flavors:
            await self._run_execute(dict_based=True, cur_config=cur_config)

    @foreach_cnx_aio()
    async def test_execute_tuple_based_injection(self):
        for cur_config in self.bug_37013057.cur_flavors:
            await self._run_execute(dict_based=False, cur_config=cur_config)


class BugOra36765200(tests.MySQLConnectorTests):
    """BUG#367652000: python mysql connector 8.3.0 raise %-.100s:%u when input a wrong host

    Unformatted error message is being shown to the client if an unreachable host is passed
    via the connection arguments while connecting with a MySQL server using pure-python
    implementation of Connector/Python.

    This patch fixes this issue by changing the error log message structure.
    """

    def test_incorrect_host_err_msg(self):
        config = tests.get_mysql_config()
        config["host"] = "foo.bar"
        config["unix_socket"] = None
        cnx = MySQLConnection

        self.assertRaises(errors.InterfaceError, cnx, **config)
        try:
            with cnx(**config) as _:
                pass
        except errors.InterfaceError as err:
            self.assertNotIn(
                "%-.100s:%u",
                str(err),
                "Error message cannot contain unstructured bind address",
            )


class BugOra37145655(tests.MySQLConnectorTests):
    """BUG#37145655: MySQL Connector/Python Configuration Files RCE"""

    def test_read_optionfiles(self):
        option_file_dir = os.path.join("tests", "data", "option_files")
        opt_file = os.path.join(option_file_dir, "bug_37145655.cnf")
        exp = {
            "user": "root",
            "password": "mypass",
            "database": "cpydata",
            "port": 10000,
            "failover": [
                {
                    "host": "127.0.1.2",
                    "port": 3306,
                    "user": "root",
                    "priority": 80,
                },
                {
                    "host": "127.0.1.5",
                    "port": 2450,
                    "user": "root_123",
                    "priority": 10,
                },
            ],
        }
        self.assertEqual(
            exp,
            read_option_files(option_files=opt_file, option_groups=["correct_config"]),
        )
        exp.pop("failover")
        exp["unix_socket"] = "unix_socket_path_for_bug37145655"
        self.assertEqual(
            exp,
            read_option_files(
                option_files=opt_file, option_groups=["correct_config_with_unix_socket"]
            ),
        )
        self.assertEqual(
            exp,
            read_option_files(
                option_files=opt_file, option_groups=["correct_config_with_socket"]
            ),
        )
        del exp["unix_socket"]
        exp["port"] = "int(10000)"
        exp["allow_local_infile"] = "__import__('os').system('whoami')"
        self.assertEqual(
            exp,
            read_option_files(
                option_files=opt_file, option_groups=["incorrect_config"]
            ),
        )
        with self.assertRaises(
            (errors.InterfaceError, TypeError),
        ) as _:
            with mysql.connector.connect(
                read_default_file=opt_file,
                option_groups=["incorrect_config"],
            ) as _:
                pass


class BugOra36922645(tests.MySQLConnectorTests):
    """BUG#36922645: Option `connection_timeout` is overwritten and works as "query" timeout instead

    The `connection_timeout` option is working as "the time taken to execute a query by Connector/Python
    inside an established connection" instead of "the time taken to establish a connection".

    This patch fixes this issue by seperating the use of connection_timeout and introducing read/write timeouts
    as a part of WL#16381.
    """

    def test_connection_timeout(self):
        config = tests.get_mysql_config()
        config["unix_socket"] = None
        config["use_pure"] = True
        config["connection_timeout"] = 3
        try:
            with mysql.connector.connect(**config) as cnx:
                # check that connection_timeout is not working as query timeout
                cnx.cmd_query("SELECT SLEEP(5)")
        except Exception as err:
            self.fail(err)


class BugOra37275524(tests.MySQLConnectorTests):
    """BUG#37275524: Exception is not interpreted properly on prepared statements when C extension is in use

    InterfaceError instead of IntegrityError is being interpreted by the connector when a server-side exception
    is being raised while working with prepared statements using C-Extension.

    This patch fixes this issue by ensuring that correct exception structure is being maintained while forwarding
    the exception from C-API to the connector interface.
    """

    table_name = "Bug37275524"

    def test_bug37275524(self):
        with mysql.connector.connect(**tests.get_mysql_config()) as cnx:
            for is_prepared in (True, False):
                with cnx.cursor(prepared=is_prepared) as cur:
                    with self.assertRaises(errors.IntegrityError) as _:
                        cur.execute(f"DROP TABLE IF EXISTS {self.table_name}")
                        cur.execute(f"CREATE TABLE {self.table_name} (id INT PRIMARY KEY)")
                        cur.execute(f"INSERT INTO {self.table_name} (id) VALUES (1)")
                        cur.execute(f"INSERT INTO {self.table_name} (id) VALUES (1)")

class BugOra37410052(tests.MySQLConnectorTests):
    """BUG#37410052: Wrong exception message being shown when ConnectionRefusedError is raised
    by the client

    ConnectionRefusedError is not being correctly formatted when being raised by the
    client while connecting with a MySQL server using pure-python implementation of
    Connector/Python.

    This patch fixes this issue by changing the error log message structure.
    """

    def test_incorrect_host_err_msg(self):
        config = tests.get_mysql_config()
        config["port"] = 4875
        config["use_pure"] = True
        config["unix_socket"] = None
        cnx = MySQLConnection

        self.assertRaises(errors.InterfaceError, cnx, **config)
        try:
            with cnx(**config) as _:
                pass
        except errors.InterfaceError as err:
            self.assertNotIn(
                "%-.100s",
                str(err),
                "Error message cannot contain unstructured bind address",
            )
