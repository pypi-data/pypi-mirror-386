# Copyright (c) 2023, 2025, Oracle and/or its affiliates.
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


"""Test module for authentication."""

import getpass
import importlib
import itertools
import logging
import os
import pathlib
import pkgutil
import subprocess
import time
import unittest

import mysql.connector.aio

import tests

from tests import MySQLConnectorAioTestCase, MySQLConnectorTests, foreach_cnx_aio

import mysql.connector
import mysql.connector.aio.plugins as plugins

from mysql.connector.aio import authentication
from mysql.connector.aio.plugins import get_auth_plugin
from mysql.connector.errors import (
    DatabaseError,
    InterfaceError,
    NotSupportedError,
    OperationalError,
    ProgrammingError,
)

try:
    import cryptography
except ImportError:
    cryptography = None

try:
    import gssapi

    from mysql.connector.aio.plugins.authentication_kerberos_client import (
        MySQLKerberosAuthPlugin,
    )
except ImportError:
    gssapi = None
    MySQLKerberosAuthPlugin = None

try:
    import oci
except ImportError:
    oci = None

try:
    import fido2
except ImportError:
    fido2 = None

try:
    from mysql.connector.aio.connection_cext import HAVE_CMYSQL, CMySQLConnection
except ImportError:
    # Test without C Extension
    CMySQLConnection = None
    HAVE_CMYSQL = False

LOGGER = logging.getLogger(tests.LOGGER_NAME)

_PLUGINS_DEPENDENCIES = {
    "authentication_kerberos_client": (gssapi,),
    "authentication_ldap_sasl_client": (gssapi,),
    "authentication_oci_client": (cryptography, oci),
    "authentication_webauthn_client": (fido2,),
}


class AuthenticationModuleTests(MySQLConnectorTests):
    """Tests globals and functions of the authentication module."""

    def test_get_auth_plugin(self):
        self.assertRaises(NotSupportedError, get_auth_plugin, "spam")
        self.assertRaises(NotSupportedError, get_auth_plugin, "")

        # Test using standard plugins
        plugin_list = []
        plugin_classes = {}
        for module in pkgutil.iter_modules(plugins.__path__):
            deps = _PLUGINS_DEPENDENCIES.get(module.name)
            if deps and not all(deps):
                LOGGER.warning(
                    f"{module.name} authentication plugin has missing dependencies"
                )
                continue
            else:
                plugin_list.append(module.name)

            plugin_module = importlib.import_module(
                f"mysql.connector.aio.plugins.{module.name}"
            )
            if hasattr(plugin_module, "AUTHENTICATION_PLUGIN_CLASS"):
                plugin_classes[module.name] = getattr(
                    plugin_module, plugin_module.AUTHENTICATION_PLUGIN_CLASS
                )
        for plugin_name in plugin_list:
            self.assertEqual(
                plugin_classes[plugin_name],
                authentication.get_auth_plugin(plugin_name),
                "Failed getting class for {0}".format(plugin_name),
            )


class MySQLNativePasswordAuthPluginTests(MySQLConnectorTests):
    """Tests authentication.MySQLNativePasswordAuthPlugin."""

    def setUp(self):
        self.plugin_class = get_auth_plugin("mysql_native_password")

    def test_class(self):
        auth_plugin = self.plugin_class(username="dummy", password="s3cr3t")
        self.assertEqual("mysql_native_password", auth_plugin.name)
        self.assertEqual(False, auth_plugin.requires_ssl)

    def test_prepare_password(self):
        auth_plugin = self.plugin_class(username=None, password="spam")
        self.assertRaises(InterfaceError, auth_plugin._prepare_password, auth_data=None)

        auth_plugin = self.plugin_class(username=None, password="spam")  # too long
        self.assertRaises(
            InterfaceError, auth_plugin._prepare_password, auth_data=123456
        )

        empty = b""
        auth_data = (
            b"\x2d\x3e\x33\x25\x5b\x7d\x25\x3c\x40\x6b"
            b"\x7b\x47\x30\x5b\x57\x25\x51\x48\x55\x53"
        )
        auth_response = (
            b"\x73\xb8\xf0\x4b\x3a\xa5\x7c\x46\xb9\x84"
            b"\x90\x50\xab\xc0\x3a\x0f\x8f\xad\x51\xa3"
        )

        auth_plugin = self.plugin_class(username=None, password=None)
        self.assertEqual(empty, auth_plugin._prepare_password("\x3f" * 20))

        auth_plugin = self.plugin_class(username=None, password="spam")
        self.assertEqual(auth_response, auth_plugin._prepare_password(auth_data))
        self.assertEqual(auth_response, auth_plugin.auth_response(auth_data))


class MySQLSHA256PasswordAuthPluginTests(MySQLConnectorTests):
    """Tests authentication.MySQLSHA256PasswordAuthPlugin"""

    def setUp(self):
        self.plugin_class = get_auth_plugin("sha256_password")

    def test_class(self):
        auth_plugin = self.plugin_class(
            username=None, password="s3cr3t", ssl_enabled=True
        )
        self.assertEqual("sha256_password", auth_plugin.name)
        self.assertEqual(True, auth_plugin.requires_ssl)

    def test_prepare_password(self):
        exp = b"spam\x00"
        auth_plugin = self.plugin_class(
            username=None, password="spam", ssl_enabled=True
        )
        self.assertEqual(exp, auth_plugin._prepare_password())
        self.assertEqual(exp, auth_plugin.auth_response(auth_data=None))


