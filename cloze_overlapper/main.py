# -*- coding: utf-8 -*-

"""
This file is part of the Cloze Overlapper add-on for Anki

Main Module, hooks add-on methods into Anki

Copyright: Glutanimate 2016-2017
License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
"""

import re

from aqt.qt import *

from aqt import mw
from aqt.editor import Editor
from aqt.addcards import AddCards
from aqt.editcurrent import EditCurrent
from aqt.utils import tooltip, showInfo

from anki.hooks import addHook, wrap
from anki.utils import ids2str, intTime
from anki.sched import Scheduler

from .consts import *
from .template import addModel
from .config import OlcOptions, OlcNoteSettings, loadConfig
from .overlapper import ClozeOverlapper
from .utils import warnUser, showTT

# Hotkey definitions

olc_hotkey_generate = "Alt+Shift+C" # Cloze generation/preview
olc_hotkey_settings = "Alt+Shift+O" # Note-specific settings
olc_hotkey_cremove = "Alt+Shift+R" # Remove selected clozes
olc_hotkey_olist = "Ctrl+Alt+Shift+." # Toggle ordered list
olc_hotkey_ulist = "Ctrl+Alt+Shift+," # Toggle unordered list
olc_hotkey_mcloze = "Ctrl+Shift+D" # Multi-line cloze
olc_hotkey_mclozealt = "Ctrl+Alt+Shift+D" # Multi-line cloze alt

# Javascript

js_cloze_multi = """
var increment = %s;
var highest = %d;
function clozeChildren(container) {
    children = container.childNodes
    for (i = 0; i < children.length; i++) { 
        var child = children[i]
        var contents = child.innerHTML
        var textOnly = false;
        if (typeof contents === 'undefined'){
            // handle text nodes
            var contents = child.textContent
            textOnly = true;}
        if (increment){idx = highest+i} else {idx = highest}
        contents = '%s' + idx + '::' + contents + '%s'
        if (textOnly){
            child.textContent = contents}
        else {
            child.innerHTML = contents}}
}
if (typeof window.getSelection != "undefined") {
    // get selected HTML
    var sel = window.getSelection();
    if (sel.rangeCount) {
        var container = document.createElement("div");
        for (var i = 0, len = sel.rangeCount; i < len; ++i) {
            container.appendChild(sel.getRangeAt(i).cloneContents());}}
    // wrap each topmost child with cloze tags; TODO: Recursion
    clozeChildren(container);
    // workaround for duplicate list items:
    var clozed = container.innerHTML.replace(/^(<li>)/, "")
    document.execCommand('insertHTML', false, clozed);
    saveField('key');
}
"""

js_cloze_remove = """
function getSelectionHtml() {
    // Based on an SO answer by Tim Down
    var html = "";
    if (typeof window.getSelection != "undefined") {
        var sel = window.getSelection();
        if (sel.rangeCount) {
            var container = document.createElement("div");
            for (var i = 0, len = sel.rangeCount; i < len; ++i) {
                container.appendChild(sel.getRangeAt(i).cloneContents());
            }
            html = container.innerHTML;
        }
    } else if (typeof document.selection != "undefined") {
        if (document.selection.type == "Text") {
            html = document.selection.createRange().htmlText;
        }
    }
    return html;
}
if (typeof window.getSelection != "undefined") {
    // get selected HTML
    var sel = getSelectionHtml();
    sel = sel.replace(/%s/mg, "$2");
    // workaround for duplicate list items:
    var sel = sel.replace(/^(<li>)/, "")
    document.execCommand('insertHTML', false, sel);
    saveField('key');
}
"""

# Editor

def onInsertCloze(self, _old):
    """Handles cloze-wraps when the add-on model is active"""
    if not checkModel(self.note.model(), fields=False, notify=False):
        return _old(self)
    # find the highest existing cloze
    highest = 0
    for name, val in self.note.items():
        m = re.findall("\[\[oc(\d+)::", val)
        if m:
            highest = max(highest, sorted([int(x) for x in m])[-1])
    # reuse last?
    if not self.mw.app.keyboardModifiers() & Qt.AltModifier:
        highest += 1
    # must start at 1
    highest = max(1, highest)
    self.web.eval("wrap('[[oc%d::', ']]');" % highest)

