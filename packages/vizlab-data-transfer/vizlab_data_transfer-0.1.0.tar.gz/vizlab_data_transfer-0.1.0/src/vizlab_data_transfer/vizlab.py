import socket
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import struct
from PIL import Image
import ipaddress
import os
import json
import pandas as pd
import astropy

IP = None  # VizLab's local IP address
PORT = None  # VizLab's port number

"""
TODO: Python objects to support:
* astropy coordinates
* HDF5 objects via h5py
* pynbody simulation objects
"""

"""
Send provided data to the VizLab.

Args:
    info (obj or list(obj)): Data to send.
"""


def send(info):
    if not _network_info_is_valid():
        return

    # Initialize socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect to socket
    s.connect((IP, PORT))

    # Get byte data
    byteData = _serialize_data(info)

    # Send to system via socket
    s.sendall(byteData)

    # Receive response message from system
    header = s.recv(4)
    size = int.from_bytes(header)
    messageBytes = s.recv(size)
    message = messageBytes.decode("utf-8")

    print(message)
    return message


"""
Wait to receive data from the VizLab.

Returns:
    data (ndarray): Deserialized data from the VizLab.
"""


def receive():
    if not _network_info_is_valid():
        return

    # Initialize socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect to socket
    s.connect((IP, PORT))

    # Receive and process header
    # header info: DataSize (int), NumDims (int), NumTypes(int)
    dataSize = int.from_bytes(s.recv(4), byteorder="little")
    numDims = int.from_bytes(s.recv(4), byteorder="little")
    numTypes = int.from_bytes(s.recv(4), byteorder="little")

    # Pull out info based on header
    dimsBytes = s.recv(4 * numDims)
    dims = list(struct.unpack("<" + "I" * numDims, dimsBytes))

    typesBytes = s.recv(4 * numTypes)
    types = list(struct.unpack("<" + "I" * numTypes, typesBytes))

    byteData = s.recv(dataSize)

    # Deserialize data and return
    data = _deserialize_data(byteData, dims, types)
    return data


"""
Set the module's config-backed IP address, if the provided address is valid.

Args:
    ip (string): Desired IP address
"""


def set_ip(ip):
    global IP
    if IP == None:
        _retrieve_network_info()

    try:
        ipaddress.ip_address(
            ip
        )  # use ipaddress module to check validity of given address

        
        IP = ip # update current module state

        # update config state
        _write_to_config("IP", IP)
        print(f"IP successfully set to {IP}.")
        return True

    except:
        raise ValueError("The given IP address is not valid.")


"""
Returns the current IP address stored in a global variable (and locally backed by config.json)

Returns:
    IP (string): Current module IP address
"""


def get_ip():
    global IP
    if IP == None:
        _retrieve_network_info()

    return IP


"""
Set the module's config-backed port number, if the provided port is valid.

Args:
    port (int or valid string format): Desired port
"""


def set_port(port):
    global PORT
    if PORT == None:
        _retrieve_network_info()
    try:
        if int(port) < 0 or int(port) > 65535:
            raise ValueError("The given port number is not valid.")
        else:
            PORT = port

            _write_to_config("PORT", PORT)
            print(f"Port number successfully set to {PORT}.")
            return True
    except:
        raise ValueError("The given port number is not valid.")


"""
Returns the current port number stored in a global variable (and locally backed by config.json)

Returns:
    PORT (int): Current module port
"""


def get_port():
    global PORT
    if PORT == None:
        _retrieve_network_info()

    return PORT


## Managing network state


def _network_info_is_valid():
    # create config file if we don't have one
    if IP == None or PORT == None:
        _retrieve_network_info()

    ip_valid = _ip_is_valid(IP)
    port_valid = _port_is_valid(PORT)
    if not ip_valid and not port_valid:
        raise ValueError(
            f"The current IP address {IP} and port number {PORT} is not valid. Please use the 'set_ip' and 'set_port' methods to fix this!"
        )
    elif not ip_valid:
        raise ValueError(
            f"The current IP address {IP} is not valid. Please use the 'set_ip' method to fix this!"
        )
    elif not port_valid:
        raise ValueError(
            f"The current port number {PORT} is not valid. Please use the 'set_port' method to fix this!"
        )

    return True


def _retrieve_network_info():
    # pull data from config file
    if not os.path.isfile("config.json"):
        _write_to_config("IP", None)
        _write_to_config("PORT", None)

    with open("config.json", "r") as f:
        data = json.load(f)

        global IP
        IP = data["IP"]

        global PORT
        PORT = data["PORT"]


def _ip_is_valid(ip):
    try:
        ipaddress.ip_address(ip)
        return True
    except:
        return False


def _port_is_valid(port):
    try:
        if int(port) < 0 or int(port) > 65535:
            return False
        return True
    except:
        return False


def _reset_socket_state():
    global IP
    IP = None

    global PORT
    PORT = None
    _write_to_config("IP", IP)
    _write_to_config("PORT", PORT)


def _write_to_config(key, value):
    ip = IP if key != "IP" else value
    port = PORT if key != "PORT" else value
    data = {"IP": ip, "PORT": port}
    with open("config.json", "w") as json_file:
        json.dump(data, json_file, indent=4)


## Data serialization


def _serialize_data(info):

    if isinstance(info, list):
        byteArray = bytearray()
        for i in range(len(info)):
            finalBlock = True if i == len(info) - 1 else False
            byteArray.extend(_serialize_single_data(info[i], finalBlock))
        return byteArray
    else:
        return _serialize_single_data(info, True)


