import logging
from typing import Any, Callable, List, Optional, Tuple, Union

from numpy.typing import NDArray
from pixelinkWrapper import*
from ctypes import*
import ctypes
import numpy as np
from qtpy import QtCore, QtWidgets
import json
import os
import time
import sys
import ctypes
from ctypes import wintypes

if not hasattr(QtCore, "pyqtSignal"):
    QtCore.pyqtSignal = QtCore.Signal  # type: ignore

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


if sys.platform.startswith("win"):
    import ctypes
    MB_YESNO = 0x04
    MB_ICONQUESTION = 0x20
    MB_OK = 0x00
    MB_ICONINFORMATION = 0x40
    MB_ICONERROR = 0x10
    IDYES = 6
    IDNO = 7
    IDOK = 1

    def _win_message_box(title, text, buttons="yesno", icon="info"):
        icon_map = {"info": MB_ICONINFORMATION, "question": MB_ICONQUESTION, "error": MB_ICONERROR}
        flags = icon_map.get(icon, MB_ICONINFORMATION)
        if buttons == "yesno":
            flags |= MB_YESNO
        else:
            flags |= MB_OK
        return ctypes.windll.user32.MessageBoxW(0, text, title, flags)


class PixelinkCamera:

    def __init__(self, info: str, callback: Optional[Callable] = None, **kwargs):
        super().__init__(**kwargs)

        self.model_name = info["Model Name"]
        self.device_info = info
        self.attributes = {}
        self._msg_opener = None

        # Default directory for parameter config files
        self.base_dir = os.path.join(os.environ.get('PROGRAMDATA'), '.pymodaq')

        self.open()

        # Callback setup for image grabbing
        self.listener = Listener()
        ret = PxLApi.setCallback(self.camera, PxLApi.Callback.FRAME, self.listener._user_data, self.listener._callback_func)
        if not PxLApi.apiSuccess(ret[0]):
            print("ERROR setting frame callback function: {0}".format(ret[0]))
            print("Error message:", PxLApi.getErrorReport(ret[0])[1].strReturnCode)

        # Load in user-defined settings as default
        ret = PxLApi.loadSettings(self.camera, PxLApi.Settings.SETTINGS_USER)
        if not PxLApi.apiSuccess(ret[0]):
            print("ERROR loading user settings: {0}".format(ret[0]))
            print("Error message:", PxLApi.getErrorReport(ret[0])[1].strReturnCode)

        # Start with triggering disabled so we start with a clean slate
        self.disable_triggering() 

        # Initialize feature map with current values
        self.feature_map = self.build_feature_param_name_map()
        
        if callback is not None:
            self.set_callback(callback=callback)

    def open(self) -> None:
        # Initialize camera using serial number
        ret = PxLApi.initialize(int(self.device_info["Serial Number"]))
        if PxLApi.apiSuccess(ret[0]):
            self.camera = ret[1]
        self.create_default_config_if_not_exists()
        self.get_attributes()
        self.attribute_names = [attr['name'] for attr in self.attributes] + [child['name'] for attr in self.attributes if attr.get('type') == 'group' for child in attr.get('children', [])]

    def set_callback(self, callback: Callable[[NDArray], None], replace_all: bool = True) -> None:
        if replace_all:
            try:
                self.listener.signals.data_ready.disconnect()
            except TypeError:
                pass  # not connected
        self.listener.signals.data_ready.connect(callback)
    
    def get_attributes(self):
        """Get the attributes of the camera and store them in a dictionary."""
        name = self.model_name.replace(" ", "-")
        file_path = os.path.join(self.base_dir, f'config_{name}.json')

        try:
            with open(file_path, 'r') as file:
                attributes = json.load(file)
                self.attributes = self.clean_device_attributes(attributes)
        except Exception as e:
            logger.error(f"Could not find attributes config file at {file_path}:", e)

    def start_acquisition(self) -> None:
        ret = PxLApi.setStreamState(self.camera, PxLApi.StreamState.START)
        if not PxLApi.apiSuccess(ret[0]):
            logger.error("ERROR setting stream state function: {0}".format(ret[0]))
            logger.error("Error message:", PxLApi.getErrorReport(ret[0])[1].strReturnCode)

    def stop_acquisition(self) -> None:
        ret = PxLApi.setStreamState(self.camera, PxLApi.StreamState.STOP)
        if not PxLApi.apiSuccess(ret[0]):
            logger.error("ERROR setting stream state function: {0}".format(ret[0]))
            logger.error("Error message:", PxLApi.getErrorReport(ret[0])[1].strReturnCode)

    def close(self) -> None:
        ret = PxLApi.setStreamState(self.camera, PxLApi.StreamState.STOP)
        if not PxLApi.apiSuccess(ret[0]):
            logger.error("ERROR setting stream state function: {0}".format(ret[0]))
            logger.error("Error message:", PxLApi.getErrorReport(ret[0])[1].strReturnCode)
        ret = PxLApi.setCallback(self.camera, PxLApi.Callback.FRAME, self.listener._user_data, 0)
        if not PxLApi.apiSuccess(ret[0]):
            logger.error("ERROR disabling frame callback function: {0}".format(ret[0]))
            logger.error("Error message:", PxLApi.getErrorReport(ret[0])[1].strReturnCode)
        ret = PxLApi.uninitialize(self.camera)
        if not PxLApi.apiSuccess(ret[0]):
            logger.error("ERROR uninitializing camera: {0}".format(ret[0]))
            logger.error("Error message:", PxLApi.getErrorReport(ret[0])[1].strReturnCode)    

    def save_device_state(self):
        ret = PxLApi.saveSettings(self.camera, PxLApi.Settings.SETTINGS_USER)
        if not PxLApi.apiSuccess(ret[0]):
            logger.error("ERROR saving device state to non-volatile memory: {0}".format(ret[0]))
            logger.error("Error message:", PxLApi.getErrorReport(ret[0])[1].strReturnCode)

    def factory_device_state(self):
        ret = PxLApi.loadSettings(self.camera, PxLApi.Settings.SETTINGS_FACTORY)
        if not PxLApi.apiSuccess(ret[0]):
            logger.error("ERROR loading factory settings: {0}".format(ret[0]))
            logger.error("Error message:", PxLApi.getErrorReport(ret[0])[1].strReturnCode)

    def enable_feature(self, flags, enable):
        if enable:
            flags = ~PxLApi.FeatureFlags.MOD_BITS | PxLApi.FeatureFlags.MANUAL
        else:
            flags = ~PxLApi.FeatureFlags.MOD_BITS | PxLApi.FeatureFlags.OFF
        return flags

    def disable_triggering(self):
        # Read current settings
        ret = PxLApi.getFeature(self.camera, PxLApi.FeatureId.TRIGGER)
        assert PxLApi.apiSuccess(ret[0])
        flags = ret[1]
        params = ret[2]
        assert 5 == len(params)

        # Disable triggering
        flags = self.enable_feature(flags, False)

        ret = PxLApi.setFeature(self.camera, PxLApi.FeatureId.TRIGGER, flags, params)
        assert PxLApi.apiSuccess(ret[0])

    def set_triggering(self, mode, triggerType, polarity, delay, param):

        # Read current settings
        ret = PxLApi.getFeature(self.camera, PxLApi.FeatureId.TRIGGER)
        assert PxLApi.apiSuccess(ret[0])
        flags = ret[1]
        params = ret[2]
        assert 5 == len(params)
        
        # Very important step: Enable triggering by clearing the FEATURE_FLAG_OFF bit
        flags = self.enable_feature(flags, True)

        # Assign the new values...
        params[PxLApi.TriggerParams.MODE] = mode
        params[PxLApi.TriggerParams.TYPE] = triggerType
        params[PxLApi.TriggerParams.POLARITY] = polarity
        params[PxLApi.TriggerParams.DELAY] = delay
        params[PxLApi.TriggerParams.PARAMETER] = param

        # ... and write them to the camera
        ret = PxLApi.setFeature(self.camera, PxLApi.FeatureId.TRIGGER, flags, params)
        assert PxLApi.apiSuccess(ret[0])

    def build_feature_param_name_map(self):
        feature_param_name_map = {}

        # Get actual features from camera
        ret = PxLApi.getCameraFeatures(self.camera, PxLApi.FeatureId.ALL)
        if not PxLApi.apiSuccess(ret[0]):
            raise RuntimeError("Failed to get camera features")

        cameraFeatures = ret[1]

        for i in range(cameraFeatures.uNumberOfFeatures):
            feature = cameraFeatures.Features[i]
            feature_id = feature.uFeatureId
            num_params = feature.uNumberOfParameters

            # Get string name of the feature
            feature_name = next(
                (name for name, value in vars(PxLApi.FeatureId).items() if value == feature_id),
                f"FEATURE_{feature_id}"
            ).upper()

            # Try to find associated Params enum
            param_class_name = feature_name.title().replace('_', '') + 'Params'
            param_class = getattr(PxLApi, param_class_name, None)

            if param_class:
                # Named indices
                param_map = {
                    k.upper(): v for k, v in vars(param_class).items()
                    if not k.startswith('__') and isinstance(v, int)
                }
            elif num_params == 1:
                # Use "VALUE" as default parameter name
                param_map = {
                    "VALUE": 0
                }
            else:
                # Fallback to generic naming
                param_map = {
                    f"PARAM_{idx}": idx for idx in range(num_params)
                }

            # Manually add entries for auto exposure continuously and once
            if feature_name == "SHUTTER":
                feature_param_name_map["SHUTTER_AUTO"] = {
                    "id": feature_id,
                    "params": {
                        "VALUE": 0,
                        "AUTO_MIN": 1,
                        "AUTO_MAX": 2
                        }
                }
                feature_param_name_map["SHUTTER_AUTO_ONCE"] = {
                    "id": feature_id,
                    "params": {
                        "VALUE": 0,
                        "AUTO_MIN": 1,
                        "AUTO_MAX": 2
                        }
                }

            # Add structured entry
            feature_param_name_map[feature_name] = {
                "id": feature_id,
                "params": param_map
            }
        


        return feature_param_name_map


    def clean_device_attributes(self, attributes):
        clean_params = []

        # Check if attributes is a list or dictionary
        if isinstance(attributes, dict):
            items = attributes.items()
        elif isinstance(attributes, list):
            # If it's a list, we assume each item is a parameter (no keys)
            items = enumerate(attributes)  # Use index for 'key'
        else:
            raise ValueError(f"Unsupported type for attributes: {type(attributes)}")

        for idx, attr in items:
            param = {}

            param['title'] = attr.get('title', '')
            param['name'] = attr.get('name', str(idx))  # use index if name is missing
            param['type'] = attr.get('type', 'str')
            param['value'] = attr.get('value', '')
            param['default'] = attr.get('default', None)
            param['limits'] = attr.get('limits', None)
            param['readonly'] = attr.get('readonly', False)

            if param['type'] == 'group' and 'children' in attr:
                children = attr['children']
                # If children is a dict, convert to a list
                if isinstance(children, dict):
                    children = list(children.values())
                param['children'] = self.clean_device_attributes(children)

            clean_params.append(param)

        return clean_params

    def check_attribute_names(self):
        found_exposure = None
        found_gain = None

        possible_exposures = ["SHUTTER"]
        for exp in possible_exposures:
            try:
                if exp in self.feature_map.keys():
                    found_exposure = exp
                    break
            except Exception:
                pass

        possible_gains = ["GAIN"]
        for gain in possible_gains:
            try:
                if gain in self.feature_map.keys():
                    found_gain = gain
            except Exception:
                pass

        found_exposure = found_exposure or "SHUTTER"
        found_gain = found_gain or "GAIN"

        return found_exposure, found_gain

    
    def create_default_config_if_not_exists(self):
        model_name = self.model_name.replace(" ", "-")
        config_dir = self.base_dir
        os.makedirs(config_dir, exist_ok=True)
        config_path = os.path.join(config_dir, f'config_{model_name}.json')
        if os.path.exists(config_path):
            return
        else:
            self._msg_opener = DefaultConfigMsg()
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Question)
            msg.setWindowTitle("Missing Config File")
            msg.setText(f"No config file found for camera model '{model_name}'.")
            msg.setInformativeText("Would you like to auto-create a default configuration file?")
            msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            msg.setDefaultButton(QtWidgets.QMessageBox.Yes)
            QtCore.QTimer.singleShot(0, QtWidgets.QApplication.processEvents)
            user_choice = self.safe_exec_messagebox(msg)
            self.handle_user_choice(user_choice, config_path, model_name)

    def handle_user_choice(self, user_choice, config_path, model_name):

        if user_choice == QtWidgets.QMessageBox.Yes:
            found_exposure, found_gain = self.check_attribute_names()

            config_data = {
                "exposure": {
                    "title": "Exposure Settings",
                    "name": "exposure",
                    "type": "group",
                    "children": {
                        "Exposure Time": {
                            "title": "Exposure Time (ms)",
                            "name": found_exposure,
                            "type": "slide",
                            "value": 100.0,
                            "default": 100.0,
                            "limits": [0.001, 10000.0],
                        }
                    },
                },
                "gain": {
                    "title": "Gain Settings",
                    "name": "gain",
                    "type": "group",
                    "children": {
                        "Gain": {
                            "title": "Gain Value",
                            "name": found_gain,
                            "type": "slide",
                            "value": 1.0,
                            "default": 1.0,
                            "limits": [0.0, 2.0],
                        }
                    },
                },
            }

            try:
                print(f"Creating default config for {model_name} at {config_path}")
                with open(config_path, "w") as f:
                    json.dump(config_data, f, indent=4)

                msg_info = QtWidgets.QMessageBox()
                msg_info.setIcon(QtWidgets.QMessageBox.Information)
                msg_info.setWindowTitle("Config Created")
                msg_info.setText(f"Default config file created for '{model_name}'.")
                msg_info.setInformativeText(
                    f"Path:\n{config_path}\n\nYou can edit this file to add/remove parameters."
                )
                self.safe_exec_messagebox(msg_info, buttons="ok")

            except Exception as e:
                msg_err = QtWidgets.QMessageBox()
                msg_err.setIcon(QtWidgets.QMessageBox.Critical)
                msg_err.setWindowTitle("Error Creating Config")
                msg_err.setText(f"Failed to write default config file:\n{e}")
                self.safe_exec_messagebox(msg_err, buttons="ok")

        else:
            msg_info = QtWidgets.QMessageBox()
            msg_info.setIcon(QtWidgets.QMessageBox.Information)
            msg_info.setWindowTitle("Config Not Created")
            msg_info.setText(f"You have chosen not to create a default config file for Basler '{model_name}'.")
            msg_info.setInformativeText(
                "You will not have access to camera parameters until you have a valid config file.\n\n"
                "You can find examples of config files in the resources directory of this package or "
                "reinitialize and create a default."
            )
            self.safe_exec_messagebox(msg_info, buttons="ok")

    def safe_exec_messagebox(self, msgbox: QtWidgets.QMessageBox, buttons: str = "yesno") -> int:
        """
        Safe dialog call that avoids creating Qt modal dialogs from non-GUI threads.

        Parameters
        ----------
        msgbox : QMessageBox
            The prepared message box.
        buttons : str
            Either "yesno" or "ok". Controls native fallback type.
        """
        app = QtWidgets.QApplication.instance()
        in_gui_thread = False
        if app is not None:
            in_gui_thread = QtCore.QThread.currentThread() == app.thread()

        # GUI thread → Safe to show Qt dialog
        if app is not None and in_gui_thread:
            try:
                return int(msgbox.exec_())
            except Exception:
                return int(QtWidgets.QMessageBox.No)

        # Non-GUI thread (Windows only safe path)
        if sys.platform.startswith("win"):
            title = str(msgbox.windowTitle() or "PyMoDAQ")
            text = str(msgbox.text() or "")
            informative = msgbox.informativeText()
            if informative:
                text += "\n\n" + str(informative)

            try:
                icon_type = "info"
                if msgbox.icon() == QtWidgets.QMessageBox.Question:
                    icon_type = "question"
                elif msgbox.icon() == QtWidgets.QMessageBox.Critical:
                    icon_type = "error"

                res = _win_message_box(title, text, buttons=buttons, icon=icon_type)

                if buttons == "yesno":
                    if res == IDYES:
                        return int(QtWidgets.QMessageBox.Yes)
                    return int(QtWidgets.QMessageBox.No)
                else:
                    return int(QtWidgets.QMessageBox.Ok)

            except Exception:
                return int(QtWidgets.QMessageBox.No)

        return int(QtWidgets.QMessageBox.No)

