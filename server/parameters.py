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

"""
This module contains classes and functions for game parameter loading, editing, and saving.
"""

import os.path
import ConfigParser
import re
import wx
import  wx.lib.scrolledpanel as scrolled
import gamecontrollers
from gamecontrollers import *
from shared.widgets import FloatSpin
from shared.constants import roundingOptions

# Constants
KEEP = 1 # Normally returned by ParamEditor.ShowModal() 
DISCARD = 2  # Returned by ParamEditor.ShowModal() if user discards changes

fileDlgWildcard = "*.ini|*.ini|"\
                    "All files|*"



def getParamsFromFile_old(filename):
    """
    Read experiment parameters from the given file.
    The file should contain a Python dictionary representing the params (in
    Python syntax).
    Return as a dictionary.
    """
    try:
        file = open(filename, 'r')
    except IOError:
        # FIXME do something useful here
        print 'IOError'
        raise
    else:
        data = file.read()
        file.close()
        # get rid of line breaks, in case they might mess things up
        data = data.replace('\r\n', ' ')
        data = data.replace('\r', ' ')
        data = data.replace('\n', ' ')
        params = dict(eval(data))
            # FIXME could this lead to arbitrary code execution?
            ### YES: the file would just need to contain an expression that
            # was a function call.

        # Trim off the Control part of the gametype
        params['gametype'] = re.sub('Control$', '', params['gametype'])

        return params

def getParamsFromFile(filename):
    """
    Read experiment parameters from the given file.
    The file should be a INI-type configuration file readable by ConfigParser.
    Return as a dictionary.
    """
    
    # Check for old format parameter file (dictionary syntax)
    # FIXME: REMOVE THIS PRETTY SOON
    try:
        file = open(filename, 'r')
    except IOError:
        # FIXME do something useful here
        print 'IOError'
        raise
    if file.read(1) == '{':
        file.close()
        print 'Warning: opening old format parameter file (insecure)'
        return getParamsFromFile_old(filename)
    file.close()

    #print 'getParamsFromFile(): opening ini-format file'

    cp = ConfigParser.SafeConfigParser()
    cp.optionxform = str  # to preserve case in option names

    # Set default values (to avoid getting a NoOptionError if paramfile is
    # incomplete)
    s = 'Experiment'
    cp.add_section(s)
    cp.set(s, 'gametype', 'Test')
    cp.set(s, 'notes', '')
    cp.set(s, 'experimentID', '')
    cp.set(s, 'surveyFile', '')
    cp.set(s, 'numPlayers', '1')
    cp.set(s, 'showUpPayment', '0')
    cp.set(s, 'rounding', '0')

    # Read the
    cp.read([filename])

    params = {}
    secname = 'Experiment'
    for paramname in ['gametype', 'notes', 'experimentID', 'surveyFile']:
        params[paramname] = cp.get(secname, paramname)
    params['numPlayers'] = cp.getint(secname, 'numPlayers')
    params['showUpPayment'] = cp.getfloat(secname, 'showUpPayment')
    params['rounding'] = cp.getint(secname, 'rounding')

    params['matches'] = []
    m = 0
    secname = 'Match ' + str(m + 1)
    while cp.has_section(secname):
        match = {}
        match['description'] = cp.get(secname, 'description')
        match['practice'] = cp.getboolean(secname, 'practice')
        match['numRounds'] = cp.getint(secname, 'numRounds')
        match['exchangeRate'] = cp.getfloat(secname, 'exchangeRate')
        secname += ' Custom'
        match['customParams'] = dict(cp.items(secname))
        params['matches'].append(match)
        m += 1
        secname = 'Match ' + str(m + 1)

    #print 'getParamsFromFile(): ', params

    return params

