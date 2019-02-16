# -*- coding: utf-8 -*-

# Cloze Overlapper Add-on for Anki
#
# Copyright (C)  2016-2019 Aristotelis P. <https://glutanimate.com/>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version, with the additions
# listed at the end of the license file that accompanied this program
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
# terms and conditions of the GNU Affero General Public License that
# accompanied this program.
#
# If not, please request a copy through one of the means of contact
# listed here: <https://glutanimate.com/contact/>.
#
# Any modifications to this file must keep this entire header intact.

"""
Additions to Anki's card reviewer
"""

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

from aqt.qt import QKeySequence

from aqt.reviewer import Reviewer
from anki.hooks import wrap

from .libaddon.platform import ANKI20

olc_hotkey_reveal = "g"
olc_keycode_reveal = QKeySequence(olc_hotkey_reveal)[0]

def onHintRevealHotkey(reviewer):
    if reviewer.state != "answer":
        return
    reviewer.web.eval("""
        var btn = document.getElementById("btn-reveal");
        if (btn) { btn.click(); };
    """)

def newKeyHandler20(reviewer, evt):
    """Bind mask reveal to a hotkey"""
    if (evt.key() == olc_keycode_reveal):
        onHintRevealHotkey(reviewer)

def onShortcutKeys21(reviewer, _old):
    keys = _old(reviewer)
    keys.append(
        (olc_hotkey_reveal, lambda r=reviewer: onHintRevealHotkey(r)))
    return keys

def initializeReviewer():
    if ANKI20:
        Reviewer._keyHandler = wrap(
            Reviewer._keyHandler, newKeyHandler20, "before")
    else:
        Reviewer._shortcutKeys = wrap(Reviewer._shortcutKeys, onShortcutKeys21,
                                      "around")
