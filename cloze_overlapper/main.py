# -*- coding: utf-8 -*-

"""
This file is part of the Cloze Overlapper add-on for Anki

Main Module

Copyright: Glutanimate 2016-2017
License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
"""

import re

from aqt.qt import *

from aqt import mw
from aqt.editor import Editor
from anki.hooks import addHook, wrap
from anki.sched import Scheduler

from .consts import *
from .template import addModel
from .config import ClozeOverlapperOptions
from .overlapper import ClozeOverlapper


def onOlClozeButton(self, markup=None):
    """Invokes an instance of the main add-on class"""
    overlapper = ClozeOverlapper(self, markup)
    overlapper.add()

def onInsertCloze(self, _old):
    """Handles cloze-wraps when the add-on model is active"""
    if self.note.model()["name"] != OLC_MODEL:
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
    if self.note.model()["name"] == OLC_MODEL:
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
    self.web.eval("""
        var increment = %s;
        var highest = %d;
        if (typeof window.getSelection != "undefined") {
            // get selected HTML
            var sel = window.getSelection();
            if (sel.rangeCount) {
                var container = document.createElement("div");
                for (var i = 0, len = sel.rangeCount; i < len; ++i) {
                    container.appendChild(sel.getRangeAt(i).cloneContents());}
            // wrap each topmost child with cloze tags
            children = container.childNodes
            for (i = 0; i < children.length; i++) { 
                var child = children[i]
                var contents = child.innerHTML
                if (typeof contents === 'undefined'){
                    // handle text nodes
                    var contents = child.textContent
                    var textOnly = true;}
                if (increment){idx = highest+i} else {idx = highest}
                contents = '%s' + idx + '::' + contents + '%s'
                if (textOnly){
                    children[i].textContent = contents}
                else {
                    children[i].innerHTML = contents}}
            document.execCommand('insertHTML', false, container.innerHTML);
        }
        """ % (increment, highest, wrap_pre, wrap_post))

def onSetupButtons(self):
    """Add buttons and hotkeys to the editor widget"""
    self._addButton("Cloze Overlapper", self.onOlClozeButton,
        _("Alt+Shift+C"), "Generate Overlapping Clozes (Alt+Shift+C)", 
        text="[.]]", size=True)
    
    add_ol_cut = QShortcut(QKeySequence(_("Ctrl+Alt+Shift+.")), self.parentWindow)
    add_ol_cut.activated.connect(lambda _, o="ol": self.onOlClozeButton(o))
    add_ul_cut = QShortcut(QKeySequence(_("Ctrl+Alt+Shift+,")), self.parentWindow)
    add_ul_cut.activated.connect(lambda _, o="ul": self.onOlClozeButton(o))

    mult_cloze_cut1 = QShortcut(QKeySequence(_("Ctrl+Shift+D")), self.parentWindow)
    mult_cloze_cut1.activated.connect(self.onInsertMultipleClozes)
    mult_cloze_cut2 = QShortcut(QKeySequence(_("Ctrl+Alt+Shift+D")), self.parentWindow)
    mult_cloze_cut2.activated.connect(self.onInsertMultipleClozes)

def onCgOptions(mw):
    """Invoke options dialog"""
    dialog = ClozeOverlapperOptions(mw)
    dialog.exec_()


def setupAddon():
    """Prepare note type and apply scheduler modifications"""
    """can only be performed after the profile has been loaded"""
    model = mw.col.models.byName(OLC_MODEL)
    if not model:
        model = addModel(mw.col)
        loadConfig()
    Scheduler._burySiblings = wrap(
        Scheduler._burySiblings, myBurySiblings, "around")

def myBurySiblings(self, card, _old):
    """Skip same-day spacing for new cards if sibling burying disabled"""
    if (not card.model()["name"] == OLC_MODEL
            or not mw.col.conf["olcloze"].get("schedmod", False)):
        return _old(self,card)
    toBury = []
    nconf = self._newConf(card)
    buryNew = nconf.get("bury", True)
    rconf = self._revConf(card)
    buryRev = rconf.get("bury", True)
    # loop through and remove from queues
    for cid,queue in self.col.db.execute("""
select id, queue from cards where nid=? and id!=?
and (queue=0 or (queue=2 and due<=?))""",
            card.nid, card.id, self.today):
        if queue == 2:
            if buryRev:
                toBury.append(cid)
            # if bury disabled, we still discard reviews to give same-day spacing
            try:
                self._revQueue.remove(cid)
            except ValueError:
                pass
        else:
            # don't discard new cards if bury disabled
            if buryNew:
                toBury.append(cid)
                try:
                    self._newQueue.remove(cid)
                except ValueError:
                    pass
            else:
                pass
    # then bury
    if toBury:
        self.col.db.execute(
            "update cards set queue=-2,mod=?,usn=? where id in "+ids2str(toBury),
            intTime(), self.col.usn())
        self.col.log(toBury)

# Menus

options_action = QAction("Cloze Over&lapper Options...", mw)
options_action.triggered.connect(lambda _, m=mw: onCgOptions(m))
mw.form.menuTools.addAction(options_action)

# Hooks

addHook("profileLoaded", setupAddon)
addHook("setupEditorButtons", onSetupButtons)
Editor.onOlClozeButton = onOlClozeButton
Editor.onInsertMultipleClozes = onInsertMultipleClozes
Editor.onCloze = wrap(Editor.onCloze, onInsertCloze, "around")