def onInsertMultipleClozes(self):
    """Wraps each line in a separate cloze"""
    model = self.note.model()
    # check that the model is set up for cloze deletion
    if not re.search('{{(.*:)*cloze:',model['tmpls'][0]['qfmt']):
        if self.addMode:
            tooltip(_("Warning, cloze deletions will not work until "
            "you switch the type at the top to Cloze."))
        else:
            showInfo(_("""\
To make a cloze deletion on an existing note, you need to change it \
to a cloze type first, via Edit>Change Note Type."""))
            return
    if checkModel(model, fields=False, notify=False):
        cloze_re = "\[\[oc(\d+)::"
        wrap_pre, wrap_post = "[[oc", "]]"
    else:
        cloze_re = "\{\{c(\d+)::"
        wrap_pre, wrap_post  = "{{c", "}}"
    # find the highest existing cloze
    highest = 0  
    for name, val in self.note.items():
        m = re.findall(cloze_re, val)
        if m:
            highest = max(highest, sorted([int(x) for x in m])[-1])
    increment = "false"
    if not self.mw.app.keyboardModifiers() & Qt.AltModifier:
        highest += 1
        increment = "true"
    highest = max(1, highest)
    # process selected text
    self.web.eval(js_cloze_multi % (
            increment, highest, wrap_pre, wrap_post))

def onRemoveClozes(self):
    """Remove cloze markers and hints from selected text"""
    if checkModel(self.note.model(), fields=False, notify=False):
        cloze_re = r"\[\[oc(\d+)::(.*?)(::(.*?))?\]\]"
    else:
        cloze_re = r"\{\{c(\d+)::(.*?)(::(.*?))?\}\}"
    self.web.eval(js_cloze_remove % cloze_re)

def checkModel(model, fields=True, notify=True):
    """Sanity checks for the model and fields"""
    config = loadConfig()
    mname = model["name"]
    is_olc = False
    # account for custom and imported note types:
    if mname in config["olmdls"] or mname.startswith(OLC_MODEL):
        is_olc = True
    if notify and not is_olc:
        showTT("Reminder", u"Can only generate overlapping clozes<br>"
            "on the following note types:<br><br>"
            "%s" % ", ".join("'{0}'".format(i) for i in config["olmdls"]))
    if not is_olc or not fields:
        return is_olc
    flds = [f['name'] for f in model['flds']]
    complete = True
    for fid in OLC_FIDS_PRIV:
        fname = config["flds"][fid] 
        if fid == "tx":
            # should have at least 3 text fields
            complete = all(fname + str(i) in flds for i in range(1,4))
        else:
            complete = fname in flds
        if not complete:
            break
    if not complete:
        warnUser("Note Type", "Looks like your note type is not configured properly. "
            "Please make sure that the fields list includes "
            "all of the following fields:<br><br><i>%s</i>" % ", ".join(
            config["flds"][fid] if fid != "tx" else "Text1-TextN" for fid in OLC_FIDS_PRIV))
    return complete

def onOlOptionsButton(self):
    """Invoke note-specific options dialog"""
    if not checkModel(self.note.model()):
        return False
    options = OlcNoteSettings(self.parentWindow)
    options.exec_()

def onOlClozeButton(self, markup=None, parent=None):
    """Invokes an instance of the main add-on class"""
    if not checkModel(self.note.model()):
        return False
    overlapper = ClozeOverlapper(self, markup=markup, parent=parent)
    overlapper.add()

def onSetupButtons(self):
    """Add buttons and hotkeys to the editor widget"""

    b = self._addButton("Remove Clozes",
        self.onRemoveClozes, _(olc_hotkey_cremove), 
        "Remove all cloze markers<br>in selected text (%s)" % _(olc_hotkey_cremove), 
        text="RC", size=True)
    b.setFixedWidth(24)

    b = self._addButton("Cloze Overlapper",
        self.onOlClozeButton, _(olc_hotkey_generate),
        "Generate overlapping clozes (%s)" % _(olc_hotkey_generate), 
        text="[.]]", size=True)
    b.setFixedWidth(24)

    b = self._addButton("Cloze Overlapper Note Settings",
        self.onOlOptionsButton, _(olc_hotkey_settings), 
        "Overlapping cloze generation settings (%s)" % _(olc_hotkey_settings), 
        text="[O]", size=True)
    b.setFixedWidth(24)
    
    add_ol_cut = QShortcut(QKeySequence(_(olc_hotkey_olist)), self.parentWindow)
    add_ol_cut.activated.connect(lambda o="ol": self.onOlClozeButton(o))
    add_ul_cut = QShortcut(QKeySequence(_(olc_hotkey_ulist)), self.parentWindow)
    add_ul_cut.activated.connect(lambda o="ul": self.onOlClozeButton(o))

    mult_cloze_cut1 = QShortcut(QKeySequence(_(olc_hotkey_mcloze)), self.parentWindow)
    mult_cloze_cut1.activated.connect(self.onInsertMultipleClozes)
    mult_cloze_cut2 = QShortcut(QKeySequence(_(olc_hotkey_mclozealt)), self.parentWindow)
    mult_cloze_cut2.activated.connect(self.onInsertMultipleClozes)


