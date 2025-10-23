import datetime
import inspect
import json
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, no_type_check

import h5py
from pydantic import BaseModel, ConfigDict, Field, model_validator
from rdflib import BNode, Literal
from rdflib.namespace import DC, OWL, RDF, RDFS

from bam_masterdata.utils import DATAMODEL_DIR, import_module, listdir_py_modules

if TYPE_CHECKING:
    from pybis import Openbis
    from rdflib import Graph, Namespace, URIRef
    from structlog._config import BoundLoggerLazyProxy

import uuid

from bam_masterdata.metadata._maps import (
    COLLECTION_TYPE_MAP,
    DATASET_TYPE_MAP,
    OBJECT_TYPE_MAP,
    VOCABULARY_TYPE_MAP,
)
from bam_masterdata.metadata.definitions import (
    CollectionTypeDef,
    DatasetTypeDef,
    ObjectTypeDef,
    PropertyTypeAssignment,
    VocabularyTerm,
    VocabularyTypeDef,
)
from bam_masterdata.openbis import OpenbisEntities
from bam_masterdata.utils import code_to_class_name


class BaseEntity(BaseModel):
    """
    Base class used to define `ObjectType` and `VocabularyType` classes. It extends the `BaseModel`
    adding new methods that are useful for interfacing with openBIS.
    """

    code: str | None = Field(
        default=None,
        description="""
        Code of the entity to assign as permanent identifier in openBIS.
        """,
    )

    def __init__(self, **kwargs):
        super().__init__()

        # We store the `_property_metadata` during instantiation of the class
        self._property_metadata = self.get_property_metadata()

        for key, value in kwargs.items():
            setattr(self, key, value)

    def __setattr__(self, key, value):
        if key == "_property_metadata":
            super().__setattr__(key, value)
            return

        if key in self._property_metadata:
            # TODO add CONTROLLEDVOCABULARY and OBJECT cases
            expected_type = self._property_metadata[key].data_type.pytype
            if expected_type and not isinstance(value, expected_type):
                raise TypeError(
                    f"Invalid type for '{key}': Expected {expected_type.__name__}, got {type(value).__name__}"
                )

        # TODO add check if someone tries to set up a definition instead of an assigned property

        object.__setattr__(self, key, value)

    def __repr__(self):
        # Filter for attributes that are `PropertyTypeAssignment` and set to a finite value
        class_prop_name = None
        fields = []
        for key, metadata in self._property_metadata.items():
            if isinstance(metadata, PropertyTypeAssignment):
                value = getattr(self, key, None)
                # Only include set attributes
                if value is not None and not isinstance(value, PropertyTypeAssignment):
                    if key == "name":
                        class_prop_name = value
                    fields.append(f"{key}={repr(value)}")

        # Format the output
        class_name = self.cls_name
        if class_prop_name:  # adding `name` if available
            class_name = f"{class_prop_name}:{class_name}"
        return f"{class_name}({', '.join(fields)})"

    # Overwriting the __str__ method to use the same representation as __repr__
    __str__ = __repr__

    @property
    def cls_name(self) -> str:
        """
        Returns the entity name of the class as a string to speed up checks. This is a property
        to be overwritten by each of the abstract entity types.
        """
        return self.__class__.__name__

    @property
    def _base_attrs(self) -> list:
        """
        List of base properties or terms assigned to an entity type. This are the direct properties or terms
        assigned when defining a new entity type.
        """
        cls_attrs = self.__class__.__dict__
        base_attrs = [
            attr_name
            for attr_name in cls_attrs
            if not (
                attr_name.startswith("_")
                or callable(cls_attrs[attr_name])
                or attr_name
                in ["defs", "model_config", "model_fields", "model_computed_fields"]
            )
        ]
        return [getattr(self, attr_name) for attr_name in base_attrs]

    def _to_openbis(
        self,
        logger: "BoundLoggerLazyProxy",
        openbis: "Openbis",
        type: str,
        type_map: dict,
        get_type: Callable[..., Any],
        create_type: Callable[..., Any],
    ) -> None:
        """
        Simplified function to add or update the entity type in openBIS.
        """
        # Get all existing entities from openBIS
        openbis_entities = getattr(
            OpenbisEntities(url=openbis.url), f"get_{type}_dict"
        )()
        defs = getattr(self, "defs")

        is_vocab = isinstance(self, VocabularyType)

        # Check if the entity already exists
        if defs.code in openbis_entities:
            logger.info(f"Entity '{defs.code}' already exists in openBIS.")
            # Retrieve the existing entity
            entity = get_type(openbis, defs.code)
            # entity = openbis_entities[defs.code]

            # Get properties from self and openBIS
            self_properties = getattr(self, "terms" if is_vocab else "properties", [])
            obis_properties = (
                entity.get_terms().df.code
                if is_vocab
                else entity.get_property_assignments()
            )
            obis_property_codes = [
                prop.code if not is_vocab else prop for prop in obis_properties
            ]

            # Check for properties in self that are not in openBIS
            new_properties_added = False
            for prop in self_properties:
                if prop.code not in obis_property_codes:
                    logger.info(
                        f"Adding new '{'term' if is_vocab else 'property'}' {prop.code}' to entity '{defs.code}'."
                    )
                    new_properties_added = True

                    # Handle special case for OBJECT or SAMPLE data types
                    if not is_vocab and (
                        prop.data_type == "OBJECT" or prop.data_type == "SAMPLE"
                    ):
                        prop.data_type = "SAMPLE"

                    # Assign the term or property to the entity
                    if is_vocab:
                        term = openbis.new_term(
                            code=prop.code,
                            vocabularyCode=defs.code,
                            label=prop.label,
                            description=prop.description,
                        )
                        if prop.official:
                            term.official = prop.official
                        term.save()
                    else:
                        if prop.vocabulary_code:
                            entity.assign_property(
                                prop=prop.code,
                                section=prop.section,
                                mandatory=prop.mandatory,
                                showInEditView=prop.show_in_edit_views,
                                vocabulary=prop.vocabulary_code,
                            )
                        else:
                            entity.assign_property(
                                prop=prop.code,
                                section=prop.section,
                                mandatory=prop.mandatory,
                                showInEditView=prop.show_in_edit_views,
                            )

            if not new_properties_added:
                logger.info(
                    f"No new '{'terms' if is_vocab else 'properties'}' added to entity '{defs.code}'."
                )

            # Save the entity after adding new properties
            if not is_vocab:
                entity.save()
            return entity

        # If the entity is new, create it
        logger.info(f"Creating new entity '{defs.code}' in openBIS.")
        if not is_vocab:
            entity = create_type(openbis, defs)
            entity.save()

            # Assign properties to the new entity
            properties = getattr(self, "properties", [])
            for prop in properties:
                logger.info(f"Adding new property {prop.code} to {defs.code}.")
                # Handle special case for OBJECT or SAMPLE data types
                if prop.data_type == "OBJECT" or prop.data_type == "SAMPLE":
                    prop.data_type = "SAMPLE"

                # Assign the property to the entity
                entity.assign_property(
                    prop=prop.code,
                    section=prop.section,
                    mandatory=prop.mandatory,
                    showInEditView=prop.show_in_edit_views,
                )
        else:
            # Transform the list of VocabularyTerm objects into the desired format
            terms = [
                {
                    "code": term.code,
                    "label": term.label,
                    "description": term.description,
                }
                for term in getattr(self, "terms", [])
            ]
            term_codes = ", ".join([term.code for term in getattr(self, "terms", [])])
            logger.info(f"Adding new terms {term_codes} to {defs.code}.")
            entity = create_type(openbis, defs, terms)
            entity.save()

        # Save the entity after assigning properties
        if not is_vocab:
            entity.save()
        return entity

    def get_property_metadata(self) -> dict:
        """
        Dictionary containing the metadata of the properties assigned to the entity type.

        Returns:
            dict: A dictionary containing the keys of the `PropertyTypeAssignment` attribute names and the
            values of the definitions of `PropertyTypeAssignment`. Example:
            {
                "name": PropertyTypeAssignment(
                    code="$NAME",
                    data_type=VARCHAR,
                    mandatory=True,
                    property_label="Name"
                ),
                "age": PropertyTypeAssignment(
                    code="AGE",
                    data_type=INTEGER,
                    mandatory=False,
                    property_label="Age"
                ),
            }
        """
        cls_attrs = self.__class__.__dict__

        # Store property metadata at class level
        prop_meta_dict: dict = {}
        for base in type(self).__mro__:
            cls_attrs = getattr(base, "__dict__", {})
            for attr_name, attr_value in cls_attrs.items():
                if isinstance(attr_value, PropertyTypeAssignment):
                    prop_meta_dict[attr_name] = attr_value
        return prop_meta_dict

    def to_json(self, indent: int | None = None) -> str:
        """
        Returns the entity as a string in JSON format storing the value of the properties
        assigned to the entity.

        Args:
            indent (Optional[int], optional): The indent to print in JSON. Defaults to None.

        Returns:
            str: The JSON representation of the entity.
        """
        data: dict = {}
        for key in self._property_metadata.keys():
            try:
                value = getattr(self, key)
            except AttributeError:
                continue
            if isinstance(value, PropertyTypeAssignment):
                continue
            data[key] = value
        return json.dumps(data, indent=indent)

    def to_dict(self) -> dict:
        """
        Returns the entity as a dictionary storing the value of the properties assigned to the entity.

        Returns:
            dict: The dictionary representation of the entity.
        """
        dump_json = self.to_json()
        return json.loads(dump_json)

    def to_hdf5(self, hdf_file: h5py.File, group_name: str = "") -> h5py.File:
        """
        Serialize the entity to a HDF5 file under the group specified in the input.

        Args:
            hdf_file (h5py.File): The HDF5 file to store the entity.
            group_name (str, optional): The group name to serialize the data.
        """
        if not group_name:
            group_name = self.cls_name
        group = hdf_file.create_group(group_name)

        for key in self._property_metadata.keys():
            try:
                value = getattr(self, key)
                if not value:
                    continue
                if isinstance(value, str | int | float | bool | list | tuple):
                    group.create_dataset(key, data=value)
                else:
                    raise TypeError(
                        f"Unsupported type {type(value)} for key {key} for HDF5 serialization."
                    )
            except AttributeError:
                continue

    def model_to_dict(self) -> dict:
        """
        Returns the model as a dictionary storing the data `defs` and the property or vocabulary term
        assignments.

        Returns:
            dict: The dictionary representation of the model.
        """
        data = self.model_dump()

        attr_value = getattr(self, "defs")
        if isinstance(attr_value, BaseModel):
            data["defs"] = attr_value.model_dump()
        else:
            data["defs"] = attr_value
        return data

    def model_to_json(self, indent: int | None = None) -> str:
        """
        Returns the model as a string in JSON format storing the data `defs` and the property or
        vocabulary term assignments.

        Args:
            indent (Optional[int], optional): The indent to print in JSON. Defaults to None.

        Returns:
            str: The JSON representation of the model.
        """
        # * `model_dump_json()` from pydantic does not store the `defs` section of each entity.
        data = self.model_to_dict()
        return json.dumps(data, indent=indent)

    def _add_properties_rdf(
        self,
        namespace: "Namespace",
        graph: "Graph",
        prop: "PropertyTypeAssignment",
        logger: "BoundLoggerLazyProxy",
    ) -> "URIRef":
        """
        Add the properties assigned to the entity to the RDF graph extracting the information from
        OpenBIS for the `object_code` or `vocabulary_code`.

        Args:
            namespace (Namespace): The namespace to use for the RDF graph.
            graph (Graph): The RDF graph to which the properties are added.
            prop (PropertyTypeAssignment): The property assigned to the entity.
            logger (BoundLoggerLazyProxy): The logger to log messages.

        Returns:
            URIRef: The URI reference of the property added to the RDF graph.
        """
        prop_uri = namespace[prop.id]

        # Define the property as an OWL class inheriting from PropertyType
        graph.add((prop_uri, RDF.type, OWL.Thing))
        graph.add((prop_uri, RDFS.subClassOf, namespace.PropertyType))

        # Add attributes like id, code, description in English and Deutsch, property_label, data_type
        graph.add((prop_uri, RDFS.label, Literal(prop.id, lang="en")))
        graph.add((prop_uri, DC.identifier, Literal(prop.code)))
        descriptions = prop.description.split("//")
        if len(descriptions) > 1:
            graph.add((prop_uri, RDFS.comment, Literal(descriptions[0], lang="en")))
            graph.add((prop_uri, RDFS.comment, Literal(descriptions[1], lang="de")))
        else:
            graph.add((prop_uri, RDFS.comment, Literal(prop.description, lang="en")))
        graph.add(
            (prop_uri, namespace.propertyLabel, Literal(prop.property_label, lang="en"))
        )
        graph.add((prop_uri, namespace.dataType, Literal(prop.data_type.value)))
        if prop.data_type.value == "OBJECT":
            # entity_ref_uri = BAM[code_to_class_name(obj.object_code)]
            # graph.add((prop_uri, BAM.referenceTo, entity_ref_uri))
            object_code = code_to_class_name(prop.object_code, logger)
            if not object_code:
                logger.error(
                    f"Failed to identify the `object_code` for the property {prop.id}"
                )
                return prop_uri
            entity_ref_uri = namespace[object_code]

            # Create a restriction with referenceTo
            restriction = BNode()
            graph.add((restriction, RDF.type, OWL.Restriction))
            graph.add((restriction, OWL.onProperty, namespace["referenceTo"]))
            graph.add((restriction, OWL.someValuesFrom, entity_ref_uri))

            # Add the restriction as a subclass of the property
            graph.add((prop_uri, RDFS.subClassOf, restriction))
        return prop_uri

    # skos:prefLabel used for class names
    # skos:definition used for `description` (en, de)
    # dc:identifier used for `code`  # ! only defined for internal codes with $ symbol
    # parents defined from `code`
    # assigned properties can be Mandatory or Optional, can be PropertyType or ObjectType
    # ? For OBJECT TYPES
    # ? `generated_code_prefix`, `auto_generate_codes`?
    @no_type_check
    def model_to_rdf(
        self, namespace: "Namespace", graph: "Graph", logger: "BoundLoggerLazyProxy"
    ) -> None:
        """
        Convert the entity to RDF triples and add them to the graph. The function uses the
        `_add_properties_rdf` method to convert the properties assigned to the entity to RDF triples.

        Args:
            namespace (Namespace): The namespace to use for the RDF graph.
            graph (Graph): The RDF graph to which the entity is added.
            logger (BoundLoggerLazyProxy): The logger to log messages.
        """
        entity_uri = namespace[self.defs.id]

        # Define the entity as an OWL class inheriting from the specific namespace type
        graph.add((entity_uri, RDF.type, OWL.Thing))
        parent_classes = self.__class__.__bases__
        for parent_class in parent_classes:
            if issubclass(parent_class, BaseEntity) and parent_class != BaseEntity:
                # if parent_class.__name__ in [
                #     "ObjectType",
                #     "CollectionType",
                #     "DatasetType",
                # ]:
                #     # ! add here logic of subClassOf connecting with PROV-O or BFO
                #     # ! maybe via classes instead of ObjectType/CollectionType/DatasetType?
                #     # ! Example:
                #     # !     graph.add((entity_uri, RDFS.subClassOf, "http://www.w3.org/ns/prov#Entity"))
                #     continue
                parent_uri = namespace[parent_class.__name__]
                graph.add((entity_uri, RDFS.subClassOf, parent_uri))

        # Add attributes like id, code, description in English and Deutsch, property_label, data_type
        graph.add((entity_uri, RDFS.label, Literal(self.defs.id, lang="en")))
        graph.add((entity_uri, DC.identifier, Literal(self.defs.code)))
        descriptions = self.defs.description.split("//")
        if len(descriptions) > 1:
            graph.add((entity_uri, RDFS.comment, Literal(descriptions[0], lang="en")))
            graph.add((entity_uri, RDFS.comment, Literal(descriptions[1], lang="de")))
        else:
            graph.add(
                (entity_uri, RDFS.comment, Literal(self.defs.description, lang="en"))
            )
        # Adding properties relationships to the entities
        for assigned_prop in self._base_attrs:
            prop_uri = self._add_properties_rdf(namespace, graph, assigned_prop, logger)
            restriction = BNode()
            graph.add((restriction, RDF.type, OWL.Restriction))
            if assigned_prop.mandatory:
                graph.add(
                    (restriction, OWL.onProperty, namespace["hasMandatoryProperty"])
                )
            else:
                graph.add(
                    (restriction, OWL.onProperty, namespace["hasOptionalProperty"])
                )
            graph.add((restriction, OWL.someValuesFrom, prop_uri))

            # Add the restriction as a subclass of the entity
            graph.add((entity_uri, RDFS.subClassOf, restriction))


