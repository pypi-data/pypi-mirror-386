from dlubal.api.rstab import object_id_pb2 as _object_id_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class LoadCombination(_message.Message):
    __slots__ = ("no", "analysis_type", "associated_standard", "design_situation", "user_defined_name_enabled", "name", "static_analysis_settings", "import_modal_analysis_load_case", "calculate_critical_load", "stability_analysis_settings", "consider_imperfection", "imperfection_case", "consider_initial_state", "initial_state_case", "consider_creep_loading_case", "creep_loading_case", "import_elastic_support_coefficients", "elastic_support_coefficients_loading", "sustained_load_enabled", "sustained_load", "sway_load_enabled", "sway_load", "structure_modification_enabled", "structure_modification", "to_solve", "comment", "load_duration", "items", "combination_rule_str", "loading_start", "time_being_investigated", "is_generated", "generating_object_info", "initial_state_definition_type", "individual_factors_of_selected_objects_table", "pushover_analysis_settings", "pushover_vertical_loads_case", "pushover_modal_analysis_from_load_case", "pushover_direction", "pushover_normalized_displacements", "pushover_mode_shape_number", "pushover_response_spectrum", "pushover_response_spectrum_scale_factor", "time_history_analysis_settings", "time_history_import_masses_from", "corresponding_load_combinations", "id_for_export_import", "metadata_for_export_import")
    class AnalysisType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        ANALYSIS_TYPE_UNKNOWN: _ClassVar[LoadCombination.AnalysisType]
        ANALYSIS_TYPE_HARMONIC_RESPONSE_ANALYSIS: _ClassVar[LoadCombination.AnalysisType]
        ANALYSIS_TYPE_PUSHOVER: _ClassVar[LoadCombination.AnalysisType]
        ANALYSIS_TYPE_STATIC_ANALYSIS: _ClassVar[LoadCombination.AnalysisType]
        ANALYSIS_TYPE_STATIC_CREEP_AND_SHRINKAGE: _ClassVar[LoadCombination.AnalysisType]
        ANALYSIS_TYPE_STATIC_TIME_DEPENDENCE: _ClassVar[LoadCombination.AnalysisType]
        ANALYSIS_TYPE_TIME_HISTORY_TIME_DIAGRAM: _ClassVar[LoadCombination.AnalysisType]
    ANALYSIS_TYPE_UNKNOWN: LoadCombination.AnalysisType
    ANALYSIS_TYPE_HARMONIC_RESPONSE_ANALYSIS: LoadCombination.AnalysisType
    ANALYSIS_TYPE_PUSHOVER: LoadCombination.AnalysisType
    ANALYSIS_TYPE_STATIC_ANALYSIS: LoadCombination.AnalysisType
    ANALYSIS_TYPE_STATIC_CREEP_AND_SHRINKAGE: LoadCombination.AnalysisType
    ANALYSIS_TYPE_STATIC_TIME_DEPENDENCE: LoadCombination.AnalysisType
    ANALYSIS_TYPE_TIME_HISTORY_TIME_DIAGRAM: LoadCombination.AnalysisType
    class LoadDuration(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        LOAD_DURATION_UNKNOWN: _ClassVar[LoadCombination.LoadDuration]
        LOAD_DURATION_10_MINUTES: _ClassVar[LoadCombination.LoadDuration]
        LOAD_DURATION_10_SECONDS: _ClassVar[LoadCombination.LoadDuration]
        LOAD_DURATION_12_HOURS: _ClassVar[LoadCombination.LoadDuration]
        LOAD_DURATION_1_DAY: _ClassVar[LoadCombination.LoadDuration]
        LOAD_DURATION_1_HOUR: _ClassVar[LoadCombination.LoadDuration]
        LOAD_DURATION_1_MINUTE: _ClassVar[LoadCombination.LoadDuration]
        LOAD_DURATION_1_MONTH: _ClassVar[LoadCombination.LoadDuration]
        LOAD_DURATION_1_WEEK: _ClassVar[LoadCombination.LoadDuration]
        LOAD_DURATION_1_YEAR: _ClassVar[LoadCombination.LoadDuration]
        LOAD_DURATION_3_MONTHS: _ClassVar[LoadCombination.LoadDuration]
        LOAD_DURATION_3_SECONDS: _ClassVar[LoadCombination.LoadDuration]
        LOAD_DURATION_50_YEARS: _ClassVar[LoadCombination.LoadDuration]
        LOAD_DURATION_5_DAYS: _ClassVar[LoadCombination.LoadDuration]
        LOAD_DURATION_5_HOURS: _ClassVar[LoadCombination.LoadDuration]
        LOAD_DURATION_5_MINUTES: _ClassVar[LoadCombination.LoadDuration]
        LOAD_DURATION_5_MONTHS: _ClassVar[LoadCombination.LoadDuration]
        LOAD_DURATION_5_SECONDS: _ClassVar[LoadCombination.LoadDuration]
        LOAD_DURATION_ASD_IMPACT_LRFD_EQUAL_TO_1_25: _ClassVar[LoadCombination.LoadDuration]
        LOAD_DURATION_ASD_PERMANENT_LRFD_EQUAL_TO_0_6: _ClassVar[LoadCombination.LoadDuration]
        LOAD_DURATION_ASD_SEVEN_DAYS_LRFD_EQUAL_TO_0_9: _ClassVar[LoadCombination.LoadDuration]
        LOAD_DURATION_ASD_TEN_MINUTES_LRFD_EQUAL_TO_1_0: _ClassVar[LoadCombination.LoadDuration]
        LOAD_DURATION_ASD_TEN_YEARS_LRFD_EQUAL_TO_0_7: _ClassVar[LoadCombination.LoadDuration]
        LOAD_DURATION_ASD_TWO_MONTHS_LRFD_EQUAL_TO_0_8: _ClassVar[LoadCombination.LoadDuration]
        LOAD_DURATION_BEYOND_1_YEAR: _ClassVar[LoadCombination.LoadDuration]
        LOAD_DURATION_IMPACT: _ClassVar[LoadCombination.LoadDuration]
        LOAD_DURATION_INSTANTANEOUS: _ClassVar[LoadCombination.LoadDuration]
        LOAD_DURATION_LONG_TERM: _ClassVar[LoadCombination.LoadDuration]
        LOAD_DURATION_MEDIUM_TERM: _ClassVar[LoadCombination.LoadDuration]
        LOAD_DURATION_PERMANENT: _ClassVar[LoadCombination.LoadDuration]
        LOAD_DURATION_SEVEN_DAYS: _ClassVar[LoadCombination.LoadDuration]
        LOAD_DURATION_SHORT_TERM: _ClassVar[LoadCombination.LoadDuration]
        LOAD_DURATION_SHORT_TERM_INSTANTANEOUS: _ClassVar[LoadCombination.LoadDuration]
        LOAD_DURATION_STANDARD_TERM: _ClassVar[LoadCombination.LoadDuration]
        LOAD_DURATION_TEN_MINUTES: _ClassVar[LoadCombination.LoadDuration]
        LOAD_DURATION_TEN_YEARS: _ClassVar[LoadCombination.LoadDuration]
        LOAD_DURATION_TWO_MONTHS: _ClassVar[LoadCombination.LoadDuration]
    LOAD_DURATION_UNKNOWN: LoadCombination.LoadDuration
    LOAD_DURATION_10_MINUTES: LoadCombination.LoadDuration
    LOAD_DURATION_10_SECONDS: LoadCombination.LoadDuration
    LOAD_DURATION_12_HOURS: LoadCombination.LoadDuration
    LOAD_DURATION_1_DAY: LoadCombination.LoadDuration
    LOAD_DURATION_1_HOUR: LoadCombination.LoadDuration
    LOAD_DURATION_1_MINUTE: LoadCombination.LoadDuration
    LOAD_DURATION_1_MONTH: LoadCombination.LoadDuration
    LOAD_DURATION_1_WEEK: LoadCombination.LoadDuration
    LOAD_DURATION_1_YEAR: LoadCombination.LoadDuration
    LOAD_DURATION_3_MONTHS: LoadCombination.LoadDuration
    LOAD_DURATION_3_SECONDS: LoadCombination.LoadDuration
    LOAD_DURATION_50_YEARS: LoadCombination.LoadDuration
    LOAD_DURATION_5_DAYS: LoadCombination.LoadDuration
    LOAD_DURATION_5_HOURS: LoadCombination.LoadDuration
    LOAD_DURATION_5_MINUTES: LoadCombination.LoadDuration
    LOAD_DURATION_5_MONTHS: LoadCombination.LoadDuration
    LOAD_DURATION_5_SECONDS: LoadCombination.LoadDuration
    LOAD_DURATION_ASD_IMPACT_LRFD_EQUAL_TO_1_25: LoadCombination.LoadDuration
    LOAD_DURATION_ASD_PERMANENT_LRFD_EQUAL_TO_0_6: LoadCombination.LoadDuration
    LOAD_DURATION_ASD_SEVEN_DAYS_LRFD_EQUAL_TO_0_9: LoadCombination.LoadDuration
    LOAD_DURATION_ASD_TEN_MINUTES_LRFD_EQUAL_TO_1_0: LoadCombination.LoadDuration
    LOAD_DURATION_ASD_TEN_YEARS_LRFD_EQUAL_TO_0_7: LoadCombination.LoadDuration
    LOAD_DURATION_ASD_TWO_MONTHS_LRFD_EQUAL_TO_0_8: LoadCombination.LoadDuration
    LOAD_DURATION_BEYOND_1_YEAR: LoadCombination.LoadDuration
    LOAD_DURATION_IMPACT: LoadCombination.LoadDuration
    LOAD_DURATION_INSTANTANEOUS: LoadCombination.LoadDuration
    LOAD_DURATION_LONG_TERM: LoadCombination.LoadDuration
    LOAD_DURATION_MEDIUM_TERM: LoadCombination.LoadDuration
    LOAD_DURATION_PERMANENT: LoadCombination.LoadDuration
    LOAD_DURATION_SEVEN_DAYS: LoadCombination.LoadDuration
    LOAD_DURATION_SHORT_TERM: LoadCombination.LoadDuration
    LOAD_DURATION_SHORT_TERM_INSTANTANEOUS: LoadCombination.LoadDuration
    LOAD_DURATION_STANDARD_TERM: LoadCombination.LoadDuration
    LOAD_DURATION_TEN_MINUTES: LoadCombination.LoadDuration
    LOAD_DURATION_TEN_YEARS: LoadCombination.LoadDuration
    LOAD_DURATION_TWO_MONTHS: LoadCombination.LoadDuration
    class InitialStateDefinitionType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        INITIAL_STATE_DEFINITION_TYPE_FINAL_STATE: _ClassVar[LoadCombination.InitialStateDefinitionType]
        INITIAL_STATE_DEFINITION_TYPE_STIFFNESS: _ClassVar[LoadCombination.InitialStateDefinitionType]
        INITIAL_STATE_DEFINITION_TYPE_STRAINS: _ClassVar[LoadCombination.InitialStateDefinitionType]
        INITIAL_STATE_DEFINITION_TYPE_STRAINS_WITH_USER_DEFINED_FACTORS: _ClassVar[LoadCombination.InitialStateDefinitionType]
    INITIAL_STATE_DEFINITION_TYPE_FINAL_STATE: LoadCombination.InitialStateDefinitionType
    INITIAL_STATE_DEFINITION_TYPE_STIFFNESS: LoadCombination.InitialStateDefinitionType
    INITIAL_STATE_DEFINITION_TYPE_STRAINS: LoadCombination.InitialStateDefinitionType
    INITIAL_STATE_DEFINITION_TYPE_STRAINS_WITH_USER_DEFINED_FACTORS: LoadCombination.InitialStateDefinitionType
    class PushoverDirection(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        PUSHOVER_DIRECTION_X: _ClassVar[LoadCombination.PushoverDirection]
        PUSHOVER_DIRECTION_MINUS_X: _ClassVar[LoadCombination.PushoverDirection]
        PUSHOVER_DIRECTION_MINUS_Y: _ClassVar[LoadCombination.PushoverDirection]
        PUSHOVER_DIRECTION_Y: _ClassVar[LoadCombination.PushoverDirection]
    PUSHOVER_DIRECTION_X: LoadCombination.PushoverDirection
    PUSHOVER_DIRECTION_MINUS_X: LoadCombination.PushoverDirection
    PUSHOVER_DIRECTION_MINUS_Y: LoadCombination.PushoverDirection
    PUSHOVER_DIRECTION_Y: LoadCombination.PushoverDirection
    class PushoverNormalizedDisplacements(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        PUSHOVER_NORMALIZED_DISPLACEMENTS_UNIFORM: _ClassVar[LoadCombination.PushoverNormalizedDisplacements]
        PUSHOVER_NORMALIZED_DISPLACEMENTS_MODAL_AUTOMATIC_MODAL_SHAPE: _ClassVar[LoadCombination.PushoverNormalizedDisplacements]
        PUSHOVER_NORMALIZED_DISPLACEMENTS_MODAL_USER_SELECTED_MODAL_SHAPE: _ClassVar[LoadCombination.PushoverNormalizedDisplacements]
    PUSHOVER_NORMALIZED_DISPLACEMENTS_UNIFORM: LoadCombination.PushoverNormalizedDisplacements
    PUSHOVER_NORMALIZED_DISPLACEMENTS_MODAL_AUTOMATIC_MODAL_SHAPE: LoadCombination.PushoverNormalizedDisplacements
    PUSHOVER_NORMALIZED_DISPLACEMENTS_MODAL_USER_SELECTED_MODAL_SHAPE: LoadCombination.PushoverNormalizedDisplacements
    class ItemsTable(_message.Message):
        __slots__ = ("rows",)
        ROWS_FIELD_NUMBER: _ClassVar[int]
        rows: _containers.RepeatedCompositeFieldContainer[LoadCombination.ItemsRow]
        def __init__(self, rows: _Optional[_Iterable[_Union[LoadCombination.ItemsRow, _Mapping]]] = ...) -> None: ...
    class ItemsRow(_message.Message):
        __slots__ = ("no", "description", "factor", "load_case", "action", "is_leading", "gamma", "psi", "xi", "k_fi", "c_esl", "k_def", "psi_0", "psi_1", "psi_2", "fi", "gamma_0", "alfa", "k_f", "phi", "rho", "omega_0", "gamma_l_1", "k_creep", "gamma_n", "j_2", "omega_m", "omega_n", "d1", "d2", "shift", "amplitude_function", "time_diagram", "time_slip")
        class AmplitudeFunction(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = ()
            AMPLITUDE_FUNCTION_CONSTANT: _ClassVar[LoadCombination.ItemsRow.AmplitudeFunction]
            AMPLITUDE_FUNCTION_LINEAR: _ClassVar[LoadCombination.ItemsRow.AmplitudeFunction]
            AMPLITUDE_FUNCTION_QUADRATIC: _ClassVar[LoadCombination.ItemsRow.AmplitudeFunction]
        AMPLITUDE_FUNCTION_CONSTANT: LoadCombination.ItemsRow.AmplitudeFunction
        AMPLITUDE_FUNCTION_LINEAR: LoadCombination.ItemsRow.AmplitudeFunction
        AMPLITUDE_FUNCTION_QUADRATIC: LoadCombination.ItemsRow.AmplitudeFunction
        NO_FIELD_NUMBER: _ClassVar[int]
        DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
        FACTOR_FIELD_NUMBER: _ClassVar[int]
        LOAD_CASE_FIELD_NUMBER: _ClassVar[int]
        ACTION_FIELD_NUMBER: _ClassVar[int]
        IS_LEADING_FIELD_NUMBER: _ClassVar[int]
        GAMMA_FIELD_NUMBER: _ClassVar[int]
        PSI_FIELD_NUMBER: _ClassVar[int]
        XI_FIELD_NUMBER: _ClassVar[int]
        K_FI_FIELD_NUMBER: _ClassVar[int]
        C_ESL_FIELD_NUMBER: _ClassVar[int]
        K_DEF_FIELD_NUMBER: _ClassVar[int]
        PSI_0_FIELD_NUMBER: _ClassVar[int]
        PSI_1_FIELD_NUMBER: _ClassVar[int]
        PSI_2_FIELD_NUMBER: _ClassVar[int]
        FI_FIELD_NUMBER: _ClassVar[int]
        GAMMA_0_FIELD_NUMBER: _ClassVar[int]
        ALFA_FIELD_NUMBER: _ClassVar[int]
        K_F_FIELD_NUMBER: _ClassVar[int]
        PHI_FIELD_NUMBER: _ClassVar[int]
        RHO_FIELD_NUMBER: _ClassVar[int]
        OMEGA_0_FIELD_NUMBER: _ClassVar[int]
        GAMMA_L_1_FIELD_NUMBER: _ClassVar[int]
        K_CREEP_FIELD_NUMBER: _ClassVar[int]
        GAMMA_N_FIELD_NUMBER: _ClassVar[int]
        J_2_FIELD_NUMBER: _ClassVar[int]
        OMEGA_M_FIELD_NUMBER: _ClassVar[int]
        OMEGA_N_FIELD_NUMBER: _ClassVar[int]
        D1_FIELD_NUMBER: _ClassVar[int]
        D2_FIELD_NUMBER: _ClassVar[int]
        SHIFT_FIELD_NUMBER: _ClassVar[int]
        AMPLITUDE_FUNCTION_FIELD_NUMBER: _ClassVar[int]
        TIME_DIAGRAM_FIELD_NUMBER: _ClassVar[int]
        TIME_SLIP_FIELD_NUMBER: _ClassVar[int]
        no: int
        description: str
        factor: float
        load_case: int
        action: int
        is_leading: bool
        gamma: float
        psi: float
        xi: float
        k_fi: float
        c_esl: float
        k_def: float
        psi_0: float
        psi_1: float
        psi_2: float
        fi: float
        gamma_0: float
        alfa: float
        k_f: float
        phi: float
        rho: float
        omega_0: float
        gamma_l_1: float
        k_creep: float
        gamma_n: float
        j_2: float
        omega_m: float
        omega_n: float
        d1: float
        d2: float
        shift: float
        amplitude_function: LoadCombination.ItemsRow.AmplitudeFunction
        time_diagram: int
        time_slip: float
        def __init__(self, no: _Optional[int] = ..., description: _Optional[str] = ..., factor: _Optional[float] = ..., load_case: _Optional[int] = ..., action: _Optional[int] = ..., is_leading: bool = ..., gamma: _Optional[float] = ..., psi: _Optional[float] = ..., xi: _Optional[float] = ..., k_fi: _Optional[float] = ..., c_esl: _Optional[float] = ..., k_def: _Optional[float] = ..., psi_0: _Optional[float] = ..., psi_1: _Optional[float] = ..., psi_2: _Optional[float] = ..., fi: _Optional[float] = ..., gamma_0: _Optional[float] = ..., alfa: _Optional[float] = ..., k_f: _Optional[float] = ..., phi: _Optional[float] = ..., rho: _Optional[float] = ..., omega_0: _Optional[float] = ..., gamma_l_1: _Optional[float] = ..., k_creep: _Optional[float] = ..., gamma_n: _Optional[float] = ..., j_2: _Optional[float] = ..., omega_m: _Optional[float] = ..., omega_n: _Optional[float] = ..., d1: _Optional[float] = ..., d2: _Optional[float] = ..., shift: _Optional[float] = ..., amplitude_function: _Optional[_Union[LoadCombination.ItemsRow.AmplitudeFunction, str]] = ..., time_diagram: _Optional[int] = ..., time_slip: _Optional[float] = ...) -> None: ...
    class IndividualFactorsOfSelectedObjectsTable(_message.Message):
        __slots__ = ("rows",)
        ROWS_FIELD_NUMBER: _ClassVar[int]
        rows: _containers.RepeatedCompositeFieldContainer[LoadCombination.IndividualFactorsOfSelectedObjectsTableRow]
        def __init__(self, rows: _Optional[_Iterable[_Union[LoadCombination.IndividualFactorsOfSelectedObjectsTableRow, _Mapping]]] = ...) -> None: ...
    class IndividualFactorsOfSelectedObjectsTableRow(_message.Message):
        __slots__ = ("no", "description", "object_type", "object_list", "strain", "factor", "comment")
        class ObjectType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = ()
            OBJECT_TYPE_UNKNOWN: _ClassVar[LoadCombination.IndividualFactorsOfSelectedObjectsTableRow.ObjectType]
            OBJECT_TYPE_LINE_HINGE: _ClassVar[LoadCombination.IndividualFactorsOfSelectedObjectsTableRow.ObjectType]
            OBJECT_TYPE_LINE_WITH_SUPPORT: _ClassVar[LoadCombination.IndividualFactorsOfSelectedObjectsTableRow.ObjectType]
            OBJECT_TYPE_MEMBER: _ClassVar[LoadCombination.IndividualFactorsOfSelectedObjectsTableRow.ObjectType]
            OBJECT_TYPE_MEMBER_HINGE: _ClassVar[LoadCombination.IndividualFactorsOfSelectedObjectsTableRow.ObjectType]
            OBJECT_TYPE_NODE_WITH_SUPPORT: _ClassVar[LoadCombination.IndividualFactorsOfSelectedObjectsTableRow.ObjectType]
            OBJECT_TYPE_SOLID: _ClassVar[LoadCombination.IndividualFactorsOfSelectedObjectsTableRow.ObjectType]
            OBJECT_TYPE_SURFACE: _ClassVar[LoadCombination.IndividualFactorsOfSelectedObjectsTableRow.ObjectType]
        OBJECT_TYPE_UNKNOWN: LoadCombination.IndividualFactorsOfSelectedObjectsTableRow.ObjectType
        OBJECT_TYPE_LINE_HINGE: LoadCombination.IndividualFactorsOfSelectedObjectsTableRow.ObjectType
        OBJECT_TYPE_LINE_WITH_SUPPORT: LoadCombination.IndividualFactorsOfSelectedObjectsTableRow.ObjectType
        OBJECT_TYPE_MEMBER: LoadCombination.IndividualFactorsOfSelectedObjectsTableRow.ObjectType
        OBJECT_TYPE_MEMBER_HINGE: LoadCombination.IndividualFactorsOfSelectedObjectsTableRow.ObjectType
        OBJECT_TYPE_NODE_WITH_SUPPORT: LoadCombination.IndividualFactorsOfSelectedObjectsTableRow.ObjectType
        OBJECT_TYPE_SOLID: LoadCombination.IndividualFactorsOfSelectedObjectsTableRow.ObjectType
        OBJECT_TYPE_SURFACE: LoadCombination.IndividualFactorsOfSelectedObjectsTableRow.ObjectType
        class Strain(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = ()
            STRAIN_ALL: _ClassVar[LoadCombination.IndividualFactorsOfSelectedObjectsTableRow.Strain]
            STRAIN_ALONG_X: _ClassVar[LoadCombination.IndividualFactorsOfSelectedObjectsTableRow.Strain]
            STRAIN_ALONG_Y: _ClassVar[LoadCombination.IndividualFactorsOfSelectedObjectsTableRow.Strain]
            STRAIN_ALONG_Z: _ClassVar[LoadCombination.IndividualFactorsOfSelectedObjectsTableRow.Strain]
            STRAIN_AROUND_X: _ClassVar[LoadCombination.IndividualFactorsOfSelectedObjectsTableRow.Strain]
            STRAIN_AROUND_Y: _ClassVar[LoadCombination.IndividualFactorsOfSelectedObjectsTableRow.Strain]
            STRAIN_AROUND_Z: _ClassVar[LoadCombination.IndividualFactorsOfSelectedObjectsTableRow.Strain]
        STRAIN_ALL: LoadCombination.IndividualFactorsOfSelectedObjectsTableRow.Strain
        STRAIN_ALONG_X: LoadCombination.IndividualFactorsOfSelectedObjectsTableRow.Strain
        STRAIN_ALONG_Y: LoadCombination.IndividualFactorsOfSelectedObjectsTableRow.Strain
        STRAIN_ALONG_Z: LoadCombination.IndividualFactorsOfSelectedObjectsTableRow.Strain
        STRAIN_AROUND_X: LoadCombination.IndividualFactorsOfSelectedObjectsTableRow.Strain
        STRAIN_AROUND_Y: LoadCombination.IndividualFactorsOfSelectedObjectsTableRow.Strain
        STRAIN_AROUND_Z: LoadCombination.IndividualFactorsOfSelectedObjectsTableRow.Strain
        NO_FIELD_NUMBER: _ClassVar[int]
        DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
        OBJECT_TYPE_FIELD_NUMBER: _ClassVar[int]
        OBJECT_LIST_FIELD_NUMBER: _ClassVar[int]
        STRAIN_FIELD_NUMBER: _ClassVar[int]
        FACTOR_FIELD_NUMBER: _ClassVar[int]
        COMMENT_FIELD_NUMBER: _ClassVar[int]
        no: int
        description: str
        object_type: LoadCombination.IndividualFactorsOfSelectedObjectsTableRow.ObjectType
        object_list: _containers.RepeatedScalarFieldContainer[int]
        strain: LoadCombination.IndividualFactorsOfSelectedObjectsTableRow.Strain
        factor: float
        comment: str
        def __init__(self, no: _Optional[int] = ..., description: _Optional[str] = ..., object_type: _Optional[_Union[LoadCombination.IndividualFactorsOfSelectedObjectsTableRow.ObjectType, str]] = ..., object_list: _Optional[_Iterable[int]] = ..., strain: _Optional[_Union[LoadCombination.IndividualFactorsOfSelectedObjectsTableRow.Strain, str]] = ..., factor: _Optional[float] = ..., comment: _Optional[str] = ...) -> None: ...
    class CorrespondingLoadCombinationsTable(_message.Message):
        __slots__ = ("rows",)
        ROWS_FIELD_NUMBER: _ClassVar[int]
        rows: _containers.RepeatedCompositeFieldContainer[LoadCombination.CorrespondingLoadCombinationsRow]
        def __init__(self, rows: _Optional[_Iterable[_Union[LoadCombination.CorrespondingLoadCombinationsRow, _Mapping]]] = ...) -> None: ...
    class CorrespondingLoadCombinationsRow(_message.Message):
        __slots__ = ("no", "description", "design_situation", "corresponding_load_combinations")
        NO_FIELD_NUMBER: _ClassVar[int]
        DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
        DESIGN_SITUATION_FIELD_NUMBER: _ClassVar[int]
        CORRESPONDING_LOAD_COMBINATIONS_FIELD_NUMBER: _ClassVar[int]
        no: int
        description: str
        design_situation: int
        corresponding_load_combinations: int
        def __init__(self, no: _Optional[int] = ..., description: _Optional[str] = ..., design_situation: _Optional[int] = ..., corresponding_load_combinations: _Optional[int] = ...) -> None: ...
    NO_FIELD_NUMBER: _ClassVar[int]
    ANALYSIS_TYPE_FIELD_NUMBER: _ClassVar[int]
    ASSOCIATED_STANDARD_FIELD_NUMBER: _ClassVar[int]
    DESIGN_SITUATION_FIELD_NUMBER: _ClassVar[int]
    USER_DEFINED_NAME_ENABLED_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    STATIC_ANALYSIS_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    IMPORT_MODAL_ANALYSIS_LOAD_CASE_FIELD_NUMBER: _ClassVar[int]
    CALCULATE_CRITICAL_LOAD_FIELD_NUMBER: _ClassVar[int]
    STABILITY_ANALYSIS_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    CONSIDER_IMPERFECTION_FIELD_NUMBER: _ClassVar[int]
    IMPERFECTION_CASE_FIELD_NUMBER: _ClassVar[int]
    CONSIDER_INITIAL_STATE_FIELD_NUMBER: _ClassVar[int]
    INITIAL_STATE_CASE_FIELD_NUMBER: _ClassVar[int]
    CONSIDER_CREEP_LOADING_CASE_FIELD_NUMBER: _ClassVar[int]
    CREEP_LOADING_CASE_FIELD_NUMBER: _ClassVar[int]
    IMPORT_ELASTIC_SUPPORT_COEFFICIENTS_FIELD_NUMBER: _ClassVar[int]
    ELASTIC_SUPPORT_COEFFICIENTS_LOADING_FIELD_NUMBER: _ClassVar[int]
    SUSTAINED_LOAD_ENABLED_FIELD_NUMBER: _ClassVar[int]
    SUSTAINED_LOAD_FIELD_NUMBER: _ClassVar[int]
    SWAY_LOAD_ENABLED_FIELD_NUMBER: _ClassVar[int]
    SWAY_LOAD_FIELD_NUMBER: _ClassVar[int]
    STRUCTURE_MODIFICATION_ENABLED_FIELD_NUMBER: _ClassVar[int]
    STRUCTURE_MODIFICATION_FIELD_NUMBER: _ClassVar[int]
    TO_SOLVE_FIELD_NUMBER: _ClassVar[int]
    COMMENT_FIELD_NUMBER: _ClassVar[int]
    LOAD_DURATION_FIELD_NUMBER: _ClassVar[int]
    ITEMS_FIELD_NUMBER: _ClassVar[int]
    COMBINATION_RULE_STR_FIELD_NUMBER: _ClassVar[int]
    LOADING_START_FIELD_NUMBER: _ClassVar[int]
    TIME_BEING_INVESTIGATED_FIELD_NUMBER: _ClassVar[int]
    IS_GENERATED_FIELD_NUMBER: _ClassVar[int]
    GENERATING_OBJECT_INFO_FIELD_NUMBER: _ClassVar[int]
    INITIAL_STATE_DEFINITION_TYPE_FIELD_NUMBER: _ClassVar[int]
    INDIVIDUAL_FACTORS_OF_SELECTED_OBJECTS_TABLE_FIELD_NUMBER: _ClassVar[int]
    PUSHOVER_ANALYSIS_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    PUSHOVER_VERTICAL_LOADS_CASE_FIELD_NUMBER: _ClassVar[int]
    PUSHOVER_MODAL_ANALYSIS_FROM_LOAD_CASE_FIELD_NUMBER: _ClassVar[int]
    PUSHOVER_DIRECTION_FIELD_NUMBER: _ClassVar[int]
    PUSHOVER_NORMALIZED_DISPLACEMENTS_FIELD_NUMBER: _ClassVar[int]
    PUSHOVER_MODE_SHAPE_NUMBER_FIELD_NUMBER: _ClassVar[int]
    PUSHOVER_RESPONSE_SPECTRUM_FIELD_NUMBER: _ClassVar[int]
    PUSHOVER_RESPONSE_SPECTRUM_SCALE_FACTOR_FIELD_NUMBER: _ClassVar[int]
    TIME_HISTORY_ANALYSIS_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    TIME_HISTORY_IMPORT_MASSES_FROM_FIELD_NUMBER: _ClassVar[int]
    CORRESPONDING_LOAD_COMBINATIONS_FIELD_NUMBER: _ClassVar[int]
    ID_FOR_EXPORT_IMPORT_FIELD_NUMBER: _ClassVar[int]
    METADATA_FOR_EXPORT_IMPORT_FIELD_NUMBER: _ClassVar[int]
    no: int
    analysis_type: LoadCombination.AnalysisType
    associated_standard: int
    design_situation: int
    user_defined_name_enabled: bool
    name: str
    static_analysis_settings: int
    import_modal_analysis_load_case: int
    calculate_critical_load: bool
    stability_analysis_settings: int
    consider_imperfection: bool
    imperfection_case: int
    consider_initial_state: bool
    initial_state_case: _object_id_pb2.ObjectId
    consider_creep_loading_case: bool
    creep_loading_case: _object_id_pb2.ObjectId
    import_elastic_support_coefficients: bool
    elastic_support_coefficients_loading: _object_id_pb2.ObjectId
    sustained_load_enabled: bool
    sustained_load: _object_id_pb2.ObjectId
    sway_load_enabled: bool
    sway_load: _object_id_pb2.ObjectId
    structure_modification_enabled: bool
    structure_modification: int
    to_solve: bool
    comment: str
    load_duration: LoadCombination.LoadDuration
    items: LoadCombination.ItemsTable
    combination_rule_str: str
    loading_start: float
    time_being_investigated: float
    is_generated: bool
    generating_object_info: str
    initial_state_definition_type: LoadCombination.InitialStateDefinitionType
    individual_factors_of_selected_objects_table: LoadCombination.IndividualFactorsOfSelectedObjectsTable
    pushover_analysis_settings: int
    pushover_vertical_loads_case: _object_id_pb2.ObjectId
    pushover_modal_analysis_from_load_case: int
    pushover_direction: LoadCombination.PushoverDirection
    pushover_normalized_displacements: LoadCombination.PushoverNormalizedDisplacements
    pushover_mode_shape_number: int
    pushover_response_spectrum: int
    pushover_response_spectrum_scale_factor: float
    time_history_analysis_settings: int
    time_history_import_masses_from: _object_id_pb2.ObjectId
    corresponding_load_combinations: LoadCombination.CorrespondingLoadCombinationsTable
    id_for_export_import: str
    metadata_for_export_import: str
    def __init__(self, no: _Optional[int] = ..., analysis_type: _Optional[_Union[LoadCombination.AnalysisType, str]] = ..., associated_standard: _Optional[int] = ..., design_situation: _Optional[int] = ..., user_defined_name_enabled: bool = ..., name: _Optional[str] = ..., static_analysis_settings: _Optional[int] = ..., import_modal_analysis_load_case: _Optional[int] = ..., calculate_critical_load: bool = ..., stability_analysis_settings: _Optional[int] = ..., consider_imperfection: bool = ..., imperfection_case: _Optional[int] = ..., consider_initial_state: bool = ..., initial_state_case: _Optional[_Union[_object_id_pb2.ObjectId, _Mapping]] = ..., consider_creep_loading_case: bool = ..., creep_loading_case: _Optional[_Union[_object_id_pb2.ObjectId, _Mapping]] = ..., import_elastic_support_coefficients: bool = ..., elastic_support_coefficients_loading: _Optional[_Union[_object_id_pb2.ObjectId, _Mapping]] = ..., sustained_load_enabled: bool = ..., sustained_load: _Optional[_Union[_object_id_pb2.ObjectId, _Mapping]] = ..., sway_load_enabled: bool = ..., sway_load: _Optional[_Union[_object_id_pb2.ObjectId, _Mapping]] = ..., structure_modification_enabled: bool = ..., structure_modification: _Optional[int] = ..., to_solve: bool = ..., comment: _Optional[str] = ..., load_duration: _Optional[_Union[LoadCombination.LoadDuration, str]] = ..., items: _Optional[_Union[LoadCombination.ItemsTable, _Mapping]] = ..., combination_rule_str: _Optional[str] = ..., loading_start: _Optional[float] = ..., time_being_investigated: _Optional[float] = ..., is_generated: bool = ..., generating_object_info: _Optional[str] = ..., initial_state_definition_type: _Optional[_Union[LoadCombination.InitialStateDefinitionType, str]] = ..., individual_factors_of_selected_objects_table: _Optional[_Union[LoadCombination.IndividualFactorsOfSelectedObjectsTable, _Mapping]] = ..., pushover_analysis_settings: _Optional[int] = ..., pushover_vertical_loads_case: _Optional[_Union[_object_id_pb2.ObjectId, _Mapping]] = ..., pushover_modal_analysis_from_load_case: _Optional[int] = ..., pushover_direction: _Optional[_Union[LoadCombination.PushoverDirection, str]] = ..., pushover_normalized_displacements: _Optional[_Union[LoadCombination.PushoverNormalizedDisplacements, str]] = ..., pushover_mode_shape_number: _Optional[int] = ..., pushover_response_spectrum: _Optional[int] = ..., pushover_response_spectrum_scale_factor: _Optional[float] = ..., time_history_analysis_settings: _Optional[int] = ..., time_history_import_masses_from: _Optional[_Union[_object_id_pb2.ObjectId, _Mapping]] = ..., corresponding_load_combinations: _Optional[_Union[LoadCombination.CorrespondingLoadCombinationsTable, _Mapping]] = ..., id_for_export_import: _Optional[str] = ..., metadata_for_export_import: _Optional[str] = ...) -> None: ...
