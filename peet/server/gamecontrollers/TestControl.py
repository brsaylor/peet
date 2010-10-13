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

from peet.server import servernet
import GameControl
from peet.server import GroupData

class TestControl(GameControl.GameControl):

    """Test game controller."""

    # name is what appears in the drop-down menu for choosing the experiment
    # type in the parameter editor.
    # description is currently unused.
    name = "Test game controller"
    description = "A game controller just for testing."

    # customParams is a static variable, a dictionary that just gives the names,
    # default values, and descriptions of this controller's game-specific
    # parameters.  The dictionary is indexed by parameter name, and each element
    # is a tuple containing the default value and the description, which appears
    # as a tooltip when the mouse hovers over the name in the parameter editor.
    customParams = {}
    customParams['numGroups'] = 1, "Number of groups"

    def __init__(self, server, params, communicator, clients, outputDir):
        GameControl.GameControl.__init__(self, server, params, communicator,
                clients, outputDir)

        for client in self.clients:
            self.initParams[client.id]['greeting'] = \
                    "Hello, client " + ' ' + str(client.id)

        self.server.enableChat()

    def initMatch(self):
        if self.matchNum == 0:
            self.histHeaders = ['xOne', 'xTwo']
        elif self.matchNum == 1:
            self.histHeaders = ['xOne', 'xTwo', 'xThree']
        elif self.matchNum == 2:
            self.histHeaders = ['xOne', 'xThree']
        elif self.matchNum == 3:
            self.histHeaders = ['xThree', 'xOne']
        elif self.matchNum == 4:
            self.histHeaders = ['xOne', 'xThree', 'xTwo']
        elif self.matchNum == 5:
            self.histHeaders = ['xTwo', 'xThree']

        numGroups = int(self.currentMatch['customParams']['numGroups'])
        groupSize = int(math.ceil(float(len(self.clients)) / float(numGroups)))
        self.groups = GroupData.makeGroups(numGroups)
        pos = 0
        for group in self.groups:
            group.assignClients(self.clients[pos:(pos+groupSize)])
            pos += groupSize
        for group in self.groups:
            print 'clients in group %d' % group.id
            for client in group.clients:
                print ' %d' % client.id

    def runRound(self):
        messages = []
        for i in range(len(self.clients)):
            mes = {'type': 'gm', 'question': 'How much money do you want?'}
            messages.append(mes)

        replies = self.askAllPlayers(messages)

        # Add payoffs and history rows
        for i, reply in enumerate(replies):
            self.clients[i].payoffs[self.matchNum] += reply['amount']
            #strAmount = '%0.2f' % reply['amount']
            a = reply['amount']
            if self.matchNum == 0:
                self.histValues[i] = [a, a*2]
            elif self.matchNum == 1:
                self.histValues[i] = [a, a*2, a*3]
            elif self.matchNum == 2:
                self.histValues[i] = [a, a*3]
            elif self.matchNum == 3:
                self.histValues[i] = [a*3, a]
            elif self.matchNum == 4:
                self.histValues[i] = [a, a*3, a*2]
            elif self.matchNum == 5:
                self.histValues[i] = [a*2, a*3]
