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

import copy

class ClientHistory:
    """
    ClientHistory holds history data for one client.  Member variables
    headers, stacks, and values should be read directly, but not modified
    directly.
    """

    def __init__(self):

        self.headers = []
        """ a list of lists:  each element of the outer list is the list of
        column names for that match headers[match][colnum] is a column header
        (string) """

        self.practice = []
        
        self.groupID = []

        self.stacks = []
        """ FIXME: OUT OF DATE a list mapping column indexes (of the headers and values as they are
        arranged here) to the visual column positions in the ClientHistoryBook.
        This can be ignored; by default, they will be the same.  But the main
        reason for this is when you want to "stack" history variables in the
        GUI, placing multiple variables in the same column.  Each stack is
        described by a list whose first element is the string to place in the
        header of the column (the header strings for the individual variables
        will be ignored), and whose subsequent elements are the column indices
        of the variables to stack.  For example, this situation:

        headers = ['Endowment', 'Investment A', 'Investment B', 'Profit']
        stackss = [0, ['Investment', 1, 2], 3]
        values = [20, 10, 5, 18]

        would result in the following in the client GUI:

        Endowment  Investment  Profit
           20         10         18
                       5

        and the following in the output file:
        Endowment, Investment A, Investment B, Profit
        20, 10, 5, 18 """

        self.values = []
        """ A list of lists of lists:
        values[match][round][colnum] is a data value (anything)
       
        [ <this contains all matches>
          [ <this is match 0>
            [ <this is match 0, round 0> value1, value2, value3, ...]
            [ <this is match 0, round 1> value1, value2, value3, ...]
            ...
          ]
          [ <this is match 1>
            [ <this is match 1, round 0> value1, value2, ...]
            [ <this is match 1, round 1> value1, value2, ...]
            ...
          ]
          ...
        ] """

        self.roundOutput = []
        """ A list of lists of dictionaries:
        roundOutput[match][round][columnName]
        of round-specific data to be
        included in the history output file but not displayed in the
        ClientHistoryBook.  Dictionaries are indexed by column name.
        """

    def startMatch(self, headers, practice, groupID=None, stacks=None):
        """  List of headers passed in is copied so if it is changed later, the
        internal copy is unaffected."""
        self.headers.append(copy.copy(headers))
        self.practice.append(practice)
        self.groupID.append(groupID)
        self.stacks.append(copy.copy(stacks))
        self.values.append([])
        self.roundOutput.append([])

    def addRound(self, values):
        """ The history data is for display and output purposes, so numeric
        values that need formatting should be formatted as desired (into
        strings) before inserting.  Otherwise, they will just be made into
        strings using str().  List of values is copied so if it is changed
        later, the internal copy is unaffected.  """
        self.values[-1].append(copy.copy(values))

        # Start the roundOutput dictionary for this round as an empty
        # dictionary, into which data may be merged later with addRoundOutput()
        self.roundOutput[-1].append({})

    def addRoundOutput(self, outputDict):
        """ Take a dictionary of output column/value pairs and add them to the
        output file for this round.  Call this following addRound().  May be
        called any number of times after addRound; will continue to update the
        output data for the current round.
        """
        self.roundOutput[-1][-1].update(outputDict)
