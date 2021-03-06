#!/usr/bin/env python3

"""
  PyPose: for all things related to PyPose projects
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


class Pose(list):
    """Class to hold a pose."""
    def __init__(self, line, length):
        # now load the name, positions for this pose
        try:
            for servo in range(length):
                if line.find(",") > 0:
                    self.append(int(line[0:line.index(",")]))
                else:
                    self.append(int(line[0:]))
                line = line[line.index(",") + 1:]
        # we may not have enough data, so dump it
        except BaseException:
            for i in range(length - len(self)):
                self.append(512)

    def __str__(self):
        return ", ".join([str(p) for p in self])


class Sequence(list):
    """
    Class to hold a sequence.

    First element is name, rest are (pose,time) pairs
    """
    def __init__(self, line=None):
        # load the name, (pose,time) pairs for this sequence
        try:
            if line is None:
                return
            while True:
                if line.find(",") > 0:
                    self.append(line[0:line.index(",")].strip().rstrip())
                elif line != "":
                    self.append(line.strip().rstrip())
                line = line[line.index(",") + 1:]
        except BaseException:
            pass

    def __str__(self):
        return ", ".join([str(t) for t in self])


class Project:
    """Class for dealing with project files."""
    def __init__(self):
        self.name = ""
        self.count = 18
        self.resolution = [1024 for i in range(self.count)]
        self.poses = dict()
        self.sequences = dict()
        self.nuke = ""
        self.save = False

    def load(self, filename):
        self.poses = dict()
        self.sequences = dict()
        prjFile = open(filename, "r").readlines()
        # load robot name and servo count
        self.name = prjFile[0].split(":")[0]
        self.count = int(prjFile[0].split(":")[1])
        # load resolution of each servo in count
        self.resolution = [int(x) for x in prjFile[0].split(":")[2:]]
        if len(self.resolution) != self.count:
            self.resolution = [1024 for x in range(self.count)]
        # load poses and sequences
        for line in prjFile[1:]:
            if line[0:5] == "Pose=":
                self.poses[line[5:line.index(":")]] = Pose(
                    line[line.index(":") + 1:].rstrip(), self.count)
            elif line[0:4] == "Seq=":
                self.sequences[line[4:line.index(":")]] = (
                    Sequence(line[line.index(":") + 1:].rstrip()))
            elif line[0:5] == "Nuke=":
                self.nuke = line[5:].rstrip()
            # these next two lines can be removed later, once everyone is moved to Ver 0.91
            else:
                self.poses[line[0:line.index(":")]] = Pose(
                    line[line.index(":") + 1:].rstrip(), self.count)
        self.save = False

    def saveFile(self, filename):
        with open(filename, "w") as prjFile:
            prjFile.write(self.name + ":" + str(self.count) + ":" + ":".join([str(x) for x in self.resolution]) + '\n')
            for p in self.poses.keys():
                prjFile.write("Pose=" + p + ":" + str(self.poses[p]) + '\n')
            for s in self.sequences.keys():
                prjFile.write("Seq=" + s + ": " + str(self.sequences[s]) + '\n')
            if self.nuke != "":
                prjFile.write("Nuke=" + self.nuke + '\n')
        self.save = False

    def new(self, nName, nCount, nResolution):
        self.poses = dict()
        self.sequences = dict()
        self.filename = ""
        self.count = nCount
        self.name = nName
        self.resolution = [nResolution for i in range(self.count)]
        self.save = True

    def export(self, filename):
        """ Export a pose file for use with Sanguino Library. """
        poses = ""
        poses += "#ifndef " + self.name.upper() + "_POSES" + '\n'
        poses += "#define " + self.name.upper() + "_POSES" + '\n\n'
        poses += "#include <avr/pgmspace.h>\n\n"
        for p in self.poses.keys():
            if p.startswith("ik_"):
                continue
            poses += "PROGMEM prog_uint16_t " + p + "[] = {" + str(self.count) + ",\n"
            p = self.poses[p]
            for x in p[0:-1]:
                poses += str(x) + ",\n"
            poses += str(p[-1]) + "};\n\n"
        for s in self.sequences.keys():
            poses += "PROGMEM transition_t " + s + "[] = {{0," + str(len(self.sequences[s])) + "}\n"
            s = self.sequences[s]
            for t in s:
                poses += ",{" + t[0:t.find("|")] + "," + t[t.find("|") + 1:] + "}\n"
            poses += "};\n\n"
        poses += "#endif\n"
        with open(filename, "w") as posefile:
            posefile.write(poses)


def extract(li):
    """ extract x%256,x>>8 for every x in li """
    out = list()
    for i in li:
        out = out + [i % 256, i >> 8]
    return out
