#!/usr/bin/env python3
# -------------------------------------------------------------------------------
# This file is part of Mentat system (https://mentat.cesnet.cz/).
#
# Copyright (C) since 2011 CESNET, z.s.p.o (http://www.ces.net/)
# Use of this source is governed by the MIT license, see LICENSE file.
# -------------------------------------------------------------------------------


"""
Unit tests for :py:mod:`hawat.blueprints.changelogs`.
"""

__author__ = "Jan Mach <jan.mach@cesnet.cz>"
__credits__ = "Pavel Kácha <pavel.kacha@cesnet.cz>, Andrea Kropáčová <andrea.kropacova@cesnet.cz>"

import unittest

import hawat.const
import hawat.test
from hawat.test import HawatTestCase, full_test_only
from hawat.test.runner import TestRunnerMixin


class ChangeLogsSearchTestCase(TestRunnerMixin, HawatTestCase):
    """Class for testing ``changelogs.search`` endpoint."""

    def _attempt_fail(self):
        self.assertGetURL(
            "/changelogs/search",
            403,
        )

    def _attempt_succeed(self):
        self.assertGetURL(
            "/changelogs/search",
            200,
        )

    @hawat.test.do_as_user_decorator(hawat.const.ROLE_USER)
    def test_01_as_user(self):
        """Test access as user ``user``."""
        self._attempt_fail()

    @full_test_only
    @hawat.test.do_as_user_decorator(hawat.const.ROLE_DEVELOPER)
    def test_02_as_developer(self):
        """Test access as user ``developer``."""
        self._attempt_fail()

    @hawat.test.do_as_user_decorator(hawat.const.ROLE_MAINTAINER)
    def test_03_as_maintainer(self):
        """Test access as user ``maintainer``."""
        self._attempt_succeed()

    @full_test_only
    @hawat.test.do_as_user_decorator(hawat.const.ROLE_ADMIN)
    def test_04_as_admin(self):
        """Test access as user ``admin``."""
        self._attempt_succeed()


# -------------------------------------------------------------------------------


if __name__ == "__main__":
    unittest.main()
