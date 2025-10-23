import pytest
from basyx.aas import model

from aas_standard_parser.aimc_parser import MappingConfiguration, SourceSinkRelation
import aas_standard_parser.aimc_parser as aimc_parser
from aas_standard_parser.utils import create_submodel_from_file


@pytest.fixture(scope="module")
def aimc_submodel() -> model.Property:
    # create a Submodel
    return create_submodel_from_file("tests/test_data/aimc_submodel.json")


def test_001_get_mapping_configuration_root_element(aimc_submodel: model.submodel):
    root_element = aimc_parser.get_mapping_configuration_root_element(aimc_submodel)

    assert root_element is not None
    assert root_element.id_short == "MappingConfigurations"


def test_002_get_mapping_configuration_elements(aimc_submodel: model.submodel):
    configuration_elements = aimc_parser.get_mapping_configuration_elements(
        aimc_submodel
    )

    assert configuration_elements is not None
    assert len(configuration_elements) == 1

    configuration_element = configuration_elements[0]
    assert isinstance(configuration_element, model.SubmodelElementCollection)

def test_003_parse_mapping_configuration_element(aimc_submodel: model.submodel):
    configuration_elements = aimc_parser.get_mapping_configuration_elements(
        aimc_submodel
    )

    configuration_element = configuration_elements[0]
    configuration = aimc_parser.parse_mapping_configuration_element(configuration_element)

    assert configuration is not None
    _check_interface_ref(configuration)
    _check_relations(configuration)
    _check_relations(configuration)

def test_004_parse_mapping_configurations(aimc_submodel: model.submodel):
    mapping_configurations = aimc_parser.parse_mapping_configurations(aimc_submodel)

    assert mapping_configurations is not None
    assert len(mapping_configurations.configurations) == 1
    assert len(mapping_configurations.aid_submodel_ids) == 1

    configuration = mapping_configurations.configurations[0]
    assert configuration.aid_submodel_id is not None
    assert configuration.aid_submodel_id in mapping_configurations.aid_submodel_ids
    assert configuration.aid_submodel_id == "https://fluid40.de/ids/sm/4757_4856_8464_1441"

    _check_interface_ref(configuration)
    _check_relations(configuration)
    _check_relations(configuration)

def _check_interface_ref(configuration: MappingConfiguration):
    assert configuration.interface_reference is not None

    interface_reference = configuration.interface_reference
    assert isinstance(interface_reference, model.ReferenceElement)
    assert interface_reference.id_short == "InterfaceReference"

    value = interface_reference.value
    assert isinstance(value, model.Reference)
    assert len(value.key) == 1

    key = value.key[0]
    assert key is not None
    assert key.value == "https://fluid40.de/ids/sm/4757_4856_8464_1442/Interface_MQTT"


def _check_relations(configuration: MappingConfiguration):
    assert len(configuration.source_sink_relations) > 0

    relation = configuration.source_sink_relations[0]
    assert relation is not None

    assert relation.source is not None
    assert relation.source_submodel_id == configuration.aid_submodel_id

    assert relation.sink is not None

    _check_relations_source(relation)
    _check_relations_sink(relation)
    _check_relation_methods(relation)

def _check_relations_source(relation: SourceSinkRelation):
    assert relation is not None

    assert isinstance(relation.source, model.ExternalReference)

    assert relation.source_property_name is not None
    assert relation.source_property_name == "HandlingC"

    assert relation.source_parent_path is not None
    assert len(relation.source_parent_path) == 5
    assert relation.source_parent_path[3] == "axes_position"

    assert relation.source_submodel_id is not None
    assert relation.source_submodel_id == relation.source.key[0].value

def _check_relations_sink(relation: SourceSinkRelation):
    assert relation is not None

    assert isinstance(relation.sink, model.ExternalReference)

    assert relation.sink_property_name is not None
    assert relation.sink_property_name == "HandlingC"

    assert relation.sink_parent_path is not None
    assert len(relation.sink_parent_path) == 2
    assert relation.sink_parent_path[1] == "AxesPosition"

    assert relation.sink_submodel_id is not None
    assert relation.sink_submodel_id == relation.sink.key[0].value

def _check_relation_methods(relation: SourceSinkRelation):
    # test to_json methods
    source_json = relation.source_as_dict()
    assert source_json is not None
    assert "type" in source_json

    sink_json = relation.sink_as_dict()
    assert sink_json is not None
    assert "type" in sink_json
