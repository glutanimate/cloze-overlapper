# -*- coding: utf-8 -*-

"""
This file is part of the Cloze Overlapper add-on for Anki

Overlapping Cloze Adder

Copyright: Glutanimate 2016-2017
License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
"""

import re
from operator import itemgetter
from itertools import groupby
from BeautifulSoup import BeautifulSoup

from aqt import mw
from anki.utils import stripHTML

from .consts import *
from .config import loadConfig, parseNoteSettings, createNoteSettings
from .generator import ClozeGenerator
from .utils import warnUser, showTT

class ClozeOverlapper(object):
    """Reads note, calls ClozeGenerator, writes results back to note"""

    creg = r"(?s)\[\[oc(\d+)::((.*?)(::(.*?))?)?\]\]"

    def __init__(self, ed, markup=False, silent=False, parent=None):
        self.ed = ed
        self.note = self.ed.note
        self.model = self.note.model()
        self.config = loadConfig()
        self.flds = self.config["flds"]
        self.markup = markup
        self.silent = silent
        self.parent = parent

    def showTT(self, title, text, period=3000):
        showTT(title, text, period, parent=self.parent)

    def add(self):
        """Add overlapping clozes to note"""
        self.ed.web.eval("saveField('key');") # save field
        original = self.note[self.flds["og"]]
        if not original:
            self.showTT("Reminder",
                u"Please enter some text in the '%s' field" % self.flds["og"])
            return False, None
        if self.markup:
            original = self.applyMarkup()

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
            self.showTT("Warning",
                "Could not find any items to cloze.<br>Please check your input.",)
            return False, None
        if len(items) < 2:
            self.showTT("Reminder",
                "Please enter at least 2 items to cloze.")
            return False, None

        setopts = parseNoteSettings(self.note[self.flds["st"]], self.config)
        maxfields = self.getMaxFields(self.model, self.flds["tx"])
        if not maxfields:
            return False, None

        gen = ClozeGenerator(setopts, maxfields)
        fields, full, total = gen.generate(items, formstr, keys)

        if fields is None:
            self.showTT("Warning", "This would generate <b>%d</b> overlapping clozes,<br>"
                "The note type can only handle a maximum of <b>%d</b> with<br>"
                "the current number of %s fields" % (total, maxfields, self.flds["tx"]))
            return False, None
        if fields == 0:
            self.showTT("Warning", "This would generate no overlapping clozes at all<br>"
                "Please check your cloze-generation settings")
            return False, None

        self.updateNote(fields, full, setopts, custom)

        if not self.silent:
            self.showTT("Info", "Generated %d overlapping clozes" % total, period=1000)

        self.ed.loadNote()
        self.ed.web.eval("focusField(%d);" % self.ed.currentField)
        
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
        soup = BeautifulSoup(html)
        text = soup.getText("\n") # will need to be updated for bs4
        if soup.findAll("ol"):
            self.markup = "ol"
        elif soup.findAll("ul"):
            self.markup = "ul"
        else:
            self.markup = "div"
        # remove empty lines:
        lines = re.sub(r"^(&nbsp;)+$", "", text, flags=re.MULTILINE).splitlines()
        items = [line for line in lines if line.strip() != ''] 
        return items, None

    @staticmethod
    def getMaxFields(model, prefix):
        """Determine number of text fields available for cloze sequences"""
        m = model
        fields = [f['name'] for f in m['flds'] if f['name'].startswith(prefix)]
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
            warnUser("Note Type", "Cloze fields are not continuous."
                "<br>(breaking off after %i fields)" % actual)
            return False
        return actual

    def updateNote(self, fields, full, setopts, custom):
        """Write changes to note"""
        note = self.note
        options = setopts[1]
        for idx, field in enumerate(fields):
            name = self.flds["tx"] + str(idx+1)
            if name not in note:
                print "Missing field. Should never happen."
                continue
            note[name] = field if custom else self.processField(field)

        if options[3]: # no full clozes
            full = ""
        else:
            full = full if custom else self.processField(full)
        note[self.flds["fl"]] = full
        note[self.flds["st"]] = createNoteSettings(setopts)

    def applyMarkup(self):
        """Update original field markup"""
        field_map = mw.col.models.fieldMap(self.model)
        ogfld = field_map[self.flds["og"]][0]
        if self.markup == "ul":
            mode = "insertUnorderedList"
        else:
            mode = "insertOrderedList"
        self.ed.web.eval("""
            focusField(%d);
            document.execCommand('selectAll')
            document.execCommand('%s');
            saveField('key');
            """ % (ogfld, mode))
        return self.note[self.flds["og"]]

    def processField(self, field):
        """Convert field contents back to HTML based on previous markup"""
        markup = self.markup
        if markup == "div":
            tag_start, tag_end = "", ""
            tag_items = "<div>{0}</div>"
        else:
            tag_start = '<{0}>'.format(markup)
            tag_end = '</{0}>'.format(markup)
            tag_items = "<li>{0}</li>"
        lines = "".join(tag_items.format(line.encode("utf-8")) for line in field)
        return unicode(tag_start + lines + tag_end, "utf-8")