def saveParamsToFile(params, filename):
    """ Given a dictionary of parameters and a filename, save the parameters in
    INI format to the file.  Unfortunately, the sections won't necessarily be in
    logical order, because of ConfigParser's implementation which uses Python
    dictionaries.
    """

    try:
        file = open(filename, 'w')
    except IOError:
        # FIXME do something useful here
        print 'IOError'
        raise
    
    cp = ConfigParser.SafeConfigParser()
    cp.optionxform = str  # to preserve case in option names

    # Experiment parameters
    cp.add_section('Experiment')
    for paramname in ['gametype', 'notes', 'numPlayers', 'experimentID',\
            'surveyFile', 'showUpPayment', 'rounding']:
        cp.set('Experiment', paramname, str(params[paramname]))

    # Match parameters
    for m, match in enumerate(params['matches']):

        # generic match parameters
        secname = 'Match ' + str(m + 1)
        cp.add_section(secname)
        for paramname in ['description', 'practice', 'numRounds',\
                'exchangeRate']:
            cp.set(secname, paramname, str(match[paramname]))

        # game-specific match parameters
        secname += ' Custom'
        cp.add_section(secname)
        for paramname, paramvalue in match['customParams'].iteritems():
            cp.set(secname, paramname, str(paramvalue))

    cp.write(file)
    file.close()


