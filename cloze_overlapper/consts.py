# -*- coding: utf-8 -*-

"""
This file is part of the Cloze Overlapper add-on for Anki

Constants

Copyright: Glutanimate 2016-2017
License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
"""

# default model
OLC_MODEL = "Cloze (overlapping)"
OLC_CARD = "cloze-ol"
OLC_MAX = 20

# default fields
OLC_FLDS = {
    'og': u"Original",
    'tt': u"Title",
    'rk': u"Remarks",
    'sc': u"Sources",
    'st': u"Settings",
    'tx': u"Text",
    'fl': u"Full"
}
OLC_FLDS_IDS = ['og', 'tt', 'rk', 'sc', 'st', 'tx', 'fl']
OLC_FIDS_PRIV = ['og', 'st', 'tx', 'fl'] # non-user editable