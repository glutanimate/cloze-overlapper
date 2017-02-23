# -*- coding: utf-8 -*-

"""
This file is part of the Cloze Overlapper add-on for Anki

Common reusable utilities

Copyright: Glutanimate 2016-2017
License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
"""

from aqt.utils import showWarning, tooltip

def warnUser(reason, text):
    showWarning(("<b>%s Error</b>: " % reason) + text, title="Cloze Overlapper")

def showTT(title, text, period=3000, parent=None):
    tooltip(u"<b>%s</b>: %s" % (title, text), period, parent)