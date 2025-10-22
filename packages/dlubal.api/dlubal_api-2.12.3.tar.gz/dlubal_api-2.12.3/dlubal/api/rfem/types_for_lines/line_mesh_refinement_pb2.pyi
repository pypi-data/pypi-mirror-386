from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class LineMeshRefinement(_message.Message):
    __slots__ = ("no", "type", "user_defined_name_enabled", "name", "comment", "lines", "number_of_layers", "target_length", "elements_finite_elements", "gradual_rows", "is_generated", "generating_object_info", "id_for_export_import", "metadata_for_export_import")
    class Type(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        TYPE_UNKNOWN: _ClassVar[LineMeshRefinement.Type]
        TYPE_ELEMENTS: _ClassVar[LineMeshRefinement.Type]
        TYPE_GRADUAL: _ClassVar[LineMeshRefinement.Type]
        TYPE_LENGTH: _ClassVar[LineMeshRefinement.Type]
    TYPE_UNKNOWN: LineMeshRefinement.Type
    TYPE_ELEMENTS: LineMeshRefinement.Type
    TYPE_GRADUAL: LineMeshRefinement.Type
    TYPE_LENGTH: LineMeshRefinement.Type
    NO_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    USER_DEFINED_NAME_ENABLED_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    COMMENT_FIELD_NUMBER: _ClassVar[int]
    LINES_FIELD_NUMBER: _ClassVar[int]
    NUMBER_OF_LAYERS_FIELD_NUMBER: _ClassVar[int]
    TARGET_LENGTH_FIELD_NUMBER: _ClassVar[int]
    ELEMENTS_FINITE_ELEMENTS_FIELD_NUMBER: _ClassVar[int]
    GRADUAL_ROWS_FIELD_NUMBER: _ClassVar[int]
    IS_GENERATED_FIELD_NUMBER: _ClassVar[int]
    GENERATING_OBJECT_INFO_FIELD_NUMBER: _ClassVar[int]
    ID_FOR_EXPORT_IMPORT_FIELD_NUMBER: _ClassVar[int]
    METADATA_FOR_EXPORT_IMPORT_FIELD_NUMBER: _ClassVar[int]
    no: int
    type: LineMeshRefinement.Type
    user_defined_name_enabled: bool
    name: str
    comment: str
    lines: _containers.RepeatedScalarFieldContainer[int]
    number_of_layers: int
    target_length: float
    elements_finite_elements: int
    gradual_rows: int
    is_generated: bool
    generating_object_info: str
    id_for_export_import: str
    metadata_for_export_import: str
    def __init__(self, no: _Optional[int] = ..., type: _Optional[_Union[LineMeshRefinement.Type, str]] = ..., user_defined_name_enabled: bool = ..., name: _Optional[str] = ..., comment: _Optional[str] = ..., lines: _Optional[_Iterable[int]] = ..., number_of_layers: _Optional[int] = ..., target_length: _Optional[float] = ..., elements_finite_elements: _Optional[int] = ..., gradual_rows: _Optional[int] = ..., is_generated: bool = ..., generating_object_info: _Optional[str] = ..., id_for_export_import: _Optional[str] = ..., metadata_for_export_import: _Optional[str] = ...) -> None: ...