# AddCards and EditCurrent windows

def onAddCards(self, _old):
    """Automatically generate overlapping clozes before adding cards"""
    note = self.editor.note
    if not note or not checkModel(note.model(), notify=False):
        return _old(self)
    overlapper = ClozeOverlapper(self.editor, silent=True)
    ret, total = overlapper.add()
    if not ret:
        return
    oldret = _old(self)
    if total:
        showTT("Info", "Added %d overlapping cloze cards" % total, period=1000)
    return oldret

def onEditCurrent(self, _old):
    """Automatically update overlapping clozes before updating cards"""
    note = self.editor.note
    if not note or not checkModel(note.model(), notify=False):
        return _old(self)
    overlapper = ClozeOverlapper(self.editor, silent=True)
    ret, total = overlapper.add()
    # returning here won't stop the window from being rejected, so we simply
    # accept whatever changes the user performed, even if the generator
    # did not fire
    oldret = _old(self)
    if total:
        showTT("Info", "Updated %d overlapping cloze cards" % total, period=1000)
    return oldret


# Scheduling

def myBurySiblings(self, card, _old):
    """Skip sibling burying for our note type if so configured"""
    if not checkModel(card.model(), fields=False, notify=False):
        return _old(self, card)
    sched_conf = mw.col.conf["olcloze"].get("sched", None)
    if not sched_conf:
        return _old(self, card)
    override_new, override_review, bury_full = sched_conf
    if override_new and override_review:
        # sibling burying disabled entirely
        return
    toBury = []
    nconf, rconf = self._newConf(card), self._revConf(card)
    buryNew, buryRev = nconf.get("bury", True), rconf.get("bury", True)
    # loop through and remove from queues
    for cid,queue in self.col.db.execute("""
select id, queue from cards where nid=? and id!=?
and (queue=0 or (queue=2 and due<=?))""",
            card.nid, card.id, self.today):
        if queue == 2:
            if override_review:
                continue
            if buryRev:
                toBury.append(cid)
            try:
                self._revQueue.remove(cid)
            except ValueError:
                pass
        else:
            if override_new:
                continue
            if buryNew:
                toBury.append(cid)
            try:
                self._newQueue.remove(cid)
            except ValueError:
                pass
    # then bury
    if toBury:
        self.col.db.execute(
            "update cards set queue=-2,mod=?,usn=? where id in "+ids2str(toBury),
            intTime(), self.col.usn())
        self.col.log(toBury)


def onAddNote(self, note, _old):
    """Suspend full cloze card if option active"""
    note = _old(self, note)
    if not note or not checkModel(note.model(), fields=False, notify=False):
        return note
    config = mw.col.conf["olcloze"]
    sched_conf = config.get("sched", None)
    if not sched_conf or not sched_conf[2]:
        return note
    maxfields = ClozeOverlapper.getMaxFields(note.model(), config["flds"]["tx"])
    last = note.cards()[-1]
    if last.ord == maxfields: # is full cloze (ord starts at 0)
        mw.col.sched.suspendCards([last.id])
    return note

# Menus

def onOlcOptions(mw):
    """Invoke global config dialog"""
    dialog = OlcOptions(mw)
    dialog.exec_()

options_action = QAction("Cloze Over&lapper Options...", mw)
options_action.triggered.connect(lambda _, m=mw: onOlcOptions(m))
mw.form.menuTools.addAction(options_action)

# Hooks

def setupAddon():
    """Prepare note type and apply scheduler modifications"""
    """can only be performed after the profile has been loaded"""
    model = mw.col.models.byName(OLC_MODEL)
    loadConfig()
    if not model:
        model = addModel(mw.col)
    Scheduler._burySiblings = wrap(
        Scheduler._burySiblings, myBurySiblings, "around")

addHook("profileLoaded", setupAddon)
addHook("setupEditorButtons", onSetupButtons)
Editor.onOlClozeButton = onOlClozeButton
Editor.onOlOptionsButton = onOlOptionsButton
Editor.onInsertMultipleClozes = onInsertMultipleClozes
Editor.onRemoveClozes = onRemoveClozes
Editor.onCloze = wrap(Editor.onCloze, onInsertCloze, "around")

AddCards.addCards = wrap(AddCards.addCards, onAddCards, "around")
AddCards.addNote = wrap(AddCards.addNote, onAddNote, "around")
EditCurrent.onSave = wrap(EditCurrent.onSave, onEditCurrent, "around")