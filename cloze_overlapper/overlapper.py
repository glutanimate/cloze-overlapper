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
from aqt.utils import tooltip, showWarning
from anki.utils import stripHTML

from .consts import *
from .config import loadConfig, parseNoteSettings, createNoteSettings
from .generator import ClozeGenerator


def warnUser(reason, text):
    showWarning(("<b>%s Error</b>: " % reason) + text, title="Cloze Overlapper")

class ClozeOverlapper(object):
    """Reads note, calls ClozeGenerator, writes results back to note"""

    creg = r"(?s)\[\[oc(\d+)::((.*?)(::(.*?))?)?\]\]"

    def __init__(self, ed, markup=None, silent=False):
        self.ed = ed
        self.note = self.ed.note
        self.model = self.note.model()
        self.config = loadConfig()
        self.dflts = self.config["dflts"]
        self.flds = self.config["flds"]
        self.markup = markup
        self.formstr = None
        self.keys = None
        self.silent = silent
        if markup:
            self.update = True
        else:
            self.update = False

    def add(self):
        """Add overlapping clozes to note"""

        if not self.checkIntegrity():
            return False, None
        self.ed.web.eval("saveField('key');") # save field
        original = self.note[self.flds["og"]]
        if not original:
            tooltip(u"<b>Reminder</b>: Please enter some text in the '%s' field" % self.flds["og"])
            return False, None

        matches = re.findall(self.creg, original)
        if matches:
            self.formstr = re.sub(self.creg, "{{\\1}}", original)
            items = self.getClozeItems(matches)
        else:
            items = self.getLineItems(original)

        if not items:
            tooltip("<b>Warning</b>: Could not find items to cloze.<br>Please check your input.")
            return False, None
        if len(items) < 3:
            tooltip("<b>Reminder</b>: Please enter at least three items to cloze.")
            return False, None

        setopts = parseNoteSettings(self.note[self.flds["st"]], self.config)
        maxfields = self.getMaxFields()
        if not maxfields:
            return False, None

        gen = ClozeGenerator(setopts, maxfields)
        fields, full, total = gen.generate(items, self.formstr, self.keys)

        if not fields:
            tooltip("<b>Warning</b>: This would generate <b>%d</b> overlapping clozes,<br>"
                "The note type can only handle a maximum of <b>%d</b> with<br>"
                "the current number of %s fields" % (total, maxfields, self.flds["tx"]))
            return False, None

        self.updateNote(fields, full, setopts)

        msg = "<b>Info</b>: Generated %d overlapping clozes" % total
        if not self.silent:
            tooltip(msg, period=1000)

        self.ed.loadNote()
        self.ed.web.eval("focusField(%d);" % self.ed.currentField)
        return True, msg

    def checkIntegrity(self):
        """Sanity checks for the model and fields"""
        if self.model["name"] not in self.config["olmdls"]:
            tooltip(u"<b>Reminder</b>:<br>Can only generate overlapping clozes<br>"
                "on the following note types:<br>"
                "%s" % ", ".join("'{0}'".format(i) for i in self.config["olmdls"]))
            return False

        fields = [f['name'] for f in self.model['flds']]
        for fid in OLC_FIDS_PRIV:
            if fid == "tx":
                continue
            if self.flds[fid] not in fields:
                warnUser("Note Type", "Looks like your note type is not configured properly. "
                    "Please make sure that the fields list includes "
                    "all of these fields:<br><br><i>%s</i>" % ", ".join(
                    self.flds[fid] if fid != "tx" else "Text1-TextN" for fid in OLC_FIDS_PRIV))
                return False

        return True

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
        self.keys = keys
        return items

    def getLineItems(self, html):
        """Detects HTML list markups and returns a list of plaintext lines"""
        soup = BeautifulSoup(html)
        text = soup.getText("\n") # will need to be updated for bs4
        if not self.markup:
            if soup.findAll("ol"):
                self.markup = "ol"
            elif soup.findAll("ul"):
                self.markup = "ul"
            else:
                self.markup = "div"
        # remove empty lines:
        lines = re.sub(r"^(&nbsp;)+$", "", text, flags=re.MULTILINE).splitlines()
        items = [line for line in lines if line.strip() != ''] 
        return items

    def getMaxFields(self):
        """Determine number of text fields available for cloze sequences"""
        prefix = self.flds["tx"]
        m = self.model
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

    def updateNote(self, fields, full, setopts):
        """Write changes to note"""
        note = self.note
        for idx, field in enumerate(fields):
            name = self.flds["tx"] + str(idx+1)
            if name not in note:
                print "Missing field. Should never happen."
                continue
            note[name] = self.processField(field)

        note[self.flds["fl"]] = self.processField(full)
        note[self.flds["st"]] = createNoteSettings(setopts)

        if self.update:
            # update original field markup
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

    def processField(self, field):
        """Convert field contents back to HTML based on previous markup"""
        markup = self.markup
        if not markup:
            return field
        if markup == "div":
            tag_start, tag_end = "", ""
            tag_items = "<div>{0}</div>"
        else:
            tag_start = '<{0}>'.format(markup)
            tag_end = '</{0}>'.format(markup)
            tag_items = u"<li>{0}</li>"
        lines = "".join(tag_items.format(line.encode("utf-8")) for line in field)
        return tag_start + lines + tag_end