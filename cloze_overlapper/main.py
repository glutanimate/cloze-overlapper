# -*- coding: utf-8 -*-

"""
This file is part of the Cloze Overlapper add-on for Anki

Copyright: Glutanimate 2016-2017
License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
"""

from aqt import editor
from aqt.utils import tooltip
from anki.utils import stripHTML
from anki.hooks import addHook

from BeautifulSoup import BeautifulSoup


overlapping_cloze_note_type = u"E-Lückentext-OL-ns"
overlapping_cloze_fields_prefix = "Text"
overlapping_cloze_fields_fullcloze = "Full"

ol_cloze_max = 20
ol_cloze_dfltopts = (1,1,0)
ol_cloze_no_context_first = False
ol_cloze_no_context_last = False
ol_cloze_incremental_ends = False
ol_cloze_model = u"E-Lückentext-OL-ns"
ol_cloze_fldprefix = "Text"
ol_cloze_fldfull = "Full"
ol_cloze_fldoptions = "Options"


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

def getOptions(field):
    options = field.replace(" ", "").split(",")
    dflts = ol_cloze_dfltopts
    if not field or not options:
        return ol_cloze_dfltopts, True
    opts = []
    for i in options:
        try:
            opts.append(int(i))
        except ValueError:
            opts.append(None)
    length = len(opts)
    if length == 3 and isinstance(opts[1], int):
        return tuple(opts), False
    elif length == 2 and isinstance(opts[0], int):
        return (opts[1], opts[0], opts[1]), False
    elif length == 1 and isinstance(opts[0], int):
        return (dflts[0], opts[0], dflts[2]), False
    return False, False

def getClozeStart(idx, target, total):
    if idx < target or idx > total:
        return 0
    return idx-target

def getBeforeStart(start, idx, target, total, start_c):
    if (target == 0 or start_c < 1 
      or (target and ol_cloze_no_context_last and idx == total)):
        return None
    if target is None or target > start_c:
        return 0
    return start_c-target

def getAfterEnd(start, idx, target, total):
    left = total - idx
    if (target == 0 or left < 1
      or (target and ol_cloze_no_context_first and idx == start)):
        return None
    if target is None or target > left:
        return total
    return idx+target

def generateOlClozes(self, items, options):
    before, prompt, after = options
    length = len(items)
    if ol_cloze_incremental_ends:
        total = length + prompt - 1
        start = 1
    else:
        total = length
        start = prompt
    if total > ol_cloze_max:
        return False
    fields = []
    cloze_format = u"{{c%i::%s}}"
    for idx in range(start,total+1):
        field = ["..."] * length
        start_c = getClozeStart(idx, prompt, total)
        start_b = getBeforeStart(start, idx, before, total, start_c)
        end_a = getAfterEnd(start, idx, after, total)
        if start_b is not None:
            field[start_b:start_c] = items[start_b:start_c]
        if end_a is not None:
            field[idx:end_a] = items[idx:end_a]
        field[start_c:idx] = [cloze_format % (idx-start+1, l) for l in items[start_c:idx]]
        fields.append(field)
    if ol_cloze_max > total: # delete contents of unused fields
        fields = fields + [""] * (ol_cloze_max - len(fields))
    full = [cloze_format % (ol_cloze_max+1, l) for l in items]

    return fields, full

def insertOverlappingCloze(self):
    # make sure the right model is set
    modelName = self.note.model()["name"]
    if modelName != ol_cloze_model:
        tooltip(u"Can only generate overlapping clozes on<br>%s" 
            % ol_cloze_model)
        return False

    # save field
    self.web.eval("""
       if (currentField) {
         saveField("key");
       }
       """)

    selection = self.note["Volltext"]
    soup = BeautifulSoup(selection)
    selection = soup.getText("\n") # will need to be updated for bs4
    items = selection.splitlines()
    
    # make sure we have a selection
    if not selection or not items:
        tooltip("Please select some lines")
        return False

    # make sure the right number of lines are selected
    if not 2 <= len(items) <= ol_cloze_max-1:
        tooltip("Please select between 3 and %d lines" 
            % ol_cloze_max )
        return False

    fld_opts = self.note[ol_cloze_fldoptions]
    options, defaults = getOptions(fld_opts)

    fields, full = self.generateOlClozes(items, options)
    if not fields:
        tooltip("Error: more clozes than the note type can handle")
        return False

    for idx, field in enumerate(fields):
        name = ol_cloze_fldprefix + str(idx+1)
        self.note[name] = "<br>".join(field)

    if defaults:
        self.note[ol_cloze_fldoptions] = ",".join(str(i) for i in ol_cloze_dfltopts)
    self.note[ol_cloze_fldfull] = "<br>".join(full)

    # save field
    self.web.eval("""
       if (currentField) {
         saveField("key");
       }
       """)
    self.loadNote()


    """
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
    """

def onSetupButtons(self):
    self._addButton("Cloze Overlapper", self.insertOverlappingCloze,
        _("Alt+Shift+C"), "Insert Overlapping Clozes (Alt+Shift+C)", 
        text="[.]]", size=True)

editor.Editor.insertOverlappingCloze = insertOverlappingCloze
editor.Editor.generateOlClozes = generateOlClozes
addHook("setupEditorButtons", onSetupButtons)