class DefaultConfigMsg(QtCore.QObject):
    def __init__(self):
        super().__init__()
    @QtCore.Slot(object)
    def run_box(self, fn):
        fn()

class Listener:

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.signals = self.ListenerSignal()
        self.frame_ready = False
        self.listener_active = True  # Add this flag to control emission

        # Store function pointer for use with API
        self._callback_func = self.frame_callback
        # IMPORTANT: Must pass a ctypes.c_void_p to setCallback, but you need to point it to a py_object, not to the pointer to that py_object
        self._user_data_obj = ctypes.py_object(self)
        self._user_data = ctypes.cast(ctypes.pointer(self._user_data_obj), ctypes.c_void_p)
    
    @staticmethod
    @PxLApi._dataProcessFunction
    def frame_callback(hCamera, frameData, dataFormat, frameDesc, userData):
        # IMPORTANT: Must cast from void* to POINTER(py_object), then dereference
        self = ctypes.cast(userData, ctypes.POINTER(ctypes.py_object)).contents.value
        
        # Check if listener is active
        if not self.listener_active:
            return 0  # Do nothing if the listener is inactive

        frameDescriptor = frameDesc.contents
        width = int(frameDescriptor.Roi.fWidth / frameDescriptor.PixelAddressingValue.fHorizontal)
        height = int(frameDescriptor.Roi.fHeight / frameDescriptor.PixelAddressingValue.fVertical)
        bytesPerPixel = PxLApi.getBytesPerPixel(dataFormat)

        # Emit signal safely
        npFrame = self.numPy_image(frameData, width, height, bytesPerPixel)
        if npFrame is not None:
            self.signals.data_ready.emit({"frame": npFrame, "timestamp": time.time_ns()})
            self.frame_ready = True

        return 0
    
    @staticmethod
    def numPy_image(frameData, width, height, bytesPerPixel):
        size = width * height * bytesPerPixel
        # Cast frameData to a ctypes array and copy into NumPy array
        buf_type = ctypes.c_ubyte * size
        buf = ctypes.cast(frameData, ctypes.POINTER(buf_type)).contents
        if bytesPerPixel == 1:
            arr = np.frombuffer(buf, dtype=c_uint8).copy()
        elif bytesPerPixel == 2:
            arr = np.frombuffer(buf, dtype=np.dtype(">u2")).copy()
            arrdiv = arr/16
            arr = np.int16(arrdiv)
        return arr.reshape(height, width)

    class ListenerSignal(QtCore.QObject):
        data_ready = QtCore.pyqtSignal(object)

    def stop_listener(self):
        """Call this to stop the listener and prevent future data_ready emissions."""
        self.listener_active = False

