"""
This module defines the device classes to be used to connect to and control the Hexapod PUNA from
Symétrie.

"""

import time
from datetime import datetime
from datetime import timedelta

from egse.device import DeviceConnectionState
from egse.device import DeviceInterface
from egse.hexapod import HexapodError
from egse.hexapod.symetrie import logger
from egse.hexapod.symetrie import pmac
from egse.hexapod.symetrie.alpha import AlphaControllerInterface
from egse.hexapod.symetrie.hexapod import HexapodSimulator
from egse.hexapod.symetrie.pmac import PMACError
from egse.hexapod.symetrie.pmac import PmacEthernetInterface
from egse.hexapod.symetrie.pmac import decode_Q29
from egse.proxy import Proxy
from egse.registry.client import RegistryClient
from egse.settings import Settings
from egse.zmq_ser import connect_address

DEVICE_SETTINGS = Settings.load(filename="puna.yaml")

NUM_OF_DECIMALS = 6  # used for rounding numbers before sending to PMAC


class PunaInterface(AlphaControllerInterface, DeviceInterface):
    """
    Interface definition for the PunaController, the PunaProxy and the PunaSimulator.
    """


class PunaController(PunaInterface):
    """
    The PunaController class allows controlling a Symétrie PUNA Hexapod through an Ethernet
    interface that is connecting a Symétrie Controller.

    The Symétrie Controller can be either in simulation mode or have a real Hexapod
    connected.

    **Synopsis**

        from egse.hexapod.symetrie.puna import PunaController
        hexapod = PunaController(hostname="10.33.178.145", port=1025)
        try:
            hexapod.connect()

            # do some useful things here with the hexapod

        except HexapodError as exc:
            print(exc)
        finally:
            hexapod.disconnect()

    The constructor also sets the connection parameters and tries to connect
    to the controller. Make sure that you explicitly use the hexapod.disconnect()
    command when no connection is needed anymore.

    The controller can also be used as a context manager, in which case the `connect()`
    and `disconnect()` methods should not be called:

        with PunaController() as puna:
            puna.info()

    """

    SPEC_POS_MAINTENANCE = 0
    """Hexapod specific position, for maintenance or Jog only."""
    SPEC_POS_ZERO = 1
    """Hexapod zero position."""
    SPEC_POS_RETRACTED = 2
    """Hexapod retracted position."""

    def __init__(self, hostname=None, port=None):
        """
        Opens a TCP/IP socket connection with the Hexapod PUNA Hardware Controller.

        Args:
            hostname (str): the IP address or fully qualified hostname of the Hexapod hardware
            controller.
                The default is defined in the ``settings.yaml`` configuration file.

            port (int): the IP port number to connect to, by default set in the ``settings.yaml``
            configuration file.

        Raises:
            HexapodError: when the connection could not be established for some reason.
        """

        super().__init__()

        if hostname is None or port is None:
            raise ValueError(f"Please provide both hostname and port for the PunaController, {hostname=}, {port=}")

        logger.debug(f"Initializing PunaController with hostname={hostname} on port={port}")

        try:
            self.pmac = PmacEthernetInterface()
            self.pmac.setConnectionParameters(hostname, port)
        except PMACError as exc:
            logger.warning(
                f"HexapodError: Couldn't establish connection with the Hexapod PUNA Hardware Controller: ({exc})"
            )

    def is_simulator(self):
        return False

    def is_connected(self):
        return self.pmac.isConnected()

    def connect(self):
        try:
            self.pmac.connect()
        except PMACError as exc:
            logger.warning(f"PMACError caught: Couldn't establish connection ({exc})")
            raise ConnectionError("Couldn't establish a connection with the Hexapod.") from exc

        self.notify_observers(DeviceConnectionState.DEVICE_CONNECTED)

    def disconnect(self):
        try:
            self.pmac.disconnect()
        except PMACError as exc:
            raise ConnectionError("Couldn't disconnect from Hexapod.") from exc

        self.notify_observers(DeviceConnectionState.DEVICE_NOT_CONNECTED)

    def reconnect(self):
        if self.is_connected():
            self.disconnect()
        self.connect()

    def is_in_position(self):
        try:
            out = self.pmac.getQVars(36, [0], int)
        except PMACError as exc:
            raise HexapodError("Couldn't retrieve information from Hexapod PUNA Hardware Controller.") from exc
        return bool(out[0] & 0x04)

    def info(self):
        try:
            msg = "Info about the Hexapod PUNA:\n"
            msg += f"model   = {self.pmac.getPmacModel()}\n"
            msg += f"CID     = {self.pmac.getCID()}\n"
            msg += f"version = {self.pmac.getVersion()}\n"
            msg += f"cpu     = {self.pmac.getCPU()}\n"
            msg += f"type    = {self.pmac.getType()}\n"
            msg += f"vendorID= {self.pmac.getVID()}\n"
            msg += f"date    = {self.pmac.getDate()}\n"
            msg += f"time    = {self.pmac.getTime()}\n"
            msg += f"today   = {self.pmac.getToday()}\n"
        except PMACError as exc:
            raise HexapodError("Couldn't retrieve information from Hexapod PUNA Hardware Controller.") from exc

        return msg

    def stop(self):
        try:
            rc = self.pmac.sendCommand(pmac.CMD_STOP)
        except PMACError as exc:
            raise HexapodError("Couldn't complete the STOP command.") from exc

        return rc

    def homing(self):
        try:
            rc = self.pmac.sendCommand(pmac.CMD_HOMING)
        except PMACError as exc:
            raise HexapodError("Couldn't complete the HOMING command.") from exc

        logger.info("Homing: Command was successful")

        return rc

    def is_homing_done(self):
        try:
            rc = self.pmac.getQVars(26, [0], int)[0]
        except PMACError as pmac_exc:
            logger.error(f"PMAC Exception: {pmac_exc}", exc_info=True)
            return False

        msg = {  # noqa: F841
            0: "Homing status is undefined.",
            1: "Homing is in progress",
            2: "Homing is done",
            3: "An error occurred during the Homing process.",
        }

        if rc == 2:
            return True

        return False

    def set_virtual_homing(self, tx, ty, tz, rx, ry, rz):
        try:
            rc = self.pmac.sendCommand(pmac.CMD_VIRTUAL_HOMING, tx=tx, ty=ty, tz=tz, rx=rx, ry=ry, rz=rz)
        except PMACError as exc:
            raise HexapodError("Couldn't execute the virtual homing command.") from exc

        logger.warning(
            f"Virtual Homing successfully set to {tx:.6f}, {ty:.6f}, {tz:.6f}, {rx:.6f}, {ry:.6f}, {rz:.6f}."
        )

        return rc

    def activate_control_loop(self):
        try:
            rc = self.pmac.sendCommand(pmac.CMD_CONTROLON)
        except PMACError as exc:
            raise HexapodError("Couldn't activate the control loop.") from exc

        msg = {  # noqa: F841
            0: "Command was successful",
            -1: "Command was ignored",
            -2: "Control of the servo motors has failed",
        }

        return rc

    def deactivate_control_loop(self):
        try:
            rc = self.pmac.sendCommand(pmac.CMD_CONTROLOFF)
        except PMACError as exc:
            raise HexapodError("Couldn't de-activate the control loop.") from exc

        return rc

    def __move(self, cm, tx, ty, tz, rx, ry, rz):
        """
        Ask the controller to perform the movement defined by the arguments.

        For all control modes cm, the rotation centre coincides with the Object
        Coordinates System origin and the movements are controlled with translation
        components at first (Tx, Ty, tZ) and then the rotation components (Rx, Ry, Rz).

        Control mode cm:
            * 0 = absolute control, object coordinate system position and orientation
                    expressed in the invariant user coordinate system
            * 1 = object relative, motion expressed in the Object Coordinate System
            * 2 = user relative, motion expressed in the User Coordinate System

        Args:
            cm (int): control mode
            tx (float): position on the X-axis [mm]
            ty (float): position on the Y-axis [mm]
            tz (float): position on the Z-axis [mm]
            rx (float): rotation around the X-axis [deg]
            ry (float): rotation around the Y-axis [deg]
            rz (float): rotation around the Z-axis [deg]

        Returns:
            0 on success, -1 when ignored, -2 on error.

        Raises:
            PMACError: when the arguments do not match up or when there is a time out or when
            there is a socket
            communication error.

        .. note:: When the command was not successful, this method will query the ``POSVALID?``
                  using the checkAbsolutePosition() and print a summary of the error messages
                  to the log file.
        """

        rc = self.pmac.sendCommand(pmac.CMD_MOVE, cm=cm, tx=tx, ty=ty, tz=tz, rx=rx, ry=ry, rz=rz)

        error_code_msg = {
            0: "Command was successful",
            -1: "Command was ignored",
            -2: "Command was invalid, check with POSVALID?",
        }

        if rc < 0:
            msg = f"Move command returned ({rc}: {error_code_msg[rc]})."

            if rc == -2:
                Q29, errors = self.__check_movement(cm, tx, ty, tz, rx, ry, rz)

                msg += "\nError messages returned from POSVALID?:\n"
                for key, value in errors.items():
                    msg += f"  bit {key:<2d}: {value}\n"

            logger.debug(msg)

        return rc

    def __check_movement(self, cm, tx, ty, tz, rx, ry, rz):
        """
        Ask the controller if the movement defined by the arguments is feasible.

        Returns a tuple where the first element is an integer that represents the
        bitfield encoding the errors. The second element is a dictionary with the
        bit numbers that were (on) and the corresponding error description.

        Args:
            tx (float): position on the X-axis [mm]
            ty (float): position on the Y-axis [mm]
            tz (float): position on the Z-axis [mm]
            rx (float): rotation around the X-axis [deg]
            ry (float): rotation around the Y-axis [deg]
            rz (float): rotation around the Z-axis [deg]

        """
        out = self.pmac.sendCommand(pmac.CMD_POSVALID_GET, cm=cm, tx=tx, ty=ty, tz=tz, rx=rx, ry=ry, rz=rz)
        Q29 = decode_Q29(out[0])
        return out[0], Q29

    def move_absolute(self, tx, ty, tz, rx, ry, rz):
        try:
            rc = self.__move(0, tx, ty, tz, rx, ry, rz)
        except PMACError as exc:
            raise HexapodError("Couldn't execute the moveAbsolute command.") from exc

        return rc

    def check_absolute_movement(self, tx, ty, tz, rx, ry, rz):
        return self.__check_movement(0, tx, ty, tz, rx, ry, rz)

    def move_relative_object(self, tx, ty, tz, rx, ry, rz):
        try:
            rc = self.__move(1, tx, ty, tz, rx, ry, rz)
        except PMACError as exc:
            raise HexapodError("Couldn't execute the relative movement [object] command.") from exc

        return rc

    def check_relative_object_movement(self, tx, ty, tz, rx, ry, rz):
        return self.__check_movement(1, tx, ty, tz, rx, ry, rz)

    def move_relative_user(self, tx, ty, tz, rx, ry, rz):
        try:
            rc = self.__move(2, tx, ty, tz, rx, ry, rz)
        except PMACError as exc:
            raise HexapodError("Couldn't execute the relative movement [user] command.") from exc

        return rc

    def check_relative_user_movement(self, tx, ty, tz, rx, ry, rz):
        return self.__check_movement(2, tx, ty, tz, rx, ry, rz)

    def perform_maintenance(self, axis):
        try:
            rc = self.pmac.sendCommand(pmac.CMD_MAINTENANCE, axis=axis)
        except PMACError as exc:
            raise HexapodError("Couldn't perform maintenance cycle.") from exc

        msg = {0: "Command was successfully executed", -1: "Command was ignored"}  # noqa: F841

        return rc

    def goto_specific_position(self, pos):
        try:
            rc = self.pmac.sendCommand(pmac.CMD_SPECIFICPOS, pos=pos)
        except PMACError as exc:
            raise HexapodError(f"Couldn't goto specific position [pos={pos}].") from exc

        msg = {
            0: "Command was successfully executed",
            -1: "Command was ignored",
            -2: "Invalid movement command",
        }

        logger.info(f"Goto Specific Position [{pos}]: {msg[rc]}")

        if rc < 0:
            try:
                out = self.pmac.getQVars(0, [29], int)
            except PMACError as exc:
                raise HexapodError("Couldn't get a response from the Hexapod controller.") from exc
            Q29 = decode_Q29(out[0])

            msg = "Error messages returned in Q29:\n"
            for key, value in Q29.items():
                msg += f"  {key:2d}: {value}\n"

            logger.debug(msg)

        return rc

    def goto_retracted_position(self):
        try:
            rc = self.pmac.sendCommand(pmac.CMD_SPECIFICPOS, pos=self.SPEC_POS_RETRACTED)
        except PMACError as exc:
            raise HexapodError("Couldn't goto retracted position.") from exc

        msg = {
            0: "Command was successfully executed",
            -1: "Command was ignored",
            -2: "Invalid movement command",
        }

        logger.info(f"Goto Retracted Position [2]: {msg[rc]}")

        if rc < 0:
            try:
                out = self.pmac.getQVars(0, [29], int)
            except PMACError as exc:
                raise HexapodError("Couldn't get a response from the Hexapod controller.") from exc
            Q29 = decode_Q29(out[0])

            msg = "Error messages returned in Q29:\n"
            for key, value in Q29.items():
                msg += f"  {key:2d}: {value}\n"

            logger.debug(msg)

        return rc

    def goto_zero_position(self):
        try:
            rc = self.pmac.sendCommand(pmac.CMD_SPECIFICPOS, pos=self.SPEC_POS_ZERO)
        except PMACError as exc:
            raise HexapodError("Couldn't goto zero position.") from exc

        msg = {
            0: "Command was successfully executed",
            -1: "Command was ignored",
            -2: "Invalid movement command",
        }

        logger.info(f"Goto Zero Position [1]: {msg[rc]}")

        if rc < 0:
            try:
                out = self.pmac.getQVars(0, [29], int)
            except PMACError as exc:
                raise HexapodError("Couldn't get a response from the Hexapod controller.") from exc
            Q29 = decode_Q29(out[0])

            msg = "Error messages returned in Q29:\n"
            for key, value in Q29.items():
                msg += f"  {key:2d}: {value}\n"

            logger.debug(msg)

        return rc

    def get_buffer(self):
        return_string = self.pmac.getBuffer()
        return return_string

    def clear_error(self):
        try:
            rc = self.pmac.sendCommand(pmac.CMD_CLEARERROR)
        except PMACError as exc:
            raise HexapodError("Couldn't clear errors in the controller software.") from exc

        return rc

    def jog(self, axis: int, inc: float) -> int:
        if not (1 <= axis <= 6):
            logger.error(f"The axis argument must be 1 <= axis <= 6, given {axis}.")
            raise HexapodError("Illegal Argument Value: axis is {axis}, should be 1 <= axis <= 6.")

        try:
            rc = self.pmac.sendCommand(pmac.CMD_JOG, axis=axis, inc=inc)
        except PMACError as exc:
            raise HexapodError(f"Couldn't execute the jog command for axis={axis} with inc={inc} [mm].") from exc

        msg = {0: "Command was successfully executed", -1: "Command was ignored"}

        logger.info(f"JOG on axis [{axis}] of {inc} mm: {msg[rc]}")

        return rc

    def configure_coordinates_systems(self, tx_u, ty_u, tz_u, rx_u, ry_u, rz_u, tx_o, ty_o, tz_o, rx_o, ry_o, rz_o):
        try:
            rc = self.pmac.sendCommand(
                pmac.CMD_CFG_CS,
                tx_u=round(tx_u, NUM_OF_DECIMALS),
                ty_u=round(ty_u, NUM_OF_DECIMALS),
                tz_u=round(tz_u, NUM_OF_DECIMALS),
                rx_u=round(rx_u, NUM_OF_DECIMALS),
                ry_u=round(ry_u, NUM_OF_DECIMALS),
                rz_u=round(rz_u, NUM_OF_DECIMALS),
                tx_o=round(tx_o, NUM_OF_DECIMALS),
                ty_o=round(ty_o, NUM_OF_DECIMALS),
                tz_o=round(tz_o, NUM_OF_DECIMALS),
                rx_o=round(rx_o, NUM_OF_DECIMALS),
                ry_o=round(ry_o, NUM_OF_DECIMALS),
                rz_o=round(rz_o, NUM_OF_DECIMALS),
            )
        except PMACError as exc:
            raise HexapodError("Couldn't configure coordinate systems on the hexapod controller.") from exc

        return rc

    def get_coordinates_systems(self):
        try:
            out = self.pmac.sendCommand(pmac.CMD_CFG_CS_GET)
        except PMACError as exc:
            raise HexapodError("Couldn't get the coordinate systems information from the hexapod controller.") from exc

        return out

    def get_debug_info(self):
        try:
            out = self.pmac.sendCommand(pmac.CMD_STATE_DEBUG_GET)
        except PMACError as exc:
            raise HexapodError("Couldn't get the debugging information from the hexapod controller.") from exc

        return out

    def set_speed(self, vt, vr):
        try:
            rc = self.pmac.sendCommand(pmac.CMD_CFG_SPEED, vt=vt, vr=vr)
        except PMACError as exc:
            raise HexapodError("Couldn't set the speed for translation [{vt} mm/s] or rotation [{vr} deg/s].") from exc

        return rc

    def get_speed(self):
        try:
            out = self.pmac.sendCommand(pmac.CMD_CFG_SPEED_GET)
        except PMACError as exc:
            raise HexapodError("Couldn't get the speed settings from the hexapod controller.") from exc

        return out

    def get_general_state(self):
        try:
            out = self.pmac.getQVars(36, [0], int)
        except PMACError as pmac_exc:
            logger.error(f"PMAC Exception: {pmac_exc}", exc_info=True)
            return None

        return out[0], pmac.decode_Q36(out[0])

    def get_actuator_state(self):
        try:
            out = self.pmac.getQVars(30, [0, 1, 2, 3, 4, 5], int)
        except PMACError as pmac_exc:
            logger.error(f"PMAC Exception: {pmac_exc}", exc_info=True)
            return None

        return [pmac.decode_Q30(value) for value in out]

    def get_user_positions(self):
        try:
            # out = self.pmac.getQVars(53, [0, 1, 2, 3, 4, 5], float)
            out = self.pmac.sendCommand(pmac.CMD_POSUSER_GET)
        except PMACError as pmac_exc:
            logger.error(f"PMAC Exception: {pmac_exc}", exc_info=True)
            return None

        return out

    def get_machine_positions(self):
        try:
            out = self.pmac.getQVars(47, [0, 1, 2, 3, 4, 5], float)
        except PMACError as pmac_exc:
            logger.error(f"PMAC Exception: {pmac_exc}", exc_info=True)
            return None

        return out

    def get_actuator_length(self):
        try:
            out = self.pmac.getQVars(41, [0, 1, 2, 3, 4, 5], float)
        except PMACError as pmac_exc:
            logger.error(f"PMAC Exception: {pmac_exc}", exc_info=True)
            return None

        return out

    def reset(self, wait=True, verbose=False):
        try:
            self.pmac.sendCommand(pmac.CMD_RESETSOFT)
        except PMACError as exc:
            raise HexapodError("Couldn't (soft) reset the hexapod controller.") from exc

        # How do I know when the RESETSOFT has finished and we can send further commands?

        if wait:
            logger.info("Sent a soft reset, this will take about 30 seconds to complete.")
            self.__wait(30, verbose=verbose)

    def __wait(self, duration, verbose=False):
        """
        Wait for a specific duration in seconds.
        """
        _timeout = timedelta(seconds=duration)
        _start = datetime.now()

        _rate = timedelta(seconds=5)  # every _rate seconds print a message
        _count = 0

        logger.info(f"Just waiting {duration} seconds ...")

        while datetime.now() - _start < _timeout:
            if verbose and (datetime.now() - _start > _count * _rate):
                _count += 1
                logger.info(f"waited for {_count * _rate} of {_timeout} seconds, ")
                print(f"waited for {_count * _rate} of {_timeout} seconds, ")

            time.sleep(0.01)


