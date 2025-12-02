import time
from collections import namedtuple

import re
import gi
import numpy
from enum import Enum
gi.require_version("Gst", "1.0")
gi.require_version("Tcam", "1.0")

from gi.repository import GLib, Gst, Tcam


DeviceInfo = namedtuple("DeviceInfo", "status name identifier connection_type")
CameraProperty = namedtuple("CameraProperty", "status value min max default step type flags category group")


class SinkFormats(Enum):
    GRAY8 = "GRAY8"
    GRAY16_LE = "GRAY16_LE"
    BGRA = "BGRx"
    BGRX = "BGRx"


class TIS:
    'The Imaging Source Camera'

    def __init__(self):
        try:
            if not Gst.is_initialized():
                Gst.init(())  # Usually better to call in the main function.
        except gi.overrides.Gst.NotInitialized:
            # Older gst-python overrides seem to have a bug where Gst needs to
            # already be initialized to call Gst.is_initialized
            Gst.init(())
        # Gst.debug_set_default_threshold(Gst.DebugLevel.WARNING)
        self.serialnumber = ""
        self.height = 0
        self.width = 0
        self.framerate = "15/1"
        self.sinkformat = SinkFormats.BGRA
        self.img_mat = None
        self.ImageCallback = None
        self.pipeline = None
        self.source = None
        self.appsink = None
        self.frame_counter = 0  # Track frame captures to ensure freshness
        self.last_capture_time = 0.0  # Track when last image was captured

    def open_device(self, serial,
                    width, height, framerate,
                    sinkformat: SinkFormats,
                    showvideo: bool,
                    conversion: str = ""):
        ''' Inialize a device, e.g. camera.
        :param serial: Serial number of the camera to be used.
        :param width: Width of the wanted video format
        :param height: Height of the wanted video format
        :param framerate: Numerator of the frame rate. /1 is added automatically
        :param sinkformat: Color format to use for the sink
        :param showvideo: Whether to always open a live video preview
        :param conversion: Optional pipeline string to add a conversion before the appsink
        :return: True if successful, False if failed
        '''
        try:
            if serial is None:
                serial = self.__get_serial_by_index(0)
            self.serialnumber = serial
            self.height = height
            self.width = width
            self.framerate = framerate
            self.sinkformat = sinkformat
            self._create_pipeline(conversion, showvideo)
            self.source.set_property("serial", self.serialnumber)
            
            # Set camera type based on detected camera type  
            # For DFK AFU420-L62, we need type=libusb
            if self.serialnumber == "30320436":
                self.source.set_property("type", "libusb")
                print(f"Set camera type to libusb for DFK AFU420-L62 (serial: {self.serialnumber})")
            
            self.pipeline.set_state(Gst.State.READY)
            ret, state, pending = self.pipeline.get_state(40000000)
            
            if ret == Gst.StateChangeReturn.SUCCESS or ret == Gst.StateChangeReturn.ASYNC:
                print(f"TIS camera pipeline initialized successfully (state: {state})")
                return True
            else:
                print(f"TIS camera pipeline failed to initialize (return: {ret})")
                return False
                
        except Exception as e:
            print(f"Error opening TIS camera: {e}")
            return False

    def _create_pipeline(self, conversion: str, showvideo: bool):
        # Handle conversion string properly - add ! only if conversion exists
        if conversion and not conversion.strip().endswith("!"):
            conversion += " !"
        elif not conversion:
            conversion = ""  # Empty string, no ! needed
        
        p = 'tcambin name=source ! capsfilter name=caps'
        if showvideo:
            p += " ! tee name=t"
            p += " t. ! queue ! videoconvert ! ximagesink"
            if conversion:
                p += f" t. ! queue ! {conversion} appsink name=sink"
            else:
                p += " t. ! queue ! appsink name=sink"
        else:
            if conversion:
                p += f" ! {conversion} appsink name=sink"
            else:
                p += " ! appsink name=sink"

        print(p)
        try:
            self.pipeline = Gst.parse_launch(p)
        except GLib.Error as error:
            print("Error creating pipeline: {0}".format(error))
            raise

        # Quere the source module.
        self.source = self.pipeline.get_by_name("source")

        # Query a pointer to the appsink, so we can assign the callback function.
        appsink = self.pipeline.get_by_name("sink")
        appsink.set_property("max-buffers", 5)
        appsink.set_property("drop", True)
        appsink.set_property("emit-signals", True)
        appsink.set_property("enable-last-sample", True)
        appsink.connect('new-sample', self.__on_new_buffer)
        self.appsink = appsink

    def __on_new_buffer(self, appsink):
        sample = appsink.get_property('last-sample')
        if sample and self.ImageCallback is not None:
            buf = sample.get_buffer()
            data = buf.extract_dup(0, buf.get_size())
            caps = sample.get_caps()
            self.img_mat = self.__convert_to_numpy(data, caps)
            self.ImageCallback(self, *self.ImageCallbackData)
        return Gst.FlowReturn.OK

    def set_sink_format(self, sf: SinkFormats):
        self.sinkformat = sf

    def show_live(self, show: bool):
        self.livedisplay = show

    def _setcaps(self):
        """
        Set pixel and sink format and frame rate
        """
        caps = Gst.Caps.from_string('video/x-raw,format=%s,width=%d,height=%d,framerate=%s' % (self.sinkformat.value, self.width, self.height, self.framerate))

        capsfilter = self.pipeline.get_by_name("caps")
        capsfilter.set_property("caps", caps)

    def start_pipeline(self):
        """
        Start the pipeline, so the video runs
        """
        # Check current state
        ret, current_state, pending = self.pipeline.get_state(1000000000)  # 1 second timeout
        print(f"Current pipeline state: {current_state} ({'NULL' if current_state == 1 else 'READY' if current_state == 2 else 'PAUSED' if current_state == 3 else 'PLAYING' if current_state == 4 else 'UNKNOWN'})")
        
        # If already playing, return success
        if current_state == Gst.State.PLAYING:
            print("Pipeline already in PLAYING state")
            return True

        # Follow the EXACT working capture-sequence example pattern
        try:
            self._setcaps()
            print("Setting pipeline to PLAYING state...")
            self.pipeline.set_state(Gst.State.PLAYING)
            
            # Wait for state change like working example
            error = self.pipeline.get_state(5000000000)  # 5 second timeout
            print(f"Pipeline state after start: {error[1]} ({'NULL' if error[1] == 1 else 'READY' if error[1] == 2 else 'PAUSED' if error[1] == 3 else 'PLAYING' if error[1] == 4 else 'UNKNOWN'})")
            print(f"State change return: {error[0]}")
            
            # If we reached PLAYING, great!
            if error[1] == Gst.State.PLAYING:
                print("Pipeline successfully reached PLAYING state - ready for sample capture")
                return True
            # If we reached PAUSED, try to understand why and test if samples work anyway
            elif error[1] == Gst.State.PAUSED:
                print("Pipeline reached PAUSED state instead of PLAYING")
                print("This happens in client mode but not in simple script - investigating...")
                
                # Even though simple script reaches PLAYING, repository examples show
                # that PAUSED state can sometimes work for sample capture
                # Let's test if samples are available in PAUSED state
                print("Testing if samples are available in PAUSED state...")
                import time
                time.sleep(1)  # Brief wait
                
                sample_test = self.appsink.emit("try-pull-sample", 1 * Gst.SECOND)
                if sample_test is not None:
                    print("SUCCESS: Samples available in PAUSED state - will proceed")
                    return True
                else:
                    print("FAILED: No samples available in PAUSED state")
                    print("Pipeline must reach PLAYING state for sample capture to work")
                    return False
            else:
                print(f"Error starting pipeline - reached unexpected state {error[1]}")
                return False
                
        except Exception as error:
            print(f"Exception starting pipeline: {error}")
            return False

    def wait_for_device_ready(self, timeout_seconds=5):
        """
        Wait for the device to be ready for property setting
        :param timeout_seconds: Maximum time to wait in seconds
        :return: True if device is ready, False if timeout
        """
        import time
        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            try:
                # Try to get a simple property to test if device is ready
                if self.source is not None:
                    self.source.get_tcam_property_names()
                    return True
            except:
                time.sleep(0.1)
        return False

    def __convert_to_numpy(self, data, caps):
        ''' Convert a GStreamer sample to a numpy array
            Sample code from https://gist.github.com/cbenhagen/76b24573fa63e7492fb6#file-gst-appsink-opencv-py-L34

            The result is in self.img_mat.
        :return:
        '''

        s = caps.get_structure(0)
        fmt = s.get_value('format')

        if (fmt == "BGRx"):
            dtype = numpy.uint8
            bpp = 4
        elif (fmt == "GRAY8"):
            dtype = numpy.uint8
            bpp = 1
        elif (fmt == "GRAY16_LE"):
            dtype = numpy.uint16
            bpp = 1
        else:
            raise RuntimeError(f"Unknown format in conversion to numpy array: {fmt}")

        img_mat = numpy.ndarray(
            (s.get_value('height'),
             s.get_value('width'),
             bpp),
            buffer=data,
            dtype=dtype)
        return img_mat

    def snap_image(self, timeout, convert_to_mat=True):
        '''
        Snap an image from stream using a timeout.
        :param timeout: wait time in second, should be a float number.
        :return: Image data.
        '''
        if self.ImageCallback is not None:
            print("Snap_image can not be called, if a callback is set.")
            return None

        # Check if appsink exists
        if self.appsink is None:
            print("appsink is None - cannot capture image")
            return None

        # CRITICAL: Clear old image data before capture to prevent using cached images
        old_frame_count = self.frame_counter
        self.img_mat = None
        
        print(f"TIS.snap_image: Capturing NEW frame (previous frame #{old_frame_count}), timeout={timeout}s")
        
        # Try to pull sample from appsink
        sample = self.appsink.emit("try-pull-sample", timeout * Gst.SECOND)
        print(f"Sample received from appsink: {sample is not None}")
        
        # Handle None sample properly - working examples return None/False in this case
        if sample is None:
            print("No sample available from appsink - pipeline may not be producing frames")
            print(f"WARNING: Capture failed, img_mat cleared to prevent stale data")
            return None
            
        # Process sample - now we know it's not None
        try:
            buf = sample.get_buffer()
            if buf is None:
                print("Buffer is None")
                print(f"WARNING: Buffer is None, img_mat cleared to prevent stale data")
                return None
                
            data = buf.extract_dup(0, buf.get_size())
            print(f"Buffer data extracted: {len(data) if data else 0} bytes")
            
            if convert_to_mat and sample is not None:
                try:
                    self.img_mat = self.__convert_to_numpy(data, sample.get_caps())
                    # Update frame tracking to ensure image freshness
                    self.frame_counter += 1
                    self.last_capture_time = time.time()
                    print(f"✓ NEW frame captured: #{self.frame_counter} at {self.last_capture_time:.3f}")
                except RuntimeError:
                    # unsuported format to convert to mat
                    # ignored to keep compatibility to old sample code
                    print("WARNING: Failed to convert to numpy array, img_mat remains None")
                    pass

            return data
            
        except Exception as e:
            print(f"Error processing sample: {e}")
            print(f"WARNING: Capture exception, img_mat cleared to prevent stale data")
            self.img_mat = None
            return None

    def get_image(self):
        """
        Get the most recently captured image.
        
        Returns:
            numpy.ndarray: The captured image, or None if no fresh image available
            
        WARNING: This returns the image from the last snap_image() call.
        Always call snap_image() before get_image() to ensure fresh data.
        """
        if self.img_mat is None:
            print("WARNING: get_image() called but img_mat is None - no image captured")
            return None
        
        # Validate that we have a fresh image (captured within last 60 seconds)
        time_since_capture = time.time() - self.last_capture_time
        if time_since_capture > 60.0:
            print(f"WARNING: Image may be stale - last captured {time_since_capture:.1f}s ago")
        
        print(f"Returning frame #{self.frame_counter} (captured {time_since_capture:.3f}s ago)")
        return self.img_mat

    def stop_pipeline(self):
        self.pipeline.set_state(Gst.State.PAUSED)
        self.pipeline.set_state(Gst.State.READY)

    def get_source(self):
        '''
        Return the source element of the pipeline.
        '''
        return self.source

    def list_properties(self):
        property_names = self.source.get_tcam_property_names()

        for name in property_names:
            try:
                base = self.source.get_tcam_property(name)
                print("{}\t{}".format(base.get_display_name(),
                                      name))
            except Exception as error:
                raise RuntimeError(f"Failed to get property '{name}'") from error

    def get_property(self, property_name):
        """
        Return the value of the passed property.
        If something fails an
        exception is thrown.
        :param property_name: Name of the property to set
        :return: Current value of the property
        """
        try:
            baseproperty = self.source.get_tcam_property(property_name)
            val = baseproperty.get_value()
            return val

        except Exception as error:
            raise RuntimeError(f"Failed to get property '{property_name}'") from error

        return None

    def set_property(self, property_name, value):
        '''
        Pass a new value to a camera property. If something fails an
        exception is thrown.
        :param property_name: Name of the property to set
        :param value: Property value. Can be of type int, float, string and boolean
        '''
        try:
            # Wait for device to be ready if pipeline is not yet playing
            if self.pipeline is not None:
                state = self.pipeline.get_state(Gst.CLOCK_TIME_NONE)
                if state[1] != Gst.State.PLAYING:
                    print(f"Warning: Pipeline not in PLAYING state when setting {property_name}")
            
            baseproperty = self.source.get_tcam_property(property_name)
            baseproperty.set_value(value)
        except Exception as error:
            raise RuntimeError(f"Failed to set property '{property_name}'") from error

    def execute_command(self, property_name):
        '''
        Execute a command property like Software Trigger
        If something fails an exception is thrown.
        :param property_name: Name of the property to set
        '''
        try:
            baseproperty = self.source.get_tcam_property(property_name)
            baseproperty.set_command()
        except Exception as error:
            raise RuntimeError(f"Failed to execute '{property_name}'") from error

    def set_image_callback(self, function, *data):
        self.ImageCallback = function
        self.ImageCallbackData = data

    def __get_serial_by_index(self, index: int):
        ' Return the serial number of the camera enumerated at given index'
        monitor = Gst.DeviceMonitor.new()
        monitor.add_filter("Video/Source/tcam")
        devices = monitor.get_devices()
        if (index < 0) or (index > len(devices)-1):
            raise RuntimeError("Index out of bounds")
        device = devices[index]
        return device.get_properties().get_string("serial")

    def select_device(self):
        ''' Select a camera, its video format and frame rate
        :return: True on success, False on nothing selected
        '''
        monitor = Gst.DeviceMonitor.new()
        monitor.add_filter("Video/Source/tcam")
        serials = []
        i = 0
        for device in monitor.get_devices():
            struc = device.get_properties()
            i += 1
            print("{} : Model: {} Serial: {} {} ".format(i,
                                                         struc.get_string("model"),
                                                         struc.get_string("serial"),
                                                         struc.get_string("type")))

            serials.append("{}-{}".format(struc.get_string("serial"),
                                          struc.get_string("type")))

        if i > 0:
            i = int(input("Select : "))
            if i == 0:
                return False

            self.serialnumber = serials[i-1]
            print(self.serialnumber)

            return self.select_format()

        return False

    def select_format(self):
        '''
        '''
        formats = self.create_formats()
        i = 0
        f = []
        for key, value in formats.items():
            f.append(key)
            i = i + 1
            print("{}: {}".format(i, key))

        i = int(input("Select : "))
        if i == 0:
            return False

        formatindex = f[i-1]
        i = 0
        for res in formats[formatindex].res_list:
            i = i + 1
            print("{}:  {}x{}".format(i, res.width, res.height))

        i = int(input("Select : "))
        if i == 0:
            return False

        width = formats[formatindex].res_list[i-1].width
        height = formats[formatindex].res_list[i-1].height
        o = 0
        for rate in formats[formatindex].res_list[i-1].fps:
            o += 1
            print("{}:  {}".format(o, rate))

        framerate = formats[formatindex].res_list[i-1].fps[o-1]
        o = int(input("Select : "))
        if o == 0:
            return False

        framerate = formats[formatindex].res_list[i-1].fps[o-1]
        # print(format,width,height,framerate )
        self.open_device(self.serialnumber, width, height, framerate, SinkFormats.BGRA, True)
        return True

    def create_formats(self):
        source = Gst.ElementFactory.make("tcambin")
        source.set_property("serial", self.serialnumber)

        source.set_state(Gst.State.READY)

        caps = source.get_static_pad("src").query_caps()
        format_dict = {}

        for x in range(caps.get_size()):
            structure = caps.get_structure(x)
            name = structure.get_name()
            try:
                videoformat = structure.get_value("format")

                width = structure.get_value("width")
                height = structure.get_value("height")

                rates = self.get_framerates(structure)
                tmprates = []

                for rate in rates:
                    tmprates.append(str(rate))

                if type(videoformat) == Gst.ValueList:
                    videoformats = videoformat
                else:
                    videoformats = [videoformat]
                for fmt in videoformats:
                    if videoformat not in format_dict:
                        format_dict[fmt] = FmtDesc(name, videoformat)
                    format_dict[fmt].res_list.append(ResDesc(width, height, tmprates))
            except Exception as error:
                print(f"Exception during format enumeration: {str(error)}")

        source.set_state(Gst.State.NULL)
        source.set_property("serial", "")
        source = None

        return format_dict

    def get_framerates(self, fmt):
        try:
            tmprates = fmt.get_value("framerate")
            if type(tmprates) == Gst.FractionRange:
                # A range is given only, so create a list of frame rate in 10 fps steps:
                rates = []
                rates.append("{0}/{1}".format(int(tmprates.start.num), int(tmprates.start.denom)))
                r = int((tmprates.start.num + 10) / 10) * 10
                while r < (tmprates.stop.num / tmprates.stop.denom):
                    rates.append("{0}/1".format(r))
                    r += 10

                rates.append("{0}/{1}".format(int(tmprates.stop.num), int(tmprates.stop.denom)))
            else:
                rates = tmprates

        except TypeError:
            # Workaround for missing GstValueList support in GI
            substr = fmt.to_string()[fmt.to_string().find("framerate="):]
            # try for frame rate lists
            field, values, remain = re.split("{|}", substr, maxsplit=3)
            rates = [x.strip() for x in values.split(",")]
        return rates


class ResDesc:
    """"""
    def __init__(self,
                 width: int,
                 height: int,
                 fps: list):
        self.width = width
        self.height = height
        self.fps = fps
        self.resolution=f"{width}x{height}"


class FmtDesc:
    """"""

    def __init__(self,
                 name: str = "",
                 fmt: str = ""):
        self.name = name
        self.fmt = fmt
        self.res_list = []

    def get_name(self):
        if self.name == "image/jpeg":
            return "jpeg"
        else:
            return self.fmt

    def get_resolution_list(self):

        res_list = []

        for entry in self.res_list:
            res_list.append(entry.resolution)

        return res_list

    def get_fps_list(self, resolution: str):

        for entry in self.res_list:
            if entry.resolution == resolution:
                return entry.fps

    def generate_caps_string(self, resolution: str, fps: str):
        if self.name == "image/jpeg":
            return "{},width={},height={},framerate={}".format(self.name,
                                                               resolution.split('x')[0],
                                                               resolution.split('x')[1],
                                                               fps)
        else:
            return "{},format={},width={},height={},framerate={}".format(self.name,
                                                                         self.fmt,
                                                                         resolution.split('x')[0],
                                                                         resolution.split('x')[1],
                                                                         fps)
