# -*- coding: utf-8 -*-

# Cloze Overlapper Add-on for Anki
#
# Copyright (C)  2016-2019 Aristotelis P. <https://glutanimate.com/>
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
Additions to Anki's note editor
"""

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

import re

from anki.hooks import wrap, addHook

from aqt.qt import *
from aqt import mw
from aqt.editor import Editor
from aqt.addcards import AddCards
from aqt.editcurrent import EditCurrent
from aqt.utils import tooltip, showInfo

from .libaddon.platform import ANKI20, PATH_ADDON

from .overlapper import ClozeOverlapper
from .gui.options_note import OlcOptionsNote
from .template import checkModel
from .config import config
from .utils import showTT


# Hotkey definitions

olc_hotkey_generate = "Alt+Shift+C"  # Cloze generation/preview
olc_hotkey_options = "Alt+Shift+O"  # Note-specific settings
olc_hotkey_cremove = "Alt+Shift+U"  # Remove selected clozes
olc_hotkey_olist = "Ctrl+Alt+Shift+."  # Toggle ordered list
olc_hotkey_ulist = "Ctrl+Alt+Shift+,"  # Toggle unordered list
olc_hotkey_mcloze = "Ctrl+Shift+K"  # Multi-line cloze
olc_hotkey_mclozealt = "Ctrl+Alt+Shift+K"  # Multi-line cloze alt

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



# EDITOR

# Button callback wrappers

# anki21 executes JS asynchronously. In order to assure that we are working
# with the most recent field contents, we use a decorator to fire the
# button/hotkey callback after evaluating the pertinent JS:

def editorSaveThen(callback):
    if ANKI20:
        return callback

    def onSaved(editor, *args, **kwargs):
        # uses evalWithCallback internally:
        editor.saveNow(lambda: callback(editor, *args, **kwargs))

    return onSaved

# In some cases we need to apply changes to field HTML via JS before
# proceeding:

def JSformatFieldThen(editor, field_idx, commands, callback):

    cmd_str = "\n".join("""document.execCommand("{}");""".format(cmd)
                        for cmd in commands)

    js = """
focusField(%(field_idx)d);
%(cmd_str)s
saveField('key');
""" % {"field_idx": field_idx, "cmd_str": cmd_str}
    
    if ANKI20:
        editor.web.eval(js)
        callback()
    else:
        editor.web.evalWithCallback(js, lambda res: callback())


# Utility

def refreshEditor(editor):
    editor.loadNote()
    focus = editor.currentField or 0
    editor.web.eval("focusField({});".format(focus))

# Button callbacks

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


@editorSaveThen
def onInsertMultipleClozes(self):
    """Wraps each line in a separate cloze"""
    model = self.note.model()
    # check that the model is set up for cloze deletion
    if not re.search('{{(.*:)*cloze:', model['tmpls'][0]['qfmt']):
        if self.addMode:
            tooltip("Warning, cloze deletions will not work until "
                    "you switch the type at the top to Cloze.")
        else:
            showInfo("""\
