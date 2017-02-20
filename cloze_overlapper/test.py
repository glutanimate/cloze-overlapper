# -*- coding: utf-8 -*-

ol_cloze_dfltopts = (1,1,0)

def getOptions(field):
    options = field.replace(" ", "").split(",")
    dflts = ol_cloze_dfltopts
    if not field or not options:
        return ol_cloze_dfltopts, False
    opts = []
    for i in options:
        try:
            opts.append(int(i))
        except ValueError:
            opts.append(None)
    length = len(opts)
    if length == 3 and isinstance(opts[1], int):
        return tuple(opts), True
    elif length == 2 and isinstance(opts[0], int):
        return (opts[1], opts[0], opts[1]), True
    elif length == 1 and isinstance(opts[0], int):
        return (dflts[0], opts[0], dflts[2]), True
    return False, False

a, b = getOptions("2,m,c")
print a, b

ol_cloze_max = 20
ol_cloze_no_context_first = False
ol_cloze_no_context_last = False
ol_cloze_incremental_ends = True


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

def generateClozes(self, items, options):
    before, prompt, after = options
    length = len(items)
    if ol_cloze_incremental_ends:
        total = length + prompt - 1
        start = 1
    else:
        total = length
        start = prompt
    if total > ol_cloze_max:
        print "Error: more clozes than the note type can handle"
        return False
    fields = []
    cloze_format = u"{{c%i::%s}}"
    for idx in range(start,total+1):
        field = ["..."] * length
        start_c = getClozeStart(idx, prompt, total)
        start_b = getBeforeStart(start, idx, before, total, start_c)
        end_a = getAfterEnd(start, idx, after, total)
        print start_b, start_c, end_a
        if start_b is not None:
            field[start_b:start_c] = items[start_b:start_c]
        if end_a is not None:
            field[idx:end_a] = items[idx:end_a]
        field[start_c:idx] = [cloze_format % (idx-start+1, l) for l in items[start_c:idx]]
        fields.append(field)
    if ol_cloze_max > total: # delete contents of unused fields
        fields = fields + [""] * (ol_cloze_max - len(fields))
    full = [cloze_format % (ol_cloze_max+1, l) for l in items]

    print "\n".join([" ".join(lst) for lst in fields])
    print " ".join(full)

    return fields, full
 
text="""a
b
c
d
e
f
g
h
i"""

lines = unicode(text, "utf-8").splitlines()
generateClozes(None, lines, (2,3,2))