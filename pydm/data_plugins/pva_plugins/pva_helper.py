from p4p.nt.ndarray import ntndarray
from .pva_codec import decompress


def pre_process(structure, nt_id):
    if 'NTNDArray' in nt_id:
        decompress(structure)
