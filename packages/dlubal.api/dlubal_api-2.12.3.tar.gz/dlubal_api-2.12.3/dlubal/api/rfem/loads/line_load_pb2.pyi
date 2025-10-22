from dlubal.api.common import common_pb2 as _common_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class LineLoad(_message.Message):
    __slots__ = ("no", "load_type", "lines", "load_case", "coordinate_system", "load_distribution", "load_direction", "load_direction_orientation", "magnitude", "magnitude_1", "magnitude_2", "magnitude_3", "mass_global", "mass_x", "mass_y", "mass_z", "distance_a_is_defined_as_relative", "distance_a_absolute", "distance_a_relative", "distance_b_is_defined_as_relative", "distance_b_absolute", "distance_b_relative", "distance_c_is_defined_as_relative", "distance_c_absolute", "distance_c_relative", "count_n", "varying_load_parameters_are_defined_as_relative", "varying_load_parameters", "varying_load_parameters_sorted", "reference_to_list_of_lines", "distance_from_line_end", "load_is_over_total_length", "has_force_eccentricity", "is_eccentricity_at_end_different_from_start", "eccentricity_y_at_start", "eccentricity_z_at_start", "eccentricity_y_at_end", "eccentricity_z_at_end", "reference_point_a", "reference_point_b", "coating_polygon_area", "rotation_about_axis", "comment", "is_generated", "generating_object_info", "individual_mass_components", "import_support_reaction", "import_support_reaction_model_name", "import_support_reaction_model_description", "import_support_reaction_length_of_line", "import_support_reaction_load_direction", "coating_polygon_points", "prestress_tendon_load_definition_type", "prestress_tendon_load_definition", "prestress_tendon_load_ratio", "prestress_tendon_load_absolute_value", "id_for_export_import", "metadata_for_export_import")
    class LoadType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        LOAD_TYPE_UNKNOWN: _ClassVar[LineLoad.LoadType]
        LOAD_TYPE_FORCE: _ClassVar[LineLoad.LoadType]
        LOAD_TYPE_MASS: _ClassVar[LineLoad.LoadType]
        LOAD_TYPE_MOMENT: _ClassVar[LineLoad.LoadType]
    LOAD_TYPE_UNKNOWN: LineLoad.LoadType
    LOAD_TYPE_FORCE: LineLoad.LoadType
    LOAD_TYPE_MASS: LineLoad.LoadType
    LOAD_TYPE_MOMENT: LineLoad.LoadType
    class LoadDistribution(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        LOAD_DISTRIBUTION_UNIFORM: _ClassVar[LineLoad.LoadDistribution]
        LOAD_DISTRIBUTION_CONCENTRATED_1: _ClassVar[LineLoad.LoadDistribution]
        LOAD_DISTRIBUTION_CONCENTRATED_2: _ClassVar[LineLoad.LoadDistribution]
        LOAD_DISTRIBUTION_CONCENTRATED_2_2: _ClassVar[LineLoad.LoadDistribution]
        LOAD_DISTRIBUTION_CONCENTRATED_N: _ClassVar[LineLoad.LoadDistribution]
        LOAD_DISTRIBUTION_CONCENTRATED_VARYING: _ClassVar[LineLoad.LoadDistribution]
        LOAD_DISTRIBUTION_PARABOLIC: _ClassVar[LineLoad.LoadDistribution]
        LOAD_DISTRIBUTION_TAPERED: _ClassVar[LineLoad.LoadDistribution]
        LOAD_DISTRIBUTION_TRAPEZOIDAL: _ClassVar[LineLoad.LoadDistribution]
        LOAD_DISTRIBUTION_UNIFORM_TOTAL: _ClassVar[LineLoad.LoadDistribution]
        LOAD_DISTRIBUTION_VARYING: _ClassVar[LineLoad.LoadDistribution]
    LOAD_DISTRIBUTION_UNIFORM: LineLoad.LoadDistribution
    LOAD_DISTRIBUTION_CONCENTRATED_1: LineLoad.LoadDistribution
    LOAD_DISTRIBUTION_CONCENTRATED_2: LineLoad.LoadDistribution
    LOAD_DISTRIBUTION_CONCENTRATED_2_2: LineLoad.LoadDistribution
    LOAD_DISTRIBUTION_CONCENTRATED_N: LineLoad.LoadDistribution
    LOAD_DISTRIBUTION_CONCENTRATED_VARYING: LineLoad.LoadDistribution
    LOAD_DISTRIBUTION_PARABOLIC: LineLoad.LoadDistribution
    LOAD_DISTRIBUTION_TAPERED: LineLoad.LoadDistribution
    LOAD_DISTRIBUTION_TRAPEZOIDAL: LineLoad.LoadDistribution
    LOAD_DISTRIBUTION_UNIFORM_TOTAL: LineLoad.LoadDistribution
    LOAD_DISTRIBUTION_VARYING: LineLoad.LoadDistribution
    class LoadDirection(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        LOAD_DIRECTION_LOCAL_X: _ClassVar[LineLoad.LoadDirection]
        LOAD_DIRECTION_GLOBAL_X_OR_USER_DEFINED_U_PROJECTED_LENGTH: _ClassVar[LineLoad.LoadDirection]
        LOAD_DIRECTION_GLOBAL_X_OR_USER_DEFINED_U_TRUE_LENGTH: _ClassVar[LineLoad.LoadDirection]
        LOAD_DIRECTION_GLOBAL_Y_OR_USER_DEFINED_V_PROJECTED_LENGTH: _ClassVar[LineLoad.LoadDirection]
        LOAD_DIRECTION_GLOBAL_Y_OR_USER_DEFINED_V_TRUE_LENGTH: _ClassVar[LineLoad.LoadDirection]
        LOAD_DIRECTION_GLOBAL_Z_OR_USER_DEFINED_W_PROJECTED_LENGTH: _ClassVar[LineLoad.LoadDirection]
        LOAD_DIRECTION_GLOBAL_Z_OR_USER_DEFINED_W_TRUE_LENGTH: _ClassVar[LineLoad.LoadDirection]
        LOAD_DIRECTION_LOCAL_Y: _ClassVar[LineLoad.LoadDirection]
        LOAD_DIRECTION_LOCAL_Z: _ClassVar[LineLoad.LoadDirection]
    LOAD_DIRECTION_LOCAL_X: LineLoad.LoadDirection
    LOAD_DIRECTION_GLOBAL_X_OR_USER_DEFINED_U_PROJECTED_LENGTH: LineLoad.LoadDirection
    LOAD_DIRECTION_GLOBAL_X_OR_USER_DEFINED_U_TRUE_LENGTH: LineLoad.LoadDirection
    LOAD_DIRECTION_GLOBAL_Y_OR_USER_DEFINED_V_PROJECTED_LENGTH: LineLoad.LoadDirection
    LOAD_DIRECTION_GLOBAL_Y_OR_USER_DEFINED_V_TRUE_LENGTH: LineLoad.LoadDirection
    LOAD_DIRECTION_GLOBAL_Z_OR_USER_DEFINED_W_PROJECTED_LENGTH: LineLoad.LoadDirection
    LOAD_DIRECTION_GLOBAL_Z_OR_USER_DEFINED_W_TRUE_LENGTH: LineLoad.LoadDirection
    LOAD_DIRECTION_LOCAL_Y: LineLoad.LoadDirection
    LOAD_DIRECTION_LOCAL_Z: LineLoad.LoadDirection
    class LoadDirectionOrientation(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        LOAD_DIRECTION_ORIENTATION_LOAD_DIRECTION_FORWARD: _ClassVar[LineLoad.LoadDirectionOrientation]
        LOAD_DIRECTION_ORIENTATION_LOAD_DIRECTION_REVERSED: _ClassVar[LineLoad.LoadDirectionOrientation]
    LOAD_DIRECTION_ORIENTATION_LOAD_DIRECTION_FORWARD: LineLoad.LoadDirectionOrientation
    LOAD_DIRECTION_ORIENTATION_LOAD_DIRECTION_REVERSED: LineLoad.LoadDirectionOrientation
    class ImportSupportReactionLoadDirection(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        IMPORT_SUPPORT_REACTION_LOAD_DIRECTION_FORCE_GLOBAL_X: _ClassVar[LineLoad.ImportSupportReactionLoadDirection]
        IMPORT_SUPPORT_REACTION_LOAD_DIRECTION_FORCE_GLOBAL_Y: _ClassVar[LineLoad.ImportSupportReactionLoadDirection]
        IMPORT_SUPPORT_REACTION_LOAD_DIRECTION_FORCE_GLOBAL_Z: _ClassVar[LineLoad.ImportSupportReactionLoadDirection]
        IMPORT_SUPPORT_REACTION_LOAD_DIRECTION_FORCE_LOCAL_X: _ClassVar[LineLoad.ImportSupportReactionLoadDirection]
        IMPORT_SUPPORT_REACTION_LOAD_DIRECTION_FORCE_LOCAL_Y: _ClassVar[LineLoad.ImportSupportReactionLoadDirection]
        IMPORT_SUPPORT_REACTION_LOAD_DIRECTION_FORCE_LOCAL_Z: _ClassVar[LineLoad.ImportSupportReactionLoadDirection]
        IMPORT_SUPPORT_REACTION_LOAD_DIRECTION_MOMENT_GLOBAL_X: _ClassVar[LineLoad.ImportSupportReactionLoadDirection]
        IMPORT_SUPPORT_REACTION_LOAD_DIRECTION_MOMENT_GLOBAL_Y: _ClassVar[LineLoad.ImportSupportReactionLoadDirection]
        IMPORT_SUPPORT_REACTION_LOAD_DIRECTION_MOMENT_GLOBAL_Z: _ClassVar[LineLoad.ImportSupportReactionLoadDirection]
        IMPORT_SUPPORT_REACTION_LOAD_DIRECTION_MOMENT_LOCAL_X: _ClassVar[LineLoad.ImportSupportReactionLoadDirection]
        IMPORT_SUPPORT_REACTION_LOAD_DIRECTION_MOMENT_LOCAL_Y: _ClassVar[LineLoad.ImportSupportReactionLoadDirection]
        IMPORT_SUPPORT_REACTION_LOAD_DIRECTION_MOMENT_LOCAL_Z: _ClassVar[LineLoad.ImportSupportReactionLoadDirection]
    IMPORT_SUPPORT_REACTION_LOAD_DIRECTION_FORCE_GLOBAL_X: LineLoad.ImportSupportReactionLoadDirection
    IMPORT_SUPPORT_REACTION_LOAD_DIRECTION_FORCE_GLOBAL_Y: LineLoad.ImportSupportReactionLoadDirection
    IMPORT_SUPPORT_REACTION_LOAD_DIRECTION_FORCE_GLOBAL_Z: LineLoad.ImportSupportReactionLoadDirection
    IMPORT_SUPPORT_REACTION_LOAD_DIRECTION_FORCE_LOCAL_X: LineLoad.ImportSupportReactionLoadDirection
    IMPORT_SUPPORT_REACTION_LOAD_DIRECTION_FORCE_LOCAL_Y: LineLoad.ImportSupportReactionLoadDirection
    IMPORT_SUPPORT_REACTION_LOAD_DIRECTION_FORCE_LOCAL_Z: LineLoad.ImportSupportReactionLoadDirection
    IMPORT_SUPPORT_REACTION_LOAD_DIRECTION_MOMENT_GLOBAL_X: LineLoad.ImportSupportReactionLoadDirection
    IMPORT_SUPPORT_REACTION_LOAD_DIRECTION_MOMENT_GLOBAL_Y: LineLoad.ImportSupportReactionLoadDirection
    IMPORT_SUPPORT_REACTION_LOAD_DIRECTION_MOMENT_GLOBAL_Z: LineLoad.ImportSupportReactionLoadDirection
    IMPORT_SUPPORT_REACTION_LOAD_DIRECTION_MOMENT_LOCAL_X: LineLoad.ImportSupportReactionLoadDirection
    IMPORT_SUPPORT_REACTION_LOAD_DIRECTION_MOMENT_LOCAL_Y: LineLoad.ImportSupportReactionLoadDirection
    IMPORT_SUPPORT_REACTION_LOAD_DIRECTION_MOMENT_LOCAL_Z: LineLoad.ImportSupportReactionLoadDirection
    class PrestressTendonLoadDefinitionType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        PRESTRESS_TENDON_LOAD_DEFINITION_TYPE_STRESS: _ClassVar[LineLoad.PrestressTendonLoadDefinitionType]
        PRESTRESS_TENDON_LOAD_DEFINITION_TYPE_FORCE: _ClassVar[LineLoad.PrestressTendonLoadDefinitionType]
    PRESTRESS_TENDON_LOAD_DEFINITION_TYPE_STRESS: LineLoad.PrestressTendonLoadDefinitionType
    PRESTRESS_TENDON_LOAD_DEFINITION_TYPE_FORCE: LineLoad.PrestressTendonLoadDefinitionType
    class PrestressTendonLoadDefinition(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        PRESTRESS_TENDON_LOAD_DEFINITION_ABSOLUTE: _ClassVar[LineLoad.PrestressTendonLoadDefinition]
        PRESTRESS_TENDON_LOAD_DEFINITION_RELATIVE_TO_FPK: _ClassVar[LineLoad.PrestressTendonLoadDefinition]
        PRESTRESS_TENDON_LOAD_DEFINITION_RELATIVE_TO_FP_MAX: _ClassVar[LineLoad.PrestressTendonLoadDefinition]
    PRESTRESS_TENDON_LOAD_DEFINITION_ABSOLUTE: LineLoad.PrestressTendonLoadDefinition
    PRESTRESS_TENDON_LOAD_DEFINITION_RELATIVE_TO_FPK: LineLoad.PrestressTendonLoadDefinition
    PRESTRESS_TENDON_LOAD_DEFINITION_RELATIVE_TO_FP_MAX: LineLoad.PrestressTendonLoadDefinition
    class VaryingLoadParametersTable(_message.Message):
        __slots__ = ("rows",)
        ROWS_FIELD_NUMBER: _ClassVar[int]
        rows: _containers.RepeatedCompositeFieldContainer[LineLoad.VaryingLoadParametersRow]
        def __init__(self, rows: _Optional[_Iterable[_Union[LineLoad.VaryingLoadParametersRow, _Mapping]]] = ...) -> None: ...
    class VaryingLoadParametersRow(_message.Message):
        __slots__ = ("no", "description", "distance", "delta_distance", "magnitude", "note", "distance_unit", "delta_distance_unit", "magnitude_unit", "magnitude_symbol")
        NO_FIELD_NUMBER: _ClassVar[int]
        DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
        DISTANCE_FIELD_NUMBER: _ClassVar[int]
        DELTA_DISTANCE_FIELD_NUMBER: _ClassVar[int]
        MAGNITUDE_FIELD_NUMBER: _ClassVar[int]
        NOTE_FIELD_NUMBER: _ClassVar[int]
        DISTANCE_UNIT_FIELD_NUMBER: _ClassVar[int]
        DELTA_DISTANCE_UNIT_FIELD_NUMBER: _ClassVar[int]
        MAGNITUDE_UNIT_FIELD_NUMBER: _ClassVar[int]
        MAGNITUDE_SYMBOL_FIELD_NUMBER: _ClassVar[int]
        no: int
        description: str
        distance: float
        delta_distance: float
        magnitude: float
        note: str
        distance_unit: str
        delta_distance_unit: str
        magnitude_unit: str
        magnitude_symbol: str
        def __init__(self, no: _Optional[int] = ..., description: _Optional[str] = ..., distance: _Optional[float] = ..., delta_distance: _Optional[float] = ..., magnitude: _Optional[float] = ..., note: _Optional[str] = ..., distance_unit: _Optional[str] = ..., delta_distance_unit: _Optional[str] = ..., magnitude_unit: _Optional[str] = ..., magnitude_symbol: _Optional[str] = ...) -> None: ...
    class CoatingPolygonPointsTable(_message.Message):
        __slots__ = ("rows",)
        ROWS_FIELD_NUMBER: _ClassVar[int]
        rows: _containers.RepeatedCompositeFieldContainer[LineLoad.CoatingPolygonPointsRow]
        def __init__(self, rows: _Optional[_Iterable[_Union[LineLoad.CoatingPolygonPointsRow, _Mapping]]] = ...) -> None: ...
    class CoatingPolygonPointsRow(_message.Message):
        __slots__ = ("no", "description", "first_coordinate", "second_coordinate", "empty")
        NO_FIELD_NUMBER: _ClassVar[int]
        DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
        FIRST_COORDINATE_FIELD_NUMBER: _ClassVar[int]
        SECOND_COORDINATE_FIELD_NUMBER: _ClassVar[int]
        EMPTY_FIELD_NUMBER: _ClassVar[int]
        no: int
        description: str
        first_coordinate: float
        second_coordinate: float
        empty: _common_pb2.Value
        def __init__(self, no: _Optional[int] = ..., description: _Optional[str] = ..., first_coordinate: _Optional[float] = ..., second_coordinate: _Optional[float] = ..., empty: _Optional[_Union[_common_pb2.Value, _Mapping]] = ...) -> None: ...
    NO_FIELD_NUMBER: _ClassVar[int]
    LOAD_TYPE_FIELD_NUMBER: _ClassVar[int]
    LINES_FIELD_NUMBER: _ClassVar[int]
    LOAD_CASE_FIELD_NUMBER: _ClassVar[int]
    COORDINATE_SYSTEM_FIELD_NUMBER: _ClassVar[int]
    LOAD_DISTRIBUTION_FIELD_NUMBER: _ClassVar[int]
    LOAD_DIRECTION_FIELD_NUMBER: _ClassVar[int]
    LOAD_DIRECTION_ORIENTATION_FIELD_NUMBER: _ClassVar[int]
    MAGNITUDE_FIELD_NUMBER: _ClassVar[int]
    MAGNITUDE_1_FIELD_NUMBER: _ClassVar[int]
    MAGNITUDE_2_FIELD_NUMBER: _ClassVar[int]
    MAGNITUDE_3_FIELD_NUMBER: _ClassVar[int]
    MASS_GLOBAL_FIELD_NUMBER: _ClassVar[int]
    MASS_X_FIELD_NUMBER: _ClassVar[int]
    MASS_Y_FIELD_NUMBER: _ClassVar[int]
    MASS_Z_FIELD_NUMBER: _ClassVar[int]
    DISTANCE_A_IS_DEFINED_AS_RELATIVE_FIELD_NUMBER: _ClassVar[int]
    DISTANCE_A_ABSOLUTE_FIELD_NUMBER: _ClassVar[int]
    DISTANCE_A_RELATIVE_FIELD_NUMBER: _ClassVar[int]
    DISTANCE_B_IS_DEFINED_AS_RELATIVE_FIELD_NUMBER: _ClassVar[int]
    DISTANCE_B_ABSOLUTE_FIELD_NUMBER: _ClassVar[int]
    DISTANCE_B_RELATIVE_FIELD_NUMBER: _ClassVar[int]
    DISTANCE_C_IS_DEFINED_AS_RELATIVE_FIELD_NUMBER: _ClassVar[int]
    DISTANCE_C_ABSOLUTE_FIELD_NUMBER: _ClassVar[int]
    DISTANCE_C_RELATIVE_FIELD_NUMBER: _ClassVar[int]
    COUNT_N_FIELD_NUMBER: _ClassVar[int]
    VARYING_LOAD_PARAMETERS_ARE_DEFINED_AS_RELATIVE_FIELD_NUMBER: _ClassVar[int]
    VARYING_LOAD_PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    VARYING_LOAD_PARAMETERS_SORTED_FIELD_NUMBER: _ClassVar[int]
    REFERENCE_TO_LIST_OF_LINES_FIELD_NUMBER: _ClassVar[int]
    DISTANCE_FROM_LINE_END_FIELD_NUMBER: _ClassVar[int]
    LOAD_IS_OVER_TOTAL_LENGTH_FIELD_NUMBER: _ClassVar[int]
    HAS_FORCE_ECCENTRICITY_FIELD_NUMBER: _ClassVar[int]
    IS_ECCENTRICITY_AT_END_DIFFERENT_FROM_START_FIELD_NUMBER: _ClassVar[int]
    ECCENTRICITY_Y_AT_START_FIELD_NUMBER: _ClassVar[int]
    ECCENTRICITY_Z_AT_START_FIELD_NUMBER: _ClassVar[int]
    ECCENTRICITY_Y_AT_END_FIELD_NUMBER: _ClassVar[int]
    ECCENTRICITY_Z_AT_END_FIELD_NUMBER: _ClassVar[int]
    REFERENCE_POINT_A_FIELD_NUMBER: _ClassVar[int]
    REFERENCE_POINT_B_FIELD_NUMBER: _ClassVar[int]
    COATING_POLYGON_AREA_FIELD_NUMBER: _ClassVar[int]
    ROTATION_ABOUT_AXIS_FIELD_NUMBER: _ClassVar[int]
    COMMENT_FIELD_NUMBER: _ClassVar[int]
    IS_GENERATED_FIELD_NUMBER: _ClassVar[int]
    GENERATING_OBJECT_INFO_FIELD_NUMBER: _ClassVar[int]
    INDIVIDUAL_MASS_COMPONENTS_FIELD_NUMBER: _ClassVar[int]
    IMPORT_SUPPORT_REACTION_FIELD_NUMBER: _ClassVar[int]
    IMPORT_SUPPORT_REACTION_MODEL_NAME_FIELD_NUMBER: _ClassVar[int]
    IMPORT_SUPPORT_REACTION_MODEL_DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    IMPORT_SUPPORT_REACTION_LENGTH_OF_LINE_FIELD_NUMBER: _ClassVar[int]
    IMPORT_SUPPORT_REACTION_LOAD_DIRECTION_FIELD_NUMBER: _ClassVar[int]
    COATING_POLYGON_POINTS_FIELD_NUMBER: _ClassVar[int]
    PRESTRESS_TENDON_LOAD_DEFINITION_TYPE_FIELD_NUMBER: _ClassVar[int]
    PRESTRESS_TENDON_LOAD_DEFINITION_FIELD_NUMBER: _ClassVar[int]
    PRESTRESS_TENDON_LOAD_RATIO_FIELD_NUMBER: _ClassVar[int]
    PRESTRESS_TENDON_LOAD_ABSOLUTE_VALUE_FIELD_NUMBER: _ClassVar[int]
    ID_FOR_EXPORT_IMPORT_FIELD_NUMBER: _ClassVar[int]
    METADATA_FOR_EXPORT_IMPORT_FIELD_NUMBER: _ClassVar[int]
    no: int
    load_type: LineLoad.LoadType
    lines: _containers.RepeatedScalarFieldContainer[int]
    load_case: int
    coordinate_system: _common_pb2.CoordinateSystemRepresentation
    load_distribution: LineLoad.LoadDistribution
    load_direction: LineLoad.LoadDirection
    load_direction_orientation: LineLoad.LoadDirectionOrientation
    magnitude: float
    magnitude_1: float
    magnitude_2: float
    magnitude_3: float
    mass_global: float
    mass_x: float
    mass_y: float
    mass_z: float
    distance_a_is_defined_as_relative: bool
    distance_a_absolute: float
    distance_a_relative: float
    distance_b_is_defined_as_relative: bool
    distance_b_absolute: float
    distance_b_relative: float
    distance_c_is_defined_as_relative: bool
    distance_c_absolute: float
    distance_c_relative: float
    count_n: int
    varying_load_parameters_are_defined_as_relative: bool
    varying_load_parameters: LineLoad.VaryingLoadParametersTable
    varying_load_parameters_sorted: bool
    reference_to_list_of_lines: bool
    distance_from_line_end: bool
    load_is_over_total_length: bool
    has_force_eccentricity: bool
    is_eccentricity_at_end_different_from_start: bool
    eccentricity_y_at_start: float
    eccentricity_z_at_start: float
    eccentricity_y_at_end: float
    eccentricity_z_at_end: float
    reference_point_a: float
    reference_point_b: float
    coating_polygon_area: float
    rotation_about_axis: float
    comment: str
    is_generated: bool
    generating_object_info: str
    individual_mass_components: bool
    import_support_reaction: bool
    import_support_reaction_model_name: str
    import_support_reaction_model_description: str
    import_support_reaction_length_of_line: float
    import_support_reaction_load_direction: LineLoad.ImportSupportReactionLoadDirection
    coating_polygon_points: LineLoad.CoatingPolygonPointsTable
    prestress_tendon_load_definition_type: LineLoad.PrestressTendonLoadDefinitionType
    prestress_tendon_load_definition: LineLoad.PrestressTendonLoadDefinition
    prestress_tendon_load_ratio: float
    prestress_tendon_load_absolute_value: float
    id_for_export_import: str
    metadata_for_export_import: str
    def __init__(self, no: _Optional[int] = ..., load_type: _Optional[_Union[LineLoad.LoadType, str]] = ..., lines: _Optional[_Iterable[int]] = ..., load_case: _Optional[int] = ..., coordinate_system: _Optional[_Union[_common_pb2.CoordinateSystemRepresentation, _Mapping]] = ..., load_distribution: _Optional[_Union[LineLoad.LoadDistribution, str]] = ..., load_direction: _Optional[_Union[LineLoad.LoadDirection, str]] = ..., load_direction_orientation: _Optional[_Union[LineLoad.LoadDirectionOrientation, str]] = ..., magnitude: _Optional[float] = ..., magnitude_1: _Optional[float] = ..., magnitude_2: _Optional[float] = ..., magnitude_3: _Optional[float] = ..., mass_global: _Optional[float] = ..., mass_x: _Optional[float] = ..., mass_y: _Optional[float] = ..., mass_z: _Optional[float] = ..., distance_a_is_defined_as_relative: bool = ..., distance_a_absolute: _Optional[float] = ..., distance_a_relative: _Optional[float] = ..., distance_b_is_defined_as_relative: bool = ..., distance_b_absolute: _Optional[float] = ..., distance_b_relative: _Optional[float] = ..., distance_c_is_defined_as_relative: bool = ..., distance_c_absolute: _Optional[float] = ..., distance_c_relative: _Optional[float] = ..., count_n: _Optional[int] = ..., varying_load_parameters_are_defined_as_relative: bool = ..., varying_load_parameters: _Optional[_Union[LineLoad.VaryingLoadParametersTable, _Mapping]] = ..., varying_load_parameters_sorted: bool = ..., reference_to_list_of_lines: bool = ..., distance_from_line_end: bool = ..., load_is_over_total_length: bool = ..., has_force_eccentricity: bool = ..., is_eccentricity_at_end_different_from_start: bool = ..., eccentricity_y_at_start: _Optional[float] = ..., eccentricity_z_at_start: _Optional[float] = ..., eccentricity_y_at_end: _Optional[float] = ..., eccentricity_z_at_end: _Optional[float] = ..., reference_point_a: _Optional[float] = ..., reference_point_b: _Optional[float] = ..., coating_polygon_area: _Optional[float] = ..., rotation_about_axis: _Optional[float] = ..., comment: _Optional[str] = ..., is_generated: bool = ..., generating_object_info: _Optional[str] = ..., individual_mass_components: bool = ..., import_support_reaction: bool = ..., import_support_reaction_model_name: _Optional[str] = ..., import_support_reaction_model_description: _Optional[str] = ..., import_support_reaction_length_of_line: _Optional[float] = ..., import_support_reaction_load_direction: _Optional[_Union[LineLoad.ImportSupportReactionLoadDirection, str]] = ..., coating_polygon_points: _Optional[_Union[LineLoad.CoatingPolygonPointsTable, _Mapping]] = ..., prestress_tendon_load_definition_type: _Optional[_Union[LineLoad.PrestressTendonLoadDefinitionType, str]] = ..., prestress_tendon_load_definition: _Optional[_Union[LineLoad.PrestressTendonLoadDefinition, str]] = ..., prestress_tendon_load_ratio: _Optional[float] = ..., prestress_tendon_load_absolute_value: _Optional[float] = ..., id_for_export_import: _Optional[str] = ..., metadata_for_export_import: _Optional[str] = ...) -> None: ...
