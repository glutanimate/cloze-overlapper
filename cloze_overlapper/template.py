# -*- coding: utf-8 -*-

"""
This file is part of the Cloze Overlapper add-on for Anki

Note type and card templates

Copyright: Glutanimate 2016-2017
License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
"""

from anki.consts import *
from .consts import *

card_front = """\
<div class="front">
  {{#Title}}<div class="title">{{Title}}:</div>{{/Title}}
  {{cloze:Text1}}
  {{cloze:Text2}}
  {{cloze:Text3}}
  {{cloze:Text4}}
  {{cloze:Text5}}
  {{cloze:Text6}}
  {{cloze:Text7}}
  {{cloze:Text8}}
  {{cloze:Text9}}
  {{cloze:Text10}}
  {{cloze:Text11}}
  {{cloze:Text12}}
  {{cloze:Text13}}
  {{cloze:Text14}}
  {{cloze:Text15}}
  {{cloze:Text16}}
  {{cloze:Text17}}
  {{cloze:Text18}}
  {{cloze:Text19}}
  {{cloze:Text20}}
  {{cloze:Full}}
</div>
"""

card_back = """\
<div class="back">
  {{#Title}}<div class="title">{{Title}}</div>{{/Title}}
  {{cloze:Text1}}
  {{cloze:Text2}}
  {{cloze:Text3}}
  {{cloze:Text4}}
  {{cloze:Text5}}
  {{cloze:Text6}}
  {{cloze:Text7}}
  {{cloze:Text8}}
  {{cloze:Text9}}
  {{cloze:Text10}}
  {{cloze:Text11}}
  {{cloze:Text12}}
  {{cloze:Text13}}
  {{cloze:Text14}}
  {{cloze:Text15}}
  {{cloze:Text16}}
  {{cloze:Text17}}
  {{cloze:Text18}}
  {{cloze:Text19}}
  {{cloze:Text20}}
  {{cloze:Full}}
  <div class="fullhint"><hr>{{hint:Original}}</hint>
</div>
"""

card_css = """\
.card {
  /* general card style */
  font-family: "Helvetica LT Std", Helvetica, Arial, Sans;
  font-size: 150%;
  text-align: left;
  color: black;
  background-color: white;
}

.cloze {
  /* regular cloze deletion */
  font-weight: bold;
  color: green;
}

.card21 .back .cloze {
  /* full cloze deletion */
  color: inherit;
  font-weight: inherit;
}

.title {
  font-weight: bold;
  font-size: 1.05em;
  margin-bottom: 0.5em;
}

.fullhint {
  /* hinted text hint */
  margin-top: 1em
}
"""

def addModel(col):
    models = col.models
    model = models.new(OLC_MODEL)
    model['type'] = MODEL_CLOZE
    # Add fields:
    for i in OLC_FLDS_IDS:
        if i == "tx":
            for i in range(1, OLC_MAX+1):
                fld = models.newField(OLC_FLDS["tx"]+str(i))
                fld["size"] = 12
                models.addField(model, fld)
            continue
        fld = models.newField(OLC_FLDS[i])
        if i == "st":
            fld["sticky"] = True
        if i == "fl":
            fld["size"] = 12
        models.addField(model, fld)
    # Add template
    template = models.newTemplate(OLC_CARD)
    template['qfmt'] = card_front
    template['afmt'] = card_back
    model['css'] = card_css
    model['sortf'] = 1 # set sortfield to title
    models.addTemplate(model, template)
    models.add(model)
    return model

def updateTemplate(col):
    print "Updating Cloze (overlapping) card template"
    model = col.models.byName(OLC_MODEL)
    template = model['tmpls'][0]
    template['qfmt'] = card_front
    template['afmt'] = card_back
    model['css'] = card_css
    col.models.save()
    return model