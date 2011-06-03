# Copyright 2009 University of Alaska Anchorage Experimental Economics
# Laboratory
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import math
from decimal import Decimal

from peet.server import servernet
from GameControl import GameControl
from peet.server import GroupData

class TestControl(GameControl):

    """Test game controller."""

    # name is what appears in the drop-down menu for choosing the experiment
    # type in the parameter editor.
    # description is currently unused.
    name = "Test game controller"
    description = "A game controller just for testing."

    def __init__(self, server):
        """
        @type server: peet.server.frame.Frame
        """
        GameControl.__init__(self, server)

        self.server.enableChat()

    def getNumPlayers(self):
        return self.params['numPlayers']

    def getRounding(self):
        return self.params['rounding']
    
    def getShowUpPayment(self):
        return Decimal(str(self.params['showUpPayment']))\
                .quantize(Decimal('0.01'))

    def runRound(self):
        messages = []
        for i in range(len(self.clients)):
            mes = {'type': 'gm', 'question': 'How much money do you want?'}
            messages.append(mes)

        replies = self.askAllPlayers(messages)

        # Add payoffs
        for i, reply in enumerate(replies):
            self.clients[i].earnings += reply['amount'] / Decimal('100.00')

        if self.roundNum == self.params['numRounds'] - 1:
            return False
        else:
            return True
