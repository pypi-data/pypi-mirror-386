import pytest
import os
import tempfile
import time
from nbitk.config import Config
from nbitk.Services.Galaxy.TaxonValidator import TaxonValidator
from nbitk.Services.Galaxy.BLASTN import BLASTNClient
from pathlib import Path


@pytest.fixture(scope="session")
def config():
    """Create a basic config for tests"""
    config = Config()
    config.config_data = {}
    config.initialized = True
    return config


@pytest.fixture(autouse=True)
def check_galaxy_key():
    """Verify Galaxy API key is available"""

    if not os.environ.get('GALAXY_API_KEY'):
        pytest.skip("GALAXY_API_KEY not set in environment")

@pytest.fixture
def test_data():
    """Create BCDM data for testing"""
    return [
        {
            'id': '1',
            'identification': 'Apidae',
            'identification_rank': None,
            'nuc': 'AATATTATACTTTATTTTTGCTATATGATCAGGAATAATTGGTTCATCTATAAGATTATTAATTCGAATAGAATTAAGACATCCAGGTATATGAATTAATAATGATCAAATTTATAATTCTTTAGTAACAAGACATGCATTTTTAATAATTTTTTTTATAGTTATACCTTTTATAATTGGTGGATTTGGAAATTATCTAATTCCATTAATATTAGGATCCCCAGATATAGCTTTTCCTCGAATAAATAATATTAGATTTTGACTTCTACCTCCATCATTATTCATATTATTATTAAGAAATATATTTACACCTAATGTAGGTACAGGATGAACTGTATATCCTCCTTTATCTTCTTATTTATTTCATTCATCACCTTCAATTGATATTGCAATCTTTTCTTTACATATATCAGGAATCTCTTCAATTATTGGATCATTAAATTTTATCGTTACTATTTTATTAATAAAAAATTTTTCATTAAATTATGATCAAATTAATTTATTTTCATGATCAGTATGTATTACAGTAATTTTATTAATTCTATCTTTACCAGTATTAGCCGGCGCAATTACTATATTATTATTTGATCGAAATTTTAATACTTCATTTTTTGACCCAATAGGAGGAGGAGATCCAATCCTTTATCAACATTTATTT'
        },
        {
            'id': '2',
            'taxon': 'Apidae',
            'identification_rank': None,
            'nuc': 'ATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG'
        }
    ]

@pytest.fixture
def client(config):
    """Create a fresh client for each test"""
    client = TaxonValidator(config)
    yield client
    del client


def test_validate_records(client, test_data):
    """Test basic taxon validation search with default parameters"""
    result = client.validate_records(
        test_data,
        params = {'databases': [{"name": 'Genbank CO1', "version": "2023-11-15"}],
                  'max_target_seqs': 100, 'identity': 80.0, "task": BLASTNClient.BlastTask.MEGABLAST})
    query_config = client.query_config

    assert len(result) == 2
    assert result[0]['is_valid']
    assert result[1]['is_valid'] == False
    assert query_config is not None


def test_blast_records_and_validate(client, test_data):
    """Test basic taxon validation search with default parameters"""
    result = client.blast_records_and_validate_taxonomy(
        test_data,
        [{'name': 'Genbank CO1', 'version': '2023-11-15'}],
        80.0,
        BLASTNClient.BlastTask.BLASTN,
        100,
        fetch_ncbi_lineage=True
    )
    query_config = client.query_config

    assert len(result) == 2
    assert result[0]['is_valid']
    assert result[1]['is_valid'] == False
    assert query_config is not None

def test_run_blast_with_wait(client, test_data):
    result = client.blast_records(
        test_data,
        [{'name': 'Genbank CO1', 'version': '2023-11-15'}],
        80.0,
        BLASTNClient.BlastTask.BLASTN,
        100,
        wait_for_result=True
    )

    assert Path(result['blast_output_fasta']).exists()

    # parse the result files, extract is_valid etc..
    parsed_blast_result = client.map_blast_output_to_records(
        blast_output= result['blast_output_fasta'],
        records=test_data,
    )

    # validate the result
    result = client.validate_taxonomy(
        records_with_taxonomy = parsed_blast_result
    )

    
    query_config = client.query_config

    assert len(result) == 2
    assert result[0]['is_valid']
    assert result[1]['is_valid'] == False
    assert query_config is not None



def test_run_blast_with_wait_and_no_file_write(client, test_data):
    result = client.blast_records(
        test_data,
        [{'name': 'Genbank CO1', 'version': '2023-11-15'}],
        80.0,
        BLASTNClient.BlastTask.BLASTN,
        100,
        wait_for_result=True,
        params = {'no_file_write': True}
    )

    # parse the result files, extract is_valid etc..
    parsed_blast_result = client.map_blast_output_to_records(
        blast_output= result['blast_output_fasta'],
        records=test_data,
        is_string = True
    )

    # validate the result
    result = client.validate_taxonomy(
        records_with_taxonomy = parsed_blast_result
    )

    
    query_config = client.query_config

    assert len(result) == 2
    assert result[0]['is_valid']
    assert result[1]['is_valid'] == False
    assert query_config is not None



def test_run_blast_without_wait(client, test_data):
    job_details = client.blast_records(
        records = test_data,
        databases = [{'name': 'Genbank CO1', 'version': '2023-11-15'}],
        identity=80.0,
        task = BLASTNClient.BlastTask.BLASTN,
        max_target_seqs = 100,
        wait_for_result=False
    )
    query_config = client.query_config
    assert query_config is not None

    job_finished = False
    for i in range(20):
        job_details_state = client.get_job_details(job_details["job_id"])
        if job_details_state["state"] == "ok":
            job_finished = True
            break
        time.sleep(5)

    if not job_finished:
        raise ValueError("Job status is not 'completed', the job took too long time to complete.")

    temp_dir = tempfile.mkdtemp()
    client.download_blast_results(
        job_id=job_details["job_id"],
        output_directory=temp_dir,
        include_log_file=False,
        maxwait=5,
    )

    # parse the result files, extract is_valid etc..
    parsed_blast_result = client.map_blast_output_to_records(
        blast_output= Path(temp_dir) / f"{job_details['job_id']}_blast_hits.tsv",
        records=test_data,
    )

    # validate the result
    result = client.validate_taxonomy(
        records_with_taxonomy = parsed_blast_result
    )

    assert len(result) == 2
    assert result[0]['is_valid']
    assert result[1]['is_valid'] == False