class TemperatureMonitor(QtCore.QObject):
    temperature_updated = QtCore.pyqtSignal(float)
    finished = QtCore.pyqtSignal()

    def __init__(self, camera_handle, check_interval=100):
        super().__init__()
        self._running = True
        self.camera = camera_handle
        self.interval = check_interval

    def stop(self):
        self._running = False

    def run(self):
        while self._running:
            ret = PxLApi.getFeature(self.camera, PxLApi.FeatureId.SENSOR_TEMPERATURE)
            if PxLApi.apiSuccess(ret[0]):
                temp = ret[2][0]
                self.temperature_updated.emit(temp)
            QtCore.QThread.msleep(self.interval)
        self.finished.emit()


def get_info_for_all_cameras():
    ret = PxLApi.getNumberCameras()
    if PxLApi.apiSuccess(ret[0]):
        cameraIdInfo = ret[1]
        numCameras = len(cameraIdInfo)
        devicesInfo = []
        if 0 < numCameras:
            for i in range(numCameras):
                serialNumber = cameraIdInfo[i].CameraSerialNum
                ret = PxLApi.initialize(serialNumber)
                if PxLApi.apiSuccess(ret[0]):
                    hCamera = ret[1]
                    ret = PxLApi.getCameraInfo(hCamera)
                    if PxLApi.apiSuccess(ret[0]):
                        cameraInfo = ret[1]
                        devicesInfo.append(get_camera_info(cameraInfo))
                    PxLApi.uninitialize(hCamera)
        return devicesInfo


def get_camera_info(cameraInfo):
    """
    Get all the info for the camera as a dictionary
    """
    info = {
        "Name": cameraInfo.CameraName.decode("utf-8"),
        "Description": cameraInfo.Description.decode("utf-8"),
        "Vendor Name": cameraInfo.VendorName.decode("utf-8"),
        "Serial Number": cameraInfo.SerialNumber.decode("utf-8"),
        "Firmware Version": cameraInfo.FirmwareVersion.decode("utf-8"),
        "FPGA Version": cameraInfo.FPGAVersion.decode("utf-8"),
        "XML Version": cameraInfo.XMLVersion.decode("utf-8"),
        "Bootload Version": cameraInfo.BootloadVersion.decode("utf-8"),
        "Model Name": cameraInfo.ModelName.decode("utf-8"),
        "Lens Description": cameraInfo.LensDescription.decode("utf-8")
    }

    return info
