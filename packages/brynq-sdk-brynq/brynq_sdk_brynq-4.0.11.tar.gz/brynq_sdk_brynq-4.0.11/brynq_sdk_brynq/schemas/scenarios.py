from collections import defaultdict
from datetime import date
from typing import Any, Dict, List, Literal, Optional, Set, Tuple, Type, Union

from pydantic import BaseModel, ConfigDict, Field
from typing_extensions import Annotated


# data level models
class MappingValue(BaseModel):
    """Represents a single input-to-output mapping rule."""
    input: Dict[str, str]
    output: Dict[str, str]

    class Config:
        frozen = True
        strict = True
        populate_by_name = True

class CustomData(BaseModel):
    uuid: str = Field(..., description="Stable identifier for the custom field")
    name: str = Field(..., description="Human-readable field name")
    technical_name: str = Field(
        ...,
        alias="technicalName",
        description="Canonical identifier used in the source system"
    )
    source: str = Field(..., description="Source category bucket")
    description: str = Field(..., description="Business description / purpose")

    class Config:
        frozen = True
        strict = True
        populate_by_name = True

# Field scale models (Source/Target branches models)
class CustomSourceTarget(BaseModel):
    type: Literal["CUSTOM"] = Field(
        "CUSTOM",
        description="Discriminator—always 'CUSTOM' for this branch"
    )
    data: List[CustomData] = Field(
        ...,
        description="List of rich field descriptors coming from an external system"
    )

    class Config:
        frozen = True
        strict = True
        populate_by_name = True


class LibraryFieldDescriptor(BaseModel):
    """Rich metadata describing a library field target."""
    id: Optional[int] = None
    uuid: Optional[str] = None
    required: Optional[bool] = None
    field: Optional[str] = None
    field_label: Optional[Dict[str, str]] = Field(default=None, alias="fieldLabel")
    app_id: Optional[int] = Field(default=None, alias="appId")
    category: Optional[Dict[str, Any]] = None

    class Config:
        frozen = True
        strict = True
        populate_by_name = True


class LibrarySourceTarget(BaseModel):
    type: Literal["LIBRARY"] = Field(
        "LIBRARY",
        description="Discriminator—fixed value for library look-ups"
    )
    data: List[Union[str, LibraryFieldDescriptor]] = Field(
        ...,
        description="List of library field identifiers or metadata objects"
    )

    class Config:
        frozen = True
        strict = True
        populate_by_name = True


class FixedSourceTarget(BaseModel):
    type: Literal["FIXED"] = Field(
        "FIXED",
        description="Discriminator—fixed value for constant/literal values"
    )
    data: str = Field(
        ...,
        description="A fixed literal value (e.g., '082')"
    )

    class Config:
        frozen = True
        strict = True
        populate_by_name = True

SourceTarget = Annotated[
    Union[CustomSourceTarget, LibrarySourceTarget, FixedSourceTarget],
    Field(discriminator="type", description="Polymorphic source/target contract"),
]

# Field scale models (Field properties)
class FieldProperties(BaseModel):
    """Metadata for a single field‑mapping detail returned by the API."""
    model_config = ConfigDict(extra="allow", frozen=True)
    logic: Optional[str] = None
    unique: bool = False
    required: bool = False
    mapping: Dict[str, Any] = Field(default_factory=dict)
    system_type: Optional[str] = None  # "source" or "target"


# Down-stream models (from scenario to field, nested in scenario detail)
class ScenarioMappingConfiguration(BaseModel):
    # The type hint for 'values' is updated to use the new MappingValue model
    values: List[MappingValue] = Field(
        default_factory=list,
        description="Explicit mapping values when value mapping is required"
    )
    default_value: str = Field(
        default="",
        alias="defaultValue",
        description="Fallback value applied when no mapping match is found"
    )

    class Config:
        frozen = True
        strict = True
        populate_by_name = True