class PunaSimulator(HexapodSimulator, DeviceInterface):
    """
    HexapodSimulator simulates the Symétrie Hexapod PUNA. The class is heavily based on the
    ReferenceFrames in the `egse.coordinates` package.

    The simulator implements the same methods as the HexapodController class which acts on the
    real hardware controller in either simulation mode or with a real Hexapod PUNA connected.

    Therefore, the HexapodSimulator can be used instead of the Hexapod class in test harnesses
    and when the hardware is not available.

    This class simulates all the movements and status of the Hexapod.
    """

    def __init__(self):
        super().__init__()


class PunaProxy(Proxy, PunaInterface):
    """The PunaProxy class is used to connect to the control server and send commands to the
    Hexapod PUNA remotely.

    Args:
        protocol: the transport protocol
        hostname: location of the control server (IP address)
        port: TCP port on which the control server is listening for commands

    """

    def __init__(self, protocol: str, hostname: str, port: int):
        super().__init__(connect_address(protocol, hostname, port))

    @classmethod
    def from_identifier(cls, device_id: str):
        with RegistryClient() as reg:
            service = reg.discover_service(device_id)

            if service:
                protocol = service.get("protocol", "tcp")
                hostname = service["host"]
                port = service["port"]

            else:
                raise RuntimeError(f"No service registered as {device_id}")

        logger.info(f"{protocol=}:{hostname=}:{port=}")

        return cls(protocol, hostname, port)
