#!/usr/bin/env python3
# coding=utf-8

#
# Copyright (c) 2022 Huawei Device Co., Ltd.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
import platform
import socket
import struct
import threading
import time
import shutil
import stat
from dataclasses import dataclass

from xdevice import DeviceOsType
from xdevice import ReportException
from xdevice import ExecuteTerminate
from xdevice import platform_logger
from xdevice import Plugin
from xdevice import get_plugin
from xdevice import IShellReceiver
from xdevice import exec_cmd
from xdevice import FilePermission
from xdevice import DeviceError
from xdevice import HdcError
from xdevice import HdcCommandRejectedException
from xdevice import ShellCommandUnresponsiveException
from xdevice import DeviceState
from xdevice import convert_serial
from xdevice import convert_mac
from xdevice import is_proc_running
from xdevice import convert_ip
from xdevice import create_dir
from ohos.error import ErrorMessage

ID_OKAY = b'OKAY'
ID_FAIL = b'FAIL'
ID_STAT = b'STAT'
ID_RECV = b'RECV'
ID_DATA = b'DATA'
ID_DONE = b'DONE'
ID_SEND = b'SEND'
ID_LIST = b'LIST'
ID_DENT = b'DENT'

DEFAULT_ENCODING = "utf-8"
COMPATIBLE_ENCODING = "ISO-8859-1"
SYNC_DATA_MAX = 64 * 1024
REMOTE_PATH_MAX_LENGTH = 1024
SOCK_DATA_MAX = 256

INSTALL_TIMEOUT = 2 * 60 * 1000
DEFAULT_TIMEOUT = 40 * 1000

MAX_CONNECT_ATTEMPT_COUNT = 10
DATA_UNIT_LENGTH = 4
HEXADECIMAL_NUMBER = 16
SPECIAL_FILE_MODE = 41471
FORMAT_BYTES_LENGTH = 4
DEFAULT_OFFSET_OF_INT = 4

INVALID_MODE_CODE = -1
DEFAULT_STD_PORT = 8710
HDC_NAME = "hdc"
HDC_STD_NAME = "hdc_std"
HDC_UDS_ADDRESS = "/data/hdc/hdc_debug/hdc_server"
LOG = platform_logger("Hdc")


