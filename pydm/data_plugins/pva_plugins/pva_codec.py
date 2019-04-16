import logging
import numpy as np
from functools import reduce
import io

logger = logging.getLogger(__name__)


ScalarType = (np.bool, np.int8, np.int16, np.int32, np.long, np.uint8,
              np.uint16, np.uint32, np.uint64, np.float, np.double)


codecs = {}


def decompress(structure):
    data = structure.get('value')
    shape = []
    for dim in structure.get('dimension', []):
        shape.append(dim.get('size'))
    codec = structure.get('codec', {})
    data_type = codec.get('parameters')
    if data_type is None:
        # Assuming data type from data
        dtype = data.dtype
    else:
        dtype = ScalarType[data_type]
    codec_name = codec.get('name')
    uncompressed_size = structure.get('uncompressedSize')

    if not codec_name:
        structure['value'] = none_decompress(data, shape, dtype,
                                             uncompressed_size)
        return
    try:
        structure['value'] = codecs[codec_name](data, shape, dtype,
                                                uncompressed_size)
    except Exception:
        logging.exception('Could not run codec decompress for %s', codec_name)


def none_decompress(data, shape, dtype, uncompressed_size):
    return np.frombuffer(data, dtype=dtype).reshape(shape)


def jpeg_decompress(data, shape, dtype, uncompressed_size):
    return np.array(Image.open(io.BytesIO(data.tobytes())))


def blosc_decompress(data, shape, dtype, uncompressed_size):
    dec_data = blosc.decompress(data)
    return np.frombuffer(dec_data, dtype=dtype).reshape(shape)


def lz4_decompress(data, shape, dtype, uncompressed_size):
    dec_data = block.decompress(data, uncompressed_size)
    return np.frombuffer(dec_data, dtype=dtype).reshape(shape)


def bslz4_decompress(data, shape, dtype, uncompressed_size):
    nelems = reduce((lambda x, y: x * y), shape)
    dec_data = bitshuffle.decompress_lz4(data, (nelems,), np.dtype(dtype))
    return dec_data.reshape(shape)


try:
    import blosc
    codecs['blosc'] = blosc_decompress
except ImportError:
    logger.warning('Blosc codec not available for PVAccess data decompression')

try:
    from lz4 import block
    codecs['lz4'] = lz4_decompress
except ImportError:
    logger.warning('LZ4 codec not available for PVAccess data decompression')

try:
    import bitshuffle
    codecs['bslz4'] = bslz4_decompress
except ImportError:
    logger.warning('BSLZ4 codec not available for PVAccess data decompression')

try:
    from PIL import Image
    codecs['jpeg'] = jpeg_decompress
except ImportError:
    logger.warning('JPEG codec not available for PVAccess data decompression')
