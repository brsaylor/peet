import sys
import os
import json
import re
from peet.server import parameters
import wx
import wx.lib.agw.hypertreelist as HTL

class TreeEditor(wx.Dialog):
    def __init__(self, parent,\
            schema, params=None, filename=None, readonly=False):

        wx.Dialog.__init__(self, parent, title="", size=(600,700),\
                style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        self.schema = schema
        self.readonly = readonly
        self._modified = False

        if params == None:
            params = {}

        sizerFlags = wx.SizerFlags(0).Border(wx.ALL, 4)

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(mainSizer)

        # Filename text
        self._filenameLabel = wx.StaticText(self, label = "File:")
        mainSizer.AddF(self._filenameLabel, sizerFlags)

        # Buttons for file operations
        newButton = wx.Button(self, wx.ID_ANY, "New")
        openButton = wx.Button(self, wx.ID_ANY, "Open")
        saveButton = wx.Button(self, wx.ID_ANY, "Save")
        saveAsButton = wx.Button(self, wx.ID_ANY, "Save As...")
        saveAndCloseButton = wx.Button(self, wx.ID_ANY, "Save and Close")
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(newButton)
        hbox.Add(openButton)
        hbox.Add(saveButton)
        hbox.Add(saveAsButton)
        hbox.Add(saveAndCloseButton)
        mainSizer.AddF(hbox, sizerFlags)
        self.Bind(wx.EVT_BUTTON, self._onNewClicked, newButton)
        self.Bind(wx.EVT_BUTTON, self._onOpenClicked, openButton)
        self.Bind(wx.EVT_BUTTON, self._onSaveClicked, saveButton)
        self.Bind(wx.EVT_BUTTON, self._onSaveAsClicked, saveAsButton)
        self.Bind(wx.EVT_BUTTON, self._onSaveAndCloseClicked,saveAndCloseButton)

        editorSizer = wx.BoxSizer(wx.HORIZONTAL)

        self._tree = HTL.HyperTreeList(self, wx.ID_ANY,\
                style=wx.TR_DEFAULT_STYLE\
                #|wx.TR_MULTIPLE\
                |wx.TR_FULL_ROW_HIGHLIGHT\
                |wx.TR_ROW_LINES\
                ^wx.TR_NO_LINES) # doesn't work
        self._tree.AddColumn("Key")
        self._tree.AddColumn("Value")
        self._tree.SetMainColumn(0)
        self._tree.SetColumnWidth(0, 200)
        #self._tree.SetColumnEditable(1, True)

        editorSizer.Add(self._tree, 1, flag=wx.EXPAND)

        # Create the parameter info pane
        self._infoPane = wx.TextCtrl(self, wx.ID_ANY,\
                size=(200, -1),\
                style=wx.TE_MULTILINE|wx.TE_READONLY)

        editorSizer.Add(self._infoPane, 0, flag=wx.EXPAND)

        mainSizer.Add(editorSizer, 1, flag=wx.EXPAND)

        # Create the image list for type icons
        self.typeNames = ['object', 'array', 'number', 'integer', 'string',\
                'boolean'] 
        imageList = wx.ImageList(16, 16, True, len(self.typeNames))
        for name in self.typeNames:
            fname = os.path.join(os.path.dirname(__file__), 'icons',\
                    name + '.png')
            bitmap = wx.Bitmap(fname)
            imageList.Add(bitmap)
        self._tree.AssignImageList(imageList)

        # Create other bitmaps
        #self.addBitmap = wx.Bitmap('icons/add.png')

        # Make a dictionary for mapping window IDs of buttons to the tree items
        # to which the buttons are associated.
        #self._treeItemsByButtonID = {}
        #self.buttonID = 0

        self._tree.GetMainWindow().Bind(wx.EVT_LEFT_DOWN, self._onLeftDown)
        self._tree.GetMainWindow().Bind(wx.EVT_LEFT_UP, self._onLeftUp)
        self._tree.GetMainWindow().Bind(wx.EVT_RIGHT_DOWN, self._onRightDown)
        self._tree.GetMainWindow().Bind(wx.EVT_RIGHT_DOWN, self._onRightDown)
        self.Bind(wx.EVT_TREE_BEGIN_DRAG, self._onBeginDrag, self._tree)
        self.Bind(wx.EVT_TREE_END_DRAG, self._onEndDrag, self._tree)
        self.Bind(wx.EVT_TREE_END_LABEL_EDIT, self._onEndLabelEdit, self._tree)

        self._tree.GetMainWindow().Bind(wx.EVT_TREE_ITEM_GETTOOLTIP,\
                self._onGetToolTip)

        # FIXME: why doesn't this work?
        self._tree.GetMainWindow().Bind(wx.EVT_MENU_HIGHLIGHT_ALL,\
                self._onMenuHighlight)

        self.Bind(wx.EVT_CLOSE, self._onClose)

        # Create the root item
        item = self._tree.AddRoot("Parameters")
        self._tree.SetItemPyData(item, {'schema': self.schema})
        self._setItemValue(item, params)
        self._tree.ExpandAll()

        self.setFilename(filename)

    def getParams(self):
        return self._getItemValue(self._tree.GetRootItem())

    def getFilename(self):
        return self.filename

    def getModified(self):
        # FIXME: Should we just assume that the editor is going to either save
        # or discard the changes?
        return self._modified

    def setParams(self, params):
        self._setItemValue(self._tree.GetRootItem(), params)

    def setFilename(self, filename):
        self.filename = filename
        if self._modified:
            modified = ' *modified* '
        else:
            modified = ''
        self.SetTitle("Parameter Editor: " + modified + self._getFilenameText())
        self._filenameLabel.SetLabel("File: " + self._getFilenameText())
        self._filenameLabel.SetToolTipString(self._getFilenameText())

    def _getFilenameText(self):
        """Assuming self.filename contains the full-path filename, return
        formatted filename text."""
        if self.filename == None:
            filenametext = "[No file]"
        else:
            dname, fname = os.path.split(self.filename)
            filenametext = fname + " (" + dname + ")"
        return filenametext

    def _onNewClicked(self, event):
        if self._confirmIfModified():
            self.setFilename(None)
            self._setModified()
            self._setItemValue(self._tree.GetRootItem(), {})

    def _onOpenClicked(self, event):
        if not self._confirmIfModified():
            return

        dlg = wx.FileDialog(self, message="Open Parameter File", style=wx.OPEN,\
                wildcard=parameters.fileDlgWildcard,\
                defaultDir=parameters.defaultDir)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
            try:
                infile = open(filename)
                params = json.load(infile)
                infile.close()
            except IOError:
                print 'IOError'
                # FIXME do something useful
            else:
                self._setModified(False)
                self.setParams(params)
                self.setFilename(filename)
                self._tree.ExpandAll()
        dlg.Destroy()

    def _onSaveClicked(self, event):
        if self.filename == None:
            self._onSaveAsClicked(event)
        else:
            try:
                self._save()
            except:
                print 'Error saving parameter file' # FIXME do something useful

    def _onSaveAsClicked(self, event):
        if self.filename == None:
            dname = parameters.defaultDir
            fname = 'untitled.json'
        else:
            dname, fname = os.path.split(self.filename)
        dlg = wx.FileDialog(self, message="Save As...", style=wx.SAVE,
                defaultDir=dname, defaultFile=fname,
                wildcard=parameters.fileDlgWildcard)
        val = dlg.ShowModal()

        if val != wx.ID_OK:
            # User cancelled
            dlg.Destroy()
            return

        filename = dlg.GetPath()
        # Automatically append the filename extension .json if the file does
        # not have it.
        #print '************'
        #print filename
        if os.path.splitext(filename)[1] != '.json':
                filename += '.json'
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

        oldFilename = self.filename  # in case the save fails
        try:
            self.setFilename(filename)
            self._save()
        except:
            print 'Error saving parameter file' # FIXME do something useful
            print sys.exc_info()
            self.setFilename(oldFilename)
        else:
            # File was successfully saved.  If this function was called from the
            # onClose() handler (i.e. user was closing window, was presented
            # with "Save Changes?" dialog, and clicked Save), then
            # event=='closing' and we close the parameter editor.
            if event=='closing':
                self.EndModal(parameters.KEEP)

    def _onSaveAndCloseClicked(self, event):
        self._onSaveClicked(None)
        self._onClose(None) 

    def _onClose(self, event):
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

        if self._modified:
            dlg = ConfirmCloseDlg(self)
            val = dlg.ShowModal()
            dlg.Destroy()
            if val == 1:
                # event.Skip() does not work if dialog is presented.
                # (Discard) Allow window to close
                self.EndModal(parameters.DISCARD)
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
            self.EndModal(parameters.KEEP)

    def _save(self):
        """ Assuming self.filename contains a the path to a writable file, save
        the parameters in JSON format to that file. """
        outfile = open(self.filename, 'w')
        json.dump(self.getParams(), outfile, sort_keys=True, indent=4)
        outfile.close()
        self._setModified(False)

    def _setModified(self, modified=True):
        if self._modified != modified:
            self._modified = modified
            if modified:
                mtext = ' *modified* '
            else:
                mtext = ''
            self.SetTitle("Parameter Editor: " + mtext +
                    self._getFilenameText())

    def _confirmIfModified(self):
        """ If the parameters have been modified, confirm with the user that the
        changes should be discarded.
        @return True if unmodified or user clicks "Yes"; otherwise False """
        if self._modified:
            text = "Parameters have been modified.  Discard changes?"
            dlg = wx.MessageDialog(self, text, 'Confirm',
                    wx.YES_NO | wx.ICON_INFORMATION)
            if dlg.ShowModal() == wx.ID_YES:
                #print 'Yes clicked'
                dlg.Destroy()
                return True
            else:
                #print 'No clicked'
                dlg.Destroy()
                return False
        else:
            return True

    def _getItemValue(self, item):
        """ Return the data value represented by item, recursively including any
        subitems. """
        schema = self._tree.GetItemPyData(item)['schema']

        # If item represents a collection, get value recursively
        if schema['type'] == 'object':
            value = {}
            (child, cookie) = self._tree.GetFirstChild(item)
            while child:
                childKey = self._tree.GetItemText(child, 0)
                childValue = self._getItemValue(child)
                value[childKey] = childValue
                (child, cookie) = self._tree.GetNextChild(item, cookie)
        elif schema['type'] == 'array':
            value = []
            (child, cookie) = self._tree.GetFirstChild(item)
            while child:
                value.append(self._getItemValue(child))
                (child, cookie) = self._tree.GetNextChild(item, cookie)

        # Item is not a collection - return its single value
        elif schema['type'] == 'boolean':
            value = (self._tree.GetItemText(item, 1) == 'True')
        else:
            # Will be a number or a string; cast directly to original type.
            pyType = parameters.JSONTypeMap[schema['type']]
            value = pyType(self._tree.GetItemText(item, 1))

        return value

    def _setItemValue(self, item, value):
        """ Set the value of the given tree item.  If the value is a dict or a
        list, recursively create subitems and set their values.  Assumes that
        the schema for the item has already been set, and that the value is of
        the type specified in the schema (mapped from JSON Schema type to Python
        type; see parameters.JSONTypeMap). """

        schema = self._tree.GetItemPyData(item)['schema']

        # If the value is a collection, delete the item's existing children,
        # then recursively set values for its elements
        if schema['type'] == 'object':
            self._tree.DeleteChildren(item)
            for k, v in sorted(value.items()):
                child = self._tree.AppendItem(item, k)
                childSchema = schema.get('properties', {}).get(k, None)
                self._tree.SetItemPyData(child, {'schema': childSchema})
                self._setItemValue(child, v)
        elif schema['type'] == 'array':
            self._tree.DeleteChildren(item)
            # FIXME: Allow the possibility that 'items' is an array of schemas
            # rather than a single schema
            childSchema = schema.get('items')
            for k, v in enumerate(value):
                child = self._tree.AppendItem(item, str(k+1))
                self._tree.SetItemPyData(child, {'schema': childSchema})
                self._setItemValue(child, v)

        else:
            # The value is not a collection - we've reached a leaf in the tree
            self._tree.SetItemText(item, str(value), 1)

        self._setItemImage(item, schema['type'])

    def _onLeftDown(self, event):
        pos = event.GetPosition()
        item, flags, col = self._tree.HitTest(pos)

        if item == None:
            event.Skip()
            return

        self.currentItem = item
        self._tree.SelectItem(self.currentItem)
        schema = self._tree.GetItemPyData(item)['schema']

        if col == 0 and (flags & wx.TREE_HITTEST_ONITEMLABEL):
            # Clicked on label in the Key column - pop up a menu with operations
            # on the key (clicking on the icon or arrow expands or collapses the
            # children, so shouldn't pop up the menu)
        
            menu = wx.Menu()

            if schema['type'] == 'object':
                # Create a submenu for adding the properties included in the
                # item's schema.
                submenu = wx.Menu()
                itemValue = self._getItemValue(item)
                for propName, propSchema in sorted(\
                        schema['properties'].items()):
                    menuItem = submenu.Append(wx.NewId(), propName,\
                            propSchema.get('description', 'No description'))
                    self.Bind(wx.EVT_MENU, self._onAddPropertyClicked, menuItem)
                    # Disable properties that it already has
                    if itemValue.has_key(propName):
                        menuItem.Enable(False)

                menu.AppendMenu(wx.ID_ANY, "Add Property", submenu)
            if schema['type'] == 'array':
                menuItem = menu.Append(wx.ID_ANY, "Append Item")
                self.Bind(wx.EVT_MENU, self._onAppendItemClicked, menuItem)
                menuItem = menu.Append(wx.ID_ANY, "Paste Items")
                self.Bind(wx.EVT_MENU, self._onPasteItemsClicked, menuItem)

            if not item == self._tree.GetRootItem():
                menuItem = menu.Append(wx.ID_ANY, "Delete Item")
                self.Bind(wx.EVT_MENU, self._onDeleteItemClicked, menuItem)

            self._tree.PopupMenu(menu)
            menu.Destroy()

        elif col == 1:
            # Clicked on the Value column - allow editing via text field or
            # popup menu as appropriate

            # FIXME: check for value change in event handlers rather than just
            # assuming user is going to modify a value
            self._setModified(True)

            if schema['type'] == 'boolean':
                menu = wx.Menu()
                for value in ('True', 'False'):
                    menuItem = menu.Append(wx.NewId(), value)
                    self.Bind(wx.EVT_MENU, self._onEnumValueSelected, menuItem)
                self._tree.PopupMenu(menu)
                menu.Destroy()

            elif schema.has_key('enum'):
                # item has a set of possible values to be select from a
                # drop-down menu

                menu = wx.Menu()
                for value in schema['enum']:
                    menuItem = menu.Append(wx.NewId(), str(value))
                    self.Bind(wx.EVT_MENU, self._onEnumValueSelected, menuItem)
                self._tree.PopupMenu(menu)
                menu.Destroy()

            elif not (schema['type'] == 'object' or schema['type'] == 'array'):
                # item has a value editable in a text box
                self._tree.EditLabel(item, 1)
                wx.CallAfter(self._tree.GetEditControl().SetFocus)

        # stop event propagation
        event.Skip()

    def _onLeftUp(self, event):
        event.Skip()

    def _onRightDown(self, event):
        pos = event.GetPosition()
        item, flags, col = self._tree.HitTest(pos)
        self.currentItem = item

        #print json.dumps(self._tree.GetItemPyData(item)['schema'],\
        #        sort_keys=True, indent=4)

        event.Skip()

    def _onBeginDrag(self, event):
        item = event.GetItem()
        if item:
            event.Allow()

    def _onEndDrag(self, event):
        targetItem = event.GetItem()
        draggedItem = self.currentItem

        # For now, only allow dragging if the source and destination items share
        # the same parent and that parent represents an array.
        parentItem = self._tree.GetItemParent(draggedItem)
        parentSchema = self._tree.GetItemPyData(parentItem)['schema']
        if parentSchema['type'] == 'array'\
                and parentItem == self._tree.GetItemParent(targetItem):
            # The TreeCtrl family doesn't support moving items: have to copy and
            # delete.
            newItem = self._tree.InsertItem(parentItem, targetItem, '')

            # Set the schema before setting the value
            self._tree.SetItemPyData(newItem,\
                    self._tree.GetItemPyData(draggedItem))

            # Set the value
            self._setItemValue(newItem, self._getItemValue(draggedItem))

            # Delete the old item
            self._tree.Delete(draggedItem)

            # Renumber the indices
            self._renumberList(parentItem)

            # FIXME: why doesn't this work?
            wx.CallAfter(self._tree.SelectItem, newItem)

            self._setModified()

        else:
            event.Skip()

    def _onEndLabelEdit(self, event):
        item = event.GetItem()
        # Item still has old value at this moment; have to use CallAfter to
        # access the new value for validation.
        wx.CallAfter(self._validateItem, item)

    def _validateItem(self, item):
        """ For now, all this does is force the item's value to a valid integer
        or float, if that's what it's supposed to be. """
        schema = self._tree.GetItemPyData(item)['schema']
        text = self._tree.GetItemText(item, 1)
        if schema['type'] == 'integer':
            # Remove the first non-digit character and everything that follows
            validText = re.sub('[^0-9].*$', '', text)
            if validText == '': validText = '0'
            self._setItemValue(item, int(validText))
        elif schema['type'] == 'number':
            # Search the string for the first valid number and use that; or 0 if
            # not found.
            matches = re.findall('[0-9]*\.?[0-9]*', text)
            validText = '0.0'
            for m in matches:
                if m != '':
                    validText = m
                    break
            self._setItemValue(item, float(validText))


    def _onEnumValueSelected(self, event):
        """ Called when the user selects a value from the menu that appears when
        editing a variable with a fixed set of possible values. """

        menu = event.GetEventObject()
        menuItem = menu.FindItemById(event.GetId())

        schema = self._tree.GetItemPyData(self.currentItem)['schema']
        if schema['type'] == 'boolean':
            value = (menuItem.GetItemLabelText() == 'True')
        else:
            value = parameters.JSONTypeMap[schema['type']](\
                    menuItem.GetItemLabelText())

        self._setItemValue(self.currentItem, value)

    def _onAddPropertyClicked(self, event):
        """ Called when the user clicks on a property to add from an object's
        popup menu of available properties """

        menu = event.GetEventObject()
        menuItem = menu.FindItemById(event.GetId())
        propName = menuItem.GetItemLabelText()

        child = self._tree.AppendItem(self.currentItem, propName)

        currentItemSchema = self._tree.GetItemPyData(self.currentItem)['schema']
        childSchema = currentItemSchema['properties'][propName]
        self._tree.SetItemPyData(child, {'schema': childSchema})

        # Initialize the new item with the default value
        self._setItemValue(child, parameters.getDefault(childSchema))

        self._tree.OnCompareItems = self._onCompareItems_alpha
        self._tree.SortChildren(self.currentItem)
        self._tree.ExpandAllChildren(self.currentItem)

        self._setModified()

    def _onAppendItemClicked(self, event):
        lastChild = self._tree.GetLastChild(self.currentItem)
        if lastChild:
            lastNum = int(self._tree.GetItemText(lastChild))
        else:
            lastNum = 0
        child = self._tree.AppendItem(self.currentItem, str(lastNum+1))
        currentItemSchema = self._tree.GetItemPyData(self.currentItem)['schema']
        childSchema = currentItemSchema['items']
        self._tree.SetItemPyData(child, {'schema': childSchema})

        # Initialize the new item with the default value
        self._setItemValue(child, parameters.getDefault(childSchema))

        self._tree.OnCompareItems = self._onCompareItems_numeric
        self._tree.SortChildren(self.currentItem)
        self._tree.ExpandAllChildren(self.currentItem)

        self._setModified()

    def _onPasteItemsClicked(self, event):
        success = False
        if not wx.TheClipboard.IsOpened():
            data = wx.TextDataObject()
            wx.TheClipboard.Open()
            success = wx.TheClipboard.GetData(data)
            wx.TheClipboard.Close()
        else:
            print "Error: Clipboard locked"

        if success:
            array = data.GetText().split()

            # Convert the elements to the type in the schema
            # FIXME: this won't work if they are booleans represented as strings
            schemaType = self._tree.GetItemPyData(self.currentItem)\
                    ['schema']['items']['type']
            try:
                array = map(parameters.JSONTypeMap[schemaType], array)
            except:
                print "Error:", sys.exc_info()
                # FIXME: display error dialog
                return

            self._setItemValue(self.currentItem, array)
            self._tree.ExpandAllChildren(self.currentItem)
        else:
            print "Error reading clipboard"

    def _onDeleteItemClicked(self, event):
        """ Delete the current item. """

        # Doesn't seem to be implemented
        # self._tree.SelectAllChildren(self.currentItem)

        dlg = wx.MessageDialog(self, 'Are you sure you want to delete this '\
                + 'item and all sub-items?',
                               'Confirm',
                               wx.OK | wx.CANCEL | wx.ICON_QUESTION
                               )
        if dlg.ShowModal() == wx.ID_OK:
            self._tree.Delete(self.currentItem)
            self._setModified()
        dlg.Destroy()

    def _onGetToolTip(self, event):
        item = event.GetItem()
        schema = self._tree.GetItemPyData(item)['schema']

        # Get the keys of this item and its ancestors
        pathKeys = []
        pathItem = item
        root = self._tree.GetRootItem()
        while pathItem != root:
            pathKeys.append(self._tree.GetItemText(pathItem, 0))
            pathItem = self._tree.GetItemParent(pathItem)
        pathKeys.reverse()

        # Build the text to show in the infoPane
        text = ''
        for i, key in enumerate(pathKeys):
            text += '  ' * i  # indent
            text += key + '\n'
        text += '\n' + 'Type: ' + schema['type'] + '\n'
        text += '\n' + schema.get('description', 'No description')

        self._infoPane.SetValue(text)

        event.Skip()

    def _onMenuHighlight(self, event):
        """ Called when the mouse moves over a menu item. """
        print 'onMenuHighlight'

    def _onCompareItems_alpha(self, item1, item2):
        """ This function is assigned to tree.OnCompareItems as a kludgy way of
        overriding it. """
        text1 = self._tree.GetItemText(item1)
        text2 = self._tree.GetItemText(item2)
        if text1 == text2:
            return 0
        elif text1 < text2:
            return -1
        else:
            return 1

    def _onCompareItems_numeric(self, item1, item2):
        return int(self._tree.GetItemText(item1))\
                - int(self._tree.GetItemText(item2))

    def _renumberList(self, item):
        """ Given a TreeItem representing a list, sequentially renumber the
        indices shown in the Key column for its children.  Note: we count array
        indices from 1. """
        i = 1
        (child, cookie) = self._tree.GetFirstChild(item)
        while child:
            self._tree.SetItemText(child, str(i), 0)
            (child, cookie) = self._tree.GetNextChild(item, cookie)
            i += 1

    def _insertItemSorted(self, item, text):
        pass

    def _setItemImage(self, item, typeName):
        """ Set image to be used for the item for all of the item's possible
        states. """
        imageIndex = self.typeNames.index(typeName)
        for state in [wx.TreeItemIcon_Normal, wx.TreeItemIcon_Selected,\
                wx.TreeItemIcon_Expanded, wx.TreeItemIcon_SelectedExpanded]:
            self._tree.SetItemImage(item, imageIndex, which=state)
