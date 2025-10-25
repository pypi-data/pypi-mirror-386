import uuid
from typing import Optional, List, Dict, Any
from collections.abc import Callable
from io import StringIO
import logging
import tempfile
import pandas as pd
import numpy as np
from nbitk.Services.Galaxy.BLASTN import BLASTNClient
from nbitk.config import Config
from Bio import SeqIO, Entrez
from Bio.SeqRecord import SeqRecord
from Bio.Seq import Seq
import time


class TaxonValidator(BLASTNClient):
    """
    Client for validating taxonomic assignments of DNA sequences using BLAST. This client
    is tailored to the use case where barcode records stored in the BioCloud DNA domain
    are validated in small batches against a reference database. The validation consists
    of a check to see whether the putative taxon (note: we assume this is the family name)
    is present in the BLAST results. The results are attached to the input records for
    further analysis. The taxonomic validation function can be replaced, making it possible
    to run a custom validation algorithm. BLAST (run_blast) and taxonomic Validation
     (validate_taxonomy) can be executed interdependently or sequentially
     (blast_records_and_validate_taxonomy).
    """

    def __init__(self, config: Config, logger: Optional[logging.Logger] = None) -> None:
        """
        Initialize the TaxonValidator client. This constructor delegates to the BLASTNClient
        constructor, which in turn initializes the Galaxy connection and tool. Consult the
        BLASTNClient documentation and that of the AbstractClient for more information.
        :param config: NBITK Config object containing Galaxy connection settings
        :param logger: Optional logging.logger instance. If None, creates one using the class name
        """
        super().__init__(config, logger)
        # Set the Entrez email to the specified address
        Entrez.email = "bioinformatics@naturalis.nl"
        self.taxonomy_cache = {}  # Cache for taxonomy lookups to minimize API calls
        self.query_config = {}

    def validate_taxonomy(
        self,
        records_with_taxonomy: list[dict],
        comparison_fn: Callable[[str, str, list[dict]], bool] = None,
    ) -> list[dict]:
        """

        :param records_with_taxonomy: identification: Expected taxon (note: we now assume this is the family name)
        :param comparison_fn: the function to use to validation the taxonomy, the default comparison function is:

            def default_comp_fn(input_taxon, input_rank, best_hits) -> bool:
                for hit in best_hits:
                    if not hit['lineage']:
                        continue
                    lineage = {k: v for k, v in hit['lineage'].items() if k != "taxon_id"}
                    if lineage and input_taxon in lineage.values():
                        return True
                return False

        :return: the list of records, and for each record a flag "is_valid" corresponding
         to the output of the comparison function.
        """

        def default_comp_fn(input_taxon, input_rank, best_hits) -> bool:
            for hit in best_hits:
                if not hit["lineage"]:
                    continue
                lineage = {k: v for k, v in hit["lineage"].items() if k != "taxon_id"}
                if lineage and input_taxon in lineage.values():
                    return True
            return False

        comparison_fn = comparison_fn if comparison_fn else default_comp_fn

        for i, rec in enumerate(records_with_taxonomy):
            try:
                rec["is_valid"] = False
                if not rec["best_hits"] or not rec["identification"]:
                    continue
                rec["is_valid"] = comparison_fn(
                    rec["identification"], rec["identification_rank"], rec["best_hits"]
                )
            except KeyError as e:
                if "id" in rec:
                    rec_id = rec["id"]
                elif "local_id" in rec:
                    rec_id = rec["local_id"]
                else:
                    rec_id = "NO ID"
                self.logger.error(f"Invalid record (#{i}) with ID: {rec_id}: {str(e)}")
                raise e

        return records_with_taxonomy

    def blast_records(
        self,
        records: List[Dict[str, Any]],
        databases: List[dict[str, str]],
        identity: float,
        task: BLASTNClient.BlastTask,
        max_target_seqs: int,
        params: dict = None,
        wait_for_result: bool = True,
    ) -> str | Dict[str, Any]:
        """
        The resulting file is uploaded to Galaxy for BLAST analysis. The results
        are joined with the input by way of the local_id.

        :param records: List of records. Each record is a dictionary with the following keys:
            - local_id or id: Locally unique identifier
            - nuc: Nucleotide sequence
        :param databases: list of BLAST databases to use (see nbitk.Services.Galaxy.BLASTN.run_blast() documentation)
        :param identity: BLAST identity to use (see nbitk.Services.Galaxy.BLASTN.run_blast() documentation)
        :param task: BLAST algorithm to use (see nbitk.Services.Galaxy.BLASTN.run_blast() documentation)
        :param max_target_seqs: number of hits per query sequence (see nbitk.Services.Galaxy.BLASTN.run_blast() documentation)
        :param params: Optional parameters for the BLAST analysis. The parameters are passed
            directly to the BLASTNClient.run_blast method. The parameters are tool-specific
            and can be found in the BLASTNClient documentation.
        :param wait_for_result: if True returns immediately the Galaxy job ID instead of
                               the blast result
        :return: job id or BLAST result as dict.
        """

        # ensure record_id are unique
        rec_id = "local_id" if "local_id" in records[0] else "id"
        assert len(set(r[rec_id] for r in records)) == len(
            records
        ), f"Invalid list of records, some ids are found duplicated."

        # Create SeqRecord objects and write to FASTA file
        self.logger.info(f"Going to validate {len(records)} records")
        fasta_filename = self._bcdm2fasta(records)

        # check BLAST tool params
        if params is not None and "output_format" in params:
            assert (
                params["output_format"] == BLASTNClient.OutputFormat.CUSTOM_TAXONOMY
            ), f"Invalid param 'output_format' value must be {BLASTNClient.OutputFormat.CUSTOM_TAXONOMY}"
        if params is not None and "taxonomy_method" in params:
            assert (
                params["taxonomy_method"] == BLASTNClient.TaxonomyMethod.DEFAULT
            ), f"Invalid param 'taxonomy_method' value must be {BLASTNClient.TaxonomyMethod.DEFAULT}"

        # Run BLAST on the Galaxy
        self.logger.info(f"Running BLAST on {fasta_filename}")
        if params is not None:
            result_or_job_id = self.run_blast(
                fasta_filename,
                databases,
                identity,
                task,
                max_target_seqs,
                wait_for_result=wait_for_result,
                **params,
            )
        else:
            result_or_job_id = self.run_blast(
                fasta_filename,
                databases,
                identity,
                task,
                max_target_seqs,
                wait_for_result=wait_for_result,
            )

        # Update config object
        self.query_config = {
            "maxh": max_target_seqs,
            "mi": identity,
            "mo": None,
            "order": None,
            "db": databases,
        }

        return result_or_job_id

    def blast_records_and_validate_taxonomy(
        self,
        records: List[Dict[str, Any]],
        blast_databases: list[dict],
        blast_identity: int,
        blast_task: BLASTNClient.BlastTask,
        blast_max_target_seqs: int,
        fetch_ncbi_lineage: bool,
    ):
        """
        Validate a list of sequence (records) and their expected taxon (identification)
        by running BLAST remotely on Galaxy, wait for the result, and compare the BLAST hits taxonomy
        against the records identification.
        :param records: List of records. Each record is a dictionary with the following keys:
            - 'id': Locally unique identifier
            - identification: Expected taxon to be in the blast hits
            - nuc: Nucleotide sequence
        :param blast_databases: see nbitk.Services.Galaxy.BLASTN.run_blast() documentation
        :param blast_identity: see nbitk.Services.Galaxy.BLASTN.run_blast() documentation
        :param blast_task: see nbitk.Services.Galaxy.BLASTN.run_blast() documentation
        :param blast_max_target_seqs: see nbitk.Services.Galaxy.BLASTN.run_blast() documentation
        :param fetch_ncbi_lineage: Use NCBI Entrez to fetch the latest NCBI taxonomy from the taxon_id in the BLAST hits.
                                   See TaxonValidator.get_taxonomic_lineage() documentation.
        :return: the list of records, and for each record a flag "is_valid" corresponding
         to the output of the comparison function. See TaxonValidation.validate_taxonomy() documentation.
        """
        # first BLAST the records
        blast_result = self.blast_records(
            records,
            blast_databases,
            blast_identity,
            blast_task,
            blast_max_target_seqs,
            wait_for_result=True,
        )

        # then map the blast output to the input record
        record_with_mapped_hits = self.map_blast_output_to_records(
            blast_output=blast_result["blast_output_fasta"],
            records=records,
            is_string=False,
            fetch_ncbi_lineage=fetch_ncbi_lineage,
        )

        # Then validate the taxonomy,
        return self.validate_taxonomy(record_with_mapped_hits)

    # keep for compatibility
    def validate_records(
        self,
        records: List[Dict[str, Any]],
        params: dict,
    ) -> List[Dict[str, Any]]:
        """
        See TaxonValidator.blast_records_and_validate_taxonomy documentation
        """
        return self.blast_records_and_validate_taxonomy(
            records,
            params["databases"],
            params["identity"],
            BLASTNClient.BlastTask.BLASTN,
            params["max_target_seqs"],
            fetch_ncbi_lineage=True,
        )

    def get_taxonomic_lineage(self, taxon_id: str) -> Dict[str, str]:
        """
        Retrieve the complete taxonomic lineage for a given NCBI taxon ID.
        Uses caching to reduce API calls to NCBI.

        Example:
        {
            "scientific_name": "Tomocerus sp. COONT866-09",
            "cellular_root": "cellular organisms",
            "domain": "Eukaryota",
            "clade": "Pancrustacea",
            "kingdom": "Metazoa",
            "phylum": "Arthropoda",
            "subphylum": "Hexapoda",
            "class": "Collembola",
            "order": "Entomobryomorpha",
            "superfamily": "Tomoceroidea",
            "family": "Tomoceridae",
            "genus": "Tomocerus",
            "species": "Tomocerus sp. COONT866-09",
            "taxon_id": "2555124"
        }

        :param taxon_id: The NCBI taxonomy ID
        :return: A dictionary with taxonomic ranks as keys and taxonomic names as values
        """
        # Check cache first
        if taxon_id in self.taxonomy_cache:
            self.logger.debug(f"Using cached taxonomy for ID {taxon_id}")
            return self.taxonomy_cache[taxon_id]

        self.logger.debug(f"Fetching taxonomy for ID {taxon_id}")
        taxonomy_dict = {}

        try:
            # Fetch the taxonomy record
            handle = Entrez.efetch(db="taxonomy", id=str(taxon_id), retmode="xml")
            records = Entrez.read(handle)
            handle.close()

            if not records or len(records) == 0:
                self.logger.warning(f"No taxonomy record found for ID {taxon_id}")
                return taxonomy_dict

            record = records[0]

            # Get the scientific name (usually species name)
            taxonomy_dict["scientific_name"] = record.get("ScientificName", "")

            # Extract lineage information from LineageEx which contains detailed rank information
            if "LineageEx" in record:
                for entry in record["LineageEx"]:
                    if "Rank" in entry and "ScientificName" in entry:
                        rank = entry["Rank"]
                        name = entry["ScientificName"]
                        if rank != "no rank":  # Skip entries without a specific rank
                            taxonomy_dict[rank] = name

            # The current taxon's rank might not be in LineageEx, so add it separately
            if "Rank" in record and record["Rank"] != "no rank":
                taxonomy_dict[record["Rank"]] = record["ScientificName"]

            # Add the taxon ID to the dictionary
            taxonomy_dict["taxon_id"] = taxon_id

            # Replace spaces in keys with underscores
            taxonomy_dict = {key.replace(" ", "_"): value for key, value in taxonomy_dict.items()}

            # Cache the result
            self.taxonomy_cache[taxon_id] = taxonomy_dict

            return taxonomy_dict

        except Exception as e:
            self.logger.error(f"Error retrieving taxonomy for ID {taxon_id}: {str(e)}")
            # Implement exponential backoff if getting rate-limited
            time.sleep(1)
            return taxonomy_dict

    @staticmethod
    def evalue_to_confidence(evalue, max_evalue=10.0):
        """
        Transform a BLAST E-value into a confidence score between 0 and 1.

        :param evalue: The E-value from BLAST results
        :param max_evalue: Maximum E-value to consider (higher values will be capped)
        :return: Confidence score between 0 and 1, where 1 represents maximum confidence
        """
        # Handle special cases
        if evalue is None or pd.isna(evalue):
            return 0.0

        # For E-value of 0, return maximum confidence
        if evalue == 0:
            return 1.0

        # Cap the E-value at the maximum
        evalue = min(float(evalue), max_evalue)

        # Exponential transformation, approaches 1 as E-value approaches 0
        k = 5.0 / max_evalue  # Controls the steepness of the curve
        return np.exp(-k * evalue)

    def map_blast_output_to_records(
        self,
        blast_output: str,
        records: List[Dict[str, Any]],
        is_string: bool = False,
        fetch_ncbi_lineage: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        The BLAST operation performed by Galaxy returns a tab-separated file with the results. For every input
        record, the operation can return zero or more results. This method parses the BLAST output file for each
        set of results corresponding with an input 'local_id'. If the expected taxon is found in any of the results,
        the record is marked as valid by setting the 'is_valid' field to True. If no results are found, the record
        is marked as invalid. The full results are attached to the record under the 'blast_results' key as a pandas
        data frame for further analysis. Furthermore, the 'timestamp' field is added to the record to indicate when
        the validation was performed.
        :param blast_output: The BLAST output file
        :param records: List of records. The records are dictionaries with at least one mandatory key:
            - id: record unique identifier, will be mapped to the Query ID column of the BLAST hits
        :param is_string: If True, the output parameter is treated as a string containing the BLAST results
            instead of a file path. Default is False.
        :param fetch_ncbi_lineage: Use NCBI Entrez to fetch the latest NCBI taxonomy from the taxon_id in the BLAST hits.
                                   By default, the methode use the taxonomy available in the hits table.
                                   See TaxonValidator.get_taxonomic_lineage() documentation.
        :return: Enriched records. The records are changed to include with one additional key:
            - best_hits: List of dictionaries containing the best BLAST hit data (ties included)
                Each blast hit is a dict with the followings keys:
                    - blast_hit_id: unique BLAST HIT ID,
                    - sequence_id: Subject accession in the ref library,
                    - source: source ref library, e.g. GENBANK,
                    - coverage: hit.Coverage,
                    - identity_percentage: hit.Identity_percentage,
                    - evalue: E value,
                    - bitscore: bitscore,
                    - taxon_id: Tax ID from the ref library,
                    - confidence: see TaxonValidator.evalue_to_confidence,
                    - lineage: dict of taxon and rank
        """
        self.logger.debug(f"Parsing BLAST output file {blast_output}")

        # Accommodate both file path and string input for testing
        if is_string:
            df = pd.read_csv(StringIO(blast_output), sep="\t", dtype=str)
        else:
            df = pd.read_csv(blast_output, sep="\t", dtype=str)

        if not fetch_ncbi_lineage:
            # check that the lineage is available in the hit table
            # two more columns should be present: '#Source' and '#Taxonomy'
            # The #Taxonomy column should be formatted as follows:
            #     kingdom   / phylum     / class   / order   / family         / genus       / species
            # e.g. Eukaryota / Arthropoda / Insecta / Diptera / Ptychopteridae / Ptychoptera / Ptychoptera minuta
            assert "#Taxonomy" in df.columns

        # Convert numerical columns to appropriate data types
        numeric_cols = ["#Identity percentage", "#Coverage", "#evalue", "#bitscore"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Rename columns first
        df.columns = [c.replace(" ", "_").replace("#", "") for c in df.columns]

        # Then group by query ID
        grouped = dict(tuple(df.groupby("Query_ID")))

        # Process records
        for seq_dict in records:
            local_id = seq_dict["local_id"] if "local_id" in seq_dict else seq_dict["id"]
            seq_dict["best_hits"] = []
            # seq_dict["blast_results"] = None
            blast_rows = grouped.get(local_id)

            if blast_rows is None or blast_rows.empty:
                continue

            # Use itertuples to significantly enhance speed
            for hit in blast_rows.itertuples(index=False):
                taxon_id = hit.Subject_Taxonomy_ID
                if not taxon_id:
                    lineage = None
                else:
                    if fetch_ncbi_lineage:
                        lineage = self.get_taxonomic_lineage(taxon_id)
                    else:
                        lineage = dict(
                            zip(
                                [
                                    "kingdom",
                                    "phylum",
                                    "class",
                                    "order",
                                    "family",
                                    "genus",
                                    "species",
                                ],
                                [e.strip() for e in hit.Taxonomy.split(" / ")],
                            )
                        )
                        lineage["taxon_id"] = taxon_id
                        lineage["scientific_name"] = lineage["species"]

                hit_dict = {
                    "blast_hit_id": str(uuid.uuid4()),
                    "sequence_id": hit.Subject_accession,
                    "source": hit.Source,
                    "coverage": hit.Coverage,
                    "identity_percentage": hit.Identity_percentage,
                    "evalue": hit.evalue,
                    "bitscore": hit.bitscore,
                    "taxon_id": taxon_id,
                    "confidence": self.evalue_to_confidence(hit.evalue),
                    "lineage": lineage,
                }

                seq_dict["best_hits"].append(hit_dict)

        return records

    def _bcdm2fasta(self, records: List[Dict[str, Any]]) -> str:
        """
        Convert a list of records to a temporary FASTA file. In this operation, the
        'nuc' key in each record is expected to contain the nucleotide sequence, and
        the 'local_id' or 'id' key is expected to contain a locally unique identifier. The
        resulting FASTA file will have the local_id as the header and the nucleotide
        sequence as the body. No other keys in the records or values will be used.
        :param records: List of records
        :return: Name of the temporary FASTA file
        """
        self.logger.debug(f"Converting {len(records)} records to FASTA")

        # Create a list of SeqRecord objects
        seq_records = []
        for i, seq_dict in enumerate(records):
            try:
                sequence = Seq(seq_dict["nuc"])
                record = SeqRecord(
                    seq=sequence,
                    id=seq_dict["local_id"] if "local_id" in seq_dict else seq_dict["id"],
                    description="",  # Empty description to keep the FASTA header clean
                )
                seq_records.append(record)
            except KeyError as e:
                self.logger.error(f"Missing key in record #{i}")
                self.logger.error(str(e))
                raise e

        # Create a temporary file with .fasta extension
        temp_fasta = tempfile.NamedTemporaryFile(suffix=".fasta", delete=False)

        # Write records to the temporary FASTA file
        SeqIO.write(seq_records, temp_fasta.name, "fasta")
        return temp_fasta.name
