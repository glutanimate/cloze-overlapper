# -*- coding: utf-8 -*-

"""
This file is part of the Cloze Overlapper add-on for Anki

Copyright: Glutanimate 2016-2017
License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
"""

import sys
reload(sys)  
sys.setdefaultencoding('utf8')

from aqt import editor
from aqt.utils import tooltip
from anki.hooks import addHook

overlapping_cloze_note_type = u"E-Lückentext-OL-ns"
overlapping_cloze_fields_prefix = "Text"
overlapping_cloze_fields_fullcloze = "Full"

ol_cloze_max = 20
ol_cloze_no_context_first = False
ol_cloze_no_context_last = False
ol_cloze_incremental_ends = False

def generateOverlappingClozes(self, text):
    lines = text.splitlines()
    total = len(lines)
    fields = []
    htmlBefore = """<div><ol type="1" start="1" style="margin-left: 20px; ">"""
    htmlAfter = """</ol></div>"""
    # regular cloze fields
    for idx in range(0, ol_cloze_max):
        if idx >= total:
            # delete contents of unused fields
            fields.append("")
            continue
        line = lines[idx]
        field = []
        context = None
        cloze = None
        cor = 0
        if idx != 0:
            # add in older lines as dots
            field += (idx-1) * ["..."]
            # add previous line as context if available
            context = lines[idx-1]
            field.append(context)
        # add current line as cloze
        cloze = "{{c%d::%s}}" % (idx+1, line)
        field.append(cloze)

        '''uncomment this to add the next line as second context'''
        # if idx != total-1:
        #     context2 = lines[idx+1]
        #     field.append(context2)
        #     cor = 1

        # add in other lines as dots
        field += (total-idx-1-cor) * ["..."]
        # format lines as ordered list
        fields.append(
            htmlBefore
            + '\n'.join('<li>{0}</li>'.format(l) for l in field)
            + htmlAfter)
    # full cloze field
    lineFormat = "<li>{{{{c%s::{0}}}}}</li>" % str(idx+2) # double {} to escape
    fullCloze = htmlBefore + '\n'.join(lineFormat.format(l) for l in lines) + htmlAfter

    return {'fields': fields, 'fullCloze': fullCloze}

def getClozeStart(idx, target, total):
    if idx < target or idx > total:
        return 0
    return idx-target

def getBeforeStart(idx, target, total, start_c):
    if start_c < 1 or (ol_cloze_no_context_last and idx == total):
        return None
    if target == "a" or target > start_c:
        return 0
    return start_c-target

def getAfterEnd(idx, target, total):
    left = total - idx
    if left < 1 or (ol_cloze_no_context_first and idx == 1):
        return None
    if target == "a" or target > left:
        return total
    return idx+target

def generateClozes(self, text, options):
    before, prompt, after = options
    print options
    lines = unicode(text, "utf-8").splitlines()
    length = len(lines)
    if ol_cloze_incremental_ends:
        total = length + prompt - 1
        start = 1
    else:
        total = length - prompt
        start = prompt
    if total > ol_cloze_max:
        print "Error: more clozes than the note type can handle"
        return
    fields = []
    cloze_format = u"{{c%i::%s}}"
    for idx in range(start,total+1):
        field = ["..."] * total
        start_c = getClozeStart(idx, prompt, total)
        start_b = getBeforeStart(idx, before, total, start_c)
        end_a = getAfterEnd(idx, after, total)
        print start_b, start_c, end_a
        if start_b is not None:
            field[start_b:start_c] = lines[start_b:start_c]
        field[start_c:idx] = [cloze_format % (idx, l) for l in lines[start_c:idx]]
        if end_a is not None:
            field[idx:end_a] = lines[idx:end_a]
        fields.append(field)
    if ol_cloze_max > total:
        # delete contents of unused fields
        fields = fields + [""] * (ol_cloze_max - total)
    full = [cloze_format % (ol_cloze_max+1, l) for l in lines]

    return fields, full

def insertOverlappingCloze(self):
    # make sure the right model is set
    modelName = self.note.model()["name"]
    if modelName != overlapping_cloze_note_type:
        tooltip(u"Can only generate overlapping clozes on<br>%s" 
            % overlapping_cloze_note_type)
        return False

    selection = self.web.selectedText()
    
    # make sure we have a selection
    if not selection:
        tooltip("Please select some lines")
        return False

    # make sure the right number of lines are selected
    if not 2 <= selection.count("\n") <= ol_cloze_max-1:
        tooltip("Please select between 3 and %d lines" 
            % ol_cloze_max )
        return False

    retDict = self.generateOverlappingClozes(selection)

    fields = retDict["fields"]
    fullCloze = retDict ["fullCloze"]

    for idx, field in enumerate(fields):
        fieldName = overlapping_cloze_fields_prefix + str(idx+1)
        self.note[fieldName] = field

    self.note[overlapping_cloze_fields_fullcloze] = fullCloze

    # set original selection to ordered list and save field
    self.web.eval("""
        var parNode = window.getSelection().focusNode.parentNode;
        if (parNode.toString() !== "[object HTMLLIElement]") {
            document.execCommand('insertOrderedList');
            var olElem = window.getSelection().focusNode.parentNode;
            if (olElem.toString() !== "[object HTMLOListElement]") {
                olElem = olElem.parentNode;
            }
            olElem.setAttribute("type", "1");
            olElem.setAttribute("start", "1");
            olElem.style.marginLeft = "20px";
        }
        if (currentField) {
          saveField("key");
        }
        """)
    self.loadNote()

def onSetupButtons(self):
    self._addButton("Cloze Overlapper", self.insertOverlappingCloze,
        _("Alt+Shift+C"), "Insert Overlapping Clozes (Alt+Shift+C)", 
        text="[.]]", size=True)

editor.Editor.insertOverlappingCloze = insertOverlappingCloze
editor.Editor.generateOverlappingClozes = generateOverlappingClozes
addHook("setupEditorButtons", onSetupButtons)