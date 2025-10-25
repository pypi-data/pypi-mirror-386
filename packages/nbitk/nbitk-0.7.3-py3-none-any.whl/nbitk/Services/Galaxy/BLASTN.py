from typing import Optional, List, Dict, Any, Union
from enum import Enum
import logging

from nbitk.Services.Galaxy.BaseToolClient import BaseToolClient
from nbitk.config import Config
import os
import ast


class BLASTNClient(BaseToolClient):

    class TaxonomyMethod(str, Enum):
        """
        Enumeration of supported taxonomy methods.
        """

        NONE = "none"
        DEFAULT = "default"
        GBIF = "GBIF"

    class BlastTask(str, Enum):
        """
        Enumeration of supported BLAST tasks.
        """

        BLASTN = "blastn"
        MEGABLAST = "megablast"

    class OutputFormat(str, Enum):
        """
        Enumeration of supported output formats.
        """

        CUSTOM_TAXONOMY = "custom_taxonomy"
        PAIRWISE = "0"
        TABULAR = "6"
        TEXT_ASN1 = "8"
        BLAST_ARCHIVE = "11"

    """
    Client for running BLASTN analyses through Galaxy.

    :param config: NBITK configuration object containing Galaxy connection settings
    :param logger: Optional logger instance. If None, creates one using the class name

    Examples:
        >>> from nbitk.config import Config
        >>> from nbitk.logger import get_formatted_logger
        >>>
        >>> # Initialize with config
        >>> config = Config()
        >>> config.load_config('config.yaml')
        >>>
        >>> # Create client
        >>> blast = BLASTNClient(config)
        >>>
        >>> # Run analysis with defaults (CO1 database, megablast)
        >>> results = blast.run_blast('sequences.fasta')
        >>>
        >>> # Export the history as RO-crate
        >>> blast.export_history_as_rocrate('my_analysis.rocrate.zip')
        >>>
        >>> # Run against custom database with specific parameters
        >>> custom_results = blast.run_blast(
        ...     'sequences.fasta',
        ...     user_database='mydb.fasta',
        ...     task=BlastTask.BLASTN,
        ...     identity=95.0
        ... )
    """

    def __init__(self, config: Config, logger: Optional[logging.Logger] = None) -> None:
        """
        Initialize the BLASTNClient object. This constructor does nothing more than specify the tool name,
        according to which the Galaxy tool is retrieved. The actual initialization of the Galaxy connection
        and tool is done in the BaseClient constructor. Consult the BaseClient documentation for more information.
        :param config: NBITK configuration object containing Galaxy connection settings
        :param logger: An optional logger instance. If None, a new logger is created using the class name
        """
        super().__init__(config, "Identify reads with blastn and find taxonomy", logger)

    def run_blast(
        self,
        input_file: str,
        databases: List[dict[str, str]],
        identity: float,
        task: BlastTask,
        max_target_seqs: int,
        output_format: OutputFormat = OutputFormat.CUSTOM_TAXONOMY,
        taxonomy_method: TaxonomyMethod = TaxonomyMethod.DEFAULT,
        coverage: float = 80.0,
        user_database: Optional[str] = None,
        no_file_write: bool = False,
        wait_for_result: bool = True,
    ) -> Dict[str, Any]:
        """
        Run BLASTN analysis with the given parameters.

        :param input_file: Path to input FASTA file
        :param databases: List of database names and versions to search against (ignored if
                          user_database is provided)
        :param identity: Identity percentage cutoff
        :param task: BLAST task type (blastn or megablast)
        :param max_target_seqs: Maximum number of BLAST hits per sequence
        :param output_format: Desired output format
        :param taxonomy_method: Method for taxonomy assignment
        :param coverage: Query coverage percentage cutoff
        :param user_database: Optional path to user-provided FASTA database
        :param no_file_write: If True, do not write output files to disk (for testing)
        :param wait_for_result: If True the method returns the Galaxy job ID
        :return: Dictionary containing paths to output files and the blast settings used or
                 the Galaxy job ID is wait_for_result is set to True
                 Dictionary output:
                 {
                    'blast_output_fasta': the name of the file containing the BLAST hits.
                                          The format is the one passed to "output_format".
                                          It is not a FASTA file!
                    'blast_tool_settings': the exact setting passed to the Galaxy tool.
                    'job_id': ID of the Galaxy job that has generated the result,
                    'log_output': the name of the file containing logging information
                }
        :raises RuntimeError: if job fails or input parameters are invalid

        Examples:
            >>> # Basic usage with defaults
            >>> # input FASTA, databases, and identify percentage must always be provided
            >>> result = client.run_blast(
            ...     'sequences.fasta',
            ...     [{'name': 'Genbank CO1', 'version': None}],
            ...     97.0,
            ...     BlastTask.BLASTN,
            ...     5
            ... )
            >>>print(result)
            {
                'blast_output_fasta': 'blast_output_fasta_7d026802d4760036.tsv',
                'blast_tool_settings': {
                    'database_type|database': ['UNITE'],
                    'database_type|type': 'local',
                    'identity': '97.0',
                    'input_type|input': {'values': [{'id': 'd94c3bcec4e8f2bb', 'src': 'hda'}]},
                    'input_type|type': 'fasta',
                    'max_target_seqs': '1',
                    'output_format|coverage': '80.0',
                    'output_format|output_format_type': 'custom_taxonomy',
                    'output_format|taxonomy_method': 'default',
                    'task': 'blastn'
               },
               'job_id': 'bd152c60036ed93a',
               'log_output': 'log_output_ffe08b319c9bbb48.log'
            }
            >>>
            >>> # Custom search against user database, "databases" is ignored
            >>> result = client.run_blast(
            ...     'query.fasta',
            ...     None,  # databases
            ...     95.0,  # identity
            ...     BlastTask.BLASTN, # algo
            ...     5, # max target seqs
            ...     user_database="custom_db.fasta",
            ... )
            >>>
            >>> # Search against multiple databases with custom taxonomy settings
            >>> result = client.run_blast(
            ...     input_file="query.fasta",
            ...     databases=[
            ...         {"name": "genbankco1", "version": None},
            ...         {"name": "genbank16S", "version": None}
            ...     ],
            ...     identity=97.0,
            ...     task=BlastTask.BLASTN,
            ...     max_target_seqs=100,
            ...     taxonomy_method=TaxonomyMethod.DEFAULT,
            ...     coverage=85.0,
            ...     output_format=OutputFormat.CUSTOM_TAXONOMY
            ... )
            >>>
            >>> # Run without waiting for result
            >>> submitted_job_details =  client.run_blast(
            ...     input_file='sequences.fasta',
            ...     databases=[{'name': 'Genbank CO1', 'version': None}],
            ...     identity=97.0,
            ...     task=BlastTask.BLASTN,
            ...     max_target_seqs=100,
            ...     wait_for_result=False
            ... )
            >>> print(submitted_job_details)
            {
                'create_time': '2025-10-24T07:36:50.376378',
                'exit_code': None,
                'galaxy_version': '25.0',
                'history_id': '9c55b454a95c687d',
                'job_id': 'ad39abf3e73ffe24',
                'model_class': 'Job',
                'state': 'new',
                'tool_id': 'toolshed.g2.bx.psu.edu/repos/duijker.d/naturalis_blast/blastn/1.3',
                'tool_version': '1.3',
                'update_time': '2025-10-24T07:36:50.417689'
            }
            >>> # Download blast results afterwards
            >>> client.download_blast_results(
            ...     job_id = submitted_job_details['job_id'],
            ...     output_directory = "directory/to/download/blast/results/"
            ... ) # see download_blast_results() below
        """
        history = self._ensure_history()

        # assert database and identity are correctly set
        if not isinstance(databases, list) or len(databases) == 0:
            raise ValueError(
                "'databases' key in params must be a non-empty list. e.g., [{'name': 'Genbank CO1', 'version': '2023-11-15'}]"
            )
        for i, db in enumerate(databases):
            if not isinstance(db, dict) or not "name" in db or not "version" in db:
                raise ValueError(
                    f"database at index #{i} key in params must be a dict. e.g., [{'name': 'Genbank CO1', 'version': '2023-11-15'}]"
                )

        assert (
            isinstance(identity, float) and 0 <= identity <= 100
        ), "'identity' must be a float value between 0 and 100"

        assert (
            isinstance(max_target_seqs, int) and max_target_seqs > 0
        ), "'max_target_seqs' must be a positive int value, greater than 0"

        # Upload input file
        self.logger.info(f"Uploading input file: {input_file}")
        file_upload_details = self._upload_file(
            file_path=input_file, file_type="fasta"  # TODO: this should be auto-detected
        )
        input_file_name = os.path.basename(input_file)
        assert (
            file_upload_details["outputs"][0]["name"] == input_file_name
        ), f"Uploaded file name {file_upload_details['outputs'][0]['name']} does not match input file name {input_file_name}"
        input_id = file_upload_details["outputs"][0]["id"]

        # Upload user database if provided
        # TODO: this is now ignored
        database_id = None
        if user_database:
            raise NotImplementedError("Option user_database not yet implemented")
            self.logger.info(f"Uploading user database: {user_database}")
            database_upload_details = self._upload_file(user_database, "fasta")
            # assert user database has been uploaded
            assert database_upload_details["outputs"][0]["name"] == os.path.basename(
                user_database
            ), f"Uploaded database name {database_upload_details['outputs'][0]['name']} does not match user database name {os.path.basename(user_database)}"
            database_id = database_upload_details["outputs"][0]["id"]
        else:
            # Prepare database list
            selected_databases = []
            for db_info in databases:
                db = db_info["name"]
                if db_info["version"]:
                    # Galaxy database names should follow this standard: "<name>" or "<name> (<version>)"
                    db += f" ({db_info['version']})"
                selected_databases.append(db)

        # Prepare tool parameters
        params = {
            "input_type|type": "fasta",
            "input_type|input": {"values": [{"id": input_id, "src": "hda"}]},
            "database_type|type": "local",
            "database_type|database": selected_databases,
            "task": task.value,
            "output_format|output_format_type": output_format.value,
            "output_format|taxonomy_method": taxonomy_method.value,
            "output_format|coverage": str(coverage),
            "identity": str(identity),
            "max_target_seqs": str(max_target_seqs),
        }

        # Run BLAST
        self.logger.info("Starting BLASTN analysis...")
        try:
            result = self._gi.tools.run_tool(history["id"], self._tool["id"], params)
            job_id = result["jobs"][0]["id"]

            if not wait_for_result:
                result["jobs"][0]['job_id'] = result["jobs"][0].pop("id")
                return result["jobs"][0]

            self._wait_for_job(job_id)

            # Collect outputs
            outputs = {}
            for output in result["outputs"]:
                if output["output_name"] == "log_output":

                    # Accommodate cases where client cannot write to temp files
                    if no_file_write:
                        outputs["log_output"] = self._download_result_content(output)
                    else:
                        outputs["log_output"] = self._download_result(output, "log")
                elif output["output_name"] == "blast_output_fasta":

                    if no_file_write:
                        outputs["blast_output_fasta"] = self._download_result_content(output)
                    else:
                        outputs["blast_output_fasta"] = self._download_result(output, "tsv")

            outputs["blast_tool_settings"] = params
            outputs["job_id"] = job_id
            return outputs

        except Exception as e:
            self.logger.error(f"BLASTN analysis failed: {str(e)}")
            raise

    def download_blast_results(
        self, job_id: str, output_directory: str, include_log_file: bool = False, maxwait=12000
    ):
        """
        Downloads BLAST results and optionally the log file from a Galaxy job.
            The downloaded files are affixed with the job ID.

            Args:
            job_id (str): The ID of the Galaxy job.
            output_directory (str): The directory to save the downloaded files.
            include_log_file (bool, optional): Whether to download the log file. Defaults to False.
            maxwait (int, optional): The maximum time to wait for the download to complete, in seconds. Defaults to 12000.

            Returns:
            dict: A dictionary containing the paths to the downloaded files.
            If `include_log_file` is False, the dictionary contains only the path to the blast taxonomy output.
            If `include_log_file` is True, the dictionary contains paths to both the blast taxonomy output and the log file, as well as the blast tool settings.

            Example:
            If include_log_file is True:
            {
                'blast_output_hits_path': 'output_directory/989a31ffbe94fd7b_blast_hits.tsv',
                'blast_tool_settings': {
                    'database_type|database': ['BOLD species only no duplicates'],
                    'database_type|type': 'local',
                    'identity': '97.0',
                    'input_type|input': {'values': [{'id': 1797, 'src': 'hda'}]},
                    'input_type|type': 'fasta',
                    'max_target_seqs': '1',
                    'output_format|coverage': '80.0',
                    'output_format|output_format_type': 'custom_taxonomy',
                    'output_format|taxonomy_method': 'default',
                    'task': 'blastn'
                    },
                'job_id': '989a31ffbe94fd7b',    
                'log_output_path': 'output_directory/989a31ffbe94fd7b_blast_logs.log'
        """

        # create the output directory
        os.makedirs(output_directory, exist_ok=True)

        job_details = self._gi.jobs.show_job(job_id, full_details=True)

        # extract job settings
        params = job_details["params"]

        blast_settings = {}
        for key, value in params.items():
            try:
                # Attempt to parse the value as a Python literal (e.g., dict, list, number)
                blast_settings[key] = ast.literal_eval(value)
            except (ValueError, SyntaxError):
                # If parsing fails, keep the original string value
                blast_settings[key] = value

        # Restructure the blast_settings to match the desired format
        blast_settings = {
            "input_type|type": blast_settings.get("input_type", {}).get("type"),
            "input_type|input": blast_settings.get("input_type", {}).get("input"),
            "database_type|type": blast_settings.get("database_type", {}).get("type"),
            "database_type|database": blast_settings.get("database_type", {}).get("database"),
            "task": blast_settings.get("task"),
            "output_format|output_format_type": blast_settings.get("output_format", {}).get(
                "output_format_type"
            ),
            "output_format|taxonomy_method": blast_settings.get("output_format", {}).get(
                "taxonomy_method"
            ),
            "output_format|coverage": blast_settings.get("output_format", {}).get("coverage"),
            "identity": blast_settings.get("identity"),
            "max_target_seqs": blast_settings.get("max_target_seqs"),
        }

        outputs_dict = {}
        for output in job_details["outputs"]:
            # download the log file
            if output == "log_output" and include_log_file is True:
                key = "log_output_path"
                filename = f"{job_id}_blast_logs.log"
            elif output == "blast_output_fasta":
                key = "blast_output_hits_path"
                filename = f"{job_id}_blast_hits.tsv"
            else: continue

            outputs_dict[key] = os.path.join(
                output_directory, filename
            )
            self._gi.datasets.download_dataset(
                dataset_id=job_details["outputs"][output]["id"],
                file_path=outputs_dict[key],
                use_default_filename=False,
                maxwait=maxwait,
            )
        # add settings
        outputs_dict["blast_tool_settings"] = blast_settings
        outputs_dict["job_id"] = job_id

        return outputs_dict
