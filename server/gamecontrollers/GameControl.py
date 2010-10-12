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

import thread
import time
import Queue
import re
import sys
import traceback

from server import servernet
from server.ClientData import ClientData
from server.HistoryWriter import HistoryWriter
from shared.constants import roundingOptions

class GameControl:

    """Base class for all game controllers."""

    name = "Game controller base class"
    description = "Base class for all game controllers; not useful on its own."

    customParams = {}
    """A dictionary: 'paramName': defaultValue, 'paramDescription'."""
    # add type info to make editing nicer?

    def __init__(self, server, params, communicator, clients, outputDir):
        """ Derived class's __init__ must send initialization messages to
        clients, including GUIclass name, client id, and client name """
        self.server = server
        self.params = params
        self.communicator = communicator
        self.clients = clients
        self.outputDir = outputDir
        self.matchNum = 0
        self.roundNum = 0
        self.waitQ = Queue.Queue()  # for waiting after each round
        self.readyQ = Queue.Queue()  # for client ready messages
        self.running = False

        # Create initParams, a list of dictionaries containing initialization
        # parameters to be sent to the client.  The derived class may add
        # information to these dictionaries in its __init__ method.  Some
        # parameters that may be set that are automatically recognized by the
        # client are:
        #   showMatch (default:True) - Show match column in ClientHistoryBook
        # initParams will be sent by GameControl.start().
        #
        self.initParams = []
        GUIclassName = re.sub('Control$', 'GUI', self.__class__.__name__)
        for client in clients:
            self.initParams.append(dict(type='init', GUIclass=GUIclassName,
                id=client.id, name=client.name))

        # Create the client history output file writer
        clientHistories = []
        for client in self.clients:
            clientHistories.append(client.history)
        self.histWriter = HistoryWriter(server.sessionID,\
            params.get('experimentID', ''), clientHistories, self.outputDir,\
            self.params)
        self.histStacks = None # see ClientHistory.py (stacks attribute)

    def askAllPlayers(self, messages,\
            sentStatus='Waiting for client reply',
            rcvdStatus='Ready'):
        """ Send a message to each client, wait for responses, and return them
        as a list.  The list will be in order of client id.  This method sets
        the following attributes of each ClientData object of self.clients:
        replyReceived - set to False before sending, True after receiving reply
        unansweredMessage - set to the message to send before sending, None
        after receiving reply
        @param messages: List of messages to send, one for each client,\
        or a single message to send to all clients.
        @param sentStatus: Status string to display in client status list when\
                message has been sent.
        @param sentStatus: Status string to display in client status list when\
                reply has been received.
        """
        replies = []
        for client in self.clients:
            client.status = sentStatus
            client.replyReceived = False
            self.server.updateClientStatus(client)
        if isinstance(messages, list):
            for i, client in enumerate(self.clients):
                client.unansweredMessage = messages[i]
                self.communicator.send(client.connection, messages[i])
                replies.append(None)
        else:
            # Here, 'messages' is actually just one message
            for client in self.clients:
                client.unansweredMessage = messages
                self.communicator.send(client.connection, messages)
                replies.append(None)

        repliesReceived = 0
        while repliesReceived < len(self.clients):
            conn, mes = self.communicator.recv()
            if replies[conn.id] == None:
                # discard messages from clients who've already replied
                repliesReceived += 1
                replies[conn.id] = mes
                self.clients[conn.id].status = rcvdStatus
                self.clients[conn.id].replyReceived = True
                self.clients[conn.id].unansweredMessage = None
                self.server.updateClientStatus(self.clients[conn.id])

        return replies

    def tellAllPlayers(self, messages):
        """ Just like askAllPlayers, but don't wait for replies.  Also, it is
        possible to pass just one message to send to all clients. """
        if isinstance(messages, list):
            for i, client in enumerate(self.clients):
                self.communicator.send(client.connection, messages[i])
        else:
            # Here, 'messages' is actually just one message
            for client in self.clients:
                self.communicator.send(client.connection, messages)

    def clientReady(self, clientConn):
        """ Called by the server when client sends a 'ready' message """
        self.readyQ.put(clientConn)

    # It may be necessary to wait for a particular client to be ready.  Maybe
    # this will do the trick:
    def waitForClientReady(self, clientConn):
        otherClientsReady = []
        # wait for a ready message from any client.
        conn = self.readyQ.get()
        if conn != clientConn:
            # if it's not the one we're waiting for, save it for later and keep
            # waiting.
            otherClientsReady.append(conn)
        else:
            # It's the one we were waiting for; put the other ready messages
            # back on the queue and return.
            for c in otherClientsReady:
                self.readyQ.put(c)
            return

    def start(self):
        thread.start_new_thread(self.run_with_traceback, ())

    def run_with_traceback(self):
        # According to Python docs for start_new_thread, "When the function
        # terminates with an unhandled exception, a stack trace is printed and
        # then the thread exits (but other threads continue to run)."
        # However, this doesn't happen; I just get an unhandled exception
        # message.  This fixes it.
        try:
            self.run()
        except:
            traceback.print_exc(file=sys.stdout)

    def run(self):

        # Send initialization parameters to clients.
        for i, client in enumerate(self.clients):
            self.communicator.send(client.connection, self.initParams[i])

        # Wait for all clients to say they are ready.  (Important;
        # otherwise, client GUIs may not have been created.  Client GUIs are
        # created when clients receive the initParams)
        clientsReady = 0
        while clientsReady < len(self.clients):
            conn = self.readyQ.get()
            # FIXME: assuming that no client sends a 'ready' message more than
            # once
            print 'Client ' + str(conn.id) + ' is ready.'
            clientsReady += 1
        # All clients should be ready now.

        self.running = True

        for m, match in enumerate(self.params['matches']):
            self.matchNum = m
            self.currentMatch = match
            self.histHeaders = []
            self.initMatch()
            for client in self.clients:
                self.communicator.send(client.connection,\
                        dict(type='histStartMatch',\
                        headers=self.histHeaders,\
                        practice=self.currentMatch['practice'],\
                        groupID=(client.group.id if client.group else None),\
                        stacks=self.histStacks))
                client.history.startMatch(self.histHeaders,\
                        self.currentMatch['practice'],\
                        groupID=(client.group.id if client.group else None),\
                        stacks=self.histStacks)
                client.payoffs.append(0)
                # Note: the controller adds the payoffs in runRound()
            for r in range(match['numRounds']):
                self.roundNum = r
                self.server.updateMatchRound(self.matchNum, self.roundNum)
                self.tellAllPlayers({'type': 'matchAndRound', 'match':
                    self.matchNum, 'round': self.roundNum})

                self.histValues = [[]] * len(self.clients)
                self.roundOutput = [{}] * len(self.clients)

                self.runRound()

                # post-round client updates/communication
                for i, client in enumerate(self.clients):
                    mes = {'type': 'payoff',
                            'experimentCurrency': client.payoffs[self.matchNum],
                            'realCurrency': self.currentMatch['exchangeRate'] *
                            client.payoffs[self.matchNum]}
                    self.communicator.send(client.connection, mes)
                    self.clients[i].history.addRound(self.histValues[i])
                    self.clients[i].history.addRoundOutput(self.roundOutput[i])
                    mes = {'type': 'histAddRound',\
                            'values': self.histValues[i]}
                    self.communicator.send(client.connection, mes)
                self.histWriter.write()

                # Anything the derived class wants to do post-round
                self.postRound()

                # Tell the server the round is finished, and possibly the match,
                # and possibly the game.
                matchFinished = (r+1 == match['numRounds'])
                gameFinished = matchFinished and\
                    (m+1 == len(self.params['matches']))
                self.server.roundFinished(matchFinished, gameFinished)

                if not gameFinished:
                    # wait for server to give the OK to cont (i.e. call
                    # nextRound())
                    self.waitQ.get()

        self.server.postMessage('All matches finished.')

        # Send end-of-experiment message
        for client in self.clients:
            mes = {'type': 'endOfExperiment',\
                    'totalPayoff': client.getTotalPayoff(),\
                    'exchangeRates': client.exchangeRates,\
                    'showUpPayment': self.params['showUpPayment'],\
                    'rounding': self.params['rounding'],\
                    'totalDollarPayoff': client.getTotalDollarPayoff(\
                        rounding = self.params['rounding'])\
                        + self.params['showUpPayment']}
            if self.params.get('surveyFile', '') != '':
                mes['survey'] = True
            self.communicator.send(client.connection, mes)

    def initMatch(self):
        """ Called at the beginning of each match (before runRound()).  Override
        this method to perform any match initialization procedures, which may
        include preparing match parameters and sending them to the clients.  At
        the least, it must set the variable self.histHeaders, a list of strings
        for the match history headers, as well as self.histStacks (if desired -
            None by default)."""
        pass

    def runRound(self):
        """ Called at the beginning of each round to do anything that happens
        during a round.  Override this method to process each round.  This
        method set the variable self.histValues, a list of lists of client
        history values (one value list for each client).  This method is also
        expected to add client payoffs. """
        pass
    
    def postRound(self):
        """ Called after runRound() has finished and client history and payoffs
        have been updated.  For example, wait for clients to say they are ready
        for the next round."""
        pass

    def nextRound(self):
        """ Called by the server to tell the controller to advance to the next
        round. """
        self.waitQ.put(1)

    def reinitClient(self, client):
        """ Called by server to send re-initialization message to reconnected
        client, and wait for that client to be ready before continuing
        @type{client} ClientData.  Don't override this method. """
        self.communicator.send(client.connection, self.getReinitParams(client))
        print 'reinitClient(): reinit params sent.'
        # FIXME: somehow, have to wait for client to be ready before allowing
        # the game to be unpaused.  waitForClientReady() doesn't work if you
        # just call it here; it locks up the GUI (because it's called from the
        # GUI thread?)

    def getReinitParams(self, client):
        """ Override this function """

        # Send the initParams again, but change type to 'reinit', and include
        # the client's history.
        reinitParams = self.initParams[client.id]
        reinitParams['type'] = 'reinit'
        reinitParams['history'] = client.history
        reinitParams['match'] = self.matchNum
        reinitParams['round'] = self.roundNum

        return reinitParams

    def onUnpause(self):
        """ Called by the server when the game has been unpaused.  Override this
        method if you need something in particular to happen here.  If there was
        a timer running, you will need to start it again here, because it was
        cancelled when the game was paused.  The variable
        communicator.timeLeftAtCancel contains the number of seconds (floating
        point) that were left on the timer when it was cancelled.  This function
        shouldn't block for too long.  """
        pass
