"""Classes for parsing and validating submission metadata and files."""

from __future__ import annotations

import json
import logging
import subprocess
import typing
from collections.abc import Generator
from itertools import groupby
from os import PathLike
from pathlib import Path

from grz_pydantic_models.submission.metadata import get_accepted_versions
from grz_pydantic_models.submission.metadata.v1 import (
    ChecksumType,
    File,
    FileType,
    GrzSubmissionMetadata,
    LibraryType,
    ReadOrder,
    SequenceData,
    SequenceSubtype,
    SequencingLayout,
    load_thresholds,
)
from grz_pydantic_models.submission.metadata.v1 import File as SubmissionFileMetadata
from pydantic import ValidationError

from ..models.identifiers import IdentifiersModel
from ..progress import DecryptionState, EncryptionState, FileProgressLogger, ValidationState
from ..utils.checksums import calculate_sha256
from ..utils.crypt import Crypt4GH
from ..validation import UserInterruptException, run_grz_check
from ..validation.bam import validate_bam
from ..validation.fastq import validate_paired_end_reads, validate_single_end_reads

log = logging.getLogger(__name__)

S3_MAX_KEY_LENGTH = 1024
# length of uploaded prefix before LE-specified filepath
# e.g. len("123456789_2025-04-01_a70eb6ce/files/") == 36
UPLOADED_FILE_PREFIX_LENGTH = 36


class SubmissionMetadata:
    """Class for reading and validating submission metadata"""

    __log = log.getChild("SubmissionMetadata")

    def __init__(self, metadata_file: Path):
        """
        Load, parse and validate the metadata file.

        :param metadata_file: path to the metadata.json file
        :raises json.JSONDecodeError: if failed to read the metadata.json file
        :raises jsonschema.exceptions.ValidationError: if metadata does not match expected schema
        """
        self.file_path = metadata_file
        self.content = self._read_metadata(self.file_path)
        self._checksum = calculate_sha256(self.file_path, progress=False)

        self._files: dict | None = None

    @classmethod
    def _read_metadata(cls, file_path: Path) -> GrzSubmissionMetadata:
        """
        Load and parse the metadata file in JSON format.

        :param file_path: Path to the metadata JSON file
        :return: Parsed metadata as a dictionary
        :raises json.JSONDecodeError: if failed to read the metadata.json file
        """
        try:
            with open(file_path, encoding="utf-8") as jsonfile:
                metadata = json.load(jsonfile)
                try:
                    metadata_model = GrzSubmissionMetadata(**metadata)
                except ValidationError as ve:
                    cls.__log.error("Invalid metadata format in metadata file: %s", file_path)
                    raise SystemExit(ve) from ve
                return metadata_model
        except json.JSONDecodeError as e:
            cls.__log.error("Invalid JSON format in metadata file: %s", file_path)
            raise e

    @property
    def transaction_id(self) -> str:
        """
        The index case ID of this submission
        """
        return self.content.submission.tan_g

    @property
    def files(self) -> dict[Path, SubmissionFileMetadata]:
        """
        The files linked in the metadata.

        :return: Dictionary of `file_path` -> `SubmissionFileMetadata` pairs.
            Each `file_path` refers to the relative file path from the metadata.
        """
        if self._files is not None:
            return self._files

        submission_files = {}
        for donor in self.content.donors:
            for lab_data in donor.lab_data:
                if not lab_data.sequence_data:
                    continue
                for file_data in lab_data.sequence_data.files:
                    file_path = Path(file_data.file_path)
                    submission_files[file_path] = file_data

        self._files = submission_files
        return self._files

    def validate(self, identifiers: IdentifiersModel) -> Generator[str]:  # noqa: C901, PLR0912
        """
        Validates this submission's metadata (content).

        :return: Generator of errors
        """
        metadata_schema_version = self.content.get_schema_version()
        accepted_versions = get_accepted_versions()
        if metadata_schema_version not in accepted_versions:
            yield f"Metadata schema version {metadata_schema_version} is outdated. Currently accepting the following versions: {', '.join(accepted_versions)}"

        expected_grz_id, expected_le_id = identifiers.grz, identifiers.le
        if (submitted_grz_id := self.content.submission.genomic_data_center_id) != expected_grz_id:
            yield (
                f"Genomic data center identifier specified in the metadata.json ({submitted_grz_id}) "
                f"does not match genomic data center identifier in config ({expected_grz_id})"
            )

        if (submitted_le_id := self.content.submission.submitter_id) != expected_le_id:
            yield (
                f"Submitter (LE) identifier specified in the metadata.json ({submitted_le_id}) "
                f"does not match submitter (LE) identifier in config ({expected_le_id})"
            )

        submission_files: dict[str | PathLike, SubmissionFileMetadata] = {}
        for donor in self.content.donors:
            for lab_data in donor.lab_data:
                if not lab_data.sequence_data:
                    log.info(f"Skipping validation of empty sequence data for donor {donor}.")
                    continue
                for file_data in lab_data.sequence_data.files:
                    # check if file is already registered
                    file_path = Path(file_data.file_path)
                    if len(str(file_path)) > (S3_MAX_KEY_LENGTH - UPLOADED_FILE_PREFIX_LENGTH):
                        yield f"{file_data.file_path}: File path is too long for the inbox!"
                    if other_metadata := submission_files.get(file_path):
                        # check if metadata matches
                        if file_data != other_metadata:
                            yield f"{file_data.file_path}: Different metadata for the same path observed!"

                        # check if FASTQ data was already linked in another submission
                        if file_data.file_type == "fastq":
                            yield f"{file_data.file_path}: FASTQ file already linked in another submission!"
                        if file_data.file_type == "bam":
                            yield f"{file_data.file_path}: BAM file already linked in another submission!"
                    else:
                        submission_files[file_path] = file_data

    @property
    def checksum(self) -> str:
        """
        Checksum of the metadata file
        """
        return self._checksum


