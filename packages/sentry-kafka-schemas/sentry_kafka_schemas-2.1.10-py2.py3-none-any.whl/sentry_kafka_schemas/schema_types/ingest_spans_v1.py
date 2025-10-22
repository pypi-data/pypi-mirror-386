from typing import List, TypedDict, Union, Literal, Any, Required, Dict


class SpanEvent(TypedDict, total=False):
    """ span_event. """

    event_id: "_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsUuid"
    """
    minLength: 32
    maxLength: 36
    """

    organization_id: Required["_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsUint"]
    """
    minimum: 0

    Required property
    """

    project_id: Required["_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsUint"]
    """
    minimum: 0

    Required property
    """

    key_id: "_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsUint"
    """ minimum: 0 """

    trace_id: Required["_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsUuid"]
    """
    minLength: 32
    maxLength: 36

    Required property
    """

    span_id: Required[str]
    """
    The span ID is a unique identifier for a span within a trace. It is an 8 byte hexadecimal string.

    Required property
    """

    parent_span_id: Union[str, None]
    """ The parent span ID is the ID of the span that caused this span. It is an 8 byte hexadecimal string. """

    start_timestamp: Required["_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsPositivefloat"]
    """
    minimum: 0

    Required property
    """

    end_timestamp: Required["_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsPositivefloat"]
    """
    minimum: 0

    Required property
    """

    retention_days: Required["_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsUint16"]
    """
    minimum: 0
    maximum: 65535

    Required property
    """

    downsampled_retention_days: "_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsUint16"
    """
    minimum: 0
    maximum: 65535
    """

    received: Required["_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsPositivefloat"]
    """
    minimum: 0

    Required property
    """

    name: Required[Union[str, None]]
    """ Required property """

    status: Required[str]
    """ Required property """

    is_remote: Required[Union[bool, None]]
    """ Required property """

    kind: Union[str, None]
    links: Union[List["_SpanEventLinksArrayItem"], None]
    """
    items:
      oneOf:
      - $ref: file://ingest-spans.v1.schema.json#/definitions/SpanLink
      - type: 'null'
      used: !!set
        $ref: null
        oneOf: null
    """

    attributes: "_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsAttributes"
    """
    additionalProperties:
      $ref: file://ingest-spans.v1.schema.json#/definitions/AttributeValue
      used: !!set
        $ref: null
    """

    _meta: Dict[str, Any]


class SpanLink(TypedDict, total=False):
    """ span_link. """

    trace_id: Required[Union["_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsUuid", None]]
    """
    Aggregation type: oneOf

    Required property
    """

    span_id: Required[Union[str, None]]
    """ Required property """

    attributes: "_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsAttributes"
    """
    additionalProperties:
      $ref: file://ingest-spans.v1.schema.json#/definitions/AttributeValue
      used: !!set
        $ref: null
    """

    sampled: Union[bool, None]


_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsAttributes = Union[Dict[str, "_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsAttributevalue"], None]
"""
additionalProperties:
  $ref: file://ingest-spans.v1.schema.json#/definitions/AttributeValue
  used: !!set
    $ref: null
"""



class _FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsAttributevalue(TypedDict, total=False):
    type: Required["_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsAttributevalueType"]
    """
    Aggregation type: anyOf

    Required property
    """

    value: Required[Union[Union[int, float], None, str, bool, List[Any], Dict[str, Any]]]
    """ Required property """



_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsAttributevalueType = Union[None, "_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsAttributevalueTypeAnyof1"]
""" Aggregation type: anyOf """



_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsAttributevalueTypeAnyof1 = Union[Literal['boolean'], Literal['integer'], Literal['double'], Literal['string'], Literal['array'], Literal['object']]
_FILECOLONINGESTSPANSFULLSTOPV1FULLSTOPSCHEMAFULLSTOPJSONNUMBERSIGNDEFINITIONSATTRIBUTEVALUETYPEANYOF1_BOOLEAN: Literal['boolean'] = "boolean"
"""The values for the '_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsAttributevalueTypeAnyof1' enum"""
_FILECOLONINGESTSPANSFULLSTOPV1FULLSTOPSCHEMAFULLSTOPJSONNUMBERSIGNDEFINITIONSATTRIBUTEVALUETYPEANYOF1_INTEGER: Literal['integer'] = "integer"
"""The values for the '_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsAttributevalueTypeAnyof1' enum"""
_FILECOLONINGESTSPANSFULLSTOPV1FULLSTOPSCHEMAFULLSTOPJSONNUMBERSIGNDEFINITIONSATTRIBUTEVALUETYPEANYOF1_DOUBLE: Literal['double'] = "double"
"""The values for the '_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsAttributevalueTypeAnyof1' enum"""
_FILECOLONINGESTSPANSFULLSTOPV1FULLSTOPSCHEMAFULLSTOPJSONNUMBERSIGNDEFINITIONSATTRIBUTEVALUETYPEANYOF1_STRING: Literal['string'] = "string"
"""The values for the '_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsAttributevalueTypeAnyof1' enum"""
_FILECOLONINGESTSPANSFULLSTOPV1FULLSTOPSCHEMAFULLSTOPJSONNUMBERSIGNDEFINITIONSATTRIBUTEVALUETYPEANYOF1_ARRAY: Literal['array'] = "array"
"""The values for the '_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsAttributevalueTypeAnyof1' enum"""
_FILECOLONINGESTSPANSFULLSTOPV1FULLSTOPSCHEMAFULLSTOPJSONNUMBERSIGNDEFINITIONSATTRIBUTEVALUETYPEANYOF1_OBJECT: Literal['object'] = "object"
"""The values for the '_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsAttributevalueTypeAnyof1' enum"""



_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsPositivefloat = Union[int, float]
""" minimum: 0 """



_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsUint = int
""" minimum: 0 """



_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsUint16 = int
"""
minimum: 0
maximum: 65535
"""



_FileColonIngestSpansFullStopV1FullStopSchemaFullStopJsonNumberSignDefinitionsUuid = str
"""
minLength: 32
maxLength: 36
"""



_SpanEventLinksArrayItem = Union["SpanLink", None]
""" Aggregation type: oneOf """

