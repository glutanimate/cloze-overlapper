# -*- coding: utf-8 -*-

"""
This file is part of the Cloze Overlapper add-on for Anki

Note Type Handler

Copyright: Glutanimate 2016-2017
License: GNU AGPL, version 3 or later; https://www.gnu.org/licenses/agpl-3.0.en.html
"""

from anki.consts import *
from .consts import *

card_front = """\
<div class="front">
  {{#Title}}<div class="title">{{Title}}</div>{{/Title}}
  <div class="text">
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
    <div class="hidden">
       <div>{{Original}}</div>
    </div>
  </div>
</div>\
"""

card_back = """\
<div class="back">
  {{#Title}}<div class="title">{{Title}}</div>{{/Title}}
  <div class="text">
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
    <div class="hidden">{{Original}}</div>
  </div>
  <div class="extra"><hr></div>
  <div class="text"><div class="fullhint">{{hint:Original}}</div></div>
  <div class="extra">
    {{#Remarks}}
    <div class="extra-entry">
      <div class="extra-descr">Remarks</div><div>{{Remarks}}</div>
    </div>
    {{/Remarks}}
    {{#Sources}}
    <div class="extra-entry">
      <div class="extra-descr">Sources</div><div>{{Sources}}</div>
    </div>
    {{/Sources}}
  </div>
</div>
<script>
  // remove cloze syntax from revealed hint
  var hint = document.querySelector('.fullhint>[id^="hint"]')
  var html = hint.innerHTML.replace(/\[\[oc(\d+)::(.*?)(::(.*?))?\]\]/mg, "$2")
  hint.innerHTML = html
  // scroll to cloze
  document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function(){
      const cloze1 = document.getElementsByClassName("cloze")[0];
      const rect = cloze1.getBoundingClientRect();
      const absTop = rect.top + window.pageYOffset;
      const absBot = rect.bottom + window.pageYOffset;
      if (absBot >= window.innerHeight) {
        const height = rect.top - rect.bottom
        const middle = absTop - (window.innerHeight/2) - (height/2);
        window.scrollTo(0, middle);};
    }, 1);
  }, false);
</script>\
"""

card_css = """\
/* general card style */

html {
  /* scrollbar always visible in order to prevent shift when revealing answer*/
  overflow-y: scroll;
}

.card {
  font-family: "Helvetica LT Std", Helvetica, Arial, Sans;
  font-size: 150%;
  text-align: center;
  color: black;
  background-color: white;
}

/* general layout */

.text {
  /* center left-aligned text on card */
  display: inline-block;
  align: center;
  text-align: left;
  margin: auto;
  max-width: 40em;
}

.hidden {
  /* guarantees a consistent width across front and back */
  font-weight: bold;
  display: block;
  line-height:0;
  height: 0;
  overflow: hidden;
  visibility: hidden;
}

.title {
  font-weight: bold;
  font-size: 1.1em;
  margin-bottom: 1em;
  text-align: center;
}

/* clozes */

.cloze {
  /* regular cloze deletion */
  font-weight: bold;
  color: #0048FF;
}

/* original text reveal hint */

.fullhint a {
  color: #0048FF;
}

.card21 .fullhint{
  /* no need to display hint on last card */
  display:none;
}

/* additional fields */

.extra{
  margin-top: 0.5em;
  margin: auto;
  max-width: 40em;
}

.extra-entry{
  margin-top: 0.8em;
  font-size: 0.9em;
  text-align:left;
}

.extra-descr{
  margin-bottom: 0.2em;
  font-weight: bold;
  font-size: 1em;
}\
"""

def addModel(col):
    """Add add-on note type to collection"""
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
    """Update add-on card templates"""
    print("Updating %s card template".format(OLC_MODEL))
    model = col.models.byName(OLC_MODEL)
    template = model['tmpls'][0]
    template['qfmt'] = card_front
    template['afmt'] = card_back
    model['css'] = card_css
    col.models.save()
    return model