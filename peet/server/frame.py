#!/usr/bin/env python

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

import os
import os.path
import sys
import getopt
import thread
import random
import time
import csv
from decimal import Decimal
import re
import json
import wx
import wx.lib.newevent

from peet.server import parameters
from peet.server.parameditors import TreeEditor
from peet.server import servernet
import peet.server.gamecontrollers
from peet.server.ClientData import ClientData
from peet.server.ClientStatusListCtrl import ClientStatusListCtrl
from peet.server import survey

# Custom wx events for network events (client connects, messages, etc.)
NetworkEvent, EVT_NETWORK = wx.lib.newevent.NewEvent()

class Frame(wx.Frame):
    def __init__(self,parent,id,title):
        wx.Frame.__init__(self,parent,wx.ID_ANY, title, size = (800,600))

        self.schema = None
        self.params = None
        self.filename = None
        self.paramsModified = False
        self.paramsReadOnly = False
        self.outputDir = None
        self.clients = []
        self.clientsLoggedIn = 0
        self.roundNum = 0

        self.chatEnabled = False
        self.chatHistory = []
        self.chatRowsWritten = 0
        self.chatFilter = None

        # Get the available control classes and put them into a dictionary
        # indexed by their name attributes.
        self.controlClassesByName = {}
        controlDir = os.path.join(os.path.dirname(__file__), 'gamecontrollers')
        filenames = os.listdir(controlDir)
        filenames.remove('__init__.py')
        filenames.remove('GameControl.py')
        for filename in filenames:
            if re.match('^.+Control\.py$', filename):
                controlClass = self.getControlClass(filename)
                self.controlClassesByName[controlClass.name] = controlClass

        borderSize = 6

        # In Windows, a Frame is dark gray, so we need a Panel inside the frame.
        self.panel = wx.Panel(self)
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(mainSizer)

        self.boxFont = self.GetFont()
        self.boxFont.SetWeight(wx.FONTWEIGHT_BOLD)
        self.boxFont.SetPointSize(int(1.25 * self.boxFont.GetPointSize()))

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self.panel, wx.ID_STATIC, "Game Type: ")
        label.SetFont(self.boxFont)
        hsizer.Add(label)
        self.gameChooser = wx.Choice(self.panel, wx.ID_ANY,\
                choices=['None Selected']\
                        + sorted(self.controlClassesByName.keys()))
        hsizer.Add(self.gameChooser)
        mainSizer.Add(hsizer, border=borderSize, flag=wx.ALL)

        self.Bind(wx.EVT_CHOICE, self.onGameSelected, self.gameChooser)

        # Experiment parameters box
        box = wx.StaticBox(self.panel, wx.ID_STATIC, "Parameters")
        box.SetFont(self.boxFont)
        bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        self.filenameText = wx.StaticText(self.panel, wx.ID_STATIC,
                                          "Parameter File: [No file]")
        bsizer.Add(self.filenameText)
        self.newButton = wx.Button(self.panel, wx.ID_ANY, "New")
        self.newButton.Enable(False)
        self.openButton = wx.Button(self.panel, wx.ID_ANY, "Open")
        self.openButton.Enable(False)
        self.editButton = wx.Button(self.panel, wx.ID_ANY, "Edit")
        self.editButton.Enable(False)
        self.outputDirButton = wx.Button(self.panel, wx.ID_ANY,
                                         "Choose output folder")
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.newButton)
        hbox.Add(self.openButton)
        hbox.Add(self.editButton)
        hbox.AddSpacer(30)
        hbox.Add(self.outputDirButton)
        bsizer.Add(hbox)
        self.outputDirText = wx.StaticText(self.panel, wx.ID_STATIC,
                                           "Output Folder: [None]")
        bsizer.Add(self.outputDirText)
        mainSizer.Add(bsizer, 0, flag=wx.EXPAND|wx.ALL, border=borderSize)
        self.Bind(wx.EVT_BUTTON, self.onNewClicked, self.newButton)
        self.Bind(wx.EVT_BUTTON, self.onOpenClicked, self.openButton)
        self.Bind(wx.EVT_BUTTON, self.onEditClicked, self.editButton)
        self.Bind(wx.EVT_BUTTON, self.onOutputDirClicked, self.outputDirButton)

        # Experiment controls box
        box = wx.StaticBox(self.panel, wx.ID_STATIC, "Controls")
        box.SetFont(self.boxFont)
        bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        self.connectButton = wx.Button(self.panel, label="Connect to Clients")
        self.connectButton.Enable(False)
        self.connectButton.SetToolTipString(
                "Please set parameters and output folder first.")
        self.startButton = wx.Button(self.panel, label="Start")
        self.startButton.Enable(False)
        #msgButton = wx.Button(self.panel, label="Send message")
        self.nextRoundButton = wx.Button(self.panel, label="Next Round")
        self.pauseButton = wx.Button(self.panel, wx.ID_ANY, "Pause")
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.connectButton)
        #hbox.Add(msgButton)
        hbox.Add(self.startButton)
        hbox.Add(self.nextRoundButton)
        hbox.Add(self.pauseButton)
        #hbox.Add(self.writeButton)
        self.nextRoundButton.Enable(False)
        bsizer.Add(hbox)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.autoAdvanceRoundCheckBox = wx.CheckBox(self.panel, wx.ID_ANY,
                                                    "Auto-advance rounds")
        hbox.Add(self.autoAdvanceRoundCheckBox)
        bsizer.Add(hbox)
        mainSizer.Add(bsizer, 0, flag=wx.EXPAND|wx.ALL, border=borderSize)
        self.Bind(wx.EVT_BUTTON, self.onConnectClicked, self.connectButton)
        #self.Bind(wx.EVT_BUTTON, self.onMsgClicked, msgButton)
        self.Bind(wx.EVT_BUTTON, self.onStartClicked, self.startButton)
        self.Bind(wx.EVT_BUTTON, self.onNextRoundClicked, self.nextRoundButton)
        self.Bind(wx.EVT_BUTTON, self.onPauseClicked, self.pauseButton)
        #self.Bind(wx.EVT_BUTTON, self.onWriteClicked, self.writeButton)

        # Status box
        box = wx.StaticBox(self.panel, wx.ID_STATIC, "Status")
        box.SetFont(self.boxFont)
        bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        self.roundLabel = wx.StaticText(self.panel, wx.ID_STATIC,
                                            "Round -")
        bsizer.Add(self.roundLabel)
        self.listCtrl = ClientStatusListCtrl(self.panel, wx.ID_ANY,
                                             style=wx.LC_REPORT)
        bsizer.Add(self.listCtrl, 1, wx.EXPAND)
        mainSizer.Add(bsizer, 1, flag=wx.EXPAND|wx.ALL, border=borderSize)

        # Message box
        box = wx.StaticBox(self.panel, wx.ID_STATIC, "Messages")
        box.SetFont(self.boxFont)
        bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        self.messageBox = wx.TextCtrl(self.panel, #size=(400,300),
            style=wx.TE_MULTILINE|wx.TE_RICH2)
        bsizer.Add(self.messageBox, 1, wx.EXPAND)
        mainSizer.Add(bsizer, 1, flag=wx.EXPAND|wx.ALL, border=borderSize)

        # Set up networking
        self.communicator = servernet.Communicator(
                port = 9123,
                postEvent = self.postNetworkEvent)
        self.Bind(EVT_NETWORK, self.onNetworkEvent)

        # Get command line options
        self.autostart = False
        try:
            opts, args = getopt.getopt(sys.argv[1:], "g:p:o:a",
                    ["game=", "paramfile=", "outdir=", "autostart"])
        except getopt.GetoptError, err:
            # print help information and exit:
            print str(err)
            self.usage()
            sys.exit(2)
        for o, a in opts:
            if o in ('-g', '--game'):
                className = a + 'Control'
                for k, v in self.controlClassesByName.iteritems():
                    if v.__name__ == className:
                        self.setControlClass(v)
                        self.gameChooser.SetStringSelection(k)
                        break
            elif o in ('-p', '--paramfile'):
                filename = os.path.abspath(a)
                self.setParams(json.load(open(filename)), filename)
            elif o in ('-o', '--outdir'):
                self.outputDir = os.path.abspath(a)
                self.outputDirText.SetLabel("Output Folder: " + self.outputDir)
                if self.params != None:
                    self.connectButton.Enable(True)
            elif o in ('-a', '--autostart'):
                self.autostart = True
                if self.outputDir != None and self.params != None:
                    self.connectButton.Enable(True)
                    self.onConnectClicked(None)

            # FIXME: may not work properly if args are given out of order (e.g.
            # the test above in --autostart, if --autostart appears before
            # --paramfile and --outdir)

        self.Bind(wx.EVT_CLOSE, self.onClose)

        self.Show(True)

    def usage(self):
        print """
            Command line options:
                --game, -g <game>  where <game> is the game class prefix
                --paramfile, -p <filename>
                --outdir, -o <directory name>
                --autostart, -a  Automatically connect and start game
        """

    def onClose(self, event):
        print 'onClose'
        dlg = wx.MessageDialog(self, 'Are you sure you want to quit?',\
                'Confirm Quit', wx.YES_NO|wx.ICON_QUESTION)
        if dlg.ShowModal() == wx.ID_YES:
            event.Skip()
        dlg.Destroy()

    def postNetworkEvent(self, clientConn, message):
        """ called by the Communicator when something happens """
        event = NetworkEvent(clientConn=clientConn, message=message)
        wx.PostEvent(self, event)

    def onNetworkEvent(self, event):
        #print "onNetworkEvent"
        clientConn = event.clientConn
        message = event.message
        if clientConn != None and message['type'] != 'ping':
            print 'client ', clientConn.id+1, ': ', message
        #if clientConn != None:
        #    self.postMessage("Received message from client " +
        #            str(clientConn.id) + ": " + str(message))

        if message['type'] == 'connect':
            self.postMessage("Client " + str(clientConn.id+1) + " connected")
            client = ClientData(clientConn.id, '', 'Connected', Decimal('0.00'),
                    clientConn)
            client.setRounding(self.rounding)
            self.clients[clientConn.id] = client
            self.listCtrl.updateClient(client)

        elif message['type'] == 'all connected':
            self.postMessage("All clients connected.")
            # But not necessarily logged in...

        elif message['type'] == 'login':

            # Ignore login message if all clients already logged in
            # (it's probably from a disconnected client that clicked 'Log In'
            # by mistake instead of Reconnect)
            if self.clientsLoggedIn < len(self.clients):

                client = self.clients[clientConn.id]
                client.name = message['name']
                self.listCtrl.updateClient(client)
                self.clientsLoggedIn += 1
                if self.clientsLoggedIn == len(self.clients):
                    print 'All clients logged in.'
                    self.postMessage("All clients logged in.")
                    self.startButton.Enable(True)
                    if self.autostart:
                        self.onStartClicked(None)

        elif message['type'] == 'ready':
            # Message from client that GUI has been created and is ready for the
            # game to begin (or resume, in the case of a reconnected client)

            if not self.gameController.running:
                # This is an initial ready message
                print 'initial ready message'
                self.gameController.clientReady(clientConn)

            else:
                # This is a ready message from a reconnecting client.
                # If there are no more clients who are still disconnected,
                # enable the unpause button.

                clientsStillDisconnected = False
                for c in self.clients:
                    if c.status == 'Disconnected':
                        clientsStillDisconnected = True
                        break
                if not clientsStillDisconnected:
                    self.pauseButton.Enable()

        elif message['type'] == 'chat':
            if self.chatEnabled:
                self.forwardChatMessage(clientConn, message)

                # Append to chat history for chat output file
                client = self.clients[clientConn.id]
                if client.group == None:
                    groupID = ''
                else:
                    groupID = str(client.group.id + 1)
                row = [self.sessionID, self.experimentID,\
                        self.roundNum+1, clientConn.id+1, groupID,
                        message['message']]
                self.chatHistory.append(row)

        elif message['type'] == 'disconnect':
            # Pause and don't allow unpausing until client has reconnected
            self.pauseButton.Enable(False)
            self.communicator.pause()
            self.pauseClients()
            self.pauseButton.SetLabel("Unpause")
            client = self.clients[clientConn.id]
            client.status = 'Disconnected'
            self.listCtrl.updateClient(client)
            self.communicator.reconnectToClients(1)

            errorstring = "A client has disconnected."
            dlg = wx.MessageDialog(self, errorstring,
                    'Client Disconnected', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()

        elif message['type'] == 'reconnect':
            self.promptRelogin(clientConn)
            
        elif message['type'] == 'relogin':
            # Reconnecting client's response to 'whoareyou'.
            # Check for valid selection
            id = message['id']
            if self.clients[id].status == 'Disconnected':
                # OK, reconnect client with selected ID
                clientConn.id = id
                client = self.clients[id]
                client.connection = clientConn
                client.status = 'Connected'
                self.listCtrl.updateClient(client)
                self.gameController.reinitClient(client)
            else:
                # Selected client is not disconnected, so as 'whoareyou' again.
                self.promptRelogin(clientConn)

    def enableChat(self, enable=True, chatFilter=None):
        """ Enable forwarding of chat messages.  The chatFilter parameter sets
        the function that determines to whom a chat message will be forwarded.
        If set to None (default), chat messages are forwarded to everyone in the
        group.  Otherwise, it should be set to a function with two arguments of
        type ClientData (first is source S, second is destination D) that
        returns True if a message from S should be forwarded to D, and False if
        the it should not. """
        self.chatEnabled = enable
        self.chatFilter = chatFilter

    def forwardChatMessage(self, clientConn, message):
        message['id'] = clientConn.id
        client = self.clients[clientConn.id]

        # if the client is in a group, then only forward the message to other
        # clients in the group
        if client.group != None:
            clients = client.group.clients
        else:
            clients = self.clients

        for c in clients:
            if c.id != client.id and (self.chatFilter == None or
                    self.chatFilter(client, c)):
                self.communicator.send(c.connection, message)

    def promptRelogin(self, clientConn):
        # Called when a disconnected client reconnects.
        # Send the client a list of disconnected clients in the form of a
        # list of tuples in the form (id, name).  Client will reply with ID
        # of the one they want to reconnect as (message type 'relogin').
        disconnectedClients = []
        for client in self.clients:
            if client.status == 'Disconnected':
                disconnectedClients.append((client.id, client.name))
        self.communicator.send(clientConn, {'type': 'whoareyou',
            'disconnectedClients': disconnectedClients})

    def setControlClass(self, controlClass):
        """ Set the controller class to the given class and try to load the
        associated schema, enabling the parameter buttons if successful. """
        if controlClass == None:
            self.schema = None
            enableParamButtons = False
        else:
            self.controlClass = controlClass
            if not self.loadSchema():
                self.controlClass = None
                enableParamButtons = False
            else:
                enableParamButtons = True

        # Only enable the parameter buttons if a valid game type is selected;
        # otherwise, we don't know what parameter schema to load.
        self.newButton.Enable(enableParamButtons)
        self.openButton.Enable(enableParamButtons)
        self.editButton.Enable(enableParamButtons)

    def onGameSelected(self, event):
        """ Called when a game type is selected from the wx.Choice menu. """
        if self.gameChooser.GetSelection() == 0:
            self.setControlClass(None)
        else:
            self.setControlClass(self.controlClassesByName[event.GetString()])

    def onNewClicked(self, event):
        editor = TreeEditor.TreeEditor(self, self.schema)
        if editor.ShowModal() == parameters.KEEP:
            #print 'keep'
            self.setParams(editor.getParams(), editor.getFilename(),
                    editor.getModified())
        else:
            #print 'discard'
            pass
        editor.Destroy()

    def onOpenClicked(self, event):
        dlg = wx.FileDialog(self, message="Open Parameter File", style=wx.OPEN,\
                wildcard=parameters.fileDlgWildcard,\
                defaultDir=parameters.defaultDir)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
            self.setParams(json.load(open(filename)), filename)
            # FIXME handle file errors
        dlg.Destroy()
        
    def onEditClicked(self, event):
        editor = TreeEditor.TreeEditor(self, self.schema, self.params,\
                self.filename, readonly=self.paramsReadOnly)
        if editor.ShowModal() == parameters.KEEP and not self.paramsReadOnly:
            #print 'keep'
            self.setParams(editor.getParams(), editor.getFilename(),
                    editor.getModified())
        else:
            #print 'discard'
            pass
        editor.Destroy()

    def onOutputDirClicked(self, event):
        # get output directory
        if self.outputDir == None:
            defaultDir = os.path.join(os.path.dirname(__file__), 'output')
        else:
            defaultDir = self.outputDir
        dlg = wx.DirDialog(self, "Choose a folder for output files",\
                defaultPath=defaultDir)
        if dlg.ShowModal() == wx.ID_OK:
            self.outputDir = dlg.GetPath()
            self.outputDirText.SetLabel("Output Folder: " + self.outputDir)
            if self.params != None:
                self.connectButton.Enable(True)

        dlg.Destroy()

    def onConnectClicked(self, event):

        # instantiate the game controller
        self.gameController = self.controlClass(self)

        # get the required server parameters from the controller
        self.numPlayers = self.gameController.getNumPlayers()
        self.rounding = self.gameController.getRounding()
        self.experimentID = self.gameController.getExperimentID()
        self.showUpPayment = self.gameController.getShowUpPayment()
        self.listCtrl.setShowUpPayment(self.showUpPayment)
        self.surveyFile = self.gameController.getSurveyFile()

        # Check that survey file exists
        if self.surveyFile != None and not os.path.exists(f):
            errorstring = "Can't read the survey file specified in the\n"\
                          "parameters.  Please check it and try again."
            dlg = wx.MessageDialog(self, errorstring,
                    'Error', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return

        self.connectButton.Enable(False)

        # Disable buttons that are no longer applicable and could screw it up
        self.newButton.Enable(False)
        self.openButton.Enable(False)
        self.editButton.SetLabel('View')
        self.paramsReadOnly = True
        self.outputDirButton.Enable(False)

        # send out the message & wait for responses
        self.clients = [None for i in range(self.numPlayers)]
        self.listCtrl.makeRows(self.numPlayers)
        self.communicator.connectToClients(self.numPlayers)

    def onMsgClicked(self, event):
        for c in self.clients:
            mes = {'type': 'message'}

            # For testing large messages
            #mstring = 'BEGIN---'
            #mlength = random.randint(5000, 10000)
            #for i in range(mlength):
            #    mstring += 'a'
            #mstring += '---END'
            #mes['message'] = mstring

            mes['message'] = "Hi, client " + str(c.id + 1)
            self.communicator.send(c.connection, mes)

    def onStartClicked(self, event):

        # Generate a unique identifier for this session, based on current time
        # to the second.  A string.
        self.sessionID = time.strftime('%y%m%d%H%M%S', time.localtime())
        self.postMessage('Session ID = ' + self.sessionID)

        # Attempt to write the parameters to the output folder.  This doubles as
        # a check to make sure the output directory is writable; if it's not,
        # refuse to start, and display an error message.
        #
        # Also, write the headers to the chat output file.
        try:
            if self.filename == None:
                fname = 'parameters.json'
            else:
                fname = os.path.basename(self.filename)
            fname = self.sessionID + '-' + fname
            outfile = open(os.path.join(self.outputDir, fname), 'w')
            json.dump(self.params, outfile, sort_keys=True, indent=4)
            outfile.close()

            # set up chat output file
            fname = self.sessionID + '-chat.csv'
            outfile = open(os.path.join(self.outputDir, fname), 'wb')
            csvwriter = csv.writer(outfile)
            headers = ['sessionID', 'experimentID',\
                'round', 'subject', 'group', 'chatmessage']
            csvwriter.writerow(headers)
            outfile.close()

        except:
            print str(sys.exc_info()[1])
            errorstring = "The selected output folder is not writable.  " +\
                    "Please select a different folder."
            dlg = wx.MessageDialog(self, errorstring,
                    'Error: Invalid output folder', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()

            return

        self.startButton.Enable(False)
        self.gameController.start(self.clients, self.sessionID)
        self.roundLabel.SetLabel("Round 0")

    def getControlClass(self, filename):
        """ Given the filename of a game controller return its class object. """
        # Tricky stuff to instantiate the class from the string containing its
        # name.
        className = re.sub('\.py', '', filename)
        moduleName = 'peet.server.gamecontrollers.' + className
        exec 'import ' + moduleName
        # FIXME security hole - need to validate className first
        controlClass = eval(moduleName + '.' + className)
        return controlClass

    def loadSchema(self):
        """ Assuming self.controClass is set to a valid controller class, load
        the associated schema file into self.schema.  The schema file is assumed
        to be in the server/schemata directory and be called
        <prefix>Schema.json, where <prefix> is the part of the controller class
        name without the "Control" part.
        @return True if successful, False if unsuccessful """
        filename = os.path.join(os.path.dirname(__file__), 'schemata',\
                re.sub('Control$', '', self.controlClass.__name__)\
                + 'Schema.json')
        try:
            schemaFile = open(filename)
            self.schema = json.load(schemaFile)
            schemaFile.close()
        except:
            errorstring = "Error loading parameter schema: "\
                    + str(sys.exc_info()[1])
            dlg = wx.MessageDialog(self, errorstring,
                    'Error Loading Schema', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return False

        return True

    def getParams(self):
        return self.params

    def setParams(self, params, filename=None, modified=False):
        self.params = params
        self.filename = filename
        self.paramsModified = modified
        if modified:
            mtext = ' *modified* '
        else:
            mtext = ''
        if self.filename == None:
            self.filenameText.SetLabel("Parameter File: " + mtext + "[No file]")
        else:
            dname, fname = os.path.split(self.filename)
            self.filenameText.SetLabel("File: " + mtext + fname + " (" + dname
                    + ")")

        if self.outputDir != None:
            self.connectButton.Enable(True)

    def getCommunicator(self):
        return self.communicator

    def getOutputDir(self):
        return self.outputDir

    def getSessionID(self):
        return self.sessionID

    def postMessage(self, str):
        """ wx.CallAfter makes this safe to call from a different thread (i.e.
        the GameControl thread) """
        wx.CallAfter(self.messageBox.AppendText, str+'\n')

    def updateRound(self, roundNum):
        """ Called by the controller to inform server of current round """
        self.roundNum = roundNum
        wx.CallAfter(self.roundLabel.SetLabel, 'Round ' + str(roundNum+1))

    def roundFinished(self, gameFinished=False):
        """ Called by the controller to inform the server that the round has
        finished.  Controller will wait until server calls
        controller.nextRound(). """
        self.postMessage("Round complete")

        # Back up existing client status file
        statusFilename = os.path.join(self.outputDir,\
                self.sessionID + '-status.csv')
        try:
            os.remove(statusFilename + '.backup')
        except:
            print "Couldn't remove old backup status file"

        try:
            os.rename(statusFilename, statusFilename + '.backup')
        except:
            print "Couldn't back up status file."
            print "  (maybe just because it doesn't exist yet)"
            print sys.exc_info()[0]

        # Write client status file
        try:
            statusFile = open(statusFilename, 'wb')
            csvwriter = csv.writer(statusFile)
            headerRow = ['Round', 'ID', 'IP Address', 'Name',\
                    'Status', 'Game Earnings ($)',\
                    'Rounded Earnings ($)',\
                    'Show-up Payment ($)',\
                    'Total Earnings ($)']
            csvwriter.writerow(headerRow)
            for c in self.clients:

                roundedEarnings = c.getRoundedEarnings()
                totalEarnings = roundedEarnings + self.showUpPayment

                row = [str(self.roundNum+1),\
                        str(c.id+1), c.connection.address[0],\
                        c.name, c.status, str(c.earnings),\
                        str(roundedEarnings),\
                        str(self.showUpPayment),\
                        str(totalEarnings)]
                print "writing row to status file"
                csvwriter.writerow(row)

            statusFile.close()
                
        except:
            print 'Failed to write status file'
            print sys.exc_info()

        # Write chat history
        # FIXME back up first
        try:
            fname = self.sessionID + '-chat.csv'
            file = open(os.path.join(self.outputDir, fname), 'ab')
            csvwriter = csv.writer(file)
            csvwriter.writerows(self.chatHistory[self.chatRowsWritten:])
            self.chatRowsWritten = len(self.chatHistory)
            file.close()
        except:
            print 'Failed to write chat file'
            print sys.exc_info()[0]

        # Start survey (starts in new thread)
        if gameFinished and self.surveyFile != None:
            self.postMessage('Starting survey')
            survey.start(self, self.sessionID,\
                    self.experimentID,\
                    self.outputDir, self.surveyFile,\
                    len(self.clients))

        def run():
            self.listCtrl.updateClients(self.gameController.clients)
            if gameFinished:
                return
            self.nextRoundButton.Enable(True)
            autoNextRound = self.autoAdvanceRoundCheckBox.GetValue()
            if autoNextRound:
                self.onNextRoundClicked(None)

        wx.CallAfter(run)

    def onNextRoundClicked(self, event):
        self.nextRoundButton.SetLabel('Next Round')
        self.nextRoundButton.Enable(False)
        self.gameController.nextRound()

    def onPauseClicked(self, event):
        if self.communicator.paused:
            self.communicator.unpause()
            self.gameController.onUnpause()
            self.pauseButton.SetLabel("Pause")
        else:
            self.communicator.pause()
            self.pauseClients()
            self.pauseButton.SetLabel("Unpause")
    
    def pauseClients(self):
        """ Send a pause message to the clients.  It's up to the particular
        GameGUI what to do with the message. """
        for c in self.clients:
            self.communicator.send(c.connection, {'type': 'pause'})

    def updateClientStatus(self, client):
        """ The game controller can call this after a client's status changes to
        update the client status list in the server window. """

        def run():
            self.listCtrl.updateClient(client)
        wx.CallAfter(run)

