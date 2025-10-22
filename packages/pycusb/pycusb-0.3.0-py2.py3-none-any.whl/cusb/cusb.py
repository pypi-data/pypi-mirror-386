import sys

import serial


# The hub reports a firmware version. This code was only tested with the following
# versions. If you find a different version that works fine, lmk.
WORKING_FIRMWARE_VERSIONS = [
    "CENTOS000104v04",  # e.g., EXSYS EX-1504HMS (@gschwaer)
    "CENTOS000207v02",  # e.g., StarTech 5G7AINDRM-USB-A-HUB (@ajfite)
]


class CUsb:

    def __init__(self, path: str, password: str = "pass", force: bool = False):
        """Initialize the CUsb interface

        This will not yet connect to the interface. For that use a resource allocator.

        Example:

          with CUsb(path_to_device) as hub:
              # do something with the hub

        Args:
            path (str): Path or COM port of the serial device controlling the hub.
            password (str, optional): Password for the hub. Defaults to "pass", which is
                                      the factory default.
            force (bool, optional): Continue even if the firmware version is unexpected.
        """
        self.path = path
        # password is padded with spaces to exactly 8 byte
        self.password = "{:<8}".format(password)
        self.force = force

    def __enter__(self):
        self.s = serial.Serial(self.path, timeout=1)
        resp = self._send_cmd("?Q")
        if resp not in WORKING_FIRMWARE_VERSIONS:
            message = f"Unknown firmware version: {resp}"
            if self.force:
                print(
                    f"{message}. Continuing because --force was specified.",
                    file=sys.stderr,
                )
            else:
                raise RuntimeError(f"{message} (check --help for --force)")
        return self

    def __exit__(self, type, value, traceback):  # type: ignore
        self.s.close()

    def _deserialize_port_states(self, text: str):
        assert len(text) == 8
        text = (
            text[6]
            + text[7]
            + text[4]
            + text[5]
            + text[2]
            + text[3]
            + text[0]
            + text[1]
        )
        return int(text, 16)

    def _serialize_port_states(self, value: int):
        assert value >= 0 and value < (1 << 32)
        text = "{:08X}".format(value)
        text = (
            text[6]
            + text[7]
            + text[4]
            + text[5]
            + text[2]
            + text[3]
            + text[0]
            + text[1]
        )
        return text

    def _get_port_states(self):
        resp = self._send_cmd("GP")
        return self._deserialize_port_states(resp)

    def _set_port_states(self, states: int):
        query = self._serialize_port_states(states)
        resp = self._send_cmd("SP" + self.password + query)
        assert resp[0] == "G"
        return self._deserialize_port_states(resp[1:])

    def _send_cmd(self, cmd: str):
        # clear read buffer
        self.s.read_all()

        self.s.write(bytes(cmd, encoding="ascii") + b"\r")

        line = self.s.read_until()

        resp = str(line, encoding="ascii")
        assert resp.endswith("\r\n")

        resp = resp.strip("\n").strip("\r")
        assert "\r" not in resp and "\n" not in resp

        return resp

    # Example - switch port 3 off:
    # Sent:      'GP'        'SPpass    FBFFFFFF'
    # Received:     'FFFFFFFF'                  'GFBFFFFFF'
    def port_power_on(self, port: int, on: bool):
        current_states = self._get_port_states()

        if on:
            requested_states = current_states | (1 << (port - 1))
        else:
            requested_states = current_states & ~(1 << (port - 1))

        if requested_states == current_states:
            # nothing to do
            return

        current_states = self._set_port_states(requested_states)
        assert current_states == requested_states

    def port_power_is_on(self, port: int) -> bool:
        current_states = self._get_port_states()

        return current_states & (1 << (port - 1)) != 0

    def save_current_state_as_default(self):
        resp = self._send_cmd("WP" + self.password)
        assert resp == "G"

    def factory_reset(self):
        resp = self._send_cmd("RD" + self.password)
        assert resp == "G"

    def reset(self):
        self.s.write(bytes("RH" + self.password + "\r", encoding="ascii"))