class ScenarioDetail(BaseModel):
    id: str = Field(..., description="Primary key of the detail record")
    logic: str = Field(default="", description="Optional transformation logic")
    unique: Optional[bool] = Field(default=False, description="Must this mapping be unique across the scenario?")
    required: Optional[bool] = Field(default=False, description="Is the field mandatory?")
    mapping_required: Optional[bool] = Field(
    default=False,
    alias="mappingRequired",
    description="Flag indicating whether an explicit mapping table is needed, right now not always present in reponse so defaults to False."
  )

    source: SourceTarget = Field(..., description="Source definition")
    target: SourceTarget = Field(..., description="Target definition")
    mapping: Optional[ScenarioMappingConfiguration] = Field(
        default=None,
        description="Mapping/value-translation configuration (may be absent)"
    )

    class Config:
        frozen = True
        strict = True
        populate_by_name = True

# Scenario models
class Scenario(BaseModel):
    id: str = Field(..., description="Scenario identifier")
    name: str = Field(..., description="Scenario display name")
    description: str = Field(default="", description="Scenario business context")
    details: List[ScenarioDetail] = Field(
        ..., description="Collection of field-level mappings"
    )

    class Config:
        frozen = True
        strict = True
        populate_by_name = True

class ParsedScenario(BaseModel):
    """
    Create object that contains all the information about a scenario that is returned by the API.
    This object is used to access the scenario data in a pythonic and flexible way.
    """
    # Core attributes
    name: str
    id: str
    details_count: int

    # Derived mappings
    source_to_target_map: Dict[str, List[str]]
    target_to_source_map: Dict[str, List[str]]
    field_properties: Dict[str, FieldProperties]
    all_source_fields: Set[str]
    all_target_fields: Set[str]
    unique_fields: List[str]
    required_fields: List[str]


    alias_to_pythonic: Optional[Dict[str, str]] = None
    pythonic_to_alias: Optional[Dict[str, str]] = None
    all_pythonic_source_fields: Optional[List[str]] = None
    source_pythonic_to_target: Optional[Dict[str, List[str]]] = None
    target_to_source_pythonic: Optional[Dict[str, Union[str, List[str]]]] = None

    # Direct lookup for value mappings from a source field
    source_to_value_mappings: Dict[str, List[ScenarioMappingConfiguration]]

    #public methods with specific functionality
    def get_mapped_field_names(self, field_name: str, direction: str = "source_to_target") -> List[str]:
        """
        Return all mapped fields for `field_name` based on the mapping `direction`.

        Args:
            field_name: The name of the field to look up.
            direction: Can be "source_to_target" (default) or "target_to_source".

        Returns:
            A list of mapped field names.
        """
        if direction == "source_to_target":
            return self.source_to_target_map.get(field_name, [])
        if direction == "target_to_source":
            return self.target_to_source_map.get(field_name, [])
        raise ValueError("Direction must be 'source_to_target' or 'target_to_source'.")

    def get_value_mappings(self, source_field_name: str) -> List[ScenarioMappingConfiguration]:
        """
        Return all value mapping configurations for a given source field.
        """
        return self.source_to_value_mappings.get(source_field_name, [])

    def get_source_fields_with_value_mappings(self) -> List[str]:
        """Returns a list of source fields that have value mappings."""
        return list(self.source_to_value_mappings.keys())

    def has_field(self, field_name: str, field_type: Optional[str] = None) -> bool:
        """Check field existence in scenario. Can denote source or target, else looks for both."""
        if field_type == "source":
            return field_name in self.all_source_fields
        if field_type == "target":
            return field_name in self.all_target_fields
        return field_name in self.all_source_fields or field_name in self.all_target_fields

    #Dunder methods for pythonic field access
    def __getitem__(self, field_id: str) -> FieldProperties:
        """Enable dict-style access to field properties: `scenario['customer_id']`."""
        try:
            return self.field_properties[field_id]
        except KeyError as exc:
            raise KeyError(f"Field '{field_id}' not found in scenario '{self.name}'.") from exc

    def __getattr__(self, name: str) -> FieldProperties:
        """Enable attribute-style access to field properties: `scenario.customer_id.unique`."""
        if name.startswith("_") or name in self.__dict__ or name in self.__class__.__dict__:
            return super().__getattribute__(name)
        try:
            return self.field_properties[name]
        except KeyError as exc:
            raise AttributeError(f"'{name}' is not a valid field in scenario '{self.name}'.") from exc

    def __repr__(self) -> str:
        """A human-friendly string representation."""
        return (
            f"<ParsedScenario name='{self.name}' id='{self.id}' "
            f"details={self.details_count} unique={len(self.unique_fields)} required={len(self.required_fields)}>"
        )

    @classmethod
    def from_api_dict(cls, scenario: Dict[str, Any], source_sdk: Any, sdk_mapping_config: Any, temp_scenario_column_fix: Dict[str, str]=None, source_field_remove_prefix: Optional[Dict[str, str]]=None) -> "ParsedScenario":
        """
        Factory method to transform raw API scenario data into a ParsedScenario object.

        This method processes the raw scenario dictionary from the API and:
        - Extracts field mappings from scenario details
        - Builds bidirectional source-to-target and target-to-source mapping dictionaries
        - Creates field properties for each field with metadata (unique, required, logic, etc.)
        - Identifies all source and target fields
        - Categorizes fields by their properties (unique, required)

        Args:
            scenario (Dict[str, Any]): Raw scenario dictionary from the BrynQ API containing
                                     'name', 'id', 'details' and other scenario metadata.

        Returns:
            ParsedScenario: A fully parsed scenario object with convenient access methods
                          for field mappings, properties, and validation capabilities.
        """
        details = scenario.get("details", [])
        src_map: Dict[str, Set[str]] = defaultdict(set)
        tgt_map: Dict[str, Set[str]] = defaultdict(set)
        props: Dict[str, FieldProperties] = {}
        source_to_value_maps: Dict[str, List[ScenarioMappingConfiguration]] = defaultdict(list)

        def _extract_names_from_branch(branch: SourceTarget) -> Set[str]:
            """Normalise source/target branch data into canonical field names."""
            if isinstance(branch, CustomSourceTarget):
                names = {item.technical_name for item in branch.data if item.technical_name}
                if names:
                    return names
                return {item.uuid for item in branch.data if getattr(item, "uuid", None)}
            if isinstance(branch, LibrarySourceTarget):
                names: Set[str] = set()
                for entry in branch.data:
                    if isinstance(entry, str):
                        names.add(entry)
                    else:
                        if entry.field:
                            names.add(entry.field)
                        elif entry.uuid:
                            names.add(entry.uuid)
                return names
            if isinstance(branch, FixedSourceTarget):
                return set()
            return set()

        for detail in details:
            detail_model = ScenarioDetail.model_validate(detail)

            source_names = _extract_names_from_branch(detail_model.source)
            target_names = _extract_names_from_branch(detail_model.target)

            for s_name in source_names:
                src_map[s_name].update(target_names)
            for t_name in target_names:
                tgt_map[t_name].update(source_names)

            mapping_config = detail_model.mapping
            if mapping_config and mapping_config.values:
                key = '|'.join(sorted(source_names)) if source_names else detail_model.id
                source_to_value_maps[key].append(mapping_config)

            base_props = FieldProperties.model_validate(detail)

            # Create source field properties
            for field_name in source_names:
                source_props = base_props.model_copy(update={"system_type": "source"})
                props[field_name] = source_props

            # Create target field properties
            for field_name in target_names:
                target_props = base_props.model_copy(update={"system_type": "target"})
                props[field_name] = target_props

        all_source_fields = set(src_map.keys())
        unique_fields = [fid for fid, props in props.items() if props.unique]
        required_fields = [fid for fid, props in props.items() if props.required]
        source_to_target_map = {k: sorted(v) for k, v in src_map.items()}
        target_to_source_map = {k: sorted(v) for k, v in tgt_map.items()}
        all_target_fields = set(tgt_map.keys())

        #_--- 2. Conditionally generate the alias mappings ---
        alias_to_pythonic = None
        source_pythonic_to_target = None
        target_to_source_pythonic = None
        all_pythonic_source_fields = None

        if source_sdk and sdk_mapping_config:
            alias_to_pythonic = cls._generate_sdk_alias_mappings(
                scenario_name=scenario.get("name", "Unnamed"),
                source_fields=all_source_fields,
                source_sdk=source_sdk,
                sdk_mapping_config=sdk_mapping_config,
                temp_scenario_column_fix=temp_scenario_column_fix,
                source_field_remove_prefix=source_field_remove_prefix
            )
            source_pythonic_to_target = {}
            for k, v in source_to_target_map.items():
                pythonic_name = alias_to_pythonic.get(k)
                if pythonic_name:
                    source_pythonic_to_target[pythonic_name] = v

            # Add custom fields that have target mappings but no pythonic mapping
            for source_alias, target_fields in source_to_target_map.items():
                if source_alias not in alias_to_pythonic and target_fields:  # non-empty list of targets
                    # Use the source alias as the key (since there's no pythonic name)
                    source_pythonic_to_target[source_alias] = target_fields

            #add reverse mapping - handle lists by creating multiple entries
            target_to_source_pythonic = {}
            for source_key, target_list in source_pythonic_to_target.items():
                if isinstance(target_list, list):
                    for target in target_list:
                        target_to_source_pythonic[target] = source_key
                else:
                    target_to_source_pythonic[target_list] = source_key

            all_pythonic_source_fields = list(set(source_pythonic_to_target.keys())) if source_pythonic_to_target else None


        # --- 3. Construct the final, frozen instance in a single call ---
        instance = cls(
            name=scenario.get("name", "Unnamed"),
            id=scenario.get("id", ""),
            details_count=len(details),
            source_to_target_map=source_to_target_map,
            target_to_source_map=target_to_source_map,
            field_properties=props,
            unique_fields=unique_fields,
            required_fields=required_fields,
            all_source_fields=all_source_fields,
            all_pythonic_source_fields=all_pythonic_source_fields,
            all_target_fields=all_target_fields,
            source_to_value_mappings=dict(source_to_value_maps),
            alias_to_pythonic=alias_to_pythonic,
            source_pythonic_to_target=source_pythonic_to_target,
            target_to_source_pythonic=target_to_source_pythonic,
            pythonic_to_alias={v: k for k, v in alias_to_pythonic.items()} if alias_to_pythonic else None
        )
        return instance

    @staticmethod
    def _generate_sdk_alias_mappings(
        scenario_name: str,
        source_fields: Set[str],
        source_sdk: Any,
        sdk_mapping_config: Dict,
        temp_scenario_column_fix: Optional[Dict] = None,
        source_field_remove_prefix: Optional[Dict[str, str]] = None
    ) -> Tuple[List[str], Dict[str, str]]:
        """
        Performs a strict validation of source fields against source SDK schemas.
        This static method is a self-contained helper for the factory.
        """
        fixes = (temp_scenario_column_fix or {}).get(scenario_name, {})
        fields_to_check = [fixes.get(f, f) for f in source_fields]

        # get schema classes and extract pythonic mappings
        source_schema_fields = []
        source_alias_to_pythonic = {}

        mapping = sdk_mapping_config.get(scenario_name)
        if mapping is None:
            raise ValueError(f"No SDK mapping found for scenario '{scenario_name}'")
        if isinstance(mapping, str):
            schema_classes = [mapping]
        elif isinstance(mapping, list):
            schema_classes = mapping
        elif isinstance(mapping, dict) and 'tables' in mapping:
            schema_classes = mapping['tables']
        else:
            raise ValueError(f"Invalid SDK mapping format for scenario '{scenario_name}': {mapping}")

        for schema_class_name in schema_classes:
            sdk_attr_name = schema_class_name.replace('Schema', '').lower() # e.g. 'people' from PeopleSchema
            clss = getattr(source_sdk, sdk_attr_name)
            schema_clss = clss.schema
            schema_vars = vars(schema_clss)
            #Loop over the schema class attributes
            for pythonic_field_name, field_info in schema_vars.items():
                if hasattr(field_info, '__class__') and 'FieldInfo' in field_info.__class__.__name__:
                    # Extract alias from FieldInfo object
                    alias = str(field_info).split('"')[1]  # Get the string between quotes
                    source_schema_fields.append(alias)
                    source_alias_to_pythonic[alias] = pythonic_field_name

        return source_alias_to_pythonic
    class Config:
        frozen = True
        strict = True
        populate_by_name = True
