#!/usr/bin/env python3

"""
  PyPose: Bioloid pose system for arbotiX robocontroller
  Copyright (c) 2008-2010 Michael E. Ferguson.  All right reserved.

  This program is free software; you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation; either version 2 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program; if not, write to the Free Software Foundation,
  Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""

import wx
from pypose import ax12
from .ToolPane import ToolPane

# help phrases
help = ["\rPyPose Terminal V2",
        "\r",
        "\rvalid commands:",
        "\rls - list the servos found on the bus at current baud",
        "\rmv id id2 - rename any servo with ID=id, to id2",
        "\rset param id val - set parameter on servo ID=id to val",
        "\rget param id - get a parameter value from a servo",
        "\rbaud b - set baud rate of bus to b",
        "\r",
        "\rvalid parameters",
        "\rpos - current position of a servo, 0-1023",
        "\rbaud - baud rate",
        "\rtemp - current temperature, degrees C, READ ONLY"]


class shell(wx.TextCtrl):
    """ The actual terminal part. """

    def __init__(self, parent, id=-1, conn=None, font_size=10, encoding="utf-8"):
        self.parent = parent
        self.encoding = encoding
        self.conn = conn
        mono = wx.Font(font_size, wx.FONTFAMILY_MODERN, wx.NORMAL, wx.NORMAL)
        dc = wx.ScreenDC()
        dc.SetFont(mono)
        (cw, ch) = dc.GetTextExtent("X")
        self.cw = cw
        self.ch = ch
        self.cols = 82
        self.rows = 25
        wx.TextCtrl.__init__(self, parent, id, size=(82 * cw + 2, 25 * ch + 2),
                             style=wx.TE_MULTILINE | wx.TE_PROCESS_TAB | wx.TE_PROCESS_ENTER | wx.HSCROLL)

        self.SetFont(mono)
        self.Bind(wx.EVT_CHAR, self.OnEnterChar)

        self.SetValue("PyPose Terminal VA.0\r>> ")
        self.SetInsertionPoint(len(self.GetValue()))

    def OnEnterChar(self, event):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_RETURN:
            # process the command!
            line = self.PositionToXY(self.GetLastPosition())[2]
            l = self.GetLineText(line)[3:].split(" ")
            try:
                if l[0] == "help":   # display help data
                    if len(l) > 1:      # for a particular command
                        if l[1] == "li":
                            self.write(help[3])
                        elif l[1] == "mv":
                            self.write(help[4])
                        elif l[1] == "set":
                            self.write(help[5])
                        elif l[1] == "get":
                            self.write(help[6])
                    else:
                        for h in help:
                            self.write(h)
                elif l[0] == "clear":
                    self.Clear()
                    self.SetValue(">> ")
                    self.SetInsertionPoint(3)
                    return
                elif l[0] == "serial":
                    # open a serial port
                    if self.parent.parent.port is not None:
                        self.parent.parent.port.ser.close()
                    print("Opening port: " + l[1])
                    self.port = self.parent.parent.openPort(str(l[1]))
                elif self.parent.parent.port is None:
                    self.write("\rNo port open!")
                elif l[0] == "ls":      # list servos
                    to = self.parent.parent.port.ser.timeout
                    self.parent.parent.port.ser.timeout = 0.25
                    # baud = 1000000
                    # if len(l) > 1:       # we have a baud too!
                    #    baud = int(l[1])
                    k = 0                # how many id's have we printed...
                    self.write("\r")
                    for i in range(18):
                        if self.parent.parent.port.getReg(i + 1, ax12.P_PRESENT_POSITION_L, 1) != -1:
                            if k > 8:    # limit the width of each printout
                                k = 0
                                self.write("\r")
                            self.write(repr(i + 1).rjust(4))
                            k = k + 1
                            wx.SafeYield()
                    self.parent.parent.port.ser.timeout = to
                elif l[0] == "mv":      # rename a servo
                    if self.parent.parent.port.setReg(int(l[1]), ax12.P_ID, [int(l[2])]) == 0:
                        self.write("\rOK")
                elif l[0] == "baud":    # set bus baud rate
                    if int(l[1]) in self.parent.parent.port.ser.BAUDRATES:
                        self.parent.parent.port.ser.baudrate(int(l[2]))
                    else:
                        self.write("\rERROR : Invalid baudrate")
                elif l[0] == "set":
                    if l[1] == "baud":
                        self.write("\r" + str(self.parent.parent.port.setReg(int(l[2]), ax12.P_BAUD_RATE, [self.convertBaud(int(l[3]))])))
                    elif l[1] == "pos":
                        self.write("\r" + str(self.parent.parent.port.setReg(int(l[2]), ax12.P_PRESENT_POSITION, 2)))
                elif l[0] == "get":
                    if l[1] == "temp":
                        self.write("\r" + str(self.parent.parent.port.getReg(int(l[2]), ax12.P_PRESENT_TEMPERATURE, 2)))
                    elif l[1] == "pos":
                        self.write("\r" + str(self.parent.parent.port.getReg(int(l[2]), ax12.P_PRESENT_POSITION, 2)))
            except ZeroDivisionError:
                self.write("\rERROR : Unrecognized command!")
            # new line!
            self.write("\r>> ")
        elif keycode == wx.WXK_BACK:
            print(self.PositionToXY(self.GetLastPosition())[1])
            if(self.PositionToXY(self.GetLastPosition())[1] > 3):
                self.Remove(self.GetLastPosition() - 1, self.GetLastPosition())
        else:
            self.write(chr(keycode))

    def convertBaud(self, b):
        if b == 500000:
            return 3
        elif b == 400000:
            return 4
        elif b == 250000:
            return 7
        elif b == 200000:
            return 9
        elif b == 115200:
            return 16
        elif b == 57600:
            return 34
        elif b == 19200:
            return 103
        elif b == 9600:
            return 207
        else:
            return 1    # default to 1Mbps


class ArbotixTerminal(ToolPane):
    """ arbotix/bioloid terminal. """

    NAME = "Terminal"
    STATUS = "opened terminal..."

    def __init__(self, parent, port=None):
        ToolPane.__init__(self, parent, port)
        self.term = shell(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.term, 1, wx.EXPAND | wx.ALL, 1)
        self.SetSizer(sizer)
        self.Fit()
        sizer.SetSizeHints(self)
        self.Show(True)