class Submission:
    """Class for handling submission data"""

    __log = log.getChild("Submission")

    def __init__(self, metadata_dir: str | PathLike, files_dir: str | PathLike):
        """
        Initialize the submission object.

        :param metadata_dir: Path to the metadata directory
        :param files_dir: Path to the files directory
        """
        self.metadata_dir = Path(metadata_dir)
        self.files_dir = Path(files_dir)

        self.metadata = SubmissionMetadata(self.metadata_dir / "metadata.json")

    @property
    def files(self) -> dict[Path, SubmissionFileMetadata]:
        """
        The files liked in the metadata.

        :return: Dictionary of `local_file_path` -> `SubmissionFileMetadata` pairs.
        """
        retval = {}
        for file_path, file_metadata in self.metadata.files.items():
            local_file_path = self.files_dir / file_path

            retval[local_file_path] = file_metadata

        return retval

    def validate_files_with_grz_check(  # noqa: C901, PLR0915, PLR0912
        self, checksum_progress_file: str | PathLike, seq_data_progress_file: str | PathLike, threads: int | None
    ) -> Generator[str, None, None]:
        """
        Validates submission files using `grz-check` and populates both progress logs.
        """
        checksum_progress_logger = FileProgressLogger[ValidationState](log_file_path=checksum_progress_file)
        checksum_progress_logger.cleanup(keep=[(fp, fm) for fp, fm in self.files.items()])

        seq_data_progress_logger = FileProgressLogger[ValidationState](log_file_path=seq_data_progress_file)
        seq_data_progress_logger.cleanup(keep=[(fp, fm) for fp, fm in self.files.items()])

        grz_check_args = []
        checked_files = set()

        def should_check_file(file_path: Path, file_metadata: File) -> bool:
            # Check against both logs. If either is missing a "pass", re-check.
            checksum_state = checksum_progress_logger.get_state(file_path, file_metadata)
            seq_data_state = seq_data_progress_logger.get_state(file_path, file_metadata)
            is_seq_file = file_metadata.file_type in ("fastq", "bam")

            checksum_passed = checksum_state and checksum_state.get("validation_passed")
            seq_data_passed = seq_data_state and seq_data_state.get("validation_passed")

            if is_seq_file:
                return not (checksum_passed and seq_data_passed)
            return not checksum_passed

        # Collect args for FASTQ and BAM from sequencing data
        for donor in self.metadata.content.donors:
            for lab_data in donor.lab_data:
                if not lab_data.sequence_data:
                    continue

                threshold_definitions = load_thresholds()
                thresholds = threshold_definitions[
                    (
                        self.metadata.content.submission.genomic_study_subtype,
                        lab_data.library_type,
                        lab_data.sequence_subtype,
                    )
                ]
                mean_read_length_threshold = thresholds.get("meanReadLength", 0)

                sequence_data = lab_data.sequence_data
                fastq_files = [f for f in sequence_data.files if f.file_type == FileType.fastq]
                bam_files = [f for f in sequence_data.files if f.file_type == FileType.bam]

                if lab_data.sequencing_layout == SequencingLayout.paired_end:
                    key = lambda f: (f.flowcell_id, f.lane_id)
                    fastq_files.sort(key=key)
                    for _key, group in groupby(fastq_files, key):
                        files = list(group)
                        fastq_r1_files = [f for f in files if f.read_order == ReadOrder.r1]
                        fastq_r2_files = [f for f in files if f.read_order == ReadOrder.r2]

                        for r1_meta, r2_meta in zip(fastq_r1_files, fastq_r2_files, strict=True):
                            r1_path = self.files_dir / r1_meta.file_path
                            r2_path = self.files_dir / r2_meta.file_path
                            if should_check_file(r1_path, r1_meta) or should_check_file(r2_path, r2_meta):
                                grz_check_args.extend(
                                    ["--fastq-paired", str(r1_path), str(r2_path), str(mean_read_length_threshold)]
                                )
                            checked_files.add(r1_path)
                            checked_files.add(r2_path)
                else:
                    for f_meta in fastq_files:
                        f_path = self.files_dir / f_meta.file_path
                        if f_path in checked_files:
                            continue
                        if should_check_file(f_path, f_meta):
                            grz_check_args.extend(["--fastq-single", str(f_path), str(mean_read_length_threshold)])
                        checked_files.add(f_path)

                for bam_meta in bam_files:
                    bam_path = self.files_dir / bam_meta.file_path
                    if bam_path in checked_files:
                        continue
                    if should_check_file(bam_path, bam_meta):
                        grz_check_args.extend(["--bam", str(bam_path)])
                    checked_files.add(bam_path)

        # Handle any other files with --raw for calculating checksums
        for file_path, file_metadata in self.files.items():
            if file_path not in checked_files and should_check_file(file_path, file_metadata):
                grz_check_args.extend(["--raw", str(file_path)])

        if not grz_check_args:
            self.__log.info("All files are already validated. Skipping `grz-check`.")
        else:
            log_dir = Path(checksum_progress_file).parent
            temp_report_path = log_dir / "grz-check.report.jsonl"
            temp_report_path.unlink(missing_ok=True)

            command_args = ["--output", str(temp_report_path), *grz_check_args]
            if threads:
                command_args.extend(["--threads", str(threads)])
            try:
                run_grz_check(command_args)
            except UserInterruptException:
                self.__log.warning("Validation cancelled by user. Processing partial results...")
                raise
            except subprocess.CalledProcessError as e:
                self.__log.error(f"`grz-check` failed with exit code {e.returncode}")
                yield "`grz-check` execution failed. See logs for details."
            finally:
                if temp_report_path.is_file():
                    self.__log.info(f"Processing report file: {temp_report_path}")
                    with temp_report_path.open("r") as f:
                        self._process_grz_check_report(f, checksum_progress_logger, seq_data_progress_logger)  # type: ignore
                    temp_report_path.unlink()
                else:
                    self.__log.warning("`grz-check` did not produce a report file.")

        # Aggregate errors from both logs
        all_errors = set()
        for local_file_path, file_metadata in self.files.items():
            checksum_state = checksum_progress_logger.get_state(local_file_path, file_metadata)
            if checksum_state and not checksum_state.get("validation_passed"):
                for error in checksum_state.get("errors", []):
                    all_errors.add(f"{local_file_path.relative_to(self.files_dir)}: {error}")

            if file_metadata.file_type in ("fastq", "bam"):
                seq_data_state = seq_data_progress_logger.get_state(local_file_path, file_metadata)
                if seq_data_state and not seq_data_state.get("validation_passed"):
                    for error in seq_data_state.get("errors", []):
                        all_errors.add(f"{local_file_path.relative_to(self.files_dir)}: {error}")
        yield from all_errors

    def _process_grz_check_report(  # noqa: C901
        self,
        report_file: typing.TextIO,
        checksum_progress_logger: FileProgressLogger[ValidationState],
        seq_data_progress_logger: FileProgressLogger[ValidationState],
    ):
        """
        Parses the JSONL report from `grz-check` and updates both progress loggers.
        """
        for line in report_file:
            try:
                report_entry = json.loads(line)
                data = report_entry.get("data", {})
                file_path_str = data.get("path")
                if not file_path_str:
                    continue

                file_path = Path(file_path_str).resolve()
                file_metadata = self.files.get(file_path)

                if not file_metadata:
                    self.__log.warning(f"Could not find metadata for file in grz-check report: {file_path_str}")
                    continue

                status = data.get("status")
                errors = data.get("errors", [])
                warnings = data.get("warnings", [])
                checksum = data.get("checksum")

                if warnings:
                    for w in warnings:
                        self.__log.warning(w)

                checksum_issues = []
                if (
                    checksum
                    and (file_metadata.checksum_type or "").lower() == "sha256"
                    and file_metadata.file_checksum != checksum
                ):
                    checksum_issues.append(
                        f"Checksum mismatch! Expected: '{file_metadata.file_checksum}', calculated: '{checksum}'"
                    )

                if file_path.exists() and file_path.is_file():
                    if file_metadata.file_size_in_bytes != file_path.stat().st_size:
                        checksum_issues.append(
                            f"File size mismatch! Expected: '{file_metadata.file_size_in_bytes}', observed: '{file_path.stat().st_size}'."
                        )
                else:
                    checksum_issues.append("File not found for size check.")

                checksum_passed = not checksum_issues
                checksum_state = ValidationState(errors=checksum_issues, validation_passed=checksum_passed)
                checksum_progress_logger.set_state(file_path, file_metadata, checksum_state)

                if file_metadata.file_type in ("fastq", "bam"):
                    integrity_passed = status == "OK"
                    integrity_errors = errors if not integrity_passed else []

                    seq_data_state = ValidationState(errors=integrity_errors, validation_passed=integrity_passed)
                    seq_data_progress_logger.set_state(file_path, file_metadata, seq_data_state)

            except json.JSONDecodeError:
                self.__log.warning(f"Could not parse line in grz-check report: {line.strip()}")
            except Exception as e:
                self.__log.error(f"Error processing grz-check report entry: {line.strip()}. Error: {e}")

    @staticmethod
    def _validate_file_data_fallback(metadata: File, local_file_path: Path) -> Generator[str]:
        """
        Validates whether the provided file matches this metadata.
        (Fallback method)

        :param metadata: Metadata model object
        :param local_file_path: Path to the actual file (resolved if symlinked)
        :return: Generator of errors
        """
        # Resolve file path
        local_file_path = local_file_path.resolve()

        # Check if path exists
        if not local_file_path.exists():
            yield f"{str(Path('files') / metadata.file_path)} does not exist! Ensure filePath is relative to the files/ directory under the submission root."
            # Return here as following tests cannot work
            return

        # Check if path is a file
        if not local_file_path.is_file():
            yield f"{str(metadata.file_path)} is not a file!"
            # Return here as following tests cannot work
            return

        # Check if the checksum is correct
        if metadata.checksum_type == "sha256":
            calculated_checksum = calculate_sha256(local_file_path)
            if metadata.file_checksum != calculated_checksum:
                yield (
                    f"{str(metadata.file_path)}: Checksum mismatch! "
                    f"Expected: '{metadata.file_checksum}', calculated: '{calculated_checksum}'."
                )
        else:
            yield (
                f"{str(metadata.file_path)}: Unsupported checksum type: {metadata.checksum_type}. "
                f"Supported types: {[e.value for e in ChecksumType]}"
            )

        # Check file size
        if metadata.file_size_in_bytes != local_file_path.stat().st_size:
            yield (
                f"{str(metadata.file_path)}: File size mismatch! "
                f"Expected: '{metadata.file_size_in_bytes}', observed: '{local_file_path.stat().st_size}'."
            )

    def _validate_checksums_fallback(self, progress_log_file: str | PathLike) -> Generator[str]:
        """
        Validates the checksum of the files against the metadata.
        (Fallback method)

        :return: Generator of errors
        """
        progress_logger = FileProgressLogger[ValidationState](log_file_path=progress_log_file)
        # cleanup log file and keep only files listed here
        progress_logger.cleanup(keep=[(file_path, file_metadata) for file_path, file_metadata in self.files.items()])
        # fields:
        # - "errors": List[str]
        # - "validation_passed": bool

        def validate_file(local_file_path, file_metadata):
            self.__log.debug("Validating '%s'...", str(local_file_path))

            # validate the file
            errors = list(self._validate_file_data_fallback(file_metadata, local_file_path))
            validation_passed = len(errors) == 0

            # return log state
            return ValidationState(errors=errors, validation_passed=validation_passed)

        for local_file_path, file_metadata in self.files.items():
            logged_state = progress_logger.get_state(
                local_file_path,
                file_metadata,
                default=validate_file,  # validate the file if the state was not calculated yet
            )

            if logged_state:
                yield from logged_state["errors"]

    def _validate_sequencing_data_fallback(self, progress_log_file: str | PathLike) -> Generator[str]:
        """
        Quick-validates sequencing data linked in this submission.
        (Fallback method)

        :return: Generator of errors
        """
        from ..progress import FileProgressLogger

        progress_logger = FileProgressLogger[ValidationState](log_file_path=progress_log_file)
        # cleanup log file and keep only files listed here
        progress_logger.cleanup(keep=[(file_path, file_metadata) for file_path, file_metadata in self.files.items()])
        # fields:
        # - "errors": List[str]
        # - "validation_passed": bool

        def find_fastq_files(sequence_data: SequenceData) -> list[File]:
            return [f for f in sequence_data.files if f.file_type == FileType.fastq]

        def find_bam_files(sequence_data: SequenceData) -> list[File]:
            return [f for f in sequence_data.files if f.file_type == FileType.bam]

        for donor in self.metadata.content.donors:
            for lab_data in donor.lab_data:
                sequencing_layout = lab_data.sequencing_layout
                sequence_data = lab_data.sequence_data
                # find all FASTQ files
                fastq_files = find_fastq_files(sequence_data) if sequence_data else []
                bam_files = find_bam_files(sequence_data) if sequence_data else []

                if not lab_data.library_type.endswith("_lr"):
                    match sequencing_layout:
                        case SequencingLayout.single_end | SequencingLayout.reverse | SequencingLayout.other:
                            yield from self._validate_single_end_fallback(
                                fastq_files, progress_logger, lab_data.library_type, lab_data.sequence_subtype
                            )
                        case SequencingLayout.paired_end:
                            yield from self._validate_paired_end_fallback(
                                fastq_files, progress_logger, lab_data.library_type, lab_data.sequence_subtype
                            )
                yield from self._validate_bams_fallback(bam_files, progress_logger)

    def _validate_bams_fallback(
        self,
        bam_files: list[File],
        progress_logger: FileProgressLogger[ValidationState],
    ) -> Generator[str, None, None]:
        """
        Basic BAM sanity checks.
        (Fallback method)

        :param bam_files: List of BAM files
        :param progress_logger: Progress logger
        """

        def validate_file(local_file_path, _file_metadata) -> ValidationState:
            self.__log.debug("Validating '%s'...", str(local_file_path))

            # validate the file
            errors = list(validate_bam(local_file_path))
            validation_passed = len(errors) == 0

            # return log state
            return ValidationState(
                errors=errors,
                validation_passed=validation_passed,
            )

        for bam_file in bam_files:
            logged_state = progress_logger.get_state(
                self.files_dir / bam_file.file_path,
                bam_file,
                default=validate_file,  # validate the file if the state was not calculated yet
            )
            if logged_state:
                yield from logged_state["errors"]

    def _validate_single_end_fallback(
        self,
        fastq_files: list[File],
        progress_logger: FileProgressLogger[ValidationState],
        library_type: LibraryType,
        sequence_subtype: SequenceSubtype,
    ) -> Generator[str, None, None]:
        def validate_file(local_file_path, file_metadata: SubmissionFileMetadata) -> ValidationState:
            self.__log.debug("Validating '%s'...", str(local_file_path))

            # validate the file
            threshold_definitions = load_thresholds()
            thresholds = threshold_definitions[
                (
                    self.metadata.content.submission.genomic_study_subtype,
                    library_type,
                    sequence_subtype,
                )
            ]
            mean_read_length_threshold = thresholds["meanReadLength"]
            errors = list(
                validate_single_end_reads(local_file_path, mean_read_length_threshold=mean_read_length_threshold)
            )
            validation_passed = len(errors) == 0

            # return log state
            return ValidationState(errors=errors, validation_passed=validation_passed)

        for fastq_file in fastq_files:
            logged_state = progress_logger.get_state(
                self.files_dir / fastq_file.file_path,
                fastq_file,
                default=validate_file,  # validate the file if the state was not calculated yet
            )
            if logged_state:
                yield from logged_state["errors"]

    def _validate_paired_end_fallback(
        self,
        fastq_files: list[File],
        progress_logger: FileProgressLogger[ValidationState],
        library_type: LibraryType,
        sequence_subtype: SequenceSubtype,
    ) -> Generator[str, None, None]:
        threshold_definitions = load_thresholds()
        thresholds = threshold_definitions[
            (
                self.metadata.content.submission.genomic_study_subtype,
                library_type,
                sequence_subtype,
            )
        ]
        mean_read_length_threshold = thresholds["meanReadLength"]
        key = lambda f: (f.flowcell_id, f.lane_id)
        fastq_files.sort(key=key)
        for _key, group in groupby(fastq_files, key):
            files = list(group)

            # separate R1 and R2 files
            fastq_r1_files = [f for f in files if f.read_order == ReadOrder.r1]
            fastq_r2_files = [f for f in files if f.read_order == ReadOrder.r2]

            for fastq_r1, fastq_r2 in zip(fastq_r1_files, fastq_r2_files, strict=True):
                local_fastq_r1_path = self.files_dir / fastq_r1.file_path
                local_fastq_r2_path = self.files_dir / fastq_r2.file_path

                # get saved state
                logged_state_r1 = progress_logger.get_state(local_fastq_r1_path, fastq_r1)
                logged_state_r2 = progress_logger.get_state(local_fastq_r2_path, fastq_r2)

                if logged_state_r1 is None or logged_state_r2 is None or logged_state_r1 != logged_state_r2:
                    # calculate state
                    errors = list(
                        validate_paired_end_reads(
                            local_fastq_r1_path,  # fastq R1
                            local_fastq_r2_path,  # fastq R2
                            mean_read_length_threshold=mean_read_length_threshold,
                        )
                    )
                    validation_passed = len(errors) == 0

                    state = ValidationState(errors=errors, validation_passed=validation_passed)
                    # update state for both files
                    progress_logger.set_state(  # fastq R1
                        local_fastq_r1_path, fastq_r1, state
                    )
                    progress_logger.set_state(  # fastq R2
                        local_fastq_r2_path, fastq_r2, state
                    )
                    yield from state["errors"]
                else:
                    # both fastq states are equal, so simply yield one of them
                    yield from logged_state_r1["errors"]

    def encrypt(
        self,
        encrypted_files_dir: str | PathLike,
        progress_log_file: str | PathLike,
        recipient_public_key_path: str | PathLike,
        submitter_private_key_path: str | PathLike | None = None,
        force: bool = False,
    ) -> EncryptedSubmission:
        """
        Encrypt this submission with a public key using Crypt4Gh

        :param encrypted_files_dir: Output directory of the encrypted files
        :param progress_log_file: Path to a log file to store the progress of the encryption process
        :param recipient_public_key_path: Path to the public key file which will be used for encryption
        :param submitter_private_key_path: Path to the private key file which will be used to sign the encryption
        :param force: Force encryption even if target files already exist
        :return: EncryptedSubmission instance
        """
        encrypted_files_dir = Path(encrypted_files_dir)

        if not Path(recipient_public_key_path).expanduser().is_file():
            msg = f"Public key file does not exist: {recipient_public_key_path}"
            self.__log.error(msg)
            raise FileNotFoundError(msg)
        if not submitter_private_key_path:
            self.__log.warning("No submitter private key provided, skipping signing.")
        elif not Path(submitter_private_key_path).expanduser().is_file():
            msg = f"Private key file does not exist: {submitter_private_key_path}"
            self.__log.error(msg)
            raise FileNotFoundError(msg)

        if not encrypted_files_dir.is_dir():
            self.__log.debug(
                "Creating encrypted submission files directory: %s...",
                encrypted_files_dir,
            )
            encrypted_files_dir.mkdir(mode=0o770, parents=False, exist_ok=False)

        from ..progress import FileProgressLogger

        progress_logger = FileProgressLogger[EncryptionState](log_file_path=progress_log_file)

        try:
            public_keys = Crypt4GH.prepare_c4gh_keys(recipient_public_key_path)
        except Exception as e:
            self.__log.error(f"Error preparing public keys: {e}")
            raise e

        for file_path, file_metadata in self.files.items():
            # encryption_successful = True
            logged_state = progress_logger.get_state(file_path, file_metadata)
            self.__log.debug("state for %s: %s", file_path, logged_state)

            encrypted_file_path = encrypted_files_dir / EncryptedSubmission.get_encrypted_file_path(
                file_metadata.file_path
            )
            encrypted_file_path.parent.mkdir(mode=0o770, parents=True, exist_ok=True)

            if (
                (logged_state is None)
                or not logged_state.get("encryption_successful", False)
                or not encrypted_file_path.is_file()
            ):
                self.__log.info(
                    "Encrypting file: '%s' -> '%s'",
                    str(file_path),
                    str(encrypted_file_path),
                )

                if encrypted_file_path.exists() and not force:
                    raise RuntimeError(
                        f"'{encrypted_file_path}' already exists. Delete it or use --force to overwrite it."
                    )

                try:
                    Crypt4GH.encrypt_file(file_path, encrypted_file_path, public_keys)

                    self.__log.info(f"Encryption complete for {str(file_path)}. ")
                    progress_logger.set_state(
                        file_path,
                        file_metadata,
                        state=EncryptionState(encryption_successful=True),
                    )
                except Exception as e:
                    self.__log.error("Encryption failed for '%s'", str(file_path))

                    progress_logger.set_state(
                        file_path,
                        file_metadata,
                        state=EncryptionState(encryption_successful=False, errors=[str(e)]),
                    )

                    raise e
            else:
                self.__log.info(
                    "File '%s' already encrypted in '%s'",
                    str(file_path),
                    str(encrypted_file_path),
                )

        self.__log.info("File encryption completed.")

        return EncryptedSubmission(
            metadata_dir=self.metadata_dir,
            encrypted_files_dir=encrypted_files_dir,
        )


