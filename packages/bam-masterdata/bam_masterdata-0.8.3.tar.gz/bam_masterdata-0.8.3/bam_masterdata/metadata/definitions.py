import datetime
import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from bam_masterdata.utils import code_to_class_name


class DataType(str, Enum):
    """Enumeration of the data types available in openBIS."""

    BOOLEAN = "BOOLEAN"
    CONTROLLEDVOCABULARY = "CONTROLLEDVOCABULARY"
    DATE = "DATE"
    HYPERLINK = "HYPERLINK"
    INTEGER = "INTEGER"
    # MATERIAL = "MATERIAL"  # ! deprecated
    MULTILINE_VARCHAR = "MULTILINE_VARCHAR"
    OBJECT = "OBJECT"
    SAMPLE = "SAMPLE"
    REAL = "REAL"
    TIMESTAMP = "TIMESTAMP"
    VARCHAR = "VARCHAR"
    XML = "XML"

    @property
    def pytype(self) -> type:
        """
        Maps the openBIS data type to its corresponding Python type.

        Returns:
            type: The native Python type of the openBIS data type.
        """
        # TODO check the other data types
        mapping = {
            "BOOLEAN": bool,
            # 'CONTROLLEDVOCABULARY': ,
            "DATE": datetime.date,
            "HYPERLINK": str,
            "INTEGER": int,
            "MULTILINE_VARCHAR": str,
            # 'OBJECT': ,
            "REAL": float,
            "TIMESTAMP": datetime.datetime,
            "VARCHAR": str,
            # 'XML': ,
        }
        return mapping.get(self, None)


class EntityDef(BaseModel):
    """
    Abstract base class for all masterdata entity definitions. The entity definitions are immutable properties.
    This class provides a common interface (with common attributes like `code` and
    `description`.) for all entity definitions.
    """

    code: str = Field(
        ...,
        description="""
        Code string identifying the entity with an openBIS inventory definition. Note that:

        - Must be uppercase and separated by underscores, e.g. `'EXPERIMENTAL_STEP'`.
        - If the entity is native to openBIS, the code must start with a dollar sign, e.g. `'$NAME'`.
        - In the case of inheritance, it needs to be separated by dots, e.g. `'WELDING_EQUIPMENT.INSTRUMENT'`.
        """,
    )

    description: str = Field(
        ...,
        description="""
        Description of the entity. This is the human-readable text for the object and must be
        as complete and concise as possible. The German description can be added after the English
        description separated by a double slash (//), e.g. `'Chemical Substance//Chemische Substanz'`.
        """,
    )

    # TODO: check if it is necessary to add something like `ontology_annotation_id` in the future
    iri: str | None = Field(
        default=None,
        description="""
        IRI (Internationalized Resource Identifier) of the entity. This is a unique identifier for the entity
        and is used to link the entity to an ontology. It is a string with the format `"<ontology_id>:<ontology_version>"`.
        Example: "http://purl.obolibrary.org/bam-masterdata/Instrument:1.0.0".
        """,
    )

    id: str | None = Field(
        default=None,
        description="""
        Identifier of the entity defined as the class name and used to serialize the entity definitions
        in other formats.
        """,
    )

    row_location: str | None = Field(
        default=None,
        description="""
        Row in the Excel at which the entity type field is defined. It is a string with the format `"<row-letter><row_number>"`.
        Example: "A1" ot "A107". This field is useful when checking the consistency of Excel files with multiple entity
        types defined to quickly locate the specific Excel cell which logs a message when applying the `checker` CLI.
        """,
    )

    # TODO check ontology_id, ontology_version, ontology_annotation_id, internal (found in the openBIS docu)

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        if not value or not re.match(r"^[\w_\$\.\-\+]+$", value):
            raise ValueError(
                "`code` must follow the rules specified in the description: 1) Must be uppercase, "
                "2) separated by underscores, 3) start with a dollar sign if native to openBIS, "
                "4) separated by dots if there is inheritance."
            )
        return value

    @field_validator("iri")
    @classmethod
    def validate_iri(cls, value: str | None) -> str | None:
        if not value:
            return value
        if not re.match(
            r"^http://purl.obolibrary.org/bam-masterdata/[\w_]+:[\d.]+$", value
        ):
            raise ValueError(
                "`iri` must follow the rules specified in the description: 1) Must start with 'http://purl.obolibrary.org/bam-masterdata/', "
                "2) followed by the entity name, 3) separated by a colon, 4) followed by the semantic versioning number. "
                "Example: 'http://purl.obolibrary.org/bam-masterdata/Instrument:1.0.0'."
            )
        return value

    @field_validator("description")
    @classmethod
    def strip_description(cls, value: str) -> str:
        return value.strip()

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @property
    def excel_name(self) -> str:
        """
        Returns the name of the entity in a format suitable for the openBIS Excel file.
        """
        name_map = {
            "CollectionTypeDef": "EXPERIMENT_TYPE",
            "DatasetTypeDef": "DATASET_TYPE",
            "ObjectTypeDef": "SAMPLE_TYPE",
            "VocabularyTypeDef": "VOCABULARY_TYPE",
        }
        return name_map.get(self.name)

    @property
    def excel_headers_map(self) -> dict:
        """
        Maps the field keys of the Pydantic model into the openBIS Excel style headers.
        """
        fields = [
            k
            for k in self.model_fields.keys()
            if k not in ["iri", "id", "row_location"]
        ]
        headers: dict = {}
        for f in fields:
            headers[f] = f.replace("_", " ").capitalize()
        return headers

    @model_validator(mode="after")
    @classmethod
    def model_id(cls, data: Any) -> Any:
        """
        Stores the model `id` as the class name from the `code` field.

        Args:
            data (Any): The data containing the fields values to validate.

        Returns:
            Any: The data with the validated fields.
        """
        if "PropertyType" in data.name:
            data.id = code_to_class_name(code=data.code, entity_type="property")
        else:
            data.id = code_to_class_name(code=data.code, entity_type="object")
        return data


