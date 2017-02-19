# -*- coding: utf-8 -*-

ol_cloze_max = 20
ol_cloze_no_context_first = False
ol_cloze_no_context_last = False
ol_cloze_incremental_ends = False


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

    print "\n".join([" ".join(lst) for lst in fields])
    print " ".join(full)
 
text="""a
b
c
d
e
f
h
i
j
k
l
m
n
o
p
q"""

generateClozes(None, text, (1,1,1))