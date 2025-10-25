"""This module provides the TransportLayer class used to establish and maintain bidirectional serial communication
with Arduino and Teensy microcontrollers running the ataraxis-transport-layer-mc library over USB / UART interface.
"""

from enum import IntEnum
from typing import Any
from dataclasses import fields, is_dataclass

from numba import njit  # type: ignore[import-untyped]
import numpy as np
from serial import Serial
from numpy.typing import NDArray
from serial.tools import list_ports
from ataraxis_time import PrecisionTimer, TimerPrecisions
from ataraxis_base_utilities import console
from serial.tools.list_ports_common import ListPortInfo

from .helper_modules import (
    SerialMock,
    CRCProcessor,
    COBSProcessor,
    _CRCProcessor,
    _COBSProcessor,
)

# Defines constants that are frequently reused in this module
_ZERO = np.uint8(0)
_POLYNOMIAL = np.uint8(0x07)
_EMPTY_ARRAY = np.empty(0, dtype=np.uint8)

# Defines the collection of NumPy types used by the CRCProcessor class to represent valid input arguments and output
# values.
type CRCType = np.uint8 | np.uint16 | np.uint32


class TransportLayerStatus(IntEnum):
    """Stores the status codes used by the TransportLayer class to communicate the state of various processing steps
    between the JIT-compiled methods and the user-facing API methods.
    """

    INSUFFICIENT_BUFFER_SPACE_ERROR = -1
    """The reception or transmission buffer does not have enough space for the requested operation."""
    MULTIDIMENSIONAL_ARRAY_ERROR = -2
    """The data to be written or the prototype to be read are not a one-dimensional NumPy array."""
    EMPTY_ARRAY_ERROR = -3
    """The data to be written or the prototype to be read is an empty NumPy array."""
    PACKET_SIZE_UNKNOWN = 0
    """Not enough bytes read to fully parse the packet. The start byte was found, but packet size has not been resolved 
    and, therefore, not known."""
    PACKET_PARSED = 1
    """Packet fully parsed."""
    NOT_ENOUGH_PACKET_BYTES = 2
    """Not enough bytes read to fully parse the packet. The packet size was resolved, but there were not enough bytes to
    fully parse the packet (encoded payload + crc postamble)."""
    NOT_ENOUGH_CRC_BYTES = 3
    """Not enough bytes read to fully parse the packet. The packet payload was successfully parsed, but there were not 
    enough bytes to fully parse the CRC postamble."""
    NO_BYTES_TO_READ = 4
    """No start byte found, which is interpreted as 'no bytes to read,' as the class is configured to ignore start byte 
    errors. Usually, this situation is caused by communication line noise generating 'noise bytes'."""
    PAYLOAD_SIZE_MISMATCH = 5
    """Parsed payload_size value does not match the expected value. This likely indicates packet corruption or 
    communication parameter mismatch between the TransportLayer instance and the connected Microcontroller."""
    DELIMITER_FOUND_TOO_EARLY = 6
    """Delimiter byte value encountered before reaching the end of the encoded payload data block. It is expected that 
    the last byte of the encoded payload is set to the delimiter value and that the value is not present anywhere else 
    inside the encoded payload region. Encountering the delimiter early indicates packet corruption."""
    DELIMITER_NOT_FOUND = 7
    """Delimiter byte value not encountered at the end of the encoded payload data block. See code 104 description for 
    more details, but this code also indicates packet corruption."""


def list_available_ports() -> tuple[ListPortInfo, ...]:  # pragma: no cover
    """Provides the information about each serial port addressable through the pySerial library.

    This function is intended to be used for discovering and selecting the serial port 'names' to use with
    TransportLayer instances.

    Returns:
        A tuple of ListPortInfo instances, each storing ID and descriptive information about each discovered serial
        port.

    """
    # Returns the list of port objects visible to the pySerial library.
    return tuple(list_ports.comports())


def print_available_ports() -> None:  # pragma: no cover
    """Prints all serial ports active on the host-system with descriptive information about the device connected to
    that port to the terminal.

    This command is intended to be used for discovering the USB ports that can be connected to by a TransportLayer
    class instance.
    """
    # Records the current console status and, if necessary, ensures the console is enabled before running this command.
    is_enabled = True
    if not console.enabled:
        is_enabled = False
        console.enable()  # Enables console output

    # Gets a tuple that stores all active USB ports with some ID information.
    available_ports = list_available_ports()

    # Loops over all discovered ports and prints the ID information about each port to the terminal
    count = 0  # Cannot use 'enumerate' due to filtering PID==None ports.
    for port in available_ports:
        # Filters out any ports with PID == None. This is primarily used to filter out invalid ports on Linux systems.
        if port.pid is not None:
            count += 1  # Counts only valid ports.
            console.echo(f"{count}: {port.device} -> {port.description}")  # Removes unnecessary information.

    # If the console was enabled by this runtime, ensures it is disabled before finishing the runtime.
    if not is_enabled:
        console.disable()


