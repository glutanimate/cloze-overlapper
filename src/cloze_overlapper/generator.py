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
Generates cloze texts for overlapping clozes.
"""

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)


class ClozeGenerator(object):
    """Cloze generator"""

    cformat = "{{c%i::%s}}"

    def __init__(self, setopts, maxfields):
        self.maxfields = maxfields
        self.before, self.prompt, self.after = setopts[0]
        self.options = setopts[1]
        self.start = None
        self.total = None

    def generate(self, items, original=None, keys=None):
        """Returns an array of lists with overlapping cloze deletions"""
        length = len(items)
        if self.prompt > length:
            return 0, None, None
        if self.options[2]:
            self.total = length + self.prompt - 1
            self.start = 1
        else:
            self.total = length
            self.start = self.prompt
        if self.total > self.maxfields:
            return None, None, self.total

        fields = []

        for idx in range(self.start, self.total+1):
            snippets = ["..."] * length
            start_c = self.getClozeStart(idx)
            start_b = self.getBeforeStart(idx, start_c)
            end_a = self.getAfterEnd(idx)

            if start_b is not None:
                snippets[start_b:start_c] = self.removeHints(
                    items[start_b:start_c])
            if end_a is not None:
                snippets[idx:end_a] = self.removeHints(items[idx:end_a])
            snippets[start_c:idx] = self.formatCloze(
                items[start_c:idx], idx-self.start+1)

            field = self.formatSnippets(snippets, original, keys)
            fields.append(field)
        nr = len(fields)
        if self.maxfields > self.total:  # delete contents of unused fields
            fields = fields + [""] * (self.maxfields - len(fields))
        fullsnippet = self.formatCloze(items, self.maxfields + 1)
        full = self.formatSnippets(fullsnippet, original, keys)
        return fields, full, nr

    def formatCloze(self, items, nr):
        """Apply cloze deletion syntax to item"""
        res = []
        for item in items:
            if not isinstance(item, (list, tuple)):
                res.append(self.cformat % (nr, item))
            else:
                res.append([self.cformat % (nr, i) for i in item])
        return res

    def removeHints(self, items):
        """Removes cloze hints from items"""
        res = []
        for item in items:
            if not isinstance(item, (list, tuple)):
                res.append(item.split("::")[0])
            else:
                res.append([i.split("::")[0] for i in item])
        return res

    def formatSnippets(self, snippets, original, keys):
        """Insert snippets back into original text, if available"""
        html = original
        if not html:
            return snippets
        for nr, phrase in zip(keys, snippets):
            if phrase == "...":  # placeholder, replace all instances
                html = html.replace("{{" + nr + "}}", phrase)
            elif not isinstance(phrase, (list, tuple)):
                html = html.replace("{{" + nr + "}}", phrase, 1)
            else:
                for item in phrase:
                    html = html.replace("{{" + nr + "}}", item, 1)
        return html

    def getClozeStart(self, idx):
        """Determine start index of clozed items"""
        if idx < self.prompt or idx > self.total:
            return 0
        return idx-self.prompt  # looking back from current index

    def getBeforeStart(self, idx, start_c):
        """Determine start index of preceding context"""
        if (self.before == 0 or start_c < 1 or
                (self.before and self.options[1] and idx == self.total)):
            return None
        if self.before is None or self.before > start_c:
            return 0
        return start_c-self.before

    def getAfterEnd(self, idx):
        """Determine end index of following context"""
        left = self.total - idx
        if (self.after == 0 or left < 1 or
                (self.after and self.options[0] and idx == self.start)):
            return None
        if self.after is None or self.after > left:
            return self.total
        return idx+self.after