class HdcMonitor:
    """
    A Device monitor.
    This monitor connects to the Device Connector, gets device and
    debuggable process information from it.
    """
    MONITOR_MAP = {}
    LOCK = threading.RLock()

    def __init__(self, host="127.0.0.1", port=None, device_connector=None, device_sns=None):
        self.channel = dict()
        self.channel.setdefault("host", host)
        self.channel.setdefault("port", port)
        self.main_hdc_connection = None
        self.connection_attempt = 0
        self.is_stop = False
        self.monitoring = False
        self.server = device_connector
        self.devices = []
        self.device_sns = device_sns or []
        self.last_msg_len = 0
        self.changed = True
        self.server_thread = None
        self.last_sock_name = None

    @staticmethod
    def get_instance(host, port=None, device_connector=None, device_sns=None):
        with HdcMonitor.LOCK:
            if host not in HdcMonitor.MONITOR_MAP:
                monitor = HdcMonitor(host, port, device_connector, device_sns)
                HdcMonitor.MONITOR_MAP[host] = monitor
                LOG.debug("HdcMonitor map add host %s, map is %s" %
                          (host, HdcMonitor.MONITOR_MAP))
                HdcHelper.CONNECTOR_NAME = HdcMonitor.peek_hdc()
            return HdcMonitor.MONITOR_MAP[host]

    def start(self):
        """
        Starts the monitoring.
        """
        with HdcMonitor.LOCK:
            if self.server_thread is not None and self.server_thread.is_alive():
                return
            try:
                self.server_thread = threading.Thread(target=self.loop_monitor,
                                                      name="HdcMonitor", args=())
                self.server_thread.daemon = True
                self.server_thread.start()
            except FileNotFoundError as _:
                LOG.error("HdcMonitor can't find connector, init device "
                          "environment failed!")

    def init_hdc(self, connector_name=HDC_NAME):
        env_hdc = shutil.which(connector_name)
        # if not, add xdevice's own hdc path to environ path.
        # tell if hdc has already been in the environ path.
        if env_hdc is None:
            self.is_stop = True
            LOG.error("Can not find {} or {} environment variable, please set first!".format(HDC_NAME, HDC_STD_NAME))
            LOG.error("Stop {} monitor!".format(HdcHelper.CONNECTOR_NAME))
        if platform.system() == 'HarmonyOS':
            process_name = "hdc -m -s"
        else:
            process_name = connector_name

        if not is_proc_running(process_name):
            port = DEFAULT_STD_PORT
            self.start_hdc(
                connector=connector_name,
                local_port=self.channel.setdefault(
                    "port", port))
            time.sleep(1)

    def _init_hdc_connection(self):
        if self.main_hdc_connection is not None:
            return
        # set all devices disconnect
        devices = [item for item in self.devices]
        devices.reverse()
        for local_device1 in devices:
            local_device1.device_state = DeviceState.OFFLINE
            self.server.device_changed(local_device1)

        connector_name = HDC_STD_NAME if HdcHelper.is_hdc_std() else HDC_NAME
        self.init_hdc(connector_name)
        self.connection_attempt = 0
        self.monitoring = False
        while self.main_hdc_connection is None:
            self.main_hdc_connection = self.open_hdc_connection()
            if self.main_hdc_connection is None:
                self.connection_attempt += 1
                if self.connection_attempt > MAX_CONNECT_ATTEMPT_COUNT:
                    LOG.error(
                        "HdcMonitor attempt %s, can't connect to hdc "
                        "for Device List Monitoring" %
                        str(self.connection_attempt))
                    raise HdcError(ErrorMessage.Hdc.Code_0304001.format(
                        self.channel.get("host"), str(self.channel.get("port"))))

                LOG.debug(
                    "HdcMonitor Connection attempts: %s" %
                    str(self.connection_attempt))
                time.sleep(2)

    def stop(self):
        """
        Stops the monitoring.
        """
        with HdcMonitor.LOCK:
            for host in HdcMonitor.MONITOR_MAP:
                LOG.debug("HdcMonitor stop host %s" % host)
                monitor = HdcMonitor.MONITOR_MAP[host]
                try:
                    monitor.is_stop = True
                    if monitor.main_hdc_connection is not None:
                        monitor.main_hdc_connection.shutdown(2)
                        monitor.main_hdc_connection.close()
                        monitor.main_hdc_connection = None
                        monitor.last_sock_name = None
                except (socket.error, socket.gaierror, socket.timeout) as _:
                    LOG.error("HdcMonitor close socket exception")
            HdcMonitor.MONITOR_MAP.clear()
            LOG.debug("HdcMonitor {} monitor stop!".format(HdcHelper.CONNECTOR_NAME))
            LOG.debug("HdcMonitor map is %s" % HdcMonitor.MONITOR_MAP)

    def loop_monitor(self):
        """
        Monitors the devices. This connects to the Debug Bridge
        """
        LOG.debug("current connector name is %s" % HdcHelper.CONNECTOR_NAME)
        while not self.is_stop:
            try:
                if self.main_hdc_connection is None:
                    self._init_hdc_connection()
                    if self.main_hdc_connection is not None:
                        LOG.debug(
                            "HdcMonitor Connected to hdc for device "
                            "monitoring, main_hdc_connection is %s" %
                            self.main_hdc_connection)

                self.list_targets()
                time.sleep(2)
            except (HdcError, Exception) as _:
                self.handle_exception_monitor_loop()
                time.sleep(2)

    def handle_exception_monitor_loop(self):
        LOG.debug("Handle exception monitor loop: %s" %
                  self.main_hdc_connection)
        if self.main_hdc_connection is None:
            return
        LOG.debug("Handle exception monitor loop, main hdc connection closed, "
                  "main hdc connection: %s" % self.main_hdc_connection)
        self.main_hdc_connection.close()
        self.main_hdc_connection = None

    def _get_device_instance(self, items, os_type):
        device_sn = items[0]
        device_state = items[3]
        host = self.channel.get("host")
        port = self.channel.get("port")
        if self.device_sns and device_sn not in self.device_sns:
            LOG.debug("Dmlib ignore device {} on {}:{} that is not in config, state: {}".format(
                device_sn, host, port, device_state))
            return None

        device = get_plugin(plugin_type=Plugin.DEVICE, plugin_id=os_type)[0]
        device_instance = device.__class__()
        device_instance.__set_serial__(device_sn)
        device_instance.host = host
        device_instance.port = port
        if self.changed:
            if DeviceState.get_state(device_state) == DeviceState.CONNECTED:
                LOG.debug("Dmlib get device {} on {}:{}, state: {}".format(
                    device_sn, host, port, device_state))
            else:
                LOG.debug("Dmlib ignore device {} on {}:{}, state: {}".format(
                    device_sn, host, port, device_state))
        device_instance.device_state = DeviceState.get_state(device_state)
        return device_instance

    def update_devices(self, param_array_list):
        devices = [item for item in self.devices]
        devices.reverse()
        for local_device1 in devices:
            k = 0
            for local_device2 in param_array_list:
                if local_device1.device_sn == local_device2.device_sn and \
                        local_device1.device_os_type == \
                        local_device2.device_os_type:
                    k = 1
                    if local_device1.device_state != \
                            local_device2.device_state:
                        local_device1.device_state = local_device2.device_state
                        self.server.device_changed(local_device1)
                    param_array_list.remove(local_device2)
                    break

            if k == 0:
                self.devices.remove(local_device1)
                self.server.device_disconnected(local_device1)
        for local_device in param_array_list:
            self.devices.append(local_device)
            self.server.device_connected(local_device)

    def open_hdc_connection(self):
        """
        Attempts to connect to the debug bridge server. Return a connect socket
        if success, null otherwise.
        """
        try:
            LOG.debug(
                "HdcMonitor connecting to hdc for Device List Monitoring")
            LOG.debug("HdcMonitor socket connection host: %s, port: %s" %
                      (str(convert_ip(self.channel.get("host"))),
                       str(int(self.channel.get("port")))))
            if self.channel.get("host") == "127.0.0.1" and platform.system() == 'HarmonyOS':
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sock.connect(HDC_UDS_ADDRESS)
            else:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((self.channel.get("host"),
                              int(self.channel.get("port"))))
            return sock

        except (socket.error, socket.gaierror, socket.timeout) as exception:
            if self.channel.get("host") == "127.0.0.1" and platform.system() == 'HarmonyOS':
                LOG.error("HdcMonitor hdc socket connection Error: {}, "
                          "address is {}".format(str(exception), HDC_UDS_ADDRESS))
            else:
                LOG.error("HdcMonitor hdc socket connection Error: {}, "
                          "host is {}, port is {}".format(str(exception),
                                                      self.channel.get("host"),
                                                      self.channel.get("port")))
            return None

    def start_hdc(self, connector=HDC_NAME, kill=False, local_port=None):
        """Starts the hdc host side server.

        Args:
            connector: connector type, like "hdc"
            kill: if True, kill exist host side server
            local_port: local port to start host side server

        Returns:
            None
        """
        if kill:
            LOG.debug("HdcMonitor {} kill".format(connector))
            exec_cmd([connector, "kill"])
        LOG.debug("HdcMonitor {} start".format(connector))
        exec_cmd(
            [connector, "-l5", "start"],
            error_print=False, redirect=True)

    def list_targets(self):
        if self.main_hdc_connection:
            self.server.monitor_lock.acquire(timeout=1)
            try:
                self.monitoring_list_targets()
                len_buf = HdcHelper.read(self.main_hdc_connection,
                                         DATA_UNIT_LENGTH)
                length = struct.unpack("!I", len_buf)[0]
                if length >= 0:
                    if self.last_msg_len != length:
                        LOG.debug("had received length is: %s" % length)
                        self.last_msg_len = length
                        self.changed = True
                    else:
                        self.changed = False
                    self.connection_attempt = 0
                    self.process_incoming_target_data(length)
            except Exception as e:
                LOG.error(e)
                raise e
            finally:
                self.server.monitor_lock.release()

    def monitoring_list_targets(self):
        try:
            if not self.monitoring:
                self.main_hdc_connection.settimeout(3)
                HdcHelper.handle_shake(self.main_hdc_connection)
                self.main_hdc_connection.settimeout(None)
                request = HdcHelper.form_hdc_request("alive")
                HdcHelper.write(self.main_hdc_connection, request)
                self.monitoring = True
        except socket.timeout as e:
            LOG.error("HdcMonitor Connection handshake: error {}".format(e))
            time.sleep(3)
            raise HdcError(ErrorMessage.Hdc.Code_0304001.format(
                self.channel.get("host"), self.channel.get("port"))) from e
        request = HdcHelper.form_hdc_request('list targets -v')
        HdcHelper.write(self.main_hdc_connection, request)

    def process_incoming_target_data(self, length):
        data_buf = HdcHelper.read(self.main_hdc_connection, length)
        if not self.is_need_to_handle():
            return
        local_array_list = []
        data_str = HdcHelper.reply_to_string(data_buf)
        LOG.info(data_str)
        if 'Empty' not in data_str:
            lines = data_str.split('\n')
            for line in lines:
                items = line.strip().split('\t')
                # Example: sn    USB     Offline localhost       hdc
                if not items[0] or len(items) < 5:
                    continue
                device_instance = self._get_device_instance(
                    items, DeviceOsType.default)
                if not device_instance:
                    continue
                local_array_list.append(device_instance)
        else:
            if self.changed:
                LOG.debug("please check device actually.[%s]" % data_str.strip())
        self.update_devices(local_array_list)

    @staticmethod
    def peek_hdc():
        LOG.debug("Peek running process to check expect connector.")
        # if not find hdc_std, find hdc
        connector_name = HDC_NAME
        env_hdc = shutil.which(connector_name)
        # if not, add xdevice's own hdc path to environ path.
        # tell if hdc has already been in the environ path.
        if env_hdc is None:
            connector_name = HDC_STD_NAME
        LOG.debug("Peak end")
        return connector_name

    def is_need_to_handle(self):
        if (self.last_sock_name is not None and self.main_hdc_connection.getsockname() == self.last_sock_name
                and not self.changed):
            return False
        self.last_sock_name = self.main_hdc_connection.getsockname()
        return True


