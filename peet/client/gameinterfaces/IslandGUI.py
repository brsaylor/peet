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
import wx
from wx.lib.scrolledpanel import ScrolledPanel
from wx.lib import newevent

from peet.client import clientnet
import GameGUI
from peet.shared.widgets import FloatSpin
from peet.client.widgets import BorderedPanel

# Fonts and colors
lightBlue = '#bfbfff' # GIMP: blue, then 25% saturation
lightRed = '#ffbfbf' # GIMP: red, then 25% saturation
lightGreen = '#bfffbf' # GIMP: green, then 25% saturation
lightOrange = '#ffbf80'
font = wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL,
        wx.FONTWEIGHT_NORMAL)
boldFont = wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL,
        wx.FONTWEIGHT_BOLD)
headingFont = wx.Font(18, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL,
        wx.FONTWEIGHT_BOLD)
transactionFont = wx.Font(16, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL,
        wx.FONTWEIGHT_BOLD)

# margins, padding, etc.
padding = 20
thinpadding = padding/2

# Events
# Mouse clicked on a point on production graph
ProductionClickEvent, EVT_PRODUCTION_CLICK = newevent.NewEvent()
# Selected point on production graph changed
ProductionMoveEvent, EVT_PRODUCTION_MOVE = newevent.NewEvent()
#
# For telling a MessageDialog to close
#CloseDialogEvent, EVT_CLOSE_DIALOG = newevent.NewCommandEvent()