class BaseObjectTypeDef(EntityDef):
    """
    Definition class used for the common fields for `CollectionTypeDef`, `ObjectTypeDef`, and `DatasetTypeDef`.
    It adds the fields of `validation_script`.
    """

    validation_script: str | None = Field(
        default=None,
        description="""
        Script written in Jython used to validate the object type.
        """,
    )


class CollectionTypeDef(BaseObjectTypeDef):
    """
    Definition class for a collection type. E.g.:

    ```python
    class DefaultExperiment(BaseModel):
        defs = CollectionTypeDef(
            code='DEFAULT_EXPERIMENT',
            description='...',
            validation_script='DEFAULT_EXPERIMENT.date_range_validation',
        )
    ```
    """

    pass


class DatasetTypeDef(BaseObjectTypeDef):
    """
    Definition class for a data set type. E.g.:

    ```python
    class RawData(BaseModel):
        defs = DatasetTypeDef(
            code='RAW_DATA',
            description='...',
        )
    """

    # TODO add descriptions for `main_dataset_pattern` and `main_dataset_path`

    main_dataset_pattern: str | None = Field(
        default=None,
        description="""""",
    )

    main_dataset_path: str | None = Field(
        default=None,
        description="""""",
    )


class ObjectTypeDef(BaseObjectTypeDef):
    """
    Definition class for an object type. It adds the fields of `generated_code_prefix`, `auto_generate_codes`,
    and `validation_script` to the common attributes of a base object type definition. E.g.:

    ```python
    class Instrument(BaseModel):
        defs = ObjectTypeDef(
            code='INSTRUMENT',
            description='
            Measuring Instrument//Messger\u00e4t
            ',
            generated_code_prefix='INS',
        )
    ```
    """

    generated_code_prefix: str | None = Field(
        default=None,
        description="""
        A short prefix for the defined object type, e.g. 'CHEM'. If not specified, it is defined
        using the first 3 characters of `code`.
        """,
    )

    auto_generate_codes: bool = Field(
        True,
        description="""
        Boolean used to generate codes using `generated_code_prefix` plus a unique number. Set to
        True by default.
        """,
    )

    @model_validator(mode="after")
    @classmethod
    def model_validator_after_init(cls, data: Any) -> Any:
        """
        Validate the model after instantiation of the class.

        Args:
            data (Any): The data containing the fields values to validate.

        Returns:
            Any: The data with the validated fields.
        """
        # If `generated_code_prefix` is not set, use the first 3 characters of `code`
        if not data.generated_code_prefix:
            data.generated_code_prefix = data.code[:3]

        return data


