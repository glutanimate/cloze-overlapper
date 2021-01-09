# Thanks to this guy: https://www.reddit.com/r/Anki/comments/jlj1yy/fixing_cloze_overlapper_for_2128/

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
Adds overlapping clozes
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from .libaddon.platform import ANKI20

import re
from operator import itemgetter
from itertools import groupby

if ANKI20:
    from BeautifulSoup import BeautifulSoup
else:
    from bs4 import BeautifulSoup

from .config import config, parseNoteSettings, createNoteSettings
from .generator import ClozeGenerator
from .utils import warnUser, showTT


class ClozeOverlapper(object):
    """Reads note, calls ClozeGenerator, writes results back to note"""

    creg = r"(?s)\[\[oc(\d+)::((.*?)(::(.*?))?)?\]\]"

    def __init__(self, note, markup=False, silent=False, parent=None):
        self.note = note
        self.model = self.note.model()
        self.flds = config["synced"]["flds"]
        self.markup = markup
        self.silent = silent
        self.parent = parent

    def showTT(self, title, text, period=3000):
        showTT(title, text, period, parent=self.parent)

    def add(self):
        """Add overlapping clozes to note"""
        original = self.note[self.flds["og"]]
        if not original:
            self.showTT(
                "Reminder", "Please enter some text in the '%s' field" % self.flds["og"]
            )
            return False, None

        matches = re.findall(self.creg, original)
        if matches:
            custom = True
            formstr = re.sub(self.creg, "{{\\1}}", original)
            items, keys = self.getClozeItems(matches)
        else:
            custom = False
            formstr = None
            items, keys = self.getLineItems(original)

        if not items:
            self.showTT(
                "Warning",
                "Could not find any items to cloze.<br>Please check your input.",
            )
            return False, None
        if len(items) < 1:
            self.showTT("Reminder", "Please enter at least 1 item to cloze.")
            return False, None

        setopts = parseNoteSettings(self.note[self.flds["st"]])
        maxfields = self.getMaxFields(self.model, self.flds["tx"])
        if not maxfields:
            return False, None

        gen = ClozeGenerator(setopts, maxfields)
        fields, full, total = gen.generate(items, formstr, keys)

        if fields is None:
            self.showTT(
                "Warning",
                "This would generate <b>%d</b> overlapping clozes,<br>"
                "The note type can only handle a maximum of <b>%d</b> with<br>"
                "the current number of %s fields" % (total, maxfields, self.flds["tx"]),
            )
            return False, None
        if fields == 0:
            self.showTT(
                "Warning",
                "This would generate no overlapping clozes at all<br>"
                "Please check your cloze-generation settings",
            )
            return False, None

        self.updateNote(fields, full, setopts, custom)

        if not self.silent:
            self.showTT("Info", "Generated %d overlapping clozes" % total, period=1000)
        return True, total

    def getClozeItems(self, matches):
        """Returns a list of items that were clozed by the user"""
        matches.sort(key=lambda x: int(x[0]))
        groups = groupby(matches, itemgetter(0))
        items = []
        keys = []
        for key, data in groups:
            phrases = tuple(item[1] for item in data)
            keys.append(key)
            if len(phrases) == 1:
                items.append(phrases[0])
            else:
                items.append(phrases)
        return items, keys

    def getLineItems(self, html):
        """Detects HTML list markups and returns a list of plaintext lines"""
        if ANKI20:  # do not supply parser to avoid AttributeError
            soup = BeautifulSoup(html)
        else:
            soup = BeautifulSoup(html, "html.parser")
        text = soup.getText("\n")  # will need to be updated for bs4
        if soup.findAll("ol"):
            self.markup = "ol"
        elif soup.findAll("ul"):
            self.markup = "ul"
        else:
            self.markup = "div"
        # remove empty lines:
        lines = re.sub(r"^(&nbsp;)+$", "", text, flags=re.MULTILINE).splitlines()
        items = [line for line in lines if line.strip() != ""]
        return items, None

    @staticmethod
    def getMaxFields(model, prefix):
        """Determine number of text fields available for cloze sequences"""
        m = model
        fields = [f["name"] for f in m["flds"] if f["name"].startswith(prefix)]
        last = 0
        for f in fields:
            # check for non-continuous cloze fields
            if not f.startswith(prefix):
                continue
            try:
                cur = int(f.replace(prefix, ""))
            except ValueError:
                break
            if cur != last + 1:
                break
            last = cur
        expected = len(fields)
        actual = last
        if not expected or not actual:
            warnUser("Note Type", "Cloze fields not configured properly")
            return False
        elif expected != actual:
            warnUser(
                "Note Type",
                "Cloze fields are not continuous."
                "<br>(breaking off after %i fields)" % actual,
            )
            return False
        return actual

    def updateNote(self, fields, full, setopts, custom):
        """Write changes to note"""
        note = self.note
        options = setopts[1]
        for idx, field in enumerate(fields):
            name = self.flds["tx"] + str(idx + 1)
            if name not in note:
                print("Missing field. Should never happen.")
                continue
            note[name] = field if custom else self.processField(field)

        if options[3]:  # no full clozes
            full = ""
        else:
            full = full if custom else self.processField(full)
        note[self.flds["fl"]] = full
        note[self.flds["st"]] = createNoteSettings(setopts)
        if note.id != 0:  # Not in add mode
            note.flush()

    def processField(self, field):
        """Convert field contents back to HTML based on previous markup"""
        markup = self.markup
        if markup == "div":
            tag_start, tag_end = "", ""
            tag_items = "<div>{0}</div>"
        else:
            tag_start = "<{0}>".format(markup)
            tag_end = "</{0}>".format(markup)
            tag_items = "<li>{0}</li>"
        lines = "".join(tag_items.format(line) for line in field)
        return tag_start + lines + tag_end
