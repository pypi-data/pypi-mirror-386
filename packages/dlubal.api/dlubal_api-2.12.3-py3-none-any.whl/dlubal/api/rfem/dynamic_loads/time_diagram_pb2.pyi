from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class TimeDiagram(_message.Message):
    __slots__ = ("no", "definition_type", "user_defined_name_enabled", "name", "user_defined_time_diagram_step_enabled", "user_defined_time_diagram_time_step", "user_defined_time_diagram_sorted", "user_defined_time_diagram", "comment", "is_generated", "generating_object_info", "function_defined_function", "function_defined_maximum_t", "function_defined_diagram_start", "function_defined_diagram_end", "assigned_to", "id_for_export_import", "metadata_for_export_import")
    class DefinitionType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        DEFINITION_TYPE_UNKNOWN: _ClassVar[TimeDiagram.DefinitionType]
        DEFINITION_TYPE_FUNCTION: _ClassVar[TimeDiagram.DefinitionType]
        DEFINITION_TYPE_USER_DEFINED: _ClassVar[TimeDiagram.DefinitionType]
    DEFINITION_TYPE_UNKNOWN: TimeDiagram.DefinitionType
    DEFINITION_TYPE_FUNCTION: TimeDiagram.DefinitionType
    DEFINITION_TYPE_USER_DEFINED: TimeDiagram.DefinitionType
    class FunctionDefinedDiagramStart(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        FUNCTION_DEFINED_DIAGRAM_START_ZERO: _ClassVar[TimeDiagram.FunctionDefinedDiagramStart]
        FUNCTION_DEFINED_DIAGRAM_START_CONSTANT: _ClassVar[TimeDiagram.FunctionDefinedDiagramStart]
    FUNCTION_DEFINED_DIAGRAM_START_ZERO: TimeDiagram.FunctionDefinedDiagramStart
    FUNCTION_DEFINED_DIAGRAM_START_CONSTANT: TimeDiagram.FunctionDefinedDiagramStart
    class FunctionDefinedDiagramEnd(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        FUNCTION_DEFINED_DIAGRAM_END_ZERO: _ClassVar[TimeDiagram.FunctionDefinedDiagramEnd]
        FUNCTION_DEFINED_DIAGRAM_END_CONSTANT: _ClassVar[TimeDiagram.FunctionDefinedDiagramEnd]
    FUNCTION_DEFINED_DIAGRAM_END_ZERO: TimeDiagram.FunctionDefinedDiagramEnd
    FUNCTION_DEFINED_DIAGRAM_END_CONSTANT: TimeDiagram.FunctionDefinedDiagramEnd
    class UserDefinedTimeDiagramTable(_message.Message):
        __slots__ = ("rows",)
        ROWS_FIELD_NUMBER: _ClassVar[int]
        rows: _containers.RepeatedCompositeFieldContainer[TimeDiagram.UserDefinedTimeDiagramRow]
        def __init__(self, rows: _Optional[_Iterable[_Union[TimeDiagram.UserDefinedTimeDiagramRow, _Mapping]]] = ...) -> None: ...
    class UserDefinedTimeDiagramRow(_message.Message):
        __slots__ = ("no", "description", "time", "multiplier")
        NO_FIELD_NUMBER: _ClassVar[int]
        DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
        TIME_FIELD_NUMBER: _ClassVar[int]
        MULTIPLIER_FIELD_NUMBER: _ClassVar[int]
        no: int
        description: str
        time: float
        multiplier: float
        def __init__(self, no: _Optional[int] = ..., description: _Optional[str] = ..., time: _Optional[float] = ..., multiplier: _Optional[float] = ...) -> None: ...
    NO_FIELD_NUMBER: _ClassVar[int]
    DEFINITION_TYPE_FIELD_NUMBER: _ClassVar[int]
    USER_DEFINED_NAME_ENABLED_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    USER_DEFINED_TIME_DIAGRAM_STEP_ENABLED_FIELD_NUMBER: _ClassVar[int]
    USER_DEFINED_TIME_DIAGRAM_TIME_STEP_FIELD_NUMBER: _ClassVar[int]
    USER_DEFINED_TIME_DIAGRAM_SORTED_FIELD_NUMBER: _ClassVar[int]
    USER_DEFINED_TIME_DIAGRAM_FIELD_NUMBER: _ClassVar[int]
    COMMENT_FIELD_NUMBER: _ClassVar[int]
    IS_GENERATED_FIELD_NUMBER: _ClassVar[int]
    GENERATING_OBJECT_INFO_FIELD_NUMBER: _ClassVar[int]
    FUNCTION_DEFINED_FUNCTION_FIELD_NUMBER: _ClassVar[int]
    FUNCTION_DEFINED_MAXIMUM_T_FIELD_NUMBER: _ClassVar[int]
    FUNCTION_DEFINED_DIAGRAM_START_FIELD_NUMBER: _ClassVar[int]
    FUNCTION_DEFINED_DIAGRAM_END_FIELD_NUMBER: _ClassVar[int]
    ASSIGNED_TO_FIELD_NUMBER: _ClassVar[int]
    ID_FOR_EXPORT_IMPORT_FIELD_NUMBER: _ClassVar[int]
    METADATA_FOR_EXPORT_IMPORT_FIELD_NUMBER: _ClassVar[int]
    no: int
    definition_type: TimeDiagram.DefinitionType
    user_defined_name_enabled: bool
    name: str
    user_defined_time_diagram_step_enabled: bool
    user_defined_time_diagram_time_step: float
    user_defined_time_diagram_sorted: bool
    user_defined_time_diagram: TimeDiagram.UserDefinedTimeDiagramTable
    comment: str
    is_generated: bool
    generating_object_info: str
    function_defined_function: str
    function_defined_maximum_t: float
    function_defined_diagram_start: TimeDiagram.FunctionDefinedDiagramStart
    function_defined_diagram_end: TimeDiagram.FunctionDefinedDiagramEnd
    assigned_to: str
    id_for_export_import: str
    metadata_for_export_import: str
    def __init__(self, no: _Optional[int] = ..., definition_type: _Optional[_Union[TimeDiagram.DefinitionType, str]] = ..., user_defined_name_enabled: bool = ..., name: _Optional[str] = ..., user_defined_time_diagram_step_enabled: bool = ..., user_defined_time_diagram_time_step: _Optional[float] = ..., user_defined_time_diagram_sorted: bool = ..., user_defined_time_diagram: _Optional[_Union[TimeDiagram.UserDefinedTimeDiagramTable, _Mapping]] = ..., comment: _Optional[str] = ..., is_generated: bool = ..., generating_object_info: _Optional[str] = ..., function_defined_function: _Optional[str] = ..., function_defined_maximum_t: _Optional[float] = ..., function_defined_diagram_start: _Optional[_Union[TimeDiagram.FunctionDefinedDiagramStart, str]] = ..., function_defined_diagram_end: _Optional[_Union[TimeDiagram.FunctionDefinedDiagramEnd, str]] = ..., assigned_to: _Optional[str] = ..., id_for_export_import: _Optional[str] = ..., metadata_for_export_import: _Optional[str] = ...) -> None: ...
