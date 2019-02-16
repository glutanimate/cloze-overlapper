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
Modifications to Anki's scheduling
"""

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

from .libaddon.platform import ANKI20

from anki.sched import Scheduler as SchedulerV1

if ANKI20:
    SCHEDULERS = (SchedulerV1, )
else:
    from anki.schedv2 import Scheduler as SchedulerV2
    SCHEDULERS = (SchedulerV1, SchedulerV2)

from anki.utils import ids2str, intTime
from anki.hooks import wrap

from aqt import mw
from .template import checkModel


# Scheduling

def myBurySiblings(self, card, _old):
    """Skip sibling burying for our note type if so configured"""
    # <MODIFICATION>
    if not checkModel(card.model(), fields=False, notify=False):
        return _old(self, card)
    sched_conf = mw.col.conf["olcloze"].get("sched", None)
    if not sched_conf:
        return _old(self, card)
    override_new, override_review, bury_full = sched_conf
    if override_new and override_review:
        # sibling burying disabled entirely
        return
    # </MODIFICATION>
    toBury = []
    nconf, rconf = self._newConf(card), self._revConf(card)
    buryNew, buryRev = nconf.get("bury", True), rconf.get("bury", True)
    # loop through and remove from queues
    for cid, queue in self.col.db.execute("""
select id, queue from cards where nid=? and id!=?
and (queue=0 or (queue=2 and due<=?))""", card.nid, card.id, self.today):
        if queue == 2:
            # <MODIFICATION>
            if override_review:
                continue
            # </MODIFICATION>
            if buryRev:
                toBury.append(cid)
            try:
                self._revQueue.remove(cid)
            except ValueError:
                pass
        else:
            # <MODIFICATION>
            if override_new:
                continue
            # </MODIFICATION>
            if buryNew:
                toBury.append(cid)
            try:
                self._newQueue.remove(cid)
            except ValueError:
                pass
    # then bury
    if toBury:
        # <MODIFICATION>
        if mw.col.schedVer() == 1:
            self.col.db.execute(
                "update cards set queue=-2,mod=?,usn=? where id in " +
                ids2str(toBury),
                intTime(), self.col.usn())
            self.col.log(toBury)
        elif mw.col.schedVer() == 2:
            self.buryCards(toBury, manual=False)
        # </MODIFICATION>


def initializeScheduler():
    for scheduler in SCHEDULERS:
        scheduler._burySiblings = wrap(
            scheduler._burySiblings, myBurySiblings, "around")
