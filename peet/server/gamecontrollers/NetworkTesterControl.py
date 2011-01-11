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

import random
import string
import sys

from peet.server import servernet
import GameControl


class NetworkTesterControl(GameControl.GameControl):
    #"""
    #The basic idea is: generate random messages, send them to the clients,
    #have the clients echo them back, and check the reply is equal to the
    #original message (repeated rapidly).
    #"""

    name = "Network tester"
    description = "Tests the network system for reliability under load."

    customParams = {}

    def __init__(self, server, params, communicator, clients, outputDir):
        GameControl.GameControl.__init__(self, server, params, communicator,
                clients, outputDir)

        self.chars = string.letters + string.digits
        self.sentMessages = [None] * len(self.clients)
        self.maxrdepth = 4
        self.rdepth = 0

        self.mesID = 0

    def runRound(self):

        # send initial batch of messages
        for client in self.clients:
            m = self.makeRandomMessage()
            self.communicator.send(client.connection, m)
            self.sentMessages[client.id] = m

        # Runs forever (will never advance to next round)
        while True:

            conn, mes = self.communicator.recv()

            # Compare message sent to message echoed back
            if mes != self.sentMessages[conn.id]:
                self.server.postMessage('Error: client ' + str(conn.id) + ': '\
                        'expected\n' + str(self.sentMessages[conn.id])\
                        + '\nbut received\n' + str(mes))
                self.server.postMessage(\
                        '(expected mesID=%d, received mesID=%s)'\
                        % (self.sentMessages[conn.id]['mesID'],\
                        str(mes.get('mesID', 'NONE'))))

                #self.postMessage('Pausing.')
                #self.server.onPauseClicked(None)


            # send a new message
            mes = self.makeRandomMessage()
            self.communicator.send(conn, mes)
            self.sentMessages[conn.id] = mes

        # clear the sent messages list
        self.sentMessages = [None] * len(self.clients)
    
    def makeRandomMessage(self):
        m = {'type': 'gm'}
        m['mesID'] = self.mesID
        self.mesID += 1

        # message with be dictionary with random number of elements len
        len = random.randint(10, 20)
        
        # for each element:
        for i in range(len-1):

            # generate a random string for the key between 3 and 20 chars
            key = ''
            for j in range(random.randint(3, 20)):
                key += random.choice(self.chars)

            # generate a random value of a random type
            value = self.makeRandomValue()
            m[key] = value

        #print 'makeRandomMessage: ', m
        
        return m
    
    # generate a value of a random type and random value
    # 1=int, 2=float, 3=bool, 4=string, 5=list
    # If list or tuple, will be called recursively up to maxrdepth
    def makeRandomValue(self):
        if self.rdepth >= self.maxrdepth:
            return None

        self.rdepth += 1

        t = random.randint(1,5)
        if t == 1: # int
            value = random.randint(-sys.maxint-1, sys.maxint)
        elif t == 2: # float
            # Python doesn't provide info on max/min float values, so just
            # use -1000...1000
            value = random.uniform(-1000, 1000)
        elif t == 3: # bool
            value = (random.random() < 0.5)
        elif t == 4: # string
            value = ''
            for j in range(random.randint(3, 20)):
                value += random.choice(self.chars)
        elif t == 5: # list
            value = []
            for j in range(random.randint(2, 10)):
                value.append(self.makeRandomValue())

        self.rdepth -= 1

        return value

    def getReinitParams(self, client):
        params = GameControl.GameControl.getReinitParams(self, client)
        params['message'] = self.sentMessages[client.id]
        return params
