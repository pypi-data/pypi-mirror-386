import os

import pytest

from nbitk.config import Config
from nbitk.Services.Galaxy.TaxonValidator import TaxonValidator
from nbitk.Services.Galaxy.BLASTN import BLASTNClient

@pytest.fixture
def galaxy_config():
    """
    Fixture to create a Galaxy configuration object.
    :return: A Config object with Galaxy settings.
    """
    config = Config()
    config.config_data = {
        'log_level': 'DEBUG',
    }
    config.initialized = True
    return config

@pytest.fixture(autouse=True)
def check_galaxy_key():
    """Verify Galaxy API key is available"""
    if not os.environ.get('GALAXY_API_KEY'):
        pytest.skip("GALAXY_API_KEY not set in environment")

@pytest.fixture
def records_dict():
    """
    Creates a dictionary of records as input to the TaxonValidator service.
    :return: A dictionary containing records.
    """
    return [
        {
            "identification_morphology_id": 7400,
            "nuc": "AACTTTATATTTTATTTTTGGTGCATGAGCTGGTATAGTAGGTACCTCCCTTAGTATCTTAGTACGAGCTGAATTAGGGCATCCTGGGGCATTAATTGGTGATGATCAAATTTATAATGTAATTGTTACTGCTCATGCTTTTGTAATGATTTTCTTTATAGTTATACCTATTTTAATTGGAGGTTTTGGAAATTGATTAGTTCCTTTAATATTAGGGGCCCCTGATATAGCTTTCCCTCGAATAAATAATATAAGATTTTGATTATTACCCCCTTCTTTAACTTTATTATTAGCTAGCTCAATTGTAGAAAACGGGGCTGGAACAGGGTGAACTGTTTACCCACCTTTAGCATCAGGAATTGCTCATGCAGGGGCTTCTGTTGATTTAGCTATTTTTTCTTTACATTTAGCTGGAGTATCTTCTATTTTAGGTGCAGTAAATTTTATTACTACAGTAATTAATATACGATCTAATGGAATTACTTTAGATCGAATACCATTATTTGTATGATCAGTAGTTATTACGGCTGTATTATTACTATTATCTTTACCTGTATTAGCTGGTGCCATTACTATATTATTAACTGACCGAAATTTAAATACATCTTTCTTTGACCCAGCTGGTGGAGGAGATCCTATTTTATATCAACATTTATTC",
            "identification": "Chironomidae",
            "consensus_sequence_id": 48204,
            "catalog_number": "RMNH.5128206",
            "material_entity_id": 21229,
            "local_id": "7400",
            "batch_id": 0,
            "identification_rank": None
        },
        {
            "identification_morphology_id": 21425,
            "nuc": "AACTTTATACTTTTTATTTGGTATTTGATCAGGTATAATTGGATCATCTCTTAGAATTTTGATTCGATTAGAATTAAGACAAATTAATTCTATTATTAATAATAATCAATTATATAATGTAATTGTTACAATTCATGCTTTTATTATAATTTTTTTTATAACTATACCAATTGTAATTGGTGGATTTGGAAATTGATTAATTCCTATAATAATAGGATGTCCTGATATATCATTTCCACGTTTAAATAATATTAGATTTTGATTACTACCTCCATCATTAATAATAATAATTTGTAGATTTTTAATTAATAATGGAACAGGAACAGGATGAACAATTTATCCCCCTTTATCAAACAATATTGCACATAATAACATTTCAGTTGATTTAACTATTTTTTCTTTACATCTAGCAGGAATCTCATCAATTTTAGGAGCAATTAATTTTATTTGTACAATTCTTAATATAATACCAAACAATATAAAATTAAATCAAATTCCTCTTTTTCCTTGATCAATTTTAATTACAGCTATTTTACTAATTTTATCTTTACCAGTTTTAGCTGGTGCCATTACAATACTTTTAACTGATCGTAATTTAAATACATCATTTTTTGATCCAGCAGGAGGAGGAGATCCTATTTTATATCAACATTTATTT",
            "identification": "Dolichopodidae",
            "consensus_sequence_id": 14595,
            "catalog_number": "RMNH.5164997",
            "material_entity_id": 366,
            "local_id": "21425",
            "batch_id": 0,
            "identification_rank": None
        },
        {
            "identification_morphology_id": 3043,
            "nuc": "AACTTTATATTTTATTTTTGGAATTTGGGCTGGAATAGTTGGAACTTCCCTTAGTTTACTAATTCGAGCAGAATTAGGAAATCCTGGATCTTTAATTGGAGATGATCAAATTTATAATACCATTGTAACAGCTCATGCTTTCATTATAATTTTTTTTATAGTTATACCCATTATAATTGGGGGATTTGGAAATTGATTAATTCCTTTAATATTAGGAGCTCCTGATATAGCTTTCCCTCGTATAAATAATATAAGTTTTTGACTCCTTCCCCCCTCATTAACATTATTAATTTCAAGAAGAATTGTAGAAAATGGAGCAGGTACTGGATGAACTGTTTATCCCCCACTTTCATCTAACATTGCCCATGGAGGAAGTTCTGTTGATTTAGCTATTTTTTCCCTTCATTTAGCTGGAATTTCCTCAATTTTAGGAGCTATTAATTTTATTACAACTATTATTAATATACGACTTAATAATATATCTTTTGATCAAATACCTTTATTTGTTTGAGCTGTAGGAATCACAGCATTTCTTTTACTTCTCTCTCTACCTGTTTTAGCTGGAGCTATTACAATACTTCTTACAGATCGTAATTTAAATACTTCCTTTTTTGACCCTGCAGGAGGAGGAGATCCTATTTTATATCAACATTTATTT",
            "identification": "Notodontidae",
            "consensus_sequence_id": 40601,
            "catalog_number": "RMNH.5113469",
            "material_entity_id": 7889,
            "local_id": "3043",
            "batch_id": 0,
            "identification_rank": None
        },
    ]


def test_taxon_validator(galaxy_config, records_dict):
    """
    Test the TaxonValidator service client.
    """
    config = galaxy_config

    # Now we instantiate the service client:
    tv = TaxonValidator(config)
    result = tv.validate_records(records_dict, params = {'databases': [{"name": 'Genbank CO1', "version": "2023-11-15"}], 'max_target_seqs': 100, 'identity': 80.0,  "task":BLASTNClient.BlastTask.MEGABLAST})
    assert result is not None, "Validation result should not be None"
