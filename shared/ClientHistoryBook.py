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

""" The GUI representation of ClientHistory """

import copy
import wx
import wx.grid
from wx.grid import Grid
from wx.lib.scrolledpanel import ScrolledPanel

from ClientHistory import ClientHistory

# constants
# view
TABBED=1
SINGLE=2
# sort order
ASCENDING=1
DESCENDING=2


class ClientHistoryBook(wx.Panel):
    def __init__(self, parent, history=None, view=SINGLE, sort=DESCENDING,\
            showMatch=True):
        """ @type{history} ClientHistory """
        wx.Panel.__init__(self, parent)
        sizer = wx.GridSizer(1,1)
        self.SetSizer(sizer)
        self.SetBackgroundColour('white')

        self.minheight = 200

        self.history = history
        self.view = view
        self.sort = sort
        self.showMatch = showMatch

        self.matchNum = -1
        self.roundNum = -1
        self.rowNum = -1

        # Assume SINGLE view for now
        if self.showMatch:
            self.headers = ['Match', 'Round']
        else:
            self.headers = ['Round']

        # Set up grid
        self.grid = Grid(self)
        self.grid.SetBackgroundColour('white')
        self.grid.CreateGrid(0, len(self.headers))
        for h, header in enumerate(self.headers):
            self.grid.SetColLabelValue(h, header)
        self.grid.SetRowLabelSize(0)
        self.grid.EnableEditing(False)
        self.grid.DisableDragRowSize()
        self.grid.DisableDragColSize()
        self.grid.SetDefaultCellAlignment(wx.ALIGN_CENTER, wx.ALIGN_CENTER)

        #for i in range(self.grid.GetNumberCols()):
            #self.grid.AutoSizeColLabelSize(i) # doesn't work
        self.grid.SetColLabelSize(50)

        self.grid.AutoSize()
        self.SetSize((-1, self.minheight))
        self.SetSizeHints(-1, self.minheight)
        self.grid.SetSize((-1, self.minheight))
        self.grid.SetSizeHints(-1, self.minheight)
        #self.grid.EnableScrolling(False, True)  # does nothing
        #self.grid.SetScrollLineX(1)
        #self.grid.SetScrollLineY(1)
        sizer.Add(self.grid)

        # Populate with existing history
        if history == None:
            matchCount = 0
        else:
            matchCount = len(history.headers)
        for m in range(matchCount):
            self.startMatch(history.headers[m], history.practice[m],\
                    history.groupID[m], history.stacks[m])
            for values in history.values[m]:
                self.addRound(values)

    def startMatch(self, headers, practice, groupID=None, stacks=None):

        #print 'headers = ', headers
        #print 'stacks = ', stacks

        self.practice = practice
        print 'self.practice = ', self.practice

        self.matchNum += 1
        self.roundNum = -1

        # Stack the headers (i.e. combine and rename them according to the
        # stacks parameter) and leave behind a map describing how to do the same
        # for the values passed in on subsequent calls to addRound().
        self.stackmaps = []
        s_headers = copy.copy(headers) # stacked headers
        if stacks == None:
            stacks = []
        for stack in stacks:
            stackmap = []
            # The first header in the stack (the second in the list, as the
            # first in the list is the 'stacked name'), we keep but rename to
            # the 'stacked name'.
            stacked_name = stack[0]
            stacked_index = s_headers.index(stack[1])
            s_headers[stacked_index] = stacked_name
            stackmap.append(stacked_index)
            # For the rest of the headers in the stack, get their position in
            # s_headers, store it, then delete that item.
            for header in stack[2:]:
                i = s_headers.index(header)
                stackmap.append(i)
                del s_headers[i]
            self.stackmaps.append(stackmap)

        print 's_headers = ', s_headers
        print 'self.stackmaps = ', self.stackmaps

        # Now that the new headers are stacked and we've mapped out how to do
        # the same for the new values, we need to merge the new stacked headers
        # into the existing headers, leaving behind a map describing how to do
        # the same for the new stacked values.
        self.colmap = []
        for header in s_headers:
            if header in self.headers:
                # Already have this header: store its existing index
                self.colmap.append(self.headers.index(header))
            else:
                # This header is new for this match.  Stick it on the end and
                # store that index.
                i = len(self.headers)
                self.colmap.append(i)
                self.headers.append(header)
                self.grid.AppendCols(1)
                self.grid.SetColLabelValue(i, header)
                self.grid.AutoSizeColLabelSize(i)

        print 'self.colmap = ', self.colmap

        self.makeItTheRightSize()

    def addRound(self, values):

        self.roundNum += 1

        if self.sort == ASCENDING:
            self.rowNum += 1
        else:
            self.rowNum = 0
        
        # Stack the values according to stackmaps
        s_values = copy.copy(values)
        for stackmap in self.stackmaps:
            # Need to make sure the first value is a string, because we need to
            # add newlines between
            s_values[stackmap[0]] = str(s_values[stackmap[0]])
            # For each subsequent value in the stack, put it below the first
            # one and remove it from its original location.
            for i in stackmap[1:]:
                s_values[stackmap[0]] += '\n' + str(s_values.pop(i))

        #print 's_values = ', s_values

        # Now that we've stacked the values, write them into the grid at the
        # appropriate locations according to the colmap.
        if self.sort == ASCENDING:
            self.grid.AppendRows(1)
        else:
            self.grid.InsertRows(pos=0, numRows=1)
        for v, value in enumerate(s_values):
            self.grid.SetCellValue(self.rowNum, self.colmap[v], str(value))

        # Make text gray if a practice match
        if self.practice:
            for c in range(len(self.headers)):
                self.grid.SetCellTextColour(self.rowNum, c, 'grey')

        if self.showMatch:
            # Write the match and round into the first 2 cells
            self.grid.SetCellValue(self.rowNum, 0, str(self.matchNum + 1))
            self.grid.SetCellValue(self.rowNum, 1, str(self.roundNum + 1))
        else:
            # Write the round into the first cell
            self.grid.SetCellValue(self.rowNum, 0, str(self.roundNum + 1))

        self.grid.AutoSize()
        self.grid.MakeCellVisible(self.rowNum, 0)


        self.makeItTheRightSize()

    def makeItTheRightSize(self):

        self.grid.AutoSize()

        # Seems to be necessary to give the panel a sizer and use Layout() even
        # though there is only one child.  Otherwise, *sometimes* the grid will
        # end up offset upwards and won't come back down.
        self.GetSizer().Layout()
        
        # workaround for bug? in Grid that causes horizontal scrollbar to appear
        # whenever vertical scrollbar appears: add 20 extra pixels to the width
        # of the grid, which should be able to accommodate the vertical
        # scrollbar.
        # Now that I'm doing Layout() above, SetSize() seems to have no effect.
        # And SetSizeHints adds more pix every time, making grid wider & wider.
        #self.SetSize((w+20, self.minheight))
        #self.SetSizeHints(w+20, self.minheight)
        #self.grid.SetSize((w+20, self.minheight))
        #self.grid.SetSizeHints(w+20, self.minheight)

        # Workaround attempt #2.
        # changed from self.grid.GetSize(), because calling SetSizeHints() on
        # the grid with the actual height of the grid somehow caused the grid's
        # vertical scrollbar to fail to appear.
        w, h = self.GetSize()
        #print 'grid size = %d, %d' % (w, h)
        totalColWidth = 0
        for i in range(self.grid.GetNumberCols()):
            totalColWidth += self.grid.GetColSize(i)
        #self.grid.SetClientSize((totalColWidth + 20, h))
        self.grid.SetSizeHints(totalColWidth + 20, h)


        # 2009-02-23: Bug: when history columns are added, grid is truncated on
        # the right.
        self.GetSizer().Layout()
        self.Fit()  #  ClientHistoryBook panel

        
        #self.GetParent().Fit()  # main panel
        #self.GetParent().GetParent().Fit()  # frame
        

