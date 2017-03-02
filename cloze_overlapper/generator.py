# -*- coding: utf-8 -*-

"""
This file is part of the Cloze Overlapper add-on for Anki

Overlapping Cloze Generator

Copyright: Glutanimate 2016-2017
License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
"""

class ClozeGenerator(object):
    """Cloze generator"""

    cformat = "{{c%i::%s}}"

    def __init__(self, setopts, maxfields):
        self.maxfields = maxfields
        self.before, self.prompt, self.after = setopts[0]
        self.options = setopts[1]
        self.start = None
        self.total = None

    def generate(self, items, original=None, keys=None):
        """Returns an array of lists with overlapping cloze deletions"""
        length = len(items)
        if self.prompt > length:
            return 0, None, None
        if self.options[2]:
            self.total = length + self.prompt - 1
            self.start = 1
        else:
            self.total = length
            self.start = self.prompt
        if self.total > self.maxfields:
            return None, None, self.total

        fields = []

        for idx in range(self.start, self.total+1):
            snippets = ["..."] * length
            start_c = self.getClozeStart(idx)
            start_b = self.getBeforeStart(idx, start_c)
            end_a = self.getAfterEnd(idx)

            if start_b is not None:
                snippets[start_b:start_c] = self.removeHints(items[start_b:start_c])
            if end_a is not None:
                snippets[idx:end_a] = self.removeHints(items[idx:end_a])
            snippets[start_c:idx] = self.formatCloze(items[start_c:idx], idx-self.start+1)

            field = self.formatSnippets(snippets, original, keys)
            fields.append(field)
        nr = len(fields)
        if self.maxfields > self.total: # delete contents of unused fields
            fields = fields + [""] * (self.maxfields - len(fields))
        fullsnippet = self.formatCloze(items, self.maxfields + 1)
        full = self.formatSnippets(fullsnippet, original, keys)
        return fields, full, nr

    def formatCloze(self, items, nr):
        """Apply cloze deletion syntax to item"""
        res = []
        for item in items:
            if not hasattr(item, "__iter__"): # not an iterable
                res.append(self.cformat % (nr, item))
            else:
                res.append([self.cformat % (nr, i) for i in item])
        return res

    def removeHints(self, items):
        """Removes cloze hints from items"""
        res = []
        for item in items:
            if not hasattr(item, "__iter__"): # not an iterable
                res.append(item.split("::")[0])
            else:
                res.append([i.split("::")[0] for i in item])
        return res

    def formatSnippets(self, snippets, original, keys):
        """Insert snippets back into original text, if available"""
        html = original
        if not html:
            return snippets
        for nr, phrase in zip(keys, snippets):
            if phrase == "...": # placeholder, replace all instances
                html = html.replace("{{" + nr + "}}", phrase)
            elif not hasattr(phrase, "__iter__"): # not an iterable
                html = html.replace("{{" + nr + "}}", phrase, 1)
            else:
                for item in phrase:
                    html = html.replace("{{" + nr + "}}", item, 1)
        return html

    def getClozeStart(self, idx):
        """Determine start index of clozed items"""
        if idx < self.prompt or idx > self.total:
            return 0
        return idx-self.prompt # looking back from current index

    def getBeforeStart(self, idx, start_c):
        """Determine start index of preceding context"""
        if (self.before == 0 or start_c < 1 
          or (self.before and self.options[1] and idx == self.total)):
            return None
        if self.before is None or self.before > start_c:
            return 0
        return start_c-self.before

    def getAfterEnd(self, idx):
        """Determine end index of following context"""
        left = self.total - idx
        if (self.after == 0 or left < 1
          or (self.after and self.options[0] and idx == self.start)):
            return None
        if self.after is None or self.after > left:
            return self.total
        return idx+self.after