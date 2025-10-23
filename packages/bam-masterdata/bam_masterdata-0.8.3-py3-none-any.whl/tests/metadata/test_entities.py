import io

import h5py
import pytest

from bam_masterdata.metadata.definitions import PropertyTypeAssignment
from bam_masterdata.metadata.entities import (
    CollectionType,
    generate_object_id,
    generate_object_relationship_id,
)
from tests.conftest import (
    generate_base_entity,
    generate_object_type,
    generate_object_type_longer,
    generate_object_type_miss_mandatory,
    generate_vocabulary_type,
)


class TestBaseEntity:
    def test_setattr(self):
        """Test the method `__setattr__` from the class `BaseEntity`."""
        entity = generate_base_entity()
        assert "name" in entity._property_metadata
        assert isinstance(entity._property_metadata["name"], PropertyTypeAssignment)
        assert isinstance(entity.name, PropertyTypeAssignment)

        # Valid type (VARCHAR is str in Python)
        entity.name = "Test"
        assert entity.name == "Test" and isinstance(entity.name, str)

        # Invalid types
        with pytest.raises(
            TypeError, match="Invalid type for 'name': Expected str, got int"
        ):
            entity.name = 42
        with pytest.raises(
            TypeError, match="Invalid type for 'name': Expected str, got bool"
        ):
            entity.name = True

    def test_repr(self):
        """Test the method `__repr__` from the class `BaseEntity`."""
        entity = generate_base_entity()
        assert repr(entity) == "MockedEntity()"
        entity.name = "Test"
        assert repr(entity) == "Test:MockedEntity(name='Test')"

    def test_to_json(self):
        """Test the method `to_json` from the class `BaseEntity`."""
        entity = generate_base_entity()
        entity.name = "Test"
        data = entity.to_json()
        assert data == '{"name": "Test"}'

    def test_to_dict(self):
        """Test the method `to_dict` from the class `BaseEntity`."""
        entity = generate_base_entity()
        entity.name = "Test"
        data = entity.to_dict()
        assert data == {"name": "Test"}

    def test_to_hdf5(self):
        """Test the method `to_hdf5` from the class `BaseEntity`."""
        entity = generate_base_entity()
        entity.name = "Test"
        # mocking the HDF5 file
        with h5py.File(io.BytesIO(), "w") as hdf_file:
            entity.to_hdf5(hdf_file=hdf_file)
            data = hdf_file
            assert isinstance(data, h5py.File)
            assert isinstance(data["MockedEntity"], h5py.Group)
            assert data["MockedEntity"]["name"][()] == b"Test"
            assert data["MockedEntity"]["name"][()].decode() == "Test"

    def test_model_to_json(self):
        """Test the method `model_to_json` from the class `BaseEntity`."""
        entity = generate_base_entity()
        assert (
            entity.model_to_json()
            == '{"code": null, "defs": {"code": "MOCKED_ENTITY", "description": "Mockup for an entity definition//Mockup f\\u00fcr eine Entit\\u00e4tsdefinition", "iri": null, "id": "MockedEntity", "row_location": null, "validation_script": null, "generated_code_prefix": "MOCKENT", "auto_generate_codes": true}}'
        )

    def test_model_to_dict(self):
        """Test the method `model_to_dict` from the class `BaseEntity`."""
        entity = generate_base_entity()
        assert entity.model_to_dict() == {
            "code": None,
            "defs": {
                "code": "MOCKED_ENTITY",
                "description": "Mockup for an entity definition//Mockup für eine Entitätsdefinition",
                "iri": None,
                "id": "MockedEntity",
                "row_location": None,
                "validation_script": None,
                "generated_code_prefix": "MOCKENT",
                "auto_generate_codes": True,
            },
        }


class TestObjectType:
    def test_model_validator_after_init(self):
        """Test the method `model_validator_after_init` from the class `ObjectType`."""
        # 2 properties in this `ObjectType`
        print(
            f"MockedObjectType properties: {[prop.code for prop in generate_object_type().properties]}"
        )
        print(
            f"MockedObjectTypeLonger properties: {[prop.code for prop in generate_object_type_longer().properties]}"
        )
        object_type = generate_object_type()
        assert len(object_type.properties) == 3
        prop_names = [prop.code for prop in object_type.properties]
        assert prop_names == ["$NAME", "ALIAS", "$STORAGE.STORAGE_VALIDATION_LEVEL"]

        # 3 properties in this `ObjectType`
        object_type = generate_object_type_longer()
        assert len(object_type.properties) == 4
        prop_names = [prop.code for prop in object_type.properties]
        assert prop_names == [
            "SETTINGS",
            "$NAME",
            "ALIAS",
            "$STORAGE.STORAGE_VALIDATION_LEVEL",
        ]

    def test_setattr(self):
        """Test the method `__setattr__` from the class `ObjectType`."""
        object_type = generate_object_type()
        assert "name" in object_type._property_metadata
        assert isinstance(
            object_type._property_metadata["name"], PropertyTypeAssignment
        )
        assert object_type.name == "Mandatory name"

        # Valid type
        object_type.name = "Test Object"
        assert object_type.name == "Test Object" and isinstance(object_type.name, str)

        object_type.storage_storage_validation_level = "BOX"
        assert object_type.storage_storage_validation_level == "BOX" and isinstance(
            object_type.storage_storage_validation_level, str
        )

        # Invalid types
        with pytest.raises(
            TypeError, match="Invalid type for 'name': Expected str, got int"
        ):
            object_type.name = 42
        with pytest.raises(
            TypeError, match="Invalid type for 'name': Expected str, got bool"
        ):
            object_type.name = True

        with pytest.raises(
            ValueError,
            match="42 for storage_storage_validation_level is not in the list of allowed terms for vocabulary.",
        ):
            object_type.storage_storage_validation_level = 42
        with pytest.raises(
            ValueError,
            match="Test Storage for storage_storage_validation_level is not in the list of allowed terms for vocabulary.",
        ):
            object_type.storage_storage_validation_level = "Test Storage"

    @pytest.mark.parametrize(
        "code, result",
        [
            ("$DEFAULT_COLLECTION_VIEWS", True),
            ("VOCABULARY_NOT_FOUND", False),
        ],
    )
    def test_get_vocabulary_class(self, code, result):
        """Test the name conversion for `VocabularyType`."""
        vocab_path = "tests/data/metadata/example_vocabulary.py"
        object_type = generate_object_type()

        vocabulary_class = object_type.get_vocabulary_class(code, vocab_path)
        assert (vocabulary_class is not None) is result


