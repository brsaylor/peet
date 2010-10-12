# Copyright:
# The wxPython license is the wxWidgets license, which is essentially LGPL,
# which is GPL3-compatible.
# - Ben Saylor

import wx
import FloatSpin as FS

import sys

#----------------------------------------------------------------------
def GetMondrianData():
    return \
'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00 \x00\x00\x00 \x08\x06\x00\
\x00\x00szz\xf4\x00\x00\x00\x04sBIT\x08\x08\x08\x08|\x08d\x88\x00\x00\x00qID\
ATX\x85\xed\xd6;\n\x800\x10E\xd1{\xc5\x8d\xb9r\x97\x16\x0b\xad$\x8a\x82:\x16\
o\xda\x84pB2\x1f\x81Fa\x8c\x9c\x08\x04Z{\xcf\xa72\xbcv\xfa\xc5\x08 \x80r\x80\
\xfc\xa2\x0e\x1c\xe4\xba\xfaX\x1d\xd0\xde]S\x07\x02\xd8>\xe1wa-`\x9fQ\xe9\
\x86\x01\x04\x10\x00\\(Dk\x1b-\x04\xdc\x1d\x07\x14\x98;\x0bS\x7f\x7f\xf9\x13\
\x04\x10@\xf9X\xbe\x00\xc9 \x14K\xc1<={\x00\x00\x00\x00IEND\xaeB`\x82' 

def GetMondrianBitmap():
    return wx.BitmapFromImage(GetMondrianImage())

def GetMondrianImage():
    import cStringIO
    stream = cStringIO.StringIO(GetMondrianData())
    return wx.ImageFromStream(stream)

def GetMondrianIcon():
    icon = wx.EmptyIcon()
    icon.CopyFromBitmap(GetMondrianBitmap())
    return icon

#----------------------------------------------------------------------