class TransportLayer:
    """Provides methods for sending and receiving serialized data over the USB and UART communication interfaces.

    This class instantiates and manages all library assets used to transcode, validate, and bidirectionally transfer
    serial data over the target communication interface. Critically, this includes the transmission and reception
    buffers that are used to temporarily store the outgoing and incoming data payloads. All user-facing class methods
    interact with the data stored in one of these buffers.

    Args:
        port: The name of the serial port to connect to, e.g.: 'COM3' or '/dev/ttyUSB0'. Use the 'axtl-ports' CLI
            command to discover available port names.
        microcontroller_serial_buffer_size: The size, in bytes, of the buffer used by the connected microcontroller's
            serial communication interface. Usually, this information is available from the microcontroller's
            manufacturer (UART / USB controller specification).
        baudrate: The baudrate to use for communication if the microcontroller uses the UART interface. Should match
            the value used by the microcontroller. This parameter is ignored when using the USB interface.
        polynomial: The polynomial to use for the generation of the CRC lookup table. The polynomial must
            be standard (non-reflected / non-reversed).
        initial_crc_value: The value to which the CRC checksum is initialized before calculation.
        final_crc_xor_value: The value with which the CRC checksum is XORed after calculation.
        test_mode: Determines whether the instance uses a pySerial (real) or a StreamMock (mocked) communication
            interface. This flag is used during testing and should be disabled for all production runtimes.

    Attributes:
        _opened: Tracks whether the serial communication has been opened (the port has been connected).
        _port: Depending on the test_mode flag, stores either a SerialMock or Serial object that provides the serial
            communication interface.
        _crc_processor: Stores the CRCProcessor instance that provides methods for working CRC checksums.
        _cobs_processor: Stores the COBSProcessor instance that provides methods for encoding and decoding transmitted
            payloads.
        _timer: Stores the PrecisionTimer instance that provides a microsecond-precise GIL-releasing timer.
        _start_byte: Stores the byte-value that marks the beginning of transmitted and received packets.
        _delimiter_byte: Stores the byte-value that marks the end of transmitted and received packets.
        _timeout: Stores the number of microseconds to wait between receiving any two consecutive bytes of a packet.
        _max_tx_payload_size: Stores the maximum number of bytes that can be transmitted as a single payload.
        _max_rx_payload_size: Stores the maximum number of bytes that can be received from the microcontroller as a
            single payload.
        _min_rx_payload_size: Stores the minimum number of bytes that can be received from the Microcontroller as a
            single payload.
        _postamble_size: Stores the byte-size of the CRC checksum.
        _transmission_buffer: The buffer used to stage the data to be sent to the Microcontroller.
        _reception_buffer: The buffer used to store the decoded data received from the Microcontroller.
        _bytes_in_transmission_buffer: Tracks how many bytes (relative to index 0) of the transmission buffer are
            currently used to store the payload to be transmitted.
        _bytes_in_reception_buffer: Same as _bytes_in_transmission_buffer, but for the reception buffer.
        _consumed_bytes: Tracks the number of the last received payload bytes that have been consumed by the
            read_data() method calls.
        _leftover_bytes: A buffer used to preserve any 'unconsumed' bytes that were read from the serial port
            but not used to reconstruct the payload sent from the Microcontroller. This is used to minimize the number
            of calls to pySerial methods, as they are costly to run.
        _accepted_numpy_scalars: Stores numpy types (classes) that can be used as scalar inputs or as 'dtype'
            fields of the numpy arrays that are provided to class methods.
        _minimum_packet_size: Stores the minimum number of bytes that can represent a valid packet. This value is used
            to optimize packet reception logic.

    Raises:
        TypeError: If any of the input arguments are not of the expected type.
        ValueError: If any of the input arguments have invalid values.
    """

    _accepted_numpy_scalars: tuple[
        type[np.uint8],
        type[np.uint16],
        type[np.uint32],
        type[np.uint64],
        type[np.int8],
        type[np.int16],
        type[np.int32],
        type[np.int64],
        type[np.float32],
        type[np.float64],
        type[np.bool],
    ] = (
        np.uint8,
        np.uint16,
        np.uint32,
        np.uint64,
        np.int8,
        np.int16,
        np.int32,
        np.int64,
        np.float32,
        np.float64,
        np.bool,
    )  # Sets up a tuple of types used to verify the transmitted data

    def __init__(
        self,
        port: str,
        microcontroller_serial_buffer_size: int,
        baudrate: int,
        polynomial: CRCType = _POLYNOMIAL,
        initial_crc_value: CRCType = _ZERO,
        final_crc_xor_value: CRCType = _ZERO,
        *,
        test_mode: bool = False,
    ) -> None:
        # Tracks whether the serial port is open. This is used solely to avoid a __del__ error during testing.
        self._opened: bool = False

        # Verifies that input arguments are valid. Does not check polynomial parameters, that is offloaded to the
        # CRCProcessor class.
        if not isinstance(port, str):
            message = (
                f"Unable to initialize TransportLayer class. Expected a string value for 'port' argument, but "
                f"encountered {port} of type {type(port).__name__}."
            )
            console.error(message=message, error=TypeError)

        if not isinstance(baudrate, int) or baudrate <= 0:
            message = (
                f"Unable to initialize TransportLayer class. Expected a positive integer value for 'baudrate' "
                f"argument, but encountered {baudrate} of type {type(baudrate).__name__}."
            )
            console.error(message=message, error=ValueError)

        if not isinstance(microcontroller_serial_buffer_size, int) or microcontroller_serial_buffer_size < 1:
            message = (
                f"Unable to initialize TransportLayer class. Expected a positive integer value for "
                f"'microcontroller_serial_buffer_size' argument, but encountered {microcontroller_serial_buffer_size} "
                f"of type {type(microcontroller_serial_buffer_size).__name__}."
            )
            console.error(message=message, error=ValueError)

        # Based on the class runtime selector, initializes a real or mock serial port manager class
        self._port: SerialMock | Serial
        if not test_mode:
            # Statically disables built-in timeout. Our jit- and c-extension classes are more optimized for this job
            # than Serial's built-in timeout.
            self._port = Serial(port, baudrate, timeout=0)  # pragma: no cover
        else:
            self._port = SerialMock()

        # This verifies input polynomial parameters at class initialization time
        self._crc_processor = CRCProcessor(polynomial, initial_crc_value, final_crc_xor_value)
        self._cobs_processor = COBSProcessor()

        # On very fast CPUs, the timer can be sub-microsecond precise. On older systems, this may not necessarily hold.
        # Either way, microsecond precision is safe for most target systems.
        self._timer = PrecisionTimer(TimerPrecisions.MICROSECOND)

        # Initializes serial packet attributes and casts all to numpy types.
        self._start_byte: np.uint8 = np.uint8(129)
        self._delimiter_byte: np.uint8 = np.uint8(0)
        self._timeout: int = 10000
        self._postamble_size: np.uint8 = self._crc_processor.crc_byte_length

        # Initializes reception and transmission buffers.
        self._max_tx_payload_size: np.uint8 = np.uint8(min((microcontroller_serial_buffer_size - 8), 254))
        self._max_rx_payload_size: np.uint8 = np.uint8(min((microcontroller_serial_buffer_size - 8), 254))
        self._min_rx_payload_size: np.uint8 = np.uint8(1)

        # Buffer sizes are up-case to uint16, as they may need to exceed the 256-size limit. They include the respective
        # payload size, the postamble size (1 to 4 bytes) and 4 static bytes for the preamble and packet metadata.
        # These 4 bytes are: start_byte, delimiter_byte, overhead_byte, and packet_size byte.
        tx_buffer_size: np.uint16 = np.uint16(self._max_tx_payload_size) + 4 + np.uint16(self._postamble_size)
        rx_buffer_size: np.uint16 = np.uint16(self._max_rx_payload_size) + 4 + np.uint16(self._postamble_size)
        self._transmission_buffer: NDArray[np.uint8] = np.zeros(shape=tx_buffer_size, dtype=np.uint8)
        self._reception_buffer: NDArray[np.uint8] = np.empty(shape=rx_buffer_size, dtype=np.uint8)

        # Based on the minimum expected payload size, calculates the minimum number of bytes that can fully represent
        # a packet. This is used to avoid costly pySerial calls unless there is a high chance that the call will return
        # a parsable packet.
        self._minimum_packet_size: int = int(self._min_rx_payload_size) + 4 + int(self._postamble_size)

        # Sets up various tracker and temporary storage variables that supplement class runtime.
        self._bytes_in_transmission_buffer: int = 0
        self._bytes_in_reception_buffer: int = 0
        self._consumed_bytes: int = 0
        self._leftover_bytes: bytes = b""  # Placeholder, this is re-initialized as needed during data reception.

        # Opens (connects to) the serial port. Cycles closing and opening to ensure the port is opened,
        # non-graciously replacing whatever is using the port at the time of instantiating TransportLayer class.
        # This non-safe procedure was implemented to avoid a frequent issue with Windows taking a long time to release
        # COM ports, preventing quick connection cycling.
        self._port.close()
        self._port.open()
        self._opened = True

    def __del__(self) -> None:
        """Ensures that the instance releases all resources prior to being garbage-collected."""
        # Closes the port before deleting the class instance. Not strictly required, but helpful to ensure resources
        # are released
        if self._opened:
            self._port.close()

    def __repr__(self) -> str:
        """Returns a string representation of the class instance."""
        if isinstance(self._port, Serial):  # pragma: no cover
            representation_string = (
                f"TransportLayer(port='{self._port.name}', baudrate={self._port.baudrate}, polynomial="
                f"{self._crc_processor.polynomial}, start_byte={self._start_byte}, "
                f"delimiter_byte={self._delimiter_byte}, timeout={self._timeout} us, "
                f"maximum_tx_payload_size={self._max_tx_payload_size}, "
                f"maximum_rx_payload_size={self._max_rx_payload_size})"
            )
        else:
            representation_string = (
                f"TransportLayer(port & baudrate=MOCKED, polynomial={self._crc_processor.polynomial}, "
                f"start_byte={self._start_byte}, delimiter_byte={self._delimiter_byte}, timeout={self._timeout} us, "
                f"maximum_tx_payload_size={self._max_tx_payload_size}, "
                f"maximum_rx_payload_size={self._max_rx_payload_size})"
            )
        return representation_string

    @property
    def available(self) -> bool:
        """Returns True if enough bytes are available from the serial port to justify attempting to receive a packet."""
        # in_waiting is twice as fast as using the read() method. The 'true' outcome of this check is capped at the
        # minimum packet size to minimize the chance of having to call read() more than once. The method counts the
        # bytes available for reading and left over from previous packet parsing operations.
        return (self._port.in_waiting + len(self._leftover_bytes)) >= self._minimum_packet_size

    @property
    def transmission_buffer(self) -> NDArray[np.uint8]:
        """Returns a copy of the transmission buffer array.

        This buffer stores the 'staged' data to be sent to the Microcontroller. Use this method to safely access the
        contents of the buffer.
        """
        return self._transmission_buffer.copy()

    @property
    def reception_buffer(self) -> NDArray[np.uint8]:
        """Returns a copy of the reception buffer array.

        This buffer stores the decoded data received from the Microcontroller. Use this method to safely access the
        contents of the buffer.
        """
        return self._reception_buffer.copy()

    @property
    def bytes_in_transmission_buffer(self) -> int:
        """Returns the number of payload bytes stored inside the instance's transmission buffer."""
        return self._bytes_in_transmission_buffer

    @property
    def bytes_in_reception_buffer(self) -> int:
        """Returns the number of payload bytes stored inside the instance's reception buffer."""
        return self._bytes_in_reception_buffer

    def reset_transmission_buffer(self) -> None:
        """Resets the instance's transmission buffer, discarding any stored data."""
        self._bytes_in_transmission_buffer = 0

    def reset_reception_buffer(self) -> None:
        """Resets the instance's reception buffer, discarding any stored data."""
        self._bytes_in_reception_buffer = 0
        self._consumed_bytes = 0

    def write_data(
        self,
        data_object: Any,
    ) -> None:
        """Serializes and writes the input object's data to the end of the payload stored in the instance's transmission
        buffer.

        Notes:
            At this time, the method only works with numpy scalars and arrays, as well as python dataclasses entirely
            made out of valid numpy types.

            The maximum runtime speed for this method is achieved when writing data as numpy arrays, which is optimized
            to a single write operation. The minimum runtime speed is achieved by writing dataclasses, as it involves
            looping over dataclass attributes. When writing dataclasses, all attributes are serialized and written
            as a consecutive data block.

        Args:
            data_object: A numpy scalar or array object or a python dataclass made entirely out of valid numpy objects.
                Supported numpy types are: uint8, uint16, uint32, uint64, int8, int16, int32, int64, float32, float64,
                and bool. Arrays have to be 1-dimensional and not empty to be supported.

        Raises:
            TypeError: If the input object is not a supported numpy scalar, numpy array, or python dataclass.
            ValueError: If the transmission buffer does not have enough space to accommodate the written object's data.
                If the input object is a multidimensional or empty numpy array.
        """
        end_index = -10  # Initializes to a specific negative value that is not a valid index or runtime error code

        # Resolves the index at which to start writing the object's data.
        start_index = self._bytes_in_transmission_buffer

        # If the input object is a supported numpy scalar, calls the scalar data writing method.
        if isinstance(data_object, self._accepted_numpy_scalars):
            end_index = self._write_scalar_data(self._transmission_buffer, data_object, start_index)

        # If the input object is a numpy array, first ensures that it's datatype matches one of the accepted scalar
        # numpy types and, if so, calls the array data writing method.
        elif isinstance(data_object, np.ndarray) and data_object.dtype in self._accepted_numpy_scalars:
            end_index = self._write_array_data(self._transmission_buffer, data_object, start_index)

        # If the input object is a python dataclass, iteratively loops over each field of the class and recursively
        # calls write_data() to write each attribute of the class to the buffer. This implementation supports using
        # this function for any dataclass that stores numpy scalars or arrays, replicating the behavior of the
        # Microcontroller TransportLayer class.
        elif is_dataclass(data_object):
            # Loops over each field (attribute) of the dataclass and writes it to the buffer
            # noinspection PyDataclass
            for field in fields(data_object):
                # Calls the write method recursively onto the value of each field
                data_value = getattr(data_object, field.name)

                # If this call fails, it will raise an error that wll terminate this loop early
                self.write_data(data_object=data_value)

            # The recurrent write_data calls resolve errors and update the payload size trackers as necessary, so if
            # the method runs without errors, returns to caller without further processing
            return

        # Unsupported input type error
        else:
            message = (
                f"Failed to write the data to the transmission buffer. Encountered an unsupported input data_object "
                f"type ({type(data_object).__name__}). At this time, only the following numpy scalar or array "
                f"types are supported: {self._accepted_numpy_scalars}. Alternatively, a dataclass with all attributes "
                f"set to supported numpy scalar or array types is also supported."
            )
            console.error(message=message, error=TypeError)

        # If the end_index exceeds the start_index, that means that an appropriate write operation was executed
        # successfully. In that case, updates the _bytes_in_transmission_buffer tracker
        if end_index > start_index:
            self._bytes_in_transmission_buffer = end_index
        elif end_index == TransportLayerStatus.INSUFFICIENT_BUFFER_SPACE_ERROR:
            message = (
                f"Failed to write the data to the transmission buffer. The transmission buffer does not have enough "
                f"space to write the data starting at the index {start_index}. Specifically, given the data size of "
                f"{data_object.nbytes} bytes, the required buffer size is {start_index + data_object.nbytes} bytes, "
                f"but the available size is {self._transmission_buffer.size} bytes."
            )
            console.error(message=message, error=ValueError)
        elif end_index == TransportLayerStatus.MULTIDIMENSIONAL_ARRAY_ERROR:
            message = (
                f"Failed to write the data to the transmission buffer. Encountered a multidimensional numpy array with "
                f"{data_object.ndim} dimensions as input data_object. At this time, only one-dimensional (flat) arrays "
                f"are supported."
            )
            console.error(message=message, error=ValueError)
        elif end_index == TransportLayerStatus.EMPTY_ARRAY_ERROR:
            message = (
                "Failed to write the data to the transmission buffer. Encountered an empty (size 0) numpy array as "
                "input data_object. Writing empty arrays is not supported."
            )
            console.error(message=message, error=ValueError)
        else:
            message = (
                f"Failed to write the data to the transmission buffer. Encountered an unknown error code ({end_index}) "
                f"returned by the writer method."
            )  # pragma: no cover
            console.error(message=message, error=RuntimeError)  # pragma: no cover

            # This fallback is to appease MyPy and will neve rbe reached
            raise RuntimeError(message)  # pragma: no cover

    @staticmethod
    @njit(nogil=True, cache=True)  # type: ignore[misc] # pragma: no cover
    def _write_scalar_data(
        target_buffer: NDArray[np.uint8],
        scalar_object: Any,
        start_index: int,
    ) -> int:
        """Converts the input numpy scalar to a sequence of bytes and writes it to the transmission buffer at the
        specified start_index.

        Args:
            target_buffer: The buffer where to write the data.
            scalar_object: The scalar numpy object to be written to the transmission buffer.
            start_index: The index inside the transmission buffer at which to start writing the data.

        Returns:
            The positive index inside the transmission buffer that immediately follows the last index of the buffer to
            which the data was written. One of the TransportLayerStatus if the method encounters a runtime error.
        """
        # Converts the input scalar to a byte array. This is mostly so that Numba can work with the data via the
        # service method calls below. Note, despite the input being scalar, the array object may have multiple elements.
        array_object = np.frombuffer(np.array([scalar_object]), dtype=np.uint8)  # scalar → array → byte array

        # Calculates the required space inside the buffer to store the data inserted at the start_index
        data_size = array_object.size * array_object.itemsize  # Size of each element * the number of elements
        required_size = start_index + data_size

        # If the space to store the data extends outside the available transmission_buffer boundaries, returns 0.
        if required_size > target_buffer.size:
            return TransportLayerStatus.INSUFFICIENT_BUFFER_SPACE_ERROR.value

        # Writes the data to the buffer.
        target_buffer[start_index:required_size] = array_object

        # Returns the required_size, which incidentally also matches the index that immediately follows the last index
        # of the buffer that was overwritten with the input data.
        return required_size

    @staticmethod
    @njit(nogil=True, cache=True)  # type: ignore[misc] # pragma: no cover
    def _write_array_data(
        target_buffer: NDArray[np.uint8],
        array_object: NDArray[Any],
        start_index: int,
    ) -> int:
        """Converts the input numpy array to a sequence of bytes and writes it to the transmission buffer at the
        specified start_index.

        Args:
            target_buffer: The buffer where to write the data.
            array_object: The numpy array to be written to the transmission buffer.
            start_index: The index inside the transmission buffer at which to start writing the data.

        Returns:
            The positive index inside the transmission buffer that immediately follows the last index of the buffer to
            which the data was written. One of the TransportLayerStatus if the method encounters a runtime error.
        """
        if array_object.ndim != 1:
            return TransportLayerStatus.MULTIDIMENSIONAL_ARRAY_ERROR.value

        if array_object.size == 0:
            return TransportLayerStatus.EMPTY_ARRAY_ERROR.value

        # Calculates the required space inside the buffer to store the data inserted at the start_index
        array_data = np.frombuffer(array_object, dtype=np.uint8)  # Serializes to bytes
        data_size = array_data.size * array_data.itemsize  # Size of each element * the number of elements
        required_size = start_index + data_size

        if required_size > target_buffer.size:
            return TransportLayerStatus.INSUFFICIENT_BUFFER_SPACE_ERROR.value

        # Writes the array data to the buffer, starting at the start_index and ending just before the required_size
        # index
        target_buffer[start_index:required_size] = array_data

        # Returns the required_size, which incidentally also matches the index that immediately follows the last index
        # of the buffer that was overwritten with the input data.
        return required_size

    def read_data(
        self,
        data_object: Any,
    ) -> Any:
        """Overwrites the input object's data with the data from the instance's reception buffer, consuming (discarding)
        all read bytes.

        This method deserializes the objects stored in the reception buffer as a sequence of bytes. Calling this method
        consumes the read bytes, making it impossible to retrieve the same data from the reception buffer again.

        Notes:
            At this time, the method only works with valid numpy scalars and arrays as well as python dataclasses
            entirely made out of valid numpy types.

            The maximum runtime speed of this method is achieved when reading data as numpy arrays, which is
            optimized to a single read operation. The minimum runtime speed is achieved by reading dataclasses, as it
            involves looping over dataclass attributes.

        Args:
            data_object: An initialized numpy scalar or array object or a python dataclass made entirely out of valid
                numpy objects. Supported numpy types are: uint8, uint16, uint32, uint64, int8, int16, int32, int64,
                float32, float64, and bool. Array prototypes have to be 1-dimensional and not empty to be supported.

        Returns:
            The deserialized data object extracted from the instance's reception buffer.

        Raises:
            TypeError: If the input object is not a supported numpy scalar, numpy array, or python dataclass.
            ValueError: If the payload stored inside the reception buffer does not have the enough unconsumed bytes
                available to reconstruct the requested object. If the input object is a multidimensional or empty
                numpy array.
        """
        end_index = -10  # Initializes to a specific negative value that is not a valid index or runtime error code

        # Computes the index at which to start reading the input object's data based on the number of bytes already
        # consumed from the buffer.
        start_index = self._consumed_bytes

        # If the input object is a supported numpy scalar, converts it to a numpy array and calls the read method.
        # Converts the returned one-element array back to a scalar numpy type. Due to current Numba limitations, this
        # is the most efficient available method.
        if isinstance(data_object, self._accepted_numpy_scalars):
            returned_object, end_index = self._read_array_data(
                self._reception_buffer,
                np.array(data_object, dtype=data_object.dtype),
                start_index,
                self._bytes_in_reception_buffer,
            )
            out_object = returned_object[0].copy()

        # If the input object is a numpy array, first ensures that its datatype matches one of the accepted scalar
        # numpy types and, if so, calls the array data reading method.
        elif isinstance(data_object, np.ndarray):
            if data_object.dtype in self._accepted_numpy_scalars:
                out_object, end_index = self._read_array_data(
                    self._reception_buffer,
                    data_object,
                    start_index,
                    self._bytes_in_reception_buffer,
                )

        # If the input object is a python dataclass, enters a recursive loop which calls this method for each class
        # attribute. This allows retrieving and overwriting each attribute with the bytes read from the buffer,
        # similar to the Microcontroller TransportLayer class.
        elif is_dataclass(data_object):
            # Loops over each field of the dataclass
            # noinspection PyDataclass
            for field in fields(data_object):
                # Calls the reader function recursively onto each field of the class
                attribute_value = getattr(data_object, field.name)
                attribute_object = self.read_data(data_object=attribute_value)

                # Updates the field in the original dataclass instance with the read object
                setattr(data_object, field.name, attribute_object)

            # The recurrent read_data calls resolve errors and update the payload size trackers as necessary, so if
            # the method runs without errors, returns to caller without further processing
            return data_object

        # If the input value is not a valid numpy scalar, an array using a valid scalar datatype or a python dataclass,
        # raises TypeError exception.
        else:
            message = (
                f"Failed to read the data from the reception buffer. Encountered an unsupported input data_object "
                f"type ({type(data_object).__name__}). At this time, only the following numpy scalar or array types "
                f"are supported: {self._accepted_numpy_scalars}. Alternatively, a dataclass with all attributes "
                f"set to supported numpy scalar or array types is also supported."
            )
            console.error(message=message, error=TypeError)

        # If end_index is different from the start_index and no error has been raised, the method runtime was
        # successful, so returns the read data_object and the end_index to the caller
        if end_index > start_index:
            # Updates the consumed bytes tracker adn returns the object recreated using data from the buffer
            self._consumed_bytes = end_index
            # noinspection PyUnboundLocalVariable
            return out_object
        if end_index == TransportLayerStatus.INSUFFICIENT_BUFFER_SPACE_ERROR:
            message = (
                f"Failed to read the data from the reception buffer. The reception buffer does not have enough "
                f"unconsumed bytes to recreate the object. Specifically, the object requires {data_object.nbytes} "
                f"bytes, but the available payload size is {self.bytes_in_reception_buffer - self._consumed_bytes} "
                f"bytes."
            )
            console.error(message=message, error=ValueError)
        elif end_index == TransportLayerStatus.MULTIDIMENSIONAL_ARRAY_ERROR:
            message = (
                f"Failed to read the data from the reception buffer. Encountered a multidimensional numpy array with "
                f"{data_object.ndim} dimensions as input data_object. At this time, only one-dimensional (flat) arrays "
                f"are supported."
            )
            console.error(message=message, error=ValueError)
        elif end_index == TransportLayerStatus.EMPTY_ARRAY_ERROR:
            message = (
                "Failed to read the data from the reception buffer. Encountered an empty (size 0) numpy array as "
                "input data_object. Reading empty arrays is not supported."
            )
            console.error(message=message, error=ValueError)

        message = (
            f"Failed to read the data from the reception buffer. Encountered an unknown error code ({end_index})"
            f"returned by the reader method."
        )  # pragma: no cover
        console.error(message=message, error=RuntimeError)  # pragma: no cover

        # Fallback to appease MyPy, will never be reached
        raise RuntimeError(message)  # pragma: no cover

    @staticmethod
    @njit(nogil=True, cache=True)  # type: ignore[misc] # pragma: no cover
    def _read_array_data(
        source_buffer: NDArray[np.uint8],
        array_object: NDArray[Any],
        start_index: int,
        payload_size: int,
    ) -> tuple[NDArray[Any], int]:
        """Reads the requested array_object from the instance's reception buffer.

        Specifically, the object's data is read as bytes and is converted to an array with the appropriate datatype.

        Args:
            source_buffer: The buffer from which to read the data.
            array_object: The numpy array to be read from the _reception_buffer.
            start_index: The index inside the reception buffer at which to start reading the data.
            payload_size: The number of payload bytes currently stored inside the buffer.

        Returns:
            A two-element tuple. The first element is the numpy array that uses the datatype and size derived from the
            input array_object, which holds the extracted data. The second element is the index that immediately follows
            the last index that was read during method runtime to support chained read calls. If method runtime fails,
            returns an empty numpy array as the first element and one of the TransportLayerStatus values as the second
            element.
        """
        # Calculates the end index for the read operation. This is based on how many bytes are required to represent the
        # object and the start_index for the read operation.
        required_size = start_index + array_object.nbytes

        # Prevents reading outside the payload boundaries.
        if required_size > payload_size:
            return np.empty(0, dtype=array_object.dtype), TransportLayerStatus.INSUFFICIENT_BUFFER_SPACE_ERROR.value

        # Prevents reading multidimensional numpy arrays.
        if array_object.ndim > 1:
            return np.empty(0, dtype=array_object.dtype), TransportLayerStatus.MULTIDIMENSIONAL_ARRAY_ERROR.value

        # Prevents reading empty numpy arrays
        if array_object.size == 0:
            return np.empty(0, dtype=array_object.dtype), TransportLayerStatus.EMPTY_ARRAY_ERROR.value

        # Generates a new array using the input data_object datatype and a slice of the byte-buffer that corresponds to
        # the number of bytes necessary to represent the object. Uses copy to ensure the returned object is not sharing
        # the buffer with the source_buffer.
        return (
            np.frombuffer(source_buffer[start_index:required_size], dtype=array_object.dtype).copy(),
            required_size,
        )

    def send_data(self) -> None:
        """Packages the data inside the instance's transmission buffer into a serialized packet and transmits it
        over the communication interface.

        Notes:
            This method resets the instance's transmission buffer after transmitting the data, discarding any data
            stored inside the buffer.
        """
        # Constructs the serial packet to be sent. This is a fast inline aggregation of all packet construction steps,
        # using JIT compilation to increase runtime speed. To maximize compilation benefits, it has to access the
        # inner jitclasses instead of using the python COBS and CRC class wrappers.
        packet = self._construct_packet(
            self._transmission_buffer,
            self._cobs_processor.processor,
            self._crc_processor.processor,
            self._bytes_in_transmission_buffer,
            self._start_byte,
        )

        # Hands the constructed packet off to the communication interface.
        self._port.write(packet.tobytes())

        # Resets the transmission buffer to indicate that the payload was sent and prepare for sending the next
        # payload.
        self.reset_transmission_buffer()

    @staticmethod
    @njit(nogil=True, cache=True)  # type: ignore[misc] # pragma: no cover
    def _construct_packet(
        payload_buffer: NDArray[np.uint8],
        cobs_processor: _COBSProcessor,
        crc_processor: _CRCProcessor,
        payload_size: int,
        start_byte: np.uint8,
    ) -> NDArray[np.uint8]:
        """Constructs the serial packet using the payload stored inside the input buffer.

        Args:
            payload_buffer: The buffer that stores the payload to be encoded into a packet.
            cobs_processor: The inner _COBSProcessor jitclass instance.
            crc_processor: The inner _CRCProcessor jitclass instance.
            payload_size: The number of bytes that makes up the payload.
            start_byte: The byte-value used to mark the beginning of each transmitted packet.

        Returns:
            The constructed serial packet.
        """
        # Extracts the payload from the input buffer and encodes it using the COBS scheme.
        packet = cobs_processor.encode_payload(payload_buffer[:payload_size])

        # Extends the packet's buffer to include the space for the CRC checksum postamble.
        # noinspection PyTypeChecker
        crc_packet = np.empty(len(packet) + crc_processor.crc_byte_length, dtype=np.uint8)
        crc_packet[: len(packet)] = packet

        # Calculates the CRC checksum for the encoded payload and adds it to the end of the crc_packet buffer (to the
        # end of the COBS-encoded packet).
        crc_processor.calculate_checksum(buffer=crc_packet, check=False)

        # Generates the message preamble using start_byte and payload_size.
        preamble = np.array([start_byte, payload_size], dtype=np.uint8)

        # Concatenates the preamble, the encoded payload, and the checksum postamble to form the serial packet
        # and returns the constructed packet to the caller.
        return np.concatenate((preamble, crc_packet))

    def receive_data(self) -> bool:
        """Receives a data packet from the communication interface, verifies its integrity, and decodes its payload into
        the instance's reception buffer.

        Notes:
            Before attempting to receive the packet, the method uses the Available() method to check whether the
            communication interface is likely to store a well-formed packet. It is safe to call this method cyclically
            (as part of a loop) until a packet is received.

            This method resets the instance's reception buffer before attempting to receive the data, discarding any
            potentially unprocessed data.

        Returns:
            True if the packet was successfully received and unpacked and False if the communication interface does not
            contain enough bytes to justify processing the packet.

        Raises:
            RuntimeError: If the method runs into an error while receiving or processing the packet's data.
        """
        # Clears the reception buffer
        self.reset_reception_buffer()

        # Attempts to receive a new packet. If successful, this method saves the received packet to the
        # _transmission_buffer and the size of the packet to the _bytes_in_transmission_buffer tracker. If the method
        # runs into an error, it raises the appropriate RuntimeError.
        if not self._receive_packet():
            # If the packet parsing method does not find any packet bytes to process, it returns False.
            return False

        # If the packet is successfully parsed, validates and unpacks the payload into the class reception buffer
        payload_size = self._process_packet(
            self._reception_buffer,
            self._bytes_in_reception_buffer,
            self._cobs_processor.processor,
            self._crc_processor.processor,
        )

        # Returned payload_size is a positive integer (>= 1) if verification succeeds. If verification
        # succeeds, overwrites the _bytes_in_reception_buffer tracker with the payload size and returns True to
        # indicate runtime success
        if payload_size:
            self._bytes_in_reception_buffer = payload_size
            return True

        # Otherwise, notifies the user about an error processing the packet
        message = (
            "Failed to process the received serial packet. This indicates that the packet was corrupted during "
            "transmission or reception."
        )
        console.error(message=message, error=RuntimeError)

        # Fallback to appease MyPy, will never be reached.
        raise RuntimeError(message)  # pragma: no cover

    def _receive_packet(self) -> bool:
        """Parses the bytes stored in the reception buffer of the communication interface as a serialized packet
        and stores it in the instance's reception buffer.

        Notes:
            For this method to work correctly, the class configuration should exactly match the configuration of the
            TransportLayer class used by the connected Microcontroller.

        Returns:
            True, if the method is able to successfully parse the incoming packet and False if there are no packet
            bytes to parse (valid non-error status).

        Raises:
            RuntimeError: If the method runs into an error while parsing the incoming packet. Broadly, this can be due
                to packet corruption, the mismatch between MicroController and PC TransportLayer instance
                configurations, or the packet transmission staling.
        """
        # Checks whether class buffers contain enough bytes to justify parsing the packet. If not, returns False to
        # indicate graceful (non-error) runtime failure.
        if not self._bytes_available(required_bytes_count=self._minimum_packet_size):
            return False

        # Pre-initializes the variables that support proper iteration of the parsing process below.
        status: int = 150  # This is not a valid status code
        parsed_bytes_count: int = 0
        parsed_bytes: NDArray[np.uint8] = np.empty(shape=0, dtype=np.uint8)
        start_found: bool = False

        # Enters the packet parsing loop. Due to the parsing implementation, the packet can be resolved over at most
        # three iterations of the parsing method. Therefore, this loop is statically capped at 3 iterations.
        for _call_count in range(3):
            # Converts leftover_bytes (bytes) to a numpy uint8 array for compatibility with _parse_packet
            remaining_bytes = np.frombuffer(self._leftover_bytes, dtype=np.uint8).copy()

            # Calls the packet parsing method. The method reuses some iterative outputs as arguments for later
            # calls.
            status, parsed_bytes_count, remaining_bytes, parsed_bytes = self._parse_packet(
                remaining_bytes,
                self._start_byte,
                self._delimiter_byte,
                self._max_rx_payload_size,
                self._min_rx_payload_size,
                self._postamble_size,
                start_found,
                parsed_bytes_count,
                parsed_bytes,
            )

            # Convert remaining_bytes_np (numpy array) back to bytes after function runtime
            self._leftover_bytes = remaining_bytes.tobytes()
            # Resolves parsing result:
            # Packet parsed. Saves the packet to the _reception_buffer and the packet size to the
            # _bytes_in_reception_buffer tracker.
            if status == 1:
                self._reception_buffer[: parsed_bytes.size] = parsed_bytes
                self._bytes_in_reception_buffer = parsed_bytes.size  # Includes encoded payload + CRC postamble!
                return True  # Success code

            # Partial success status. The method was able to resolve the start_byte, but not the payload_size. This
            # means that the method does not know the exact number of bytes needed to fully resolve the packet. The
            # expectation is that the next byte after the start_byte is the payload_size byte. Therefore, technically,
            # only one additional byte needs to be available to justify the next iteration of packet parsing. However,
            # to minimize the number of serial interface calls, _bytes_available() blocks until there are enough bytes
            # to fully cover the minimum packet size -1 (-1 is to account for already processed start_byte). This
            # maximizes the chances of successfully parsing the full packet during iteration 2. That said, since the
            # exact size of the packet is not known, iteration 3 may be necessary.
            if status == TransportLayerStatus.PACKET_SIZE_UNKNOWN and not self._bytes_available(
                required_bytes_count=self._minimum_packet_size - 1, timeout=self._timeout
            ):
                # The only way for _bytes_available() to return False is due to timeout guard aborting additional bytes'
                # reception.
                message = (
                    f"Failed to parse the size of the incoming serial packet. The packet size byte was not received in "
                    f"time ({self._timeout} microseconds), following the reception of the START byte."
                )
                console.error(message=message, error=RuntimeError)

                # This explicit fallback terminator is here to appease Mypy and will never be reached.
                raise RuntimeError(message)  # pragma: no cover

            # Partial success status. This is generally similar to status 0 with one notable exception. Status 2 means
            # that the payload size was parsed and, therefore, the exact number of bytes making up the processed packet
            # is known. This method, therefore, blocks until the class is able to receive enough bytes to fully
            # represent the packet or until the reception timeout.
            if status == TransportLayerStatus.NOT_ENOUGH_PACKET_BYTES and not self._bytes_available(
                required_bytes_count=parsed_bytes.size - parsed_bytes_count, timeout=self._timeout
            ):
                # The only way for _bytes_available() to return False is due to timeout guard aborting additional bytes'
                # reception.
                message = (
                    f"Failed to parse the incoming serial packet data. The byte number {parsed_bytes_count + 1} "
                    f"out of {parsed_bytes.size} was not received in time ({self._timeout} microseconds), "
                    f"following the reception of the previous byte. Packet reception staled."
                )
                console.error(message=message, error=RuntimeError)

                # This explicit fallback terminator is here to appease Mypy and will never be reached.
                raise RuntimeError(message)  # pragma: no cover

            # A separate error message that specifically detects status 3: Not enough bytes to resolve the CRC
            # postamble. Technically, this error should not be possible (it is the terminal runtime status for the
            # packet parsing method). However, it is implemented to avoid confusion with status 2 and 0.
            if status == TransportLayerStatus.NOT_ENOUGH_CRC_BYTES and not self._bytes_available(
                required_bytes_count=parsed_bytes.size - parsed_bytes_count, timeout=self._timeout
            ):
                # The only way for _bytes_available() to return False is due to timeout guard aborting additional bytes'
                # reception.
                message = (
                    f"Failed to parse the incoming serial packet's CRC postamble. The byte number "
                    f"{parsed_bytes_count + 1} out of {parsed_bytes.size} was not received in time "
                    f"({self._timeout} microseconds), following the reception of the previous byte. Packet reception "
                    f"staled."
                )  # pragma: no cover
                console.error(message=message, error=RuntimeError)  # pragma: no cover

                # This explicit fallback terminator is here to appease Mypy and will never be reached.
                raise RuntimeError(message)  # pragma: no cover

            # If _bytes_available() method returned true for status codes 1 to 3, that means that additional bytes were
            # received in time and the loop has to be cycled again to process newly received bytes.
            if status <= TransportLayerStatus.NOT_ENOUGH_CRC_BYTES:
                continue

            # Any code other than partial or full success code is interpreted as the terminal code. All codes other
            # than 101 are error codes. Code 101 is a non-error non-success terminal code. This clause also contains
            # the resolution for unexpected status codes.

            # No packet to receive. This is a non-error terminal status.
            if status == TransportLayerStatus.NO_BYTES_TO_READ:
                return False  # Non-error, non-success return code

            # Parsed payload size is not within the boundaries specified by the minimum and maximum payload sizes.
            if status == TransportLayerStatus.PAYLOAD_SIZE_MISMATCH:
                message = (
                    f"Failed to parse the incoming serial packet data. The parsed size of the COBS-encoded payload "
                    f"({parsed_bytes.size}), is outside the expected boundaries "
                    f"({self._min_rx_payload_size} to {self._max_rx_payload_size}). This likely indicates a "
                    f"mismatch in the transmission parameters between this system and the Microcontroller."
                )

            # Delimiter byte value was encountered before reaching the end of the COBS-encoded payload data region.
            # 'expected number' is calculated like this: parsed_bytes has space for the encoded packet + CRC. So, to get
            # the expected delimiter byte number, we just subtract the CRC size from the parsed_bytes size.
            elif status == TransportLayerStatus.DELIMITER_FOUND_TOO_EARLY:
                message = (
                    f"Failed to parse the incoming serial packet data. Delimiter byte value ({self._delimiter_byte}) "
                    f"encountered at payload byte number {parsed_bytes_count}, instead of the expected byte number "
                    f"{parsed_bytes.size - int(self._postamble_size)}. This likely indicates packet corruption or "
                    f"mismatch in the transmission parameters between this system and the Microcontroller."
                )

            # The last COBS-encoded payload (encoded packet's) data value does not match the expected delimiter byte
            # value.
            elif status == TransportLayerStatus.DELIMITER_NOT_FOUND:
                message = (
                    f"Failed to parse the incoming serial packet data. Delimiter byte value ({self._delimiter_byte}) "
                    f"expected as the last encoded packet byte ({parsed_bytes.size - int(self._postamble_size)}), but "
                    f"instead encountered {parsed_bytes[parsed_bytes_count - 1]}. This likely indicates packet "
                    f"corruption or mismatch in the transmission parameters between this system and the "
                    f"Microcontroller."
                )

            # Unknown status_code. Reaching this clause should not be possible. This is a static guard to help
            # developers during future codebase updates.
            else:  # pragma: no cover
                break  # Breaks the loop, which issues the 'unknown status code' message

            # Raises the resolved error message as RuntimeError.
            console.error(message=message, error=RuntimeError)

        # The static guard for unknown status code. This is moved to the end of the message to appease MyPy.
        message = (
            f"Failed to parse the incoming serial packet data. Encountered an unknown status value "
            f"{status}, returned by the _receive_packet() method. Manual user intervention is required to "
            f"resolve the issue."
        )  # pragma: no cover
        # Raises the resolved error message as RuntimeError.
        console.error(message=message, error=RuntimeError)  # pragma: no cover

        # This explicit fallback terminator is here to appease Mypy and will never be reached.
        raise RuntimeError(message)  # pragma: no cover

    def _bytes_available(self, required_bytes_count: int = 1, timeout: int = 0) -> bool:
        """Determines if the required number of bytes is available across all class buffers that store unprocessed
        serial stream bytes.

        Notes:
            This method is primarily designed to optimize packet processing speed by minimizing the number of calls to
            the serial interface methods.

        Args:
            required_bytes_count: The number of bytes that needs to be available across all instance's buffers that
                store unprocessed bytes for this method to return True.
            timeout: The maximum number of microseconds that can pass between the serial port receiving any two
                consecutive bytes. Using a non-zero timeout allows the method to briefly block and wait for the
                required number of bytes to become available, as long as the serial port keeps receiving new bytes.

        Returns:
            True if enough bytes are available at the end of this method's runtime to justify parsing the packet.
        """
        # Tracks the number of bytes available from the leftover_bytes buffer
        available_bytes = len(self._leftover_bytes)

        # If the requested number of bytes is already available from the leftover_bytes buffer, returns True.
        if available_bytes >= required_bytes_count:
            return True

        # If there are not enough leftover bytes to satisfy the requirement, enters a timed loop that waits for
        # the serial port to receive additional bytes. The serial port has its own buffer, and it takes a
        # comparatively long time to view and access that buffer. Hence, this is a 'fallback' procedure.
        self._timer.reset()  # Resets the timer before entering the loop
        previous_additional_bytes = 0  # Tracks how many bytes were available during the previous iteration of the loop
        once = True  # Allows the loop below to run once even if timeout is 0
        while self._timer.elapsed < timeout or once:
            # Deactivates the 'once' condition to make future loop iterations correctly depend on timeout
            if once:
                once = False

            additional_bytes = self._port.in_waiting  # Returns the number of bytes that can be read from serial port.
            total_bytes = available_bytes + additional_bytes  # Combines leftover and serial port bytes.

            # If the combined total matches the required number of bytes, reads additional bytes into the leftover_bytes
            # buffer and returns True.
            if total_bytes >= required_bytes_count:
                self._leftover_bytes += self._port.read(
                    additional_bytes
                )  # This takes twice as long as the 'available' check
                return True

            # If the total number of bytes was not enough, checks whether serial port has received any additional bytes
            # since the last loop iteration. This is primarily used to reset the timer upon new bytes' reception.
            if previous_additional_bytes < additional_bytes:  # pragma: no cover
                previous_additional_bytes = additional_bytes  # Updates the byte tracker, if necessary
                self._timer.reset()  # Resets the timeout timer as long as the port receives additional bytes

        # If there are not enough bytes across both buffers, returns False.
        return False

    @staticmethod
    @njit(nogil=True, cache=True)  # type: ignore[misc] # pragma: no cover
    def _parse_packet(
        unparsed_bytes: NDArray[np.uint8],
        start_byte: np.uint8,
        delimiter_byte: np.uint8,
        max_payload_size: np.uint8,
        min_payload_size: np.uint8,
        postamble_size: np.uint8,
        start_found: bool = False,
        parsed_byte_count: int = 0,
        parsed_bytes: NDArray[np.uint8] = _EMPTY_ARRAY,
    ) -> tuple[int, int, NDArray[np.uint8], NDArray[np.uint8]]:
        """Parses as much of the incoming serialized packet's data as possible using the input unparsed_bytes object.

        Notes:
            It is common for the method to not advance through all parsing stages during a single call, requiring
            multiple calls to fully parse the packet. The method is written in a way that supports iterative calls to
            work on the same packet.

            For this method, the 'packet' refers to the COBS encoded payload + the CRC checksum postamble. While each
            received byte stream also necessarily includes the metadata preamble, the preamble data is used and
            discarded during this method's runtime.

        Args:
            unparsed_bytes: A bytes() object that stores the serial stream bytes ot be parsed.
            start_byte: The byte-value used to mark the beginning of a transmitted packet in the byte-stream.
            delimiter_byte: The byte-value used to mark the end of a transmitted packet in the byte-stream.
            max_payload_size: The maximum size of the payload, in bytes, that can be received.
            min_payload_size: The minimum size of the payload, in bytes, that can be received.
            postamble_size: The number of bytes needed to store the CRC checksum.
            start_found: Iterative argument. When this method is called two or more times, this value can be provided
                to the method to skip resolving the start byte (detecting packet presence).
            parsed_byte_count: Iterative parameter. When this method is called multiple times, this value communicates
                how many bytes out of the expected byte number have been parsed by the previous method runtime.
            parsed_bytes: Iterative parameter. This object is initialized to the expected packet size once it is parsed.
                Multiple method runtimes may be necessary to fully fill the object with parsed data bytes.

        Returns:
            A tuple of four elements. The first element is an integer status code that describes the runtime. The
            second element is the number of packet's bytes processed during method runtime. The third element is a
            bytes' object that stores any unprocessed bytes that remain after method runtime. The fourth element
            is the uint8 array that stores some or all of the packet's bytes.
        """
        # Converts the input 'bytes' object to a numpy array to optimize further buffer manipulations
        total_bytes = unparsed_bytes.size  # Calculates the total number of bytes available for parsing
        processed_bytes = 0  # Tracks how many input bytes are processed during method runtime
        remaining_bytes: NDArray[np.uint8]

        # Stage 1: Resolves the start_byte. Detecting the start byte tells the method the processed byte-stream contains
        # a packet that needs to be parsed.
        if not start_found:
            # Loops over available bytes until the start byte is found or the method runs out of bytes to evaluate
            for i in range(total_bytes):
                processed_bytes += 1  # Increments the counter for each evaluated byte

                # If the start byte is found, breaks the loop and sets the start byte acquisition flag to True
                if unparsed_bytes[i] == start_byte:
                    start_found = True
                    break

            # If the loop above terminates without finding the start byte, ends method runtime with the appropriate
            # status code.
            if not start_found:
                remaining_bytes = np.empty(0, dtype=np.uint8)  # The loop above used all unprocessed bytes
                return TransportLayerStatus.NO_BYTES_TO_READ.value, parsed_byte_count, remaining_bytes, parsed_bytes

            # If this stage uses up all unprocessed bytes, ends method runtime with partial success code
            if processed_bytes == total_bytes:
                remaining_bytes = np.empty(0, dtype=np.uint8)  # The loop above used all unprocessed bytes
                return TransportLayerStatus.PACKET_SIZE_UNKNOWN.value, parsed_byte_count, remaining_bytes, parsed_bytes

        # Calculates the size of the COBS-encoded payload (data packet) from the total size of the parsed_bytes
        # array and the crc_postamble. Ensures the value is always non-negative. Relies on the fact that stage 2
        # initializes the parsed_bytes array to have enough space for the COBS-encoded payload and the crc_postamble.
        # Assumes that the default parsed_bytes array is an empty (size 0) array.
        packet_size = max(parsed_bytes.size - int(postamble_size), 0)

        # Stage 2: Resolves the packet_size. Packet size is essential for knowing how many bytes need to be read to
        # fully parse the packet. Additionally, this is used to infer the packet layout, which is critical for the
        # following stages.
        if packet_size == 0:
            # Reads the first available unprocessed byte and checks it for validity. This relies on the fact that
            # valid packets store the payload_size byte immediately after the start_byte.
            payload_size = unparsed_bytes[processed_bytes]

            processed_bytes += 1  # Increments the counter. Has to be done after reading the byte above.

            # Verifies that the payload size is within the expected payload size limits. If payload size is out of
            # bounds, returns with an error code.
            if not min_payload_size <= payload_size <= max_payload_size:
                remaining_bytes = unparsed_bytes[processed_bytes:].copy()  # Returns any remaining unprocessed bytes
                parsed_bytes = np.empty(payload_size, dtype=np.uint8)  # Uses invalid size for the array shape anyway
                return (
                    TransportLayerStatus.PAYLOAD_SIZE_MISMATCH.value,
                    parsed_byte_count,
                    remaining_bytes,
                    parsed_bytes,
                )

            # If payload size passed verification, calculates the number of bytes occupied by the COBS-encoded payload
            # and the CRC postamble. Specifically, uses the payload_size and increments it with +2 to account for the
            # overhead and delimiter bytes introduced by COBS-encoding the packet. Also adds the size of the CRC
            # postamble.
            remaining_size = int(payload_size) + 2 + int(postamble_size)

            # Uses the calculated size to pre-initialize the parsed_bytes array to accommodate the encoded payload and
            # the CRC postamble. Subsequently, the size of the array will be used to infer the size of the encoded
            # payload.
            parsed_bytes = np.empty(shape=remaining_size, dtype=np.uint8)

            # If this stage uses up all unprocessed bytes, ends method runtime with partial success code
            if processed_bytes == total_bytes:
                remaining_bytes = np.empty(0, dtype=np.uint8)  # The loop above used all unprocessed bytes
                return (
                    TransportLayerStatus.NOT_ENOUGH_PACKET_BYTES.value,
                    parsed_byte_count,
                    remaining_bytes,
                    parsed_bytes,
                )
            # Recalculates the packet size to match the size of the expanded array. Otherwise, if all stages are
            # resolved as part of the same cycle, the code below will continue working with the assumption that the
            # packet size is 0.
            packet_size = max(parsed_bytes.size - int(postamble_size), 0)

        # Based on the size of the packet and the number of already parsed packet bytes, calculates the remaining
        # number of bytes. Ensures the resultant value is always non-negative. If this value is 0, stage 3 is skipped.
        remaining_packet_bytes = max((packet_size - parsed_byte_count), 0)

        # Stage 3: Resolves the COBS-encoded payload. This is the variably sized portion of the stream that contains
        # communicated data with some service values.
        if remaining_packet_bytes != 0:
            # Adjusts loop indices to account for bytes that might have been processed prior to this step
            for i in range(processed_bytes, total_bytes):
                # Transfers the evaluated byte from the unparsed buffer into the parsed buffer.
                # Uses parsed_byte_count as writing index to sequentially fill the array with data over potentially
                # multiple iterations of this method
                parsed_bytes[parsed_byte_count] = unparsed_bytes[i]

                processed_bytes += 1  # Increments the processed bytes counter
                parsed_byte_count += 1  # Unlike processed_bytes, this tracker is shared by multiple method calls.
                remaining_packet_bytes -= 1  # Decrements remaining packet bytes counter with each processed byte

                # If the evaluated byte matches the delimiter byte value and this is not the last byte of the encoded
                # payload, the packet is likely corrupted. Returns with error code 104: Delimiter byte encountered too
                # early.
                if unparsed_bytes[i] == delimiter_byte and remaining_packet_bytes != 0:
                    remaining_bytes = unparsed_bytes[processed_bytes:].copy()  # Returns any remaining unprocessed bytes
                    return (
                        TransportLayerStatus.DELIMITER_FOUND_TOO_EARLY.value,
                        parsed_byte_count,
                        remaining_bytes,
                        parsed_bytes,
                    )

                # If the evaluated byte is a delimiter byte value and this is the last byte of the encoded payload, the
                # payload is fully parsed. Gracefully breaks the loop and advances to the CRC postamble parsing stage.
                if unparsed_bytes[i] == delimiter_byte and remaining_packet_bytes == 0:
                    break

                # If the last evaluated payload byte is not a delimiter byte value, this also indicates that the
                # packet is likely corrupted. Returns with code 105: Delimiter byte not found.
                if remaining_packet_bytes == 0 and unparsed_bytes[i] != delimiter_byte:
                    remaining_bytes = unparsed_bytes[processed_bytes:].copy()  # Returns any remaining unprocessed bytes
                    return (
                        TransportLayerStatus.DELIMITER_NOT_FOUND.value,
                        parsed_byte_count,
                        remaining_bytes,
                        parsed_bytes,
                    )

            # If this stage uses up all unprocessed bytes, ends method runtime with partial success code
            if total_bytes - processed_bytes == 0:
                remaining_bytes = np.empty(0, dtype=np.uint8)  # The loop above used all unprocessed bytes
                return (
                    TransportLayerStatus.NOT_ENOUGH_PACKET_BYTES.value,
                    parsed_byte_count,
                    remaining_bytes,
                    parsed_bytes,
                )

        # If the packet is fully resolved at this point, terminates the runtime before advancing to stage 4. While this
        # is likely not possible, this guard would catch a case where the CRC payload is fully resolved when the
        # execution reaches this point.
        if parsed_bytes.size == parsed_byte_count:
            remaining_bytes = unparsed_bytes[processed_bytes:].copy()
            return TransportLayerStatus.PACKET_PARSED.value, parsed_byte_count, remaining_bytes, parsed_bytes
        # Otherwise, determines how many CRC bytes are left to parse
        remaining_crc_bytes = parsed_bytes.size - parsed_byte_count

        # Stage 4: Resolves the CRC checksum postamble. This is the static portion of the stream that follows the
        # encoded payload. This is used for payload data integrity verification.
        for i in range(processed_bytes, total_bytes):
            # Transfers the evaluated byte from the unparsed buffer into the parsed buffer
            parsed_bytes[parsed_byte_count] = unparsed_bytes[i]

            processed_bytes += 1  # Increments the processed bytes counter
            parsed_byte_count += 1  # Increments the parsed packet and postamble byte tracker
            remaining_crc_bytes -= 1  # Decrements remaining CRC bytes counter with each processed byte

            # If all crc bytes have been parsed, the packet is also fully parsed. Returns with success code.
            if remaining_crc_bytes == 0:
                remaining_bytes = unparsed_bytes[processed_bytes:].copy()
                return TransportLayerStatus.PACKET_PARSED.value, parsed_byte_count, remaining_bytes, parsed_bytes

        # The only way to reach this point is when the CRC parsing loop above escapes due to running out of bytes to
        # process without fully parsing the postamble. Returns with partial success code
        remaining_bytes = np.empty(0, dtype=np.uint8)  # The loop above used all unprocessed bytes
        return TransportLayerStatus.NOT_ENOUGH_CRC_BYTES.value, parsed_byte_count, remaining_bytes, parsed_bytes

    @staticmethod
    @njit(nogil=True, cache=True)  # type: ignore[misc] # pragma: no cover
    # pragma: no cover
    def _process_packet(
        reception_buffer: NDArray[np.uint8],
        packet_size: int,
        cobs_processor: _COBSProcessor,
        crc_processor: _CRCProcessor,
    ) -> int:
        """Validates the parsed data packet by verifying its integrity, decodes the COBS-encoded payload, and saves it
        back to the input reception_buffer.

        Notes:
            This method expects the packet to be stored inside the reception_buffer and writes the decoded payload back
            to the reception_buffer.

        Args:
            reception_buffer: The buffer that stores the packet to be processed.
            packet_size: The size of the packet ot be processed, in bytes.
            cobs_processor: The inner _COBSProcessor jitclass instance.
            crc_processor: The inner _CRCProcessor jitclass instance.

        Returns:
             The size of the decoded payload if the method succeeds or 0 if the method runtime fails.
        """
        # Extracts the packet from the reception buffer. The methods below assume the entirety of the input buffer
        # stores the data to be processed, which is likely not true for the input reception buffer. The reception buffer
        # is statically initialized to have enough space to store the maximum supported payload size.
        packet = reception_buffer[:packet_size]

        # Checks the packet's integrity. The result is 1 if the packet's data is intact and 0 if it is corrupted.
        result = crc_processor.calculate_checksum(buffer=packet, check=True)
        if not result:
            return 0  # Aborts with an error

        # Removes the CRC bytes from the end of the packet, as they are no longer necessary after the CRC verification
        packet = packet[: packet.size - int(crc_processor.crc_byte_length)]

        # Decodes the COBS-encoded payload from the packet
        payload = cobs_processor.decode_payload(packet=packet)
        if payload.size == 0:
            return 0  # Aborts with an error

        # If decoding succeeds, copies the decoded payload over to the reception buffer and returns the positive size
        # of the payload to caller to indicate runtime success. The returned size should always be above 0 if this
        # stage is reached
        reception_buffer[: payload.size] = payload
        return payload.size