To make a cloze deletion on an existing note, you need to change it \
to a cloze type first, via Edit>Change Note Type.""")
            return
    if checkModel(model, fields=False, notify=False):
        cloze_re = "\[\[oc(\d+)::"
        wrap_pre, wrap_post = "[[oc", "]]"
    else:
        cloze_re = "\{\{c(\d+)::"
        wrap_pre, wrap_post = "{{c", "}}"
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


@editorSaveThen
def onRemoveClozes(self):
    """Remove cloze markers and hints from selected text"""
    if checkModel(self.note.model(), fields=False, notify=False):
        cloze_re = r"\[\[oc(\d+)::(.*?)(::(.*?))?\]\]"
    else:
        cloze_re = r"\{\{c(\d+)::(.*?)(::(.*?))?\}\}"
    self.web.eval(js_cloze_remove % cloze_re)


@editorSaveThen
def onOlOptionsButton(self):
    """Invoke note-specific options dialog"""
    if not checkModel(self.note.model()):
        return False
    options = OlcOptionsNote(self.parentWindow)
    options.exec_()


@editorSaveThen
def onOlClozeButton(editor, markup=None, parent=None):
    """Invokes an instance of the main add-on class"""
    if not checkModel(editor.note.model()):
        return False
    
    def onFieldReady():
        overlapper = ClozeOverlapper(editor.note, markup=markup,
                                     parent=parent)
        overlapper.add()
        refreshEditor(editor)

    if markup:
        field_map = mw.col.models.fieldMap(editor.note.model())
        og_fld_name = config["synced"]["flds"]["og"]
        og_fld_idx = field_map[og_fld_name][0]

        field_commands = ["selectAll", "insertOrderedList" if markup == "ol"
                          else "insertUnorderedList"]
        return JSformatFieldThen(editor, og_fld_idx,
                                 field_commands, onFieldReady)
    
    return onFieldReady()

# ADDCARDS / EDITCURRENT

# Callbacks

def onAddCards(self, _old):
    """Automatically generate overlapping clozes before adding cards"""
    editor = self.editor
    note = editor.note

    if not note or not checkModel(note.model(), notify=False):
        return _old(self)

    if ANKI20:
        editor.saveNow()

    overlapper = ClozeOverlapper(editor.note, silent=True)
    ret, total = overlapper.add()

    if ret is False:
        return

    refreshEditor(editor)

    oldret = _old(self)
    if total:
        showTT("Info", "Added %d overlapping cloze cards" % total, period=1000)

    return oldret


def onEditCurrent(editcurrent, _old):
    """Automatically update overlapping clozes when editing cards"""
    editor = editcurrent.editor
    note = editor.note

    if not note or not checkModel(note.model(), notify=False):
        return _old(editcurrent)

    if ANKI20:
        editor.saveNow()

    overlapper = ClozeOverlapper(editor.note, silent=True)
    ret, total = overlapper.add()

    # returning here won't stop the window from being rejected, so we simply
    # accept whatever changes the user performed, even if the generator
    # did not fire

    oldret = _old(editcurrent)
    if total:
        showTT("Info", "Updated %d overlapping cloze cards" %
               total, period=1000)

    return oldret


def onAddNote(addcards, note, _old):
    """Suspend full cloze card if option active"""
    note = _old(addcards, note)
    if not note or not checkModel(note.model(), fields=False, notify=False):
        return note
    sched_conf = config["synced"].get("sched", None)
    if not sched_conf or not sched_conf[2]:
        return note
    maxfields = ClozeOverlapper.getMaxFields(
        note.model(), config["synced"]["flds"]["tx"])
    last = note.cards()[-1]
    if last.ord == maxfields:  # is full cloze (ord starts at 0)
        mw.col.sched.suspendCards([last.id])
    return note


# BUTTONS / HOTKEYS

icon_path = os.path.join(PATH_ADDON, "gui", "resources", "icons")
icon_generate = os.path.join(icon_path, "oc_generate.svg")
icon_options = os.path.join(icon_path, "oc_options.svg")
icon_remove = os.path.join(icon_path, "oc_remove.svg")


tooltip_generate = "Generate overlapping clozes ({})".format(
    olc_hotkey_generate)
tooltip_options = "Overlapping cloze options ({})".format(
    olc_hotkey_options)
tooltip_remove = "Remove all cloze markers in selected text ({})".format(
    olc_hotkey_cremove)

def onSetupEditorButtons20(editor):
    """Add buttons and hotkeys to the editor widget"""

    b = editor._addButton("OlCloze",
                          editor.onOlClozeButton, olc_hotkey_generate,
                          tooltip_generate, size=True)
    b.setIcon(QIcon(icon_generate))
    b.setFixedWidth(24)

    b = editor._addButton("OlOptions",
                          editor.onOlOptionsButton, olc_hotkey_options,
                          tooltip_options, size=True)
    b.setIcon(QIcon(icon_options))
    b.setFixedWidth(24)

    b = editor._addButton("RemoveClozes",
                          editor.onRemoveClozes, olc_hotkey_cremove,
                          tooltip_remove, size=True)
    b.setIcon(QIcon(icon_remove))
    b.setFixedWidth(24)

    setupAdditionalHotkeys(editor)


def onSetupEditorButtons21(buttons, editor):
    """Add buttons and hotkeys"""

    # bind to editor.olc_hotkey_generate because anki21 passes
    # editor instance by default
    b = editor.addButton(icon_generate, "OlCloze", onOlClozeButton,
                         tooltip_generate, keys=olc_hotkey_generate)
    buttons.append(b)

    b = editor.addButton(icon_options, "OlOptions", onOlOptionsButton,
                         tooltip_options, keys=olc_hotkey_options)
    buttons.append(b)

    b = editor.addButton(icon_remove, "RemoveClozes", onRemoveClozes,
                         tooltip_remove, keys=olc_hotkey_cremove)
    buttons.append(b)

    setupAdditionalHotkeys(editor)

    return buttons

def setupAdditionalHotkeys(editor):
    add_ol_cut = QShortcut(QKeySequence(olc_hotkey_olist), editor.widget)
    add_ol_cut.activated.connect(lambda o="ol": onOlClozeButton(editor, o))
    add_ul_cut = QShortcut(QKeySequence(olc_hotkey_ulist), editor.widget)
    add_ul_cut.activated.connect(lambda o="ul": onOlClozeButton(editor, o))

    mult_cloze_cut1 = QShortcut(QKeySequence(
        olc_hotkey_mcloze), editor.widget)
    mult_cloze_cut1.activated.connect(lambda: onInsertMultipleClozes(editor))
    mult_cloze_cut2 = QShortcut(QKeySequence(
        olc_hotkey_mclozealt), editor.widget)
    mult_cloze_cut2.activated.connect(lambda: onInsertMultipleClozes(editor))


# MAIN

def initializeEditor():
    # Editor widget
    Editor.onCloze = wrap(Editor.onCloze, onInsertCloze, "around")
    Editor.onOlClozeButton = onOlClozeButton
    Editor.onOlOptionsButton = onOlOptionsButton
    Editor.onInsertMultipleClozes = onInsertMultipleClozes
    Editor.onRemoveClozes = onRemoveClozes
    if ANKI20:
        addHook("setupEditorButtons", onSetupEditorButtons20)
    else:
        addHook("setupEditorButtons", onSetupEditorButtons21)

    # AddCard / EditCurrent windows
    AddCards.addNote = wrap(AddCards.addNote, onAddNote, "around")
    if ANKI20:
        AddCards.addCards = wrap(AddCards.addCards, onAddCards, "around")
        EditCurrent.onSave = wrap(EditCurrent.onSave, onEditCurrent, "around")
    else:
        # always use the methods that are fired on editor save:
        AddCards._addCards = wrap(AddCards._addCards, onAddCards, "around")
        EditCurrent._saveAndClose = wrap(EditCurrent._saveAndClose,
                                         onEditCurrent, "around")
