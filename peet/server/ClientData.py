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

import decimal
#from peet.shared.util import stepround

D = decimal.Decimal

class ClientData:
    """ Holds everything the server needs to know about one client.  Also,
    GameController subclasses may assign arbitrary properties to the ClientData
    objects. """

    def __init__(self, id, name=None, status=None, earnings=D('0.00'),
            connection=None):
        """
        @type id: int
        @type name: string
        @type status: string
        @type earnings: Decimal
        @type connection: peet.server.servernet.ClientConnection
        """
        self.id = id
        self.name = name
        self.status = status
        self.earnings = earnings
        self.roundingFunction = lambda(x): x
        self.connection = connection
        self.group = None
        self.replyReceived = None  # Set by GameControl.askAllPlayers()
        self.unansweredMessage = None  # Set by GameControl.askAllPlayers()

    def setRounding(self, rounding):
        """ Given a string which is one of the keys in
        peet.shared.constants.roundingOptions, set the method to be used for
        rounding this client's earnings. """
        if rounding == 'PENNY':
            self.roundingFunction = roundPenny
        elif rounding == 'QUARTER':
            self.roundingFunction = roundQuarter
        elif rounding == 'QUARTER_UP':
            self.roundingFunction = roundQuarterUp
        elif rounding == 'DOLLAR':
            self.roundingFunction = roundDollar
        elif rounding == 'DOLLAR_UP':
            self.roundingFunction = roundDollarUp
        else:
            print "Error in ClientData.setRounding(): unknown rounding option"
            self.roundingFunction = lambda(x): x

    def getRoundedEarnings(self):
        return self.roundingFunction(self.earnings)

def roundPenny(x):
    return x.quantize(D('0.01'))

def roundQuarter(x):
    return ((x*4).quantize(D('1')) / 4).quantize(D('0.01'))

def roundQuarterUp(x):
    return ((x*4).quantize(D('1'), rounding=decimal.ROUND_UP)\
            / 4).quantize(D('0.01'))

def roundDollar(x):
    return x.quantize(D('1')).quantize(D('0.01'))

def roundDollarUp(x):
    return x.quantize(D('1'), rounding=decimal.ROUND_UP).quantize(D('0.01'))
