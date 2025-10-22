from dlubal.api.common import common_pb2 as _common_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Dimension(_message.Message):
    __slots__ = ("no", "type", "user_defined_name_enabled", "name", "display_properties_index", "dimension_line_offset", "is_custom_vertical_position", "custom_vertical_position", "is_custom_horizontal_position", "custom_horizontal_position", "symbol", "comment", "measured_length", "measured_lengths", "measured_angle", "measured_angles", "measured_slope", "is_global_dimension_line_offset", "linear_coordinate_system", "linear_reference", "linear_global_dimension_line_offset_y", "linear_global_dimension_line_offset_z", "linear_global_dimension_line_offset", "linear_reference_table", "arc_length_reference_line", "arc_length_reference_table", "arc_length_angle_greater_than_180", "angular_reference_table", "angular_quadrant", "angular_angle_greater_than_180", "radius_diameter_reference_line", "radius_diameter_is_target_point", "radius_diameter_target_point_coordinate_y", "radius_diameter_target_point_coordinate_z", "radius_diameter_target_point_coordinates", "radius_diameter_position_on_line", "slope_coordinate_system", "slope_plane", "slope_reference_type", "slope_reference_line", "slope_first_point_coordinate_y", "slope_first_point_coordinate_z", "slope_first_point_coordinates", "slope_second_point_coordinate_y", "slope_second_point_coordinate_z", "slope_second_point_coordinates", "slope_direction", "slope_refer_distance_from_line_end", "slope_position_absolute", "slope_position_relative", "slope_position_is_relative", "parent_layer", "is_locked_by_parent_layer", "is_generated", "generating_object_info", "is_detail_dimension", "detail_dimension_parent_object", "id_for_export_import", "metadata_for_export_import")
    class Type(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        TYPE_UNKNOWN: _ClassVar[Dimension.Type]
        TYPE_ANGULAR: _ClassVar[Dimension.Type]
        TYPE_ARC_LENGTH: _ClassVar[Dimension.Type]
        TYPE_DIAMETER: _ClassVar[Dimension.Type]
        TYPE_LINEAR: _ClassVar[Dimension.Type]
        TYPE_RADIUS: _ClassVar[Dimension.Type]
        TYPE_SLOPE: _ClassVar[Dimension.Type]
    TYPE_UNKNOWN: Dimension.Type
    TYPE_ANGULAR: Dimension.Type
    TYPE_ARC_LENGTH: Dimension.Type
    TYPE_DIAMETER: Dimension.Type
    TYPE_LINEAR: Dimension.Type
    TYPE_RADIUS: Dimension.Type
    TYPE_SLOPE: Dimension.Type
    class CustomVerticalPosition(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        CUSTOM_VERTICAL_POSITION_CENTER: _ClassVar[Dimension.CustomVerticalPosition]
        CUSTOM_VERTICAL_POSITION_ABOVE: _ClassVar[Dimension.CustomVerticalPosition]
        CUSTOM_VERTICAL_POSITION_UNDER: _ClassVar[Dimension.CustomVerticalPosition]
    CUSTOM_VERTICAL_POSITION_CENTER: Dimension.CustomVerticalPosition
    CUSTOM_VERTICAL_POSITION_ABOVE: Dimension.CustomVerticalPosition
    CUSTOM_VERTICAL_POSITION_UNDER: Dimension.CustomVerticalPosition
    class CustomHorizontalPosition(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        CUSTOM_HORIZONTAL_POSITION_CENTER: _ClassVar[Dimension.CustomHorizontalPosition]
        CUSTOM_HORIZONTAL_POSITION_LEFT: _ClassVar[Dimension.CustomHorizontalPosition]
        CUSTOM_HORIZONTAL_POSITION_RIGHT: _ClassVar[Dimension.CustomHorizontalPosition]
    CUSTOM_HORIZONTAL_POSITION_CENTER: Dimension.CustomHorizontalPosition
    CUSTOM_HORIZONTAL_POSITION_LEFT: Dimension.CustomHorizontalPosition
    CUSTOM_HORIZONTAL_POSITION_RIGHT: Dimension.CustomHorizontalPosition
    class LinearReference(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        LINEAR_REFERENCE_LENGTH: _ClassVar[Dimension.LinearReference]
        LINEAR_REFERENCE_PROJECTION_IN_X: _ClassVar[Dimension.LinearReference]
        LINEAR_REFERENCE_PROJECTION_IN_Y: _ClassVar[Dimension.LinearReference]
    LINEAR_REFERENCE_LENGTH: Dimension.LinearReference
    LINEAR_REFERENCE_PROJECTION_IN_X: Dimension.LinearReference
    LINEAR_REFERENCE_PROJECTION_IN_Y: Dimension.LinearReference
    class AngularQuadrant(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        ANGULAR_QUADRANT_POSITIVE: _ClassVar[Dimension.AngularQuadrant]
        ANGULAR_QUADRANT_LEFT: _ClassVar[Dimension.AngularQuadrant]
        ANGULAR_QUADRANT_NEGATIVE: _ClassVar[Dimension.AngularQuadrant]
        ANGULAR_QUADRANT_RIGHT: _ClassVar[Dimension.AngularQuadrant]
    ANGULAR_QUADRANT_POSITIVE: Dimension.AngularQuadrant
    ANGULAR_QUADRANT_LEFT: Dimension.AngularQuadrant
    ANGULAR_QUADRANT_NEGATIVE: Dimension.AngularQuadrant
    ANGULAR_QUADRANT_RIGHT: Dimension.AngularQuadrant
    class SlopePlane(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        SLOPE_PLANE_PROJECTION_IN_X: _ClassVar[Dimension.SlopePlane]
        SLOPE_PLANE_PROJECTION_IN_Y: _ClassVar[Dimension.SlopePlane]
    SLOPE_PLANE_PROJECTION_IN_X: Dimension.SlopePlane
    SLOPE_PLANE_PROJECTION_IN_Y: Dimension.SlopePlane
    class SlopeReferenceType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        SLOPE_REFERENCE_TYPE_LINE_OR_MEMBER: _ClassVar[Dimension.SlopeReferenceType]
        SLOPE_REFERENCE_TYPE_TWO_POINTS: _ClassVar[Dimension.SlopeReferenceType]
    SLOPE_REFERENCE_TYPE_LINE_OR_MEMBER: Dimension.SlopeReferenceType
    SLOPE_REFERENCE_TYPE_TWO_POINTS: Dimension.SlopeReferenceType
    class SlopeDirection(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        SLOPE_DIRECTION_UPWARD: _ClassVar[Dimension.SlopeDirection]
        SLOPE_DIRECTION_DOWNWARD: _ClassVar[Dimension.SlopeDirection]
    SLOPE_DIRECTION_UPWARD: Dimension.SlopeDirection
    SLOPE_DIRECTION_DOWNWARD: Dimension.SlopeDirection
    class LinearReferenceTable(_message.Message):
        __slots__ = ("rows",)
        ROWS_FIELD_NUMBER: _ClassVar[int]
        rows: _containers.RepeatedCompositeFieldContainer[Dimension.LinearReferenceTableRow]
        def __init__(self, rows: _Optional[_Iterable[_Union[Dimension.LinearReferenceTableRow, _Mapping]]] = ...) -> None: ...
    class LinearReferenceTableRow(_message.Message):
        __slots__ = ("no", "description", "reference_object_type", "reference_object", "line_relative_distance", "coordinate_y", "coordinate_z")
        class ReferenceObjectType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = ()
            REFERENCE_OBJECT_TYPE_POINT: _ClassVar[Dimension.LinearReferenceTableRow.ReferenceObjectType]
            REFERENCE_OBJECT_TYPE_CONTROL_POINT: _ClassVar[Dimension.LinearReferenceTableRow.ReferenceObjectType]
            REFERENCE_OBJECT_TYPE_LINE: _ClassVar[Dimension.LinearReferenceTableRow.ReferenceObjectType]
            REFERENCE_OBJECT_TYPE_LOCATION: _ClassVar[Dimension.LinearReferenceTableRow.ReferenceObjectType]
            REFERENCE_OBJECT_TYPE_POINT_ON_LINE: _ClassVar[Dimension.LinearReferenceTableRow.ReferenceObjectType]
            REFERENCE_OBJECT_TYPE_SNAP_POSITION: _ClassVar[Dimension.LinearReferenceTableRow.ReferenceObjectType]
            REFERENCE_OBJECT_TYPE_STRESS_POINT: _ClassVar[Dimension.LinearReferenceTableRow.ReferenceObjectType]
        REFERENCE_OBJECT_TYPE_POINT: Dimension.LinearReferenceTableRow.ReferenceObjectType
        REFERENCE_OBJECT_TYPE_CONTROL_POINT: Dimension.LinearReferenceTableRow.ReferenceObjectType
        REFERENCE_OBJECT_TYPE_LINE: Dimension.LinearReferenceTableRow.ReferenceObjectType
        REFERENCE_OBJECT_TYPE_LOCATION: Dimension.LinearReferenceTableRow.ReferenceObjectType
        REFERENCE_OBJECT_TYPE_POINT_ON_LINE: Dimension.LinearReferenceTableRow.ReferenceObjectType
        REFERENCE_OBJECT_TYPE_SNAP_POSITION: Dimension.LinearReferenceTableRow.ReferenceObjectType
        REFERENCE_OBJECT_TYPE_STRESS_POINT: Dimension.LinearReferenceTableRow.ReferenceObjectType
        NO_FIELD_NUMBER: _ClassVar[int]
        DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
        REFERENCE_OBJECT_TYPE_FIELD_NUMBER: _ClassVar[int]
        REFERENCE_OBJECT_FIELD_NUMBER: _ClassVar[int]
        LINE_RELATIVE_DISTANCE_FIELD_NUMBER: _ClassVar[int]
        COORDINATE_Y_FIELD_NUMBER: _ClassVar[int]
        COORDINATE_Z_FIELD_NUMBER: _ClassVar[int]
        no: int
        description: str
        reference_object_type: Dimension.LinearReferenceTableRow.ReferenceObjectType
        reference_object: int
        line_relative_distance: float
        coordinate_y: float
        coordinate_z: float
        def __init__(self, no: _Optional[int] = ..., description: _Optional[str] = ..., reference_object_type: _Optional[_Union[Dimension.LinearReferenceTableRow.ReferenceObjectType, str]] = ..., reference_object: _Optional[int] = ..., line_relative_distance: _Optional[float] = ..., coordinate_y: _Optional[float] = ..., coordinate_z: _Optional[float] = ...) -> None: ...
    class ArcLengthReferenceTable(_message.Message):
        __slots__ = ("rows",)
        ROWS_FIELD_NUMBER: _ClassVar[int]
        rows: _containers.RepeatedCompositeFieldContainer[Dimension.ArcLengthReferenceTableRow]
        def __init__(self, rows: _Optional[_Iterable[_Union[Dimension.ArcLengthReferenceTableRow, _Mapping]]] = ...) -> None: ...
    class ArcLengthReferenceTableRow(_message.Message):
        __slots__ = ("no", "description", "reference_object_type", "reference_object", "line_relative_distance", "coordinate_y", "coordinate_z")
        class ReferenceObjectType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = ()
            REFERENCE_OBJECT_TYPE_POINT: _ClassVar[Dimension.ArcLengthReferenceTableRow.ReferenceObjectType]
            REFERENCE_OBJECT_TYPE_CONTROL_POINT: _ClassVar[Dimension.ArcLengthReferenceTableRow.ReferenceObjectType]
            REFERENCE_OBJECT_TYPE_LINE: _ClassVar[Dimension.ArcLengthReferenceTableRow.ReferenceObjectType]
            REFERENCE_OBJECT_TYPE_LOCATION: _ClassVar[Dimension.ArcLengthReferenceTableRow.ReferenceObjectType]
            REFERENCE_OBJECT_TYPE_POINT_ON_LINE: _ClassVar[Dimension.ArcLengthReferenceTableRow.ReferenceObjectType]
            REFERENCE_OBJECT_TYPE_SNAP_POSITION: _ClassVar[Dimension.ArcLengthReferenceTableRow.ReferenceObjectType]
            REFERENCE_OBJECT_TYPE_STRESS_POINT: _ClassVar[Dimension.ArcLengthReferenceTableRow.ReferenceObjectType]
        REFERENCE_OBJECT_TYPE_POINT: Dimension.ArcLengthReferenceTableRow.ReferenceObjectType
        REFERENCE_OBJECT_TYPE_CONTROL_POINT: Dimension.ArcLengthReferenceTableRow.ReferenceObjectType
        REFERENCE_OBJECT_TYPE_LINE: Dimension.ArcLengthReferenceTableRow.ReferenceObjectType
        REFERENCE_OBJECT_TYPE_LOCATION: Dimension.ArcLengthReferenceTableRow.ReferenceObjectType
        REFERENCE_OBJECT_TYPE_POINT_ON_LINE: Dimension.ArcLengthReferenceTableRow.ReferenceObjectType
        REFERENCE_OBJECT_TYPE_SNAP_POSITION: Dimension.ArcLengthReferenceTableRow.ReferenceObjectType
        REFERENCE_OBJECT_TYPE_STRESS_POINT: Dimension.ArcLengthReferenceTableRow.ReferenceObjectType
        NO_FIELD_NUMBER: _ClassVar[int]
        DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
        REFERENCE_OBJECT_TYPE_FIELD_NUMBER: _ClassVar[int]
        REFERENCE_OBJECT_FIELD_NUMBER: _ClassVar[int]
        LINE_RELATIVE_DISTANCE_FIELD_NUMBER: _ClassVar[int]
        COORDINATE_Y_FIELD_NUMBER: _ClassVar[int]
        COORDINATE_Z_FIELD_NUMBER: _ClassVar[int]
        no: int
        description: str
        reference_object_type: Dimension.ArcLengthReferenceTableRow.ReferenceObjectType
        reference_object: int
        line_relative_distance: float
        coordinate_y: float
        coordinate_z: float
        def __init__(self, no: _Optional[int] = ..., description: _Optional[str] = ..., reference_object_type: _Optional[_Union[Dimension.ArcLengthReferenceTableRow.ReferenceObjectType, str]] = ..., reference_object: _Optional[int] = ..., line_relative_distance: _Optional[float] = ..., coordinate_y: _Optional[float] = ..., coordinate_z: _Optional[float] = ...) -> None: ...
    class AngularReferenceTable(_message.Message):
        __slots__ = ("rows",)
        ROWS_FIELD_NUMBER: _ClassVar[int]
        rows: _containers.RepeatedCompositeFieldContainer[Dimension.AngularReferenceTableRow]
        def __init__(self, rows: _Optional[_Iterable[_Union[Dimension.AngularReferenceTableRow, _Mapping]]] = ...) -> None: ...
    class AngularReferenceTableRow(_message.Message):
        __slots__ = ("no", "description", "reference_object_type", "reference_object", "line_relative_distance", "coordinate_y", "coordinate_z")
        class ReferenceObjectType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = ()
            REFERENCE_OBJECT_TYPE_POINT: _ClassVar[Dimension.AngularReferenceTableRow.ReferenceObjectType]
            REFERENCE_OBJECT_TYPE_CONTROL_POINT: _ClassVar[Dimension.AngularReferenceTableRow.ReferenceObjectType]
            REFERENCE_OBJECT_TYPE_LINE: _ClassVar[Dimension.AngularReferenceTableRow.ReferenceObjectType]
            REFERENCE_OBJECT_TYPE_LOCATION: _ClassVar[Dimension.AngularReferenceTableRow.ReferenceObjectType]
            REFERENCE_OBJECT_TYPE_POINT_ON_LINE: _ClassVar[Dimension.AngularReferenceTableRow.ReferenceObjectType]
            REFERENCE_OBJECT_TYPE_SNAP_POSITION: _ClassVar[Dimension.AngularReferenceTableRow.ReferenceObjectType]
            REFERENCE_OBJECT_TYPE_STRESS_POINT: _ClassVar[Dimension.AngularReferenceTableRow.ReferenceObjectType]
        REFERENCE_OBJECT_TYPE_POINT: Dimension.AngularReferenceTableRow.ReferenceObjectType
        REFERENCE_OBJECT_TYPE_CONTROL_POINT: Dimension.AngularReferenceTableRow.ReferenceObjectType
        REFERENCE_OBJECT_TYPE_LINE: Dimension.AngularReferenceTableRow.ReferenceObjectType
        REFERENCE_OBJECT_TYPE_LOCATION: Dimension.AngularReferenceTableRow.ReferenceObjectType
        REFERENCE_OBJECT_TYPE_POINT_ON_LINE: Dimension.AngularReferenceTableRow.ReferenceObjectType
        REFERENCE_OBJECT_TYPE_SNAP_POSITION: Dimension.AngularReferenceTableRow.ReferenceObjectType
        REFERENCE_OBJECT_TYPE_STRESS_POINT: Dimension.AngularReferenceTableRow.ReferenceObjectType
        NO_FIELD_NUMBER: _ClassVar[int]
        DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
        REFERENCE_OBJECT_TYPE_FIELD_NUMBER: _ClassVar[int]
        REFERENCE_OBJECT_FIELD_NUMBER: _ClassVar[int]
        LINE_RELATIVE_DISTANCE_FIELD_NUMBER: _ClassVar[int]
        COORDINATE_Y_FIELD_NUMBER: _ClassVar[int]
        COORDINATE_Z_FIELD_NUMBER: _ClassVar[int]
        no: int
        description: str
        reference_object_type: Dimension.AngularReferenceTableRow.ReferenceObjectType
        reference_object: int
        line_relative_distance: float
        coordinate_y: float
        coordinate_z: float
        def __init__(self, no: _Optional[int] = ..., description: _Optional[str] = ..., reference_object_type: _Optional[_Union[Dimension.AngularReferenceTableRow.ReferenceObjectType, str]] = ..., reference_object: _Optional[int] = ..., line_relative_distance: _Optional[float] = ..., coordinate_y: _Optional[float] = ..., coordinate_z: _Optional[float] = ...) -> None: ...
    NO_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    USER_DEFINED_NAME_ENABLED_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DISPLAY_PROPERTIES_INDEX_FIELD_NUMBER: _ClassVar[int]
    DIMENSION_LINE_OFFSET_FIELD_NUMBER: _ClassVar[int]
    IS_CUSTOM_VERTICAL_POSITION_FIELD_NUMBER: _ClassVar[int]
    CUSTOM_VERTICAL_POSITION_FIELD_NUMBER: _ClassVar[int]
    IS_CUSTOM_HORIZONTAL_POSITION_FIELD_NUMBER: _ClassVar[int]
    CUSTOM_HORIZONTAL_POSITION_FIELD_NUMBER: _ClassVar[int]
    SYMBOL_FIELD_NUMBER: _ClassVar[int]
    COMMENT_FIELD_NUMBER: _ClassVar[int]
    MEASURED_LENGTH_FIELD_NUMBER: _ClassVar[int]
    MEASURED_LENGTHS_FIELD_NUMBER: _ClassVar[int]
    MEASURED_ANGLE_FIELD_NUMBER: _ClassVar[int]
    MEASURED_ANGLES_FIELD_NUMBER: _ClassVar[int]
    MEASURED_SLOPE_FIELD_NUMBER: _ClassVar[int]
    IS_GLOBAL_DIMENSION_LINE_OFFSET_FIELD_NUMBER: _ClassVar[int]
    LINEAR_COORDINATE_SYSTEM_FIELD_NUMBER: _ClassVar[int]
    LINEAR_REFERENCE_FIELD_NUMBER: _ClassVar[int]
    LINEAR_GLOBAL_DIMENSION_LINE_OFFSET_Y_FIELD_NUMBER: _ClassVar[int]
    LINEAR_GLOBAL_DIMENSION_LINE_OFFSET_Z_FIELD_NUMBER: _ClassVar[int]
    LINEAR_GLOBAL_DIMENSION_LINE_OFFSET_FIELD_NUMBER: _ClassVar[int]
    LINEAR_REFERENCE_TABLE_FIELD_NUMBER: _ClassVar[int]
    ARC_LENGTH_REFERENCE_LINE_FIELD_NUMBER: _ClassVar[int]
    ARC_LENGTH_REFERENCE_TABLE_FIELD_NUMBER: _ClassVar[int]
    ARC_LENGTH_ANGLE_GREATER_THAN_180_FIELD_NUMBER: _ClassVar[int]
    ANGULAR_REFERENCE_TABLE_FIELD_NUMBER: _ClassVar[int]
    ANGULAR_QUADRANT_FIELD_NUMBER: _ClassVar[int]
    ANGULAR_ANGLE_GREATER_THAN_180_FIELD_NUMBER: _ClassVar[int]
    RADIUS_DIAMETER_REFERENCE_LINE_FIELD_NUMBER: _ClassVar[int]
    RADIUS_DIAMETER_IS_TARGET_POINT_FIELD_NUMBER: _ClassVar[int]
    RADIUS_DIAMETER_TARGET_POINT_COORDINATE_Y_FIELD_NUMBER: _ClassVar[int]
    RADIUS_DIAMETER_TARGET_POINT_COORDINATE_Z_FIELD_NUMBER: _ClassVar[int]
    RADIUS_DIAMETER_TARGET_POINT_COORDINATES_FIELD_NUMBER: _ClassVar[int]
    RADIUS_DIAMETER_POSITION_ON_LINE_FIELD_NUMBER: _ClassVar[int]
    SLOPE_COORDINATE_SYSTEM_FIELD_NUMBER: _ClassVar[int]
    SLOPE_PLANE_FIELD_NUMBER: _ClassVar[int]
    SLOPE_REFERENCE_TYPE_FIELD_NUMBER: _ClassVar[int]
    SLOPE_REFERENCE_LINE_FIELD_NUMBER: _ClassVar[int]
    SLOPE_FIRST_POINT_COORDINATE_Y_FIELD_NUMBER: _ClassVar[int]
    SLOPE_FIRST_POINT_COORDINATE_Z_FIELD_NUMBER: _ClassVar[int]
    SLOPE_FIRST_POINT_COORDINATES_FIELD_NUMBER: _ClassVar[int]
    SLOPE_SECOND_POINT_COORDINATE_Y_FIELD_NUMBER: _ClassVar[int]
    SLOPE_SECOND_POINT_COORDINATE_Z_FIELD_NUMBER: _ClassVar[int]
    SLOPE_SECOND_POINT_COORDINATES_FIELD_NUMBER: _ClassVar[int]
    SLOPE_DIRECTION_FIELD_NUMBER: _ClassVar[int]
    SLOPE_REFER_DISTANCE_FROM_LINE_END_FIELD_NUMBER: _ClassVar[int]
    SLOPE_POSITION_ABSOLUTE_FIELD_NUMBER: _ClassVar[int]
    SLOPE_POSITION_RELATIVE_FIELD_NUMBER: _ClassVar[int]
    SLOPE_POSITION_IS_RELATIVE_FIELD_NUMBER: _ClassVar[int]
    PARENT_LAYER_FIELD_NUMBER: _ClassVar[int]
    IS_LOCKED_BY_PARENT_LAYER_FIELD_NUMBER: _ClassVar[int]
    IS_GENERATED_FIELD_NUMBER: _ClassVar[int]
    GENERATING_OBJECT_INFO_FIELD_NUMBER: _ClassVar[int]
    IS_DETAIL_DIMENSION_FIELD_NUMBER: _ClassVar[int]
    DETAIL_DIMENSION_PARENT_OBJECT_FIELD_NUMBER: _ClassVar[int]
    ID_FOR_EXPORT_IMPORT_FIELD_NUMBER: _ClassVar[int]
    METADATA_FOR_EXPORT_IMPORT_FIELD_NUMBER: _ClassVar[int]
    no: int
    type: Dimension.Type
    user_defined_name_enabled: bool
    name: str
    display_properties_index: int
    dimension_line_offset: float
    is_custom_vertical_position: bool
    custom_vertical_position: Dimension.CustomVerticalPosition
    is_custom_horizontal_position: bool
    custom_horizontal_position: Dimension.CustomHorizontalPosition
    symbol: str
    comment: str
    measured_length: float
    measured_lengths: _containers.RepeatedScalarFieldContainer[float]
    measured_angle: float
    measured_angles: _containers.RepeatedScalarFieldContainer[float]
    measured_slope: float
    is_global_dimension_line_offset: bool
    linear_coordinate_system: int
    linear_reference: Dimension.LinearReference
    linear_global_dimension_line_offset_y: float
    linear_global_dimension_line_offset_z: float
    linear_global_dimension_line_offset: _common_pb2.Vector3d
    linear_reference_table: Dimension.LinearReferenceTable
    arc_length_reference_line: int
    arc_length_reference_table: Dimension.ArcLengthReferenceTable
    arc_length_angle_greater_than_180: bool
    angular_reference_table: Dimension.AngularReferenceTable
    angular_quadrant: Dimension.AngularQuadrant
    angular_angle_greater_than_180: bool
    radius_diameter_reference_line: int
    radius_diameter_is_target_point: bool
    radius_diameter_target_point_coordinate_y: float
    radius_diameter_target_point_coordinate_z: float
    radius_diameter_target_point_coordinates: _common_pb2.Vector3d
    radius_diameter_position_on_line: float
    slope_coordinate_system: int
    slope_plane: Dimension.SlopePlane
    slope_reference_type: Dimension.SlopeReferenceType
    slope_reference_line: int
    slope_first_point_coordinate_y: float
    slope_first_point_coordinate_z: float
    slope_first_point_coordinates: _common_pb2.Vector3d
    slope_second_point_coordinate_y: float
    slope_second_point_coordinate_z: float
    slope_second_point_coordinates: _common_pb2.Vector3d
    slope_direction: Dimension.SlopeDirection
    slope_refer_distance_from_line_end: bool
    slope_position_absolute: float
    slope_position_relative: float
    slope_position_is_relative: bool
    parent_layer: int
    is_locked_by_parent_layer: bool
    is_generated: bool
    generating_object_info: str
    is_detail_dimension: bool
    detail_dimension_parent_object: int
    id_for_export_import: str
    metadata_for_export_import: str
    def __init__(self, no: _Optional[int] = ..., type: _Optional[_Union[Dimension.Type, str]] = ..., user_defined_name_enabled: bool = ..., name: _Optional[str] = ..., display_properties_index: _Optional[int] = ..., dimension_line_offset: _Optional[float] = ..., is_custom_vertical_position: bool = ..., custom_vertical_position: _Optional[_Union[Dimension.CustomVerticalPosition, str]] = ..., is_custom_horizontal_position: bool = ..., custom_horizontal_position: _Optional[_Union[Dimension.CustomHorizontalPosition, str]] = ..., symbol: _Optional[str] = ..., comment: _Optional[str] = ..., measured_length: _Optional[float] = ..., measured_lengths: _Optional[_Iterable[float]] = ..., measured_angle: _Optional[float] = ..., measured_angles: _Optional[_Iterable[float]] = ..., measured_slope: _Optional[float] = ..., is_global_dimension_line_offset: bool = ..., linear_coordinate_system: _Optional[int] = ..., linear_reference: _Optional[_Union[Dimension.LinearReference, str]] = ..., linear_global_dimension_line_offset_y: _Optional[float] = ..., linear_global_dimension_line_offset_z: _Optional[float] = ..., linear_global_dimension_line_offset: _Optional[_Union[_common_pb2.Vector3d, _Mapping]] = ..., linear_reference_table: _Optional[_Union[Dimension.LinearReferenceTable, _Mapping]] = ..., arc_length_reference_line: _Optional[int] = ..., arc_length_reference_table: _Optional[_Union[Dimension.ArcLengthReferenceTable, _Mapping]] = ..., arc_length_angle_greater_than_180: bool = ..., angular_reference_table: _Optional[_Union[Dimension.AngularReferenceTable, _Mapping]] = ..., angular_quadrant: _Optional[_Union[Dimension.AngularQuadrant, str]] = ..., angular_angle_greater_than_180: bool = ..., radius_diameter_reference_line: _Optional[int] = ..., radius_diameter_is_target_point: bool = ..., radius_diameter_target_point_coordinate_y: _Optional[float] = ..., radius_diameter_target_point_coordinate_z: _Optional[float] = ..., radius_diameter_target_point_coordinates: _Optional[_Union[_common_pb2.Vector3d, _Mapping]] = ..., radius_diameter_position_on_line: _Optional[float] = ..., slope_coordinate_system: _Optional[int] = ..., slope_plane: _Optional[_Union[Dimension.SlopePlane, str]] = ..., slope_reference_type: _Optional[_Union[Dimension.SlopeReferenceType, str]] = ..., slope_reference_line: _Optional[int] = ..., slope_first_point_coordinate_y: _Optional[float] = ..., slope_first_point_coordinate_z: _Optional[float] = ..., slope_first_point_coordinates: _Optional[_Union[_common_pb2.Vector3d, _Mapping]] = ..., slope_second_point_coordinate_y: _Optional[float] = ..., slope_second_point_coordinate_z: _Optional[float] = ..., slope_second_point_coordinates: _Optional[_Union[_common_pb2.Vector3d, _Mapping]] = ..., slope_direction: _Optional[_Union[Dimension.SlopeDirection, str]] = ..., slope_refer_distance_from_line_end: bool = ..., slope_position_absolute: _Optional[float] = ..., slope_position_relative: _Optional[float] = ..., slope_position_is_relative: bool = ..., parent_layer: _Optional[int] = ..., is_locked_by_parent_layer: bool = ..., is_generated: bool = ..., generating_object_info: _Optional[str] = ..., is_detail_dimension: bool = ..., detail_dimension_parent_object: _Optional[int] = ..., id_for_export_import: _Optional[str] = ..., metadata_for_export_import: _Optional[str] = ...) -> None: ...
