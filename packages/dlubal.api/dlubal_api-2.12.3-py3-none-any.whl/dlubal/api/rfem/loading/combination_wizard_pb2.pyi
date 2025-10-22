from dlubal.api.rfem import object_id_pb2 as _object_id_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class CombinationWizard(_message.Message):
    __slots__ = ("no", "user_defined_name_enabled", "name", "associated_standard", "static_analysis_settings", "generate_combinations", "has_stability_analysis", "stability_analysis_settings", "consider_imperfection_case", "generate_same_CO_without_IC", "user_defined_action_combinations", "favorable_permanent_actions", "reduce_number_of_generated_combinations", "auxiliary_combinations", "generate_subcombinations_of_type_superposition", "generate_as_permanent_superposition", "import_elastic_support_coefficients", "import_elastic_support_coefficients_from", "elastic_support_coefficients_loading", "elastic_support_coefficients_design_situation", "consider_initial_state", "generate_co_without_initial_state", "initial_state_items", "structure_modification_enabled", "structure_modification", "comment", "id_for_export_import", "metadata_for_export_import")
    class GenerateCombinations(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        GENERATE_COMBINATIONS_LOAD_COMBINATIONS: _ClassVar[CombinationWizard.GenerateCombinations]
        GENERATE_COMBINATIONS_RESULT_COMBINATIONS: _ClassVar[CombinationWizard.GenerateCombinations]
    GENERATE_COMBINATIONS_LOAD_COMBINATIONS: CombinationWizard.GenerateCombinations
    GENERATE_COMBINATIONS_RESULT_COMBINATIONS: CombinationWizard.GenerateCombinations
    class ImportElasticSupportCoefficientsFrom(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        IMPORT_ELASTIC_SUPPORT_COEFFICIENTS_FROM_LOADING: _ClassVar[CombinationWizard.ImportElasticSupportCoefficientsFrom]
        IMPORT_ELASTIC_SUPPORT_COEFFICIENTS_FROM_DESIGN_SITUATION: _ClassVar[CombinationWizard.ImportElasticSupportCoefficientsFrom]
    IMPORT_ELASTIC_SUPPORT_COEFFICIENTS_FROM_LOADING: CombinationWizard.ImportElasticSupportCoefficientsFrom
    IMPORT_ELASTIC_SUPPORT_COEFFICIENTS_FROM_DESIGN_SITUATION: CombinationWizard.ImportElasticSupportCoefficientsFrom
    class InitialStateItemsTable(_message.Message):
        __slots__ = ("rows",)
        ROWS_FIELD_NUMBER: _ClassVar[int]
        rows: _containers.RepeatedCompositeFieldContainer[CombinationWizard.InitialStateItemsRow]
        def __init__(self, rows: _Optional[_Iterable[_Union[CombinationWizard.InitialStateItemsRow, _Mapping]]] = ...) -> None: ...
    class InitialStateItemsRow(_message.Message):
        __slots__ = ("no", "description", "case_object", "definition_type")
        class DefinitionType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = ()
            DEFINITION_TYPE_FINAL_STATE: _ClassVar[CombinationWizard.InitialStateItemsRow.DefinitionType]
            DEFINITION_TYPE_STIFFNESS: _ClassVar[CombinationWizard.InitialStateItemsRow.DefinitionType]
            DEFINITION_TYPE_STRAINS: _ClassVar[CombinationWizard.InitialStateItemsRow.DefinitionType]
            DEFINITION_TYPE_STRAINS_WITH_USER_DEFINED_FACTORS: _ClassVar[CombinationWizard.InitialStateItemsRow.DefinitionType]
        DEFINITION_TYPE_FINAL_STATE: CombinationWizard.InitialStateItemsRow.DefinitionType
        DEFINITION_TYPE_STIFFNESS: CombinationWizard.InitialStateItemsRow.DefinitionType
        DEFINITION_TYPE_STRAINS: CombinationWizard.InitialStateItemsRow.DefinitionType
        DEFINITION_TYPE_STRAINS_WITH_USER_DEFINED_FACTORS: CombinationWizard.InitialStateItemsRow.DefinitionType
        NO_FIELD_NUMBER: _ClassVar[int]
        DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
        CASE_OBJECT_FIELD_NUMBER: _ClassVar[int]
        DEFINITION_TYPE_FIELD_NUMBER: _ClassVar[int]
        no: int
        description: str
        case_object: _object_id_pb2.ObjectId
        definition_type: CombinationWizard.InitialStateItemsRow.DefinitionType
        def __init__(self, no: _Optional[int] = ..., description: _Optional[str] = ..., case_object: _Optional[_Union[_object_id_pb2.ObjectId, _Mapping]] = ..., definition_type: _Optional[_Union[CombinationWizard.InitialStateItemsRow.DefinitionType, str]] = ...) -> None: ...
    NO_FIELD_NUMBER: _ClassVar[int]
    USER_DEFINED_NAME_ENABLED_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    ASSOCIATED_STANDARD_FIELD_NUMBER: _ClassVar[int]
    STATIC_ANALYSIS_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    GENERATE_COMBINATIONS_FIELD_NUMBER: _ClassVar[int]
    HAS_STABILITY_ANALYSIS_FIELD_NUMBER: _ClassVar[int]
    STABILITY_ANALYSIS_SETTINGS_FIELD_NUMBER: _ClassVar[int]
    CONSIDER_IMPERFECTION_CASE_FIELD_NUMBER: _ClassVar[int]
    GENERATE_SAME_CO_WITHOUT_IC_FIELD_NUMBER: _ClassVar[int]
    USER_DEFINED_ACTION_COMBINATIONS_FIELD_NUMBER: _ClassVar[int]
    FAVORABLE_PERMANENT_ACTIONS_FIELD_NUMBER: _ClassVar[int]
    REDUCE_NUMBER_OF_GENERATED_COMBINATIONS_FIELD_NUMBER: _ClassVar[int]
    AUXILIARY_COMBINATIONS_FIELD_NUMBER: _ClassVar[int]
    GENERATE_SUBCOMBINATIONS_OF_TYPE_SUPERPOSITION_FIELD_NUMBER: _ClassVar[int]
    GENERATE_AS_PERMANENT_SUPERPOSITION_FIELD_NUMBER: _ClassVar[int]
    IMPORT_ELASTIC_SUPPORT_COEFFICIENTS_FIELD_NUMBER: _ClassVar[int]
    IMPORT_ELASTIC_SUPPORT_COEFFICIENTS_FROM_FIELD_NUMBER: _ClassVar[int]
    ELASTIC_SUPPORT_COEFFICIENTS_LOADING_FIELD_NUMBER: _ClassVar[int]
    ELASTIC_SUPPORT_COEFFICIENTS_DESIGN_SITUATION_FIELD_NUMBER: _ClassVar[int]
    CONSIDER_INITIAL_STATE_FIELD_NUMBER: _ClassVar[int]
    GENERATE_CO_WITHOUT_INITIAL_STATE_FIELD_NUMBER: _ClassVar[int]
    INITIAL_STATE_ITEMS_FIELD_NUMBER: _ClassVar[int]
    STRUCTURE_MODIFICATION_ENABLED_FIELD_NUMBER: _ClassVar[int]
    STRUCTURE_MODIFICATION_FIELD_NUMBER: _ClassVar[int]
    COMMENT_FIELD_NUMBER: _ClassVar[int]
    ID_FOR_EXPORT_IMPORT_FIELD_NUMBER: _ClassVar[int]
    METADATA_FOR_EXPORT_IMPORT_FIELD_NUMBER: _ClassVar[int]
    no: int
    user_defined_name_enabled: bool
    name: str
    associated_standard: int
    static_analysis_settings: int
    generate_combinations: CombinationWizard.GenerateCombinations
    has_stability_analysis: bool
    stability_analysis_settings: int
    consider_imperfection_case: bool
    generate_same_CO_without_IC: bool
    user_defined_action_combinations: bool
    favorable_permanent_actions: bool
    reduce_number_of_generated_combinations: bool
    auxiliary_combinations: bool
    generate_subcombinations_of_type_superposition: bool
    generate_as_permanent_superposition: bool
    import_elastic_support_coefficients: bool
    import_elastic_support_coefficients_from: CombinationWizard.ImportElasticSupportCoefficientsFrom
    elastic_support_coefficients_loading: _object_id_pb2.ObjectId
    elastic_support_coefficients_design_situation: int
    consider_initial_state: bool
    generate_co_without_initial_state: bool
    initial_state_items: CombinationWizard.InitialStateItemsTable
    structure_modification_enabled: bool
    structure_modification: int
    comment: str
    id_for_export_import: str
    metadata_for_export_import: str
    def __init__(self, no: _Optional[int] = ..., user_defined_name_enabled: bool = ..., name: _Optional[str] = ..., associated_standard: _Optional[int] = ..., static_analysis_settings: _Optional[int] = ..., generate_combinations: _Optional[_Union[CombinationWizard.GenerateCombinations, str]] = ..., has_stability_analysis: bool = ..., stability_analysis_settings: _Optional[int] = ..., consider_imperfection_case: bool = ..., generate_same_CO_without_IC: bool = ..., user_defined_action_combinations: bool = ..., favorable_permanent_actions: bool = ..., reduce_number_of_generated_combinations: bool = ..., auxiliary_combinations: bool = ..., generate_subcombinations_of_type_superposition: bool = ..., generate_as_permanent_superposition: bool = ..., import_elastic_support_coefficients: bool = ..., import_elastic_support_coefficients_from: _Optional[_Union[CombinationWizard.ImportElasticSupportCoefficientsFrom, str]] = ..., elastic_support_coefficients_loading: _Optional[_Union[_object_id_pb2.ObjectId, _Mapping]] = ..., elastic_support_coefficients_design_situation: _Optional[int] = ..., consider_initial_state: bool = ..., generate_co_without_initial_state: bool = ..., initial_state_items: _Optional[_Union[CombinationWizard.InitialStateItemsTable, _Mapping]] = ..., structure_modification_enabled: bool = ..., structure_modification: _Optional[int] = ..., comment: _Optional[str] = ..., id_for_export_import: _Optional[str] = ..., metadata_for_export_import: _Optional[str] = ...) -> None: ...
