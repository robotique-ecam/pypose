#!/usr/bin/env python3

"""
  PyPose: Bioloid pose system for ArbotiX robocontroller
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
from pypose import project
from .ToolPane import ToolPane


class PoseEditor(ToolPane):
    """Editor for the capture and creation of poses. """
    BT_DELTA_T = wx.NewIdRef()
    BT_RELAX = wx.NewIdRef()
    BT_RELAX_ID = wx.NewIdRef()
    BT_CAPTURE = wx.NewIdRef()
    BT_SET = wx.NewIdRef()
    BT_POSE_ADD = wx.NewIdRef()
    BT_POSE_ADV = wx.NewIdRef()
    BT_POSE_REM = wx.NewIdRef()
    BT_POSE_RENAME = wx.NewIdRef()
    ID_POSE_BOX = wx.NewIdRef()

    NAME = "Pose editor"
    STATUS = "Please create or select a sequence to edit..."

    def __init__(self, parent, port=None):
        ToolPane.__init__(self, parent, port)
        self.curpose = ""
        self.saveReq = False
        self.live = self.parent.live.IsChecked()

        sizer = wx.GridBagSizer(10, 10)

        # pose editor, goes in a box:
        temp = wx.StaticBox(self, -1, 'edit pose')
        temp.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD))
        editBox = wx.StaticBoxSizer(temp, orient=wx.VERTICAL)
        poseEditSizer = wx.GridBagSizer(5, 5)
        # build servo editors
        self.servos = list()  # the editors in the window
        for i in range(self.parent.project.count):
            temp = wx.Panel(self, -1)
            hbox = wx.BoxSizer(wx.HORIZONTAL)
            if (i + 1) < 10:
                temp.enable = wx.CheckBox(temp, i, "ID 0" + str(i + 1))
            else:
                temp.enable = wx.CheckBox(temp, i, "ID " + str(i + 1))
            temp.enable.SetValue(True)
            temp.position = wx.Slider(
                temp, i, 512, 0, self.parent.project.resolution[i] - 1, wx.DefaultPosition, (200, -1), wx.SL_HORIZONTAL | wx.SL_LABELS)
            hbox.Add(temp.enable)
            hbox.Add(temp.position)
            temp.SetSizer(hbox)
            # multiple columns now:
            if i < self.parent.columns:
                poseEditSizer.Add(temp, (0, i), wx.GBSpan(1, 1), wx.TOP, 10)
            else:
                poseEditSizer.Add(
                    temp, (i / self.parent.columns, i % self.parent.columns))
            temp.Disable()  # servo editors start out disabled, enabled only when a pose is selected
            self.servos.append(temp)
        # grid it
        editBox.Add(poseEditSizer)
        sizer.Add(editBox, (0, 0), wx.GBSpan(1, 1), wx.EXPAND)

        # list of poses
        self.posebox = wx.ListBox(self, self.ID_POSE_BOX, choices=[*self.parent.project.poses])
        sizer.Add(self.posebox, (0, 1), wx.GBSpan(1, 1), wx.EXPAND)
        # and add/remove
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(wx.Button(self, self.BT_POSE_ADD, 'add'))
        hbox.Add(wx.Button(self, self.BT_POSE_REM, 'remove'))
        hbox.Add(wx.Button(self, self.BT_POSE_RENAME, 'rename'))
        sizer.Add(hbox, (1, 1), wx.GBSpan(1, 1), wx.ALIGN_CENTER)

        # toolbar
        toolbar = wx.Panel(self, -1)
        toolbarsizer = wx.BoxSizer(wx.HORIZONTAL)
        #  delta-T for interpolation
        self.deltaTButton = wx.Button(toolbar, self.BT_DELTA_T, 'delta-T')
        self.deltaTButton.Disable()
        toolbarsizer.Add(self.deltaTButton, 1)
        self.deltaT = 500
        if port is not None and port.hasInterpolation:
            self.deltaTButton.Enable()
        toolbarsizer.Add(wx.Button(toolbar, self.BT_RELAX, 'relax'), 1)
        toolbarsizer.Add(wx.Button(toolbar, self.BT_CAPTURE, 'capture'), 1)
        toolbarsizer.Add(wx.Button(toolbar, self.BT_SET, 'set'), 1)
        toolbar.SetSizer(toolbarsizer)
        sizer.Add(toolbar, (1, 0), wx.GBSpan(1, 1), wx.ALIGN_CENTER)

        self.Bind(wx.EVT_SLIDER, self.updatePose)
        self.Bind(wx.EVT_CHECKBOX, self.relaxServo)
        self.Bind(wx.EVT_BUTTON, self.parent.doRelax, self.BT_RELAX)
        self.Bind(wx.EVT_BUTTON, self.capturePose, self.BT_CAPTURE)
        self.Bind(wx.EVT_BUTTON, self.setPose, self.BT_SET)
        self.Bind(wx.EVT_BUTTON, self.addPose, self.BT_POSE_ADD)
        self.Bind(wx.EVT_BUTTON, self.remPose, self.BT_POSE_REM)
        self.Bind(wx.EVT_BUTTON, self.renamePose, self.BT_POSE_RENAME)
        self.Bind(wx.EVT_BUTTON, self.doDeltaT, self.BT_DELTA_T)
        self.Bind(wx.EVT_LISTBOX, self.doPose, self.ID_POSE_BOX)

        # key accelerators
        aTable = wx.AcceleratorTable([(wx.ACCEL_CTRL,  ord('S'), self.BT_CAPTURE),  # capture Servos
                                      (wx.ACCEL_CTRL, ord('R'),
                                       self.BT_RELAX),     # Relax
                                      (wx.ACCEL_CTRL, ord('A'),
                                       self.BT_POSE_ADV),  # Advance
                                      ])
        self.SetAcceleratorTable(aTable)
        self.Bind(wx.EVT_MENU, self.capturePose, id=self.BT_CAPTURE)
        self.Bind(wx.EVT_MENU, self.parent.doRelax, id=self.BT_RELAX)
        self.Bind(wx.EVT_MENU, self.advancePose, id=self.BT_POSE_ADV)

        self.SetSizerAndFit(sizer)

    def updatePose(self, e=None):
        """Save updates to a pose, do live update if neeeded."""
        if self.curpose != "":
            self.parent.project.poses[self.curpose][e.GetId()] = e.GetInt()
            self.parent.project.save = True
            # live update
            if self.live and self.servos[e.GetId()].enable.IsChecked():
                pos = e.GetInt()
                self.port.setReg(
                    e.GetId() + 1, ax12.P_GOAL_POSITION_L, [pos % 256, pos >> 8])

    def relaxServo(self, e=None):
        """ Relax or enable a servo. """
        servo = e.GetId() + 1
        checked = e.IsChecked()
        if checked:
            self.port.setReg(servo, ax12.P_TORQUE_ENABLE, [1])
        else:
            self.port.setReg(servo, ax12.P_TORQUE_ENABLE, [0])

    def loadPose(self, posename):
        if self.curpose == "":   # if we haven't yet, enable servo editors
            for servo in self.servos:
                servo.Enable()
        self.curpose = posename
        for servo in range(self.parent.project.count):
            self.servos[servo].position.SetValue(
                self.parent.project.poses[self.curpose][servo])
        self.parent.sb.SetStatusText('now editing pose: ' + self.curpose, 0)
        self.parent.project.save = True

    def doPose(self, e=None):
        """ Load a pose into the slider boxes. """
        if e.IsSelection():
            self.loadPose(str(e.GetString()))

    def capturePose(self, e=None):
        """ Downloads the current pose from the robot to the GUI. """
        if self.port is not None:
            if self.curpose != "":
                print("Capturing pose...")
                errors = "could not read servos: "
                errCount = 0.0
                dlg = wx.ProgressDialog(
                    "capturing pose", "this may take a few seconds, please wait...", self.parent.project.count + 1)
                dlg.Update(1)
                for servo in range(self.parent.project.count):
                    pos = self.port.getReg(servo + 1, ax12.P_PRESENT_POSITION_L, 2)
                    if pos != -1 and len(pos) > 1:
                        self.servos[servo].position.SetValue(
                            pos[0] + (pos[1] << 8))
                    else:
                        errors = errors + str(servo + 1) + ", "
                        errCount = errCount + 1.0
                    if self.curpose != "":
                        self.parent.project.poses[self.curpose][servo] = self.servos[servo].position.GetValue(
                        )
                    val = servo + 2
                    dlg.Update(val)
                if errors != "could not read servos: ":
                    self.parent.sb.SetStatusText(errors[0:-2], 0)
                    # if we are failing a lot, raise the timeout
                    if errCount / self.parent.project.count > 0.1 and self.parent.port.ser.timeout < 10:
                        self.parent.port.ser.timeout = self.parent.port.ser.timeout * 2.0
                        print("Raised timeout threshold to ",
                              self.parent.port.ser.timeout)
                else:
                    self.parent.sb.SetStatusText("captured pose!", 0)
                dlg.Destroy()
                self.parent.project.save = True
            else:
                self.parent.sb.SetBackgroundColour('RED')
                self.parent.sb.SetStatusText("Please Select a Pose", 0)
                self.parent.timer.Start(20)
        else:
            self.parent.sb.SetBackgroundColour('RED')
            self.parent.sb.SetStatusText("No Port Open", 0)
            self.parent.timer.Start(20)

    def setPose(self, e=None):
        """ Write a pose out to the robot. """
        if self.port is not None:
            if self.curpose != "":
                # update pose in project
                for servo in range(self.parent.project.count):
                    self.parent.project.poses[self.curpose][servo] = self.servos[servo].position.GetValue(
                    )
                print("Setting pose...")
                if self.port.hasInterpolation:  # lets do this smoothly!
                    # set pose size -- IMPORTANT!
                    print("Setting pose size at", self.parent.project.count)
                    self.port.execute(253, 7, [self.parent.project.count])
                    # download the pose
                    self.port.execute(
                        253, 8, [0] + project.extract(self.parent.project.poses[self.curpose]))
                    self.port.execute(
                        253, 9, [0, self.deltaT % 256, self.deltaT >> 8, 255, 0, 0])
                    self.port.execute(253, 10, list())
                else:
                    # aww shucks...
                    # curPose = list() TODO: should we use a syncWrite here?
                    for servo in range(self.parent.project.count):
                        pos = self.servos[servo].position.GetValue()
                        self.port.setReg(
                            servo + 1, ax12.P_GOAL_POSITION_L, [pos % 256, pos >> 8])
                        self.parent.project.poses[self.curpose][servo] = self.servos[servo].position.GetValue(
                        )
                    #    pos = self.servos[servo].position.get()
                    #    curPose.append( (servo+1, pos%256, pos>>8) )
                    # self.pose.syncWrite(P_GOAL_POSITION_L, curPose)
            else:
                self.parent.sb.SetBackgroundColour('RED')
                self.parent.sb.SetStatusText("Please Select a Pose", 0)
                self.parent.timer.Start(20)
        else:
            self.parent.sb.SetBackgroundColour('RED')
            self.parent.sb.SetStatusText("No Port Open", 0)
            self.parent.timer.Start(20)

    def addPose(self, e=None):
        """ Add a new pose. """
        if self.parent.project.name != "":
            dlg = wx.TextEntryDialog(self, 'Pose Name:', 'New Pose Settings')
            dlg.SetValue("")
            if dlg.ShowModal() == wx.ID_OK:
                self.posebox.Append(dlg.GetValue())
                self.parent.project.poses[dlg.GetValue()] = project.Pose(
                    "", self.parent.project.count)
                dlg.Destroy()
            self.parent.project.save = True
        else:
            dlg = wx.MessageDialog(
                self, 'Please create a new robot first.', 'Error', wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()

    def advancePose(self, e=None):
        """ Create a new pose, with a default name. """
        if self.parent.project.name != "":
            i = 0
            while True:
                if "pose" + str(i) in self.parent.project.poses:
                    i = i + 1
                else:
                    break
            # have name, create pose
            self.parent.project.poses["pose" + str(i)] = project.Pose("", self.parent.project.count)
            self.posebox.Append("pose" + str(i))
            # select pose
            self.loadPose("pose" + str(i))
            self.posebox.SetSelection(self.posebox.FindString("pose" + str(i)))

    def renamePose(self, e=None):
        """ Rename a pose. """
        if self.curpose != "":
            dlg = wx.TextEntryDialog(self, 'Name of pose:', 'Rename Pose')
            dlg.SetValue(self.curpose)
            if dlg.ShowModal() == wx.ID_OK:
                # rename in project data
                newName = dlg.GetValue()
                self.parent.project.poses[newName] = self.parent.project.poses[self.curpose]
                del self.parent.project.poses[self.curpose]
                v = self.posebox.FindString(self.curpose)
                self.posebox.Delete(v)
                self.posebox.Insert(newName, v)
                self.posebox.SetSelection(v)
                self.curpose = newName
                self.parent.project.save = True

    def remPose(self, e=None):
        """ Remove a pose. """
        if self.curpose != "":
            dlg = wx.MessageDialog(self, 'Are you sure you want to delete this pose?',
                                   'Confirm', wx.OK | wx.CANCEL | wx.ICON_EXCLAMATION)
            if dlg.ShowModal() == wx.ID_OK:
                v = self.posebox.FindString(self.curpose)
                del self.parent.project.poses[self.curpose]
                self.posebox.Delete(v)
                self.curpose = ""
                dlg.Destroy()
                for servo in self.servos:   # disable editors if we have no pose selected
                    servo.Disable()
            self.parent.sb.SetStatusText(
                "please create or select a pose to edit...", 0)
            self.parent.project.save = True

    def doDeltaT(self, e=None):
        """ Adjust delta-T variable """
        dlg = wx.TextEntryDialog(
            self, 'Enter time in mS:', 'Adjust Interpolation time')
        dlg.SetValue(str(self.deltaT))
        if dlg.ShowModal() == wx.ID_OK:
            print("Adjusting delta-T:", dlg.GetValue())
            self.deltaT = int(dlg.GetValue())
            dlg.Destroy()

    def portUpdated(self):
        """ Adjust delta-T button """
        if self.port is not None and self.port.hasInterpolation:
            self.deltaTButton.Enable()
        else:
            self.deltaTButton.Disable()