class IslandGUI(GameGUI.GameGUI):
    def __init__(self, communicator, initParams):
        GameGUI.GameGUI.__init__(self, communicator, initParams)

        self.panel.SetBackgroundColour('white')
        self.panel.SetFont(font)

        # outerSizer holds the top line of information on the top, and
        # everything else on the bottom.
        outerSizer = wx.BoxSizer(wx.VERTICAL)
        self.outerSizer = outerSizer # need later to re-Layout()
        self.panel.SetSizer(outerSizer)

        # topSizer holds the top line of information
        f = wx.SizerFlags(1)
        topSizer = wx.BoxSizer(wx.HORIZONTAL)
        topSizer.AddF(wx.StaticText(self.panel, wx.ID_STATIC, self.name), f)
        topSizer.AddF(wx.StaticText(self.panel, wx.ID_STATIC,\
               'ID: %d' % (self.id + 1)), f)
        self.yourColorLabel = wx.StaticText(self.panel, wx.ID_STATIC, '-')
        topSizer.AddF(self.yourColorLabel, f)
        self.matchRoundLabel = wx.StaticText(self.panel, wx.ID_STATIC, '-')
        topSizer.AddF(self.matchRoundLabel, f)
        f = wx.SizerFlags(0)
        f.Align(wx.ALIGN_CENTER)
        f.Border(wx.ALL, padding)
        outerSizer.AddF(topSizer, f)

        # bottomSizer holds the market (mktSizer) on the left and the account
        # (acctSizer) on the right
        bottomSizer = wx.BoxSizer(wx.HORIZONTAL)

        # mktSizer holds the heading, market info line, market panel, and
        # bid/ask spinner and button.
        f = wx.SizerFlags(0)
        f.Align(wx.ALIGN_CENTER)
        f.Border(wx.LEFT|wx.BOTTOM, padding)
        mktSizer = wx.BoxSizer(wx.VERTICAL)
        self.mktSizer = mktSizer # We need it later to re-Layout()
        mktHeading = wx.StaticText(self.panel, wx.ID_STATIC, 'Market')
        mktHeading.SetFont(headingFont)
        mktSizer.AddF(mktHeading, f)

        # Market info, e.g. "You are selling blue." - separate labels for
        # different fonts.
        mktInfoSizer = wx.BoxSizer(wx.HORIZONTAL)
        mktInfoSizer.Add(wx.StaticText(self.panel, wx.ID_STATIC, 'You are '))
        self.mktRoleLabel = wx.StaticText(self.panel, wx.ID_STATIC, '- ')
        self.mktRoleLabel.SetFont(boldFont)
        mktInfoSizer.Add(self.mktRoleLabel)
        self.mktColorLabel = wx.StaticText(self.panel, wx.ID_STATIC, '-.')
        self.mktColorLabel.SetFont(boldFont)
        mktInfoSizer.Add(self.mktColorLabel)
        mktSizer.AddF(mktInfoSizer, f)

        # Market panel
        self.mktPanel = MarketPanel(self.panel)
        mktSizer.AddF(self.mktPanel, f)

        # Bid/Ask spinner and button
        spinSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.spinner = FloatSpin.FloatSpin(self.panel, min_val = 0.1,
                value = 0.1, digits = 2, increment = 0.1,
                extrastyle = FloatSpin.FS_RIGHT)
        spinSizer.Add(self.spinner)
        self.submitButton = wx.Button(self.panel, wx.ID_ANY, 'Submit')
        self.submitButton.Disable()
        self.Bind(wx.EVT_BUTTON, self.onSubmitClicked, self.submitButton)
        spinSizer.Add(self.submitButton, flag=wx.LEFT, border=padding)
        mktSizer.AddF(spinSizer, f)

        bottomSizer.Add(mktSizer)

        # acctSizer holds account panel, chat box, and market timer
        f = wx.SizerFlags(0)
        f.Align(wx.ALIGN_CENTER)
        f.Border(wx.LEFT|wx.RIGHT|wx.BOTTOM, padding)
        acctSizer = wx.BoxSizer(wx.VERTICAL)
        self.acctSizer = acctSizer
        acctHeading = wx.StaticText(self.panel, wx.ID_STATIC, 'Account')
        acctHeading.SetFont(headingFont)
        acctSizer.AddF(acctHeading, f)

        # Extra space to push the rest down as far as mktInfoSizer on the left
        # does
        t = wx.StaticText(self.panel, wx.ID_STATIC, 'You are selling') 
        t.SetFont(boldFont)
        t.SetForegroundColour('white') # to hide it
        acctSizer.AddF(t, f)

        # Account panel
        self.acctPanel = AccountPanel(self.panel)
        acctSizer.AddF(self.acctPanel, f)

        self.acctSizerSpacer = acctSizer.AddStretchSpacer()

        # Chat panel
        f.Proportion(2)
        acctSizer.AddF(self.chatPanel, f)
        f.Proportion(0)

        # Timer
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.onTimer, self.timer)
        self.timeLeft = 0
        self.timerLabel = wx.StaticText(self.panel, wx.ID_STATIC, ' ')
        self.timerLabel.SetFont(headingFont)
        f.Expand()
        f.Proportion(0)
        f.Align(wx.ALIGN_BOTTOM | wx.ALIGN_RIGHT)
        acctSizer.AddF(self.timerLabel, f)

        bottomSizer.Add(acctSizer, flag=wx.EXPAND)

        outerSizer.Add(bottomSizer)

        # A list of window IDs of MessageDialogs that are currently shown
        # (generally only 1).  Every time one is created, MessageDialog.__init__
        # appends its ID to this list.
        # Call closeMessageDialogs() to close them all.
        self.openMessageDialogs = []

        # This seems to do what I wanted Fit() to do: Just set the window to a
        # size such that nothing is chopped off and there's no extra space.
        # Another one of the many mysteries of wxWidgets layout solved!
        self.SetClientSize(self.panel.GetBestSize())

        self.CentreOnScreen()
        self.Show(True)

        # Process reinitialization parameters.
        if initParams['type'] == 'reinit':
            print 'Re-initializing'
            self.doReinit(initParams)

    def doReinit(self, rp):

        self.onMessageReceived({'type': 'gm', 'subtype': 'matchAndRound',
            'match': rp['match'],
            'round': rp['round'],
            'doNotPrintEvent': True})
            # Don't print the match and round in the market panel - we take care
            # of that in the loop below
        self.onMessageReceived(rp['matchInitMessage'])
        self.onMessageReceived({'type': 'gm', 'subtype': 'acctUpdate',
            'acct': rp['acct']})
        
        # Restore the marketpanel from 'events' and 'mktHist'
        # -- go thru all matches and rounds up thru current, but check
        # whether they exist in 'events and 'mktHist'
        # 2009-06-12 Too slow when there are many events. Only do current round.
        for m in range(rp['match'], rp['match']+1):
            for r in range(rp['round'], rp['round']+1):
                self.mktPanel.addEvent({'type': 'gm',
                    'subtype': 'matchAndRound', 'match': m, 'round': r})
                
                # True if this is the current round
                thisRound = (m == rp['match'] and
                        r == rp['round'])

                for color in ('blue', 'red'):
                    e = rp['events'][m][r]
                    print e
                    
                    # production shock
                    if color == self.color and e.get('prodShock') == 1:
                        self.mktPanel.addEvent({'subtype': 'prodShock'})

                    # production choice (but not if it hasn't been made yet)
                    if not thisRound\
                            or color in rp['productionChoicesMade']:
                        self.mktPanel.addEvent(
                            {'subtype': 'productionChoice',
                            'color': color,
                            'green': e.get('productionChoice_green'),
                            color: e.get('productionChoice_' + color)})
                    
                    # money shock
                    if e.get('moneyShock_'+color+'Mkt') == 1:
                        self.mktPanel.addEvent({'subtype': 'moneyShock',
                            'amount': e.get('moneyShockAmountRealized_' +
                                color + 'Mkt')})
                    
                    # market activity
                    mkt = rp['mktHist'][m][r][color]
                    # If any market events for this match, round, and color,
                    if len(mkt) > 0:
                        # Set up the market panel
                        self.mktPanel.setMarketColor(color)
                    for e in mkt:
                        if e['Action'] == 'bid':
                            self.mktPanel.addEvent({'subtype': 'bid',
                                'id': e['Buyer'], 'amount': e['Bid']})
                        elif e['Action'] == 'ask':
                            self.mktPanel.addEvent({'subtype': 'ask',
                                'id': e['Seller'], 'amount': e['Ask']})
                        elif e['Action'] == 'accept':
                            self.mktPanel.addEvent(
                                    {'subtype': 'transaction',
                                    'buyerID': e['Buyer'],
                                    'sellerID': e['Seller'],
                                    'amount': e['Accept']})


        # If the server is waiting for a reply for some message, process
        # that message, too.
        if rp['unansweredMessage'] != None:
            wx.CallAfter(self.onMessageReceived, rp['unansweredMessage'])

    def makeChatString(self, mes, id):
        # Overriding GameGUI.makeChatString()
        s = '(B) ' if id in self.blueIDs else '(R) '
        s += '%d: %s\n' % (id+1, mes['message'])
        return s

    def onMessageReceived(self, m):
        if m['type'] == 'pause':
            self.timer.Stop()
            self.submitButton.Disable()

        elif m['type'] == 'gm':

            if m['subtype'] == 'initmatch':
                self.closeMessageDialogs()
                self.color = m['color']
                self.blueIDs = m['blueIDs']
                self.yourColorLabel.SetLabel(self.color)
                self.yourColorLabel.SetForegroundColour(self.color)
                self.yourColorLabel.SetFont(boldFont)
                self.acctSizerSpacer.Show(m['chat'] == 'NO_CHAT')
                self.chatPanel.Show(m['chat'] != 'NO_CHAT')
                self.mktPanel.setPlayerColor(self.color)

            elif m['subtype'] == 'matchAndRound':
                self.closeMessageDialogs()
                self.matchRoundLabel.SetLabel('Match %d, Round %d' %
                        (m['match'], m['round'] + 1))
                self.outerSizer.Layout()
                if not m.has_key('doNotPrintEvent'):
                    self.mktPanel.addEvent(m)

            elif m['subtype'] == 'acctUpdate':
                self.acctPanel.update(m['acct'])
                # Account panel may have grown to accommodate new digits.
                self.SetClientSize(self.panel.GetBestSize())

            # Request from server for the production choice.
            # It also contains info on whether this player is receiving a
            # production shock or money shock.
            # Shows a series of dialogs and sends a message to the server when
            # player is ready for the auction.
            elif m['subtype'] == 'production':
                self.closeMessageDialogs()

                if m['color'] == self.color:
                    self.pf = m['pf']

                    # DIALOG: production shock
                    if m['prodShock']:
                        self.mktPanel.addEvent({'subtype': 'prodShock'})
                        text = "You have received a production shock."
                        dlg = MessageDialog(self, text, "Production Shock")
                        dlg.ShowModal()
                        dlg.Destroy()

                    # DIALOG: production choice
                    dlg = ProductionDialog(self, self.color, self.pf,
                            m['timeLimit'])
                    choice = dlg.ShowModal()
                    e = m
                    e['green'] = self.pf[choice][0]
                    e[m['color']] = self.pf[choice][1]
                    dlg.Destroy()
                else:
                    e = m
                    choice = None
                e['subtype'] = 'productionChoice'
                self.mktPanel.addEvent(e)
                
                # DIALOG: money shock
                if m['moneyShock']:
                    amount = m['moneyShockAmount']
                    self.mktPanel.addEvent({'subtype': 'moneyShock',
                        'amount': amount})
                    text = "You have received a money shock.\n"
                    if amount > 0:
                        text += "You have gained $%0.2f." % amount
                    else:
                        text += "You have lost $%0.2f." % abs(amount)
                    dlg = MessageDialog(self, text, "Money Shock")
                    dlg.ShowModal()
                    dlg.Destroy()

                # MESSAGE TO SERVER: ready for auction
                # (and here's my production choice)
                self.communicator.send({'type': 'gm', 'choice': choice})

                # DIALOG: please wait
                # (closed automatically when everyone's ready and auction
                # starts)
                text = "Please wait for the other players"\
                    + " to make their production choices."
                dlg = MessageDialog(self, text, 'Please Wait',
                        showOKButton=False)
                dlg.ShowModal()
                dlg.Destroy()
            
            # Confirmation from server after all production choices have been
            # submitted
            elif m['subtype'] == 'productionChoice':
                self.closeMessageDialogs()
                #self.mktPanel.addEvent(m)

            # Start the auction
            elif m['subtype'] == 'auction':
                self.closeMessageDialogs()
                self.setTimeLeft(m['auctionTime'])
                self.timer.Start(1000)
                self.mktColor = m['color']
                self.mktPanel.setMarketColor(m['color'])
                self.mktRoleLabel.SetLabel(
                        'selling' if self.color == self.mktColor else 'buying')
                self.mktColorLabel.SetLabel(' ' + self.mktColor + '.')
                self.mktColorLabel.SetForegroundColour(self.mktColor)
                self.mktSizer.Layout()
                self.submitButton.SetLabel(
                        'Ask' if self.color == self.mktColor else 'Bid')
                self.submitButton.Enable()

            elif m['subtype'] == 'error':
                self.closeMessageDialogs()
                if m['error'] == 'bidTooLow':
                    text = "You must bid higher than the current high bidder."
                if m['error'] == 'notEnoughDollars':
                    text = "You don't have enough dollars."
                if m['error'] == 'askTooHigh':
                    text = "You must ask lower than the current low seller."
                if m['error'] == 'notEnoughChips':
                    text = "You don't have enough " + self.mktColor + "."
                dlg = MessageDialog(self, text, 'Error')
                dlg.ShowModal()
                dlg.Destroy()

            elif m['subtype'] in ('bid', 'ask', 'transaction'):
                self.mktPanel.addEvent(m)

            elif m['subtype'] == 'timeup':
                self.closeMessageDialogs()
                self.submitButton.Enable(False)
                self.timer.Stop()
                self.setTimeLeft(0)

    def onTimer(self, event):
        self.setTimeLeft(self.timeLeft - 1)

    def setTimeLeft(self, t):
        self.timeLeft = t
        min = t / 60
        sec = t % 60
        self.timerLabel.SetLabel('%d:%02d' % (min, sec))
        self.timerLabel.SetForegroundColour('black' if t > 10 else 'red')

    def onSubmitClicked(self, event):

        # Determine whether it's an ask or a bid.
        if self.mktColor == self.color:
            action = 'ask'
        else:
            action = 'bid'

        amount = Decimal(self.spinner.GetTextCtrl().GetValue())
        m = {'type': 'gm', 'subtype': action, 'amount': amount}
        self.communicator.send(m)

    def closeMessageDialogs(self):
        print 'closeMessageDialogs'
        dlgs = []
        for dlgID in self.openMessageDialogs:
            dlgs.append(wx.FindWindowById(dlgID))
        for dlg in dlgs:
            #wx.CallAfter(dlg.EndModal, 1) # Seems to be unnecessary
            # Be paranoid and make sure it hasn't been destroyed in the mean
            # time:
            if dlg != None:
                dlg.EndModal(1)
        #wx.PostEvent(self, CloseDialogEvent(EVT_CLOSE_DIALOG))

class MarketPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        self.h = 400 # height of scrolled area
        self.hgap = 6  # Horizontal spacing for GridSizers
        self.pageSize = 50 # scrollbar page up/down distance in pixels

        self.SetBackgroundColour('white')

        vsizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(vsizer)

        self.headerPanel = wx.Panel(self)
        self.headerPanel.SetBackgroundColour('white')
        gsizer = wx.GridSizer(1, 5, hgap = self.hgap)
        self.headerPanel.SetSizer(gsizer)
        for colHeader in ('Buyer', 'Bid', 'Accept', 'Ask', 'Seller'):
            t = wx.StaticText(self.headerPanel, wx.ID_STATIC, colHeader)
            t.SetFont(boldFont)
            gsizer.Add(t, flag=wx.ALIGN_CENTER)
        vsizer.Add(self.headerPanel)

        # self.w (width of the scrolled area) = width of header panel
        vsizer.Layout() # unknown until Layout()
        self.w = self.headerPanel.GetSize()[0]

        # A custom scrolled panel rather than wx.ScrolledPanel, because we never
        # want a horizontal scrollbar and always want a vertical scrollbar and
        # want to set the width of {everything excluding the scrollbar}, none of
        # which wx.ScrolledPanel seems to me to be able to do.

        # Scrolled area on the left, scrollbar on the right
        hsizer = wx.BoxSizer(wx.HORIZONTAL)

        # One panel, stationary and always the same size, which acts as the
        # port/window
        self.scrollPort = wx.Panel(self, style=wx.BORDER_SIMPLE)

        # Set the width of the scrollport to match the width of the header row
        # (which is unknown until after Layout()), and the height to the height
        # we want.  I don't understand why, but SetSize() doesn't work, it must
        # be SetMinSize(), even though we aren't calling Fit() anywhere.
        # NOTE: The behavior of wx sizers can be difficult to fathom.  My latest
        # theory: avoid using Fit() and things will make a bit more sense.
        self.scrollPort.SetMinSize((self.w, self.h))

        # Now, the scrolled panel, which is a child of scrollPort, which may
        # move up or down, and whose visible area (the area drawn on the
        # scrollPart) may be smaller than its actual size.
        # No sizers here - position is controlled manually.
        self.scrolledPanel = wx.Panel(self.scrollPort)
        self.scrolledPanel.SetBackgroundColour('white')
        self.scrolledPanelSizer = wx.BoxSizer(wx.VERTICAL)
        self.scrolledPanel.SetSizer(self.scrolledPanelSizer)

        # Just as with the port, set the minimum size of the scrolled panel
        self.scrolledPanel.SetMinSize((self.w, self.h))
        # I don't understand why, but need to SetSize as well.  Maybe SetMinSize
        # doesn't work because it's not contained in a sizer.
        self.scrolledPanel.SetSize((self.w, self.h))
        # Also, in Windows but not GTK, SetMinSize does not prevent shrinking
        # beyond minsize by calling SetSize

        hsizer.Add(self.scrollPort)

        # The scrollbar
        self.scrollbar = wx.ScrollBar(self, style=wx.SB_VERTICAL,
                size=(-1, self.h))
        # As usual, using wxWidgets docs instead of wxPython docs because
        # translating from C++ is easier than filling in the many blanks left in
        # the wxPython docs...
        # http://docs.wxwidgets.org/stable/wx_wxscrollbar.html
        #   virtual void SetScrollbar(int position, int thumbSize, int range,
        #                             int pageSize, const bool refresh = true)
        self.scrollbar.SetScrollbar(0, self.h, self.h, self.pageSize)
        self.scrollbarHeld = False
        self.Bind(wx.EVT_SCROLL_THUMBTRACK, self.onScrollThumbtrack,
                self.scrollbar)
        self.Bind(wx.EVT_SCROLL_THUMBRELEASE, self.onScrollThumbRelease,
                self.scrollbar)
        self.Bind(wx.EVT_SCROLL_LINEUP, self.onScrollLineUp,
                self.scrollbar)
        self.Bind(wx.EVT_SCROLL_LINEDOWN, self.onScrollLineDown,
                self.scrollbar)
        self.Bind(wx.EVT_SCROLL_PAGEUP, self.onScrollPageUp,
                self.scrollbar)
        self.Bind(wx.EVT_SCROLL_PAGEDOWN, self.onScrollPageDown,
                self.scrollbar)
        hsizer.Add(self.scrollbar)

        vsizer.Add(hsizer)

    def onScrollThumbtrack(self, event):
        self.scrolledPanel.SetPosition((0, -event.GetPosition()))
        self.scrollbarHeld = True

    def onScrollThumbRelease(self, event):
        self.scrolledPanel.SetPosition((0, -event.GetPosition()))
        self.scrollbarHeld = False

    def onScrollLineUp(self, event):
        self.scrolledPanel.SetPosition((0, -event.GetPosition()))
    def onScrollLineDown(self, event):
        self.scrolledPanel.SetPosition((0, -event.GetPosition()))
    def onScrollPageUp(self, event):
        self.scrolledPanel.SetPosition((0, -event.GetPosition()))
    def onScrollPageDown(self, event):
        self.scrolledPanel.SetPosition((0, -event.GetPosition()))

    def setPlayerColor(self, color):
        self.playerColor = color

    def setMarketColor(self, color):
        self.mktColor = color
        if color == 'blue':
            self.lightColor = lightBlue
        else:
            self.lightColor = lightRed

    def addEvent(self, m):

        # Create a panel for the row to add to the bottom of the scrolled panel.
        panel = wx.Panel(self.scrolledPanel)

        f = wx.SizerFlags(1)
        f.Align(wx.ALIGN_CENTER)

        if m.get('subtype') == 'matchAndRound':
            panel.SetBackgroundColour('black')
            sizer = wx.BoxSizer(wx.VERTICAL)
            panel.SetSizer(sizer)
            t = wx.StaticText(panel, wx.ID_STATIC, 'Match %d, Round %d'
                    % (m['match'] + 1, m['round'] + 1))
            t.SetFont(boldFont)
            t.SetForegroundColour('white')
            sizer.Add(t, flag=wx.ALIGN_CENTER) # Center the text

        elif m['subtype'] == 'prodShock':
            panel.SetBackgroundColour(lightOrange)
            sizer = wx.BoxSizer(wx.VERTICAL)
            panel.SetSizer(sizer)
            text = 'Production Shock'
            t = wx.StaticText(panel, wx.ID_STATIC, text)
            t.SetFont(boldFont)
            sizer.Add(t, flag=wx.ALIGN_CENTER) # Center the text

        elif m['subtype'] == 'productionChoice':
            panel.SetBackgroundColour(m['color'])
            sizer = wx.BoxSizer(wx.VERTICAL)
            panel.SetSizer(sizer)
            text = m['color'].capitalize() + ' Production'
            if m['color'] == self.playerColor:
                text += ' (%d green, %d %s)' \
                        % (m['green'], m[m['color']], m['color'])
            t = wx.StaticText(panel, wx.ID_STATIC, text)
            t.SetFont(boldFont)
            t.SetForegroundColour('white')
            sizer.Add(t, flag=wx.ALIGN_CENTER) # Center the text

        elif m['subtype'] == 'moneyShock':
            panel.SetBackgroundColour(lightOrange)
            sizer = wx.BoxSizer(wx.VERTICAL)
            panel.SetSizer(sizer)
            text = 'Money Shock ('
            amount = m['amount']
            if amount < 0:
                text += 'lost $%0.2f)' % abs(amount)
            else:
                text += 'gained $%0.2f)' % amount
            t = wx.StaticText(panel, wx.ID_STATIC, text)
            t.SetFont(boldFont)
            sizer.Add(t, flag=wx.ALIGN_CENTER) # Center the text

        elif m['subtype'] == 'bid':
            panel.SetBackgroundColour(self.lightColor)
            sizer = wx.GridSizer(1, 5)
            panel.SetSizer(sizer)
            sizer.AddF(wx.StaticText(panel, wx.ID_STATIC, str(m['id']+1)), f)
            sizer.AddF(wx.StaticText(panel, wx.ID_STATIC, str(m['amount'])), f)
            sizer.AddF(wx.StaticText(panel, wx.ID_STATIC, ' '), f)
            sizer.AddF(wx.StaticText(panel, wx.ID_STATIC, ' '), f)
            sizer.AddF(wx.StaticText(panel, wx.ID_STATIC, ' '), f)

        elif m['subtype'] == 'ask':
            panel.SetBackgroundColour(self.lightColor)
            sizer = wx.GridSizer(1, 5)
            panel.SetSizer(sizer)
            sizer.AddF(wx.StaticText(panel, wx.ID_STATIC, ' '), f)
            sizer.AddF(wx.StaticText(panel, wx.ID_STATIC, ' '), f)
            sizer.AddF(wx.StaticText(panel, wx.ID_STATIC, ' '), f)
            sizer.AddF(wx.StaticText(panel, wx.ID_STATIC, str(m['amount'])), f)
            sizer.AddF(wx.StaticText(panel, wx.ID_STATIC, str(m['id']+1)), f)

        elif m['subtype'] == 'transaction':
            panel.SetBackgroundColour(self.lightColor)
            sizer = wx.GridSizer(1, 5)
            panel.SetSizer(sizer)
            sizer.AddF(wx.StaticText(panel, wx.ID_STATIC,str(m['buyerID']+1)),f)
            sizer.AddF(wx.StaticText(panel, wx.ID_STATIC, ' '), f)
            t = wx.StaticText(panel, wx.ID_STATIC, str(m['amount']))
            t.SetFont(transactionFont)
            sizer.AddF(t, f)
            sizer.AddF(wx.StaticText(panel, wx.ID_STATIC, ' '), f)
            sizer.AddF(wx.StaticText(panel,wx.ID_STATIC,str(m['sellerID']+1)),f)

        # In Windows but not GTK, when we expand the scrolledPanel by setting
        # its size to GetBestSize(), the "best size" allows these panels to
        # shrink, and therefore the scrolledPanel shrinks in width.  This
        # prevents the panel from shrinking.
        #panel.SetMinSize((self.w, -1))
        # Actually: fixed by only using the height part of GetBestSize()

        # Expand the row panel to fill the width of the scrolled panel
        self.scrolledPanelSizer.Add(panel, flag=wx.EXPAND)

        # The wx.EXPAND will do nothing until we call Layout on the scrolled
        # panel's sizer
        self.scrolledPanelSizer.Layout()

        # Make the scrolledPanel grow to fit all the child panels
        bestSize = self.scrolledPanel.GetBestSize() 
        # but don't let it be smaller than height of scrollport
        h = max(self.h, bestSize[1])
        self.scrolledPanel.SetSize((self.w, h))

        # Determine the position of the scrollbar.
        # If the user is dragging/holding it, leave it as is.
        # Otherwise, move it and the scrolledPanel itself to the bottom.
        if self.scrollbarHeld:
            pos = self.scrollbar.GetThumbPosition()
        else:
            pos = h - self.h
            self.scrolledPanel.SetPosition((0, -pos))

        # Set the scrollbar's new range and position
        self.scrollbar.SetScrollbar(
                pos,
                self.h,
                bestSize[1],
                self.pageSize)

class AccountPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        self.SetBackgroundColour('white')

        # rows=0 means add rows dynamically
        sizer = wx.FlexGridSizer(rows=0, cols=2, vgap=10, hgap=20)
        self.SetSizer(sizer)
        self.sizer = sizer

        t = wx.StaticText(self, wx.ID_STATIC, 'Dollars')
        t.SetFont(boldFont)
        sizer.Add(t)
        self.dollarsLabel = wx.StaticText(self, wx.ID_STATIC, '0.00')
        sizer.Add(self.dollarsLabel, flag=wx.ALIGN_RIGHT)

        t = wx.StaticText(self, wx.ID_STATIC, 'Blue')
        t.SetFont(boldFont)
        sizer.Add(t)
        self.blueLabel = wx.StaticText(self, wx.ID_STATIC, '0')
        sizer.Add(self.blueLabel, flag=wx.ALIGN_RIGHT)

        t = wx.StaticText(self, wx.ID_STATIC, 'Red')
        t.SetFont(boldFont)
        sizer.Add(t)
        self.redLabel = wx.StaticText(self, wx.ID_STATIC, '0')
        sizer.Add(self.redLabel, flag=wx.ALIGN_RIGHT)

        t = wx.StaticText(self, wx.ID_STATIC, 'Green')
        t.SetFont(boldFont)
        sizer.Add(t)
        self.greenLabel = wx.StaticText(self, wx.ID_STATIC, '0')
        sizer.Add(self.greenLabel, flag=wx.ALIGN_RIGHT)

        sizer.AddSpacer((-1, padding))
        sizer.AddSpacer((-1, padding))

        t = wx.StaticText(self, wx.ID_STATIC, 'Current Round Score')
        t.SetFont(boldFont)
        sizer.Add(t)
        self.roundScoreLabel = wx.StaticText(self, wx.ID_STATIC, '0')
        sizer.Add(self.roundScoreLabel, flag=wx.ALIGN_RIGHT)

        sizer.AddSpacer((-1, padding))
        sizer.AddSpacer((-1, padding))

        t = wx.StaticText(self, wx.ID_STATIC, 'Total Match Score')
        t.SetFont(boldFont)
        sizer.Add(t)
        self.matchScoreLabel = wx.StaticText(self, wx.ID_STATIC, '0')
        sizer.Add(self.matchScoreLabel, flag=wx.ALIGN_RIGHT)

    def update(self, acct):
        self.dollarsLabel.SetLabel(str(acct['dollars']))
        self.blueLabel.SetLabel(str(acct['blue']))
        self.redLabel.SetLabel(str(acct['red']))
        self.greenLabel.SetLabel(str(acct['green']))
        self.roundScoreLabel.SetLabel(str(acct['roundScore']))
        self.matchScoreLabel.SetLabel(str(acct['matchScore']))

        # Panel may need to grow to accommodate extra digits.
        self.SetSize(self.GetBestSize())
        self.sizer.Layout()

