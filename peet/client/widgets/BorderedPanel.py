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

class BorderedPanel(wx.Panel):
    """
    A panel with a border around (well, just inside) it, optionally rounded.
    """

    def __init__(self, parent,\
            borderThickness,\
            borderColor,\
            innerColor=None,\
            outerColor=None,\
            cornerRadius=0):
        wx.Panel.__init__(self, parent)

        if innerColor == None:
            innerColor = parent.GetBackgroundColour()
        if outerColor == None:
            outerColor = parent.GetBackgroundColour()

        self.borderThickness = borderThickness
        self.borderColor = borderColor
        self.innerColor = innerColor
        self.outerColor = outerColor
        self.cornerRadius = cornerRadius

        # In wxGTK, StaticTexts are drawn directly on the parent.  However, in
        # wxWin, they are full-fledged windows with their own backgrounds.
        # Their background colors are inherited from the parent.  So to avoid
        # rectangles of a different color around StaticTexts drawn on this
        # panel, we need to set the background color of this panel.
        self.SetBackgroundColour(innerColor)

        self.outerBrush = wx.Brush(outerColor)
        self.innerBrush = wx.Brush(innerColor)
        if borderThickness == 0:
            self.borderPen = wx.TRANSPARENT_PEN
        else:
            self.borderPen = wx.Pen(borderColor, borderThickness)

        self.Bind(wx.EVT_PAINT, self.onPaint)
        self.Bind(wx.EVT_SIZE, self.onSize)

    def onPaint(self, event):
        dc = wx.PaintDC(self)
        try:
            gc = wx.GraphicsContext.Create(dc)
        except NotImplementedError:
            dc.DrawText("This build of wxPython does not support the "
                        " wx.GraphicsContext family of classes.",
                        25, 25)
            return
        
        w, h = self.GetSize()

        # Draw the part outside the corners
        gc.SetBrush(self.outerBrush)
        gc.DrawRectangle(0, 0, w, h)

        # Draw the main part
        gc.SetPen(self.borderPen)
        gc.SetBrush(self.innerBrush)
        gc.DrawRoundedRectangle(self.borderThickness/2, self.borderThickness/2,\
                w - self.borderThickness, h - self.borderThickness,\
                self.cornerRadius)

    def onSize(self, event):
        self.Refresh()
        event.Skip()
