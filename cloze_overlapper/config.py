# -*- coding: utf-8 -*-

"""
This file is part of the Cloze Overlapper add-on for Anki

Handles user-set options.

Copyright: Glutanimate 2016-2017
License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
"""

import os

from aqt.qt import *
from PyQt4 import QtCore, QtGui, uic


default_conf = {
    "settings": (1,1,0),
    "ncFirst": False,
    "ncLast": False,
    "incrEnds": False,
    "version": 0.1
}

class OlClozeOpts(QDialog):
    """Options Menu"""
    def __init__(self, mw):
        super(OlClozeOpts, self).__init__(parent=mw)
        # load qt-designer form:
        uic.loadUi(os.path.join(os.path.dirname(os.path.abspath(__file__))
            , "forms", "options.ui"), self)
        self.buttonBox.accepted.connect(self.onAccept)
        self.buttonBox.rejected.connect(self.onReject)
        self.buttonBox.helpRequested.connect(self.onHelp)
        self.buttonBox.button(
            QDialogButtonBox.RestoreDefaults).clicked.connect(self.onRestore)

    def onAccept(self):
        print "accepted"
        self.close()

    def onReject(self):
        print "rejected"
        self.close()

    def onHelp(self):
        print "help"

    def onRestore(self):
        print "restore"