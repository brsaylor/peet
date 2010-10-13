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

import sys
import os.path
import os
import csv
import re

from peet.shared.ClientHistory import ClientHistory

class HistoryWriter:

    """
    HistoryWriter writes all ClientHistory data, as well as other match- or
    round-specific data, to a CSV file with one row per round per client.  Each
    time a new match header is encountered, a new column is created for it.

    It takes a list of ClientHistory objects, one from each client (these must
    be the same ones being updated by the GameController), the name of the
    output directory, and the game parameters (dictionary).

    It has a single public method: write().  This will synchronize the output
    file with the content of the ClientHistory objects.  This should be called
    once after each round, so that the output file is always up-to-date.
    """

    def __init__(self, sessionID, experimentID, clientHistories, outputDir,\
            params):
        self.sessionID = sessionID
        self.experimentID = experimentID
        self.chist = clientHistories
        self.filename = os.path.join(outputDir, sessionID + '-history.csv')
        self.params = params
        self.matchesWritten = 0 # Number of *complete* matches written
        self.roundsWritten = 0  # Number of rounds written *this match*
        self.rewriteNeeded = True # File needs to be re-written from scratch
        self.fileHeaders = ['sessionID', 'experimentID', 'match', 'practice',\
                'exchangeRate', 'round', 'subject', 'group']

        # Add headers for game-specific parameters, but prefix them with
        # "param_" to avoid column name collisions
        paramColumnNames = map(lambda s: 'param_'+s,\
            params['matches'][0]['customParams'].keys())
        self.fileHeaders.extend(paramColumnNames)

        # One per round.  A list mapping visible history columns to output file
        # columns (needed because they may change from match to match, and
        # order matters)
        self.columnMaps = []

        # A column map for ClientHistory.roundOutput.  The latter is made of
        # dictionaries, and the order doesn't matter, so we only need one of
        # these instead of one per match.
        # Key: output column name
        # Value: column index in output file (= index of "column name" in
        #        self.fileheaders)
        self.columnMap_roundOutput = {}

    def write(self):

        """
        Each match has an associated column map.  Actually, each headerlist in
        the ClientHistory.headers[] has an associated column map.  If
        len(ch.headers) > len(columnMaps), then it is time to create a new
        column map and rewrite the history file from the start.  Once we have
        done that, we don't have to worry about checking for the start of a new
        match in the m and r loops below.  To make those loops rewrite the whole
        file, simply set matchesWritten and roundsWritten to 0.  No
        header-writing will occur in those loops.
        """

        print 'HistoryWriter.write()'
        
        # Look for new headers in ClientHistory.
        # We'll check only the first ClientHistory and assume the others have
        # the same amount of data, because this is the case unless there's
        # something wrong.  FIXME
        # ClientHistory.headers is a list of lists - each inner list contains
        # the headers for a match.
        headers = self.chist[0].headers
        if len(headers) > len(self.columnMaps):
            print '  Found headers for new match'
            self.rewriteNeeded = True
            # Found headers for a new match.  Need to create a new column map
            # for each new match, then rewrite the history file.
            for m in range(len(self.columnMaps), len(headers)):
                print '  Creating columnMap for match ' + str(m)
                # m is now the index of the column map that needs to be created
                # based on headers[m].  For each element of headers[m]: Find its
                # position in self.fileHeaders.  If found, append that position
                # to columnMaps[m].  If not found, append it to the end of
                # self.fileHeaders and append that position to self.fileHeaders.
                self.columnMaps.append([])
                for header in headers[m]:
                    if header in self.fileHeaders:
                        self.columnMaps[m].append(\
                                self.fileHeaders.index(header))
                    else:
                        self.columnMaps[m].append(len(self.fileHeaders))
                        self.fileHeaders.append(header)

        # Look for new headers in the roundOutput, and if found, add them to the
        # fileheaders and columnMap_roundOutput and schedule a re-write of the
        # file.
        #   Check all unwritten rounds in all matches that have not been
        #   completely written, in all ClientHistories.
        #
        # For each match that has not been completely written:
        for m in range(self.matchesWritten, len(headers)):
            # For each ClientHistory:
            for h in range(0, len(self.chist)):
                # For each round in this match (easier and harmless to go
                # through them all):
                for r in range(0, len(self.chist[h].roundOutput[m])):
                    # For each key in the roundOutput for this round:
                    for k in self.chist[h].roundOutput[m][r]:
                        if not (k in self.fileHeaders):
                            # We've found a new column, so
                            # Schedule re-write of file
                            self.rewriteNeeded = True
                            # Add to fileheaders
                            self.fileHeaders.append(k)
                            # Add to column map
                            self.columnMap_roundOutput[k] =\
                                    self.fileHeaders.index(k)


        # If new headers were found,
        if self.rewriteNeeded:

            # Move existing history file out of the way (keep as backup)
            try:
                os.remove(self.filename + '.backup')
            except:
                print "Couldn't remove old backup history file"
            try:
                print '  Backing up history file'
                os.rename(self.filename, self.filename + '.backup')
            except:
                print "Couldn't back up history file."
                print "  (maybe just because it doesn't exist yet)"
                print sys.exc_info()[0]

            # Write headers.
            print '  Writing headers: '
            print '    ' + str(self.fileHeaders)
            file = open(self.filename, 'wb')
            csvwriter = csv.writer(file)
            # Replace whitespace with underscore
            uheaders = []
            for header in self.fileHeaders:
                uheaders.append(re.sub('\s', '_', header))
            csvwriter.writerow(uheaders)
            file.close()

            # Reset matchesWritten and roundsWritten so they all get rewritten.
            print '  Resetting matchesWritten and roundsWritten to 0'
            self.matchesWritten = 0
            self.roundsWritten = 0


        file = open(self.filename, 'ab')
        csvwriter = csv.writer(file)

        # If there is no new data to be written, the range() functions in the
        # loops below with return empty lists and the code won't get executed.
        values = self.chist[0].values
        totalMatches = len(values)
        for m in range(self.matchesWritten, totalMatches):
            print '  Writing match ' + str(m)
            if m > self.matchesWritten:
                # Just finished writing a match.
                self.matchesWritten += 1
                print '  Incremented matchesWritten to ' +\
                        str(self.matchesWritten)
                print '  Setting roundsWritten to 0'
                self.roundsWritten = 0
            totalRounds = len(values[m])
            for r in range(self.roundsWritten, totalRounds):
                print '  Writing rows for match ' + str(m) +\
                        ', round ' + str(r)
                for id in range(len(self.chist)):
                    # Make a blank row (list) of appropriate length
                    row = [''] * len(self.fileHeaders)
                    # Always start with
                    #   sessionID, experimentID, match, practice, exchangeRate,
                    # round, clientID, groupID
                    row[0] = self.sessionID
                    row[1] = self.experimentID
                    row[2] = m + 1
                    row[3] = 1 if self.chist[id].practice[m] else 0
                    row[4] = self.params['matches'][m]['exchangeRate']
                    row[5] = r + 1
                    row[6] = id
                    if self.chist[id].groupID[m] != None:
                        row[7] = self.chist[id].groupID[m]
                    else:
                        row[7] = ''

                    # Add values of custom match parameters
                    for k, v in\
                            self.params['matches'][m]['customParams'].items():
                        row[self.fileHeaders.index('param_'+k)] = v

                    # Populate the row with values for this client in this match
                    # and round, placing the values in the positions defined by
                    # the column map for this match.
                    for v, val in enumerate(self.chist[id].values[m][r]):
                        pos = self.columnMaps[m][v]
                        row[pos] = val

                    # Add values of roundOutput
                    for k,v in self.chist[id].roundOutput[m][r].iteritems():
                        pos = self.columnMap_roundOutput[k]
                        row[pos] = v

                    csvwriter.writerow(row)
                self.roundsWritten += 1  # Done writing this round
                print '  Incremented self.roundsWritten to ' +\
                        str(self.roundsWritten)

        file.close()
        self.rewriteNeeded = False
