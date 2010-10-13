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

from peet.shared.ClientHistory import ClientHistory
from peet.shared.util import stepround

class ClientData:
    
    def __init__(self, id, name=None, status=None, payoffs=[],
            connection=None, exchangeRates=[]):
        self.id = id
        self.name = name
        self.status = status
        self.payoffs = payoffs  # list of payoffs for each match
        self.history = ClientHistory()
        self.connection = connection
        self.exchangeRates = exchangeRates
        self.group = None
        self.replyReceived = None  # Set by GameControl.askAllPlayers()
        self.unansweredMessage = None  # Set by GameControl.askAllPlayers()

    def getTotalPayoff(self):
        return reduce(lambda x,y: x+y, self.payoffs, 0)

    def getTotalDollarPayoff(self, rounding=0):
        d = 0
        for m in range(len(self.payoffs)):
            d += self.payoffs[m] * self.exchangeRates[m]

        if rounding == 0: # to the cent
            return round(d, 2)
        elif rounding == 1: # to the quarter
            return stepround(d, 4)
        elif rounding == 2: # UP to the nearest quarter
            return stepround(d, 4, True)
        elif rounding == 3: # to the dollar
            return round(d, 0)
        else: # UP to the nearest dollar
            return stepround(d, 1, True)