# wx.MessageDialog won't work for us, because:
# - You can't disable the close button
# - You can't set the font
class MessageDialog(wx.Dialog):
    def __init__(self, parent, text, title, showOKButton=True):
        wx.Dialog.__init__(self, parent, title=title,
                style = wx.DEFAULT_DIALOG_STYLE ^ wx.CLOSE_BOX)

        parent.openMessageDialogs.append(self.GetId())
        #self.Bind(EVT_CLOSE_DIALOG, self.onCloseDialog)

        panel = wx.Panel(self)
        panel.SetBackgroundColour(lightOrange)
        sizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(sizer)

        f = wx.SizerFlags(0)
        f.Align(wx.ALIGN_CENTER)
        f.Border(wx.ALL, padding)
        
        t = wx.StaticText(panel, wx.ID_STATIC, text)
        t.SetFont(font)
        t.Wrap(400)
        sizer.AddF(t, f)

        if showOKButton:
            self.OKButton = wx.Button(panel, wx.ID_ANY, 'OK')
            sizer.AddF(self.OKButton, f)
            self.Bind(wx.EVT_BUTTON, self.onOKClicked, self.OKButton)

        self.SetClientSize(panel.GetBestSize())
        self.CenterOnParent()

    def onOKClicked(self, event):
        self.EndModal(1)

    #def onCloseDialog(self, event):
    #    print 'onCloseDialog'
    #    event.Skip()
    #    self.EndModal(1)

    def EndModal(self, retCode):
        print 'EndModal'
        # Remove this dialog from the main frame's list of open message dialogs.
        # This dialog may already have been Ended, so check the list first.
        if self.GetId() in self.GetParent().openMessageDialogs:
            self.GetParent().openMessageDialogs.remove(self.GetId())
            wx.Dialog.EndModal(self, retCode)
        else:
            print ' - Dialog already closed'