############ testing ################

class TestApp(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, wx.ID_ANY, 'ClientHistoryBook')

        hist = ClientHistory()
        hist.startMatch(['Amount\nRequested', 'Amount\nGranted'], False)
        hist.addRound([2, 2])
        hist.addRound([3, 3])
        hist.addRound([4, 4])
        hist.startMatch(['Your\nInvestment', 'Group\nInvestment',\
                'Your\nEarnings'], False)
        hist.addRound([5, 15, 7])
        hist.addRound([6, 16, 8])
        hist.addRound([7, 17, 9])
        hist.addRound([8, 18, 10])
        hist.addRound([8, 18, 10])
        hist.addRound([8, 18, 10])
        hist.addRound([8, 18, 10])
        hist.addRound([8, 18, 10])
        hist.addRound([8, 18, 10])
        hist.addRound([8, 18, 10])

        hist.startMatch(['Endowment', 'Clicks A', 'Clicks B', 'Profit'],\
                False,
                [0, ['Clicks', 1, 2], 3])
        hist.addRound([5, 1, 2, 10])
        hist.addRound([6, 3, 4, 12])
        hist.addRound([7, 5, 6, 14])
        hist.addRound([8, 7, 8, 16])


        chist = ClientHistoryBook(self, hist)

        self.Show(True)

def main():
    app = wx.PySimpleApp()
    frame = TestApp()
    app.MainLoop()

if __name__ == '__main__':
    __name__ = 'Main'
    main()
