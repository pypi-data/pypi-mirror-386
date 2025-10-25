# SPDX-FileCopyrightText: All Contributors to the PyTango project
# SPDX-License-Identifier: LGPL-3.0-or-later
from tango import AttrWriteType, DeviceProxy, InfoIt
from tango.server import Device, attribute, command, device_property


class Leader(Device):
    FollowerTRLs = device_property(dtype=(str,))

    @InfoIt(show_args=True)
    @command(dtype_in=int)
    def Turn_Follower_On(self, follower_id):
        follower_trl = self.FollowerTRLs[follower_id - 1]
        follower_device = DeviceProxy(follower_trl)
        follower_device.is_on = True

    @command(dtype_in=int)
    def Turn_Follower_Off(self, follower_id):
        follower_trl = self.FollowerTRLs[follower_id - 1]
        follower_device = DeviceProxy(follower_trl)
        follower_device.is_on = False


class Follower(Device):
    def init_device(self):
        super().init_device()
        self._is_on = False

    is_on = attribute(
        dtype=bool,
        access=AttrWriteType.READ_WRITE,
    )

    @InfoIt(show_ret=True)
    def read_is_on(self):
        return self._is_on

    @InfoIt(show_args=True)
    def write_is_on(self, value):
        self._is_on = value


devices_info = [
    {
        "class": Leader,
        "devices": (
            {
                "name": "device/leader/1",
                "properties": {
                    "FollowerTRLs": ["device/follower/1", "device/follower/2"],
                },
            },
        ),
    },
    {
        "class": Follower,
        "devices": [
            {"name": "device/follower/1", "properties": {}},
            {"name": "device/follower/2", "properties": {}},
        ],
    },
]


class TestLeaderFollowerIntegration:
    def test_leader_turn_follower_on(self, tango_context):
        leader = DeviceProxy("device/leader/1")
        follower_1 = DeviceProxy("device/follower/1")
        follower_2 = DeviceProxy("device/follower/2")

        # check initial state: both followers are off
        assert follower_1.is_on == False
        assert follower_2.is_on == False

        # tell leader to enable follower_1
        leader.turn_follower_on(1)

        # check follower_1 is now on, and follower_2 is still off
        assert follower_1.is_on == True
        assert follower_2.is_on == False

    def test_leader_turn_follower_off(self, tango_context):
        leader = DeviceProxy("device/leader/1")
        follower_1 = DeviceProxy("device/follower/1")
        follower_2 = DeviceProxy("device/follower/2")

        # tell leader to enable both followers
        leader.turn_follower_on(1)
        leader.turn_follower_on(2)

        # check initial state: both followers are on
        assert follower_1.is_on == True
        assert follower_2.is_on == True

        # tell leader to disable follower_1
        leader.turn_follower_off(1)

        # check follower_1 is now off, and follower_2 is still on
        assert follower_1.is_on == False
        assert follower_2.is_on == True