@unittest.skipIf(gssapi is None, "Module gssapi is required")
class MySQLLdapSaslPasswordAuthPluginTests(MySQLConnectorTests):
    """Tests authentication.MySQLLdapSaslPasswordAuthPlugin"""

    def setUp(self):
        self.plugin_class = get_auth_plugin("authentication_ldap_sasl_client")

    def test_class(self):
        auth_plugin = self.plugin_class(username="user", password="spam")
        self.assertEqual("authentication_ldap_sasl_client", auth_plugin.name)
        self.assertEqual(False, auth_plugin.requires_ssl)

    def test_auth_response(self):
        # Test unsupported mechanism error message
        auth_data = b"UNKOWN-METHOD"
        auth_plugin = self.plugin_class(username="user", password="spam")
        with self.assertRaises(InterfaceError) as context:
            auth_plugin.auth_response(auth_data)
        self.assertIn(
            "sasl authentication method",
            context.exception.msg,
            f"not the expected error {context.exception.msg}",
        )
        self.assertIn(
            "is not supported",
            context.exception.msg,
            f"not the expected error {context.exception.msg}",
        )

        # Test SCRAM-SHA-1 mechanism is accepted
        auth_data = b"SCRAM-SHA-1"

        auth_plugin = self.plugin_class(username="", password="")

        # Verify the format of the first message from client.
        exp = b"n,a=,n=,r="
        client_first_nsg = auth_plugin.auth_response(auth_data)
        self.assertTrue(
            client_first_nsg.startswith(exp),
            f"got header: {auth_plugin.auth_response(auth_data)}",
        )

        auth_plugin = self.plugin_class(username="user", password="spam")

        # Verify the length of the client's nonce in r=
        cnonce = client_first_nsg[(len(b"n,a=,n=,r=")) :]
        r_len = len(cnonce)
        self.assertEqual(32, r_len, "Unexpected legth {}".format(len(cnonce)))

        # Verify the format of the first message from client.
        exp = b"n,a=user,n=user,r="
        client_first_nsg = auth_plugin.auth_response(auth_data)
        self.assertTrue(
            client_first_nsg.startswith(exp),
            f"got header: {auth_plugin.auth_response(auth_data)}",
        )

        # Verify the length of the client's nonce in r=
        cnonce = client_first_nsg[(len(exp)) :]
        r_len = len(cnonce)
        self.assertEqual(
            32,
            r_len,
            f"Unexpected cnonce legth {len(cnonce)}, response {client_first_nsg}",
        )

        # Verify that a user name that requires character mapping is mapped
        auth_plugin = self.plugin_class(username="u\u1680ser", password="spam")
        exp = b"n,a=u ser,n=u ser,r="
        client_first_nsg = auth_plugin.auth_response(auth_data)
        self.assertTrue(
            client_first_nsg.startswith(exp),
            f"got header: {auth_plugin.auth_response(auth_data)}",
        )

        # Verify the length of the client's nonce in r=
        cnonce = client_first_nsg[(len(exp)) :]
        r_len = len(cnonce)
        self.assertEqual(32, r_len, f"Unexpected legth {len(cnonce)}")

        bad_responses = [None, "", "v=5H6b+IApa7ZwqQ/ZT33fXoR/BTM=", b"", 123]
        for bad_res in bad_responses:
            # verify an error is shown if server response is not as expected.
            with self.assertRaises(InterfaceError) as context:
                auth_plugin.auth_continue(bad_res)
            self.assertIn(
                "Unexpected server message",
                context.exception.msg,
                f"not the expected: {context.exception.msg}",
            )

        # verify an error is shown if server response is not well formated.
        with self.assertRaises(InterfaceError) as context:
            auth_plugin.auth_continue(
                bytearray("r=/ZT33fXoR/BZT,s=IApa7ZwqQ/ZT,w54".encode())
            )
        self.assertIn(
            "Incomplete reponse",
            context.exception.msg,
            f"not the expected error {context.exception.msg}",
        )

        # verify an error is shown if server does not authenticate response.
        with self.assertRaises(InterfaceError) as context:
            auth_plugin.auth_continue(
                bytearray("r=/ZT33fXoR/BZT,s=IApa7ZwqQ/ZT,i=40".encode())
            )
        self.assertIn(
            "Unable to authenticate resp",
            context.exception.msg,
            f"not the expected error {context.exception.msg}",
        )

        bad_proofs = [None, "", b"5H6b+IApa7ZwqQ/ZT33fXoR/BTM=", b"", 123]
        for bad_proof in bad_proofs:
            # verify an error is shown if server proof is not well formated.
            with self.assertRaises(InterfaceError) as context:
                auth_plugin.auth_finalize(bad_proof)
            self.assertIn(
                "proof is not well formated",
                context.exception.msg,
                f"not the expected: {context.exception.msg}",
            )

        # verify an error is shown it the server can not prove it self.
        with self.assertRaises(InterfaceError) as context:
            auth_plugin.auth_finalize(bytearray(b"v=5H6b+IApa7ZwqQ/ZT33fXoR/BTM="))
        self.assertIn(
            "Unable to proof server identity",
            context.exception.msg,
            f"not the expected error {context.exception.msg}",
        )

    def test_auth_response256(self):
        # Test unsupported mechanism error message
        auth_data = b"UNKOWN-METHOD"
        auth_plugin = self.plugin_class(username="user", password="spam")
        with self.assertRaises(InterfaceError) as context:
            auth_plugin.auth_response(auth_data)
        self.assertIn(
            'sasl authentication method "UNKOWN-METHOD"',
            context.exception.msg,
            f"not the expected error {context.exception.msg}",
        )
        self.assertIn(
            "is not supported",
            context.exception.msg,
            f"not the expected error {context.exception.msg}",
        )

        # Test SCRAM-SHA-256 mechanism is accepted
        auth_data = b"SCRAM-SHA-256"

        auth_plugin = self.plugin_class(username="", password="")

        # Verify the format of the first message from client.
        exp = b"n,a=,n=,r="
        client_first_nsg = auth_plugin.auth_response(auth_data)
        self.assertTrue(
            client_first_nsg.startswith(exp),
            f"got header: {auth_plugin.auth_response(auth_data)}",
        )

        auth_plugin = self.plugin_class(username="user", password="spam")

        # Verify the length of the client's nonce in r=
        cnonce = client_first_nsg[(len(b"n,a=,n=,r=")) :]
        r_len = len(cnonce)
        self.assertEqual(32, r_len, f"Unexpected legth {len(cnonce)}")

        # Verify the format of the first message from client.
        exp = b"n,a=user,n=user,r="
        client_first_nsg = auth_plugin.auth_response(auth_data)
        self.assertTrue(
            client_first_nsg.startswith(exp),
            f"got header: {auth_plugin.auth_response(auth_data)}",
        )

        # Verify the length of the client's nonce in r=
        cnonce = client_first_nsg[(len(exp)) :]
        r_len = len(cnonce)
        self.assertEqual(
            32,
            r_len,
            f"Unexpected cnonce legth {len(cnonce)}, response {client_first_nsg}",
        )

        # Verify that a user name that requires character mapping is mapped
        auth_plugin = self.plugin_class(username="u\u1680ser", password="spam")
        exp = b"n,a=u ser,n=u ser,r="
        client_first_nsg = auth_plugin.auth_response(auth_data)
        self.assertTrue(
            client_first_nsg.startswith(exp),
            f"got header: {auth_plugin.auth_response(auth_data)}",
        )

        # Verify the length of the client's nonce in r=
        cnonce = client_first_nsg[(len(exp)) :]
        r_len = len(cnonce)
        self.assertEqual(32, r_len, f"Unexpected legth {len(cnonce)}")

        bad_responses = [None, "", "v=5H6b+IApa7ZwqQ/ZT33fXoR/BTM=", b"", 123]
        for bad_res in bad_responses:
            # verify an error is shown if server response is not as expected.
            with self.assertRaises(InterfaceError) as context:
                auth_plugin.auth_continue(bad_res)
            self.assertIn(
                "Unexpected server message",
                context.exception.msg,
                f"not the expected: {context.exception.msg}",
            )

        # verify an error is shown if server response is not well formated.
        with self.assertRaises(InterfaceError) as context:
            auth_plugin.auth_continue(bytearray(b"r=/ZT33fXoR/BZT,s=IApa7ZwqQ/ZT,w54"))
        self.assertIn(
            "Incomplete reponse",
            context.exception.msg,
            f"not the expected error {context.exception.msg}",
        )

        # verify an error is shown if server does not authenticate response.
        with self.assertRaises(InterfaceError) as context:
            auth_plugin.auth_continue(bytearray(b"r=/ZT33fXoR/BZT,s=IApa7ZwqQ/ZT,i=40"))
        self.assertIn(
            "Unable to authenticate resp",
            context.exception.msg,
            f"not the expected error {context.exception.msg}",
        )

        bad_proofs = [None, "", b"5H6b+IApa7ZwqQ/ZT33fXoR/BTM=", b"", 123]
        for bad_proof in bad_proofs:
            # verify an error is shown if server proof is not well formated.
            with self.assertRaises(InterfaceError) as context:
                auth_plugin.auth_finalize(bad_proof)
            self.assertIn(
                "proof is not well formated",
                context.exception.msg,
                f"not the expected: {context.exception.msg}",
            )

        # verify an error is shown it the server can not prove it self.
        with self.assertRaises(InterfaceError) as context:
            auth_plugin.auth_finalize(bytearray(b"v=5H6b+IApa7ZwqQ/ZT33fXoR/BTM="))
        self.assertIn(
            "Unable to proof server identity",
            context.exception.msg,
            f"not the expected error {context.exception.msg}",
        )


