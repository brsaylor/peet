# Copyright 2009 University of Alaska Anchorage Experimental Economics
# Laboratory, Paul Johnson
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
import csv
import copy
import os
import time

from server import servernet
import GameControl
from server import GroupData
from shared import util

class IslandControl(GameControl.GameControl):

    name = "The Island Experiment (Paul Johnson)"
    description = ""

    customParams = {}
    customParams['enableChat'] = 0, "Enable chat"\
                + " (0 = no chat, 1 = chat only with same color, 2 = open chat"
    customParams['numGroups'] = 1, "Number of groups\n(NOTE: This is an "\
            "experiment-level parameter taken from the first match only. "\
            "The value from the first match applies to the whole game.)"
    customParams['auctionTime'] = 30, "Number of seconds for each auction"
    customParams['prodChoiceTimeLimit'] = 15,\
            "Time limit in seconds for the production choice"
    customParams['pf_blue_x'] = '0 1 3 6 10 15',\
            "Blue production function (green values)"
    customParams['pf_blue_y'] = '15 10 6 3 1 0',\
            "Blue production function (blue values)"
    customParams['pf_shock_blue_x'] = '0 1 3 6 10',\
            "Shocked Blue production function (green values)"
    customParams['pf_shock_blue_y'] = '10 6 3 1 0',\
            "Shocked Blue production function (blue values)"
    customParams['pf_red_x'] = '0 1 2 3 4 5',\
            "Red production function (green values)"
    customParams['pf_red_y'] = '5 4 3 2 1 0',\
            "Red production function (red values)"
    customParams['pf_shock_red_x'] = '0 1 2 3 4',\
            "Shocked Red production function (green values)"
    customParams['pf_shock_red_y'] = '4 3 2 1 0',\
            "Shocked Red production function (red values)"
    customParams['pf_shockRounds_blue'] = '', 'Rounds for blue production shock'
    customParams['pf_shockRounds_red'] = '', 'Rounds for red production shock'
    customParams['startingDollars'] = 10, "Dollars given at match start"
    customParams['resetBalances'] = 1, 'Reset chip balances each round'

    # dictionary of safe things to be passed as eval()'s "locals" argument when
    # evaluating the scoring_formula, so the expression can call no other
    # functions and access no other variables.  The d,b,r, and g will be added
    # later.
    safe_for_eval = {
            'abs': abs,
            'float': float,
            'int': int,
            'max': max,
            'min': min,
            'pow': pow,
            'round': round
            }
    tip = "Python expression that evaluates "
    tip += "to the player's current round score.\n"
    tip += "It will automatically be rounded to the nearest integer value.\n"
    tip += "Available variables: d (dollars), b (blue), r (red), g (green)\n"
    tip += "Available functions: "
    safelist = safe_for_eval.keys()
    safelist.sort()
    tip += ', '.join(safelist)
    customParams['scoring_formula'] = 'd + 10 * (min(b, r, g))', tip

    customParams['moneyShocks_blueMkt'] = '','Aggregate quantities for money'\
            + ' shocks that will occur before the blue auction'
    customParams['moneyShocks_blueMkt_rounds'] = '', 'The corresponding rounds'
    customParams['moneyShocks_blueMkt_who'] = '', 'The corresponding targets'\
            + ' (1 for blue teams only, 2 for red, 3 for both)'
    customParams['moneyShocks_redMkt'] = '','Aggregate quantities for money'\
            + ' shocks that will occur before the red auction'
    customParams['moneyShocks_redMkt_rounds'] = '', 'The corresponding rounds'
    customParams['moneyShocks_redMkt_who'] = '', 'The corresponding targets'\
            + ' (1 for blue teams only, 2 for red, 3 for both)'

    customParams['allowNegativeDollars'] = 0,\
            'Set to 1 to allow dollar balances to go negative.\n'\
            + 'Set to 0 to prevent dollar balances from going negative.'

    def __init__(self, server, params, communicator, clients, outputDir):
        GameControl.GameControl.__init__(self, server, params, communicator,
                clients, outputDir)
        
        # Get experiment-level parameters, hackishly expected as the values from
        # the first match
        self.numGroups = int(params['matches'][0]['customParams']['numGroups'])

        # Group clients (once per game)
        self.groups = GroupData.groupClients_random(
                self.clients, numGroups=self.numGroups)

        # Assign industries (alternate blue and red)
        # g.blueIDs is a list of blue client IDs we send to the clients,
        # because they need to know who's which color so the chat messages can
        # be marked with that color.
        for g in self.groups:
            g.blueIDs = []
            for i in range(len(g.clients)):
                if i % 2 == 0:
                    g.clients[i].color = 'blue'
                    g.blueIDs.append(g.clients[i].id)
                else:
                    g.clients[i].color = 'red'

        # initialize clients
        for c in self.clients:
            #
            #
            c.acct = {}  # Account data
            #
            # c.events[match][round] is a dictionary of non-market events for
            # that match and round:
                # productionChoice_blue
                # productionChoice_red
                # productionChoice_green
                # prodShock
                # moneyShock_blueMkt
                # moneyShockAmount_blueMkt
                # moneyShockAmountRealized_blueMkt
                # moneyShock_redMkt
                # moneyShockAmountRealized_redMkt
            c.events = []

        # Keep market history and other event history separate.  That way
        # mktHist is easier to analyze, and it can be sent without filtering to
        # any client that needs it upon re-connect.
        #
        # group.mktHist[match][round]{market} is a list of market events
        for g in self.groups:
            g.mktHist = []

        ## Output files
        # Market history
        self.mktHistFilename = os.path.join(self.outputDir,
                server.sessionID + '-market-history.csv')
        file = open(self.mktHistFilename, 'wb')
        csvwriter = csv.writer(file)
        self.mktHistHeaders = ['Match', 'Round', 'Group', 'Market', 'Action',
                'Buyer', 'Bid', 'Accept', 'Ask', 'Seller', 'Time']
        csvwriter.writerow(self.mktHistHeaders)
        file.close()

        # market events are given timestamps along a timeline that starts with
        # the first auction and "pauses" in between auctions.  baseTime is the
        # number of seconds of auction time so far, incremented at the end of
        # every auction.
        self.baseTime = 0.0

    def initMatch(self):

        # Get match parameters
        cp = self.currentMatch['customParams']
        self.chat = int(cp['enableChat'])
        self.auctionTime = int(cp['auctionTime'])
        self.prodChoiceTimeLimit = int(cp['prodChoiceTimeLimit'])
        # Get production functions
        # x = green, y = industry color 
        self.pf = {}
        self.pf_shock = {}
        self.pf_shockRounds = {}
        for color in ('blue', 'red'):

            X = map(int, cp['pf_' + color + '_x'].split())
            Y = map(int, cp['pf_' + color + '_y'].split())
            self.pf[color] = []
            for i in range(min(len(X), len(Y))):
                self.pf[color].append((X[i], Y[i]))

            X = map(int, cp['pf_shock_' + color + '_x'].split())
            Y = map(int, cp['pf_shock_' + color + '_y'].split())
            self.pf_shock[color] = []
            for i in range(min(len(X), len(Y))):
                self.pf_shock[color].append((X[i], Y[i]))

            self.pf_shockRounds[color] = map(lambda x: int(x) - 1,
                    cp['pf_shockRounds_' + color].split())

        self.resetBalances = bool(int(cp['resetBalances']))
        self.startingDollars =\
                Decimal(cp['startingDollars']).quantize(Decimal('0.01'))
        self.scoring_formula = cp['scoring_formula']

        # dictionaries indexed by color of market
        self.moneyShocks = {}
        self.moneyShocks_rounds = {}
        # moneyShocks_who[marketColor][i][playerColor] = <True or False>
        self.moneyShocks_who = {}
        for color in ('blue', 'red'):
            self.moneyShocks[color] = map(
                    lambda x: Decimal(x).quantize(Decimal('0.01')),
                    cp['moneyShocks_'+color+'Mkt'].split())
            self.moneyShocks_rounds[color] = map(lambda x: int(x) - 1,
                    cp['moneyShocks_'+color+'Mkt_rounds'].split())
            whoList = map(int, cp['moneyShocks_'+color+'Mkt_who'].split())
            self.moneyShocks_who[color] = []
            for who in whoList:
                if who == 1:
                    whoDict = {'blue': True, 'red': False}
                elif who == 2:
                    whoDict = {'blue': False, 'red': True}
                else:
                    whoDict = {'blue': True, 'red': True}
                self.moneyShocks_who[color].append(whoDict)

        #print 'moneyShocks =', self.moneyShocks
        #print 'moneyShocks_rounds =', self.moneyShocks_rounds
        #print 'moneyShocks_who =', self.moneyShocks_who

        self.allowNegativeDollars = bool(int(cp['allowNegativeDollars']))

        if self.chat == 1:
            # Chat among players of the same color
            filter = lambda c1, c2: c1.color == c2.color
        else:
            filter = None
        self.server.enableChat(self.chat > 0, filter)

        # initialize clients
        for c in self.clients:
            c.acct['dollars'] = self.startingDollars
            c.acct['blue'] = 0
            c.acct['red'] = 0
            c.acct['green'] = 0
            self.updateRoundScore(c)
            c.acct['matchScore'] = 0

            c.events.append([]) # append new empty match to event history

            c.matchInitMessage = {'type': 'gm',
                'subtype': 'initmatch', 'color': c.color, 'chat': self.chat,
                'blueIDs': c.group.blueIDs}
            self.communicator.send(c.connection, c.matchInitMessage)

        for g in self.groups:
            g.mktHist.append([]) # append new empty match to market history

    def runRound(self):

        # for reconnecting clients
        self.productionChoicesMade = []
        self.auctionInProgress = False

        # Append new empty round to current match of market history
        for g in self.groups:
            g.mktHist[-1].append({'blue': [], 'red': []})

        if self.resetBalances:
            for c in self.clients:
                c.acct['blue'] = 0
                c.acct['red'] = 0
                c.acct['green'] = 0
                self.updateRoundScore(c)

        for c in self.clients:
            c.events[self.matchNum].append({})
            # c.events[self.matchNum][self.roundNum] is now an empty dict
            self.sendAccountUpdate(c)

        # Sequence of things in each round:
        # - Potential blue production shock
        # - Blue production choice
        # - Potential money shock
        # - Blue auction
        # - Potential Red production shock
        # - Red production choice
        # - Potential Money shock
        # - Red auction
        for color in ('blue', 'red'):
            self.color = color
            self.doProductionChoice(color) # includes potential shocks
            self.productionChoicesMade.append(color)
            self.auctionInProgress = True
            self.doAuction(color)
            self.auctionInProgress = False

        # Update match score
        for c in self.clients:
            if self.resetBalances:
                c.acct['matchScore'] += c.acct['roundScore']
            else:
                c.acct['matchScore'] = c.acct['roundScore']
            self.sendAccountUpdate(c)

        # Add payoffs
        for i, c in enumerate(self.clients):
            c.payoffs[self.matchNum] = c.acct['matchScore']

        # Append round data to output files
        #
        # Market history to its own file
        file = open(self.mktHistFilename, 'ab')
        csvwriter = csv.DictWriter(file, self.mktHistHeaders)
        for g in self.groups:
            for color in ('blue', 'red'):
                for event in g.mktHist[self.matchNum][self.roundNum][color]:
                    row = copy.copy(event)
                    row['Match'] = self.matchNum + 1
                    row['Round'] = self.roundNum + 1
                    row['Group'] = g.id
                    row['Market'] = color
                    csvwriter.writerow(row)
        file.close()
        #
        # Account and events to main output file
        for c in self.clients:
            self.roundOutput[c.id] = {'color': c.color}
            self.roundOutput[c.id].update(c.acct)
            self.roundOutput[c.id].update(
                    c.events[self.matchNum][self.roundNum])


    def doProductionChoice(self, color):
        # Send the message out to everyone;
        # the <color> clients will send back their production choices and the
        # other clients will send back empty replies.

        # determine production shock
        if self.roundNum in self.pf_shockRounds[color]:
            prodShock = True
            pf = self.pf_shock[color]
        else:
            prodShock = False
            pf = self.pf[color]

        # determine money shock
        for g in self.groups:
            g.moneyShockTargets = []
        if self.roundNum in self.moneyShocks_rounds[color]:
            # There is a money shock before the <color> auction in this round.
            # Get the position into the arrays so we can get the corresponding
            # quantities and targets.
            i = self.moneyShocks_rounds[color].index(self.roundNum)
            Q = self.moneyShocks[color][i]
            # "who" is {'blue': <bool>, 'red': <bool>}
            who = self.moneyShocks_who[color][i]

            # Each group has a potentially different number of targets N, and
            # needs independent calculation of individual shock quantities.
            for g in self.groups:
                # Identify and count the recipients of the money shock
                g.N = 0
                for c in g.clients:
                    if who[c.color]:
                        g.N += 1
                        g.moneyShockTargets.append(c.id)
                        c.events[self.matchNum][self.roundNum]\
                                ['moneyShock_'+color+'Mkt'] = 1

                # determine the shock quantities for this group
                # We are using Decimals to 2 decimal places, but randomdivide()
                # uses ints, so multiply by 100 and divide again.
                # It also needs positive ints, so abs(Q) and make negative again
                # if Q is negative.
                g.shocks = util.randomdivide(abs(int(Q * 100)), g.N)
                g.shocks = map(lambda x: Decimal(x) / 100, g.shocks)
                if Q < 0: # make negative if Q is negative
                    g.shocks = map(lambda x: -x, g.shocks)

        messages = []
        for c in self.clients:
            m = {'type': 'gm', 'subtype': 'production', 'color': color,
                    'timeLimit': self.prodChoiceTimeLimit}
            g = c.group
            if c.color == color:
                m['prodShock'] = prodShock
                c.events[self.matchNum][self.roundNum]\
                        ['prodShock'] = 1 if prodShock else 0
                m['pf'] = pf
            if c.id in g.moneyShockTargets:
                m['moneyShock'] = True
                amount = g.shocks[g.moneyShockTargets.index(c.id)]
                c.events[self.matchNum][self.roundNum]\
                        ['moneyShockAmt_'+color+'Mkt'] = amount
                # Apply the money shock here, since it's convenient
                c.acct['dollars'] += amount
                if not self.allowNegativeDollars and c.acct['dollars'] < 0:
                    amountRealized = c.acct['dollars']
                    c.acct['dollars'] = Decimal('0.00')
                else:
                    amountRealized = amount
                m['moneyShockAmount'] = amountRealized
                c.events[self.matchNum][self.roundNum]\
                        ['moneyShockAmountRealized_'+color+'Mkt']\
                        = amountRealized
            else:
                m['moneyShock'] = False
            messages.append(m)
        replies = self.askAllPlayers(messages,
                'Waiting for ' + color + ' production choice',
                'Ready')
        
        for id, r in enumerate(replies):
            c = self.clients[id]

            # Create message to send back to clients to confirm production
            # choice
            m = {'type': 'gm', 'subtype': 'productionChoice', 'color': color}
            if c.color == color:

                # Get production choice i (an index into the production function
                # pf) and clip it to the valid range
                i = r.get('choice', 0)
                if i < 0: i = 0
                if i > len(pf) - 1: i = len(pf) - 1
                
                # Update the client's account
                c.acct['green'] += pf[i][0]
                c.acct[color] += pf[i][1]
                self.updateRoundScore(c)

                # Update client's event history
                c.events[self.matchNum][self.roundNum]\
                        ['productionChoice_green'] = pf[i][0]
                c.events[self.matchNum][self.roundNum]\
                        ['productionChoice_' + color] = pf[i][1]

                m['green'] = pf[i][0]
                m[color] = pf[i][1]

            self.sendAccountUpdate(c)

            # Send back the confirmation message whether or not the client
            # produced
            self.communicator.send(c.connection, m)

    def doAuction(self, color):

        # Initialize the market state
        for g in self.groups:
            self.resetMarket(g)

        self.tellAllPlayers({'type': 'gm', 'subtype': 'auction',
            'color': color, 'auctionTime': self.auctionTime})
        self.communicator.startTimer(self.auctionTime)

        while True:
            # Receive and process a message

            conn, m = self.communicator.recv()
            t = m.get('subtype')

            # Calculate the timestamp to give this market event (to help with
            # analysis of output data), as the starting timestamp of this
            # auction plus the amount of time into the auction.
            # To account for the fact that a pause cancels the communicator's
            # timer, we get time elapsed by subtracting the time LEFT from the
            # auctionTime.
            timeElapsed = self.auctionTime - self.communicator.getTimeLeft()
            print 'baseTime =', self.baseTime, 'timeElapsed =', timeElapsed
            msgTime = self.baseTime + timeElapsed

            if t == 'timeup':
                # Auction is over
                self.baseTime += self.auctionTime
                self.tellAllPlayers(m)
                self.server.postMessage('Auction over')
                return

            c = self.clients[conn.id]
            g = c.group

            # Message should be a bid or ask.  Check for valid amount, ignoring
            # message if not valid
            if not (type(m.get('amount')) == Decimal and m['amount'] > 0):
                print 1
                continue

            # Convert amount so that it's a multiple of .10, with the zero
            amount = m['amount'].quantize(Decimal('.1')) * Decimal('1.0')

            if t == 'bid':

                # Check for valid bid, sending error message or ignoring
                # entirely, depending...
                if c.color == color:
                    # c is a seller, doesn't make sense to bid
                    print 2
                    continue
                if amount <= g.highBid:
                    self.communicator.send(c.connection, {'type': 'gm',
                        'subtype': 'error', 'error': 'bidTooLow'})
                    print 3
                    continue
                if amount > c.acct['dollars']:
                    self.communicator.send(c.connection, {'type': 'gm',
                        'subtype': 'error', 'error': 'notEnoughDollars'})
                    print 4
                    continue

                # Valid bid - tell everyone in group
                g.highBidder = c
                g.highBid = amount
                for c2 in g.clients:
                    self.communicator.send(c2.connection, {'type': 'gm',
                        'subtype': 'bid', 'id': c.id, 'amount': amount})
                # and append to market history
                g.mktHist[-1][-1][color].append({'Action': 'bid',
                    'Buyer': c.id, 'Bid': amount, 'Time': msgTime })

            elif t == 'ask':
                if c.color != color:
                    # c is a buyer, doesn't make sense to ask
                    print 5
                    continue
                if amount >= g.lowAsk:
                    self.communicator.send(c.connection, {'type': 'gm',
                        'subtype': 'error', 'error': 'askTooHigh'})
                    print 6
                    continue
                if c.acct[color] < 1:
                    self.communicator.send(c.connection, {'type': 'gm',
                        'subtype': 'error', 'error': 'notEnoughChips'})
                    print 7
                    continue

                # Valid ask - tell everyone in group
                g.lowSeller = c
                g.lowAsk = amount
                for c2 in g.clients:
                    self.communicator.send(c2.connection, {'type': 'gm',
                        'subtype': 'ask', 'id': c.id, 'amount': amount})
                # and append to market history
                g.mktHist[-1][-1][color].append({'Action': 'ask',
                    'Ask': amount, 'Seller': c.id, 'Time': msgTime})

            else:
                # Invalid message (not a bid or ask) - ignore it
                print 8
                continue

            # If the high bid and low sell have met or crossed, make the
            # transaction, tell everyone in the group, and reset the market for
            # the group.
            if g.highBid >= g.lowAsk:
                g.highBidder.acct[color] += 1
                g.highBidder.acct['dollars'] -= amount
                g.lowSeller.acct[color] -= 1
                g.lowSeller.acct['dollars'] += amount
                self.updateRoundScore(g.highBidder)
                self.updateRoundScore(g.lowSeller)
                for c2 in g.clients:
                    self.communicator.send(c2.connection, {'type': 'gm',
                        'subtype': 'transaction', 'buyerID': g.highBidder.id,
                        'sellerID': g.lowSeller.id, 'amount': amount})
                self.sendAccountUpdate(g.highBidder)
                self.sendAccountUpdate(g.lowSeller)
                # and append to market history
                g.mktHist[-1][-1][color].append({'Action': 'accept',
                    'Buyer': g.highBidder.id, 'Accept': amount,
                    'Seller': g.lowSeller.id, 'Time': msgTime})
                self.resetMarket(g)

    def resetMarket(self, group):
        group.highBidder = None
        group.highBid = Decimal('-Infinity')
        group.lowSeller = None
        group.lowAsk = Decimal('Infinity')

    def updateRoundScore(self, client):
        a = client.acct
        # Here is a useful page:
        # http://lybniz2.sourceforge.net/safeeval.html
        safe_for_eval = {
                'd': float(a['dollars']),
                'b': a['blue'],
                'r': a['red'],
                'g': a['green'],
                }
        safe_for_eval.update(IslandControl.safe_for_eval)
        a['roundScore'] = int(round(eval(self.scoring_formula,
                {"__builtins__": None}, safe_for_eval)))

    def sendAccountUpdate(self, client):
        print 'sendAccountUpdate to ', client.id
        self.communicator.send(client.connection,
                {'type': 'gm', 'subtype': 'acctUpdate', 'acct': client.acct})

    def getReinitParams(self, client):
        m = self.initParams[client.id]
        m['type'] = 'reinit'
        m['history'] = client.history
        m['match'] = self.matchNum
        m['round'] = self.roundNum
        m['matchInitMessage'] = client.matchInitMessage
        m['acct'] = client.acct
        m['events'] = client.events
        m['mktHist'] = client.group.mktHist
        m['productionChoicesMade'] = self.productionChoicesMade
        m['auctionInProgress'] = self.auctionInProgress

        # Set by askAllPlayers when the message was sent, and back to None when
        # reply is received.
        m['unansweredMessage'] = client.unansweredMessage

        return m
    
    def onUnpause(self):
        if self.auctionInProgress:
            timeLeft = int(round(self.communicator.timeLeftAtCancel))
            self.tellAllPlayers({'type': 'gm', 'subtype': 'auction',
                'color': self.color, 'auctionTime': timeLeft})
            self.communicator.startTimer(timeLeft)

