#!/usr/bin/env python
#   This file is part of nexdatas - Tango Server for NeXus data writer
#
#    Copyright (C) 2012-2017 DESY, Jan Kotanski <jkotan@mail.desy.de>
#
#    nexdatas is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    nexdatas is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with nexdatas.  If not, see <http://www.gnu.org/licenses/>.
# \package test nexdatas
# \file ClientFieldTagAsynchH5PY_test.py
# unittests for field Tags running Tango Server in asynchronous mode
#
import unittest

try:
    import tango
except Exception:
    import PyTango as tango


try:
    from ProxyHelper import ProxyHelper
except Exception:
    from .ProxyHelper import ProxyHelper

try:
    import ServerSetUp
except Exception:
    from . import ServerSetUp

try:
    import ClientFieldTagWriterH5PY_test
except Exception:
    from . import ClientFieldTagWriterH5PY_test

# test fixture


class ClientFieldTagAsynchH5PYTest(
        ClientFieldTagWriterH5PY_test.ClientFieldTagWriterH5PYTest):
    # server counter
    serverCounter = 0

    # constructor
    # \param methodName name of the test method
    def __init__(self, methodName):
        ClientFieldTagWriterH5PY_test.ClientFieldTagWriterH5PYTest.__init__(
            self, methodName)

        ClientFieldTagAsynchH5PYTest.serverCounter += 1
        sins = self.__class__.__name__ + \
            "%s" % ClientFieldTagAsynchH5PYTest.serverCounter
        self._sv = ServerSetUp.ServerSetUp("testp09/testtdw/" + sins, sins)

#        self._counter =  [1, 2]
#        self._fcounter =  [1.1,-2.4,6.54,-8.456,9.456,-0.46545]

        self.__status = {
            tango.DevState.OFF: "Not Initialized",
            tango.DevState.ON: "Ready",
            tango.DevState.OPEN: "File Open",
            tango.DevState.EXTRACT: "Entry Open",
            tango.DevState.RUNNING: "Writing ...",
            tango.DevState.FAULT: "Error",
        }

    def setProp(self, rc, name, value):
        db = tango.Database()
        name = "" + name[0].upper() + name[1:]
        db.put_device_property(
            self._sv.new_device_info_writer.name,
            {name: value})
        rc.Init()

    # test starter
    # \brief Common set up of Tango Server
    def setUp(self):
        self._sv.setUp()
        print("SEED = %s" % self.seed)
        print("CHECKER SEED = %s" % self._sc.seed)

    # test closer
    # \brief Common tear down oif Tango Server
    def tearDown(self):
        self._sv.tearDown()

    # opens writer
    # \param fname file name
    # \param xml XML settings
    # \param json JSON Record with client settings
    # \returns Tango Data Writer proxy instance
    def openWriter(self, fname, xml, json=None):
        tdw = tango.DeviceProxy(self._sv.new_device_info_writer.name)
        self.assertTrue(ProxyHelper.wait(tdw, 10000))
        self.setProp(tdw, "writer", "h5py")
        tdw.FileName = fname
        self.assertEqual(tdw.state(), tango.DevState.ON)
        self.assertEqual(tdw.status(), self.__status[tdw.state()])

        tdw.OpenFile()
        self.assertEqual(tdw.state(), tango.DevState.OPEN)
        self.assertEqual(tdw.status(), self.__status[tdw.state()])

        tdw.XMLSettings = xml
        self.assertEqual(tdw.state(), tango.DevState.OPEN)
        self.assertEqual(tdw.status(), self.__status[tdw.state()])
        if json:
            tdw.JSONRecord = json
        self.assertEqual(tdw.state(), tango.DevState.OPEN)
        self.assertEqual(tdw.status(), self.__status[tdw.state()])
        tdw.OpenEntryAsynch()
        self.assertTrue(ProxyHelper.wait(tdw, 10000))
        self.assertEqual(tdw.state(), tango.DevState.EXTRACT)
        self.assertEqual(tdw.status(), self.__status[tdw.state()])
        return tdw

    # closes writer
    # \param tdw Tango Data Writer proxy instance
    # \param json JSON Record with client settings
    def closeWriter(self, tdw, json=None):
        self.assertEqual(tdw.state(), tango.DevState.EXTRACT)
        self.assertEqual(tdw.status(), self.__status[tdw.state()])

        if json:
            tdw.JSONRecord = json
        self.assertEqual(tdw.state(), tango.DevState.EXTRACT)
        self.assertEqual(tdw.status(), self.__status[tdw.state()])
        tdw.CloseEntryAsynch()
        self.assertTrue(ProxyHelper.wait(tdw, 10000))
        self.assertEqual(tdw.status(), self.__status[tdw.state()])
        self.assertEqual(tdw.state(), tango.DevState.OPEN)

        tdw.CloseFile()
        self.assertEqual(tdw.status(), self.__status[tdw.state()])
        self.assertEqual(tdw.state(), tango.DevState.ON)

    # performs one record step
    def record(self, tdw, string):
        self.assertEqual(tdw.status(), self.__status[tdw.state()])
        self.assertEqual(tdw.state(), tango.DevState.EXTRACT)
        tdw.RecordAsynch(string)
        self.assertTrue(ProxyHelper.wait(tdw, 10000))
        self.assertEqual(tdw.state(), tango.DevState.EXTRACT)
        self.assertEqual(tdw.status(), self.__status[tdw.state()])


if __name__ == '__main__':
    unittest.main()