class ProductionDialog(wx.Dialog):
    def __init__(self, parent, color, pf, timeLimit):
        wx.Dialog.__init__(self, parent,\
                style = wx.DEFAULT_DIALOG_STYLE ^ wx.CLOSE_BOX)

        self.color = color
        self.pf = pf

        f = wx.SizerFlags(0)
        f.Align(wx.ALIGN_CENTER)
        f.Border(wx.ALL, padding)

        panel = wx.Panel(self)
        panel.SetBackgroundColour('white')
        sizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(sizer)

        t = wx.StaticText(panel, wx.ID_STATIC, 'Production')
        t.SetFont(headingFont)
        sizer.AddF(t, f)

        gsizer = wx.FlexGridSizer(rows = 2, cols = 2, hgap = 8, vgap = 8)
        self.colorLabel = wx.StaticText(panel, wx.ID_STATIC, '000')
        self.colorLabel.SetFont(boldFont)
        self.colorLabel.SetForegroundColour('white') # hide initially
        gsizer.Add(self.colorLabel, flag=wx.ALIGN_RIGHT)
        t = wx.StaticText(panel, wx.ID_STATIC, color.capitalize())
        t.SetFont(boldFont)
        gsizer.Add(t, flag=wx.ALIGN_LEFT)
        self.greenLabel = wx.StaticText(panel, wx.ID_STATIC, '000')
        self.greenLabel.SetFont(boldFont)
        self.greenLabel.SetForegroundColour('white') # hide initially
        gsizer.Add(self.greenLabel, flag=wx.ALIGN_RIGHT)
        t = wx.StaticText(panel, wx.ID_STATIC, 'Green')
        t.SetFont(boldFont)
        gsizer.Add(t, flag=wx.ALIGN_LEFT)
        sizer.AddF(gsizer, f)

        prodPanel = ProductionPanel(panel, color, pf)
        sizer.AddF(prodPanel, f)
        prodPanel.Bind(EVT_PRODUCTION_CLICK, self.onProductionClick)
        prodPanel.Bind(EVT_PRODUCTION_MOVE, self.onProductionMove)

        # Timer to implement timelimit on production choice.
        self.timeLeft = timeLimit
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.onTimer, self.timer)
        self.timer.Start(1000, oneShot=False)
        self.timerLabel = wx.StaticText(panel, wx.ID_STATIC, str(self.timeLeft))
        self.timerLabel.SetFont(headingFont)
        sizer.AddF(self.timerLabel, f)

        self.SetClientSize(panel.GetBestSize())
        self.CenterOnParent()

    def onTimer(self, event):
        self.timeLeft -= 1
        self.timerLabel.SetLabel(str(self.timeLeft))
        if self.timeLeft <= 0:
            self.timer.Stop()
            # Time's up - choose the middle index, rounding up if even
            choice = len(self.pf) / 2
            self.EndModal(choice)

    def onProductionClick(self, event):
        # Close the dialog, returning production choice to main window
        self.timer.Stop()
        self.EndModal(event.selectedIndex)

    def onProductionMove(self, event):
        i = event.selectedIndex
        if i == None:
            g = '000'
            c = '000'
            self.greenLabel.SetForegroundColour('white')
            self.colorLabel.SetForegroundColour('white')
        else:
            g = '%3d' % self.pf[i][0]
            c = '%3d' % self.pf[i][1]
            self.greenLabel.SetForegroundColour('black')
            self.colorLabel.SetForegroundColour('black')
        self.greenLabel.SetLabel(g)
        self.colorLabel.SetLabel(c)
        #self.gsizer.Layout()

