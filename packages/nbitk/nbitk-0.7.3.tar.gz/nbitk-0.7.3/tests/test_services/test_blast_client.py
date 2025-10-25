import pytest
import os
import tempfile
from pathlib import Path
from nbitk.config import Config
import sys

from nbitk.Services.Galaxy.BLASTN import BLASTNClient
from bioblend.galaxy.datasets import TimeoutException


@pytest.fixture(scope="session")
def config():
    """Create a basic config for tests"""
    config = Config()
    config.config_data = {"galaxy_domain": "https://galaxy.naturalis.nl/"}
    config.initialized = True
    return config


@pytest.fixture(scope="session")
def test_files():
    """Create temporary FASTA files with test sequences"""
    # Valid ITS sequence (Bombus terrestris)
    bombus_seq = """>Symbiotaphrina_buchneri_DQ248313
ACGATTTTGACCCTTCGGGGTCGATCTCCAACCCTTTGTCTACCTTCCTTGTTGCTTTGGCGGGCCGATGTTCGTTCTCGCGAACGACACCGCTGGCCTGACGGCTGGTGCGCGCCCGCC
AGAGTCCACCAAAACTCTGATTCAAACCTACAGTCTGAGTATATATTATATTAAAACTTTCAACAACGGATCTCTTGGTTCTGGCATCGATGAAGAACGCAGCGAAATGCGATAAGTAAT
GTGAATTGCAGAATTCAGTGAATCATCGAATCTTTGAACGCACATTGCGCCCCTTGGTATTCCGAGGGGCATGCCTGTTCGAGCGTCATTTCACCACTCAAGCTCAGCTTGGTATTGGGT
CATCGTCTGGTCACACAGGCGTGCCTGAAAATCAGTGGCGGTGCCCATCCGGCTTCAAGCATAGTAATTTCTATCTTGCTTTGGAAGTCTCCGGAGGGTTACACCGGCCAACAACCCCAA
TTTTCTATG
"""

    # Invalid sequence (random nucleotides)
    random_seq = """>Random_sequence
ATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG
ATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG"""

    # Create temp directory and files
    temp_dir = tempfile.mkdtemp()
    files = {}

    # Write valid sequence
    valid_path = Path(temp_dir) / "DQ248313.fa"
    with open(valid_path, "w") as f:
        f.write(bombus_seq)
    files["valid"] = str(valid_path)

    # Write invalid sequence
    invalid_path = Path(temp_dir) / "random.fa"
    with open(invalid_path, "w") as f:
        f.write(random_seq)
    files["invalid"] = str(invalid_path)

    yield files

    # Cleanup after all tests
    for filepath in files.values():
        try:
            os.remove(filepath)
        except OSError:
            pass
    try:
        os.rmdir(temp_dir)
    except OSError:
        pass


@pytest.fixture(autouse=True)
def check_galaxy_key():
    """Verify Galaxy API key is available"""
    if not os.environ.get("GALAXY_API_KEY"):
        pytest.skip("GALAXY_API_KEY not set in environment")


@pytest.fixture
def client(config):
    """Create a fresh client for each test"""
    client = BLASTNClient(config)
    yield client
    del client


def test_basic_its_search(client, test_files):
    """Test basic ITS search with default parameters"""
    result = client.run_blast(
        input_file=test_files["valid"],
        databases=[{"name": "UNITE", "version": ""}],
        task=BLASTNClient.BlastTask.BLASTN,
        identity=80.0,
        max_target_seqs=1,
    )

    assert "blast_output_fasta" in result
    output_file = result["blast_output_fasta"]
    assert os.path.exists(output_file)

    # Verify the content is tabular
    with open(output_file) as f:
        first_line = f.readline().strip()
        assert "\t" in first_line


def test_custom_parameters(client, test_files):
    """Test CO1 search with custom parameters"""
    result = client.run_blast(
        input_file=test_files["valid"],
        databases=[{"name": "UNITE", "version": ""}],
        task=BLASTNClient.BlastTask.BLASTN,
        max_target_seqs=5,
        identity=95.0,
        coverage=75.0,
        output_format=BLASTNClient.OutputFormat.TABULAR,
    )

    assert "blast_output_fasta" in result
    assert os.path.exists(result["blast_output_fasta"])


