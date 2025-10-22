import argparse
import copy
import os
import traceback
from collections import namedtuple
from io import TextIOWrapper
from unittest import mock

import ophyd
from bec_lib.atlas_models import Device as DeviceModel
from bec_lib.bec_yaml_loader import yaml_load

from ophyd_devices.utils.bec_device_base import BECDevice

try:
    from bec_server.device_server.devices.devicemanager import DeviceManagerDS as device_manager
except ImportError:
    device_manager = None

TestResult = namedtuple("TestResult", ["name", "success", "message"])


class StaticDeviceAnalysisError(Exception):
    """Error class for static device analysis"""


class StaticDeviceTest:
    """Class to perform tests on an ophyd device config file."""

    def __init__(
        self,
        output_file: TextIOWrapper | None = None,
        config_file: str | None = None,
        config_dict: dict[str, dict] | None = None,
    ) -> None:
        """
        Initialize the StaticDeviceTest class. Either output_file or config_dict must be provided.
        Config_file will have precedence over config_dict.
        Args:
            config(str): path to the config file
            config_dict(dict): device configuration dictionary. Same formatting as in device_manager
            output_file(TextIOWrapper): file to write the output to
        """
        if config_file is not None:
            self.config_file = config_file
            self.config = self.read_config(config_file)
        else:
            if config_dict is None:
                raise ValueError("Either config or config_dict must be provided.")
            self.config = config_dict
            self.config_file = ""
        self.file = output_file

    @staticmethod
    def read_config(config) -> dict:
        """
        Read the config file

        Args:
            config(str): path to the config file

        Returns:
            dict: config content
        """
        content = yaml_load(config)
        return content

    def _check_all_signals_of_device(self, name: str, device: ophyd.Device) -> None:
        """
        Check if all signals of the device that are not omitted are configured with auto_monitor=True

        Args:
            name(str): name of the device
            device(ophyd.Device): device object
        """
        for _, sub_name, item in device.walk_components():
            if not issubclass(item.cls, ophyd.signal.EpicsSignalBase):
                continue
            if not item.is_signal:
                continue
            if not item.kind == ophyd.Kind.omitted:
                continue
            # check if auto_monitor is in kwargs
            self._has_auto_monitor(f"{name}/{sub_name}", item.kwargs)

    def _check_epics_motor(self, name: str, config: dict) -> None:
        """
        Check if the epics motor config is valid.

        Args:
            name(str): name of the device
            config(dict): device config
        """
        if "prefix" in config["deviceConfig"]:
            return
        msg_suffix = ""

        # check if the device specifies a read_pv instead of a prefix.
        # This is a common copy-paste error.
        if "read_pv" in config["deviceConfig"]:
            msg_suffix = "Maybe a typo? The device specifies a read_pv instead."
        raise ValueError(f"{name}: does not specify the prefix. {msg_suffix}")

    def _check_epics_signal(self, name: str, config: dict) -> None:
        """
        Check if the epics signal config is valid. The device must specify a read_pv.

        Args:
            name(str): name of the device
            config(dict): device config
        """
        self._has_auto_monitor(name, config["deviceConfig"])
        if "read_pv" not in config["deviceConfig"]:
            raise ValueError(f"{name}: does not specify the read_pv")

    def check_device_classes(self, name: str, conf: dict) -> int:
        """
        Run checks on the device class

        Args:
            name(str): name of the device
            conf(dict): device config

        Returns:
            int: 0 if all checks passed, 1 otherwise
        """
        try:
            dev_class = device_manager._get_device_class(conf["deviceClass"])

            if issubclass(dev_class, ophyd.EpicsMotor):
                self._check_epics_motor(name, conf)
                return 0

            if issubclass(dev_class, ophyd.signal.EpicsSignalBase):
                self._check_epics_signal(name, conf)
                return 0

            if issubclass(dev_class, ophyd.Device):
                self._check_all_signals_of_device(name, dev_class)
            return 0

        except Exception as e:
            self.print_and_write(f"ERROR: {name} is not valid: {e}")
            return 1

    def _has_auto_monitor(self, name: str, config: dict) -> None:
        """
        Check if the config has an auto_monitor key and print a warning if not.

        Args:
            name(str): name of the device
            config(dict): device config
        """
        if "auto_monitor" not in config:
            self.print_and_write(f"WARNING: Device {name} is configured without auto monitor.")

    def connect_device(
        self, name: str, conf: dict, force_connect: bool = False, timeout_per_device: float = 30
    ) -> int:
        """
        Connect to the device

        Args:
            name(str): name of the device
            conf(dict): device config
            force_connect(bool): force connection to all signals even if devices report .connected = True. Default is False.
            timeout_per_device(float): timeout for each device connection. Default is 30 seconds.

        Returns:
            int: 0 if all checks passed, 1 otherwise
        """
        try:
            conf_in = copy.deepcopy(conf)
            conf_in["name"] = name
            obj, _ = device_manager.construct_device_obj(conf_in, None)

            device_manager.connect_device(
                obj, wait_for_all=True, timeout=timeout_per_device, force=force_connect
            )
            assert obj.connected is True
            self.check_basic_ophyd_methods(obj)
            obj.destroy()
            if hasattr(obj, "component_names") and obj.component_names:
                assert obj.connected is False
                assert obj._destroyed is True
            return 0

        except Exception:
            content = traceback.format_exc()
            self.print_and_write(f"ERROR: {name} is not connectable: {content}")
            return 1

    def check_basic_ophyd_methods(self, obj: ophyd.OphydObject) -> int:
        """
        Check if the basic ophyd methods work

        Args:
            obj(ophyd.OphydObject): device object

        Returns:

        """
        assert isinstance(obj, BECDevice)
        assert isinstance(obj.name, str)
        assert isinstance(obj.read(), dict)
        assert isinstance(obj.read_configuration(), dict)
        assert isinstance(obj.describe(), dict)
        assert isinstance(obj.describe_configuration(), dict)
        assert isinstance(obj.hints, dict)

    def validate_schema(self, name: str, conf: dict) -> None:
        """
        Validate the device config against the BEC device model

        Args:
            name(str): name of the device
            conf(dict): device config
        """
        try:
            db_config = self._translate_to_db_config(name, conf)
            DeviceModel(**db_config)
            return 0
        except Exception as e:
            self.print_and_write(f"ERROR: {name} is not valid: {e}")
            return 1

    @staticmethod
    def _translate_to_db_config(name, config) -> dict:
        """
        Translate the device config to a db config

        Args:
            name(str): name of the device
            config(dict): device config

        Returns:
            dict: db config
        """
        db_config = copy.deepcopy(config)
        db_config["name"] = name
        if "deviceConfig" in db_config and db_config["deviceConfig"] is None:
            db_config["deviceConfig"] = {}
        db_config.pop("deviceType", None)
        return db_config

    def run(
        self, connect: bool, force_connect: bool = False, timeout_per_device: float = 30
    ) -> None:
        """
        Run the tests

        Args:
            connect(bool): connect to the devices
            force_connect(bool): force connection to all signals even if devices report .connected = True. Default is False.
            timeout_per_device(float): timeout for each device connection. Default is 30 seconds.
        """
        failed_devices = []
        for name, conf in self.config.items():
            return_val = 0
            self.print_and_write(f"Checking {name}...")
            return_val += self.validate_schema(name, conf)
            return_val += self.check_device_classes(name, conf)
            if connect:
                return_val += self.connect_device(
                    name, conf, force_connect=force_connect, timeout_per_device=timeout_per_device
                )

            if return_val == 0:
                self.print_and_write("OK")
            else:
                self.print_and_write("FAILED")
                failed_devices.append(name)

        self.print_and_write("\n\n")
        self.print_and_write("========================================")
        # print summary
        self.print_and_write("Summary:")
        if len(failed_devices) == 0:
            print("All devices passed the test.")
            self.file.write("All devices passed the test.\n")
        else:
            print(f"{len(failed_devices)} devices failed the test:")
            self.file.write(f"{len(failed_devices)} devices failed the test:\n")
            for device in failed_devices:
                print(f"    {device}")
                self.file.write(f"    {device}\n")
            raise StaticDeviceAnalysisError(
                f"The following devices failed the test in {self.config_file}: {failed_devices}. Check the report for more details."
            )

    def print_and_write(self, text: str) -> None:
        """
        Print and write to the output file

        Args:
            text(str): text to print and write
        """
        print(text)
        if self.file is not None:  # Write only if no output file is provided
            self.file.write(text + "\n")

    def run_with_list_output(
        self, connect: bool = False, force_connect: bool = False, timeout_per_device: float = 30
    ) -> list[TestResult]:
        """
        Run the tests and return a list of tuples with the device name, success status, and error message.

        Args:
            connect(bool): connect to the devices
            force_connect(bool): force connection to all signals even if devices report .connected = True. Default is False.
            timeout_per_device(float): timeout for each device connection. Default is 30 seconds.

        Returns:
            list[tuple[str, bool, str]]: list of tuples with the device name, success status, and error message
        """
        if device_manager is None:
            raise ImportError(
                "bec-server is not installed. Please install it first with pip install bec-server."
            )

        print_and_write = []

        def mock_print(text: str):
            print_and_write.append(text)

        results = []
        with mock.patch.object(self, "print_and_write", side_effect=mock_print):
            for name, conf in self.config.items():
                return_val = 0
                status = False
                try:
                    return_val += self.validate_schema(name, conf)
                    return_val += self.check_device_classes(name, conf)
                    if device_manager is not None and connect:
                        return_val += self.connect_device(
                            name,
                            conf,
                            force_connect=force_connect,
                            timeout_per_device=timeout_per_device,
                        )
                    if return_val == 0:
                        status = True
                        self.print_and_write(f"{name} is OK")
                except Exception as e:
                    self.print_and_write(f"ERROR: {name} failed: {e}")
                finally:
                    results.append(
                        TestResult(name=name, success=status, message="\n".join(print_and_write))
                    )
                    print_and_write.clear()
        return results


