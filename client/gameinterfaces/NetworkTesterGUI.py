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
import wx

from client import clientnet
import GameGUI

class NetworkTesterGUI(GameGUI.GameGUI):
    def __init__(self, communicator, initParams):
        GameGUI.GameGUI.__init__(self, communicator, initParams)

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(sizer)
        errorButton = wx.Button(self.panel, label="Cause error")
        sizer.Add(errorButton)

        self.Bind(wx.EVT_BUTTON, self.onErrorClicked, errorButton)

        self.causeError = False

        self.panel.Fit()
        self.Fit()
        self.Show(True)

        if initParams['type'] == 'reinit':
            self.onMessageReceived(initParams['message'])

    def onErrorClicked(self, event):
        self.causeError = True

    def onMessageReceived(self, mes):
        # Just echo the message back
        if mes['type'] == 'gm':
            if self.causeError:
                mes['error'] = 'asdlfkjsldfj'
                self.causeError = False
            self.communicator.send(mes)
