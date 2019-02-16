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
Manages note type and templates
"""

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

from anki.consts import MODEL_CLOZE

from aqt import mw

from .config import config
from .utils import showTT, warnUser
from .consts import *

card_front = """\
<!--template
######## CLOZE OVERLAPPER DEFAULT TEMPLATE START ########
version: 1.0.0
-->

<!--
PLEASE DO NOT MODIFY THE DEFAULT TEMPLATE SECTIONS.
Any changes between the 'template' markers will be lost once
the add-on updates its template.

Copyright (C) 2016-2019 Aristotelis P. <https://glutanimate.com/>

The Cloze Overlapper card template is licensed under the CC BY-SA 4.0
license (https://creativecommons.org/licenses/by-sa/4.0/). This only
applies to the card template, not the contents of your notes.

Get Cloze Overlapper for Anki at:
https://ankiweb.net/shared/info/969733775
-->

<div class="front">
    {{#Title}}<div class="title">{{Title}}</div>{{/Title}}
    <div class="text">
        <div id="clozed">
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
        <div class="hidden">
            <div><span class="cloze">[...]</span></div>
            <div>{{Original}}</div>
        </div>
    </div>
</div>

<script>
// Scroll to cloze
function scrollToCloze () {
    const cloze1 = document.getElementsByClassName("cloze")[0];
    const rect = cloze1.getBoundingClientRect();
    const absTop = rect.top + window.pageYOffset;
    const absBot = rect.bottom + window.pageYOffset;
    if (absBot >= window.innerHeight) {
        const height = rect.top - rect.bottom
        const middle = absTop - (window.innerHeight/2) - (height/2);
        window.scrollTo(0, middle);
    };
}
if ( document.readyState === 'complete' ) {
    setTimeout(scrollToCloze, 1);
} else {
    document.addEventListener('DOMContentLoaded', function() {
        setTimeout(scrollToCloze, 1);
    }, false);
}
</script>

<!--
######## CLOZE OVERLAPPER DEFAULT TEMPLATE END ######## */
template-->

<!-- Add your customizations here: -->\
"""

card_back = """\
<!--template
######## CLOZE OVERLAPPER DEFAULT TEMPLATE START ########
version: 1.0.0
-->

<!--
PLEASE DO NOT MODIFY THE DEFAULT TEMPLATE SECTIONS.
Any changes between the 'template' markers will be lost once
the add-on updates its template.
-->

<div class="back">
    {{#Title}}<div class="title">{{Title}}</div>{{/Title}}
    <div class="text">
        <div id="clozed">
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
        <div class="hidden">
            <div><span class="cloze">[...]</span></div>
            <div>{{Original}}</div>
        </div>
    </div>
    <div class="extra"><hr></div>
    <button id="btn-reveal" onclick="olToggle();">Reveal all clozes</button>
    <div class="hidden"><div id="original">{{Original}}</div></div>
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
// Remove cloze syntax from revealed hint
var hint = document.getElementById("original");
if (hint) {
    var html = hint.innerHTML.replace(/\[\[oc(\d+)::(.*?)(::(.*?))?\]\]/mg,
                                      "<span class='cloze'>$2</span>");
    hint.innerHTML = html
};

// Scroll to cloze
function scrollToCloze () {
    const cloze1 = document.getElementsByClassName("cloze")[0];
    const rect = cloze1.getBoundingClientRect();
    const absTop = rect.top + window.pageYOffset;
    const absBot = rect.bottom + window.pageYOffset;
    if (absBot >= window.innerHeight) {
        const height = rect.top - rect.bottom
        const middle = absTop - (window.innerHeight/2) - (height/2);
        window.scrollTo(0, middle);
    };
}
if ( document.readyState === 'complete' ) {
    setTimeout(scrollToCloze, 1);
} else {
    document.addEventListener('DOMContentLoaded', function() {
        setTimeout(scrollToCloze, 1);
    }, false);
}


// Reveal full list
var olToggle = function() {
    var orig = document.getElementById('original');
    var clozed = document.getElementById('clozed');
    var origHtml = orig.innerHTML
    orig.innerHTML = clozed.innerHTML
    clozed.innerHTML = origHtml
}
</script>

<!--
######## CLOZE OVERLAPPER DEFAULT TEMPLATE END ######## */
template-->

<!-- Add your customizations here: -->
\
"""

card_css = """\
/*template
######## CLOZE OVERLAPPER DEFAULT TEMPLATE START ########
version: 1.0.0
*/

/*
PLEASE DO NOT MODIFY THE DEFAULT TEMPLATE SECTIONS.
Any changes between the 'template' markers will be lost once
the add-on updates its template.
*/

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

.card21 #btn-reveal{
  /* no need to display reveal btn on last card */
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
}

#btn-reveal {
  font-size: 0.5em;
}

.mobile #btn-reveal {
  font-size: 0.8em;
}

/*
######## CLOZE OVERLAPPER DEFAULT TEMPLATE END ########
template*/

/* Add your customizations here: */
\
"""


def checkModel(model, fields=True, notify=True):
    """Sanity checks for the model and fields"""
    mname = model["name"]
    is_olc = False
    # account for custom and imported note types:
    if mname in config["synced"]["olmdls"] or mname.startswith(OLC_MODEL):
        is_olc = True
    if notify and not is_olc:
        olc_types = sorted(set([OLC_MODEL] + config["synced"]["olmdls"]))
        showTT("Reminder", "Can only generate overlapping clozes<br>"
               "on the following note types:<br><br>{}".format(
                   ", ".join("'{0}'".format(i) for i in olc_types))
               )
    if not is_olc or not fields:
        return is_olc
    flds = [f['name'] for f in model['flds']]
    complete = True
    for fid in OLC_FIDS_PRIV:
        fname = config["synced"]["flds"][fid]
        if fid == "tx":
            # should have at least 3 text fields
            complete = all(fname + str(i) in flds for i in range(1, 4))
        else:
            complete = fname in flds
        if not complete:
            break
    if not complete:
        warnUser("Note Type", "Looks like your note type is not configured properly. "
                 "Please make sure that the fields list includes "
                 "all of the following fields:<br><br><i>%s</i>" % ", ".join(
                     config["synced"]["flds"][fid] if fid != "tx" else "Text1-TextN" for fid in OLC_FIDS_PRIV))
    return complete


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
    model['sortf'] = 1  # set sortfield to title
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


def initializeModels():
    model = mw.col.models.byName(OLC_MODEL)
    if not model:
        model = addModel(mw.col)