class EncryptedSubmission:
    """The encrypted counterpart to `Submission`. Handles encrypted submission data."""

    __log = log.getChild("EncryptedSubmission")

    def __init__(
        self, metadata_dir: str | PathLike, encrypted_files_dir: str | PathLike, log_dir: str | PathLike | None = None
    ):
        """
        Initialize the encrypted submission object.

        :param metadata_dir: Path to the metadata directory
        :param encrypted_files_dir: Path to the encrypted files directory
        """
        self.metadata_dir = Path(metadata_dir)
        self.encrypted_files_dir = Path(encrypted_files_dir)
        self.log_dir = Path(log_dir) if log_dir is not None else None

        self.metadata = SubmissionMetadata(self.metadata_dir / "metadata.json")

    @property
    def encrypted_files(self) -> dict[Path, SubmissionFileMetadata]:
        """
        The encrypted files linked in the metadata.

        :return: Dictionary of `local_file_path` -> `SubmissionFileMetadata` pairs.
        """
        retval = {}
        for file_path, file_metadata in self.metadata.files.items():
            encrypted_file_path = self.get_encrypted_file_path(self.encrypted_files_dir / file_path)

            retval[encrypted_file_path] = file_metadata

        return retval

    @property
    def submission_id(self) -> str:
        return self.metadata.content.submission_id

    def get_metadata_file_path_and_object_id(self) -> tuple[Path, str]:
        """
        :return: tuple with the `local_file_path` and s3_object_id of the metadata file
        """
        return Path(self.metadata.file_path), str(Path(self.submission_id) / "metadata" / self.metadata.file_path.name)

    def get_encrypted_files_and_object_id(self) -> dict[Path, str]:
        """
        :return Dictionary of `local_file_path` -> s3_object_id
        """
        retval = {}
        for local_file_path, file_metadata in self.encrypted_files.items():
            retval[local_file_path] = str(
                Path(self.submission_id) / "files" / self.get_encrypted_file_path(file_metadata.file_path)
            )
        return retval

    def get_log_files_and_object_id(self) -> dict[Path, str]:
        """
        :return Dictionary of `local_file_path` -> s3_object_id
        """
        retval = {}
        if self.log_dir is not None:
            log_dir = self.log_dir
            for dirpath, _dirnames, filenames in log_dir.walk():
                for filename in filenames:
                    local_file_path = dirpath / filename
                    retval[local_file_path] = str(
                        Path(self.submission_id) / "logs" / local_file_path.relative_to(log_dir)
                    )
        return retval

    @staticmethod
    def get_encrypted_file_path(file_path: str | PathLike) -> Path:
        """
        Return the path to the encrypted file based on the original file path,
        with additional extension'.c4gh'.
        """
        p = Path(file_path)
        return p.with_suffix(p.suffix + ".c4gh")

    @staticmethod
    def get_encryption_header_path(file_path: str | PathLike) -> Path:
        """
        Return the path to the encryption header file based on the original file path,
        with additional extension'.c4gh_header'.
        """
        p = Path(file_path)
        return p.with_suffix(p.suffix + ".c4gh_header")

    def decrypt(
        self,
        files_dir: str | PathLike,
        progress_log_file: str | PathLike,
        recipient_private_key_path: str | PathLike,
    ) -> Submission:
        """
        Decrypt this encrypted submission with a private key using Crypt4Gh

        :param files_dir: Output directory of the decrypted files
        :param progress_log_file: Path to a log file to store the progress of the decryption process
        :param recipient_private_key_path: Path to the private key file which will be used for decryption
        :return: Submission instance
        """
        files_dir = Path(files_dir)

        if not files_dir.is_dir():
            self.__log.debug(
                "Creating decrypted submission files directory: %s...",
                files_dir,
            )
            files_dir.mkdir(mode=0o770, parents=False, exist_ok=False)

        from ..progress import FileProgressLogger

        progress_logger = FileProgressLogger[DecryptionState](log_file_path=progress_log_file)

        try:
            private_key = Crypt4GH.retrieve_private_key(recipient_private_key_path)
        except Exception as e:
            self.__log.error(f"Error preparing private key: {e}")
            raise e

        for encrypted_file_path, file_metadata in self.encrypted_files.items():
            logged_state = progress_logger.get_state(encrypted_file_path, file_metadata)
            self.__log.debug("state for %s: %s", encrypted_file_path, logged_state)

            decrypted_file_path = files_dir / file_metadata.file_path
            if not decrypted_file_path.parent.is_dir():
                decrypted_file_path.parent.mkdir(mode=0o770, parents=True, exist_ok=False)

            if (
                (logged_state is None)
                or not logged_state.get("decryption_successful", False)
                or not decrypted_file_path.is_file()
            ):
                self.__log.info(
                    "Decrypting file: '%s' -> '%s'",
                    str(encrypted_file_path),
                    str(decrypted_file_path),
                )

                try:
                    Crypt4GH.decrypt_file(encrypted_file_path, decrypted_file_path, private_key)

                    self.__log.info(f"Decryption complete for {str(encrypted_file_path)}. ")
                    progress_logger.set_state(
                        encrypted_file_path,
                        file_metadata,
                        state=DecryptionState(decryption_successful=True),
                    )
                except Exception as e:
                    self.__log.error("Decryption failed for '%s'", str(encrypted_file_path))

                    progress_logger.set_state(
                        encrypted_file_path,
                        file_metadata,
                        state=DecryptionState(decryption_successful=False, errors=[str(e)]),
                    )

                    raise e
            else:
                self.__log.info(
                    "File '%s' already decrypted in '%s'",
                    str(encrypted_file_path),
                    str(decrypted_file_path),
                )

        self.__log.info("File decryption completed.")

        return Submission(
            metadata_dir=self.metadata_dir,
            files_dir=files_dir,
        )


class SubmissionValidationError(Exception):
    """Exception raised when validation of a submission fails"""

    pass