class VocabularyType(BaseEntity):
    """
    Base class used to define vocabulary types. All vocabulary types must inherit from this class. The
    vocabulary types are defined in the module `bam_masterdata/vocabulary_types.py`.

    The `VocabularyType` class contains a list of all `terms` defined for a `VocabularyType`, for
    internally represent the model in other formats (e.g., JSON or Excel).
    """

    model_config = ConfigDict(ignored_types=(VocabularyTypeDef, VocabularyTerm))

    terms: list[VocabularyTerm] = Field(
        default=[],
        description="""
        List of vocabulary terms. This is useful for internal representation of the model.
        """,
    )

    @property
    def base_name(self) -> str:
        """
        Returns the entity name of the class as a string.
        """
        return "VocabularyType"

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
        # Add all the vocabulary terms defined in the vocabulary type to the `terms` list.
        # TODO check if the order is properly assigned
        for base in cls.__mro__:
            for attr_name, attr_val in base.__dict__.items():
                if isinstance(attr_val, VocabularyTerm):
                    data.terms.append(attr_val)

        return data

    def to_openbis(
        self,
        logger: "BoundLoggerLazyProxy",
        openbis: "Openbis",
        type: str = "vocabulary",
        type_map: dict = VOCABULARY_TYPE_MAP,
    ) -> None:
        def get_type(openbis: "Openbis", code: str):
            return openbis.get_vocabulary(code)

        def create_type(openbis: "Openbis", defs: VocabularyTypeDef, terms: list):
            return openbis.new_vocabulary(
                code=defs.code, description=defs.description, terms=terms
            )

        super()._to_openbis(
            logger=logger,
            openbis=openbis,
            type=type,
            type_map=type_map,
            get_type=get_type,
            create_type=create_type,
        )


