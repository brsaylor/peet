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
from decimal import Decimal
import wx
from wx.lib.mixins.listctrl import ColumnSorterMixin
import wx.lib.newevent

from ClientData import ClientData
import images

# For sending right-click menu events to the server
ClientListEvent, EVT_CLIENT_LIST = wx.lib.newevent.NewEvent()

class ClientStatusListCtrl (wx.ListCtrl, ColumnSorterMixin):
    def __init__(self, parent, id, pos=wx.DefaultPosition, size=wx.DefaultSize,
            style=0):
        wx.ListCtrl.__init__(self, parent, id, pos, size, style)

        self.showUpPayment = Decimal('0.00')

        # for ColumnSorterMixin: a dictionary of lists, one for each row (data
        # item) which basically replicates what the list contains, but is
        # sortable (e.g. numbers are numbers rather than strings).  Indexed by
        # integers 0 to n.
        self.itemDataMap = {}

        self.numCols = 8  # number of columns
    
        # Hard way to create columns, because we need images (sort arrows)
        info = wx.ListItem()
        info.m_mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_IMAGE \
                | wx.LIST_MASK_FORMAT
        info.m_image = -1
        info.m_format = 0
        info.m_text = 'ID'
        self.InsertColumnInfo(0, info)
        info.m_text = 'IP Address'
        self.InsertColumnInfo(1, info)
        info.m_text = 'Name'
        self.InsertColumnInfo(2, info)
        info.m_text = 'Status'
        self.InsertColumnInfo(3, info)
        info.m_format = wx.LIST_FORMAT_RIGHT
        info.m_text = 'Game Earnings ($)'
        self.InsertColumnInfo(4, info)
        info.m_text = 'Rounded Earnings ($)'
        self.InsertColumnInfo(5, info)
        info.m_text = 'Show-up Payment ($)'
        self.InsertColumnInfo(6, info)
        info.m_text = 'Total Earnings ($)'
        self.InsertColumnInfo(7, info)

        # This is the widest each column has ever been after an automatic
        # resize.  They will never be auto-resized smaller than this.
        self.maxColumnWidths = [0] * self.numCols
        for i in range(self.numCols):
            self.SetColumnWidth(i, wx.LIST_AUTOSIZE_USEHEADER)
            self.maxColumnWidths[i] = self.GetColumnWidth(i)

            # Unfortunately, AUTOSIZE_USE_HEADER doesn't take images into
            # account, so even if we put sort arrow images in all the headers to
            # begin with, they end up too small to accommodate the arrows.  So
            # we'll add a few pixels here:
            self.maxColumnWidths[i] += 16
            self.SetColumnWidth(i, self.maxColumnWidths[i])

        # Maybe the name is misleading: it just tells updateClient() whether to
        # do a resizeColumns() next time it is called.  updateClients() sets it
        # to false to avoid doing a resize for every updated client when
        # updating multiple clients.
        self.columnsNeedResize = True

        self.sortColumn = 0

        self.Bind(wx.EVT_LIST_COL_CLICK, self.onHeaderClicked)

        # Right-clicking has some platform differences.  Windows sends an
        # EVT_COMMAND_RIGHT_CLICK while GTK sends an EVT_RIGHT_UP.  We need to
        # know the location of the click.  EVT_RIGHT_UP has GetX()/GetY(), but
        # EVT_COMMAND_RIGHT_CLICK doesn't and it crashes.  But both platforms
        # have an EVT_RIGHT_DOWN that seems to work the same way, so we get the
        # location of the click in EVT_RIGHT_DOWN, and the UP/CLICK event comes
        # later and pops up the menu.
        self.Bind(wx.EVT_RIGHT_DOWN, self.onRightDown)
        # for wxMSW:
        self.Bind(wx.EVT_COMMAND_RIGHT_CLICK, self.onRightClick)
        # for wxGTK:
        self.Bind(wx.EVT_RIGHT_UP, self.onRightClick)

        # Sort arrow bitmaps
        self.il = wx.ImageList(16, 16)
        self.sm_up = self.il.Add(images.getSmallUpArrowBitmap())
        self.sm_dn = self.il.Add(images.getSmallDnArrowBitmap())
        self.SetImageList(self.il, wx.IMAGE_LIST_SMALL)

        # needs to be after the Bind
        ColumnSorterMixin.__init__(self, self.numCols)

    # for ColumnSorterMixin
    def GetListCtrl(self):
        return self

    # Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
    def GetSortImages(self):
        return (self.sm_dn, self.sm_up)

    def makeRows(self, count):

        # populate the itemDataMap for ColumnSorterMixin
        for id in range(count):
            self.itemDataMap[id] =\
                   [id+1, '', '', 'Waiting for connection',
                           Decimal('0.00'),
                           Decimal('0.00'),
                           Decimal('0.00'),
                           Decimal('0.00')]

        items = self.itemDataMap.items()
        for key, data in items:
            index = self.InsertStringItem(sys.maxint, str(data[0]))
            for col in range(1, self.numCols):
                self.SetStringItem(index, col, str(data[col]))

            # for ColumnSorterMixin
            self.SetItemData(index, key)

        self.resizeColumns()

    def setShowUpPayment(self, showUpPayment):
        self.showUpPayment = showUpPayment

    def updateClient(self, client):
        # client is of type ClientData

        roundedEarnings = client.getRoundedEarnings()
        if client.connection != None:
            address = client.connection.address[0]
        else:
            address = ''

        # Update the itemDataMap for ColumnSorterMixin
        id = client.id
        self.itemDataMap[id][0] = client.id+1
        self.itemDataMap[id][1] = address
        self.itemDataMap[id][2] = client.name if client.name != None else ''
        self.itemDataMap[id][3] = client.status
        self.itemDataMap[id][4] = client.earnings
        self.itemDataMap[id][5] = roundedEarnings
        self.itemDataMap[id][6] = self.showUpPayment
        self.itemDataMap[id][7] = roundedEarnings + self.showUpPayment

        # Get the position of the item
        itemPos = self.FindItemData(-1, id)

        # Update the representation in the ListCtrl
        for col in range(self.numCols):
            self.SetStringItem(itemPos, col, str(self.itemDataMap[id][col]))

        if self.columnsNeedResize:
            self.resizeColumns()

    def updateClients(self, clients):
        self.columnsNeedResize = False
        for id, client in enumerate(clients):
            if client == None:
                # Create a dummy client
                client = ClientData(id, None, 'Waiting for connection',
                        Decimal('0.00'), None)
            self.updateClient(client)
        self.columnsNeedResize = True
        self.resizeColumns()

    def resizeColumns(self):
        # Unfortunately, wx doesn't seem to provide a way to set the minimum
        # autosize width.  Nor does it seem to provide a way to autosize to
        # accommodate both the widest data item and the header; only one or the
        # other.  So we'll autosize for the headers now, and subsequently
        # autosize for content when the content is updated, but keep track of
        # the largest width each column has ever been after a resize, and then
        # restore to that width if the column ever gets smaller than that.

        for i in range(self.numCols):
            # Set column width automatically based on content width (not header)
            self.SetColumnWidth(i, wx.LIST_AUTOSIZE)
            w = self.GetColumnWidth(i)
            if w < self.maxColumnWidths[i]:
                # Restore previous width if this made it shrink
                self.SetColumnWidth(i, self.maxColumnWidths[i])
            else:
                # else, this is the new max width
                self.maxColumnWidths[i] = w

    ### Methods for sorting by column

    def onHeaderClicked(self, event):

        return


        colNum = event.GetColumn()

        # Make the column header bold
        col = self.GetColumn(colNum)
        #print col.GetText()
        #font = col.GetFont()
        #font.SetWeight(wx.FONTWEIGHT_BOLD)
        #col.SetFont(font)
        col.SetText('foo')  # this works
        col.SetTextColour('BLUE')  # this doesn't work
        self.SetColumn(colNum, col)

        # Make the previously clicked column header normal weight
        col = self.GetColumn(self.sortColumn)
        font = col.GetFont()
        font.SetWeight(wx.FONTWEIGHT_NORMAL)
        col.SetFont(font)
        self.SetColumn(self.sortColumn, col)


        ## The following code from the Wiki works to set the first row to bold.
        # Get the item at a specific index:
        #item = self.GetItem(0)
        # Get its font, change it, and put it back:
        #font = item.GetFont()
        #font.SetWeight(wx.FONTWEIGHT_BOLD)
        #item.SetFont(font)
        # This does the trick:
        #self.SetItem(item)

        #self.sortColumn = colNum
        #self.SortItems(self.sortFunc)

    def onRightDown(self, event):
        x = event.GetX()
        y = event.GetY()
        itemid, flags = self.HitTest((x, y))
        if itemid != wx.NOT_FOUND and flags & wx.LIST_HITTEST_ONITEM:
            # 'itemid' is the index of the item, index 0 being the item
            # currently at the top of the list.  The item data associated with
            # each item is the client ID.
            self.idClicked = self.GetItemData(itemid)
        else:
            self.idClicked = -1

    def onRightClick(self, event):

        if self.idClicked != -1:

            menu = wx.Menu()
            menuItem = menu.Append(wx.NewId(), "Drop client")
            self.Bind(wx.EVT_MENU, self.onDropClicked, menuItem)
            self.PopupMenu(menu)
            menu.Destroy()

    def onDropClicked(self, event):
        print 'onDropClicked'
        wx.PostEvent(self, ClientListEvent(command='drop',
            id=self.idClicked))

    # FIXME: I don't think this is used anymore
    def sortFunc(self, item1, item2):
        # item1 is the "item data" associated with the first item (row) using
        # SetItemData(), i.e. the client ID.  item2 is similarly the ID of the
        # second item to compare.
        # Return 0 if the items are equal, negative value if the first item is
        # less than the second one and positive value if the first one is
        # greater than the second one.

        #print 'sortFunc('+str(item1)+', '+str(item2)+')'

        # FIXME: is this guaranteed to be the same 'clients' as the
        # GameController has?
        clients = self.GetParent().clients
        c1 = clients[item1]
        c2 = clients[item2]

        if self.sortColumn == 0:
            # sort by ID
            if item1 == item2: return 0
            elif item1 < item2: return -1
            elif item1 > item2: return 1
        elif self.sortColumn == 2:
            # sort by name
            if c1.name == c2.name: return 0
            elif c1.name < c2.name: return -1
            elif c1.name > c2.name: return 1
        else:
            return 0
