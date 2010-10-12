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

class BitmapPanel(wx.Panel):
    """ A semi-replacement for wx.StaticBitmap, which crashes in wxGTK if you
    give it any children, and claims to be designed only for small images
    anyway. """
    def __init__(self, parent, id=-1, bitmap=None):
        wx.Panel.__init__(self, parent, id)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.SetBitmap(bitmap)

    def SetBitmap(self, bitmap):
        self.bitmap = bitmap
        if bitmap != None:
            self.SetSize(bitmap.GetSize())
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

        w, h = self.GetSize()
        if self.bitmap != None:
            gc.DrawBitmap(self.bitmap, 0, 0, w, h)
