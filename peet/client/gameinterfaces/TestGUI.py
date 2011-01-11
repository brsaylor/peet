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

import wx

from peet.client import clientnet
import GameGUI

class TestGUI(GameGUI.GameGUI):

    """Test game GUI."""

    def __init__(self, communicator, initParams):
        GameGUI.GameGUI.__init__(self, communicator, initParams)
        #print "Hi, I'm TestGUI!  initParams = "
        #print self.initParams

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(sizer)
        self.matchRoundLabel = wx.StaticText(self.panel, wx.ID_STATIC,
                                             "Match -, Round -")
        sizer.Add(self.matchRoundLabel)
        self.spinner = wx.SpinCtrl(self.panel, min=1, initial=1)
        sizer.Add(self.spinner)
        self.sendButton = wx.Button(self.panel, wx.ID_ANY, "Send")
        self.sendButton.Enable(False)
        sizer.Add(self.sendButton)
        self.payoffLabel = wx.StaticText(self.panel, wx.ID_STATIC
                                         ,
                "Payoff: $'0.00 ($0.00)")
        sizer.Add(self.payoffLabel)

        self.messageBox = wx.TextCtrl(self.panel, #size=(400,300),
            style=wx.TE_MULTILINE|wx.TE_RICH2|wx.TE_READONLY)
        sizer.Add(self.messageBox, 1, wx.EXPAND)

        sizer.Add(self.chatPanel)
        self.chatPanel.Show(True)

        self.Bind(wx.EVT_BUTTON, self.onSendClicked, self.sendButton)
        
        self.Show(True)

    def onMessageReceived(self, mes):
        self.messageBox.AppendText(str(mes) + "\n")
        if mes['type'] == 'gm':
            self.sendButton.Enable(True)
        elif mes['type'] == 'payoff':
            self.payoffLabel.SetLabel("Payoff: $'%0.2f ($%0.2f)"\
                    % (mes['experimentCurrency'], mes['realCurrency']))
        elif mes['type'] == 'round':
            self.matchRoundLabel.SetLabel("Round " + str(mes['round']+1))

    def onSendClicked(self, event):
        self.sendButton.Enable(False)
        mes = {'type': 'gm'}
        mes['amount'] = self.spinner.GetValue()
        self.communicator.send(mes)
