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

import socket
import sys
import re
import getopt
import ConfigParser
import wx
import wx.lib.newevent

from peet.client import clientnet
from peet.client.gameinterfaces import GameGUI

class LoginWindow(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, wx.ID_ANY, "Client Login",
                          style=(wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER))

        # Read config file
        config = ConfigParser.SafeConfigParser()
        # Take default values from client-default.ini
        config.read([
            'peet/client/config/client-default.ini',
            'peet/client/config/client.ini'
            ])
        self.host = config.get('Server', 'Host')
        self.port = int(config.get('Server', 'Port'))
        print 'Host = ' + self.host
        print 'Port = ' + str(self.port)

        self.panel = wx.Panel(self)

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(sizer)
        prompt = wx.StaticText(self.panel, -1, "Please enter your name:")
        prompt.SetFont(wx.Font(18, wx.FONTFAMILY_ROMAN, wx.NORMAL, wx.NORMAL))
        sizer.Add(prompt, 0, wx.ALIGN_CENTER)
        self.loginField = wx.TextCtrl(self.panel, size=(300,-1),\
                style=wx.TE_PROCESS_ENTER)
        sizer.Add(self.loginField, 0, wx.ALIGN_CENTER)
        self.note = wx.StaticText(self.panel, -1,
                "Note: You do not need to enter your name to reconnect.")
        notefont = self.note.GetFont()
        notefont.SetStyle(wx.FONTSTYLE_ITALIC)
        self.note.SetFont(notefont)
        sizer.Add(self.note, 0, wx.ALIGN_CENTER)
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.loginButton = wx.Button(self.panel, -1, "Log In")
        loginFont = self.loginButton.GetFont()
        loginFont.SetWeight(wx.FONTWEIGHT_BOLD)
        self.loginButton.SetFont(loginFont)
        self.loginButton.Enable(False)
        hsizer.Add(self.loginButton, 0, wx.ALIGN_CENTER)
        self.reconnectButton = wx.Button(self.panel, -1, "Reconnect")
        hsizer.Add(self.reconnectButton, 0, wx.ALIGN_CENTER)
        sizer.Add(hsizer, 0, wx.ALIGN_CENTER)

        self.Bind(wx.EVT_TEXT, self.onType, self.loginField)
        self.Bind(wx.EVT_BUTTON, self.onLoginClicked, self.loginButton)
        self.Bind(wx.EVT_TEXT_ENTER, self.onLoginClicked, self.loginField)
        self.Bind(wx.EVT_BUTTON, self.reconnectClicked, self.reconnectButton)

        self.communicator = clientnet.Communicator(self.host, self.port,
                self.postNetworkEvent)
        self.Bind(GameGUI.EVT_NETWORK, self.onNetworkEvent)

        self.loginField.SetFocus()
        sizer.Fit(self)
        self.CenterOnScreen()
        self.Show(True)

        # Get command line options
        try:
            opts, args = getopt.getopt(sys.argv[1:], 'l:', ['login='])
        except  getopt.GetoptError, err:
            # print help information and exit:
            print str(err)
            self.usage()
            sys.exit(2)
        for o, a in opts:
            if o in ('-l', '--login'):
                self.loginField.SetValue(a)
                self.onLoginClicked(None)

    def usage(self):
        print """
            Command line options:
                --login, -l <client name>
        """

    def onType(self, event):
        """ User typed into the box.  Enable the login button (or disable if
        empty) """
        if self.loginField.GetValue() == '':
            self.loginButton.Enable(False)
        else:
            self.loginButton.Enable(True)

    def onLoginClicked(self, event):
        # Button clicked or Enter pressed
        
        # Ignore if no named entered
        if self.loginField.GetValue() == '':
            return

        self.loginField.Enable(False)
        self.loginButton.Enable(False)
        self.reconnectButton.Enable(False)
        self.note.SetLabel('Please wait - connecting to server...')
        self.communicator.connectToServer(self.loginField.GetValue())

    def reconnectClicked(self, event):
        self.loginField.Enable(False)
        self.loginButton.Enable(False)
        self.reconnectButton.Enable(False)
        self.communicator.reconnectToServer()

    def postNetworkEvent(self, message):
        """ called by the Communicator when something happens """
        event = GameGUI.NetworkEvent(message=message)
        wx.PostEvent(self, event)

    def onNetworkEvent(self, event):
        message = event.message
        print "server said: " + str(message)

        if message['type'] == 'init' or message['type'] == 'reinit':
            self.startGUI(message)

        elif message['type'] == 'whoareyou':
            # Server sends this message asking for re-login after reconnection.
            # disconnectedClients is a list of tuples (id, name).
            disconnectedClients = message['disconnectedClients']
            choices = []
            for id, name in disconnectedClients:
                choices.append(name + ' (id ' + str(id) + ')')
            dlg = wx.SingleChoiceDialog(self,
                    'Please select your login name from the list.',
                    'Reconnect to Server', choices, wx.CHOICEDLG_STYLE)
            if dlg.ShowModal() == wx.ID_OK:
                selection = dlg.GetSelection()
                selectedID = disconnectedClients[selection][0]
                print 'selected id ' + str(selectedID)
                self.communicator.send({'type': 'relogin', 'id': selectedID})
            else:
                # FIXME  User pressed Cancel.  What does that mean?
                pass
            dlg.Destroy()

    def startGUI(self, initParams):
        className = initParams['GUIclass']
        moduleName = 'peet.client.gameinterfaces.' + className
        exec 'import ' + moduleName
        GUIclass = eval(moduleName + '.' + className)
        self.gameGUI = GUIclass(self.communicator, initParams)
        self.Unbind(GameGUI.EVT_NETWORK)
        self.gameGUI.sendReadyMessage()
        self.Destroy()
