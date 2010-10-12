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

import sys
import os.path
import traceback
import csv
import wx

class MainWindow(wx.Frame):
    def __init__(self,parent,id,title):
        wx.Frame.__init__(self,parent,wx.ID_ANY, title, size = (600,400))
        self.panel = wx.Panel(self)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(self.sizer)

        self.openButton = wx.Button(self.panel,-1, 'Choose (more) files')
        self.sizer.Add(self.openButton)
        self.clearButton = wx.Button(self.panel,-1, 'Clear file list')
        self.sizer.Add(self.clearButton)
        self.fileListBox = wx.TextCtrl(self.panel, #size=(400,300),
            style=wx.TE_MULTILINE|wx.TE_RICH2)
        self.fileListBox.SetEditable(False)
        self.sizer.Add(self.fileListBox, 1, flag=wx.EXPAND)
        self.mergeButton = wx.Button(self.panel,-1, 'Merge files')
        self.sizer.Add(self.mergeButton)

        self.Bind(wx.EVT_BUTTON, self.onOpenClicked, self.openButton)
        self.Bind(wx.EVT_BUTTON, self.onClearClicked, self.clearButton)
        self.Bind(wx.EVT_BUTTON, self.onMergeClicked, self.mergeButton)

        self.wildcard = "Comma-delimited files (*.csv)|*.csv|"     \
           "Comma-delimited history files (*history.csv)|*history.csv|" \
           "All files|*"
        self.paths = []

        self.Show(True)

    def onOpenClicked(self, event):

        dlg = wx.FileDialog(self, message="Open CSV Files",\
                style=wx.OPEN | wx.MULTIPLE | wx.CHANGE_DIR,\
                wildcard=self.wildcard)
        if dlg.ShowModal() == wx.ID_OK:
            paths = dlg.GetPaths()
            for path in paths:
                self.fileListBox.AppendText(path + '\n')
                self.paths.append(path)
        dlg.Destroy()

    def onClearClicked(self, event):
        self.fileListBox.Clear()
        self.paths = []

    def onMergeClicked(self, event):
        dlg = wx.FileDialog(self, message="Save merged file as...",\
                style=wx.SAVE | wx.CHANGE_DIR,\
                wildcard=self.wildcard)
        val = dlg.ShowModal()

        if val != wx.ID_OK:
            # User cancelled
            dlg.Destroy()
            return

        filename = dlg.GetPath()
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
            self.outfilename = filename
            self.mergeCSV()
        except:
            text = traceback.format_exc()
            dlg = wx.MessageDialog(self, text, 'Error', wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return
        
        text = "Successfully merged files."
        dlg = wx.MessageDialog(self, text, 'Success', wx.OK|wx.ICON_INFORMATION)
        val = dlg.ShowModal()
        dlg.Destroy()

    def mergeCSV(self):
        """ Take all the files named by self.paths[] and merge them, writing to
        the file named by self.outfilename."""

        headerrow = []

        # Read the header row from all the files so we can build the headerrow
        # which contains the fields from all the files.
        for path in self.paths:
            file = open(path, 'rb')
            csvreader = csv.reader(file)
            firstrow = csvreader.next()
            for header in firstrow:
                if header not in headerrow:
                    headerrow.append(header)
            file.close()
        
        # open output file
        outfile = open(self.outfilename, 'wb')
        csvwriter = csv.DictWriter(outfile, headerrow)

        # write header row (DictWriter does not write it automatically)
        rowdict = {}
        for header in headerrow:
            rowdict[header] = header
        csvwriter.writerow(rowdict)

        # open the input files and append them to the output file
        # Note: The first row returned by DictReader is the first data row, not
        # the header row.
        for path in self.paths:
            infile = open(path, 'rb')
            csvreader = csv.DictReader(infile)
            for row in csvreader:
                csvwriter.writerow(row)
            infile.close()

        outfile.close()

app = wx.PySimpleApp()
frame = MainWindow(None, -1, "CSV Merge")
app.MainLoop()