@dataclass
class HdcResponse:
    """Response from HDC."""
    okay = ID_OKAY  # first 4 bytes in response were "OKAY"?
    message = ""  # diagnostic string if okay is false


class SyncService:
    """
    Sync service class to push/pull to/from devices/emulators,
    through the debug bridge.
    """

    def __init__(self, device, host=None, port=None):
        self.device = device
        self.host = host
        self.port = port
        self.sock = None

    def open_sync(self, timeout=DEFAULT_TIMEOUT):
        """
        Opens the sync connection. This must be called before any calls to
        push[File] / pull[File].
        Return true if the connection opened, false if hdc refuse the
        connection. This can happen device is invalid.
        """
        LOG.debug("Open sync, timeout=%s" % int(timeout / 1000))
        self.sock = HdcHelper.socket(host=self.host, port=self.port,
                                     timeout=timeout)
        HdcHelper.set_device(self.device, self.sock)

        request = HdcHelper.form_hdc_request("sync:")
        HdcHelper.write(self.sock, request)

        resp = HdcHelper.read_hdc_response(self.sock)
        if not resp.okay:
            err_msg = ErrorMessage.Hdc.Code_0304002.format(resp.message)
            self.device.log.error(err_msg)
            raise HdcError(err_msg)

    def close(self):
        """
        Closes the connection.
        """
        if self.sock is not None:
            try:
                self.sock.close()
            except socket.error as error:
                LOG.error("Socket close error: %s" % error, error_no="00420")
            finally:
                self.sock = None

    def pull_file(self, remote, local, is_create=False):
        """
        Pulls a file.
        The top directory won't be created if is_create is False (by default)
        and vice versa
        """
        mode = self.read_mode(remote)
        self.device.log.debug("Remote file %s mode is %d" % (remote, mode))
        if mode == 0:
            raise HdcError(ErrorMessage.Device.Code_0303003.format(remote))

        if str(mode).startswith("168"):
            if is_create:
                remote_file_split = os.path.split(remote)[-1] \
                    if os.path.split(remote)[-1] else os.path.split(remote)[-2]
                remote_file_basename = os.path.basename(remote_file_split)
                new_local = os.path.join(local, remote_file_basename)
                create_dir(new_local)
            else:
                new_local = local

            collect_receiver = CollectingOutputReceiver()
            HdcHelper.execute_shell_command(self.device, "ls %s" % remote,
                                            receiver=collect_receiver)
            files = collect_receiver.output.split()
            for file_name in files:
                self.pull_file("%s/%s" % (remote, file_name),
                               new_local, is_create=True)
        elif mode == SPECIAL_FILE_MODE:
            self.device.log.info("skipping special file '%s'" % remote)
        else:
            if os.path.isdir(local):
                local = os.path.join(local, os.path.basename(remote))

            self.do_pull_file(remote, local)

    def do_pull_file(self, remote, local):
        """
        Pulls a remote file
        """
        self.device.log.info(
            "%s pull %s to %s" % (convert_serial(self.device.device_sn),
                                  remote, local))
        remote_path_content = remote.encode(DEFAULT_ENCODING)
        if len(remote_path_content) > REMOTE_PATH_MAX_LENGTH:
            raise HdcError(ErrorMessage.Hdc.Code_0304003)

        msg = self.create_file_req(ID_RECV, remote_path_content)
        HdcHelper.write(self.sock, msg)
        pull_result = HdcHelper.read(self.sock, DATA_UNIT_LENGTH * 2)
        if not self.check_result(pull_result, ID_DATA) and \
                not self.check_result(pull_result, ID_DONE):
            raise HdcError(self.read_error_message(pull_result))
        if platform.system() == "Windows":
            flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_BINARY
        else:
            flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
        pulled_file_open = os.open(local, flags, FilePermission.mode_755)
        with os.fdopen(pulled_file_open, "wb") as pulled_file:
            while True:
                if self.check_result(pull_result, ID_DONE):
                    break

                if not self.check_result(pull_result, ID_DATA):
                    raise HdcError(self.read_error_message(pull_result))

                try:
                    length = self.swap32bit_from_array(
                        pull_result, DEFAULT_OFFSET_OF_INT)
                except IndexError as index_error:
                    self.device.log.debug("do_pull_file: %s" %
                                          str(pull_result))
                    if pull_result == ID_DATA:
                        pull_result = self.sock.recv(DATA_UNIT_LENGTH)
                        self.device.log.debug(
                            "do_pull_file: %s" % str(pull_result))
                        length = self.swap32bit_from_array(pull_result, 0)
                        self.device.log.debug("do_pull_file: %s" % str(length))
                    else:
                        raise IndexError(str(index_error)) from index_error

                if length > SYNC_DATA_MAX:
                    raise HdcError(ErrorMessage.Hdc.Code_0304004)

                pulled_file.write(HdcHelper.read(self.sock, length))
                pulled_file.flush()
                pull_result = self.sock.recv(DATA_UNIT_LENGTH * 2)

    def push_file(self, local, remote, is_create=False):
        """
        Push a single file.
        The top directory won't be created if is_create is False (by default)
        and vice versa
        """
        if not os.path.exists(local):
            raise HdcError(ErrorMessage.Device.Code_0303002.format(local))

        if os.path.isdir(local):
            if is_create:
                local_file_split = os.path.split(local)[-1] \
                    if os.path.split(local)[-1] else os.path.split(local)[-2]
                local_file_basename = os.path.basename(local_file_split)
                remote = "{}/{}".format(
                    remote, local_file_basename)
                HdcHelper.execute_shell_command(
                    self.device, "mkdir -p %s" % remote)

            for child in os.listdir(local):
                file_path = os.path.join(local, child)
                if os.path.isdir(file_path):
                    self.push_file(
                        file_path, "%s/%s" % (remote, child),
                        is_create=False)
                else:
                    self.do_push_file(file_path, "%s/%s" % (remote, child))
        else:
            self.do_push_file(local, remote)

    def do_push_file(self, local, remote):
        """
        Push a single file

        Args:
        ------------
        local : string
            the local file to push
        remote : string
            the remote file (length max is 1024)
        """
        mode = self.read_mode(remote)
        self.device.log.debug("Remote file %s mode is %d" % (remote, mode))
        self.device.log.debug("%s execute command: hdc push %s %s" % (
            convert_serial(self.device.device_sn), local, remote))
        if str(mode).startswith("168"):
            remote = "%s/%s" % (remote, os.path.basename(local))

        try:
            try:
                remote_path_content = remote.encode(DEFAULT_ENCODING)
            except UnicodeEncodeError as _:
                remote_path_content = remote.encode("UTF-8")
            if len(remote_path_content) > REMOTE_PATH_MAX_LENGTH:
                raise HdcError(ErrorMessage.Hdc.Code_0304003)

            # create the header for the action
            # and send it. We use a custom try/catch block to make the
            # difference between file and network IO exceptions.
            msg = self.create_send_file_req(ID_SEND, remote_path_content,
                                            FilePermission.mode_644)

            HdcHelper.write(self.sock, msg)
            flags = os.O_RDONLY
            modes = stat.S_IWUSR | stat.S_IRUSR
            with os.fdopen(os.open(local, flags, modes), "rb") as test_file:
                while True:
                    if platform.system() == "Windows":
                        data = test_file.read(SYNC_DATA_MAX)
                    else:
                        data = test_file.read(1024 * 4)

                    if not data:
                        break

                    buf = struct.pack(
                        "%ds%ds%ds" % (len(ID_DATA), FORMAT_BYTES_LENGTH,
                                       len(data)), ID_DATA,
                        self.swap32bits_to_bytes(len(data)), data)
                    self.sock.send(buf)
        except Exception as exception:
            self.device.log.error("exception %s" % exception)
            raise exception

        msg = self.create_req(ID_DONE, int(time.time()))
        HdcHelper.write(self.sock, msg)
        result = HdcHelper.read(self.sock, DATA_UNIT_LENGTH * 2)
        if not self.check_result(result, ID_OKAY):
            self.device.log.error("exception %s" % result)
            raise HdcError(self.read_error_message(result))

    def read_mode(self, path):
        """
        Returns the mode of the remote file.
        Return an Integer containing the mode if all went well or null
        """
        msg = self.create_file_req(ID_STAT, path)
        HdcHelper.write(self.sock, msg)

        # read the result, in a byte array containing 4 ints
        stat_result = HdcHelper.read(self.sock, DATA_UNIT_LENGTH * 4)
        if not self.check_result(stat_result, ID_STAT):
            return INVALID_MODE_CODE

        return self.swap32bit_from_array(stat_result, DEFAULT_OFFSET_OF_INT)

    def create_file_req(self, command, path):
        """
        Creates the data array for a file request. This creates an array with a
        4 byte command + the remote file name.

        Args:
        ------------
        command :
            the 4 byte command (ID_STAT, ID_RECV, ...)
        path : string
            The path, as a byte array, of the remote file on which to execute
            the command.

        return:
        ------------
            return the byte[] to send to the device through hdc
        """
        if isinstance(path, str):
            try:
                path = path.encode(DEFAULT_ENCODING)
            except UnicodeEncodeError as _:
                path = path.encode("UTF-8")

        return struct.pack(
            "%ds%ds%ds" % (len(command), FORMAT_BYTES_LENGTH, len(path)),
            command, self.swap32bits_to_bytes(len(path)), path)

    def create_send_file_req(self, command, path, mode=0o644):
        # make the mode into a string
        mode_str = ",%s" % str(mode & FilePermission.mode_777)
        mode_content = mode_str.encode(DEFAULT_ENCODING)
        return struct.pack(
            "%ds%ds%ds%ds" % (len(command), FORMAT_BYTES_LENGTH, len(path),
                              len(mode_content)),
            command, self.swap32bits_to_bytes(len(path) + len(mode_content)),
            path, mode_content)

    def create_req(self, command, value):
        """
        Create a command with a code and an int values
        """
        return struct.pack("%ds%ds" % (len(command), FORMAT_BYTES_LENGTH),
                           command, self.swap32bits_to_bytes(value))

    @staticmethod
    def check_result(result, code):
        """
        Checks the result array starts with the provided code

        Args:
        ------------
        result :
            the result array to check
        path : string
            the 4 byte code

        return:
        ------------
        bool
            return true if the code matches
        """
        return result[0:4] == code[0:4]

    def read_error_message(self, result):
        """
        Reads an error message from the opened Socket.

        Args:
        ------------
        result :
            the current hdc result. Must contain both FAIL and the length of
            the message.
        """
        if self.check_result(result, ID_FAIL):
            length = self.swap32bit_from_array(result, 4)
            if length > 0:
                return str(HdcHelper.read(self.sock, length))

        return None

    @staticmethod
    def swap32bits_to_bytes(value):
        """
        Swaps an unsigned value around, and puts the result in an bytes that
        can be sent to a device.

        Args:
        ------------
        value :
            the value to swap.
        """
        return bytes([value & 0x000000FF,
                      (value & 0x0000FF00) >> 8,
                      (value & 0x00FF0000) >> 16,
                      (value & 0xFF000000) >> 24])

    @staticmethod
    def swap32bit_from_array(value, offset):
        """
        Reads a signed 32 bit integer from an array coming from a device.

        Args:
        ------------
        value :
            the array containing the int
        offset:
            the offset in the array at which the int starts

        Return:
        ------------
        int
            the integer read from the array
        """
        result = 0
        result |= (int(value[offset])) & 0x000000FF
        result |= (int(value[offset + 1]) & 0x000000FF) << 8
        result |= (int(value[offset + 2]) & 0x000000FF) << 16
        result |= (int(value[offset + 3]) & 0x000000FF) << 24

        return result