class ParamEditor(wx.Dialog):
    def __init__(self, parent, params=None, filename=None, readonly=False):
        wx.Dialog.__init__(self, parent, title="", size=(400,700),\
                style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        self.modified = False
        self.readonly = readonly

        sizerFlags = wx.SizerFlags(0).Border(wx.ALL, 4)

        # This holds the filename label and the innerSizer
        outerSizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(outerSizer)

        self.filenameLabel = wx.StaticText(self, label = "File:")
        outerSizer.AddF(self.filenameLabel, sizerFlags)

        # This holds the leftBoxSizer and the rightBoxSizer
        innerSizer = wx.BoxSizer(wx.HORIZONTAL)

        # holds experiment-level parameters
        leftBoxSizer = wx.BoxSizer(wx.VERTICAL)

        # holds match-level parameters
        rightBoxSizer = wx.BoxSizer(wx.VERTICAL)


        self.gameClassNames = gamecontrollers.__all__
        self.gameNames = []
        self.gameClassLookup = {}  # a table we'll need later
        for className in self.gameClassNames:
            gameName = eval(className + '.' + className).name
            self.gameNames.append(gameName)
            self.gameClassLookup[gameName] = className
        self.gameNames.sort()


        # Buttons for file operations
        newButton = wx.Button(self,-1,"New")
        openButton = wx.Button(self,-1,"Open")
        saveButton = wx.Button(self,-1,"Save")
        saveAsButton = wx.Button(self,-1,"Save As...")
        saveAndCloseButton = wx.Button(self,-1,"Save and Close")
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(newButton)
        hbox.Add(openButton)
        hbox.Add(saveButton)
        hbox.Add(saveAsButton)
        hbox.Add(saveAndCloseButton)
        leftBoxSizer.AddF(hbox, sizerFlags)
        self.Bind(wx.EVT_BUTTON, self.onNewClicked, newButton)
        self.Bind(wx.EVT_BUTTON, self.onOpenClicked, openButton)
        self.Bind(wx.EVT_BUTTON, self.onSaveClicked, saveButton)
        self.Bind(wx.EVT_BUTTON, self.onSaveAsClicked, saveAsButton)
        self.Bind(wx.EVT_BUTTON, self.onSaveAndCloseClicked, saveAndCloseButton)

        # Game type selection
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.AddF(wx.StaticText(self, label = "Game Type"), sizerFlags)
        self.choiceBox = wx.Choice(self, choices=self.gameNames)
        hbox.AddF(self.choiceBox, sizerFlags)
        leftBoxSizer.AddF(hbox, sizerFlags)
        self.Bind(wx.EVT_CHOICE, self.onGameSelected, self.choiceBox)
        self.choiceBoxSelection = self.choiceBox.GetSelection()

        # Notes box
        leftBoxSizer.AddF(wx.StaticText(self, label="Notes"), sizerFlags)
        self.notes = wx.TextCtrl(self, size=(400,100), style=wx.TE_MULTILINE)
        leftBoxSizer.AddF(self.notes, sizerFlags)

        # Number of players
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.AddF(wx.StaticText(self, label="Number of Players: "), sizerFlags)
        self.numPlayersSpinner = wx.SpinCtrl(self, min=1, initial=1)
        hbox.AddF(self.numPlayersSpinner, sizerFlags)

        # Experiment ID (arbitrary string)
        expIDlabel = wx.StaticText(self, label="Experiment ID: ")
        expIDtip = "A short identifier for this experiment/treatment\n"\
                "that will be written to the output file."
        expIDlabel.SetToolTipString(expIDtip)
        hbox.AddF(expIDlabel, sizerFlags)
        self.experimentID = wx.TextCtrl(self)
        self.experimentID.SetToolTipString(expIDtip)
        hbox.AddF(self.experimentID, sizerFlags)
        leftBoxSizer.AddF(hbox, sizerFlags)

        # Show-up payment
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.AddF(wx.StaticText(self, label="Show-up Payment: "), sizerFlags)
        self.showUpPaymentSpinner = FloatSpin.FloatSpin(self, min_val=0,\
                increment=0.25, digits=2, extrastyle=FloatSpin.FS_RIGHT)
        hbox.AddF(self.showUpPaymentSpinner, sizerFlags)
        leftBoxSizer.AddF(hbox, sizerFlags)

        # Round total earnings
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.AddF(wx.StaticText(self, label="Round Total Earnings:"),\
                sizerFlags)
        self.roundingChoice = wx.Choice(self, choices=roundingOptions)
        hbox.AddF(self.roundingChoice, sizerFlags)
        leftBoxSizer.AddF(hbox, sizerFlags)

        # Survey file
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.AddF(wx.StaticText(self, label="Survey File: "), sizerFlags)
        self.surveyFile = wx.TextCtrl(self, size=(300, -1))
        hbox.AddF(self.surveyFile, sizerFlags)
        surveyFileButton = wx.Button(self,-1,"Choose")
        hbox.AddF(surveyFileButton, sizerFlags)
        self.Bind(wx.EVT_BUTTON, self.onSurveyFileClicked, surveyFileButton)
        leftBoxSizer.AddF(hbox, sizerFlags)

        innerSizer.Add(leftBoxSizer)

        self.newMatchButton = wx.Button(self, label="New Match")
        rightBoxSizer.AddF(self.newMatchButton, sizerFlags)
        self.Bind(wx.EVT_BUTTON, self.onNewMatchClicked, self.newMatchButton)
    
        self.matchbook = MatchBook(self)
        rightBoxSizer.Add(self.matchbook, proportion=2, flag=wx.ALL|wx.EXPAND,\
                border=4)

        innerSizer.Add(rightBoxSizer, proportion=2, flag=wx.EXPAND)

        outerSizer.Add(innerSizer, proportion=2, flag=wx.EXPAND)

        #innerSizer.Fit(self)

        # If parameters were given, populate the editor fields with them
        if params != {} and params != None:
            self.setParams(params)
        else:
            # Otherwise, add one blank match page
            self.matchbook.addMatch(self.getGameClass())

        self.modified = False
        self.setFilename(filename)

        # Disable controls when in read-only mode
        if self.readonly:
            for control in [newButton, openButton, saveButton, saveAsButton,\
                    self.choiceBox, self.notes, self.numPlayersSpinner,\
                    self.experimentID, self.surveyFile, self.newMatchButton]:
                control.Enable(False)
                control.SetForegroundColour('BLUE') # FIXME - doesn't work

        self.Fit()
        self.Center(wx.BOTH)

        # Catch any events that come from controls that indicate a value has
        # changed, so we know the parameters have been modified.
        self.Bind(wx.EVT_TEXT, self.onValueChanged)
        self.Bind(wx.EVT_SPIN, self.onValueChanged)
        self.Bind(wx.EVT_CHECKBOX, self.onValueChanged)

        self.Bind(wx.EVT_CLOSE, self.onClose)
    
    def onClose(self, event):
        #print 'onClose'

        class ConfirmCloseDlg(wx.Dialog):
            def __init__(self, parent):
                wx.Dialog.__init__(self, parent, title='Save Changes?')
                padding=12
                vsizer = wx.BoxSizer(wx.VERTICAL)
                self.SetSizer(vsizer)
                text = wx.StaticText(self, label=\
                    "Save the changes to the parameter file before closing?"\
                    + "\nIf you don't save, your changes will be lost.")
                vsizer.Add(text, flag=wx.ALL, border=padding)
                hsizer = wx.BoxSizer(wx.HORIZONTAL)
                discardButton = wx.Button(self, label="Discard Changes")
                hsizer.Add(discardButton, flag=wx.ALL, border=padding)
                cancelButton = wx.Button(self, label="Cancel")
                hsizer.Add(cancelButton, flag=wx.ALL, border=padding)
                saveButton = wx.Button(self, label="Save As...")
                hsizer.Add(saveButton, flag=wx.ALL, border=padding)
                vsizer.Add(hsizer)
                self.Fit()
                self.Bind(wx.EVT_BUTTON, self.onDiscardClicked, discardButton)
                self.Bind(wx.EVT_BUTTON, self.onCancelClicked, cancelButton)
                self.Bind(wx.EVT_BUTTON, self.onSaveClicked, saveButton)

            def onDiscardClicked(self, event):
                self.EndModal(1)

            def onCancelClicked(self, event):
                self.EndModal(2)

            def onSaveClicked(self, event):
                self.EndModal(3)

        if self.modified:
            dlg = ConfirmCloseDlg(self)
            val = dlg.ShowModal()
            dlg.Destroy()
            if val == 1:
                # event.Skip() does not work if dialog is presented.
                self.EndModal(DISCARD)  # (Discard) Allow window to close
            elif val == 2:
                return  # (Cancel) Don't allow window to close
            elif val == 3:  # (Save)
                # pass the string 'closing' in place of what would normally be
                # a click event, so the saveAs function knows to close the
                # window after the file has been saved.
                self.onSaveAsClicked('closing')
            else:
                #print 'val==%d' % val
                return  # (dlg was closed or something)
                        # Don't allow window to close

        else:
            self.EndModal(KEEP)

    def onValueChanged(self, event):
        self.setModified()

    def getParams(self):
        """
        Gather the parameter values from GUI elements and return them as a
        dictionary.
        """
        #print 'getParams'
        params = {}
        gameName = self.gameNames[self.choiceBox.GetSelection()]
        #print '  gameName = ' + gameName
        className = self.gameClassLookup[gameName]
        #print '  className = ' + className
        #gameClass = eval(className + '.' + className)
        params['gametype'] = re.sub('Control$', '', className)
        params['notes'] = self.notes.GetValue()
        params['numPlayers'] = self.numPlayersSpinner.GetValue()
        params['experimentID'] = self.experimentID.GetValue()
        params['showUpPayment'] = float(self.showUpPaymentSpinner.GetValue())
        params['rounding'] = self.roundingChoice.GetSelection()
        params['surveyFile'] = self.surveyFile.GetValue()
        matches = []
        for p in range(self.matchbook.GetPageCount()):
            page = self.matchbook.GetPage(p)
            matches.append(page.getMatchParams())
        params['matches'] = matches

        return params

    def setParams(self, params):
        """Populate GUI fields with the values from the given dictionary."""
        self.clear(addBlankMatch=False)
        className = params.get('gametype', 'Test') + 'Control'
        #print 'parameters.setParams(): className = ', className
        gameClass = eval(className + '.' + className) 
            # FIXME: above is security hole
        gameName = gameClass.name
        i = self.gameNames.index(gameName)
        self.choiceBox.SetSelection(i)
        self.notes.SetValue(params.get('notes',''))
        self.numPlayersSpinner.SetValue(params.get('numPlayers', 1))
        self.experimentID.SetValue(params.get('experimentID', ''))
        self.showUpPaymentSpinner.SetValue(params.get('showUpPayment', 0))
        self.roundingChoice.SetSelection(params.get('rounding', 0))
        self.surveyFile.SetValue(params.get('surveyFile', ''))
        for match in params.get('matches', []):
            self.matchbook.addMatch(gameClass, match)
        self.matchbook.SetSelection(0)

    def clear(self, addBlankMatch=True):
        """Clear the editor and put it in blank-document state."""
        self.setFilename(None)
        self.setModified(False)
        self.notes.SetValue('')
        self.numPlayersSpinner.SetValue(1)
        self.experimentID.SetValue('')
        self.surveyFile.SetValue('')
        self.matchbook.DeleteAllPages()
        if addBlankMatch:
            self.matchbook.addMatch(self.getGameClass())

    def getFilename(self):
        return self.filename

    def setFilename(self, filename):
        self.filename = filename
        if self.modified:
            modified = ' *modified* '
        else:
            modified = ''
        self.SetTitle("Parameter Editor: " + modified + self.getFilenameText())
        self.filenameLabel.SetLabel("File: " + self.getFilenameText())
        self.filenameLabel.SetToolTipString(self.getFilenameText())

    def getFilenameText(self):
        """Assuming self.filename contains the full-path filename, return
        formatted filename text."""
        if self.filename == None:
            filenametext = "[No file]"
        else:
            dname, fname = os.path.split(self.filename)
            filenametext = fname + " (" + dname + ")"
        return filenametext

    def onNewClicked(self, event):
        #print 'onNewClicked'
        if self.modified:
            text = "Parameters have been modified.  Discard changes?"
            dlg = wx.MessageDialog(self, text, 'Confirm',
                    wx.YES_NO | wx.ICON_INFORMATION)
            if dlg.ShowModal() == wx.ID_YES:
                #print 'Yes clicked'
                pass
            else:
                #print 'No clicked'
                return
            dlg.Destroy()
        self.clear()

    def onOpenClicked(self, event):
        #print 'onOpenClicked'

        if self.modified:
            text = "Parameters have been modified.  Discard changes?"
            dlg = wx.MessageDialog(self, text, 'Confirm',
                    wx.YES_NO | wx.ICON_INFORMATION)
            if dlg.ShowModal() == wx.ID_YES:
                #print 'Yes clicked'
                pass
            else:
                #print 'No clicked'
                return
            dlg.Destroy()

        defaultDir = os.path.join(os.path.dirname(__file__), 'paramfiles')
        dlg = wx.FileDialog(self, message="Open Parameter File", style=wx.OPEN,\
                wildcard=fileDlgWildcard, defaultDir=defaultDir)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
            try:
                params = getParamsFromFile(filename)
            except IOError:
                print 'IOError'
                # FIXME do something useful
            else:
                self.modified = False
                self.setParams(params)
                self.setFilename(filename)
        dlg.Destroy()

    def onSaveClicked(self, event):
        #print 'onSaveClicked'
        if self.filename == None:
            self.onSaveAsClicked(event)
        else:
            params = self.getParams()
            try:
                saveParamsToFile(params, self.filename)
                self.setModified(False)
            except:
                print 'Error saving parameter file' # FIXME do something useful

    def onSaveAndCloseClicked(self, event):
        self.onSaveClicked(None)
        self.onClose(None)

    def onSaveAsClicked(self, event):
        #print 'onSaveAsClicked'
        if self.filename == None:
            dname = os.path.join(os.path.dirname(__file__), 'paramfiles')
            fname = 'untitled.ini'
        else:
            dname, fname = os.path.split(self.filename)
        dlg = wx.FileDialog(self, message="Save As...", style=wx.SAVE,
                defaultDir=dname, defaultFile=fname, wildcard=fileDlgWildcard)
        val = dlg.ShowModal()

        if val != wx.ID_OK:
            # User cancelled
            dlg.Destroy()
            return

        filename = dlg.GetPath()
        # Automatically append the filename extension .ini if the file does
        # not have it.
        #print '************'
        #print filename
        if os.path.splitext(filename)[1] != '.ini':
                filename += '.ini'
        #print filename

        dlg.Destroy()

        if os.path.exists(filename):
            text = "Are you sure you want to overwrite existing file\n"
            text += filename + "\n?"
            dlg = wx.MessageDialog(self, text, 'Confirm Overwrite',
                                   wx.OK | wx.CANCEL | wx.ICON_INFORMATION)
            val = dlg.ShowModal()
            dlg.Destroy()
            if val != wx.ID_OK:
                # User cancelled
                return

        try:
            saveParamsToFile(self.getParams(), filename)
            self.setModified(False)
        except:
            print 'Error saving parameter file' # FIXME do something useful
        else:
            self.setFilename(filename)
            # File was successfully saved.  If this function was called from the
            # onClose() handler (i.e. user was closing window, was presented
            # with "Save Changes?" dialog, and clicked Save), then
            # event=='closing' and we close the parameter editor.
            if event=='closing':
                self.EndModal(KEEP)

    def onSurveyFileClicked(self, event):
        defaultDir = os.path.join(os.path.dirname(__file__), 'surveys')
        dlg = wx.FileDialog(self, message="Choose Survey File", style=wx.OPEN,\
                defaultDir=defaultDir)
        val = dlg.ShowModal()
        if val != wx.ID_OK:
            # User cancelled
            dlg.Destroy()
            return
        self.surveyFile.SetValue(dlg.GetPath())
        dlg.Destroy()

    def setModified(self, modified=True):
        if self.modified != modified:
            self.modified = modified
            if modified:
                mtext = ' *modified* '
            else:
                mtext = ''
            self.SetTitle("Parameter Editor: " + mtext +
                    self.getFilenameText())

    def onGameSelected(self, event):

        # don't do anything if the selection hasn't changed
        if self.choiceBox.GetSelection() == self.choiceBoxSelection:
            return

        text = str("Are you sure you want to change the game type?  " +
            "Any changes to the game-specific parameters will be lost.")
        dlg = wx.MessageDialog(self, text, 'Confirm Change',
                               wx.OK | wx.CANCEL | wx.ICON_INFORMATION)
        val = dlg.ShowModal()

        if val == wx.ID_OK:
            # Clear the custom parameter fields and then put in ones for the
            # selected game.
            self.choiceBoxSelection = self.choiceBox.GetSelection()
            for p in range(self.matchbook.GetPageCount()):
                page = self.matchbook.GetPage(p)
                # page is a MatchPage
                page.removeCustomParamFields()
                gameName = self.gameNames[self.choiceBoxSelection]
                className = self.gameClassLookup[gameName]
                gameClass = eval(className + '.' + className)
                page.addCustomParamFields(gameClass)
            self.setModified()
        else:
            # user cancelled operation
            # SetSelection seems to be undocumented
            self.choiceBox.SetSelection(self.choiceBoxSelection)
        dlg.Destroy()

    def onNewMatchClicked(self, event):
        self.matchbook.addMatch(self.getGameClass())

    def getGameClass(self):
        """Return the class of the selected game, itself (not an instance)"""
        gameName = self.gameNames[self.choiceBox.GetSelection()]
        className = self.gameClassLookup[gameName]
        gameClass = eval(className + '.' + className)
        return gameClass

class MatchBook(wx.Notebook):
    def __init__(self, parent):
        wx.Notebook.__init__(self, parent, style=
                             wx.BK_DEFAULT
                             #wx.BK_TOP 
                             #wx.BK_BOTTOM
                             #wx.BK_LEFT
                             #wx.BK_RIGHT
                             # | wx.NB_MULTILINE
                             )
        self.fitCalled = False

    def onDuplicateClicked(self, event):
        page = self.GetPage(self.GetSelection())
        self.addMatch(self.GetParent().getGameClass(), page.getMatchParams())
        self.renumberTabs()
        self.GetParent().setModified()

    def onDeleteClicked(self, event):
        text = "Are you sure you want to delete the selected match?"
        dlg = wx.MessageDialog(self, text, 'Confirm Delete',
                               wx.OK | wx.CANCEL | wx.ICON_INFORMATION)
        val = dlg.ShowModal()
        dlg.Destroy()
        if val == wx.ID_OK:
            self.DeletePage(self.GetSelection())
            self.renumberTabs()
            self.GetParent().setModified()

    def onMoveBackClicked(self, event):
        p = self.GetSelection()
        if p == 0:
            return
        page = self.GetPage(p)
        self.RemovePage(p)
        self.InsertPage(p-1, page, "title", select=True)
        self.renumberTabs()
        self.GetParent().setModified()

    def onMoveFwdClicked(self, event):
        p = self.GetSelection()
        if p == self.GetPageCount()-1:
            return
        page = self.GetPage(p)
        self.RemovePage(p)
        self.InsertPage(p+1, page, "title", select=True)
        self.renumberTabs()
        self.GetParent().setModified()

    def renumberTabs(self):
        for p in range(self.GetPageCount()):
            self.SetPageText(p, "Match " + str(p+1))

    def addMatch(self, gameClass, match=None):
        """
        Add a new match to the matchbook, using the given game class to create
        the appropriate parameter fields.
        If match (dictionary of match parameters) is given, use it to populate
        the fields.
        """
        #print 'addMatch(): ', match
        tabtitle = 'Match ' + str(self.GetPageCount() + 1)
        page = MatchPage(self, gameClass, match)
        self.AddPage(page, tabtitle, select=True)

        # only call Fit() when the first match is added, to avoid resizing the
        # window after the user has sized it.
        if not self.fitCalled:
            self.GetParent().GetSizer().Fit(self.GetParent())
            self.fitCalled = True

class MatchPage(wx.Panel):
    def __init__(self, parent, gameClass=None, match=None):
        """
        Create a new page for the matchbook.  If match (dictionary of match
        parameters is given), use it to populate the non-game-specific fields of
        the page.  If gameClass is also given, also populate the game-specific
        fields.
        """

        wx.Panel.__init__(self,parent)
        vbox = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(vbox)
        sizerFlags = wx.SizerFlags(0).Border(wx.ALL, 4)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        duplicateButton = wx.Button(self, label="Duplicate")
        deleteButton = wx.Button(self, label="Delete")
        moveBackButton = wx.Button(self, label="Move <<")
        moveFwdButton = wx.Button(self, label="Move >>")
        hbox.Add(duplicateButton)
        hbox.Add(deleteButton)
        hbox.Add(moveBackButton)
        hbox.Add(moveFwdButton)
        vbox.AddF(hbox, sizerFlags)

        # need to ask the parent to do these things
        self.Bind(wx.EVT_BUTTON, self.GetParent().onDuplicateClicked,
                duplicateButton)
        self.Bind(wx.EVT_BUTTON, self.GetParent().onDeleteClicked, deleteButton)
        self.Bind(wx.EVT_BUTTON, self.GetParent().onMoveBackClicked,
                moveBackButton)
        self.Bind(wx.EVT_BUTTON, self.GetParent().onMoveFwdClicked,
                moveFwdButton)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.AddF(wx.StaticText(self, label="Description: "), sizerFlags)
        self.description = wx.TextCtrl(self, size=(300,-1))
        hbox.AddF(self.description, sizerFlags)
        vbox.AddF(hbox, sizerFlags)

        gbag = wx.GridBagSizer()
        gbag.Add(wx.StaticText(self, label="Practice"), (0,0))
        self.practice = wx.CheckBox(self)
        gbag.Add(self.practice, (0,1))
        gbag.Add(wx.StaticText(self, label="Number of Rounds"), (1,0))
        self.numRoundsSpinner = wx.SpinCtrl(self, min=1, initial=1)
        gbag.Add(self.numRoundsSpinner, (1,1))
        gbag.Add(wx.StaticText(self, label="Exchange Rate"), (2,0))
        self.exchRate = wx.TextCtrl(self, size=(80,-1))
            # SpinCtrl only supports integer values
        self.exchRate.SetToolTipString('US$ = ExchRate*E$')
        self.exchRate.SetValue('1')
        gbag.Add(self.exchRate, (2,1))
        vbox.Add(gbag)

        # If match was given, populate the parameter fields
        if match != None:
            self.description.SetValue(match['description'])
            self.practice.SetValue(match['practice'])
            self.numRoundsSpinner.SetValue(match['numRounds'])
            self.exchRate.SetValue(str(match['exchangeRate']))

        # Game-specific parameters
        vbox.Add(wx.StaticText(self, label="Game-specific Parameters"))
        self.scrolledPanel = scrolled.ScrolledPanel(self, size=(450,300),
            style=wx.TAB_TRAVERSAL|wx.SUNKEN_BORDER)
        gbag = wx.GridBagSizer()
        self.scrolledPanel.SetSizer(gbag)
        self.scrolledPanel.SetAutoLayout(1)
        self.scrolledPanel.SetupScrolling(scroll_x = False)
        self.addCustomParamFields(gameClass, match)

        gbag.Fit(self.scrolledPanel)
        vbox.Add(self.scrolledPanel, proportion=2, flag=wx.EXPAND)

        vbox.Fit(self)

        # Disable controls when opened in read-only mode
        readonly = parent.GetParent().readonly
        if readonly:
            for control in [duplicateButton, deleteButton, moveBackButton,\
                    moveFwdButton, self.description, self.practice,\
                    self.numRoundsSpinner, self.exchRate]:
                control.Enable(False)
                control.SetForegroundColour('BLUE')
            for control in self.custParamTextFields.values():
                control.Enable(False)
                control.SetForegroundColour('BLUE')

    def addCustomParamFields(self, gameClass, match=None):
        """
        Given the gameClass, which contains the names and descriptions of its
        custom parameters, create the labels and textfields for the custom
        parameters and put them the scrolledPanel of the MatchPage.
        If match is given, use it to populate the fields.
        """
        self.custParamTextFields = {}
        row = 0
        gbag = self.scrolledPanel.GetSizer()

        # This one takes them in whatever randomish order they happen to be in
        # the dictionary
        #for name, (defaultVal, desc) in gameClass.customParams.iteritems():

        # This one sorts them alphabetically by key (parameter name)
        for name, (defaultVal, desc) in sorted(gameClass.customParams.items()):

            # name is the key and tuple (defaultVal, desc) is the value in the
            # dictionary
            stext = wx.StaticText(self.scrolledPanel, label=name)
            stext.SetToolTipString(desc)
            gbag.Add(stext, (row, 0))
            # Store these textfields in a dictionary indexed by parameter name
            # so we can easily retrieve their values later.
            self.custParamTextFields[name] = wx.TextCtrl(self.scrolledPanel,
                size=(200,-1))
            self.custParamTextFields[name].SetValue(str(defaultVal))
            self.custParamTextFields[name].SetToolTipString(desc)
            gbag.Add(self.custParamTextFields[name], (row,1))

            # Place a label to the right of the box, indicating the number of
            # space-delimited values detected in the box (this is for where a
            # parameter is an array of values).
            stext = wx.StaticText(self.scrolledPanel, label="")
            self.custParamTextFields[name].valueCountLabel = stext
                # Now we can easily access the value count label associated with
                # this parameter when we receive a value changed event from the
                # parameter's text field.
            self.Bind(wx.EVT_TEXT, self.onCustomValueChanged,
                    self.custParamTextFields[name])
            gbag.Add(stext, (row, 2))

            row += 1

        # do voodoo to fix the layout
        gbag.Layout()
        self.GetSizer().Layout()
        # in Windows, need to jiggle the panel to get scrollbar to appear:
        w, h = self.scrolledPanel.GetSize()
        self.scrolledPanel.SetSize((w+1, h+1))
        self.scrolledPanel.SetSize((w, h))

        # Populate the textfields if match parameter values are available
        if match != None:
            for name, (defaultVal, desc) in gameClass.customParams.iteritems():
                if match['customParams'].has_key(name):
                    paramValue = match['customParams'][name]
                    self.custParamTextFields[name].SetValue(str(paramValue))
                    self.updateValueCountLabel(self.custParamTextFields[name])

    def onCustomValueChanged(self, event):
        paramField = event.GetEventObject()
        self.updateValueCountLabel(paramField)
        event.Skip()
    
    def updateValueCountLabel(self, paramField):
        """ Update value count label based on number of space-delimited values
        present in the text field. """
        paramValue = paramField.GetValue()
        valueCount = len(paramValue.split())
        if valueCount > 1:
            label = '(' + str(valueCount) + ')'
        else:
            label = ''
        paramField.valueCountLabel.SetLabel(label)
            # paramField.valueCountLabel is an attribute we created when
            # creating the paramField

    def removeCustomParamFields(self):
        self.scrolledPanel.GetSizer().Clear(deleteWindows=True)
        self.custParamTextFields = {}


    def getMatchParams(self):
        """Return the match parameters as a dictionary."""
        match = {}
        match['description'] = self.description.GetValue()
        match['practice'] = self.practice.GetValue()
        match['numRounds'] = self.numRoundsSpinner.GetValue()
        match['exchangeRate'] = float(self.exchRate.GetValue())
        customParams = {}
        for pname in self.custParamTextFields.keys():
            customParams[pname] = self.custParamTextFields[pname].GetValue()
        match['customParams'] = customParams
        return match
