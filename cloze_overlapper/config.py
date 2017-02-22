# -*- coding: utf-8 -*-

"""
This file is part of the Cloze Overlapper add-on for Anki

Configuration

Copyright: Glutanimate 2016-2017
License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
"""

import os
from PyQt4 import uic

from aqt.qt import *
from aqt import mw

from consts import *

# dflto: no-context-first, no-context-last, gradual ends
default_conf = {
    "dflts": [1,1,0],
    "dflto": [False, False, False],
    "flds": OLC_FLDS,
    "nosib": [True, False],
    "version": 0.21
}

def loadConfig():
    """Load and/or create add-on configuration"""
    conf = mw.col.conf
    default = default_conf
    if not 'olcloze' in conf:
        # create initial configuration
        conf['olcloze'] = default
        mw.col.setMod()

    elif conf['olcloze']['version'] < default['version']:
        print("Updating olcloze config from earlier add-on release")
        for key in list(default.keys()):
            if key not in conf['olcloze']:
                conf['olcloze'][key] = default[key]
        conf['olcloze']['version'] = default['version']
        # insert other update actions here:
        conf['olcloze'] = default # DEBUG ONLY completely replace existing conf 
        mw.col.setMod()

    return mw.col.conf['olcloze']

class ClozeOverlapperOptions(QDialog):
    """Options Menu"""
    def __init__(self, mw):
        super(ClozeOverlapperOptions, self).__init__(parent=mw)
        # load qt-designer form:
        uic.loadUi(os.path.join(os.path.dirname(os.path.abspath(__file__))
            , "forms", "options.ui"), self)
        self.buttonBox.accepted.connect(self.onAccept)
        self.buttonBox.rejected.connect(self.onReject)
        self.buttonBox.button(
            QDialogButtonBox.RestoreDefaults).clicked.connect(self.onRestore)
        fnedits = [self.le_og, self.le_st, self.le_tx, self.le_fl]
        self.fndict = zip(OLC_FIDS_PRIV, fnedits)
        config = loadConfig()
        self.setupValues(config)

    def setupValues(self, config):
        before, prompt, after = config["dflts"]
        if before is None:
            before = -1
        if after is None:
            after = -1
        self.sb_before.setValue(before)
        self.sb_after.setValue(after)
        self.sb_cloze.setValue(prompt)
        self.cb_ns_new.setChecked(config["nosib"][0])
        self.cb_ns_rev.setChecked(config["nosib"][1])
        for idx, cb in enumerate((self.cb_ncf, self.cb_ncl, self.cb_incr)):
            cb.setChecked(config["dflto"][idx])
        for key, fnedit in self.fndict:
            fnedit.setText(config["flds"][key])

    def onAccept(self):
        modified = False
        try:
            modified = self.renameFields()
        except AnkiError:
            print "Field rename action aborted"
            return
        config = mw.col.conf['olcloze']
        before = self.sb_before.value()
        after = self.sb_after.value()
        prompt = self.sb_cloze.value()
        if before == -1:
            before = None
        if after == -1:
            after = None
        config['dflts'] = [before, prompt, after]
        config['nosib'][0] = self.cb_ns_new.isChecked()
        config['nosib'][1] = self.cb_ns_rev.isChecked()
        config["dflto"] = [i.isChecked() for i in (
                self.cb_ncf, self.cb_ncl, self.cb_incr)]
        mw.col.setMod()
        if modified:
            mw.reset()
        self.close()

    def onRestore(self):
        self.setupValues(default_conf)
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
            oldname = mw.col.conf['olcloze']['flds'][key]
            if name is None or not name.strip() or name == oldname:
                continue
            idx = mw.col.models.fieldNames(model).index(oldname)
            fld = flds[idx]
            if fld:
                # rename note type fields
                mw.col.models.renameField(model, fld, name)
                # update olcloze field-id <-> field-name assignment
                mw.col.conf['olcloze']['flds'][key] = name
                modified = True
        return modified