class FloatSpinDemo(wx.Frame):

    def __init__(self, *args, **kwds):
       
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        self.SetIcon(GetMondrianIcon())

        self.statusbar = self.CreateStatusBar(2, wx.ST_SIZEGRIP)
        self.statusbar.SetStatusWidths([-2, -1])
        # statusbar fields
        statusbar_fields = [("FloatSpin Demo, Andrea Gavana @ 16 Nov 2005"),
                            ("Welcome To wxPython!")]

        for i in range(len(statusbar_fields)):
            self.statusbar.SetStatusText(statusbar_fields[i], i)
            
        self.SetMenuBar(self.CreateMenuBar())
        
        self.mainpanel = wx.Panel(self, -1)
        self.sizer_5_staticbox = wx.StaticBox(self.mainpanel, -1, "Example 2")
        self.sizer_7_staticbox = wx.StaticBox(self.mainpanel, -1, "Example 3")
        self.sizer_8_staticbox = wx.StaticBox(self.mainpanel, -1, "Example 4")
        self.sizer_4_staticbox = wx.StaticBox(self.mainpanel, -1, "Example 1")
        self.helptext = wx.StaticText(self.mainpanel, -1, "FloatSpin Demo: Play With Different Options!")
        
        self.floatspin1 = FS.FloatSpin(self.mainpanel, -1, min_val=0, max_val=1,
                                       increment=0.01, value=0.1, extrastyle=FS.FS_LEFT)
        self.floatspin1.SetFormat("%f")
        self.floatspin1.SetDigits(2)
        
        self.setvalue1 = wx.Button(self.mainpanel, -1, "Set Value")
        self.textctrlvalue1 = wx.TextCtrl(self.mainpanel, -1, "0.0")
        self.setdigits1 = wx.Button(self.mainpanel, -1, "Set Digits")
        self.textctrldigits1 = wx.TextCtrl(self.mainpanel, -1, "2")
        self.radioformat1 = wx.RadioBox(self.mainpanel, -1, "Set Format",
                                        choices=["%f", "%F", "%e", "%E", "%g", "%G"],
                                        majorDimension=2, style=wx.RA_SPECIFY_COLS)
        self.setincrement1 = wx.Button(self.mainpanel, -1, "Set Increment")
        self.textctrlincr1 = wx.TextCtrl(self.mainpanel, -1, "0.01")
        self.setfont1 = wx.Button(self.mainpanel, -1, "Set Font")

        self.floatspin2 = FS.FloatSpin(self.mainpanel, -1, min_val=-10, max_val=100,
                                       increment=0.1, extrastyle=FS.FS_RIGHT)
        self.floatspin2.SetFormat("%e")
        self.floatspin2.SetDigits(4)
        
        self.setvalue2 = wx.Button(self.mainpanel, -1, "Set Value")
        self.textctrlvalue2 = wx.TextCtrl(self.mainpanel, -1, "0.0")
        self.setdigits2 = wx.Button(self.mainpanel, -1, "Set Digits")
        self.textctrldigits2 = wx.TextCtrl(self.mainpanel, -1, "4")
        self.radioformat2 = wx.RadioBox(self.mainpanel, -1, "Set Format",
                                        choices=["%f", "%F", "%e", "%E", "%g", "%G"],
                                        majorDimension=2, style=wx.RA_SPECIFY_COLS)
        self.setincrement2 = wx.Button(self.mainpanel, -1, "Set Increment")
        self.textctrlincr2 = wx.TextCtrl(self.mainpanel, -1, "0.1")
        self.setfont2 = wx.Button(self.mainpanel, -1, "Set Font")

        self.floatspin3 = FS.FloatSpin(self.mainpanel, -1, min_val=0.01, max_val=0.05,
                                       increment=0.0001, extrastyle=FS.FS_CENTRE)
        self.floatspin3.SetFormat("%f")
        self.floatspin3.SetDigits(5)
        
        self.setvalue3 = wx.Button(self.mainpanel, -1, "Set Value")
        self.textctrlvalue3 = wx.TextCtrl(self.mainpanel, -1, "0.01")
        self.setdigits3 = wx.Button(self.mainpanel, -1, "Set Digits")
        self.textctrldigits3 = wx.TextCtrl(self.mainpanel, -1, "5")
        self.radioformat3 = wx.RadioBox(self.mainpanel, -1, "Set Format",
                                        choices=["%f", "%F", "%e", "%E", "%g", "%G"],
                                        majorDimension=2, style=wx.RA_SPECIFY_COLS)
        self.setincrement3 = wx.Button(self.mainpanel, -1, "Set Increment")
        self.textctrlincr3 = wx.TextCtrl(self.mainpanel, -1, "0.0001")
        self.setfont3 = wx.Button(self.mainpanel, -1, "Set Font")

        self.floatspin4 = FS.FloatSpin(self.mainpanel, -1, min_val=-2, max_val=20000,
                                       increment=0.1, extrastyle=FS.FS_READONLY)
        self.floatspin4.SetFormat("%G")
        self.floatspin4.SetDigits(3)
        
        self.setvalue4 = wx.Button(self.mainpanel, -1, "Set Value")
        self.textctrlvalue4 = wx.TextCtrl(self.mainpanel, -1, "0.0")
        self.setdigits4 = wx.Button(self.mainpanel, -1, "Set Digits")
        self.textctrldigits4 = wx.TextCtrl(self.mainpanel, -1, "3")
        self.radioformat4 = wx.RadioBox(self.mainpanel, -1, "Set Format",
                                        choices=["%f", "%F", "%e", "%E", "%g", "%G"],
                                        majorDimension=2, style=wx.RA_SPECIFY_COLS)
        self.setincrement4 = wx.Button(self.mainpanel, -1, "Set Increment")
        self.textctrlincr4 = wx.TextCtrl(self.mainpanel, -1, "0.1")
        self.setfont4 = wx.Button(self.mainpanel, -1, "Set Font")

        self.valuebuttons = [self.setvalue1, self.setvalue2, self.setvalue3,
                             self.setvalue4]
        self.digitbuttons = [self.setdigits1, self.setdigits2, self.setdigits3,
                             self.setdigits4]
        self.radioboxes = [self.radioformat1, self.radioformat2, self.radioformat3,
                           self.radioformat4]
        self.incrbuttons = [self.setincrement1, self.setincrement2, self.setincrement3,
                           self.setincrement4]
        self.fontbuttons = [self.setfont1, self.setfont2, self.setfont3, self.setfont4]
        self.textvalues = [self.textctrlvalue1, self.textctrlvalue2, self.textctrlvalue3,
                           self.textctrlvalue4]
        self.textdigits = [self.textctrldigits1, self.textctrldigits2, self.textctrldigits3,
                           self.textctrldigits4]
        self.textincr = [self.textctrlincr1, self.textctrlincr2, self.textctrlincr3,
                         self.textctrlincr4]
        self.floatspins = [self.floatspin1, self.floatspin2, self.floatspin3,
                           self.floatspin4]

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.OnSetValue, self.setvalue1)
        self.Bind(wx.EVT_BUTTON, self.OnSetDigits, self.setdigits1)
        self.Bind(wx.EVT_RADIOBOX, self.OnChangeFormat, self.radioformat1)
        self.Bind(wx.EVT_BUTTON, self.OnSetIncrement, self.setincrement1)
        self.Bind(wx.EVT_BUTTON, self.OnSetFont, self.setfont1)
        self.Bind(wx.EVT_BUTTON, self.OnSetValue, self.setvalue2)
        self.Bind(wx.EVT_BUTTON, self.OnSetDigits, self.setdigits2)
        self.Bind(wx.EVT_RADIOBOX, self.OnChangeFormat, self.radioformat2)
        self.Bind(wx.EVT_BUTTON, self.OnSetIncrement, self.setincrement2)
        self.Bind(wx.EVT_BUTTON, self.OnSetFont, self.setfont2)
        self.Bind(wx.EVT_BUTTON, self.OnSetValue, self.setvalue3)
        self.Bind(wx.EVT_BUTTON, self.OnSetDigits, self.setdigits3)
        self.Bind(wx.EVT_RADIOBOX, self.OnChangeFormat, self.radioformat3)
        self.Bind(wx.EVT_BUTTON, self.OnSetIncrement, self.setincrement3)
        self.Bind(wx.EVT_BUTTON, self.OnSetFont, self.setfont3)
        self.Bind(wx.EVT_BUTTON, self.OnSetValue, self.setvalue4)
        self.Bind(wx.EVT_BUTTON, self.OnSetDigits, self.setdigits4)
        self.Bind(wx.EVT_RADIOBOX, self.OnChangeFormat, self.radioformat4)
        self.Bind(wx.EVT_BUTTON, self.OnSetIncrement, self.setincrement4)
        self.Bind(wx.EVT_BUTTON, self.OnSetFont, self.setfont4)

        self.floatspin1.Bind(FS.EVT_FLOATSPIN, self.OnFloatSpin)
        self.floatspin2.Bind(FS.EVT_FLOATSPIN, self.OnFloatSpin)
        self.floatspin3.Bind(FS.EVT_FLOATSPIN, self.OnFloatSpin)
        self.floatspin4.Bind(FS.EVT_FLOATSPIN, self.OnFloatSpin)
        

    def __set_properties(self):
        
        self.helptext.SetFont(wx.Font(10, wx.MODERN, wx.NORMAL, wx.BOLD, 0, "Verdana"))
        self.radioformat1.SetSelection(0)
        self.radioformat2.SetSelection(2)
        self.radioformat3.SetSelection(0)
        self.radioformat4.SetSelection(5)
        

    def __do_layout(self):
        
        mainsizer = wx.BoxSizer(wx.VERTICAL)
        panelsizer = wx.BoxSizer(wx.VERTICAL)
        sizer_6 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_8 = wx.StaticBoxSizer(self.sizer_8_staticbox, wx.HORIZONTAL)
        right4 = wx.BoxSizer(wx.VERTICAL)
        subright43 = wx.BoxSizer(wx.HORIZONTAL)
        subright42 = wx.BoxSizer(wx.HORIZONTAL)
        subright41 = wx.BoxSizer(wx.HORIZONTAL)
        bottomright2 = wx.BoxSizer(wx.VERTICAL)
        sizer_7 = wx.StaticBoxSizer(self.sizer_7_staticbox, wx.HORIZONTAL)
        right3 = wx.BoxSizer(wx.VERTICAL)
        subright33 = wx.BoxSizer(wx.HORIZONTAL)
        subright32 = wx.BoxSizer(wx.HORIZONTAL)
        subright31 = wx.BoxSizer(wx.HORIZONTAL)
        bottomleft2 = wx.BoxSizer(wx.VERTICAL)
        sizer_3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_5 = wx.StaticBoxSizer(self.sizer_5_staticbox, wx.HORIZONTAL)
        right2 = wx.BoxSizer(wx.VERTICAL)
        subright23 = wx.BoxSizer(wx.HORIZONTAL)
        subright22 = wx.BoxSizer(wx.HORIZONTAL)
        subright21 = wx.BoxSizer(wx.HORIZONTAL)
        topright2 = wx.BoxSizer(wx.VERTICAL)
        sizer_4 = wx.StaticBoxSizer(self.sizer_4_staticbox, wx.HORIZONTAL)
        right1 = wx.BoxSizer(wx.VERTICAL)
        subright13 = wx.BoxSizer(wx.HORIZONTAL)
        subright12 = wx.BoxSizer(wx.HORIZONTAL)
        subright11 = wx.BoxSizer(wx.HORIZONTAL)
        topleft2 = wx.BoxSizer(wx.VERTICAL)
        panelsizer.Add(self.helptext, 0, wx.ALL|wx.ADJUST_MINSIZE, 10)
        topleft2.Add((0, 1), 1, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        label_1 = wx.StaticText(self.mainpanel, -1, "FS_LEFT")
        topleft2.Add(label_1, 0, wx.BOTTOM|wx.ALIGN_CENTER_HORIZONTAL|
                     wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 5)
        topleft2.Add(self.floatspin1, 0, wx.ALIGN_CENTER_HORIZONTAL|
                     wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 0)
        topleft2.Add((0, 1), 1, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        sizer_4.Add(topleft2, 0, wx.LEFT|wx.RIGHT|wx.EXPAND, 5)
        subright11.Add(self.setvalue1, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|
                       wx.ADJUST_MINSIZE | wx.BOTTOM, 3)
        subright11.Add(self.textctrlvalue1, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.ALIGN_CENTER_HORIZONTAL|
                       wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 3)
        right1.Add((0,1), 1, wx.EXPAND)
        right1.Add(subright11, 0, wx.EXPAND, 0)
        subright12.Add(self.setdigits1, 0, wx.ALIGN_CENTER_HORIZONTAL|
                       wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 0)
        subright12.Add(self.textctrldigits1, 1, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_HORIZONTAL|
                       wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 3)
        right1.Add(subright12, 0, wx.EXPAND, 0)
        right1.Add(self.radioformat1, 0, wx.ALL|wx.EXPAND|wx.ADJUST_MINSIZE, 3)
        right1.Add((0, 5), 0, wx.ADJUST_MINSIZE, 0)
        subright13.Add(self.setincrement1, 0, wx.ALIGN_CENTER_HORIZONTAL|
                       wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 0)
        subright13.Add(self.textctrlincr1, 1, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_HORIZONTAL|
                       wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 3)
        right1.Add(subright13, 0, wx.EXPAND, 0)        
        right1.Add((0, 5), 0, wx.ADJUST_MINSIZE, 0)
        right1.Add(self.setfont1, 0, wx.LEFT|wx.TOP|wx.BOTTOM|wx.ADJUST_MINSIZE, 3)
        right1.Add((0,1), 1, wx.EXPAND)
        sizer_4.Add(right1, 1, wx.EXPAND, 0)
        sizer_3.Add(sizer_4, 1, wx.ALL|wx.EXPAND, 5)
        topright2.Add((0, 1), 1, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        label_2 = wx.StaticText(self.mainpanel, -1, "FS_RIGHT")
        topright2.Add(label_2, 0, wx.BOTTOM|wx.ALIGN_CENTER_HORIZONTAL|
                      wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 5)
        topright2.Add(self.floatspin2, 0, wx.ALIGN_CENTER_HORIZONTAL|
                      wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 0)
        topright2.Add((0, 1), 1, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        sizer_5.Add(topright2, 0, wx.LEFT|wx.RIGHT|wx.EXPAND, 5)
        subright21.Add(self.setvalue2, 0, wx.ALIGN_CENTER_HORIZONTAL|
                       wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE | wx.BOTTOM, 3)
        subright21.Add(self.textctrlvalue2, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|
                       wx.ALIGN_CENTER_HORIZONTAL|
                       wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 3)
        right2.Add((0,1), 1, wx.EXPAND)
        right2.Add(subright21, 0, wx.EXPAND, 0)
        subright22.Add(self.setdigits2, 0, wx.ALIGN_CENTER_HORIZONTAL|
                       wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 0)
        subright22.Add(self.textctrldigits2, 1, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_HORIZONTAL|
                       wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 3)
        right2.Add(subright22, 0, wx.EXPAND, 0)
        right2.Add(self.radioformat2, 0, wx.ALL|wx.EXPAND|wx.ADJUST_MINSIZE, 3)
        right2.Add((0, 5), 0, wx.ADJUST_MINSIZE, 0)
        subright23.Add(self.setincrement2, 0, wx.ALIGN_CENTER_HORIZONTAL|
                       wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 0)
        subright23.Add(self.textctrlincr2, 1, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_HORIZONTAL|
                       wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 3)
        right2.Add(subright23, 0, wx.EXPAND, 0)     
        right2.Add((0, 5), 0, wx.ADJUST_MINSIZE, 0)
        right2.Add(self.setfont2, 0, wx.LEFT|wx.TOP|wx.BOTTOM|wx.ADJUST_MINSIZE, 3)
        right2.Add((0,1), 1, wx.EXPAND)
        sizer_5.Add(right2, 1, wx.EXPAND, 0)
        sizer_3.Add(sizer_5, 1, wx.ALL|wx.EXPAND, 5)
        panelsizer.Add(sizer_3, 1, wx.EXPAND, 0)
        bottomleft2.Add((0, 1), 1, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        label_3 = wx.StaticText(self.mainpanel, -1, "FS_CENTER")
        bottomleft2.Add(label_3, 0, wx.BOTTOM|wx.ALIGN_CENTER_HORIZONTAL|
                        wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 5)
        bottomleft2.Add(self.floatspin3, 0, wx.ALIGN_CENTER_HORIZONTAL|
                        wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 0)
        bottomleft2.Add((0, 1), 1, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        sizer_7.Add(bottomleft2, 0, wx.LEFT|wx.RIGHT|wx.EXPAND, 5)
        subright31.Add(self.setvalue3, 0, wx.ALIGN_CENTER_HORIZONTAL|
                       wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE | wx.BOTTOM, 3)
        subright31.Add(self.textctrlvalue3, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|
                       wx.ALIGN_CENTER_HORIZONTAL|
                       wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 3)
        right3.Add(subright31, 0, wx.EXPAND, 0)
        subright32.Add(self.setdigits3, 0, wx.ALIGN_CENTER_HORIZONTAL|
                       wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 0)
        subright32.Add(self.textctrldigits3, 1, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_HORIZONTAL|
                       wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 3)
        right3.Add((0,1), 1, wx.EXPAND)
        right3.Add(subright32, 0, wx.EXPAND, 0)
        right3.Add(self.radioformat3, 0, wx.ALL|wx.EXPAND|wx.ADJUST_MINSIZE, 3)
        right3.Add((0, 5), 0, wx.ADJUST_MINSIZE, 0)
        subright33.Add(self.setincrement3, 0, wx.ALIGN_CENTER_HORIZONTAL|
                       wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 0)
        subright33.Add(self.textctrlincr3, 1, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_HORIZONTAL|
                       wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 3)
        right3.Add(subright33, 0, wx.EXPAND, 0)     
        right3.Add((0, 5), 0, wx.ADJUST_MINSIZE, 0)
        right3.Add(self.setfont3, 0, wx.LEFT|wx.TOP|wx.BOTTOM|wx.ADJUST_MINSIZE, 3)
        right3.Add((0,1), 1, wx.EXPAND)
        sizer_7.Add(right3, 1, wx.EXPAND, 0)
        sizer_6.Add(sizer_7, 1, wx.ALL|wx.EXPAND, 5)
        bottomright2.Add((0, 1), 1, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        label_4 = wx.StaticText(self.mainpanel, -1, "FS_READONLY")
        bottomright2.Add(label_4, 0, wx.BOTTOM|wx.ALIGN_CENTER_HORIZONTAL|
                         wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 5)
        bottomright2.Add(self.floatspin4, 0, wx.ALIGN_CENTER_HORIZONTAL|
                         wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 0)
        bottomright2.Add((0, 1), 1, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        sizer_8.Add(bottomright2, 0, wx.LEFT|wx.RIGHT|wx.EXPAND, 5)
        subright41.Add(self.setvalue4, 0, wx.ALIGN_CENTER_HORIZONTAL|
                       wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE | wx.BOTTOM, 3)
        subright41.Add(self.textctrlvalue4, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|
                       wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|
                       wx.ADJUST_MINSIZE, 3)
        right4.Add((0,1), 1, wx.EXPAND)
        right4.Add(subright41, 0, wx.EXPAND, 0)
        subright42.Add(self.setdigits4, 0, wx.ALIGN_CENTER_HORIZONTAL|
                       wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 0)
        subright42.Add(self.textctrldigits4, 1, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_HORIZONTAL|
                       wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 3)
        right4.Add(subright42, 0, wx.EXPAND, 0)
        right4.Add(self.radioformat4, 0, wx.ALL|wx.EXPAND|wx.ADJUST_MINSIZE, 3)
        right4.Add((0, 5), 0, wx.ADJUST_MINSIZE, 0)
        subright43.Add(self.setincrement4, 0, wx.ALIGN_CENTER_HORIZONTAL|
                       wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 0)
        subright43.Add(self.textctrlincr4, 1, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_HORIZONTAL|
                       wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 3)
        right4.Add(subright43, 0, wx.EXPAND, 0)     
        right4.Add((0, 5), 0, wx.ADJUST_MINSIZE, 0)
        right4.Add(self.setfont4, 0, wx.LEFT|wx.TOP|wx.BOTTOM|wx.ADJUST_MINSIZE, 3)
        right4.Add((0,1), 1, wx.EXPAND)
        sizer_8.Add(right4, 1, wx.EXPAND, 0)
        sizer_6.Add(sizer_8, 1, wx.ALL|wx.EXPAND, 5)
        panelsizer.Add(sizer_6, 1, wx.EXPAND, 0)
        self.mainpanel.SetAutoLayout(True)
        self.mainpanel.SetSizer(panelsizer)
        panelsizer.Fit(self.mainpanel)
        panelsizer.SetSizeHints(self.mainpanel)
        mainsizer.Add(self.mainpanel, 1, wx.EXPAND, 0)
        self.SetAutoLayout(True)
        self.SetSizer(mainsizer)
        mainsizer.Fit(self)
        mainsizer.SetSizeHints(self)
        self.Layout()


    def CreateMenuBar(self):

        file_menu = wx.Menu()
        
        AS_EXIT = wx.NewId()        
        file_menu.Append(AS_EXIT, "&Exit")
        self.Bind(wx.EVT_MENU, self.OnClose, id=AS_EXIT)

        help_menu = wx.Menu()

        AS_ABOUT = wx.NewId()        
        help_menu.Append(AS_ABOUT, "&About...")
        self.Bind(wx.EVT_MENU, self.OnAbout, id=AS_ABOUT)

        menu_bar = wx.MenuBar()

        menu_bar.Append(file_menu, "&File")
        menu_bar.Append(help_menu, "&Help")        

        return menu_bar        


    def OnClose(self, event):
        
        self.Destroy()


    def OnAbout(self, event):

        msg = "This Is The About Dialog Of The FloatSpin Demo.\n\n" + \
              "Author: Andrea Gavana @ 16 Nov 2005\n\n" + \
              "Please Report Any Bug/Requests Of Improvements\n" + \
              "To Me At The Following Adresses:\n\n" + \
              "andrea.gavana@agip.it\n" + "andrea_gavana@tin.it\n\n" + \
              "Welcome To wxPython " + wx.VERSION_STRING + "!!"
              
        dlg = wx.MessageDialog(self, msg, "FloatSpin Demo",
                               wx.OK | wx.ICON_INFORMATION)
        
        dlg.SetFont(wx.Font(8, wx.NORMAL, wx.NORMAL, wx.NORMAL, False, "Verdana"))
        dlg.ShowModal()
        dlg.Destroy()
        

    def OnSetValue(self, event):

        btn = event.GetEventObject()
        indx = self.valuebuttons.index(btn)
        textctrl = self.textvalues[indx]
        floatspin = self.floatspins[indx]

        try:
            value = float(textctrl.GetValue().strip())
        except:
            errstr = "Error: Non Floating Value For The Text Control! "
            dlg = wx.MessageDialog(self, errstr, "FloatSpinDemo Error",
                                   wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return

        floatspin.SetValue(value)
        
        event.Skip()
        

    def OnSetDigits(self, event):

        btn = event.GetEventObject()
        indx = self.digitbuttons.index(btn)
        textctrl = self.textdigits[indx]
        floatspin = self.floatspins[indx]

        try:
            value = int(textctrl.GetValue().strip())
        except:
            errstr = "Error: Non Integer Value For The Text Control! "
            dlg = wx.MessageDialog(self, errstr, "FloatSpinDemo Error",
                                   wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return

        floatspin.SetDigits(value)
        
        event.Skip()
        

    def OnChangeFormat(self, event):

        radio = event.GetEventObject()
        indx = self.radioboxes.index(radio)
        floatspin = self.floatspins[indx]

        fmt = radio.GetStringSelection()
        floatspin.SetFormat(fmt)
        
        event.Skip()
        

    def OnSetIncrement(self, event):

        btn = event.GetEventObject()
        indx = self.incrbuttons.index(btn)
        textctrl = self.textincr[indx]
        floatspin = self.floatspins[indx]

        try:
            value = float(textctrl.GetValue().strip())
        except:
            errstr = "Error: Non Floating Value For The Text Control! "
            dlg = wx.MessageDialog(self, errstr, "FloatSpinDemo Error",
                                   wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return

        try:
            floatspin.SetIncrement(value)
        except:
            textctrl.DiscardEdits()
            strs = sys.exc_info()
            dlg = wx.MessageDialog(self, strs[0], "FloatSpinDemo Error",
                                   wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return
        
        event.Skip()


    def OnSetFont(self, event):

        btn = event.GetEventObject()
        indx = self.fontbuttons.index(btn)
        floatspin = self.floatspins[indx]
        
        data = wx.FontData()
        data.EnableEffects(True)
        data.SetInitialFont(floatspin.GetFont())

        dlg = wx.FontDialog(self, data)
        
        if dlg.ShowModal() == wx.ID_OK:
            data = dlg.GetFontData()
            font = data.GetChosenFont()
            colour = data.GetColour()
            floatspin.SetFont(font)
            floatspin.GetTextCtrl().SetForegroundColour(colour)
            floatspin.Refresh()
        
        # Don't destroy the dialog until you get everything you need from the
        # dialog!
        dlg.Destroy()
        

    def OnFloatSpin(self, event):

        floatspin = event.GetEventObject()
        indx = self.floatspins.index(floatspin)

        fmt = floatspin.GetFormat()
        dgt = floatspin.GetDigits()
        currenttext = self.textvalues[indx]

        strs = ("%100." + str(dgt) + fmt[1])%floatspin.GetValue()
        
        currenttext.SetValue(strs.strip())
        currenttext.Refresh()
    

if __name__ == "__main__":
    
    app = wx.PySimpleApp(0)

    frame = FloatSpinDemo(None, -1, "Float Spin Demo ;-)")
    frame.CenterOnScreen()

    app.SetTopWindow(frame)

    frame.Show()
    
    app.MainLoop()
