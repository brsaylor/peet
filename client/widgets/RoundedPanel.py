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

class RoundedPanel(wx.Panel):

    def __init__(self, parent, radii, bgcolor, fgcolor):
        wx.Panel.__init__(self, parent)

        self.radii = radii
        self.bgcolor = bgcolor
        self.fgcolor = fgcolor

        # In wxGTK, StaticTexts are drawn directly on the parent.  However, in
        # wxWin, they are full-fledged windows with their own backgrounds.
        # Their background colors are inherited from the parent.  So to avoid
        # rectangles of a different color around StaticTexts drawn on this
        # panel, we need to set the background color of this panel (which is
        # actually the foreground color as we are thinking about it in the
        # context of drawing the rounded rectangle).
        self.SetBackgroundColour(fgcolor)

        self.diams = []
        for radius in self.radii:
            self.diams.append(radius * 2)

        self.fgbrush = wx.Brush(fgcolor)
        self.bgbrush = wx.Brush(bgcolor)

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

        # FIXME: Could probably do this using a GraphicsPath (from
        # gc.CreatePath()).  Then, it would be possible to draw a border around
        # the edge as well.  May be faster, too.

        # Fill with foreground color
        gc.SetBrush(self.fgbrush)
        gc.DrawRectangle(0, 0, w, h)

        # In each corner, draw a bgcolor square and a fgcolor circle.
        # But only if the radius for that corner is positive (seems to screw up
        # the rest of the drawing if it's 0).

        # upper left
        if self.radii[0] > 0:
            gc.SetBrush(self.bgbrush)
            gc.DrawRectangle(0, 0, self.radii[0], self.radii[0])
            gc.SetBrush(self.fgbrush)
            gc.DrawEllipse(0, 0, self.diams[0], self.diams[0])

        # upper right
        if self.radii[1] > 0:
            gc.SetBrush(self.bgbrush)
            gc.DrawRectangle(w-self.radii[1], 0, self.radii[1], self.radii[1])
            gc.SetBrush(self.fgbrush)
            gc.DrawEllipse(w-self.diams[1], 0, self.diams[1], self.diams[1])
        
        # lower left
        if self.radii[2] > 0:
            gc.SetBrush(self.bgbrush)
            gc.DrawRectangle(0, h-self.radii[2], self.radii[2], self.radii[2])
            gc.SetBrush(self.fgbrush)
            gc.DrawEllipse(0, h-self.diams[2], self.diams[2], self.diams[2])

        # lower right
        if self.radii[3] > 0:
            gc.SetBrush(self.bgbrush)
            gc.DrawRectangle(w-self.radii[3], h-self.radii[3],\
                    self.radii[3], self.radii[3])
            gc.SetBrush(self.fgbrush)
            gc.DrawEllipse(w-self.diams[3], h-self.diams[3],\
                    self.diams[3], self.diams[3])

    def onSize(self, event):
        self.Refresh()
        event.Skip()


class TestApp(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, wx.ID_ANY, 'RoundedPanel')

        # UL, UR, LL, LR
        panel = RoundedPanel(self, [10,20,30,40], 'white', 'black')

        self.Show(True)

def main():
    app = wx.PySimpleApp()
    frame = TestApp()
    app.MainLoop()

if __name__ == '__main__':
    __name__ = 'Main'
    main()