@unittest.skipIf(
    os.getenv("TEST_AUTHENTICATION_KERBEROS") is None,
    "The 'TEST_AUTHENTICATION_KERBEROS' environment variable is not set",
)
@unittest.skipIf(
    gssapi is None, "The 'gssapi' package is required to run Kerberos tests"
)
@unittest.skipIf(
    tests.MYSQL_VERSION < (8, 0, 24),
    "Authentication with Kerberos not supported",
)
@unittest.skipIf(
    tests.MYSQL_VERSION < (8, 0, 32) and os.name == "nt",
    "Authentication with Kerberos on Windows is not supported for MySQL <8.0.32",
)
class MySQLKerberosAuthPluginTests(MySQLConnectorAioTestCase):
    """Test authentication.MySQLKerberosAuthPlugin.

    Implemented by WL#14440: Support for authentication kerberos.
    """

    user = "test1"
    password = "Testpw1"
    other_user = "test3"
    realm = "MTR.LOCAL"
    badrealm = "MYSQL2.LOCAL"
    krb5ccname = os.environ.get("KRB5CCNAME")
    kinit = os.environ.get("KINIT", "kinit")
    default_config = {}
    plugin_installed_and_active = False
    skip_reason = None

    @classmethod
    def setUpClass(cls):
        if not tests.is_host_reachable("100.103.25.98"):
            cls.skip_reason = "Kerberos server is not reachable"
            return

        config = tests.get_mysql_config()
        cls.default_config = {
            "host": config["host"],
            "port": config["port"],
            "user": cls.user,
            "password": cls.password,
            "auth_plugin": "authentication_kerberos_client",
        }

        # Enable Kerberos GSSPI mode for Windows
        if os.name == "nt":
            cls.default_config["kerberos_auth_mode"] = "GSSAPI"

        with mysql.connector.connection.MySQLConnection(**config) as cnx:
            cnx.cmd_query(f"DROP USER IF EXISTS'{cls.user}'")
            cnx.cmd_query(
                f"""
                CREATE USER '{cls.user}'
                IDENTIFIED WITH authentication_kerberos BY '{cls.realm}'
                """
            )
            cnx.cmd_query(f"GRANT ALL ON *.* to '{cls.user}'")
            cnx.cmd_query("FLUSH PRIVILEGES")

    @classmethod
    def tearDownClass(cls):
        config = tests.get_mysql_config()
        with mysql.connector.connection.MySQLConnection(**config) as cnx:
            cnx.cmd_query(f"DROP USER IF EXISTS '{cls.user}'")
            cnx.cmd_query("FLUSH PRIVILEGES")

    def setUp(self):
        self.plugin_class = get_auth_plugin("authentication_kerberos_client")
        if self.skip_reason is not None:
            self.skipTest(self.skip_reason)

    def _kdestroy(self):
        if os.name == "nt" and self.krb5ccname and os.path.exists(self.krb5ccname):
            os.remove(self.krb5ccname)
        else:
            subprocess.run(["kdestroy"], check=True, stderr=subprocess.DEVNULL)

    def _get_kerberos_tgt(self, user=None, password=None, realm=None, expired=False):
        """Obtain and cache Kerberos ticket-granting ticket.

        Call `kinit` with a specified user and password for obtaining and
        caching Kerberos ticket-granting ticket.
        """
        keytab = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "data",
            "kerberos",
            "users.keytab",
        )

        cmd = [self.kinit]
        if expired:
            cmd.extend(["-l", "0:0:6"])
        if self.krb5ccname:
            cmd.extend(["-c", str(self.krb5ccname)])
        cmd.extend(
            ["-k", "-t", keytab, "{}@{}".format(user or self.user, realm or self.realm)]
        )

        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
        )
        _, err = proc.communicate()

        if err:
            raise InterfaceError(
                "Failing obtaining Kerberos ticket-granting ticket: {}"
                "".format(err.decode("utf-8"))
            )

        if expired:
            time.sleep(8)

    async def _test_connection(self, conn_class, config, fail=False):
        """Test a MySQL connection.

        Try to connect to a MySQL server using a specified connection class
        and config.
        """
        if fail:
            self.assertRaises(
                (
                    DatabaseError,
                    InterfaceError,
                    OperationalError,
                    ProgrammingError,
                ),
                conn_class,
                **config,
            )
            return

        async with conn_class(**config) as cnx:
            self.assertTrue(cnx.is_connected)
            async with cnx.cursor() as cur:
                await cur.execute("SELECT @@version")
                res = await cur.fetchone()
                self.assertIsNotNone(res[0])

    async def _test_with_tgt_cache(
        self,
        conn_class,
        config,
        user=None,
        password=None,
        realm=None,
        expired=False,
        fail=False,
    ):
        """Test with cached valid TGT."""
        # Destroy Kerberos tickets
        self._kdestroy()

        # Obtain and cache Kerberos ticket-granting ticket
        self._get_kerberos_tgt(
            user=user, password=password, realm=realm, expired=expired
        )

        # Test connection
        await self._test_connection(conn_class, config, fail=fail)

        # Destroy Kerberos tickets
        self._kdestroy()

    async def _test_with_st_cache(self, conn_class, config, fail=False):
        """Test with cached valid ST."""
        # Destroy Kerberos tickets
        self._kdestroy()

        # Obtain and cache Kerberos ticket-granting ticket
        self._get_kerberos_tgt()

        # Obtain the service ticket
        cnx = conn_class(**self.default_config)
        await cnx.connect()
        await cnx.close()

        # Test connection
        await self._test_connection(conn_class, config, fail=fail)

        # Destroy Kerberos tickets
        self._kdestroy()

    def test_class(self):
        plugin_obj = self.plugin_class(username="", password="")
        self.assertEqual("authentication_kerberos_client", plugin_obj.name)
        self.assertEqual(False, plugin_obj.requires_ssl)

    # Test with TGT in the cache

    @foreach_cnx_aio()
    async def test_tgt_cache(self):
        """Test with cached valid TGT."""
        config = self.default_config.copy()
        await self._test_with_tgt_cache(self.cnx.__class__, config, fail=False)

    @foreach_cnx_aio()
    async def test_tgt_cache_wrongpassword(self):
        """Test with cached valid TGT with a wrong password."""
        config = self.default_config.copy()
        config["password"] = "wrong_password"
        await self._test_with_tgt_cache(self.cnx.__class__, config, fail=False)

    @foreach_cnx_aio()
    async def test_tgt_cache_nouser(self):
        """Test with cached valid TGT with no user."""
        config = self.default_config.copy()
        del config["user"]
        await self._test_with_tgt_cache(self.cnx.__class__, config, fail=False)

    @foreach_cnx_aio()
    async def test_tgt_cache_nouser_wrongpassword(self):
        """Test with cached valid TGT with no user and a wrong password."""
        config = self.default_config.copy()
        config["password"] = "wrong_password"
        del config["user"]
        await self._test_with_tgt_cache(self.cnx.__class__, config, fail=False)

    @foreach_cnx_aio()
    async def test_tgt_cache_nopassword(self):
        """Test with cached valid TGT with no password."""
        config = self.default_config.copy()
        del config["password"]
        await self._test_with_tgt_cache(self.cnx.__class__, config, fail=False)

    @foreach_cnx_aio()
    async def test_tgt_cache_nouser_nopassword(self):
        """Test with cached valid TGT with no user and no password."""
        config = self.default_config.copy()
        del config["user"]
        del config["password"]
        await self._test_with_tgt_cache(self.cnx.__class__, config, fail=False)

    # Tests with ST in the cache

    @foreach_cnx_aio()
    async def test_st_cache(self):
        """Test with cached valid ST."""
        config = self.default_config.copy()
        await self._test_with_st_cache(self.cnx.__class__, config, fail=False)

    @foreach_cnx_aio()
    async def test_st_cache_wrongpassword(self):
        """Test with cached valid ST with a wrong password."""
        config = self.default_config.copy()
        config["password"] = "wrong_password"
        await self._test_with_st_cache(self.cnx.__class__, config, fail=False)

    @foreach_cnx_aio()
    async def test_st_cache_nouser(self):
        """Test with cached valid ST with no user."""
        config = self.default_config.copy()
        del config["user"]
        await self._test_with_st_cache(self.cnx.__class__, config, fail=False)

    @foreach_cnx_aio()
    async def test_st_cache_nouser_wrongpassword(self):
        """Test with cached valid ST with no user and a wrong password."""
        config = self.default_config.copy()
        config["password"] = "wrong_password"
        del config["user"]
        await self._test_with_st_cache(self.cnx.__class__, config, fail=False)

    @foreach_cnx_aio()
    async def test_st_cache_nopassword(self):
        """Test with cached valid ST with no password."""
        config = self.default_config.copy()
        del config["password"]
        await self._test_with_st_cache(self.cnx.__class__, config, fail=False)

    @foreach_cnx_aio()
    async def test_st_cache_nouser_nopassword(self):
        """Test with cached valid ST with no user and no password."""
        config = self.default_config.copy()
        del config["user"]
        del config["password"]
        await self._test_with_st_cache(self.cnx.__class__, config, fail=False)

    # Tests with cache is present but contains expired TGT

    @foreach_cnx_aio(CMySQLConnection if os.name == "nt" else None)
    async def test_tgt_expired(self):
        """Test with cache expired.

        NOTE: This test is skipped for MySQLConnection on Windows due to
              https://github.com/pythongssapi/python-gssapi/issues/302
        """
        config = self.default_config.copy()
        await self._test_with_tgt_cache(
            self.cnx.__class__,
            config,
            expired=True,
            fail=False,
        )

    @foreach_cnx_aio()
    async def test_tgt_expired_wrongpassword(self):
        """Test with cache expired with a wrong password."""
        config = self.default_config.copy()
        config["password"] = "wrong_password"
        await self._test_with_tgt_cache(
            self.cnx.__class__,
            config,
            expired=True,
            fail=True,
        )

    @unittest.skipIf(not HAVE_CMYSQL, "C Extension not available")
    @foreach_cnx_aio(CMySQLConnection)
    async def test_tgt_expired_nouser(self):
        """Test with cache expired with no user."""
        config = self.default_config.copy()
        del config["user"]
        await self._test_with_tgt_cache(
            self.cnx.__class__,
            config,
            expired=True,
            fail=False,
        )

    @foreach_cnx_aio()
    async def test_tgt_expired_nouser_wrongpassword(self):
        """Test with cache expired with no user and a wrong password."""
        config = self.default_config.copy()
        config["password"] = "wrong_password"
        del config["user"]
        await self._test_with_tgt_cache(
            self.cnx.__class__,
            config,
            expired=True,
            fail=True,
        )

    @foreach_cnx_aio()
    async def test_tgt_expired_nopassword(self):
        """Test with cache expired with no password."""
        config = self.default_config.copy()
        del config["password"]
        await self._test_with_tgt_cache(
            self.cnx.__class__,
            config,
            expired=True,
            fail=True,
        )

    @foreach_cnx_aio()
    async def test_tgt_expired_nouser_nopassword(self):
        """Test with cache expired with no user and no password."""
        config = self.default_config.copy()
        del config["user"]
        del config["password"]
        await self._test_with_tgt_cache(
            self.cnx.__class__,
            config,
            expired=True,
            fail=True,
        )

    # Tests with TGT in the cache for a different UPN

    @foreach_cnx_aio(CMySQLConnection if os.name == "nt" else None)
    async def test_tgt_badupn(self):
        """Test with cached valid TGT with a bad UPN.

        NOTE: This test is skipped for MySQLConnection on Windows due to
              https://github.com/pythongssapi/python-gssapi/issues/302
        """
        config = self.default_config.copy()
        await self._test_with_tgt_cache(
            self.cnx.__class__,
            config,
            user=self.other_user,
            fail=False,
        )

    @foreach_cnx_aio()
    async def test_tgt_badupn_wrongpassword(self):
        """Test with cached valid TGT with a wrong password with a bad UPN."""
        config = self.default_config.copy()
        config["password"] = "wrong_password"
        await self._test_with_tgt_cache(
            self.cnx.__class__,
            config,
            user=self.other_user,
            fail=True,
        )

    @foreach_cnx_aio()
    async def test_tgt_badupn_nouser(self):
        """Test with cached valid TGT with no user with a bad UPN."""
        config = self.default_config.copy()
        del config["user"]
        await self._test_with_tgt_cache(
            self.cnx.__class__,
            config,
            user=self.other_user,
            fail=True,
        )

    @foreach_cnx_aio()
    async def test_tgt_badupn_nouser_wrongpassword(self):
        """Test with cached valid TGT with no user and a wrong password and
        bad UPN."""
        config = self.default_config.copy()
        config["password"] = "wrong_password"
        del config["user"]
        await self._test_with_tgt_cache(
            self.cnx.__class__,
            config,
            user=self.other_user,
            fail=True,
        )

    @foreach_cnx_aio()
    async def test_tgt_badupn_nopassword(self):
        """Test with cached valid TGT with no password and bad UPN."""
        config = self.default_config.copy()
        del config["password"]
        await self._test_with_tgt_cache(
            self.cnx.__class__,
            config,
            user=self.other_user,
            fail=True,
        )

    @foreach_cnx_aio()
    async def test_tgt_badupn_nouser_nopassword(self):
        """Test with cached valid TGT with no user and no password."""
        config = self.default_config.copy()
        del config["user"]
        del config["password"]
        await self._test_with_tgt_cache(
            self.cnx.__class__,
            config,
            user=self.other_user,
            fail=True,
        )

    # Tests with TGT in the cache with for a different realm

    @foreach_cnx_aio(CMySQLConnection if os.name == "nt" else None)
    async def test_tgt_badrealm(self):
        """Test with cached valid TGT with a bad realm.

        NOTE: This test is skipped for MySQLConnection on Windows due to
              https://github.com/pythongssapi/python-gssapi/issues/302
        """
        config = self.default_config.copy()
        await self._test_with_tgt_cache(
            self.cnx.__class__,
            config,
            user=self.user,
            password=self.password,
            realm=self.badrealm,
            fail=False,
        )

    @foreach_cnx_aio()
    async def test_tgt_badrealm_wrongpassword(self):
        """Test with cached valid TGT with a wrong password with a bad realm."""
        config = self.default_config.copy()
        config["password"] = "wrong_password"
        await self._test_with_tgt_cache(
            self.cnx.__class__,
            config,
            user=self.user,
            password=self.password,
            realm=self.badrealm,
            fail=True,
        )

    @foreach_cnx_aio(CMySQLConnection if os.name == "nt" else None)
    async def test_tgt_badrealm_nouser(self):
        """Test with cached valid TGT with no user with a bad realm.

        NOTE: This test is skipped for MySQLConnection on Windows due to
              https://github.com/pythongssapi/python-gssapi/issues/302
        """
        config = self.default_config.copy()
        del config["user"]
        await self._test_with_tgt_cache(
            self.cnx.__class__,
            config,
            user=self.user,
            password=self.password,
            realm=self.badrealm,
            fail=False,
        )

    @foreach_cnx_aio()
    async def test_tgt_badrealm_nouser_wrongpassword(self):
        """Test with cached valid TGT with no user and a wrong password and
        bad realm."""
        config = self.default_config.copy()
        config["password"] = "wrong_password"
        del config["user"]
        await self._test_with_tgt_cache(
            self.cnx.__class__,
            config,
            user=self.user,
            password=self.password,
            realm=self.badrealm,
            fail=True,
        )

    @foreach_cnx_aio()
    async def test_tgt_badrealm_nopassword(self):
        """Test with cached valid TGT with no password and bad realm."""
        config = self.default_config.copy()
        del config["password"]
        await self._test_with_tgt_cache(
            self.cnx.__class__,
            config,
            user=self.user,
            password=self.password,
            realm=self.badrealm,
            fail=True,
        )

    @foreach_cnx_aio()
    async def test_tgt_badrealm_nouser_nopassword(self):
        """Test with cached valid TGT with no user and no password."""
        config = self.default_config.copy()
        del config["user"]
        del config["password"]
        await self._test_with_tgt_cache(
            self.cnx.__class__,
            config,
            user=self.user,
            password=self.password,
            realm=self.badrealm,
            fail=True,
        )

    @unittest.skipIf(
        getpass.getuser() != "test1",
        "Test only available for system user 'test1'",
    )
    @foreach_cnx_aio()
    async def test_nocache_nouser(self):
        """Test with no valid TGT cache, no user and with password."""
        config = self.default_config.copy()
        del config["user"]

        # Destroy Kerberos tickets
        self._kdestroy()

        # Test connection
        await self._test_connection(self.cnx.__class__, config, fail=False)

    # Tests 'kerberos_auth_mode' option

    @unittest.skipIf(os.name == "nt", "Tests not available for Windows")
    @foreach_cnx_aio()
    async def test_kerberos_auth_mode_sspi(self):
        """Test 'kerberos_auth_mode=SSPI' on platforms without support for SSPI."""
        config = self.default_config.copy()
        config["kerberos_auth_mode"] = "SSPI"
        with self.assertRaises(InterfaceError):
            cnx = self.cnx.__class__(**config)
            await cnx.connect()

    @foreach_cnx_aio()
    async def test_kerberos_auth_mode_invalid(self):
        """Test invalid options for 'kerberos_auth_mode'."""
        config = self.default_config.copy()
        for option in ("abc", ["GSSAPI"], 0):
            config["kerberos_auth_mode"] = option
            with self.assertRaises(InterfaceError):
                cnx = self.cnx.__class__(**config)
                await cnx.connect()

    @foreach_cnx_aio()
    async def test_kerberos_auth_mode_valid(self):
        """Test valid options for 'kerberos_auth_mode'."""
        # Destroy Kerberos tickets
        self._kdestroy()

        # Obtain and cache Kerberos ticket-granting ticket
        self._get_kerberos_tgt()

        config = self.default_config.copy()
        for option in ("GSSAPI", "GssApi", "gssapi"):
            config["kerberos_auth_mode"] = option
            # Test connection
            await self._test_connection(self.cnx.__class__, config, fail=False)

        # Destroy Kerberos tickets
        self._kdestroy()

    # Tests 'MySQLKerberosAuthPlugin.get_store()' function

    @foreach_cnx_aio()
    async def test_get_store(self):
        """Test when 'MySQLKerberosAuthPlugin.get_store()."""
        self.maxDiff = 33333
        default_krb5ccname = (
            f"/tmp/krb5cc_{os.getuid()}"
            if os.name == "posix"
            else pathlib.Path("%TEMP%").joinpath("krb5cc")
        )

        # Store current KRB5CCNAME
        krb5ccname = os.environ.get("KRB5CCNAME")

        # Set KRB5CCNAME environment variable to empty
        os.environ["KRB5CCNAME"] = ""
        self.assertRaises(InterfaceError, MySQLKerberosAuthPlugin.get_store)

        # Test using the default KRB5CCNAME environment variable
        if krb5ccname is None and "KRB5CCNAME" in os.environ:
            del os.environ["KRB5CCNAME"]
        self.assertEqual(
            MySQLKerberosAuthPlugin.get_store(),
            {b"ccache": f"FILE:{default_krb5ccname}".encode("utf-8")},
        )

        # Set custom KRB5CCNAME environment variable
        os.environ["KRB5CCNAME"] = f"{default_krb5ccname}_test"
        self.assertEqual(
            MySQLKerberosAuthPlugin.get_store(),
            {b"ccache": f"FILE:{default_krb5ccname}_test".encode("utf-8")},
        )

        # Restore KRB5CCNAME in os.environ
        if krb5ccname is None and "KRB5CCNAME" in os.environ:
            del os.environ["KRB5CCNAME"]
        else:
            os.environ["KRB5CCNAME"] = krb5ccname


