# -*- coding: utf-8 -*-

# Cloze Overlapper Add-on for Anki
#
# Copyright (C) 2016-2019  Aristotelis P. <https://glutanimate.com/>
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
Note settings dialog
"""

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

from aqt.qt import *

from ..config import config, parseNoteSettings, createNoteSettings

from .forms import settings_note

class OlcOptionsNote(QDialog):
    """Note-specific options dialog"""

    def __init__(self, parent):
        super(OlcOptionsNote, self).__init__(parent=parent)
        # load qt-designer form:
        self.f = settings_note.Ui_Dialog()
        self.f.setupUi(self)
        self.f.buttonBox.accepted.connect(self.onAccept)
        self.f.buttonBox.rejected.connect(self.onReject)
        self.parent = parent
        self.ed = parent.editor
        self.note = self.ed.note
        self.flds = config["synced"]["flds"]
        self.setupValues()

    def setupValues(self):
        self.ed.web.eval("saveField('key');")  # save field
        setopts = parseNoteSettings(self.note[self.flds["st"]])
        settings, options = setopts
        before, prompt, after = settings
        if before is None:
            before = -1
        if after is None:
            after = -1
        self.f.sb_before.setValue(before)
        self.f.sb_after.setValue(after)
        self.f.sb_cloze.setValue(prompt)
        for idx, cb in enumerate((self.f.cb_ncf, self.f.cb_ncl,
                                  self.f.cb_incr, self.f.cb_gfc)):
            cb.setChecked(options[idx])

    def onAccept(self):
        before = self.f.sb_before.value()
        after = self.f.sb_after.value()
        prompt = self.f.sb_cloze.value()
        
        before = before if before != -1 else None
        after = after if after != -1 else None

        settings = [before, prompt, after]
        options = [i.isChecked() for i in (
            self.f.cb_ncf, self.f.cb_ncl,
            self.f.cb_incr, self.f.cb_gfc)]
        setopts = (settings, options)
        settings_fld = createNoteSettings(setopts)
        self.note[self.flds["st"]] = settings_fld
        
        self.ed.loadNote()
        
        if self.ed.currentField is not None:
            self.ed.web.eval("focusField(%d);" % self.ed.currentField)
        else:
            self.ed.web.eval("focusField(0);")
        
        self.ed.onOlClozeButton(parent=self.parent)
        
        self.close()

    def onReject(self):
        self.close()
