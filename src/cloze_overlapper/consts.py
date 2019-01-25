# -*- coding: utf-8 -*-

# Cloze Overlapper Add-on for Anki
#
# Copyright (C)  2016-2019 Aristotelis P. <https://glutanimate.com/>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version, with the additions
# listed at the end of the accompanied license file.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# NOTE: This program is subject to certain additional terms pursuant to
# Section 7 of the GNU Affero General Public License.  You should have
# received a copy of these additional terms immediately following the
# terms and conditions of the GNU Affero General Public License which
# accompanied this program.
#
# If not, please request a copy through one of the means of contact
# listed here: <https://glutanimate.com/contact/>.
#
# Any modifications to this file must keep this entire header intact.

"""
Addon-wide constants

FIXME: temporary
"""

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

import sys
import os
from anki import version

ANKI21 = version.startswith("2.1.")
sys_encoding = sys.getfilesystemencoding()

if ANKI21:
    addon_path = os.path.dirname(__file__)
else:
    addon_path = os.path.dirname(__file__).decode(sys_encoding)

# default model
OLC_MODEL = "Cloze (overlapping)"
OLC_CARD = "cloze-ol"
OLC_MAX = 20

# default fields
OLC_FLDS = {
    'og': u"Original",
    'tt': u"Title",
    'rk': u"Remarks",
    'sc': u"Sources",
    'st': u"Settings",
    'tx': u"Text",
    'fl': u"Full"
}
OLC_FLDS_IDS = ['og', 'tt', 'rk', 'sc', 'st', 'tx', 'fl']
OLC_FIDS_PRIV = ['og', 'st', 'tx', 'fl'] # non-user editable