@unittest.skipIf(
    tests.MYSQL_VERSION < (8, 0, 28),
    "Multi Factor Authentication not supported",
)
class MySQLMultiFactorAuthenticationTests(MySQLConnectorAioTestCase):
    """Test Multi Factor Authentication.

    Implemented by WL#14667: Support for MFA authentication.

    The initialization of the passwords permutations creates a tuple with
    two values:
       - The first is a tuple with the passwords to be set:
         + True: Valid password provided
         + False: Invalid password provived
         + None: No password provided
       - The second is the expected connection result:
         + True: Connection established
         + False: Connection denied
    """

    user_1f = "user_1f"
    user_2f = "user_2f"
    user_3f = "user_3f"
    password1 = "Testpw1"
    password2 = "Testpw2"
    password3 = "Testpw3"
    base_config = {}
    skip_reason = None

    @classmethod
    def setUpClass(cls):
        config = tests.get_mysql_config()
        cls.base_config = {
            "host": config["host"],
            "port": config["port"],
            "auth_plugin": "mysql_clear_password",
        }
        plugin_ext = "dll" if os.name == "nt" else "so"
        with mysql.connector.connection.MySQLConnection(**config) as cnx:
            try:
                cnx.cmd_query("UNINSTALL PLUGIN cleartext_plugin_server")
            except ProgrammingError:
                pass
            try:
                cnx.cmd_query(
                    f"""
                    INSTALL PLUGIN cleartext_plugin_server
                    SONAME 'auth_test_plugin.{plugin_ext}'
                    """
                )
            except DatabaseError:
                cls.skip_reason = "Plugin cleartext_plugin_server not available"
                return
            cnx.cmd_query(f"DROP USER IF EXISTS '{cls.user_1f}'")
            cnx.cmd_query(f"DROP USER IF EXISTS '{cls.user_2f}'")
            cnx.cmd_query(f"DROP USER IF EXISTS '{cls.user_3f}'")
            cnx.cmd_query(
                f"""
                CREATE USER '{cls.user_1f}'
                IDENTIFIED WITH cleartext_plugin_server BY '{cls.password1}'
                """
            )
            try:
                cnx.cmd_query(
                    f"""
                    CREATE USER '{cls.user_2f}'
                    IDENTIFIED WITH cleartext_plugin_server BY '{cls.password1}'
                    AND
                    IDENTIFIED WITH cleartext_plugin_server BY '{cls.password2}'
                    """
                )
                cnx.cmd_query(
                    f"""
                    CREATE USER '{cls.user_3f}'
                    IDENTIFIED WITH cleartext_plugin_server BY '{cls.password1}'
                    AND
                    IDENTIFIED WITH cleartext_plugin_server BY '{cls.password2}'
                    AND
                    IDENTIFIED WITH cleartext_plugin_server BY '{cls.password3}'
                    """
                )
            except ProgrammingError:
                cls.skip_reason = "Multi Factor Authentication not supported"
                return

    @classmethod
    def tearDownClass(cls):
        config = tests.get_mysql_config()
        with mysql.connector.connection.MySQLConnection(**config) as cnx:
            cnx.cmd_query(f"DROP USER IF EXISTS '{cls.user_1f}'")
            cnx.cmd_query(f"DROP USER IF EXISTS '{cls.user_2f}'")
            cnx.cmd_query(f"DROP USER IF EXISTS '{cls.user_3f}'")
            try:
                cnx.cmd_query("UNINSTALL PLUGIN cleartext_plugin_server")
            except ProgrammingError:
                pass

    def setUp(self):
        if self.skip_reason is not None:
            self.skipTest(self.skip_reason)

    async def _test_connection(self, cls, permutations, user):
        """Helper method for testing connection with MFA."""
        LOGGER.debug("Running %d permutations...", len(permutations))
        for perm, valid in permutations:
            config = self.base_config.copy()
            config["user"] = user
            if perm[0] is not None:
                config["password"] = self.password1 if perm[0] else "invalid"
            if perm[1] is not None:
                config["password1"] = self.password1 if perm[1] else "invalid"
            if perm[2] is not None:
                config["password2"] = self.password2 if perm[2] else "invalid"
            if perm[3] is not None:
                config["password3"] = self.password3 if perm[3] else "invalid"
            LOGGER.debug(
                "Test connection with user '%s' using '%s'. (Expected %s)",
                user,
                perm,
                "SUCCESS" if valid else "FAIL",
            )
            if valid:
                async with cls(**config) as cnx:
                    self.assertTrue(await cnx.is_connected())
                    await cnx.cmd_query("SELECT @@version")
                    res = await cnx.get_rows()
                    self.assertIsNotNone(res[0][0][0])
            else:
                with self.assertRaises(ProgrammingError):
                    cnx = cls(**config)
                    await cnx.connect()

    async def _test_change_user(self, cls, permutations, user):
        """Helper method for testing cnx.cmd_change_user() with MFA."""
        LOGGER.debug("Running %d permutations...", len(permutations))
        for perm, valid in permutations:
            # Connect with 'user_1f'
            config = self.base_config.copy()
            config["user"] = self.user_1f
            config["password"] = self.password1
            async with cls(**config) as cnx:
                await cnx.cmd_query("SELECT @@version")
                res = await cnx.get_rows()
                self.assertIsNotNone(res[0][0][0])
                # Create kwargs options for the provided user
                kwargs = {"username": user}
                if perm[0] is not None:
                    kwargs["password"] = self.password1 if perm[0] else "invalid"
                if perm[1] is not None:
                    kwargs["password1"] = self.password1 if perm[1] else "invalid"
                if perm[2] is not None:
                    kwargs["password2"] = self.password2 if perm[2] else "invalid"
                if perm[3] is not None:
                    kwargs["password3"] = self.password3 if perm[3] else "invalid"
                LOGGER.debug(
                    "Test change user to '%s' using '%s'. (Expected %s)",
                    user,
                    perm,
                    "SUCCESS" if valid else "FAIL",
                )
                # Change user to the provided user
                if valid:
                    await cnx.cmd_change_user(**kwargs)
                    await cnx.cmd_query("SELECT @@version")
                    res = await cnx.get_rows()
                    self.assertIsNotNone(res[0][0][0])
                else:
                    with self.assertRaises(ProgrammingError):
                        cnx = cls(**config)
                        await cnx.cmd_change_user(**kwargs)

    @foreach_cnx_aio()
    async def test_user_1f(self):
        """Test connection 'user_1f' password permutations."""
        permutations = []
        for perm in itertools.product([True, False, None], repeat=4):
            permutations.append((perm, perm[1] or (perm[0] and perm[1] is None)))
        await self._test_connection(self.cnx.__class__, permutations, self.user_1f)
        await self._test_change_user(self.cnx.__class__, permutations, self.user_1f)

    @foreach_cnx_aio()
    async def test_user_2f(self):
        """Test connection and change user 'user_2f' password permutations."""
        permutations = []
        for perm in itertools.product([True, False, None], repeat=4):
            permutations.append(
                (
                    perm,
                    perm[2] and ((perm[0] and perm[1] is not False) or perm[1]),
                )
            )
        await self._test_connection(self.cnx.__class__, permutations, self.user_2f)
        await self._test_change_user(self.cnx.__class__, permutations, self.user_2f)

    @foreach_cnx_aio()
    async def test_user_3f(self):
        """Test connection and change user 'user_3f' password permutations."""
        permutations = []
        for perm in itertools.product([True, False, None], repeat=4):
            permutations.append(
                (
                    perm,
                    perm[2]
                    and perm[3]
                    and ((perm[0] and perm[1] is not False) or perm[1]),
                )
            )
        await self._test_connection(self.cnx.__class__, permutations, self.user_3f)
        await self._test_change_user(self.cnx.__class__, permutations, self.user_3f)