def launch() -> None:
    """launch the test"""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Perform tests on an ophyd device config file.",
    )

    parser.add_argument("--config", help="path to the config file", required=True, type=str)
    optional = parser.add_argument_group("optional arguments")
    optional.add_argument(
        "--output", default="./device_test_reports", help="path to the output directory"
    )
    optional.add_argument("--connect", action="store_true", help="connect to the devices")
    optional.add_argument(
        "--force-connect",
        action="store_true",
        default=False,
        help="force connection to all signals",
    )
    optional.add_argument(
        "--timeout-per-device",
        type=float,
        default=30,
        help="timeout for each device connection in seconds",
    )
    parser.add_help = True

    clargs = parser.parse_args()

    if device_manager is None:
        raise ImportError(
            "bec-server is not installed. Please install it first with pip install bec-server."
        )

    if not os.path.exists(clargs.config):
        raise FileNotFoundError(f"Config file {clargs.config} not found.")

    if os.path.isdir(clargs.config):
        files = []
        for root, _, filenames in os.walk(clargs.config):
            for filename in filenames:
                if filename.endswith(".yaml") or filename.endswith(".yml"):
                    files.append(os.path.join(root, filename))
    else:
        files = [clargs.config]

    print(f"Running tests on the following files: {files}")

    if not os.path.exists(clargs.output):
        os.makedirs(clargs.output)

    for file in files:
        report_name = os.path.basename(file).split(".")[0]
        with open(
            os.path.join(clargs.output, f"report_{report_name}.txt"), "w", encoding="utf-8"
        ) as report_file:
            device_config_test = StaticDeviceTest(config_file=file, output_file=report_file)
            device_config_test.run(clargs.connect, clargs.force_connect, clargs.timeout_per_device)


if __name__ == "__main__":  # pragma: no cover
    import sys

    sys.argv = ["", "--config", "../bec/bec_lib/bec_lib/configs/demo_config.yaml", "--connect"]
    launch()