class ObjectType(BaseEntity):
    """
    Base class used to define object types. All object types must inherit from this class. The
    object types are defined in the module `bam_masterdata/object_types.py`.

    The `ObjectType` class contains a list of all `properties` defined for a `ObjectType`, for
    internally represent the model in other formats (e.g., JSON or Excel).

    Note this is also used for `CollectionType` and `DatasetType`, as they also contain a list of
    properties.
    """

    model_config = ConfigDict(
        ignored_types=(
            ObjectTypeDef,
            CollectionTypeDef,
            DatasetTypeDef,
            PropertyTypeAssignment,
        )
    )

    properties: list[PropertyTypeAssignment] = Field(
        default=[],
        description="""
        List of properties assigned to an object type. This is useful for internal representation of the model.
        """,
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Initialize the properties list to store PropertyTypeAssignment instances
        self._properties = {}
        for key, prop in self._property_metadata.items():
            self._properties[key] = prop.data_type

    def _set_object_value(self, key, value):
        """
        Sets the value when the data type is OBJECT.
        """
        if isinstance(value, str):
            # Validate the path format: /{space}/{project}/{collection}/{object} or /{space}/{project}/{object}
            # If path is valid, store it as-is
            if not value.startswith("/"):
                raise ValueError(
                    f"Invalid OBJECT path format for '{key}': Path must start with '/', got '{value}'"
                )
            path_parts = value.strip("/").split("/")
            if len(path_parts) not in [3, 4]:
                raise ValueError(
                    f"Invalid OBJECT path format for '{key}': Expected '/<space>/<project>/<collection>/<object>' "
                    f"or '/<space>/<project>/<object>', got '{value}'"
                )
            # * We don't validate if the object exists here as it requires pybis connection
            # * That validation should be done when saving to openBIS
        elif isinstance(value, ObjectType):
            # Check if the object instance has a code
            if not hasattr(value, "code") or value.code is None:
                raise ValueError(
                    f"Object instance for '{key}' must have a 'code' attribute set to be used as a reference"
                )
        else:
            raise TypeError(
                f"Invalid type for OBJECT property '{key}': Expected str (path) or ObjectType instance, "
                f"got {type(value).__name__}"
            )
        return value

    def _validate_controlled_vocabulary(self, meta, key, value) -> None:
        """
        Validates the value of a CONTROLLEDVOCABULARY.
        """
        vocabulary_code = meta[key].vocabulary_code
        if not vocabulary_code:
            raise ValueError(
                f"Property '{key}' of type CONTROLLEDVOCABULARY must have a vocabulary_code defined."
            )
        vocab_path = None
        for file in listdir_py_modules(DATAMODEL_DIR):
            if "vocabulary_types.py" in file:
                vocab_path = file
                break
        if vocab_path is None:
            raise FileNotFoundError(
                f"The file 'vocabulary_types.py' was not found in the directory specified by {DATAMODEL_DIR}."
            )
        vocabulary_class = self.get_vocabulary_class(vocabulary_code, vocab_path)
        if vocabulary_class is None:
            raise ValueError(
                f"No matching vocabulary class found for vocabulary_code '{vocabulary_code}'."
            )
        codes = [term.code for term in vocabulary_class.terms]
        if value not in codes:
            raise ValueError(
                f"{value} for {key} is not in the list of allowed terms for vocabulary."
            )

    def __setattr__(self, key, value):
        if key in ["_property_metadata", "_properties", "code"]:
            super().__setattr__(key, value)
            return

        # key search in every nested class
        for base in type(self).__mro__:
            prop_meta = getattr(base, "get_property_metadata", None)
            if callable(prop_meta):
                meta = (
                    prop_meta(self)
                    if base is not type(self)
                    else self._property_metadata
                )
                if key in meta:
                    # Type check
                    expected_type = meta[key].data_type.pytype
                    if expected_type is datetime.datetime:
                        if isinstance(value, datetime.datetime):
                            try:
                                value = value.strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                )  # create string
                                expected_type = str
                            except ValueError:
                                raise ValueError(
                                    f"Invalid datetime format for '{key}': Expected ISO format string, got '{value}'"
                                )
                        elif isinstance(value, str):
                            try:
                                datetime.datetime.fromisoformat(value)
                                expected_type = str
                            except ValueError:
                                raise ValueError(
                                    f"Invalid datetime format for '{key}': Expected ISO format string, got '{value}'"
                                )
                        else:
                            raise TypeError(
                                f"Invalid type for '{key}': Expected datetime or ISO format string, got {type(value).__name__}"
                            )
                    if expected_type and not isinstance(value, expected_type):
                        raise TypeError(
                            f"Invalid type for '{key}': Expected {expected_type.__name__}, got {type(value).__name__}"
                        )

                    # Get data type for additional checks
                    data_type = meta[key].data_type
                    # OBJECT check and attr assignment
                    if data_type == "OBJECT":
                        return object.__setattr__(
                            self, key, self._set_object_value(key, value)
                        )
                    # CONTROLLEDVOCABULARY check
                    if data_type == "CONTROLLEDVOCABULARY":
                        self._validate_controlled_vocabulary(meta, key, value)

                    # Setting attribute value after all checks
                    return object.__setattr__(self, key, value)

        raise KeyError(
            f"Key '{key}' not found in any property_metadata of {type(self).__name__} or its bases."
        )

    def get_vocabulary_class(
        self, vocabulary_code: str, vocab_path: str
    ) -> VocabularyType | None:
        """
        Get the class instance of the vocabulary type defined by `vocabulary_code` in the Python module
        specified by `vocab_path`.

        Args:
            vocabulary_code (str): Code of the vocabulary type to get.
            vocab_path (str): Path to the module containing the vocabulary type definitions.

        Returns:
            VocabularyType | None: The class of the vocabulary type if found, otherwise None.
        """
        module = import_module(vocab_path)
        vocabulary_class = None
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if name == code_to_class_name(vocabulary_code):
                vocabulary_class = obj()
                break

        return vocabulary_class

    @property
    def base_name(self) -> str:
        """
        Returns the entity name of the class as a string.
        """
        return "ObjectType"

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
        # Add all the properties assigned to the object type to the `properties` list.
        # TODO check if the order is properly assigned
        for base in cls.__mro__:
            for _, attr_val in base.__dict__.items():
                if isinstance(attr_val, PropertyTypeAssignment):
                    data.properties.append(attr_val)

        return data

    def to_openbis(
        self,
        logger: "BoundLoggerLazyProxy",
        openbis: "Openbis",
        type: str = "object",
        type_map: dict = OBJECT_TYPE_MAP,
    ) -> None:
        def get_type(openbis: "Openbis", code: str):
            return openbis.get_object_type(code)

        def create_type(openbis: "Openbis", defs: ObjectTypeDef):
            return openbis.new_object_type(
                code=defs.code,
                description=defs.description,
                validationPlugin=defs.validation_script,
                generatedCodePrefix=defs.generated_code_prefix,
                autoGeneratedCode=defs.auto_generate_codes,
            )

        super()._to_openbis(
            logger=logger,
            openbis=openbis,
            type=type,
            type_map=type_map,
            get_type=get_type,
            create_type=create_type,
        )