class TestVocabularyType:
    def test_model_validator_after_init(self):
        """Test the method `model_validator_after_init` from the class `VocabularyType`."""
        vocabulary_type = generate_vocabulary_type()
        assert len(vocabulary_type.terms) == 2
        term_names = [term.code for term in vocabulary_type.terms]
        assert term_names == ["OPTION_A", "OPTION_B"]


def test_generate_object_id():
    """Test the function `generate_object_id`."""
    object_type = generate_object_type()
    object_id = generate_object_id(object_type=object_type)
    assert object_id.startswith("MOCKOBJTYPE")
    assert len(object_id) == 19  # 11 characters for prefix + 8 uuid digits


def test_generate_object_relationship_id():
    object_1 = generate_object_type()
    object_2 = generate_object_type()
    relationship_id = generate_object_relationship_id(
        parent_id=generate_object_id(object_type=object_1),
        child_id=generate_object_id(object_type=object_2),
    )
    ids = relationship_id.split(">>")
    assert len(ids) == 2
    for id in ids:
        assert id.startswith("MOCKOBJTYPE")
        assert len(id) == 19


class TestCollectionType:
    def test_repr(self):
        """Test the method `__repr__` from the class `CollectionType`."""
        collection = CollectionType()
        assert (
            repr(collection) == "CollectionType(attached_objects={}, relationships={})"
        )

        obj_id = collection.add(generate_object_type())
        assert (
            repr(collection)
            == f"CollectionType(attached_objects={{'{obj_id}': Mandatory name:MockedObjectType(name='Mandatory name')}}, relationships={{}})"
        )

        obj_id_2 = collection.add(generate_object_type())
        relation_id = collection.add_relationship(obj_id, obj_id_2)
        assert (
            repr(collection)
            == f"CollectionType(attached_objects={{'{obj_id}': Mandatory name:MockedObjectType(name='Mandatory name'), "
            f"'{obj_id_2}': Mandatory name:MockedObjectType(name='Mandatory name')}}, relationships={{'{relation_id}': ('{obj_id}', '{obj_id_2}')}})"
        )

    def test_add(self):
        """Test the method `add` from the class `CollectionType`."""
        collection = CollectionType()

        with pytest.raises(
            TypeError,
            match="Expected an ObjectType instance, got `MockedVocabularyType`",
        ):
            entity_id = collection.add(generate_vocabulary_type())

        with pytest.raises(
            ValueError,
            match="The following mandatory fields are missing for ObjectType 'MockedObjectType': name",
        ):
            entity_id = collection.add(generate_object_type_miss_mandatory())

        entity_id = collection.add(generate_object_type())
        assert entity_id.startswith("MOCKOBJTYPE")
        assert entity_id in collection.attached_objects.keys()

    def test_remove(self):
        """Test the method `remove` from the class `CollectionType`."""
        collection = CollectionType()
        entity_type = generate_object_type()
        entity_id = collection.add(entity_type)

        with pytest.raises(
            ValueError,
            match="You must provide an `object_id` to remove the object type from the collection.",
        ):
            collection.remove("")

        with pytest.raises(
            ValueError,
            match="Object with ID 'NOT_AN_ENTITY_ID' does not exist in the collection.",
        ):
            collection.remove("NOT_AN_ENTITY_ID")

        collection.remove(entity_id)
        assert entity_id not in collection.attached_objects

    def test_add_relationship(self):
        collection = CollectionType()
        parent = generate_object_type()
        child = generate_object_type()

        with pytest.raises(
            ValueError,
            match="Both `parent_id` and `child_id` must be provided to add a relationship.",
        ):
            collection.add_relationship("", "")

        parent_id = collection.add(parent)
        child_id = collection.add(child)

        with pytest.raises(
            ValueError,
            match="Both `parent_id` and `child_id` must be assigned to objects attached to the collection.",
        ):
            collection.add_relationship(parent_id, "NOT_A_CHILD_ID")

        relationship_id = collection.add_relationship(parent_id, child_id)
        assert relationship_id.startswith("MOCKOBJTYPE")
        ids = relationship_id.split(">>")
        assert len(ids) == 2
        assert ids[0] == parent_id
        assert ids[1] == child_id