def test_do_not_wait_blast(client, test_files):
    """Test running blast without waiting"""
    # with pytest.raises(DatasetStateException):
    job_details = client.run_blast(
        input_file=test_files["valid"],
        databases=[{"name": "UNITE", "version": ""}],
        task=BLASTNClient.BlastTask.BLASTN,
        max_target_seqs=5,
        identity=95.0,
        coverage=75.0,
        output_format=BLASTNClient.OutputFormat.TABULAR,
        wait_for_result=False,
    )

    temp_dir = tempfile.mkdtemp()
    # should break if you try to download while
    # the job is still running which indicated
    # not waiting did not work

    with pytest.raises(TimeoutException) as timeout:
        client.download_blast_results(
            job_id=job_details["job_id"],
            output_directory=Path(temp_dir),
            include_log_file=False,
            maxwait=5,
        )


def test_download_blast_result_with_wait(client, test_files):
    job_details = client.run_blast(
        input_file=test_files["valid"],
        databases=[{"name": "UNITE", "version": ""}],
        task=BLASTNClient.BlastTask.BLASTN,
        max_target_seqs=5,
        identity=95.0,
        coverage=75.0,
        output_format=BLASTNClient.OutputFormat.TABULAR,
        wait_for_result=True,
    )

    temp_dir = tempfile.mkdtemp()

    client.download_blast_results(
        job_id=job_details["job_id"], output_directory=temp_dir, include_log_file=False
    )
    downloaded_hits_file = Path(temp_dir) / f"{job_details['job_id']}_blast_hits.tsv"
    assert downloaded_hits_file.resolve().exists(), "downloading blast result did not work"


def test_invalid_sequence(client, test_files):
    """Test behavior with invalid/random sequence"""
    result = client.run_blast(
        input_file=test_files["invalid"],
        databases=[{"name": "UNITE", "version": ""}],
        output_format=BLASTNClient.OutputFormat.TABULAR,
        task=BLASTNClient.BlastTask.BLASTN,
        identity=97.0,
        max_target_seqs=1,
        wait_for_result=True,
    )

    assert "blast_output_fasta" in result
    assert os.path.exists(result["blast_output_fasta"])


def test_output_formats(client, test_files):
    """Test different output formats"""
    result = client.run_blast(
        input_file=test_files["valid"],
        databases=[{"name": "UNITE", "version": ""}],
        output_format=BLASTNClient.OutputFormat.TABULAR,
        task=BLASTNClient.BlastTask.BLASTN,
        identity=97.0,
        max_target_seqs=1,
        wait_for_result=True,
    )
    assert "blast_output_fasta" in result
    assert os.path.exists(result["blast_output_fasta"])


def test_taxonomy_methods(client, test_files):
    """Test different taxonomy methods"""
    result = client.run_blast(
        input_file=test_files["valid"],
        databases=[{"name": "UNITE", "version": ""}],
        output_format=BLASTNClient.OutputFormat.CUSTOM_TAXONOMY,
        taxonomy_method=BLASTNClient.TaxonomyMethod.DEFAULT,
        task=BLASTNClient.BlastTask.BLASTN,
        identity=97.0,
        max_target_seqs=1,
        wait_for_result=True,
    )
    assert "blast_output_fasta" in result
    assert os.path.exists(result["blast_output_fasta"])


@pytest.mark.xfail(reason="write_store endpoint not available or path incorrect")
def test_export_rocrate(client, test_files):
    """Test exporting results as RO-crate"""
    # Run a basic analysis
    client.run_blast(
        input_file=test_files["valid"],
        databases=[{"name": "UNITE", "version": ""}],
        output_format=BLASTNClient.OutputFormat.CUSTOM_TAXONOMY,
        taxonomy_method=BLASTNClient.TaxonomyMethod.DEFAULT,
        identity=97.0,
        max_target_seqs=1,
    )

    # Export as RO-crate
    with tempfile.NamedTemporaryFile(suffix=".rocrate.zip") as tmp:
        crate_path = client.export_history_as_rocrate(tmp.name)
        assert os.path.exists(crate_path)
        assert os.path.getsize(crate_path) > 0


if __name__ == "__main__":
    pytest.main()