def _serialize_single_data(info, is_final_block):

    if isinstance(info, np.ndarray) and info.dtype.names is None:
        return _serialize_ndarray_data(info, is_final_block)
    elif isinstance(info, plt.Figure):
        return _serialize_mpl_data(info, is_final_block)
    elif isinstance(info, Image.Image):
        return _serialize_pil_data(info, is_final_block)
    elif isinstance(info, np.ndarray) and info.dtype.names is not None:
        return _serialize_recarray_data(info, is_final_block)
    elif isinstance(info, pd.DataFrame):
        return _serialize_pandas_data(info, is_final_block)
    elif isinstance(info, astropy.table.Table):
        return _serialize_astropy_table_data(info, is_final_block)
    elif isinstance(info, astropy.io.fits.ImageHDU):
        return _serialize_astropy_image_data(info, is_final_block)
    else:
        raise ValueError(
            "Provided Python objects must be one of the following types: numpy ndarray or recarray, pandas dataframe, astropy FITS table, matplotlib figure, PIL image."
        )


def _serialize_header(size_in_bytes, dims, dtypes, name, unit, is_final_block):

    block_value = 1 if is_final_block else 0
    content_header = (
        size_in_bytes.to_bytes(4, byteorder="little")
        + len(dims).to_bytes(4, byteorder="little")
        + len(dtypes).to_bytes(4, byteorder="little")
        + len(name).to_bytes(4, byteorder="little")
        + len(unit).to_bytes(4, byteorder="little")
        + (block_value).to_bytes(4, byteorder="little")
    )
    dims_header = b"".join([i.to_bytes(4, byteorder="little") for i in dims])
    dtypes_header = b"".join([i.to_bytes(1, byteorder="little") for i in dtypes])
    name_header = name.encode("utf-8")
    unit_header = unit.encode("utf-8")

    return content_header + dims_header + dtypes_header + name_header + unit_header


def _serialize_ndarray_data(arr, is_final_block=False):

    # Serialize data
    data = arr.tobytes()

    # Serialize header info
    header = _serialize_header(
        arr.nbytes,
        arr.shape,
        [_get_internal_dtype(arr.dtype)],
        "dataset",
        "dimensionless",
        is_final_block,
    )

    return header + data


def _serialize_astropy_image_data(img, is_final_block=False):
    return _serialize_ndarray_data(img.data, is_final_block=False)


def _serialize_recarray_data(arr, is_final_block=False):

    # Serialize data
    data = arr.tobytes()

    # Serialize header info
    header = _serialize_header(
        arr.nbytes,
        arr.shape + (len(arr.dtype.names),),
        _get_internal_dtypes(arr.dtype),
        _combine_string_list(arr.dtype.names),
        "dimensionless",
        is_final_block,
    )

    return header + data


def _serialize_pandas_data(df, is_final_block=False):
    # Convert dataframe to np.recarray, then serialize that
    return _serialize_recarray_data(df.to_records(), is_final_block)


def _serialize_astropy_table_data(table, is_final_block=False):
    # Convert FITS table to np.recarray, then serialize that
    return _serialize_recarray_data(table.as_array(), is_final_block)


def _serialize_mpl_data(fig, is_final_block=False):

    # Convert plot to a byte-stored image
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=300)
    buf.seek(0)  # Rewind the buffer to the beginning
    data = bytearray(buf.getvalue())

    # Serialize header info
    header = _serialize_header(
        buf.getbuffer().nbytes,
        [int(i) for i in list(fig.get_size_inches())] * 300,
        [10],
        "dataset",
        "dimensionless",
        is_final_block,
    )

    return header + data


def _serialize_pil_data(img, is_final_block=False):

    # Convert PIL Image class to a byte-stored image
    buf = BytesIO()
    img.save(buf, format="PNG")
    data = buf.getvalue()

    # Serialize header info
    header = _serialize_header(
        buf.getbuffer().nbytes,
        list(img.size),
        [10],
        "dataset",
        "dimensionless",
        is_final_block,
    )

    return header + data


def _combine_string_list(lst):
    combined_string = ""
    for i in range(len(lst)):
        combined_string += lst[i]
        combined_string += (
            "\0" if i < len(lst) - 1 else ""
        )  # use null terminator to split in C#
    return combined_string


def _get_internal_dtype(numpy_dtype):
    if numpy_dtype is np.dtype(np.int8):
        return 0
    elif numpy_dtype is np.dtype(np.uint8):
        return 1
    elif numpy_dtype is np.dtype(np.int16):
        return 2
    elif numpy_dtype is np.dtype(np.uint16):
        return 3
    elif numpy_dtype is np.dtype(np.int32):
        return 4
    elif numpy_dtype is np.dtype(np.uint32):
        return 5
    elif numpy_dtype is np.dtype(np.int64):
        return 6
    elif numpy_dtype is np.dtype(np.uint64):
        return 7
    elif numpy_dtype is np.dtype(np.float32):
        return 8
    elif numpy_dtype is np.dtype(np.float64):
        return 9
    else:
        raise ValueError(
            "Provided ndarray must be one of the following datatypes: np.int/uint(8, 16, 32, 64), np.float(16, 32, 64)"
        )


def _get_internal_dtypes(recarray_dtype):
    dtypes = []
    for i in recarray_dtype.names:
        dtypes.append(_get_internal_dtype(recarray_dtype[i]))
    return dtypes


## Data deserialization


def _deserialize_data(data, dims, dtype):
    try:
        # convert to numpy array based on data info
        flat = np.frombuffer(data, dtype=_get_numpy_dtype(dtype))
        reshaped = flat.reshape(tuple(dims))
        return reshaped
    except:
        raise ValueError("Received server data not in acceptable format.")


def _get_numpy_dtype(internal_type):
    return np.float32
