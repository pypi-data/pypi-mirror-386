from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ConstructionStage(_message.Message):
    __slots__ = ("no", "user_defined_name_enabled", "name", "associated_standard", "to_solve", "previous_construction_stage", "start_time", "start_date", "end_time", "end_date", "duration", "loading", "generate_combinations", "static_analysis_settings", "consider_imperfection", "imperfection_case", "structure_modification_enabled", "structure_modification", "stability_analysis_enabled", "stability_analysis", "comment", "load_duration", "are_members_enabled_to_modify", "are_all_members_active", "added_members", "deactivated_members", "active_members", "member_property_modifications", "are_surfaces_enabled_to_modify", "are_all_surfaces_active", "added_surfaces", "deactivated_surfaces", "active_surfaces", "surface_property_modifications", "are_solids_enabled_to_modify", "are_all_solids_active", "added_solids", "deactivated_solids", "active_solids", "solid_property_modifications", "are_nodes_enabled_to_modify", "node_property_modifications", "are_surface_contacts_enabled_to_modify", "are_all_surface_contacts_active", "added_surface_contacts", "deactivated_surface_contacts", "active_surface_contacts", "are_rigid_links_enabled_to_modify", "are_all_rigid_links_active", "added_rigid_links", "deactivated_rigid_links", "active_rigid_links", "support_all_nodes_with_support", "add_nodes_to_support", "deactivated_nodes_for_support", "currently_supported_nodes", "are_line_supports_enabled_to_modify", "support_all_lines_with_support", "add_lines_to_support", "deactivated_lines_for_support", "currently_supported_lines", "line_support_property_modifications", "are_line_hinges_enabled_to_modify", "are_all_hinges_assigned", "add_line_hinges", "deactivated_line_hinges", "current_line_hinges", "are_line_welded_joints_enabled_to_modify", "are_all_welds_assigned", "add_line_welded_joints", "deactivated_line_welded_joints", "current_line_welded_joints", "geotechnical_analysis_reset_small_strain_history", "id_for_export_import", "metadata_for_export_import")
    class GenerateCombinations(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        GENERATE_COMBINATIONS_LOAD_COMBINATIONS: _ClassVar[ConstructionStage.GenerateCombinations]
    GENERATE_COMBINATIONS_LOAD_COMBINATIONS: ConstructionStage.GenerateCombinations
    class LoadDuration(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        LOAD_DURATION_UNKNOWN: _ClassVar[ConstructionStage.LoadDuration]
        LOAD_DURATION_10_MINUTES: _ClassVar[ConstructionStage.LoadDuration]
        LOAD_DURATION_10_SECONDS: _ClassVar[ConstructionStage.LoadDuration]
        LOAD_DURATION_12_HOURS: _ClassVar[ConstructionStage.LoadDuration]
        LOAD_DURATION_1_DAY: _ClassVar[ConstructionStage.LoadDuration]
        LOAD_DURATION_1_HOUR: _ClassVar[ConstructionStage.LoadDuration]
        LOAD_DURATION_1_MINUTE: _ClassVar[ConstructionStage.LoadDuration]
        LOAD_DURATION_1_MONTH: _ClassVar[ConstructionStage.LoadDuration]
        LOAD_DURATION_1_WEEK: _ClassVar[ConstructionStage.LoadDuration]
        LOAD_DURATION_1_YEAR: _ClassVar[ConstructionStage.LoadDuration]
        LOAD_DURATION_3_MONTHS: _ClassVar[ConstructionStage.LoadDuration]
        LOAD_DURATION_3_SECONDS: _ClassVar[ConstructionStage.LoadDuration]
        LOAD_DURATION_50_YEARS: _ClassVar[ConstructionStage.LoadDuration]
        LOAD_DURATION_5_DAYS: _ClassVar[ConstructionStage.LoadDuration]
        LOAD_DURATION_5_HOURS: _ClassVar[ConstructionStage.LoadDuration]
        LOAD_DURATION_5_MINUTES: _ClassVar[ConstructionStage.LoadDuration]
        LOAD_DURATION_5_MONTHS: _ClassVar[ConstructionStage.LoadDuration]
        LOAD_DURATION_5_SECONDS: _ClassVar[ConstructionStage.LoadDuration]
        LOAD_DURATION_ASD_IMPACT_LRFD_EQUAL_TO_1_25: _ClassVar[ConstructionStage.LoadDuration]
        LOAD_DURATION_ASD_PERMANENT_LRFD_EQUAL_TO_0_6: _ClassVar[ConstructionStage.LoadDuration]
        LOAD_DURATION_ASD_SEVEN_DAYS_LRFD_EQUAL_TO_0_9: _ClassVar[ConstructionStage.LoadDuration]
        LOAD_DURATION_ASD_TEN_MINUTES_LRFD_EQUAL_TO_1_0: _ClassVar[ConstructionStage.LoadDuration]
        LOAD_DURATION_ASD_TEN_YEARS_LRFD_EQUAL_TO_0_7: _ClassVar[ConstructionStage.LoadDuration]
        LOAD_DURATION_ASD_TWO_MONTHS_LRFD_EQUAL_TO_0_8: _ClassVar[ConstructionStage.LoadDuration]
        LOAD_DURATION_BEYOND_1_YEAR: _ClassVar[ConstructionStage.LoadDuration]
        LOAD_DURATION_IMPACT: _ClassVar[ConstructionStage.LoadDuration]
        LOAD_DURATION_INSTANTANEOUS: _ClassVar[ConstructionStage.LoadDuration]
        LOAD_DURATION_LONG_TERM: _ClassVar[ConstructionStage.LoadDuration]
        LOAD_DURATION_MEDIUM_TERM: _ClassVar[ConstructionStage.LoadDuration]
        LOAD_DURATION_PERMANENT: _ClassVar[ConstructionStage.LoadDuration]
        LOAD_DURATION_SEVEN_DAYS: _ClassVar[ConstructionStage.LoadDuration]
        LOAD_DURATION_SHORT_TERM: _ClassVar[ConstructionStage.LoadDuration]
        LOAD_DURATION_SHORT_TERM_INSTANTANEOUS: _ClassVar[ConstructionStage.LoadDuration]
        LOAD_DURATION_STANDARD_TERM: _ClassVar[ConstructionStage.LoadDuration]
        LOAD_DURATION_TEN_MINUTES: _ClassVar[ConstructionStage.LoadDuration]
        LOAD_DURATION_TEN_YEARS: _ClassVar[ConstructionStage.LoadDuration]
        LOAD_DURATION_TWO_MONTHS: _ClassVar[ConstructionStage.LoadDuration]
    LOAD_DURATION_UNKNOWN: ConstructionStage.LoadDuration
    LOAD_DURATION_10_MINUTES: ConstructionStage.LoadDuration
    LOAD_DURATION_10_SECONDS: ConstructionStage.LoadDuration
    LOAD_DURATION_12_HOURS: ConstructionStage.LoadDuration
    LOAD_DURATION_1_DAY: ConstructionStage.LoadDuration
    LOAD_DURATION_1_HOUR: ConstructionStage.LoadDuration
    LOAD_DURATION_1_MINUTE: ConstructionStage.LoadDuration
    LOAD_DURATION_1_MONTH: ConstructionStage.LoadDuration
    LOAD_DURATION_1_WEEK: ConstructionStage.LoadDuration
    LOAD_DURATION_1_YEAR: ConstructionStage.LoadDuration
    LOAD_DURATION_3_MONTHS: ConstructionStage.LoadDuration
    LOAD_DURATION_3_SECONDS: ConstructionStage.LoadDuration
    LOAD_DURATION_50_YEARS: ConstructionStage.LoadDuration
    LOAD_DURATION_5_DAYS: ConstructionStage.LoadDuration
    LOAD_DURATION_5_HOURS: ConstructionStage.LoadDuration
    LOAD_DURATION_5_MINUTES: ConstructionStage.LoadDuration
    LOAD_DURATION_5_MONTHS: ConstructionStage.LoadDuration
    LOAD_DURATION_5_SECONDS: ConstructionStage.LoadDuration
    LOAD_DURATION_ASD_IMPACT_LRFD_EQUAL_TO_1_25: ConstructionStage.LoadDuration
    LOAD_DURATION_ASD_PERMANENT_LRFD_EQUAL_TO_0_6: ConstructionStage.LoadDuration
    LOAD_DURATION_ASD_SEVEN_DAYS_LRFD_EQUAL_TO_0_9: ConstructionStage.LoadDuration
    LOAD_DURATION_ASD_TEN_MINUTES_LRFD_EQUAL_TO_1_0: ConstructionStage.LoadDuration
    LOAD_DURATION_ASD_TEN_YEARS_LRFD_EQUAL_TO_0_7: ConstructionStage.LoadDuration
    LOAD_DURATION_ASD_TWO_MONTHS_LRFD_EQUAL_TO_0_8: ConstructionStage.LoadDuration
    LOAD_DURATION_BEYOND_1_YEAR: ConstructionStage.LoadDuration
    LOAD_DURATION_IMPACT: ConstructionStage.LoadDuration
    LOAD_DURATION_INSTANTANEOUS: ConstructionStage.LoadDuration
    LOAD_DURATION_LONG_TERM: ConstructionStage.LoadDuration
    LOAD_DURATION_MEDIUM_TERM: ConstructionStage.LoadDuration
    LOAD_DURATION_PERMANENT: ConstructionStage.LoadDuration
    LOAD_DURATION_SEVEN_DAYS: ConstructionStage.LoadDuration
    LOAD_DURATION_SHORT_TERM: ConstructionStage.LoadDuration
    LOAD_DURATION_SHORT_TERM_INSTANTANEOUS: ConstructionStage.LoadDuration
    LOAD_DURATION_STANDARD_TERM: ConstructionStage.LoadDuration
    LOAD_DURATION_TEN_MINUTES: ConstructionStage.LoadDuration
    LOAD_DURATION_TEN_YEARS: ConstructionStage.LoadDuration
    LOAD_DURATION_TWO_MONTHS: ConstructionStage.LoadDuration
    class LoadingTable(_message.Message):
        __slots__ = ("rows",)
        ROWS_FIELD_NUMBER: _ClassVar[int]
        rows: _containers.RepeatedCompositeFieldContainer[ConstructionStage.LoadingRow]
        def __init__(self, rows: _Optional[_Iterable[_Union[ConstructionStage.LoadingRow, _Mapping]]] = ...) -> None: ...
    class LoadingRow(_message.Message):
        __slots__ = ("no", "description", "load_case", "status", "permanent", "factor")
        class Status(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = ()
            STATUS_ACTIVE_PERMANENT: _ClassVar[ConstructionStage.LoadingRow.Status]
            STATUS_INACTIVE: _ClassVar[ConstructionStage.LoadingRow.Status]
            STATUS_NONE: _ClassVar[ConstructionStage.LoadingRow.Status]
        STATUS_ACTIVE_PERMANENT: ConstructionStage.LoadingRow.Status
        STATUS_INACTIVE: ConstructionStage.LoadingRow.Status
        STATUS_NONE: ConstructionStage.LoadingRow.Status
        NO_FIELD_NUMBER: _ClassVar[int]
        DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
        LOAD_CASE_FIELD_NUMBER: _ClassVar[int]
        STATUS_FIELD_NUMBER: _ClassVar[int]
        PERMANENT_FIELD_NUMBER: _ClassVar[int]
        FACTOR_FIELD_NUMBER: _ClassVar[int]
        no: int
        description: str
        load_case: int
        status: ConstructionStage.LoadingRow.Status
        permanent: bool
        factor: float
        def __init__(self, no: _Optional[int] = ..., description: _Optional[str] = ..., load_case: _Optional[int] = ..., status: _Optional[_Union[ConstructionStage.LoadingRow.Status, str]] = ..., permanent: bool = ..., factor: _Optional[float] = ...) -> None: ...
    class MemberPropertyModificationsTable(_message.Message):
        __slots__ = ("rows",)
        ROWS_FIELD_NUMBER: _ClassVar[int]
        rows: _containers.RepeatedCompositeFieldContainer[ConstructionStage.MemberPropertyModificationsRow]
        def __init__(self, rows: _Optional[_Iterable[_Union[ConstructionStage.MemberPropertyModificationsRow, _Mapping]]] = ...) -> None: ...
    class MemberPropertyModificationsRow(_message.Message):
        __slots__ = ("no", "description", "members_no", "action", "property_to_modify", "original_value", "new_value", "comment")
        class Action(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = ()
            ACTION_MODIFICATION: _ClassVar[ConstructionStage.MemberPropertyModificationsRow.Action]
            ACTION_REPLACEMENT: _ClassVar[ConstructionStage.MemberPropertyModificationsRow.Action]
        ACTION_MODIFICATION: ConstructionStage.MemberPropertyModificationsRow.Action
        ACTION_REPLACEMENT: ConstructionStage.MemberPropertyModificationsRow.Action
        class PropertyToModify(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = ()
            PROPERTY_TO_MODIFY_UNKNOWN: _ClassVar[ConstructionStage.MemberPropertyModificationsRow.PropertyToModify]
            PROPERTY_TO_MODIFY_PROPERTY_TYPE_ALUMINUM_EFFECTIVE_LENGTH: _ClassVar[ConstructionStage.MemberPropertyModificationsRow.PropertyToModify]
            PROPERTY_TO_MODIFY_PROPERTY_TYPE_ALUMINUM_FIRE_RESISTANCE_CONFIGURATION: _ClassVar[ConstructionStage.MemberPropertyModificationsRow.PropertyToModify]
            PROPERTY_TO_MODIFY_PROPERTY_TYPE_ALUMINUM_SECTION_REDUCTION: _ClassVar[ConstructionStage.MemberPropertyModificationsRow.PropertyToModify]
            PROPERTY_TO_MODIFY_PROPERTY_TYPE_ALUMINUM_SERVICEABILITY_CONFIGURATION: _ClassVar[ConstructionStage.MemberPropertyModificationsRow.PropertyToModify]
            PROPERTY_TO_MODIFY_PROPERTY_TYPE_ALUMINUM_TRANSVERSE_WELD: _ClassVar[ConstructionStage.MemberPropertyModificationsRow.PropertyToModify]
            PROPERTY_TO_MODIFY_PROPERTY_TYPE_ALUMINUM_ULTIMATE_CONFIGURATION: _ClassVar[ConstructionStage.MemberPropertyModificationsRow.PropertyToModify]
            PROPERTY_TO_MODIFY_PROPERTY_TYPE_CONCRETE_EFFECTIVE_LENGTH: _ClassVar[ConstructionStage.MemberPropertyModificationsRow.PropertyToModify]
            PROPERTY_TO_MODIFY_PROPERTY_TYPE_CONCRETE_FIRE_RESISTANCE_CONFIGURATION: _ClassVar[ConstructionStage.MemberPropertyModificationsRow.PropertyToModify]
            PROPERTY_TO_MODIFY_PROPERTY_TYPE_CONCRETE_SEISMIC_CONFIGURATION: _ClassVar[ConstructionStage.MemberPropertyModificationsRow.PropertyToModify]
            PROPERTY_TO_MODIFY_PROPERTY_TYPE_CONCRETE_SERVICEABILITY_CONFIGURATION: _ClassVar[ConstructionStage.MemberPropertyModificationsRow.PropertyToModify]
            PROPERTY_TO_MODIFY_PROPERTY_TYPE_CONCRETE_ULTIMATE_CONFIGURATION: _ClassVar[ConstructionStage.MemberPropertyModificationsRow.PropertyToModify]
            PROPERTY_TO_MODIFY_PROPERTY_TYPE_SECTION_END: _ClassVar[ConstructionStage.MemberPropertyModificationsRow.PropertyToModify]
            PROPERTY_TO_MODIFY_PROPERTY_TYPE_SECTION_INTERNAL: _ClassVar[ConstructionStage.MemberPropertyModificationsRow.PropertyToModify]
            PROPERTY_TO_MODIFY_PROPERTY_TYPE_SECTION_START: _ClassVar[ConstructionStage.MemberPropertyModificationsRow.PropertyToModify]
            PROPERTY_TO_MODIFY_PROPERTY_TYPE_SECTION_TAPER_END: _ClassVar[ConstructionStage.MemberPropertyModificationsRow.PropertyToModify]
            PROPERTY_TO_MODIFY_PROPERTY_TYPE_SECTION_TAPER_START: _ClassVar[ConstructionStage.MemberPropertyModificationsRow.PropertyToModify]
            PROPERTY_TO_MODIFY_PROPERTY_TYPE_STEEL_BOUNDARY_CONDITION: _ClassVar[ConstructionStage.MemberPropertyModificationsRow.PropertyToModify]
            PROPERTY_TO_MODIFY_PROPERTY_TYPE_STEEL_EFFECTIVE_LENGTH: _ClassVar[ConstructionStage.MemberPropertyModificationsRow.PropertyToModify]
            PROPERTY_TO_MODIFY_PROPERTY_TYPE_STEEL_FIRE_RESISTANCE_CONFIGURATION: _ClassVar[ConstructionStage.MemberPropertyModificationsRow.PropertyToModify]
            PROPERTY_TO_MODIFY_PROPERTY_TYPE_STEEL_LOCAL_SECTION_REDUCTION: _ClassVar[ConstructionStage.MemberPropertyModificationsRow.PropertyToModify]
            PROPERTY_TO_MODIFY_PROPERTY_TYPE_STEEL_SEISMIC_CONFIGURATION: _ClassVar[ConstructionStage.MemberPropertyModificationsRow.PropertyToModify]
            PROPERTY_TO_MODIFY_PROPERTY_TYPE_STEEL_SERVICEABILITY_CONFIGURATION: _ClassVar[ConstructionStage.MemberPropertyModificationsRow.PropertyToModify]
            PROPERTY_TO_MODIFY_PROPERTY_TYPE_STEEL_ULTIMATE_CONFIGURATION: _ClassVar[ConstructionStage.MemberPropertyModificationsRow.PropertyToModify]
            PROPERTY_TO_MODIFY_PROPERTY_TYPE_SUPPORT: _ClassVar[ConstructionStage.MemberPropertyModificationsRow.PropertyToModify]
            PROPERTY_TO_MODIFY_PROPERTY_TYPE_TIMBER_EFFECTIVE_LENGTH: _ClassVar[ConstructionStage.MemberPropertyModificationsRow.PropertyToModify]
            PROPERTY_TO_MODIFY_PROPERTY_TYPE_TIMBER_FIRE_RESISTANCE_CONFIGURATION: _ClassVar[ConstructionStage.MemberPropertyModificationsRow.PropertyToModify]
            PROPERTY_TO_MODIFY_PROPERTY_TYPE_TIMBER_LOCAL_SECTION_REDUCTION: _ClassVar[ConstructionStage.MemberPropertyModificationsRow.PropertyToModify]
            PROPERTY_TO_MODIFY_PROPERTY_TYPE_TIMBER_SERVICEABILITY_CONFIGURATION: _ClassVar[ConstructionStage.MemberPropertyModificationsRow.PropertyToModify]
            PROPERTY_TO_MODIFY_PROPERTY_TYPE_TIMBER_SERVICE_CLASS: _ClassVar[ConstructionStage.MemberPropertyModificationsRow.PropertyToModify]
            PROPERTY_TO_MODIFY_PROPERTY_TYPE_TIMBER_ULTIMATE_CONFIGURATION: _ClassVar[ConstructionStage.MemberPropertyModificationsRow.PropertyToModify]
        PROPERTY_TO_MODIFY_UNKNOWN: ConstructionStage.MemberPropertyModificationsRow.PropertyToModify
        PROPERTY_TO_MODIFY_PROPERTY_TYPE_ALUMINUM_EFFECTIVE_LENGTH: ConstructionStage.MemberPropertyModificationsRow.PropertyToModify
        PROPERTY_TO_MODIFY_PROPERTY_TYPE_ALUMINUM_FIRE_RESISTANCE_CONFIGURATION: ConstructionStage.MemberPropertyModificationsRow.PropertyToModify
        PROPERTY_TO_MODIFY_PROPERTY_TYPE_ALUMINUM_SECTION_REDUCTION: ConstructionStage.MemberPropertyModificationsRow.PropertyToModify
        PROPERTY_TO_MODIFY_PROPERTY_TYPE_ALUMINUM_SERVICEABILITY_CONFIGURATION: ConstructionStage.MemberPropertyModificationsRow.PropertyToModify
        PROPERTY_TO_MODIFY_PROPERTY_TYPE_ALUMINUM_TRANSVERSE_WELD: ConstructionStage.MemberPropertyModificationsRow.PropertyToModify
        PROPERTY_TO_MODIFY_PROPERTY_TYPE_ALUMINUM_ULTIMATE_CONFIGURATION: ConstructionStage.MemberPropertyModificationsRow.PropertyToModify
        PROPERTY_TO_MODIFY_PROPERTY_TYPE_CONCRETE_EFFECTIVE_LENGTH: ConstructionStage.MemberPropertyModificationsRow.PropertyToModify
        PROPERTY_TO_MODIFY_PROPERTY_TYPE_CONCRETE_FIRE_RESISTANCE_CONFIGURATION: ConstructionStage.MemberPropertyModificationsRow.PropertyToModify
        PROPERTY_TO_MODIFY_PROPERTY_TYPE_CONCRETE_SEISMIC_CONFIGURATION: ConstructionStage.MemberPropertyModificationsRow.PropertyToModify
        PROPERTY_TO_MODIFY_PROPERTY_TYPE_CONCRETE_SERVICEABILITY_CONFIGURATION: ConstructionStage.MemberPropertyModificationsRow.PropertyToModify
        PROPERTY_TO_MODIFY_PROPERTY_TYPE_CONCRETE_ULTIMATE_CONFIGURATION: ConstructionStage.MemberPropertyModificationsRow.PropertyToModify
        PROPERTY_TO_MODIFY_PROPERTY_TYPE_SECTION_END: ConstructionStage.MemberPropertyModificationsRow.PropertyToModify
        PROPERTY_TO_MODIFY_PROPERTY_TYPE_SECTION_INTERNAL: ConstructionStage.MemberPropertyModificationsRow.PropertyToModify
        PROPERTY_TO_MODIFY_PROPERTY_TYPE_SECTION_START: ConstructionStage.MemberPropertyModificationsRow.PropertyToModify
        PROPERTY_TO_MODIFY_PROPERTY_TYPE_SECTION_TAPER_END: ConstructionStage.MemberPropertyModificationsRow.PropertyToModify
        PROPERTY_TO_MODIFY_PROPERTY_TYPE_SECTION_TAPER_START: ConstructionStage.MemberPropertyModificationsRow.PropertyToModify
        PROPERTY_TO_MODIFY_PROPERTY_TYPE_STEEL_BOUNDARY_CONDITION: ConstructionStage.MemberPropertyModificationsRow.PropertyToModify
        PROPERTY_TO_MODIFY_PROPERTY_TYPE_STEEL_EFFECTIVE_LENGTH: ConstructionStage.MemberPropertyModificationsRow.PropertyToModify
        PROPERTY_TO_MODIFY_PROPERTY_TYPE_STEEL_FIRE_RESISTANCE_CONFIGURATION: ConstructionStage.MemberPropertyModificationsRow.PropertyToModify
        PROPERTY_TO_MODIFY_PROPERTY_TYPE_STEEL_LOCAL_SECTION_REDUCTION: ConstructionStage.MemberPropertyModificationsRow.PropertyToModify
        PROPERTY_TO_MODIFY_PROPERTY_TYPE_STEEL_SEISMIC_CONFIGURATION: ConstructionStage.MemberPropertyModificationsRow.PropertyToModify
        PROPERTY_TO_MODIFY_PROPERTY_TYPE_STEEL_SERVICEABILITY_CONFIGURATION: ConstructionStage.MemberPropertyModificationsRow.PropertyToModify
        PROPERTY_TO_MODIFY_PROPERTY_TYPE_STEEL_ULTIMATE_CONFIGURATION: ConstructionStage.MemberPropertyModificationsRow.PropertyToModify
        PROPERTY_TO_MODIFY_PROPERTY_TYPE_SUPPORT: ConstructionStage.MemberPropertyModificationsRow.PropertyToModify
        PROPERTY_TO_MODIFY_PROPERTY_TYPE_TIMBER_EFFECTIVE_LENGTH: ConstructionStage.MemberPropertyModificationsRow.PropertyToModify
        PROPERTY_TO_MODIFY_PROPERTY_TYPE_TIMBER_FIRE_RESISTANCE_CONFIGURATION: ConstructionStage.MemberPropertyModificationsRow.PropertyToModify
        PROPERTY_TO_MODIFY_PROPERTY_TYPE_TIMBER_LOCAL_SECTION_REDUCTION: ConstructionStage.MemberPropertyModificationsRow.PropertyToModify
        PROPERTY_TO_MODIFY_PROPERTY_TYPE_TIMBER_SERVICEABILITY_CONFIGURATION: ConstructionStage.MemberPropertyModificationsRow.PropertyToModify
        PROPERTY_TO_MODIFY_PROPERTY_TYPE_TIMBER_SERVICE_CLASS: ConstructionStage.MemberPropertyModificationsRow.PropertyToModify
        PROPERTY_TO_MODIFY_PROPERTY_TYPE_TIMBER_ULTIMATE_CONFIGURATION: ConstructionStage.MemberPropertyModificationsRow.PropertyToModify
        NO_FIELD_NUMBER: _ClassVar[int]
        DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
        MEMBERS_NO_FIELD_NUMBER: _ClassVar[int]
        ACTION_FIELD_NUMBER: _ClassVar[int]
        PROPERTY_TO_MODIFY_FIELD_NUMBER: _ClassVar[int]
        ORIGINAL_VALUE_FIELD_NUMBER: _ClassVar[int]
        NEW_VALUE_FIELD_NUMBER: _ClassVar[int]
        COMMENT_FIELD_NUMBER: _ClassVar[int]
        no: int
        description: str
        members_no: _containers.RepeatedScalarFieldContainer[int]
        action: ConstructionStage.MemberPropertyModificationsRow.Action
        property_to_modify: ConstructionStage.MemberPropertyModificationsRow.PropertyToModify
        original_value: int
        new_value: int
        comment: str
        def __init__(self, no: _Optional[int] = ..., description: _Optional[str] = ..., members_no: _Optional[_Iterable[int]] = ..., action: _Optional[_Union[ConstructionStage.MemberPropertyModificationsRow.Action, str]] = ..., property_to_modify: _Optional[_Union[ConstructionStage.MemberPropertyModificationsRow.PropertyToModify, str]] = ..., original_value: _Optional[int] = ..., new_value: _Optional[int] = ..., comment: _Optional[str] = ...) -> None: ...
    class SurfacePropertyModificationsTable(_message.Message):
        __slots__ = ("rows",)
        ROWS_FIELD_NUMBER: _ClassVar[int]
        rows: _containers.RepeatedCompositeFieldContainer[ConstructionStage.SurfacePropertyModificationsRow]
        def __init__(self, rows: _Optional[_Iterable[_Union[ConstructionStage.SurfacePropertyModificationsRow, _Mapping]]] = ...) -> None: ...
    class SurfacePropertyModificationsRow(_message.Message):
        __slots__ = ("no", "description", "surfaces_no", "action", "property_to_modify", "original_value", "new_value", "comment")
        class Action(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = ()
            ACTION_MODIFICATION: _ClassVar[ConstructionStage.SurfacePropertyModificationsRow.Action]
            ACTION_REPLACEMENT: _ClassVar[ConstructionStage.SurfacePropertyModificationsRow.Action]
        ACTION_MODIFICATION: ConstructionStage.SurfacePropertyModificationsRow.Action
        ACTION_REPLACEMENT: ConstructionStage.SurfacePropertyModificationsRow.Action
        class PropertyToModify(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = ()
            PROPERTY_TO_MODIFY_UNKNOWN: _ClassVar[ConstructionStage.SurfacePropertyModificationsRow.PropertyToModify]
            PROPERTY_TO_MODIFY_PROPERTY_TYPE_ALUMINUM_SERVICEABILITY_CONFIGURATION: _ClassVar[ConstructionStage.SurfacePropertyModificationsRow.PropertyToModify]
            PROPERTY_TO_MODIFY_PROPERTY_TYPE_ALUMINUM_ULTIMATE_CONFIGURATION: _ClassVar[ConstructionStage.SurfacePropertyModificationsRow.PropertyToModify]
            PROPERTY_TO_MODIFY_PROPERTY_TYPE_CONCRETE_FIRE_RESISTANCE_CONFIGURATION: _ClassVar[ConstructionStage.SurfacePropertyModificationsRow.PropertyToModify]
            PROPERTY_TO_MODIFY_PROPERTY_TYPE_CONCRETE_SEISMIC_CONFIGURATION: _ClassVar[ConstructionStage.SurfacePropertyModificationsRow.PropertyToModify]
            PROPERTY_TO_MODIFY_PROPERTY_TYPE_CONCRETE_SERVICEABILITY_CONFIGURATION: _ClassVar[ConstructionStage.SurfacePropertyModificationsRow.PropertyToModify]
            PROPERTY_TO_MODIFY_PROPERTY_TYPE_CONCRETE_ULTIMATE_CONFIGURATION: _ClassVar[ConstructionStage.SurfacePropertyModificationsRow.PropertyToModify]
            PROPERTY_TO_MODIFY_PROPERTY_TYPE_GLASS_SERVICEABILITY_CONFIGURATION: _ClassVar[ConstructionStage.SurfacePropertyModificationsRow.PropertyToModify]
            PROPERTY_TO_MODIFY_PROPERTY_TYPE_GLASS_ULTIMATE_CONFIGURATION: _ClassVar[ConstructionStage.SurfacePropertyModificationsRow.PropertyToModify]
            PROPERTY_TO_MODIFY_PROPERTY_TYPE_STEEL_SERVICEABILITY_CONFIGURATION: _ClassVar[ConstructionStage.SurfacePropertyModificationsRow.PropertyToModify]
            PROPERTY_TO_MODIFY_PROPERTY_TYPE_STEEL_ULTIMATE_CONFIGURATION: _ClassVar[ConstructionStage.SurfacePropertyModificationsRow.PropertyToModify]
            PROPERTY_TO_MODIFY_PROPERTY_TYPE_SUPPORT: _ClassVar[ConstructionStage.SurfacePropertyModificationsRow.PropertyToModify]
            PROPERTY_TO_MODIFY_PROPERTY_TYPE_THICKNESS: _ClassVar[ConstructionStage.SurfacePropertyModificationsRow.PropertyToModify]
            PROPERTY_TO_MODIFY_PROPERTY_TYPE_TIMBER_FIRE_RESISTANCE_CONFIGURATION: _ClassVar[ConstructionStage.SurfacePropertyModificationsRow.PropertyToModify]
            PROPERTY_TO_MODIFY_PROPERTY_TYPE_TIMBER_SERVICEABILITY_CONFIGURATION: _ClassVar[ConstructionStage.SurfacePropertyModificationsRow.PropertyToModify]
            PROPERTY_TO_MODIFY_PROPERTY_TYPE_TIMBER_SERVICE_CLASS: _ClassVar[ConstructionStage.SurfacePropertyModificationsRow.PropertyToModify]
            PROPERTY_TO_MODIFY_PROPERTY_TYPE_TIMBER_ULTIMATE_CONFIGURATION: _ClassVar[ConstructionStage.SurfacePropertyModificationsRow.PropertyToModify]
        PROPERTY_TO_MODIFY_UNKNOWN: ConstructionStage.SurfacePropertyModificationsRow.PropertyToModify
        PROPERTY_TO_MODIFY_PROPERTY_TYPE_ALUMINUM_SERVICEABILITY_CONFIGURATION: ConstructionStage.SurfacePropertyModificationsRow.PropertyToModify
        PROPERTY_TO_MODIFY_PROPERTY_TYPE_ALUMINUM_ULTIMATE_CONFIGURATION: ConstructionStage.SurfacePropertyModificationsRow.PropertyToModify
        PROPERTY_TO_MODIFY_PROPERTY_TYPE_CONCRETE_FIRE_RESISTANCE_CONFIGURATION: ConstructionStage.SurfacePropertyModificationsRow.PropertyToModify
        PROPERTY_TO_MODIFY_PROPERTY_TYPE_CONCRETE_SEISMIC_CONFIGURATION: ConstructionStage.SurfacePropertyModificationsRow.PropertyToModify
        PROPERTY_TO_MODIFY_PROPERTY_TYPE_CONCRETE_SERVICEABILITY_CONFIGURATION: ConstructionStage.SurfacePropertyModificationsRow.PropertyToModify
        PROPERTY_TO_MODIFY_PROPERTY_TYPE_CONCRETE_ULTIMATE_CONFIGURATION: ConstructionStage.SurfacePropertyModificationsRow.PropertyToModify
        PROPERTY_TO_MODIFY_PROPERTY_TYPE_GLASS_SERVICEABILITY_CONFIGURATION: ConstructionStage.SurfacePropertyModificationsRow.PropertyToModify
        PROPERTY_TO_MODIFY_PROPERTY_TYPE_GLASS_ULTIMATE_CONFIGURATION: ConstructionStage.SurfacePropertyModificationsRow.PropertyToModify
        PROPERTY_TO_MODIFY_PROPERTY_TYPE_STEEL_SERVICEABILITY_CONFIGURATION: ConstructionStage.SurfacePropertyModificationsRow.PropertyToModify
        PROPERTY_TO_MODIFY_PROPERTY_TYPE_STEEL_ULTIMATE_CONFIGURATION: ConstructionStage.SurfacePropertyModificationsRow.PropertyToModify
        PROPERTY_TO_MODIFY_PROPERTY_TYPE_SUPPORT: ConstructionStage.SurfacePropertyModificationsRow.PropertyToModify
        PROPERTY_TO_MODIFY_PROPERTY_TYPE_THICKNESS: ConstructionStage.SurfacePropertyModificationsRow.PropertyToModify
        PROPERTY_TO_MODIFY_PROPERTY_TYPE_TIMBER_FIRE_RESISTANCE_CONFIGURATION: ConstructionStage.SurfacePropertyModificationsRow.PropertyToModify
        PROPERTY_TO_MODIFY_PROPERTY_TYPE_TIMBER_SERVICEABILITY_CONFIGURATION: ConstructionStage.SurfacePropertyModificationsRow.PropertyToModify
        PROPERTY_TO_MODIFY_PROPERTY_TYPE_TIMBER_SERVICE_CLASS: ConstructionStage.SurfacePropertyModificationsRow.PropertyToModify
        PROPERTY_TO_MODIFY_PROPERTY_TYPE_TIMBER_ULTIMATE_CONFIGURATION: ConstructionStage.SurfacePropertyModificationsRow.PropertyToModify
        NO_FIELD_NUMBER: _ClassVar[int]
        DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
        SURFACES_NO_FIELD_NUMBER: _ClassVar[int]
        ACTION_FIELD_NUMBER: _ClassVar[int]
        PROPERTY_TO_MODIFY_FIELD_NUMBER: _ClassVar[int]
        ORIGINAL_VALUE_FIELD_NUMBER: _ClassVar[int]
        NEW_VALUE_FIELD_NUMBER: _ClassVar[int]
        COMMENT_FIELD_NUMBER: _ClassVar[int]
        no: int
        description: str
        surfaces_no: _containers.RepeatedScalarFieldContainer[int]
        action: ConstructionStage.SurfacePropertyModificationsRow.Action
        property_to_modify: ConstructionStage.SurfacePropertyModificationsRow.PropertyToModify
        original_value: int
        new_value: int
        comment: str
        def __init__(self, no: _Optional[int] = ..., description: _Optional[str] = ..., surfaces_no: _Optional[_Iterable[int]] = ..., action: _Optional[_Union[ConstructionStage.SurfacePropertyModificationsRow.Action, str]] = ..., property_to_modify: _Optional[_Union[ConstructionStage.SurfacePropertyModificationsRow.PropertyToModify, str]] = ..., original_value: _Optional[int] = ..., new_value: _Optional[int] = ..., comment: _Optional[str] = ...) -> None: ...
    class SolidPropertyModificationsTable(_message.Message):
        __slots__ = ("rows",)
        ROWS_FIELD_NUMBER: _ClassVar[int]
        rows: _containers.RepeatedCompositeFieldContainer[ConstructionStage.SolidPropertyModificationsRow]
        def __init__(self, rows: _Optional[_Iterable[_Union[ConstructionStage.SolidPropertyModificationsRow, _Mapping]]] = ...) -> None: ...
    class SolidPropertyModificationsRow(_message.Message):
        __slots__ = ("no", "description", "solids_no", "action", "property_to_modify", "original_value", "new_value", "comment")
        class Action(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = ()
            ACTION_MODIFICATION: _ClassVar[ConstructionStage.SolidPropertyModificationsRow.Action]
            ACTION_REPLACEMENT: _ClassVar[ConstructionStage.SolidPropertyModificationsRow.Action]
        ACTION_MODIFICATION: ConstructionStage.SolidPropertyModificationsRow.Action
        ACTION_REPLACEMENT: ConstructionStage.SolidPropertyModificationsRow.Action
        class PropertyToModify(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = ()
            PROPERTY_TO_MODIFY_UNKNOWN: _ClassVar[ConstructionStage.SolidPropertyModificationsRow.PropertyToModify]
        PROPERTY_TO_MODIFY_UNKNOWN: ConstructionStage.SolidPropertyModificationsRow.PropertyToModify
        NO_FIELD_NUMBER: _ClassVar[int]
        DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
        SOLIDS_NO_FIELD_NUMBER: _ClassVar[int]
        ACTION_FIELD_NUMBER: _ClassVar[int]
        PROPERTY_TO_MODIFY_FIELD_NUMBER: _ClassVar[int]
        ORIGINAL_VALUE_FIELD_NUMBER: _ClassVar[int]
        NEW_VALUE_FIELD_NUMBER: _ClassVar[int]
        COMMENT_FIELD_NUMBER: _ClassVar[int]
        no: int
        description: str
        solids_no: _containers.RepeatedScalarFieldContainer[int]
        action: ConstructionStage.SolidPropertyModificationsRow.Action
        property_to_modify: ConstructionStage.SolidPropertyModificationsRow.PropertyToModify
        original_value: int
        new_value: int
        comment: str
        def __init__(self, no: _Optional[int] = ..., description: _Optional[str] = ..., solids_no: _Optional[_Iterable[int]] = ..., action: _Optional[_Union[ConstructionStage.SolidPropertyModificationsRow.Action, str]] = ..., property_to_modify: _Optional[_Union[ConstructionStage.SolidPropertyModificationsRow.PropertyToModify, str]] = ..., original_value: _Optional[int] = ..., new_value: _Optional[int] = ..., comment: _Optional[str] = ...) -> None: ...
    class NodePropertyModificationsTable(_message.Message):
        __slots__ = ("rows",)
        ROWS_FIELD_NUMBER: _ClassVar[int]
        rows: _containers.RepeatedCompositeFieldContainer[ConstructionStage.NodePropertyModificationsRow]
        def __init__(self, rows: _Optional[_Iterable[_Union[ConstructionStage.NodePropertyModificationsRow, _Mapping]]] = ...) -> None: ...
    class NodePropertyModificationsRow(_message.Message):
        __slots__ = ("no", "description", "nodes_no", "action", "property_to_modify", "original_value", "new_value", "comment")
        class Action(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = ()
            ACTION_MODIFICATION: _ClassVar[ConstructionStage.NodePropertyModificationsRow.Action]
            ACTION_REPLACEMENT: _ClassVar[ConstructionStage.NodePropertyModificationsRow.Action]
        ACTION_MODIFICATION: ConstructionStage.NodePropertyModificationsRow.Action
        ACTION_REPLACEMENT: ConstructionStage.NodePropertyModificationsRow.Action
        class PropertyToModify(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = ()
            PROPERTY_TO_MODIFY_UNKNOWN: _ClassVar[ConstructionStage.NodePropertyModificationsRow.PropertyToModify]
            PROPERTY_TO_MODIFY_PROPERTY_TYPE_SUPPORT: _ClassVar[ConstructionStage.NodePropertyModificationsRow.PropertyToModify]
        PROPERTY_TO_MODIFY_UNKNOWN: ConstructionStage.NodePropertyModificationsRow.PropertyToModify
        PROPERTY_TO_MODIFY_PROPERTY_TYPE_SUPPORT: ConstructionStage.NodePropertyModificationsRow.PropertyToModify
        NO_FIELD_NUMBER: _ClassVar[int]
        DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
        NODES_NO_FIELD_NUMBER: _ClassVar[int]
        ACTION_FIELD_NUMBER: _ClassVar[int]
        PROPERTY_TO_MODIFY_FIELD_NUMBER: _ClassVar[int]
        ORIGINAL_VALUE_FIELD_NUMBER: _ClassVar[int]
        NEW_VALUE_FIELD_NUMBER: _ClassVar[int]
        COMMENT_FIELD_NUMBER: _ClassVar[int]
        no: int
        description: str
        nodes_no: _containers.RepeatedScalarFieldContainer[int]
        action: ConstructionStage.NodePropertyModificationsRow.Action
        property_to_modify: ConstructionStage.NodePropertyModificationsRow.PropertyToModify
        original_value: int
        new_value: int
        comment: str
        def __init__(self, no: _Optional[int] = ..., description: _Optional[str] = ..., nodes_no: _Optional[_Iterable[int]] = ..., action: _Optional[_Union[ConstructionStage.NodePropertyModificationsRow.Action, str]] = ..., property_to_modify: _Optional[_Union[ConstructionStage.NodePropertyModificationsRow.PropertyToModify, str]] = ..., original_value: _Optional[int] = ..., new_value: _Optional[int] = ..., comment: _Optional[str] = ...) -> None: ...
    class LineSupportPropertyModificationsTable(_message.Message):
        __slots__ = ("rows",)
        ROWS_FIELD_NUMBER: _ClassVar[int]
        rows: _containers.RepeatedCompositeFieldContainer[ConstructionStage.LineSupportPropertyModificationsRow]
        def __init__(self, rows: _Optional[_Iterable[_Union[ConstructionStage.LineSupportPropertyModificationsRow, _Mapping]]] = ...) -> None: ...
    class LineSupportPropertyModificationsRow(_message.Message):
        __slots__ = ("no", "description", "lines_no", "action", "property_to_modify", "original_value", "new_value", "comment")
        class Action(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = ()
            ACTION_MODIFICATION: _ClassVar[ConstructionStage.LineSupportPropertyModificationsRow.Action]
            ACTION_REPLACEMENT: _ClassVar[ConstructionStage.LineSupportPropertyModificationsRow.Action]
        ACTION_MODIFICATION: ConstructionStage.LineSupportPropertyModificationsRow.Action
        ACTION_REPLACEMENT: ConstructionStage.LineSupportPropertyModificationsRow.Action
        class PropertyToModify(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = ()
            PROPERTY_TO_MODIFY_UNKNOWN: _ClassVar[ConstructionStage.LineSupportPropertyModificationsRow.PropertyToModify]
            PROPERTY_TO_MODIFY_PROPERTY_TYPE_SUPPORT: _ClassVar[ConstructionStage.LineSupportPropertyModificationsRow.PropertyToModify]
        PROPERTY_TO_MODIFY_UNKNOWN: ConstructionStage.LineSupportPropertyModificationsRow.PropertyToModify
        PROPERTY_TO_MODIFY_PROPERTY_TYPE_SUPPORT: ConstructionStage.LineSupportPropertyModificationsRow.PropertyToModify
        NO_FIELD_NUMBER: _ClassVar[int]
        DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
        LINES_NO_FIELD_NUMBER: _ClassVar[int]
        ACTION_FIELD_NUMBER: _ClassVar[int]
        PROPERTY_TO_MODIFY_FIELD_NUMBER: _ClassVar[int]
        ORIGINAL_VALUE_FIELD_NUMBER: _ClassVar[int]
        NEW_VALUE_FIELD_NUMBER: _ClassVar[int]
        COMMENT_FIELD_NUMBER: _ClassVar[int]
        no: int
        description: str
        lines_no: _containers.RepeatedScalarFieldContainer[int]
        action: ConstructionStage.LineSupportPropertyModificationsRow.Action
        property_to_modify: ConstructionStage.LineSupportPropertyModificationsRow.PropertyToModify
        original_value: int
        new_value: int
        comment: str
        def __init__(self, no: _Optional[int] = ..., description: _Optional[str] = ..., lines_no: _Optional[_Iterable[int]] = ..., action: _Optional[_Union[ConstructionStage.LineSupportPropertyModificationsRow.Action, str]] = ..., property_to_modify: _Optional[_Union[ConstructionStage.LineSupportPropertyModificationsRow.PropertyToModify, str]] = ..., original_value: _Optional[int] = ..., new_value: _Optional[int] = ..., comment: _Optional[str] = ...) -> None: ...
    NO_FIELD_NUMBER: _ClassVar[int]
    USER_DEFINED_NAME_ENABLED_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    ASSOCIATED_STANDARD_FIELD_NUMBER: _ClassVar[int]
    TO_SOLVE_FIELD_NUMBER: _ClassVar[int]
    PREVIOUS_CONSTRUCTION_STAGE_FIELD_NUMBER: _ClassVar[int]
    START_TIME_FIELD_NUMBER: _ClassVar[int]
    START_DATE_FIELD_NUMBER: _ClassVar[int]
    END_TIME_FIELD_NUMBER: _ClassVar[int]
    END_DATE_FIELD_NUMBER: _ClassVar[int]
    DURATION_FIELD_NUMBER: _ClassVar[int]
    LOADING_FIELD_NUMBER: _ClassVar[int]
    GENERATE_COMBINATIONS_FIELD_NUMBER: _ClassVar[int]
    STATIC_ANALYSIS_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    CONSIDER_IMPERFECTION_FIELD_NUMBER: _ClassVar[int]
    IMPERFECTION_CASE_FIELD_NUMBER: _ClassVar[int]
    STRUCTURE_MODIFICATION_ENABLED_FIELD_NUMBER: _ClassVar[int]
    STRUCTURE_MODIFICATION_FIELD_NUMBER: _ClassVar[int]
    STABILITY_ANALYSIS_ENABLED_FIELD_NUMBER: _ClassVar[int]
    STABILITY_ANALYSIS_FIELD_NUMBER: _ClassVar[int]
    COMMENT_FIELD_NUMBER: _ClassVar[int]
    LOAD_DURATION_FIELD_NUMBER: _ClassVar[int]
    ARE_MEMBERS_ENABLED_TO_MODIFY_FIELD_NUMBER: _ClassVar[int]
    ARE_ALL_MEMBERS_ACTIVE_FIELD_NUMBER: _ClassVar[int]
    ADDED_MEMBERS_FIELD_NUMBER: _ClassVar[int]
    DEACTIVATED_MEMBERS_FIELD_NUMBER: _ClassVar[int]
    ACTIVE_MEMBERS_FIELD_NUMBER: _ClassVar[int]
    MEMBER_PROPERTY_MODIFICATIONS_FIELD_NUMBER: _ClassVar[int]
    ARE_SURFACES_ENABLED_TO_MODIFY_FIELD_NUMBER: _ClassVar[int]
    ARE_ALL_SURFACES_ACTIVE_FIELD_NUMBER: _ClassVar[int]
    ADDED_SURFACES_FIELD_NUMBER: _ClassVar[int]
    DEACTIVATED_SURFACES_FIELD_NUMBER: _ClassVar[int]
    ACTIVE_SURFACES_FIELD_NUMBER: _ClassVar[int]
    SURFACE_PROPERTY_MODIFICATIONS_FIELD_NUMBER: _ClassVar[int]
    ARE_SOLIDS_ENABLED_TO_MODIFY_FIELD_NUMBER: _ClassVar[int]
    ARE_ALL_SOLIDS_ACTIVE_FIELD_NUMBER: _ClassVar[int]
    ADDED_SOLIDS_FIELD_NUMBER: _ClassVar[int]
    DEACTIVATED_SOLIDS_FIELD_NUMBER: _ClassVar[int]
    ACTIVE_SOLIDS_FIELD_NUMBER: _ClassVar[int]
    SOLID_PROPERTY_MODIFICATIONS_FIELD_NUMBER: _ClassVar[int]
    ARE_NODES_ENABLED_TO_MODIFY_FIELD_NUMBER: _ClassVar[int]
    NODE_PROPERTY_MODIFICATIONS_FIELD_NUMBER: _ClassVar[int]
    ARE_SURFACE_CONTACTS_ENABLED_TO_MODIFY_FIELD_NUMBER: _ClassVar[int]
    ARE_ALL_SURFACE_CONTACTS_ACTIVE_FIELD_NUMBER: _ClassVar[int]
    ADDED_SURFACE_CONTACTS_FIELD_NUMBER: _ClassVar[int]
    DEACTIVATED_SURFACE_CONTACTS_FIELD_NUMBER: _ClassVar[int]
    ACTIVE_SURFACE_CONTACTS_FIELD_NUMBER: _ClassVar[int]
    ARE_RIGID_LINKS_ENABLED_TO_MODIFY_FIELD_NUMBER: _ClassVar[int]
    ARE_ALL_RIGID_LINKS_ACTIVE_FIELD_NUMBER: _ClassVar[int]
    ADDED_RIGID_LINKS_FIELD_NUMBER: _ClassVar[int]
    DEACTIVATED_RIGID_LINKS_FIELD_NUMBER: _ClassVar[int]
    ACTIVE_RIGID_LINKS_FIELD_NUMBER: _ClassVar[int]
    SUPPORT_ALL_NODES_WITH_SUPPORT_FIELD_NUMBER: _ClassVar[int]
    ADD_NODES_TO_SUPPORT_FIELD_NUMBER: _ClassVar[int]
    DEACTIVATED_NODES_FOR_SUPPORT_FIELD_NUMBER: _ClassVar[int]
    CURRENTLY_SUPPORTED_NODES_FIELD_NUMBER: _ClassVar[int]
    ARE_LINE_SUPPORTS_ENABLED_TO_MODIFY_FIELD_NUMBER: _ClassVar[int]
    SUPPORT_ALL_LINES_WITH_SUPPORT_FIELD_NUMBER: _ClassVar[int]
    ADD_LINES_TO_SUPPORT_FIELD_NUMBER: _ClassVar[int]
    DEACTIVATED_LINES_FOR_SUPPORT_FIELD_NUMBER: _ClassVar[int]
    CURRENTLY_SUPPORTED_LINES_FIELD_NUMBER: _ClassVar[int]
    LINE_SUPPORT_PROPERTY_MODIFICATIONS_FIELD_NUMBER: _ClassVar[int]
    ARE_LINE_HINGES_ENABLED_TO_MODIFY_FIELD_NUMBER: _ClassVar[int]
    ARE_ALL_HINGES_ASSIGNED_FIELD_NUMBER: _ClassVar[int]
    ADD_LINE_HINGES_FIELD_NUMBER: _ClassVar[int]
    DEACTIVATED_LINE_HINGES_FIELD_NUMBER: _ClassVar[int]
    CURRENT_LINE_HINGES_FIELD_NUMBER: _ClassVar[int]
    ARE_LINE_WELDED_JOINTS_ENABLED_TO_MODIFY_FIELD_NUMBER: _ClassVar[int]
    ARE_ALL_WELDS_ASSIGNED_FIELD_NUMBER: _ClassVar[int]
    ADD_LINE_WELDED_JOINTS_FIELD_NUMBER: _ClassVar[int]
    DEACTIVATED_LINE_WELDED_JOINTS_FIELD_NUMBER: _ClassVar[int]
    CURRENT_LINE_WELDED_JOINTS_FIELD_NUMBER: _ClassVar[int]
    GEOTECHNICAL_ANALYSIS_RESET_SMALL_STRAIN_HISTORY_FIELD_NUMBER: _ClassVar[int]
    ID_FOR_EXPORT_IMPORT_FIELD_NUMBER: _ClassVar[int]
    METADATA_FOR_EXPORT_IMPORT_FIELD_NUMBER: _ClassVar[int]
    no: int
    user_defined_name_enabled: bool
    name: str
    associated_standard: int
    to_solve: bool
    previous_construction_stage: int
    start_time: float
    start_date: str
    end_time: float
    end_date: str
    duration: float
    loading: ConstructionStage.LoadingTable
    generate_combinations: ConstructionStage.GenerateCombinations
    static_analysis_settings: int
    consider_imperfection: bool
    imperfection_case: int
    structure_modification_enabled: bool
    structure_modification: int
    stability_analysis_enabled: bool
    stability_analysis: int
    comment: str
    load_duration: ConstructionStage.LoadDuration
    are_members_enabled_to_modify: bool
    are_all_members_active: bool
    added_members: _containers.RepeatedScalarFieldContainer[int]
    deactivated_members: _containers.RepeatedScalarFieldContainer[int]
    active_members: _containers.RepeatedScalarFieldContainer[int]
    member_property_modifications: ConstructionStage.MemberPropertyModificationsTable
    are_surfaces_enabled_to_modify: bool
    are_all_surfaces_active: bool
    added_surfaces: _containers.RepeatedScalarFieldContainer[int]
    deactivated_surfaces: _containers.RepeatedScalarFieldContainer[int]
    active_surfaces: _containers.RepeatedScalarFieldContainer[int]
    surface_property_modifications: ConstructionStage.SurfacePropertyModificationsTable
    are_solids_enabled_to_modify: bool
    are_all_solids_active: bool
    added_solids: _containers.RepeatedScalarFieldContainer[int]
    deactivated_solids: _containers.RepeatedScalarFieldContainer[int]
    active_solids: _containers.RepeatedScalarFieldContainer[int]
    solid_property_modifications: ConstructionStage.SolidPropertyModificationsTable
    are_nodes_enabled_to_modify: bool
    node_property_modifications: ConstructionStage.NodePropertyModificationsTable
    are_surface_contacts_enabled_to_modify: bool
    are_all_surface_contacts_active: bool
    added_surface_contacts: _containers.RepeatedScalarFieldContainer[int]
    deactivated_surface_contacts: _containers.RepeatedScalarFieldContainer[int]
    active_surface_contacts: _containers.RepeatedScalarFieldContainer[int]
    are_rigid_links_enabled_to_modify: bool
    are_all_rigid_links_active: bool
    added_rigid_links: _containers.RepeatedScalarFieldContainer[int]
    deactivated_rigid_links: _containers.RepeatedScalarFieldContainer[int]
    active_rigid_links: _containers.RepeatedScalarFieldContainer[int]
    support_all_nodes_with_support: bool
    add_nodes_to_support: _containers.RepeatedScalarFieldContainer[int]
    deactivated_nodes_for_support: _containers.RepeatedScalarFieldContainer[int]
    currently_supported_nodes: _containers.RepeatedScalarFieldContainer[int]
    are_line_supports_enabled_to_modify: bool
    support_all_lines_with_support: bool
    add_lines_to_support: _containers.RepeatedScalarFieldContainer[int]
    deactivated_lines_for_support: _containers.RepeatedScalarFieldContainer[int]
    currently_supported_lines: _containers.RepeatedScalarFieldContainer[int]
    line_support_property_modifications: ConstructionStage.LineSupportPropertyModificationsTable
    are_line_hinges_enabled_to_modify: bool
    are_all_hinges_assigned: bool
    add_line_hinges: str
    deactivated_line_hinges: str
    current_line_hinges: str
    are_line_welded_joints_enabled_to_modify: bool
    are_all_welds_assigned: bool
    add_line_welded_joints: str
    deactivated_line_welded_joints: str
    current_line_welded_joints: str
    geotechnical_analysis_reset_small_strain_history: bool
    id_for_export_import: str
    metadata_for_export_import: str
    def __init__(self, no: _Optional[int] = ..., user_defined_name_enabled: bool = ..., name: _Optional[str] = ..., associated_standard: _Optional[int] = ..., to_solve: bool = ..., previous_construction_stage: _Optional[int] = ..., start_time: _Optional[float] = ..., start_date: _Optional[str] = ..., end_time: _Optional[float] = ..., end_date: _Optional[str] = ..., duration: _Optional[float] = ..., loading: _Optional[_Union[ConstructionStage.LoadingTable, _Mapping]] = ..., generate_combinations: _Optional[_Union[ConstructionStage.GenerateCombinations, str]] = ..., static_analysis_settings: _Optional[int] = ..., consider_imperfection: bool = ..., imperfection_case: _Optional[int] = ..., structure_modification_enabled: bool = ..., structure_modification: _Optional[int] = ..., stability_analysis_enabled: bool = ..., stability_analysis: _Optional[int] = ..., comment: _Optional[str] = ..., load_duration: _Optional[_Union[ConstructionStage.LoadDuration, str]] = ..., are_members_enabled_to_modify: bool = ..., are_all_members_active: bool = ..., added_members: _Optional[_Iterable[int]] = ..., deactivated_members: _Optional[_Iterable[int]] = ..., active_members: _Optional[_Iterable[int]] = ..., member_property_modifications: _Optional[_Union[ConstructionStage.MemberPropertyModificationsTable, _Mapping]] = ..., are_surfaces_enabled_to_modify: bool = ..., are_all_surfaces_active: bool = ..., added_surfaces: _Optional[_Iterable[int]] = ..., deactivated_surfaces: _Optional[_Iterable[int]] = ..., active_surfaces: _Optional[_Iterable[int]] = ..., surface_property_modifications: _Optional[_Union[ConstructionStage.SurfacePropertyModificationsTable, _Mapping]] = ..., are_solids_enabled_to_modify: bool = ..., are_all_solids_active: bool = ..., added_solids: _Optional[_Iterable[int]] = ..., deactivated_solids: _Optional[_Iterable[int]] = ..., active_solids: _Optional[_Iterable[int]] = ..., solid_property_modifications: _Optional[_Union[ConstructionStage.SolidPropertyModificationsTable, _Mapping]] = ..., are_nodes_enabled_to_modify: bool = ..., node_property_modifications: _Optional[_Union[ConstructionStage.NodePropertyModificationsTable, _Mapping]] = ..., are_surface_contacts_enabled_to_modify: bool = ..., are_all_surface_contacts_active: bool = ..., added_surface_contacts: _Optional[_Iterable[int]] = ..., deactivated_surface_contacts: _Optional[_Iterable[int]] = ..., active_surface_contacts: _Optional[_Iterable[int]] = ..., are_rigid_links_enabled_to_modify: bool = ..., are_all_rigid_links_active: bool = ..., added_rigid_links: _Optional[_Iterable[int]] = ..., deactivated_rigid_links: _Optional[_Iterable[int]] = ..., active_rigid_links: _Optional[_Iterable[int]] = ..., support_all_nodes_with_support: bool = ..., add_nodes_to_support: _Optional[_Iterable[int]] = ..., deactivated_nodes_for_support: _Optional[_Iterable[int]] = ..., currently_supported_nodes: _Optional[_Iterable[int]] = ..., are_line_supports_enabled_to_modify: bool = ..., support_all_lines_with_support: bool = ..., add_lines_to_support: _Optional[_Iterable[int]] = ..., deactivated_lines_for_support: _Optional[_Iterable[int]] = ..., currently_supported_lines: _Optional[_Iterable[int]] = ..., line_support_property_modifications: _Optional[_Union[ConstructionStage.LineSupportPropertyModificationsTable, _Mapping]] = ..., are_line_hinges_enabled_to_modify: bool = ..., are_all_hinges_assigned: bool = ..., add_line_hinges: _Optional[str] = ..., deactivated_line_hinges: _Optional[str] = ..., current_line_hinges: _Optional[str] = ..., are_line_welded_joints_enabled_to_modify: bool = ..., are_all_welds_assigned: bool = ..., add_line_welded_joints: _Optional[str] = ..., deactivated_line_welded_joints: _Optional[str] = ..., current_line_welded_joints: _Optional[str] = ..., geotechnical_analysis_reset_small_strain_history: bool = ..., id_for_export_import: _Optional[str] = ..., metadata_for_export_import: _Optional[str] = ...) -> None: ...