@unittest.skipIf(
    tests.MYSQL_VERSION < (8, 2, 0), "Authentication with WebAuthn not supported"
)
class MySQLWebAuthnAuthPluginTests(tests.MySQLConnectorTests):
    """Test authentication.MySQLWebAuthnAuthPlugin.

    Implemented by WL#11521: Support WebAuthn authentication
    """

    @foreach_cnx_aio()
    async def test_invalid_webauthn_callback(self):
        """Test invalid 'webauthn_callback' option."""

        def my_callback(): ...

        test_cases = (
            "abc",  # No callable named 'abc'
            "abc.abc",  # module 'abc' has no attribute 'abc'
            my_callback,  # 1 positional argument required
        )
        config = tests.get_mysql_config()
        for case in test_cases:
            config["webauthn_callback"] = case
            with self.assertRaises(ProgrammingError):
                cnx = self.cnx.__class__(**config)
                await cnx.connect()


@unittest.skipIf(
    tests.MYSQL_VERSION < (9, 1, 0),
    "Authentication with OpenID Connect is not supported",
)
@unittest.skipIf(
    not tests.SSL_AVAILABLE,
    "SSL support is unavailable, OpenID authentication strictly needs SSL enabled to work properly.",
)
class MySQLOpenIDConnectAuthPluginTests(MySQLConnectorAioTestCase):
    """Test OpenID Connect authentication

    Implemented by WL#16341: OpenID Connect (Oauth2 - JWT) Authentication Support
    """

    skip_reason = None

    @classmethod
    def setUpClass(cls):
        config = tests.get_mysql_config()
        server_host = config['host']
        plugin_ext = "dll" if os.name == "nt" else "so"
        with mysql.connector.connect(**config) as cnx:
            # Install the auth plugin `authentication_openid_connect`
            try:
                cnx.cmd_query(
                    f"""
                    INSTALL PLUGIN authentication_openid_connect
                    SONAME 'authentication_openid_connect.{plugin_ext}'
                    """
                )
            except DatabaseError:
                cls.skip_reason = (
                    "Plugin authentication_openid_connect is not available"
                )
                return
            # Add the JWK to `authentication_openid_connect_configuration` server variable
            jwk = (
                r'JSON://{"myissuer":"{\\"kty\\":\\"RSA\\",\\"n\\":\\"rNF2tLljUxA-IZ9sCD'
                r"XEzeQKAUnJ0BCy3QWGLqTh2I4cLGF_JPHlk5xRHdCV8YOzxpxgGKbj8ClLaxkt3eSWU8oQAvEH7f"
                r"ATOpPHunZzc0n9ak2oFNJqlqHVadhWNxj1LaJPhniqGrDO9iWutd3-zXLgYksPbjZcXXl01SBArc"
                r"zM7OJvL2nQ-lmizVsm0MGfGSCRjpewRPLklGqawOOs8qcqW0J5QOpSby4i-YLG_rRGrfqE-f6BMu"
                r"sX8snSQVx-MlsNO2AS54pi8aC2njEFP3AT_FLxX6gFcfIxbsw_ZwsbDktjj6-UKU0LA0Jvaib2EM"
                r"kS9UJDuni85pKfUfMD4Votq3U9kFjSPl0ZraPDgCLYy-q_vLN5BhQxAsYiCQUnZYQBKsELw07SYF"
                r"7I8kwQcKs8V5ryRvCtjjAbVOHzVdwUKxm2HrKyh4yhogtiSwicndAzgfq2aTHIDDWHpOmEgXmfaX"
                r"shx9vCS5qLZmgOZDGzga2My0dO8sQAYfpP3PF5saZ0MkddSj5kwjCvEeugCdrNHKMimb77BipmJz"
                r"E8WibQEg5IN1P2VmMDfoF-lYNBmZu41pe-OzAqrBLLMEkMWrhTr8jjLFHhTKYTGvtgu0xF4FQkjF"
                r'sbopVCUueMAX8fLYuUYV0cuSF3qFLqDWWH0gl4HK-IsCmjAU_ghAaA-Ys\\",\\"e\\":\\"AQAB'
                r'\\",\\"alg\\":\\"RS256\\",\\"use\\":\\"sig\\",\\"name\\":\\"https://myissuer.com\\"}"}'
            )
            cnx.cmd_query(
                f"SET GLOBAL authentication_openid_connect_configuration = '{jwk}'"
            )
            # Create the user configured with OpenID connect
            cnx.cmd_query(f"DROP USER IF EXISTS 'openid-test'@'{server_host}'")
            cnx.cmd_query(
                f"""CREATE USER 'openid-test'@'{server_host}' IDENTIFIED WITH 'authentication_openid_connect' AS
                '{{"identity_provider" : "myissuer", "user" : "mysubj"}}'"""
            )
            cnx.cmd_query(f"GRANT ALL ON *.* TO 'openid-test'@'{server_host}'")

    @classmethod
    def tearDownClass(cls):
        config = tests.get_mysql_config()
        with mysql.connector.connect(**config) as cnx:
            cnx.cmd_query(f"DROP USER IF EXISTS 'openid-test'@'{config['host']}'")
            try:
                cnx.cmd_query("UNINSTALL PLUGIN authentication_openid_connect")
            except ProgrammingError:
                pass

    def setUp(self):
        if self.skip_reason is not None:
            self.skipTest(self.skip_reason)

    async def helper_for_token_file_valid_test(self, cnx, expected_user):
        await cnx.cmd_query(query="SELECT USER()")
        res = await cnx.get_rows()
        self.assertIsInstance(res, tuple)
        self.assertTrue(expected_user in res[0][0][0])

    @tests.foreach_cnx_aio()
    async def test_openid_identity_token_file_valid(self):
        """Checks whether an user is able to authenticate with a path to a valid
        OpenID Identity Token file passed through `openid_token_file` option via
        fast authentication, switch authentication and change user request process."""

        config = tests.get_mysql_config()
        config["user"] = "openid-test"
        config["auth_plugin"] = "authentication_openid_connect_client"
        config["openid_token_file"] = "tests/data/openid/test_token_valid"
        config["unix_socket"] = None

        # fast authentication check
        async with await mysql.connector.aio.connect(**config) as cnx:
            await self.helper_for_token_file_valid_test(cnx, config["user"])

        # switch authentication check
        del config["auth_plugin"]
        async with await mysql.connector.aio.connect(**config) as cnx:
            await self.helper_for_token_file_valid_test(cnx, config["user"])

        # change user request check
        async with await mysql.connector.aio.connect(**config) as cnx:
            await cnx.cmd_change_user(
                username="openid-test",
                openid_token_file="tests/data/openid/test_token_valid",
            )
            await self.helper_for_token_file_valid_test(cnx, config["user"])

    @tests.foreach_cnx_aio()
    async def test_openid_identity_token_file_path_invalid(self):
        """Checks whether an user is able to authenticate with an invalid path
        to an OpenID Identity Token file passed through `openid_token_file` option."""

        config = tests.get_mysql_config()
        config["user"] = "openid-test"
        config["unix_socket"] = None

        # Non-existent file path
        config["openid_token_file"] = "tests/data/openid/test_token_nonexistent"
        with self.assertRaises(InterfaceError):
            cnx = self.cnx.__class__(**config)
            await cnx.connect()
        # Invalid file path syntax
        config["openid_token_file"] = r"tests\data\openid/test_token_nonexistent"
        with self.assertRaises(InterfaceError):
            cnx = self.cnx.__class__(**config)
            await cnx.connect()
        # File path missing
        del config["openid_token_file"]
        with self.assertRaises((DatabaseError, ProgrammingError)):
            cnx = self.cnx.__class__(**config)
            await cnx.connect()

    @tests.foreach_cnx_aio()
    async def test_openid_identity_token_file_invalid(self):
        """Checks whether an user is able to authenticate with an OpenID Identity
        Token file passed through `openid_token_file` option containing invalid
        token."""

        config = tests.get_mysql_config()
        config["user"] = "openid-test"
        config["unix_socket"] = None

        for invalid_type in (
            "url_unsafe",
            "missing_sub",
            "missing_iss",
            "missing_exp",
            "invalid_struct",
            "invalid_sig",
            "gt_10k",
            "empty",
            "expired",
        ):
            config["openid_token_file"] = "tests/data/openid/test_token_" + invalid_type
            # Check for fast auth
            config["auth_plugin"] = "authentication_openid_connect_client"
            with self.assertRaises((DatabaseError, ProgrammingError, InterfaceError)):
                cnx = self.cnx.__class__(**config)
                await cnx.connect()
            # Check for switch auth
            del config["auth_plugin"]
            with self.assertRaises((DatabaseError, ProgrammingError, InterfaceError)):
                cnx = self.cnx.__class__(**config)
                await cnx.connect()

    @tests.foreach_cnx_aio()
    async def test_openid_connection_ssl_disabled(self):
        """Checks whether an user is able to authenticate via OpenID Connect
        authentication process using an insecure connection."""

        config = tests.get_mysql_config()
        config["user"] = "openid-test"
        config["auth_plugin"] = "authentication_openid_connect_client"
        config["openid_token_file"] = "tests/data/openid/test_token_valid"
        config["ssl_disabled"] = True
        config["unix_socket"] = None

        with self.assertRaises(InterfaceError):
            cnx = self.cnx.__class__(**config)
            await cnx.connect()

    @tests.foreach_cnx_aio()
    async def test_openid_user_invalid(self):
        """Checks whether an user not configured with OpenID Connect authentication is
        able to authenticate when auth_plugin is set to `authentication_openid_connect_client`."""

        config = tests.get_mysql_config()
        config["auth_plugin"] = "authentication_openid_connect_client"
        config["openid_token_file"] = "tests/data/openid/test_token_valid"
        config["unix_socket"] = None

        # Authentication should pass using switch auth process
        async with await mysql.connector.aio.connect(**config) as cnx:
            await self.helper_for_token_file_valid_test(cnx, config["user"])
