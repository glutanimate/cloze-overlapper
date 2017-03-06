# -*- coding: utf-8 -*-

"""
This file is part of the Cloze Overlapper add-on for Anki

Configuration

Copyright: Glutanimate 2016-2017
License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
"""

import os

from aqt.qt import *
from aqt import mw
from anki.utils import stripHTML
from anki.errors import AnkiError

from .forms import settings_global, settings_note
from .template import updateTemplate
from .consts import *

# dflts: before, prompt, after
# dflto: no-context-first, no-context-last, gradual ends, generate full cloze
# sched: no-siblings new, no-siblings review, auto-suspend full cloze
default_conf = {
    "dflts": [1,1,0],
    "dflto": [False, False, False, False],
    "flds": OLC_FLDS,
    "sched": [True, False, False],
    "olmdls": [OLC_MODEL],
    "version": 0.261
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
        oldversion = conf['olcloze']['version']
        conf['olcloze']['version'] = default['version']
        # insert other update actions here:
        if oldversion <= 0.25:
            conf['olcloze']['sched'] = conf['olcloze']['nosib'] + [default['sched'][2]]
            del conf['olcloze']['nosib']
            conf['olcloze']['dflto'].append(default['dflto'][3])
        mw.col.setMod()

    return mw.col.conf['olcloze']

def parseNoteSettings(html, config):
    """Return note settings. Fall back to defaults if necessary."""
    options, settings, opts, sets = None, None, None, None
    dflt_set, dflt_opt = config["dflts"], config["dflto"]
    field = stripHTML(html.encode("utf-8"))

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
        for i in range(4):
            try: 
                if options[i] == "y":
                    opts.append(True)
                else:
                    opts.append(False)
            except IndexError:
                opts.append(dflt_opt[i])

    return (sets, opts)

def createNoteSettings(setopts):
    """Create plain text settings string"""
    set_str = ",".join(str(i) if i is not None else "all" for i in setopts[0])
    opt_str = ",".join("y" if i else "n" for i in setopts[1])
    return unicode(set_str + " | " + opt_str, "utf-8")

class OlcNoteSettings(QDialog):
    """Note-specific options dialog"""
    def __init__(self, parent):
        super(OlcNoteSettings, self).__init__(parent=parent)
        # load qt-designer form:
        self.f = settings_note.Ui_Dialog()
        self.f.setupUi(self)
        self.f.buttonBox.accepted.connect(self.onAccept)
        self.f.buttonBox.rejected.connect(self.onReject)
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
        if before == -1:
            before = None
        if after == -1:
            after = None
        settings = [before, prompt, after]
        options = [i.isChecked() for i in (
            self.f.cb_ncf, self.f.cb_ncl, 
            self.f.cb_incr, self.f.cb_gfc)]
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
    """Global options dialog"""
    def __init__(self, mw):
        super(OlcOptions, self).__init__(parent=mw)
        # load qt-designer form:
        self.f = settings_global.Ui_Dialog()
        self.f.setupUi(self)
        self.f.textBrowser.setOpenExternalLinks(True); 
        self.f.buttonBox.accepted.connect(self.onAccept)
        self.f.buttonBox.rejected.connect(self.onReject)
        self.f.buttonBox.button(
            QDialogButtonBox.RestoreDefaults).clicked.connect(self.onRestore)
        self.fndict = zip(OLC_FIDS_PRIV, 
            [self.f.le_og, self.f.le_st, self.f.le_tx, self.f.le_fl])
        self.fsched = (self.f.cb_ns_new, self.f.cb_ns_rev, self.f.cb_sfc)
        self.fopts = (self.f.cb_ncf, self.f.cb_ncl, self.f.cb_incr, self.f.cb_gfc)
        config = loadConfig()
        self.setupValues(config)

    def setupValues(self, config):
        """Set widget values"""
        before, prompt, after = config["dflts"]
        before = before if before is not None else -1
        after = after if after is not None else -1
        self.f.sb_before.setValue(before)
        self.f.sb_after.setValue(after)
        self.f.sb_cloze.setValue(prompt)
        self.f.le_model.setText(",".join(config["olmdls"]))
        for idx, cb in enumerate(self.fsched):
            cb.setChecked(config["sched"][idx])
        for idx, cb in enumerate(self.fopts):
            cb.setChecked(config["dflto"][idx])
        for key, fnedit in self.fndict:
            fnedit.setText(config["flds"][key])

    def onAccept(self):
        modified = False
        config = loadConfig()
        try:
            modified = self.renameFields(config)
        except AnkiError: # rejected full sync warning
            return
        before = self.f.sb_before.value()
        after = self.f.sb_after.value()
        prompt = self.f.sb_cloze.value()
        before = before if before != -1 else None
        after = after if after != -1 else None
        config['dflts'] = [before, prompt, after]
        config['sched'] = [i.isChecked() for i in self.fsched]
        config["dflto"] = [i.isChecked() for i in self.fopts]
        config["olmdls"] = self.f.le_model.text().split(",")
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

    def renameFields(self, config):
        """Check for modified names and rename fields accordingly"""
        modified = False
        model = mw.col.models.byName(OLC_MODEL)
        flds = model['flds']
        for key, fnedit in self.fndict:
            if not fnedit.isModified():
                continue
            name = fnedit.text()
            oldname = config['flds'][key]
            if name is None or not name.strip() or name == oldname:
                continue
            idx = mw.col.models.fieldNames(model).index(oldname)
            fld = flds[idx]
            if fld:
                # rename note type fields
                mw.col.models.renameField(model, fld, name)
                # update olcloze field-id <-> field-name assignment
                config['flds'][key] = name
                modified = True
        return modified
