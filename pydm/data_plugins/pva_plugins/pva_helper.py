import logging

logger = logging.getLogger(__name__)

from .pva_codec import decompress

DEFAULT_NT_KEYS = dict(
    connection_key="CONNECTION", value_key="value",
    severity_key="alarm.severity", write_access_key="WRITE_ACCESS",
    enum_strings_key=None, unit_key=None,
    precision_key=None, upper_limit_key=None,
    lower_limit_key=None
)

NTScalarKeys = dict(
    connection_key="CONNECTION", value_key="value",
    severity_key="alarm.severity", write_access_key="WRITE_ACCESS",
    enum_strings_key=None, unit_key="display.units",
    precision_key="display.precision", upper_limit_key="control.limitHigh",
    lower_limit_key="control.limitLow"
)

NTScalarArrayKeys = NTScalarKeys
NTMatrixKeys = NTScalarKeys
NTNDArrayKeys = NTScalarKeys

NTEnumKeys = dict(
    connection_key="CONNECTION", value_key="value.index",
    severity_key="alarm.severity", write_access_key="WRITE_ACCESS",
    enum_strings_key="value.choices", unit_key=None,
    precision_key=None, upper_limit_key=None,
    lower_limit_key=None
)

NTNameValueKeys = DEFAULT_NT_KEYS
NTTableKeys = DEFAULT_NT_KEYS
NTAttributeKeys = DEFAULT_NT_KEYS
NTHistogramKeys = DEFAULT_NT_KEYS
NTAggregateKeys = DEFAULT_NT_KEYS

# NTURIKeys = ???
# NTMultiChannelKeys = ???
# NTContinuumKeys = ???

nt_introspection = {
    'epics:nt/NTScalar:1.0': NTScalarKeys,
    'epics:nt/NTScalarArray:1.0': NTScalarArrayKeys,
    'epics:nt/NTEnum:1.0': NTEnumKeys,
    'epics:nt/NTMatrix:1.0': NTMatrixKeys,
    # 'epics:nt/NTURI:1.0': NTURIKeys,
    'epics:nt/NTNameValue:1.0': NTNameValueKeys,
    'epics:nt/NTTable:1.0': NTTableKeys,
    'epics:nt/NTAttribute:1.0': NTAttributeKeys,
    # 'epics:nt/NTMultiChannel:1.0': NTMultiChannelKeys,
    'epics:nt/NTNDArray:1.0': NTNDArrayKeys,
    # 'epics:nt/NTContinuum:1.0': NTContinuumKeys,
    'epics:nt/NTHistogram:1.0': NTHistogramKeys,
    'epics:nt/NTAggregate:1.0': NTAggregateKeys
}


def pre_process(structure, nt_id):
    if 'NTNDArray' in nt_id:
        try:
            decompress(structure)
        except Exception:
            logger.exception('Failed to pre-process NTNDArray.')
