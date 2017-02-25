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
from anki.utils import stripHTML

from consts import *

# dflto: no-context-first, no-context-last, gradual ends
default_conf = {
    "dflts": [1,1,0],
    "dflto": [False, False, False],
    "flds": OLC_FLDS,
    "nosib": [True, False],
    "olmdls": [OLC_MODEL],
    "version": 0.22
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
        mw.col.setMod()

    return mw.col.conf['olcloze']

def parseNoteSettings(html, config):
    """Return note settings. Fall back to defaults if necessary."""
    options, settings, opts, sets = None, None, None, None
    dflt_set, dflt_opt = config["dflts"], config["dflto"]
    field = stripHTML(html)

    lines = field.replace(" ", "").split("|")
    if not lines:
        return (dflt_set, dflt_opt)
    settings = lines[0].split(",")
    if len(lines) > 1:
        options = lines[1].split(",")

    if not options and not settings:
        return (dflt_set, dflt_opt)

    if not settings:
        sets = dflt_set
    else:
        sets = []
        for idx, item in enumerate(settings[:3]):
            try:
                sets.append(int(item))
            except ValueError:
                sets.append(None)
        length = len(sets)
        if length == 3 and isinstance(sets[1], int):
            pass
        elif length == 2 and isinstance(sets[0], int):
            sets = [sets[1], sets[0], sets[1]]
        elif length == 1 and isinstance(sets[0], int):
            sets = [dflt_set[0], sets[0], dflt_set[2]]
        else:
            sets = dflt_set

    if not options:
        opts = dflt_opt
    else:
        opts = []
        for i in range(3):
            try: 
                if options[i] == "y":
                    opts.append(True)
                else:
                    opts.append(False)
            except IndexError:
                opts.append(False)

    return (sets, opts)

def createNoteSettings(setopts):
    """Create plain text settings string"""
    settings_string = ",".join(str(i) if i is not None else "all" for i in setopts[0])
    options_string = ",".join("y" if i else "n" for i in setopts[1])
    return settings_string + " | " + options_string

class OlcNoteSettings(QDialog):
    """Note-specific settings"""
    def __init__(self, parent):
        super(OlcNoteSettings, self).__init__(parent=parent)
        # load qt-designer form:
        uic.loadUi(os.path.join(os.path.dirname(os.path.abspath(__file__))
            , "forms", "settings_note.ui"), self)
        self.buttonBox.accepted.connect(self.onAccept)
        self.buttonBox.rejected.connect(self.onReject)
        self.parent = parent
        self.ed = parent.editor
        self.note = self.ed.note
        self.config = loadConfig()
        self.flds = self.config["flds"]
        self.setupValues()

    def setupValues(self):
        self.ed.web.eval("saveField('key');") # save field
        setopts = parseNoteSettings(self.note[self.flds["st"]], self.config)
        settings, options = setopts
        before, prompt, after = settings
        if before is None:
            before = -1
        if after is None:
            after = -1
        self.sb_before.setValue(before)
        self.sb_after.setValue(after)
        self.sb_cloze.setValue(prompt)
        for idx, cb in enumerate((self.cb_ncf, self.cb_ncl, self.cb_incr)):
            cb.setChecked(options[idx])

    def onAccept(self):
        before = self.sb_before.value()
        after = self.sb_after.value()
        prompt = self.sb_cloze.value()
        if before == -1:
            before = None
        if after == -1:
            after = None
        settings = [before, prompt, after]
        options = [i.isChecked() for i in (
                self.cb_ncf, self.cb_ncl, self.cb_incr)]
        setopts = (settings, options)
        settings_fld = createNoteSettings(setopts)
        self.note[self.flds["st"]] = settings_fld
        self.ed.loadNote()
        self.ed.web.eval("focusField(%d);" % self.ed.currentField)
        self.ed.onOlClozeButton(parent=self.parent)
        self.close()

    def onReject(self):
        self.close()

class OlcOptions(QDialog):
    """Options Menu"""
    def __init__(self, mw):
        super(OlcOptions, self).__init__(parent=mw)
        # load qt-designer form:
        uic.loadUi(os.path.join(os.path.dirname(os.path.abspath(__file__))
            , "forms", "settings_global.ui"), self)
        self.textBrowser.setOpenExternalLinks(True); 
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
        self.le_model.setText(",".join(config["olmdls"]))
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
        config["olmdls"] = self.le_model.text().split(",")
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