class HdcHelper:
    CONNECTOR_NAME = ""

    @staticmethod
    def check_if_hdc_running(timeout=30):
        LOG.debug("Check if {} is running, timeout is {}s".format(
            HdcHelper.CONNECTOR_NAME, timeout))
        index = 1
        while index < timeout:
            if is_proc_running(HdcHelper.CONNECTOR_NAME):
                return True
            index = index + 1
            time.sleep(1)
        return False

    @staticmethod
    def push_file(device, local, remote, is_create=False,
                  timeout=DEFAULT_TIMEOUT):
        device.log.info("{} execute command: {} file send {} to {}".format(
            convert_serial(device.device_sn), HdcHelper.CONNECTOR_NAME, local, remote))
        HdcHelper._operator_file("file send", device, local, remote, timeout)

    @staticmethod
    def pull_file(device, remote, local, is_create=False,
                  timeout=DEFAULT_TIMEOUT):
        device.log.info("{} execute command: {} file recv {} to {}".format(
            convert_serial(device.device_sn), HdcHelper.CONNECTOR_NAME, remote, local))
        HdcHelper._operator_file("file recv", device, remote, local, timeout)

    @staticmethod
    def _install_remote_package(device, remote_file_path, command):
        receiver = CollectingOutputReceiver()
        cmd = "bm install -p %s %s" % (command.strip(), remote_file_path)
        HdcHelper.execute_shell_command(device, cmd, INSTALL_TIMEOUT, receiver)
        return receiver.output

    @staticmethod
    def install_package(device, package_file_path, command):
        device.log.info("%s install %s" % (convert_serial(device.device_sn),
                                           package_file_path))
        remote_file_path = "/data/local/tmp/%s" % os.path.basename(
            package_file_path)
        device.push_file(package_file_path, remote_file_path)
        result = HdcHelper._install_remote_package(device, remote_file_path,
                                                   command)
        HdcHelper.execute_shell_command(device, "rm %s " % remote_file_path)
        return result

    @staticmethod
    def uninstall_package(device, package_name):
        receiver = CollectingOutputReceiver()
        command = "bm uninstall -n %s " % package_name
        device.log.info("%s %s" % (convert_serial(device.device_sn), command))
        HdcHelper.execute_shell_command(device, command, INSTALL_TIMEOUT,
                                        receiver)
        return receiver.output

    @staticmethod
    def reboot(device, into=None):
        device.log.info("{} execute command: {} target boot".format(convert_serial(device.device_sn),
                                                                    HdcHelper.CONNECTOR_NAME))
        with HdcHelper.socket(host=device.host, port=device.port) as sock:
            HdcHelper.handle_shake(sock, device.device_sn)
            request = HdcHelper.form_hdc_request("target boot")
            HdcHelper.write(sock, request)
        # 2024/7/4日出现新系统执行hdc target boot后不会马上重启情况,需要等待2s
        time.sleep(2)

    @staticmethod
    def execute_shell_command(device, command, timeout=DEFAULT_TIMEOUT,
                              receiver=None, **kwargs):
        """
        Executes a shell command on the device and retrieve the output.

        Args:
        ------------
        device : IDevice
            on which to execute the command.
        command : string
            the shell command to execute
        timeout : int
            max time between command output. If more time passes between
            command output, the method will throw
            ShellCommandUnresponsiveException (ms).
        """
        try:
            if not timeout:
                timeout = DEFAULT_TIMEOUT

            with HdcHelper.socket(host=device.host, port=device.port,
                                  timeout=timeout) as sock:
                output_flag = kwargs.get("output_flag", True)
                timeout_msg = " with timeout %ss" % str(timeout / 1000)
                message = "{} execute command: {} shell {}{}".format(convert_serial(device.device_sn),
                                                                     HdcHelper.CONNECTOR_NAME,
                                                                     convert_mac(command), timeout_msg)
                if output_flag:
                    LOG.info(message)
                else:
                    LOG.debug(message)
                from xdevice import Binder
                HdcHelper.handle_shake(sock, device.device_sn)
                request = HdcHelper.form_hdc_request("shell {}".format(command))
                HdcHelper.write(sock, request)
                resp = HdcResponse()
                resp.okay = True
                while True:
                    len_buf = sock.recv(DATA_UNIT_LENGTH)
                    if len_buf:
                        length = struct.unpack("!I", len_buf)[0]
                    else:
                        break
                    data = sock.recv(length)
                    recv_length = len(data)
                    if recv_length < length:
                        data += HdcHelper.read(sock, length - recv_length)
                    ret = HdcHelper.reply_to_string(data)
                    if ret:
                        if receiver:
                            receiver.__read__(ret)
                        else:
                            LOG.debug(ret)
                    if not Binder.is_executing():
                        raise ExecuteTerminate()
                return resp
        except socket.timeout as error:
            err_msg = ErrorMessage.Device.Code_0303013.format(
                convert_serial(device.device_sn), convert_mac(command), str(timeout / 1000))
            device.log.error(err_msg)
            raise ShellCommandUnresponsiveException() from error
        finally:
            if receiver:
                receiver.__done__()

    @staticmethod
    def set_device(device, sock):
        """
        Tells hdc to talk to a specific device
        if the device is not -1, then we first tell hdc we're looking to talk
        to a specific device
        """
        msg = "host:transport:%s" % device.device_sn
        device_query = HdcHelper.form_hdc_request(msg)
        HdcHelper.write(sock, device_query)
        resp = HdcHelper.read_hdc_response(sock)
        if not resp.okay:
            raise HdcCommandRejectedException(ErrorMessage.Hdc.Code_0304005.format(resp.message))

    @staticmethod
    def form_hdc_request(req):
        """
        Create an ASCII string preceded by four hex digits.
        """
        try:
            if not req.endswith('\0'):
                req = "%s\0" % req
            req = req.encode("utf-8")
            fmt = "!I%ss" % len(req)
            result = struct.pack(fmt, len(req), req)
        except UnicodeEncodeError as ex:
            LOG.error(ex)
            raise ex
        return result

    @staticmethod
    def read_hdc_response(sock, read_diag_string=False):
        """
        Reads the response from HDC after a command.

        Args:
        ------------
        read_diag_string :
            If true, we're expecting an OKAY response to be followed by a
            diagnostic string. Otherwise, we only expect the diagnostic string
            to follow a FAIL.
        """
        resp = HdcResponse()
        reply = HdcHelper.read(sock, DATA_UNIT_LENGTH)
        if HdcHelper.is_okay(reply):
            resp.okay = True
        else:
            read_diag_string = True
            resp.okay = False

        while read_diag_string:
            len_buf = HdcHelper.read(sock, DATA_UNIT_LENGTH)
            len_str = HdcHelper.reply_to_string(len_buf)
            msg = HdcHelper.read(sock, int(len_str, HEXADECIMAL_NUMBER))
            resp.message = HdcHelper.reply_to_string(msg)
            break

        return resp

    @staticmethod
    def write(sock, req, timeout=10):
        if isinstance(req, str):
            req = req.encode(DEFAULT_ENCODING)
        elif isinstance(req, list):
            req = bytes(req)

        start_time = time.time()
        while req:
            if time.time() - start_time > timeout:
                LOG.debug("Socket write timeout, timeout:%ss" % timeout)
                break

            size = sock.send(req)
            if size < 0:
                raise DeviceError(ErrorMessage.Device.Code_0303017)

            req = req[size:]
            time.sleep(5 / 1000)

    @staticmethod
    def read(sock, length, timeout=10):
        data = b''
        recv_len = 0
        start_time = time.time()
        exc_num = 3
        while length - recv_len > 0:
            if time.time() - start_time > timeout:
                LOG.debug("Socket read timeout, timout:%ss" % timeout)
                break
            try:
                recv = sock.recv(length - recv_len)
                if len(recv) > 0:
                    time.sleep(5 / 1000)
                else:
                    break
            except ConnectionResetError as error:
                if exc_num <= 0:
                    raise error
                exc_num = exc_num - 1
                recv = b''
                time.sleep(1)
                LOG.debug("ConnectionResetError occurs")

            data += recv
            recv_len += len(recv)

        return data

    @staticmethod
    def is_okay(reply):
        """
        Checks to see if the first four bytes in "reply" are OKAY.
        """
        return reply[0:4] == ID_OKAY

    @staticmethod
    def reply_to_string(reply):
        """
        Converts an HDC reply to a string.
        """
        for encoding in [DEFAULT_ENCODING, COMPATIBLE_ENCODING]:
            try:
                return str(reply, encoding=encoding)
            except (ValueError, TypeError) as _:
                continue
        return ""

    @staticmethod
    def socket(host=None, port=None, timeout=None):
        end = time.time() + 10 * 60
        sock = None
        hdc_connection = HdcMonitor.MONITOR_MAP.get(host, "127.0.0.1")
        while host not in HdcMonitor.MONITOR_MAP or \
                hdc_connection.main_hdc_connection is None:
            LOG.debug("Host: %s, port: %s, HdcMonitor map is %s" % (
                host, port, HdcMonitor.MONITOR_MAP))
            if host in HdcMonitor.MONITOR_MAP:
                LOG.debug("Monitor main hdc connection is %s" %
                          hdc_connection.main_hdc_connection)
            if time.time() > end:
                raise HdcError(ErrorMessage.Hdc.Code_0304006)
            time.sleep(2)

        try:
            if host == "127.0.0.1" and platform.system() == 'HarmonyOS':
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sock.connect(HDC_UDS_ADDRESS)
            else:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((host, int(port)))
        except socket.error as exception:
            LOG.exception("Connect hdc server error: %s" % str(exception),
                          exc_info=False)
            raise exception

        if sock is None:
            raise HdcError(ErrorMessage.Hdc.Code_0304007)

        if timeout is not None:
            sock.setblocking(False)
            sock.settimeout(timeout / 1000)

        return sock

    @staticmethod
    def handle_shake(connection, connect_key=""):
        reply = HdcHelper.read(connection, 48)
        struct.unpack(">I12s32s", reply)
        banner_str = b'OHOS HDC'
        connect_key = connect_key.encode("utf-8")
        size = struct.calcsize('12s256s')
        fmt = "!I12s256s"
        pack_cmd = struct.pack(fmt, size, banner_str, connect_key)
        HdcHelper.write(connection, pack_cmd)
        return True

    @staticmethod
    def _operator_file(command, device, local, remote, timeout):
        sock = HdcHelper.socket(host=device.host, port=device.port,
                                timeout=timeout)
        HdcHelper.handle_shake(sock, device.device_sn)
        request = HdcHelper.form_hdc_request(
            "%s %s %s" % (command, local, remote))
        HdcHelper.write(sock, request)
        reply = HdcHelper.read(sock, DATA_UNIT_LENGTH)
        length = struct.unpack("!I", reply)[0]
        data_buf = HdcHelper.read(sock, length)
        HdcHelper.reply_to_string(data_buf)
        LOG.debug(data_buf.decode().strip())

    @staticmethod
    def is_hdc_std():
        return HDC_STD_NAME in HdcHelper.CONNECTOR_NAME


