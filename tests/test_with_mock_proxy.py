from typing import OrderedDict
# import sys
# sys.path.append('../src/')
from ophyd_tango_devices.tango_devices import *
from ophyd_tango_devices.signals import *

import unittest
import asyncio
from PyTango import DeviceProxy, DevFailed  # type: ignore
from PyTango.asyncio import DeviceProxy as AsyncDeviceProxy
from ophyd.v2.core import CommsConnector
from bluesky import RunEngine
from bluesky.run_engine import call_in_bluesky_event_loop
from typing import OrderedDict
import random
import bluesky.plan_stubs as bps
from bluesky.plans import count, scan
from bluesky.callbacks import LiveTable, LivePlot
import bluesky.utils

RE = RunEngine()

class MotorTestMockDeviceProxy(unittest.IsolatedAsyncioTestCase):
    '''Replaces the (Async)DeviceProxy object with the MockDeviceProxy class, so makes no outside calls to the network for Tango commands'''
    #may be a complication in creating a new RunEngine. Have to close the first one perhaps?

    #why wont sim mode work in unittests...
    def setUp(self):
        self.dev_name = "mock/device/name"
        # self.dev_name = "motor/motctrl01/1"
        with CommsConnector(sim_mode=True):
            self.test_motor = motor(self.dev_name, "test_motor")

    def test_instantiate_motor(self):
        pass

    def test_motor_readable(self):
        reading = call_in_bluesky_event_loop(self.test_motor.read())
        assert isinstance(reading, dict)

    def test_motor_config_writable(self):
        rand_number = random.random() 
        _, new_reading = call_in_bluesky_event_loop(self.test_motor.configure("velocity", rand_number))
        assert new_reading["test_motor-velocity"]['value'] == rand_number
    
    async def test_cant_set_non_config_attributes(self):
        rand_number = random.random()
        with self.assertRaises(KeyError):
            await self.test_motor.configure("position", rand_number)
        #this should complain, can't set slow settable (like a motor) attributes like this

    def test_read_in_RE(self):
        RE(bps.rd(self.test_motor))

    def test_count_in_RE(self):
        RE(count([self.test_motor],1), print)

    def test_count_in_RE_with_callback_named_attribute(self):
        RE(count([self.test_motor],1), LiveTable(["test_motor-position"]))

    def test_motor_bluesky_movable(self):
        rand_number = random.random() + 1.0
        call_in_bluesky_event_loop(self.test_motor.configure('velocity', 1000))
        RE(bps.mv(self.test_motor, rand_number))
    
    async def test_motor_scans(self):
        rand_number = random.random() + 1.0
        RE(scan([],self.test_motor,0,rand_number,2), LiveTable(["test_motor-position"]))
        currentPos = await self.test_motor.read()
        assert currentPos['test_motor-position']['value'] == rand_number, "Final position does not equal set number"

# del RE
#not sure what the deal is with "1 comm not connected ... NoneType object is not iterable"
#think it's to do with connecttherest