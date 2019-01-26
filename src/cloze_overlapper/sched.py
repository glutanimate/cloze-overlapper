# -*- coding: utf-8 -*-

# Cloze Overlapper Add-on for Anki
#
# Copyright (C)  2016-2019 Aristotelis P. <https://glutanimate.com/>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version, with the additions
# listed at the end of the accompanied license file.
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
# terms and conditions of the GNU Affero General Public License which
# accompanied this program.
#
# If not, please request a copy through one of the means of contact
# listed here: <https://glutanimate.com/contact/>.
#
# Any modifications to this file must keep this entire header intact.

"""
Modifications to Anki's scheduling
"""

from anki.sched import Scheduler
from anki.utils import ids2str, intTime
from anki.hooks import wrap

from aqt import mw

from .template import checkModel


# Scheduling

def myBurySiblings(self, card, _old):
    """Skip sibling burying for our note type if so configured"""
    if not checkModel(card.model(), fields=False, notify=False):
        return _old(self, card)
    sched_conf = mw.col.conf["olcloze"].get("sched", None)
    if not sched_conf:
        return _old(self, card)
    override_new, override_review, bury_full = sched_conf
    if override_new and override_review:
        # sibling burying disabled entirely
        return
    toBury = []
    nconf, rconf = self._newConf(card), self._revConf(card)
    buryNew, buryRev = nconf.get("bury", True), rconf.get("bury", True)
    # loop through and remove from queues
    for cid, queue in self.col.db.execute("""
select id, queue from cards where nid=? and id!=?
and (queue=0 or (queue=2 and due<=?))""",
                                          card.nid, card.id, self.today):
        if queue == 2:
            if override_review:
                continue
            if buryRev:
                toBury.append(cid)
            try:
                self._revQueue.remove(cid)
            except ValueError:
                pass
        else:
            if override_new:
                continue
            if buryNew:
                toBury.append(cid)
            try:
                self._newQueue.remove(cid)
            except ValueError:
                pass
    # then bury
    if toBury:
        self.col.db.execute(
            "update cards set queue=-2,mod=?,usn=? where id in " +
            ids2str(toBury),
            intTime(), self.col.usn())
        self.col.log(toBury)


def initializeScheduler():
    Scheduler._burySiblings = wrap(
        Scheduler._burySiblings, myBurySiblings, "around")
