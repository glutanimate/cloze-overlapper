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
Global settings dialog
"""

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

from anki.errors import AnkiError

from aqt.qt import *
from aqt import mw

from ..libaddon.gui.about import get_about_string

from ..config import config
from ..consts import *

from .forms import settings_global


class OlcOptionsGlobal(QDialog):
    """Global options dialog"""

    def __init__(self, mw):
        super(OlcOptionsGlobal, self).__init__(parent=mw)
        # load qt-designer form:
        self.f = settings_global.Ui_Dialog()
        self.f.setupUi(self)
        self.setupUI()
        self.fndict = list(zip((i for i in OLC_FIDS_PRIV if i != "tx"),
            [self.f.le_og, self.f.le_st, self.f.le_fl]))
        self.fsched = (self.f.cb_ns_new, self.f.cb_ns_rev, self.f.cb_sfc)
        self.fopts = (self.f.cb_ncf, self.f.cb_ncl,
                      self.f.cb_incr, self.f.cb_gfc)
        self.setupValues(config["synced"])

    def setupUI(self):
        self.f.buttonBox.accepted.connect(self.onAccept)
        self.f.buttonBox.rejected.connect(self.onReject)
        self.f.buttonBox.button(
            QDialogButtonBox.RestoreDefaults).clicked.connect(self.onRestore)
        about_string = get_about_string()
        self.f.htmlAbout.setHtml(about_string)

    def setupValues(self, values):
        """Set widget values"""
        before, prompt, after = values["dflts"]
        before = before if before is not None else -1
        after = after if after is not None else -1
        self.f.sb_before.setValue(before)
        self.f.sb_after.setValue(after)
        self.f.sb_cloze.setValue(prompt)
        self.f.le_model.setText(",".join(values["olmdls"]))
        for idx, cb in enumerate(self.fsched):
            cb.setChecked(values["sched"][idx])
        for idx, cb in enumerate(self.fopts):
            cb.setChecked(values["dflto"][idx])
        for key, fnedit in self.fndict:
            fnedit.setText(values["flds"][key])

    def onAccept(self):
        reset_req = False
        try:
            reset_req = self.renameFields()
        except AnkiError:  # rejected full sync warning
            return
        before = self.f.sb_before.value()
        after = self.f.sb_after.value()
        prompt = self.f.sb_cloze.value()
        before = before if before != -1 else None
        after = after if after != -1 else None
        config["synced"]['dflts'] = [before, prompt, after]
        config["synced"]['sched'] = [i.isChecked() for i in self.fsched]
        config["synced"]["dflto"] = [i.isChecked() for i in self.fopts]
        config["synced"]["olmdls"] = self.f.le_model.text().split(",")
        config.save(reset=reset_req)
        self.close()

    def onRestore(self):
        self.setupValues(config.defaults["synced"])
        for key, lnedit in self.fndict:
            lnedit.setModified(True)

    def onReject(self):
        self.close()

    def renameFields(self):
        """Check for modified names and rename fields accordingly"""
        modified = False
        model = mw.col.models.byName(OLC_MODEL)
        flds = model['flds']
        for key, fnedit in self.fndict:
            if not fnedit.isModified():
                continue
            name = fnedit.text()
            oldname = config["synced"]['flds'][key]
            if name is None or not name.strip() or name == oldname:
                continue
            idx = mw.col.models.fieldNames(model).index(oldname)
            fld = flds[idx]
            if fld:
                # rename note type fields
                mw.col.models.renameField(model, fld, name)
                # update olcloze field-id <-> field-name assignment
                config["synced"]['flds'][key] = name
                modified = True
        return modified


def invokeOptionsGlobal():
    """Invoke global config dialog"""
    dialog = OlcOptionsGlobal(mw)
    return dialog.exec_()


def initializeOptions():
    config.setConfigAction(invokeOptionsGlobal)
    # Set up menu entry:
    options_action = QAction("Cloze Over&lapper Options...", mw)
    options_action.triggered.connect(invokeOptionsGlobal)
    mw.form.menuTools.addAction(options_action)