class ProductionPanel(wx.Panel):
    def __init__(self, parent, color, pf):
        wx.Panel.__init__(self, parent)

        self.color = color
        self.pf = pf

        # Visual parameters
        self.w = 400
        self.h = 400
        self.bgcolor = 'white'
        self.bordercolor = 'black'
        self.axiscolor = 'white'
        self.dotcolor = 'white'
        self.crosscolor = 'white'
        self.circlecolor = 'white'
        self.margin = 30
        self.dotr = 4
        self.circler = 16

        if self.color == 'blue':
            self.lightColor = lightBlue
        else:
            self.lightColor = lightRed

        self.mouseInWindow = False
        self.selectedIndex = None

        self.SetSize((self.w, self.h))
        self.bgbrush = wx.Brush(self.bgcolor)
        self.borderpen = wx.Pen(self.bordercolor, 2)
        self.axispen = wx.Pen(self.axiscolor, 2)
        self.dotbrush = wx.Brush(self.dotcolor)
        self.dotpen = wx.TRANSPARENT_PEN
        self.crosspen = wx.Pen(self.crosscolor, 2)
        self.circlepen = wx.Pen(self.circlecolor, 2)
        self.circlebrush = wx.TRANSPARENT_BRUSH

        # Unpack all the x and y coords and find maximum values
        self.X, self.Y = zip(*self.pf)
        self.maxx = max(self.X)
        self.maxy = max(self.Y)

        # Determine scaling ratio (want a square aspect ratio)
        maxcoord = max(self.maxx, self.maxy)
        minphysical = min(self.w, self.h)
        self.scale = float(minphysical - 2 * self.margin) / float(maxcoord)
        print 'scale = ', self.scale

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ENTER_WINDOW, self.onEnterWindow)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.onLeaveWindow)
        self.Bind(wx.EVT_MOTION, self.onMotion)
        self.Bind(wx.EVT_LEFT_UP, self.onClick)

        # Ignore clicks for 1 second after the panel first appears, to prevent
        # accidental clicking
        self.acceptingClicks = False
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.onTimer, self.timer)
        self.timer.Start(1000, oneShot=True)

    def onTimer(self, event):
        self.acceptingClicks = True
        self.axiscolor = 'black'
        self.axispen = wx.Pen(self.axiscolor, 2)
        self.dotcolor = 'black'
        self.dotbrush = wx.Brush(self.dotcolor)
        self.Refresh()

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        try:
            gc = wx.GraphicsContext.Create(dc)
        except NotImplementedError:
            dc.DrawText("This build of wxPython does not support the "
                        " wx.GraphicsContext family of classes.",
                        25, 25)
            return

        # Draw background with border
        bgbrush = gc.CreateLinearGradientBrush(0, 0, self.w, self.h,
                self.lightColor, lightGreen)
        gc.SetBrush(bgbrush)
        gc.SetPen(self.borderpen)
        gc.DrawRectangle(0, 0, self.w, self.w)

        # Draw axes
        gc.SetPen(self.axispen)
        gc.StrokeLine(0, self.h - self.margin, self.w, self.h - self.margin)
        gc.StrokeLine(self.margin, 0, self.margin, self.h)

        # Draw crosshairs
        if self.selectedIndex != None:
            gc.SetPen(self.crosspen)
            lx, ly = self.pf[self.selectedIndex] # logical x, y
            # physical x, y
            px = lx * self.scale + self.margin
            py = ly * self.scale * -1 + self.h - self.margin
            gc.StrokeLine(0, py, self.w, py)
            gc.StrokeLine(px, 0, px, self.h)
            gc.SetPen(self.circlepen)
            gc.SetBrush(self.circlebrush)
            gc.DrawEllipse(px - self.circler, py - self.circler,
                    self.circler * 2, self.circler * 2)

        # Draw axis labels
        #gc.SetFont(boldFont)
        #gc.DrawText('Green', 


        # Flip Y axis and move origin to create margin
        gc.Scale(1, -1)
        gc.Translate(self.margin, self.margin - self.h)

        # Draw dots
        gc.SetPen(self.dotpen)
        gc.SetBrush(self.dotbrush)
        for x, y in self.pf:
            gc.DrawEllipse(x * self.scale - self.dotr,
                    y * self.scale - self.dotr, self.dotr * 2, self.dotr * 2)

    def onEnterWindow(self, event):
        self.mouseInWindow = True
        self.selectedIndex = None

    def onLeaveWindow(self, event):
        self.mouseInWindow = False
        self.selectedIndex = None
        wx.PostEvent(self,
                    ProductionMoveEvent(selectedIndex=None))
        self.Refresh()

    # Mouse motion event
    def onMotion(self, event):

        # Determine logical coordinates (lx, ly) of mouse on graph
        lx = (event.GetX() - self.margin) / self.scale
        ly = (-event.GetY() - self.margin + self.h) / self.scale

        # Find the point with the closest coordinates
        d = 9999 # smallest distance found so far
        closest_i = None # index of nearest point
        for i in range(len(self.pf)):
            dx = self.pf[i][0] - lx # x distance
            dy = self.pf[i][1] - ly # y distance
            d2 = math.sqrt(dx*dx + dy*dy) # distance from lx to this point
            if d2 < d:
                d = d2
                closest_i = i
        
        # If it has changed since the previously selected index, update the
        # selected index and refresh the graph.
        if closest_i != self.selectedIndex:
            self.selectedIndex = closest_i
            wx.PostEvent(self,
                    ProductionMoveEvent(selectedIndex=self.selectedIndex))
            self.Refresh()

    def onClick(self, event):
        if not self.acceptingClicks:
            return
        if self.selectedIndex != None:
            wx.PostEvent(self,
                    ProductionClickEvent(selectedIndex=self.selectedIndex))