UUID_SUFFIX_LENGTH = 8


def generate_object_id(object_type: ObjectType) -> str:
    """
    Generate a unique identifier for an object type based on its definition.

    Args:
        object_type (ObjectType): The object type for which to generate the identifier.

    Returns:
        str: A unique identifier string for the object type, combining a prefix from the definition
        and a random 8-characters-long UUID suffix.
    """
    try:
        prefix = object_type.defs.generated_code_prefix  # string prefix
        # UUID suffix with a defined length
        suffix = uuid.uuid4().hex[:UUID_SUFFIX_LENGTH]
    except AttributeError:
        # fallback if the object type does not have a generated_code_prefix
        prefix = ""
        suffix = str(uuid.uuid4())
    return f"{prefix}{suffix}"


def generate_object_relationship_id(parent_id: str, child_id: str) -> str:
    """
    Generate a unique identifier for a relationship between two object types as their IDs concatenated.

    Args:
        parent_id (str): The unique identifier of the parent object type.
        child_id (str): The unique identifier of the child object type.

    Returns:
        str: A unique identifier string for the relationship, combining the parent and child IDs.
    """
    return f"{parent_id}>>{child_id}"


class CollectionType(ObjectType):
    model_config = ConfigDict(
        ignored_types=(
            ObjectTypeDef,
            ObjectType,
            CollectionTypeDef,
            PropertyTypeAssignment,
        )
    )

    attached_objects: dict[str, ObjectType] = Field(
        default={},
        exclude=True,
        description="""
        Dictionary containing the object types attached to the collection type.
        The keys are object unique identifiers and the values are the ObjectType instances.
        """,
    )

    relationships: dict[str, tuple[str, str]] = Field(
        default={},
        exclude=True,
        description="""
        Dictionary containing the relationships between the objects attached to the collection type.
        The keys are relationships unique identifiers, the values are the object unique identifiers as a
        tuple, and the order is always (parent_id, child_id).
        """,
    )

    def __repr__(self):
        return f"{self.base_name}(attached_objects={self.attached_objects}, relationships={self.relationships})"

    @property
    def base_name(self) -> str:
        """
        Returns the entity name of the class as a string.
        """
        return "CollectionType"

    def to_openbis(
        self,
        logger: "BoundLoggerLazyProxy",
        openbis: "Openbis",
        type: str = "collection",
        type_map: dict = COLLECTION_TYPE_MAP,
    ) -> None:
        def get_type(openbis: "Openbis", code: str):
            return openbis.get_collection_type(code)

        def create_type(openbis: "Openbis", defs: CollectionTypeDef):
            if defs.validation_script == "None":
                defs.validation_script = None
            if defs.validation_script:
                return openbis.new_collection_type(
                    code=defs.code,
                    description=defs.description,
                    validationPlugin=defs.validation_script,
                )
            else:
                return openbis.new_collection_type(
                    code=defs.code,
                    description=defs.description,
                    validationPlugin="",
                )

        super()._to_openbis(
            logger=logger,
            openbis=openbis,
            type=type,
            type_map=type_map,
            get_type=get_type,
            create_type=create_type,
        )

    def add(self, object_type: ObjectType) -> str:
        """
        Add an object type to the collection type.

        Args:
            object_type (ObjectType): The object type to add to the collection type.

        Returns:
            str: The unique identifier of the object type assigned in openBIS.
        """
        if not isinstance(object_type, ObjectType):
            raise TypeError(
                f"Expected an ObjectType instance, got `{type(object_type).__name__}`"
            )

        # Check mandatory properties are filled
        missing_fields = []
        for attr_name, prop in object_type._property_metadata.items():
            assigned_prop = getattr(object_type, attr_name, None)
            if prop.mandatory and isinstance(assigned_prop, PropertyTypeAssignment):
                missing_fields.append(attr_name)

        if missing_fields:
            raise ValueError(
                f"The following mandatory fields are missing for ObjectType '{object_type.cls_name}': {', '.join(missing_fields)}"
            )

        object_id = generate_object_id(object_type)
        self.attached_objects[object_id] = object_type
        return object_id

    def remove(self, object_id: str = "") -> None:
        """
        Remove an object type from the collection type by its unique identifier.

        Args:
            object_id (str, optional): The ID of the object type to be removed from the collection.
        """
        if not object_id:
            raise ValueError(
                "You must provide an `object_id` to remove the object type from the collection."
            )
        if object_id not in self.attached_objects.keys():
            raise ValueError(
                f"Object with ID '{object_id}' does not exist in the collection."
            )
        del self.attached_objects[object_id]

    def add_relationship(self, parent_id: str, child_id: str) -> str:
        """
        Add a relationship between two object types in the collection type.

        Args:
            parent_id (str): The unique identifier of the parent object type.
            child_id (str): The unique identifier of the child object type.

        Returns:
            str: The unique identifier of the relationship created, which is a concatenation of the parent
            and child IDs.
        """
        if not parent_id or not child_id:
            raise ValueError(
                "Both `parent_id` and `child_id` must be provided to add a relationship."
            )
        if (
            parent_id not in self.attached_objects.keys()
            or child_id not in self.attached_objects.keys()
        ):
            raise ValueError(
                "Both `parent_id` and `child_id` must be assigned to objects attached to the collection."
            )
        relationship_id = generate_object_relationship_id(parent_id, child_id)
        self.relationships[relationship_id] = (parent_id, child_id)
        return relationship_id

    def remove_relationship(self, relationship_id: str) -> None:
        """
        Remove a relationship from the collection type.

        Args:
            relationship_id (str): The unique identifier of the relationship to remove.
        """
        if not relationship_id:
            raise ValueError(
                "You must provide a `relationship_id` to remove the relationship from the collection type."
            )
        if relationship_id not in self.relationships.keys():
            raise ValueError(
                f"Relationship with ID '{relationship_id}' does not exist in the collection type."
            )
        del self.relationships[relationship_id]


class DatasetType(ObjectType):
    @property
    def base_name(self) -> str:
        """
        Returns the entity name of the class as a string.
        """
        return "DatasetType"

    def to_openbis(
        self,
        logger: "BoundLoggerLazyProxy",
        openbis: "Openbis",
        type: str = "dataset",
        type_map: dict = DATASET_TYPE_MAP,
    ) -> None:
        def get_type(openbis: "Openbis", code: str):
            return openbis.get_dataset_type(code)

        def create_type(openbis: "Openbis", defs: DatasetTypeDef):
            return openbis.new_dataset_type(
                code=defs.code,
                description=defs.description,
                validationPlugin=defs.validation_script,
                # This is not accepted by openBIS when creating dataset types
                # mainDatasetPattern=defs.main_dataset_pattern,
                # mainDatasetPath=defs.main_dataset_path,
            )

        super()._to_openbis(
            logger=logger,
            openbis=openbis,
            type=type,
            type_map=type_map,
            get_type=get_type,
            create_type=create_type,
        )