class DeviceConnector(object):
    __instance = None
    __init_flag = False

    def __init__(self, host=None, port=None, usb_type=None, device_sns=None):
        if DeviceConnector.__init_flag:
            return
        self.device_listeners = []
        self.device_monitor = None
        self.device_sns = device_sns or []
        self.monitor_lock = threading.Condition()
        self.host = host if host else "127.0.0.1"
        self.usb_type = usb_type
        if port:
            self.port = int(port)
        else:
            self.port = int(os.getenv("OHOS_HDC_SERVER_PORT", DEFAULT_STD_PORT))

    def start(self):
        self.device_monitor = HdcMonitor.get_instance(
            self.host, self.port, device_connector=self, device_sns=self.device_sns)
        self.device_monitor.start()

    def terminate(self):
        if self.device_monitor:
            self.device_monitor.stop()
        self.device_monitor = None

    def add_device_change_listener(self, device_change_listener):
        self.device_listeners.append(device_change_listener)

    def remove_device_change_listener(self, device_change_listener):
        if device_change_listener in self.device_listeners:
            self.device_listeners.remove(device_change_listener)

    def device_connected(self, device):
        LOG.debug("DeviceConnector device connected:host %s, port %s, "
                  "device sn %s " % (self.host, self.port, device.device_sn))
        if device.host != self.host or device.port != self.port:
            LOG.debug("DeviceConnector device error")
        for listener in self.device_listeners:
            listener.device_connected(device)

    def device_disconnected(self, device):
        LOG.debug("DeviceConnector device disconnected:host %s, port %s, "
                  "device sn %s" % (self.host, self.port, device.device_sn))
        if device.host != self.host or device.port != self.port:
            LOG.debug("DeviceConnector device error")
        for listener in self.device_listeners:
            listener.device_disconnected(device)

    def device_changed(self, device):
        LOG.debug("DeviceConnector device changed:host %s, port %s, "
                  "device sn %s" % (self.host, self.port, device.device_sn))
        if device.host != self.host or device.port != self.port:
            LOG.debug("DeviceConnector device error")
        for listener in self.device_listeners:
            listener.device_changed(device)


