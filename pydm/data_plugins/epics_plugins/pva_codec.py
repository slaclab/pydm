import io
import logging
import numpy as np
from functools import reduce
from p4p.wrapper import Value

logger = logging.getLogger(__name__)


ScalarType = (
    bool,
    np.int8,
    np.int16,
    np.int32,
    np.int64,  # same as np.long
    np.uint8,
    np.uint16,
    np.uint32,
    np.uint64,
    float,
    np.double,
)


codecs = {}


def decompress(structure: Value):
    """
    Performs decompression on the input value if the codec field has been set and is valid. If the data is being sent
    uncompressed already, will just reshape the data using the sizes specified in the dimension field.

    Parameters
    ----------
    structure : Value
        The value we have received from P4P
    """
    if structure is None:
        return

    data = structure.get("value")
    if data is None:
        return
    shape = []
    for dim in structure.get("dimension", []):
        shape.append(dim.get("size"))
    codec = structure.get("codec", {})
    data_type = codec.get("parameters")
    if data_type is None:
        # Assuming data type from data
        dtype = data.dtype
    else:
        dtype = ScalarType[data_type]

    codec_name = codec.get("name")
    uncompressed_size = structure.get("uncompressedSize")

    if not codec_name:
        return none_decompress(data, shape, dtype)

    try:
        return codecs[codec_name](data, shape, dtype, uncompressed_size)
    except Exception:
        logging.exception("Could not run codec decompress for %s", codec_name)
        return data


def none_decompress(data, shape, dtype):
    """Perform a reshape based on the dimensions that were set"""
    return np.frombuffer(data, dtype=dtype).reshape(shape)


def jpeg_decompress(data, shape, dtype, uncompressed_size):
    """Decompress using Pillow's jpeg decompression"""
    return np.array(Image.open(io.BytesIO(data.tobytes())))


def blosc_decompress(data, shape, dtype, uncompressed_size):
    """Decompress using blosc"""
    dec_data = blosc.decompress(data)
    return np.frombuffer(dec_data, dtype=dtype).reshape(shape)


def lz4_decompress(data, shape, dtype, uncompressed_size):
    """Decompress using lz4"""
    dec_data = block.decompress(data, uncompressed_size)
    return np.frombuffer(dec_data, dtype=dtype).reshape(shape)


def bslz4_decompress(data, shape, dtype, uncompressed_size):
    """Decompress using bslz4"""
    nelems = reduce((lambda x, y: x * y), shape)
    dec_data = bitshuffle.decompress_lz4(data, (nelems,), np.dtype(dtype))
    return dec_data.reshape(shape)


try:
    import blosc

    codecs["blosc"] = blosc_decompress
except ImportError:
    logger.debug("Blosc codec not available for PVAccess data decompression")

try:
    from lz4 import block

    codecs["lz4"] = lz4_decompress
except ImportError:
    logger.debug("LZ4 codec not available for PVAccess data decompression")

try:
    import bitshuffle

    codecs["bslz4"] = bslz4_decompress
except ImportError:
    logger.debug("BSLZ4 codec not available for PVAccess data decompression")

try:
    from PIL import Image

    codecs["jpeg"] = jpeg_decompress
except ImportError:
    logger.debug("JPEG codec not available for PVAccess data decompression")
