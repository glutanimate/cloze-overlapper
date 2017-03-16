# -*- coding: utf-8 -*-

"""
This file is part of the Cloze Overlapper add-on for Anki

Common reusable utilities

Copyright: Glutanimate 2016-2017
License: GNU AGPL, version 3 or later; https://www.gnu.org/licenses/agpl-3.0.en.html
"""

from aqt.utils import showWarning, tooltip

def warnUser(reason, text):
    showWarning(("<b>%s Error</b>: " % reason) + text, title="Cloze Overlapper")

def showTT(title, text, period=3000, parent=None):
    tooltip(u"<b>%s</b>: %s" % (title, text), period, parent)