class CollectingOutputReceiver(IShellReceiver):
    def __init__(self):
        self.output = ""

    def __read__(self, output):
        self.output = "%s%s" % (self.output, output)

    def __error__(self, message):
        pass

    def __done__(self, result_code="", message=""):
        pass


class DisplayOutputReceiver(IShellReceiver):
    def __init__(self):
        self.output = ""
        self.unfinished_line = ""

    def _process_output(self, output, end_mark="\n"):
        content = output
        if self.unfinished_line:
            content = "".join((self.unfinished_line, content))
            self.unfinished_line = ""
        lines = content.split(end_mark)
        if content.endswith(end_mark):
            # get rid of the tail element of this list contains empty str
            return lines[:-1]
        else:
            self.unfinished_line = lines[-1]
            # not return the tail element of this list contains unfinished str,
            # so we set position -1
            return lines[:-1]

    def __read__(self, output):
        self.output = "%s%s" % (self.output, output)
        lines = self._process_output(output)
        for line in lines:
            line = line.strip()
            if line:
                LOG.info(line)

    def __error__(self, message):
        pass

    def __done__(self, result_code="", message=""):
        pass


def process_command_ret(ret, receiver):
    try:
        if ret != "" and receiver:
            receiver.__read__(ret)
            receiver.__done__()
    except Exception as error:
        LOG.exception(ErrorMessage.Common.Code_0301014, exc_info=False)
        raise ReportException() from error

    if ret != "" and not receiver:
        lines = ret.split("\n")
        for line in lines:
            line = line.strip()
            if line:
                LOG.debug(line)