class PropertyTypeDef(EntityDef):
    """
    Definition class for a property type. It adds the fields of `property_label`, `data_type`,
    `vocabulary_code`, `metadata`, `dynamic_script`, and `multivalued` to the common attributes of
    an entity definition.

    This class is used as an abstract layer for `PropertyTypeAssignment`, as in openBIS a PropertyType
    definition has less fields than when it is actually assigned to an entity type.
    """

    property_label: str = Field(
        ...,
        description="""
        Label that appears in the inventory view. This is the human-readable text for the property
        type definition, and it typically coincides with the `code`, e.g., `'Monitoring date'` for the
        `MONITORING_DATE` property type.
        """,
    )

    data_type: DataType = Field(
        ...,
        description="""
        The data type of the property, i.e., if it is an integer, float, string, etc. The allowed
        data types in openBIS are:
            - `BOOLEAN`
            - `CONTROLLEDVOCABULARY`
            - `DATE`
            - `HYPERLINK`
            - `INTEGER`
            - `MATERIAL`
            - `MULTILINE_VARCHAR`
            - `OBJECT`
            - `SAMPLE`
            - `REAL`
            - `TIMESTAMP`
            - `VARCHAR`
            - `XML`

        These are defined as an enumeration in the `DataType` class.

        Read more in https://openbis.readthedocs.io/en/latest/uncategorized/register-master-data-via-the-admin-interface.html#data-types-available-in-openbis.
        """,
    )

    vocabulary_code: str | None = Field(
        default=None,
        description="""
        String identifying the controlled vocabulary used for the data type of the property. This is
        thus only relevant if `data_type == 'CONTROLLEDVOCABULARY'`.
        """,
    )

    object_code: str | None = Field(
        default=None,
        description="""
        String identifying the object type used for the data type of the property. This is only
        relevant if `data_type == 'OBJECT'`.
        """,
    )

    # TODO add descriptions for `dynamic_script`

    metadata: dict | None = Field(
        default=None,
        description="""
        General metadata written in a dictionary format. This is used to store additional information
        about the property type, e.g., `{'unit': 'm', 'precision': 2}`.
        """,
    )

    dynamic_script: str | None = Field(
        default=None,
        description="""""",
    )


class PropertyTypeAssignment(PropertyTypeDef):
    """
    Base class used to define properties inside `ObjectType`, `CollectionType`, or `DatasetType`.
    This is used to construct these types by assigning property types to them. It adds the fields
    of `mandatory`, `show_in_edit_views`, `section`, `unique`, and `internal_assignment` to the common
    attributes of a property type definition. E.g.:

    ```python
    class Instrument(ObjectType):
        defs = ObjectTypeDef(
            code='INSTRUMENT',
            description='
            Measuring Instrument//Messger\u00e4t
            ',
            generated_code_prefix='INS',
        )

        alias = PropertyTypeAssignment(
            code='ALIAS',
            data_type='VARCHAR',
            property_label='Alternative name',
            description='
            e.g. abbreviation or nickname//z.B. Abkürzung oder Spitzname//z.B. Abkürzung oder Spitzname
            ',
            mandatory=False,
            show_in_edit_views=True,
            section='General information',
        )

        # ... other property type assignments here ...
    ```
    """

    mandatory: bool = Field(
        ...,
        description="""
        If `True`, the property is mandatory and has to be set during instantiation of the object type.
        If `False`, the property is optional.
        """,
    )

    show_in_edit_views: bool = Field(
        ...,
        description="""
        If `True`, the property is shown in the edit views of the ELN in the object type instantiation.
        If `False`, the property is hidden.
        """,
    )

    section: str = Field(
        ...,
        description="""
        Section to which the property type belongs to. E.g., `'General Information'`.
        """,
    )

    # TODO add descriptions for `unique` and `internal_assignment`

    unique: str | None = Field(
        default=None,
        description="""""",
    )

    internal_assignment: str | None = Field(
        default=None,
        description="""""",
    )


class VocabularyTypeDef(EntityDef):
    """
    Definition class for a vocabulary type. It adds the fields of `url_template` to the common attributes of
    an entity definition. E.g.:

    ```python
    class DocumentType(VocabularyType):
        defs = VocabularyTypeDef(
            code='DOCUMENT_TYPE',
            description='Document type//Dokumententypen',
        )
    ```
    """

    # TODO add descriptions for `url_template`

    url_template: str | None = Field(
        default=None,
        description="""""",
    )


class VocabularyTerm(VocabularyTypeDef):
    """
    Base class used to define terms inside a `VocabularyType`. This is used to construct the vocabulary types
    by assigning vocabulary terms to them. It adds the fields of `label` and `official` to the common attributes
    of a vocabulary type definition. E.g.:

    ```python
    class DocumentType(VocabularyType):
        defs = VocabularyTypeDef(
            code='DOCUMENT_TYPE',
            description='Document type//Dokumententypen',
        )

        acceptance_certificate = VocabularyTerm(
            code='ACCEPTANCE_CERTIFICATE',
            label='Acceptance Certificate',
            description='Acceptance Certificate//Abnahmezeugnis',
        )

        calibration_certificate = VocabularyTerm(
            code='CALIBRATION_CERTIFICATE',
            label='Calibration Certificate',
            description='Calibration Certificate//Kalibrierschein',
        )

        # ... other vocabulary term definitions here ...
    """

    # TODO add descriptions for `label` and `official`

    label: str = Field(
        ...,
        description="""""",
    )

    official: bool = Field(
        True,
        description="""""",
    )
