# -*- coding: utf-8 -*-

"""
This file is part of the Cloze Overlapper add-on for Anki

Handles user-set options.

Copyright: Glutanimate 2016-2017
License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
"""

import os
from PyQt4 import uic

from aqt.qt import *
from aqt import mw

from consts import *

default_conf = {
    "dflts": (1,1,0),
    "ncf": False,
    "ncl": False,
    "incr": False,
    "flds": OLC_FLDS,
    "version": 0.1
}

def loadConfig():
    """Load and/or create add-on preferences"""
    conf = mw.col.conf
    default = default_conf
    if not 'olcloze' in conf:
        # create initial configuration
        conf['olcloze'] = default
        mw.col.setMod()

    elif conf['olcloze']['version'] < default['version']:
        print("Updating synced config DB from earlier add-on release")
        for key in list(default.keys()):
            if key not in conf['olcloze']:
                conf['olcloze'][key] = default[key]
        conf['olcloze']['version'] = default['version']
        # insert other update actions here:
        mw.col.setMod()

    return mw.col.conf['olcloze']

class OlClozeOpts(QDialog):
    """Options Menu"""
    def __init__(self, mw):
        super(OlClozeOpts, self).__init__(parent=mw)
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
        self.sb_before.setValue(config["dflts"][0])
        self.sb_cloze.setValue(config["dflts"][1])
        self.sb_after.setValue(config["dflts"][2])
        self.cb_ncf.setChecked(config["ncf"])
        self.cb_ncl.setChecked(config["ncl"])
        self.cb_incr.setChecked(config["incr"])
        for key, fnedit in self.fndict:
            fnedit.setText(config["flds"][key])

    def onAccept(self):
        modified = False
        try:
            modified = self.renameFields()
        except AnkiError:
            print "Field rename action aborted"
            return
        mw.col.conf['olcloze']['dflts'] = tuple(i.value() for i in 
                        (self.sb_before, self.sb_cloze, self.sb_after))
        mw.col.conf['olcloze']['ncf'] = self.cb_ncf.isChecked()
        mw.col.conf['olcloze']['ncl'] = self.cb_ncl.isChecked()
        mw.col.conf['olcloze']['incr'] = self.cb_incr.isChecked()
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
