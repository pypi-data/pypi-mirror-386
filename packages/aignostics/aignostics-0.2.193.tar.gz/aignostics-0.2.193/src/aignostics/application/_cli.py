"""CLI of application module."""

import json
import sys
import time
import zipfile
from pathlib import Path
from typing import Annotated

import typer
from aignx.codegen.models import RunState

from aignostics.bucket import Service as BucketService
from aignostics.platform import NotFoundException
from aignostics.utils import console, get_logger, get_user_data_directory, sanitize_path

from ._service import DownloadProgress, DownloadProgressState, Service
from ._utils import (
    application_run_status_to_str,
    get_mime_type_for_artifact,
    print_runs_non_verbose,
    print_runs_verbose,
    read_metadata_csv_to_dict,
    retrieve_and_print_run_details,
    write_metadata_dict_to_csv,
)

MESSAGE_NOT_YET_IMPLEMENTED = "NOT YET IMPLEMENTED"

logger = get_logger(__name__)

cli = typer.Typer(name="application", help="List and inspect applications on Aignostics Platform.")

run_app = typer.Typer()
cli.add_typer(run_app, name="run", help="List, submit and manage application runs")

result_app = typer.Typer()
run_app.add_typer(result_app, name="result", help="Download or delete run results.")


@cli.command("list")
def application_list(
    verbose: Annotated[bool, typer.Option(help="Show application details")] = False,
) -> None:
    """List available applications."""
    try:
        apps = Service().applications()
    except Exception as e:
        logger.exception("Could not load applications")
        console.print(f"[error]Error:[/error] Could not load applications: {e}")
        sys.exit(1)

    app_count = 0

    if verbose:
        console.print("[bold]Available Applications:[/bold]")
        console.print("=" * 80)

        for app in apps:
            app_count += 1
            console.print(f"[bold]Application ID:[/bold] {app.application_id}")
            console.print(f"[bold]Name:[/bold] {app.name}")
            console.print(f"[bold]Regulatory Classes:[/bold] {', '.join(app.regulatory_classes)}")

            try:
                details = Service().application(app.application_id)
            except Exception as e:
                logger.exception("Failed to get application details for application '%s'", app.application_id)
                console.print(
                    f"[error]Error:[/error] Failed to get application details for application "
                    f"'{app.application_id}': {e}"
                )
                continue
            console.print("[bold]Available Versions:[/bold]")
            for version in details.versions:
                console.print(f"  - {version.number} ({version.released_at})")

                app_version = Service().application_version(app.application_id, version.number)
                console.print(f"    Changelog: {app_version.changelog}")

                num_inputs = len(app_version.input_artifacts)
                num_outputs = len(app_version.output_artifacts)
                console.print(f"    Artifacts: {num_inputs} input(s), {num_outputs} output(s)")

            console.print("[bold]Description:[/bold]")
            for line in app.description.strip().split("\n"):
                console.print(f"  {line}")

            console.print("-" * 80)
    else:
        console.print("[bold]Available Aignostics Applications:[/bold]")
        for app in apps:
            app_count += 1
            console.print(
                f"- [bold]{app.application_id}[/bold] - latest application version: `{app.latest_version or 'None'}`"
            )

    if app_count == 0:
        logger.info("No applications available.")
        console.print("No applications available.")


@cli.command("dump-schemata")
def application_dump_schemata(  # noqa: C901
    application_id: Annotated[
        str,
        typer.Argument(help="Id of the application or application_version to dump the output schema for."),
    ],
    application_version: Annotated[
        str | None,
        typer.Option(
            help="Version of the application. If not provided, the latest version will be used.",
        ),
    ] = None,
    destination: Annotated[
        Path,
        typer.Option(
            help="Path pointing to directory where the input and output schemata will be dumped.",
            exists=False,
            file_okay=False,
            dir_okay=True,
            writable=True,
            readable=True,
            resolve_path=True,
        ),
    ] = Path().cwd(),  # noqa: B008,
    zip: Annotated[  # noqa: A002
        bool,
        typer.Option(
            help="If set, the schema files will be zipped into a single file, with the schema files deleted.",
        ),
    ] = False,
) -> None:
    """Output the input schema of the application in JSON format."""
    try:
        app = Service().application(application_id)
        app_version = Service().application_version(application_id, application_version)
    except (NotFoundException, ValueError) as e:
        message = f"Failed to load application version with ID '{id}', check your input: : {e!s}."
        logger.warning(message)
        console.print(f"[warning]Warning:[/warning] {message}")
        sys.exit(2)
    except (Exception, RuntimeError) as e:
        message = f"Failed to load application version with ID '{id}': {e!s}."
        logger.exception(message)
        console.print(f"[warning]Error:[/warning] {message}")
        sys.exit(1)
    try:
        destination.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        console.print(f"[error]Error:[/error] Failed to create directory '{destination}': {e}")
        sys.exit(1)

    created_files: list[Path] = []

    for input_artifact in app_version.input_artifacts:
        if input_artifact.metadata_schema:
            file_path: Path = sanitize_path(
                Path(
                    destination / f"{app.application_id}_{app_version.version_number}_input_{input_artifact.name}.json"
                )
            )  # type: ignore
            file_path.write_text(data=json.dumps(input_artifact.metadata_schema, indent=2), encoding="utf-8")
            created_files.append(file_path)

    for output_artifact in app_version.output_artifacts:
        if output_artifact.metadata_schema:
            file_path = sanitize_path(
                Path(
                    destination
                    / f"{app.application_id}_{app_version.version_number}_output_{output_artifact.name}.json"
                )
            )  # type: ignore
            file_path.write_text(data=json.dumps(output_artifact.metadata_schema, indent=2), encoding="utf-8")
            created_files.append(file_path)

    md_file_path: Path = sanitize_path(
        Path(destination / f"{app.application_id}_{app_version.version_number}_schemata.md")
    )  # type: ignore
    with md_file_path.open("w", encoding="utf-8") as md_file:
        md_file.write(f"# Schemata for Aignostics Application {app.name}\n")
        md_file.write(f"* ID: {app.application_id}\n")
        md_file.write(f"\n## Description: \n{app.description}\n\n")
        md_file.write("\n## Input Artifacts\n")
        for input_artifact in app_version.input_artifacts:
            md_file.write(
                f"- {input_artifact.name}: "
                f"{app.application_id}_{app_version.version_number}_input_{input_artifact.name}.json\n"
            )
        md_file.write("\n## Output Artifacts\n")
        for output_artifact in app_version.output_artifacts:
            md_file.write(
                f"- {output_artifact.name}: "
                f"{app.application_id}_{app_version.version_number}_output_{output_artifact.name}.json\n"
            )
    created_files.append(md_file_path)

    if zip:
        zip_filename = sanitize_path(
            Path(destination / f"{app.application_id}_{app_version.version_number}_schemata.zip")
        )
        with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in created_files:
                zipf.write(file_path, arcname=file_path.name)
        console.print(f"Zipped {len(created_files)} files to [bold]{zip_filename}[/bold]")
        for file_path in created_files:
            file_path.unlink()


@cli.command("describe")
def application_describe(
    application_id: Annotated[str, typer.Argument(help="Id of the application to describe")],
    verbose: Annotated[bool, typer.Option(help="Show application details")] = False,
) -> None:
    """Describe application."""
    try:
        app = Service().application(application_id)
    except NotFoundException:
        logger.warning("Application with ID '%s' not found.", application_id)
        console.print(f"[warning]Warning:[/warning] Application with ID '{application_id}' not found.")
        sys.exit(2)
    except Exception as e:
        logger.exception("Failed to describe application with ID '%s'", application_id)
        console.print(f"[error]Error:[/error] Failed to describe application: {e}")
        sys.exit(1)

    console.print(f"[bold]Application Details for {app.application_id}[/bold]")
    console.print("=" * 80)
    console.print(f"[bold]Name:[/bold] {app.name}")
    console.print(f"[bold]Regulatory Classes:[/bold] {', '.join(app.regulatory_classes)}")

    console.print("[bold]Description:[/bold]")
    for line in app.description.strip().split("\n"):
        console.print(f"  {line}")

    if app.versions:
        console.print()
        console.print("[bold]Available Versions:[/bold]")
        for version in app.versions:
            console.print(f"  [bold]Version:[/bold] {version.number} ({version.released_at})")
            if not verbose:
                continue
            try:
                app_version = Service().application_version(app.application_id, version.number)
            except Exception as e:
                logger.exception("Failed to get application version for '%s', '%s'", application_id, version.number)
                console.print(
                    f"[error]Error:[/error] Failed to get application version for "
                    f"'{application_id}', '{version.number}': {e}"
                )
                sys.exit(1)

            console.print(f"  [bold]Changelog:[/bold] {app_version.changelog}")
            console.print("  [bold]Input Artifacts:[/bold]")
            for artifact in app_version.input_artifacts:
                console.print(f"    - Name: {artifact.name}")
                console.print(f"      MIME Type: {get_mime_type_for_artifact(artifact)}")
                console.print(f"      Schema: {artifact.metadata_schema}")

            console.print("  [bold]Output Artifacts:[/bold]")
            for artifact in app_version.output_artifacts:
                console.print(f"    - Name: {artifact.name}")
                console.print(f"      MIME Type: {get_mime_type_for_artifact}")
                console.print(f"      Scope: {artifact.scope}")
                console.print(f"      Schema: {artifact.metadata_schema}")

            console.print()


@run_app.command(name="execute")
def run_execute(  # noqa: PLR0913, PLR0917
    application_id: Annotated[
        str,
        typer.Argument(help="Id of application version to execute."),
    ],
    metadata_csv_file: Annotated[
        Path,
        typer.Argument(
            help="Filename of the .csv file containing the metadata and external ids.",
            exists=False,
            file_okay=True,
            dir_okay=False,
            writable=True,
            readable=True,
            resolve_path=True,
        ),
    ],
    source_directory: Annotated[
        Path,
        typer.Argument(
            help="Source directory to scan for whole slide images",
            exists=True,
            file_okay=False,
            dir_okay=True,
            writable=True,
            readable=True,
            resolve_path=True,
        ),
    ],
    mapping: Annotated[
        list[str],
        typer.Argument(
            help="Mapping to use for amending metadata CSV file. "
            "Each mapping is of the form '<regexp>:<key>:<value>,<key>:<value>,...'."
            "The regular expression is matched against the external_id attribute of the entry. "
            "The key/value pairs are applied to the entry if the pattern matches. "
            "You can use the mapping option multiple times to set values for multiple files. "
            'Example: ".*:staining_method:H&E,tissue:LIVER,disease:LIVER_CANCER"',
        ),
    ],
    application_version: Annotated[
        str | None,
        typer.Option(
            help="Version of the application. If not provided, the latest version will be used.",
        ),
    ] = None,
    create_subdirectory_for_run: Annotated[
        bool,
        typer.Option(
            help="Create a subdirectory for the results of the run in the destination directory",
        ),
    ] = True,
    create_subdirectory_per_item: Annotated[
        bool,
        typer.Option(
            help="Create a subdirectory per item in the destination directory",
        ),
    ] = True,
    upload_prefix: Annotated[
        str,
        typer.Option(
            help="Prefix for the upload destination. If not given will be set to current milliseconds.",
        ),
    ] = f"{time.time() * 1000}",
    wait_for_completion: Annotated[
        bool,
        typer.Option(
            help="Wait for run completion and download results incrementally",
        ),
    ] = True,
    note: Annotated[
        str | None,
        typer.Option(help="Optional note to include with the run submission via custom metadata."),
    ] = None,
    due_date: Annotated[
        str | None,
        typer.Option(
            help="Optional soft due date to include with the run submission, ISO8601 format. "
            "The scheduler will try to complete the run by this date, taking the subscription tier"
            "and available GPU resources into account."
        ),
    ] = None,
    deadline: Annotated[
        str | None,
        typer.Option(
            help=(
                "Optional hard deadline to include with the run submission, ISO8601 format. "
                "If processing exceeds this deadline, the run can be aborted."
            ),
        ),
    ] = None,
    onboard_to_aignostics_portal: Annotated[
        bool,
        typer.Option(help="If True, onboard the run to the Aignostics Portal."),
    ] = False,
    validate_only: Annotated[
        bool, typer.Option(help="If True, cancel the run post validation, before analysis.")
    ] = False,
) -> None:
    """Prepare metadata, upload data to platform, and submit an application run, then incrementally download results.

    (1) Prepares metadata CSV file for the given application version
        by scanning the source directory for whole slide images
        and extracting metadata such as width, height, and mpp.
    (2) Amends the metadata CSV file using the given mappings
        to set all required attributes.
    (3) Uploads the files referenced in the metadata CSV file
        to the cloud bucket provisioned in the Aignostics platform.
    (4) Submits the run for the given application version
        with the metadata from the CSV file.
    (5) Downloads the results of the run to the destination directory,
        by default waiting for the run to complete
        and downloading results incrementally.
    """
    run_prepare(
        application_id=application_id,
        metadata_csv=metadata_csv_file,
        source_directory=source_directory,
        application_version=application_version,
        mapping=mapping,
    )
    run_upload(
        application_id=application_id,
        metadata_csv_file=metadata_csv_file,
        application_version=application_version,
        upload_prefix=upload_prefix,
        onboard_to_aignostics_portal=onboard_to_aignostics_portal,
    )
    run_id = run_submit(
        application_id=application_id,
        metadata_csv_file=metadata_csv_file,
        application_version=application_version,
        note=note,
        due_date=due_date,
        deadline=deadline,
        onboard_to_aignostics_portal=onboard_to_aignostics_portal,
        validate_only=validate_only,
    )
    result_download(
        run_id=run_id,
        destination_directory=metadata_csv_file.parent,
        create_subdirectory_for_run=create_subdirectory_for_run,
        create_subdirectory_per_item=create_subdirectory_per_item,
        wait_for_completion=wait_for_completion,
    )


@run_app.command(name="prepare")
def run_prepare(
    application_id: Annotated[
        str,
        typer.Argument(help="Id of the application to generate the metadata for. "),
    ],
    metadata_csv: Annotated[
        Path,
        typer.Argument(
            help="Target filename for the generated metadata CSV file.",
            exists=False,
            file_okay=True,
            dir_okay=False,
            writable=True,
            readable=True,
            resolve_path=True,
        ),
    ],
    source_directory: Annotated[
        Path,
        typer.Argument(
            help="Source directory to scan for whole slide images",
            exists=True,
            file_okay=False,
            dir_okay=True,
            writable=True,
            readable=True,
            resolve_path=True,
        ),
    ],
    application_version: Annotated[
        str | None,
        typer.Option(
            help="Version of the application. If not provided, the latest version will be used.",
        ),
    ] = None,
    mapping: Annotated[
        list[str] | None,
        typer.Option(
            help="Mapping to use for amending metadata CSV file. "
            "Each mapping is of the form '<regexp>:<key>:<value>,<key>:<value>,...'. "
            "The regular expression is matched against the external_id attribute of the entry. "
            "The key/value pairs are applied to the entry if the pattern matches. "
            "You can use the mapping option multiple times to set values for multiple files. "
        ),
    ] = None,
) -> None:
    """Prepare metadata CSV file required for submitting a run.

    (1) Scans source_directory for whole slide images.
    (2) Extracts metadata from whole slide images such as width, height, mpp.
    (3) Creates CSV file with columns as required by the given application version.
    (4) Optionally applies mappings to amend the metadata CSV file for columns
        that are not automatically filled by the metadata extraction process.

    Example:
        aignostics application run prepare "he-tme:v0.51.0" metadata.csv /path/to/source_directory
        --mapping "*.tiff:staining_method:H&E,tissue:LUNG,disease:LUNG_CANCER"
    """
    write_metadata_dict_to_csv(
        metadata_csv=metadata_csv,
        metadata_dict=Service().generate_metadata_from_source_directory(
            source_directory=source_directory,
            application_id=application_id,
            application_version=application_version,
            mappings=mapping or [],
        ),
    )
    console.print(f"Generated metadata file [bold]{metadata_csv}[/bold]")
    logger.info("Generated metadata file: '%s'", metadata_csv)


@run_app.command(name="upload")
def run_upload(
    application_id: Annotated[
        str,
        typer.Argument(help="Id of the application to upload data for. "),
    ],
    metadata_csv_file: Annotated[
        Path,
        typer.Argument(
            help="Filename of the .csv file containing the metadata and external ids.",
            exists=True,
            file_okay=True,
            dir_okay=False,
            writable=True,
            readable=True,
            resolve_path=True,
        ),
    ],
    application_version: Annotated[
        str | None,
        typer.Option(
            help="Version of the application. If not provided, the latest version will be used.",
        ),
    ] = None,
    upload_prefix: Annotated[
        str,
        typer.Option(
            help="Prefix for the upload destination. If not given will be set to current milliseconds.",
        ),
    ] = str(time.time() * 1000),
    onboard_to_aignostics_portal: Annotated[
        bool,
        typer.Option(
            help="If set, the run will be onboarded to the Aignostics Portal.",
        ),
    ] = False,
) -> None:
    """Upload files referenced in the metadata CSV file to the Aignostics platform.

    1. Reads the metadata CSV file.
    2. Uploads the files referenced in the CSV file to the Aignostics platform.
    3. Incrementally updates the CSV file with upload progress and the signed URLs for the uploaded files.
    """
    from rich.progress import (  # noqa: PLC0415
        BarColumn,
        FileSizeColumn,
        Progress,
        TaskProgressColumn,
        TextColumn,
        TimeRemainingColumn,
        TotalFileSizeColumn,
        TransferSpeedColumn,
    )

    metadata_dict = read_metadata_csv_to_dict(metadata_csv_file=metadata_csv_file)
    if not metadata_dict:
        sys.exit(2)

    total_bytes = 0
    for i, entry in enumerate(metadata_dict):
        source = entry["external_id"]
        source_file_path = Path(source)
        if not source_file_path.is_file():
            logger.warning("Source file '%s' (row %d) does not exist", source_file_path, i)
            console.print(f"[warning]Warning:[/warning] Source file '{source_file_path}' (row {i}) does not exist")
            sys.exit(2)

        total_bytes += source_file_path.stat().st_size

    with Progress(
        TextColumn(
            f"[progress.description]Uploading from {metadata_csv_file} to "
            f"{BucketService().get_bucket_protocol()}:/{BucketService().get_bucket_name()}/{upload_prefix}"
        ),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        FileSizeColumn(),
        TotalFileSizeColumn(),
        TransferSpeedColumn(),
        TextColumn("[progress.description]{task.description}"),
    ) as progress:
        task = progress.add_task(f"Uploading to {upload_prefix}/...", total=total_bytes)

        def update_progress(bytes_uploaded: int, source: Path, platform_bucket_url: str) -> None:
            progress.update(task, advance=bytes_uploaded, description=f"{source.name}")
            for entry in metadata_dict:
                if entry["external_id"] == str(source):
                    entry["platform_bucket_url"] = platform_bucket_url
                    break
            write_metadata_dict_to_csv(
                metadata_csv=metadata_csv_file,
                metadata_dict=metadata_dict,
            )

        Service().application_run_upload(
            application_id=application_id,
            application_version=application_version,
            metadata=metadata_dict,
            onboard_to_aignostics_portal=onboard_to_aignostics_portal,
            upload_prefix=upload_prefix,
            upload_progress_callable=update_progress,
        )

    logger.info("Upload completed.")
    console.print("Upload completed.", style="info")


@run_app.command("submit")
def run_submit(  # noqa: PLR0913, PLR0917
    application_id: Annotated[
        str,
        typer.Argument(help="Id of the application to submit run for."),
    ],
    metadata_csv_file: Annotated[
        Path,
        typer.Argument(
            help="Filename of the .csv file containing the metadata and external ids.",
            exists=False,
            file_okay=True,
            dir_okay=False,
            writable=False,
            readable=True,
            resolve_path=True,
        ),
    ],
    application_version: Annotated[
        str | None,
        typer.Option(
            help="Version of the application to generate the metadata for. "
            "If not provided, the latest version will be used.",
        ),
    ] = None,
    note: Annotated[
        str | None,
        typer.Option(help="Optional note to include with the run submission via custom metadata."),
    ] = None,
    due_date: Annotated[
        str | None,
        typer.Option(
            help="Optional soft due date to include with the run submission, ISO8601 format. "
            "The scheduler will try to complete the run by this date, taking the subscription tier"
            "and available GPU resources into account."
        ),
    ] = None,
    deadline: Annotated[
        str | None,
        typer.Option(
            help=(
                "Optional hard deadline to include with the run submission, ISO8601 format. "
                "If processing exceeds this deadline, the run can be aborted."
            ),
        ),
    ] = None,
    onboard_to_aignostics_portal: Annotated[
        bool,
        typer.Option(help="If True, onboard the run to the Aignostics Portal."),
    ] = False,
    validate_only: Annotated[
        bool, typer.Option(help="If True, cancel the run post validation, before analysis.")
    ] = False,
) -> str:
    """Submit run by referencing the metadata CSV file.

    1. Requires the metadata CSV file to be generated and referenced files uploaded first

    Returns:
        The ID of the submitted application run.
    """
    try:
        app_version = Service().application_version(
            application_id=application_id, application_version=application_version
        )
    except ValueError as e:
        logger.warning(
            "Bad input to create run for application '%s' (version: '%s'): %s", application_id, application_version, e
        )
        console.print(
            f"[warning]Warning:[/warning] Bad input to create run for application "
            f"'{application_id} (version: {application_version})': {e}"
        )
        sys.exit(2)
    except NotFoundException as e:
        logger.warning(
            "Could not find application version '%s' (version: '%s'): %s", application_id, application_version, e
        )
        console.print(
            f"[warning]Warning:[/warning] Could not find application '{application_id} "
            f"(version: {application_version})': {e}"
        )
        sys.exit(2)
    except (Exception, RuntimeError) as e:
        message = (
            f"Failed to load application version '{application_version}' for application '{application_id}': {e!s}."
        )
        logger.exception(message)
        console.print(f"[error]Error:[/error] {message}")
        sys.exit(1)

    try:
        metadata_dict = read_metadata_csv_to_dict(metadata_csv_file=metadata_csv_file)
        if not metadata_dict:
            console.print("Could mot read metadata file '%s'", metadata_csv_file)
            sys.exit(2)
        logger.debug(
            "Submitting run for application '%s' (version: '%s') with metadata: %s",
            application_id,
            app_version.version_number,
            metadata_dict,
        )
        application_run = Service().application_run_submit_from_metadata(
            application_id=application_id,
            metadata=metadata_dict,
            application_version=application_version,
            custom_metadata=None,  # TODO(Helmut): Add support for custom metadata
            note=note,
            due_date=due_date,
            deadline=deadline,
            onboard_to_aignostics_portal=onboard_to_aignostics_portal,
            validate_only=validate_only,
        )
        console.print(
            f"Submitted run with id '{application_run.run_id}' for "
            f"'{application_id} (version: {app_version.version_number})'."
        )
        return application_run.run_id
    except ValueError as e:
        logger.warning(
            "Bad input to create run for application '%s' (version: %s): %s",
            application_id,
            app_version.version_number,
            e,
        )
        console.print(
            f"[warning]Warning:[/warning] Bad input to create run for application "
            f"'{application_id} (version: {app_version.version_number})': {e}"
        )
        sys.exit(2)
    except Exception as e:
        logger.exception(
            "Failed to create run for application '%s' (version: %s)", application_id, app_version.version_number
        )
        console.print(
            f"[error]Error:[/error] Failed to create run for application "
            f"'{application_id} (version: {app_version.version_number})': {e}"
        )
        sys.exit(1)


@run_app.command("list")
def run_list(
    verbose: Annotated[bool, typer.Option(help="Show application details")] = False,
    limit: Annotated[int | None, typer.Option(help="Maximum number of runs to display")] = None,
) -> None:
    """List runs."""
    try:
        runs = Service().application_runs(limit=limit)
        if len(runs) == 0:
            message = "You did not yet create a run."
            logger.warning(message)
            console.print(message, style="warning")
        else:
            print_runs_verbose(runs) if verbose else print_runs_non_verbose(runs)
            message = f"Listed '{len(runs)}' run(s)."
            console.print(message, style="info")
            logger.info(message)
    except Exception as e:
        logger.exception("Failed to list runs")
        console.print(f"[error]Error:[/error] Failed to list runs: {e}")


@run_app.command("describe")
def run_describe(run_id: Annotated[str, typer.Argument(help="Id of the run to describe")]) -> None:
    """Describe run."""
    logger.debug("Describing run with ID '%s'", run_id)

    try:
        retrieve_and_print_run_details(Service().application_run(run_id))
        logger.info("Described run with ID '%s'", run_id)
    except NotFoundException:
        logger.warning("Run with ID '%s' not found.", run_id)
        console.print(f"[warning]Warning:[/warning] Run with ID '{run_id}' not found.")
        sys.exit(2)
    except Exception as e:
        logger.exception("Failed to retrieve and print run details for ID '%s'", run_id)
        console.print(f"[error]Error:[/error] Failed to retrieve run details for ID '{run_id}': {e}")
        sys.exit(1)


@run_app.command("cancel")
def run_cancel(
    run_id: Annotated[str, typer.Argument(..., help="Id of the run to cancel")],
) -> None:
    """Cancel run."""
    logger.debug("Canceling run with ID '%s'", run_id)

    try:
        Service().application_run_cancel(run_id)
        logger.info("Canceled run with ID '%s'.", run_id)
        console.print(f"Run with ID '{run_id}' has been canceled.")
    except NotFoundException:
        logger.warning("Run with ID '%s' not found.", run_id)
        console.print(f"[warning]Warning:[/warning] Run with ID '{run_id}' not found.")
        sys.exit(2)
    except ValueError:
        logger.warning("Run ID '%s' invalid", run_id)
        console.print(f"[warning]Warning:[/warning] Run ID '{run_id}' invalid.")
        sys.exit(2)
    except Exception as e:
        logger.exception("Failed to cancel run with ID '%s'", run_id)
        console.print(f"[bold red]Error:[/bold red] Failed to cancel run with ID '{run_id}': {e}")
        sys.exit(1)


@result_app.command("download")
def result_download(  # noqa: C901, PLR0913, PLR0915, PLR0917
    run_id: Annotated[str, typer.Argument(..., help="Id of the run to download results for")],
    destination_directory: Annotated[
        Path,
        typer.Argument(
            help="Destination directory to download results to",
            exists=False,
            file_okay=False,
            dir_okay=True,
            writable=True,
            readable=True,
            resolve_path=True,
        ),
    ] = get_user_data_directory("results"),  # noqa: B008
    create_subdirectory_for_run: Annotated[
        bool,
        typer.Option(
            help="Create a subdirectory for the results of the run in the destination directory",
        ),
    ] = True,
    create_subdirectory_per_item: Annotated[
        bool,
        typer.Option(
            help="Create a subdirectory per item in the destination directory",
        ),
    ] = True,
    wait_for_completion: Annotated[
        bool,
        typer.Option(
            help="Wait for run completion and download results incrementally",
        ),
    ] = True,
    qupath_project: Annotated[
        bool,
        typer.Option(
            help="Create a QuPath project referencing input slides and results. \n"
            "The QuPath project will be created in a subfolder of the destination directory. \n"
            "This option requires the QuPath extension for Launchpad: "
            'start the Launchpad with `uvx --with "aignostics[qupath]" aignostics ...` \n'
            "This options requires installation of the QuPath application: "
            'Run uvx --with "aignostics[qupath]" aignostics qupath install'
        ),
    ] = False,
) -> None:
    """Download results of a run."""
    logger.debug(
        "Downloading results for run with ID '%s' to '%s' with options: "
        "create_subdirectory_for_run=%s, create_subdirectory_per_item=%s, wait_for_completion=%s, qupath_project=%r",
        run_id,
        destination_directory,
        create_subdirectory_for_run,
        create_subdirectory_per_item,
        wait_for_completion,
        qupath_project,
    )
    from rich.console import Group  # noqa: PLC0415
    from rich.live import Live  # noqa: PLC0415
    from rich.panel import Panel  # noqa: PLC0415
    from rich.progress import (  # noqa: PLC0415
        BarColumn,
        FileSizeColumn,
        Progress,
        TaskID,
        TaskProgressColumn,
        TextColumn,
        TimeElapsedColumn,
        TimeRemainingColumn,
        TotalFileSizeColumn,
        TransferSpeedColumn,
    )

    try:
        download_tasks: dict[str, TaskID] = {}

        main_download_progress_ui = Progress(
            BarColumn(),
            TaskProgressColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            TextColumn("{task.fields[extra_description]}"),
        )
        artifact_download_progress_ui = Progress(
            BarColumn(),
            TaskProgressColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            FileSizeColumn(),
            TotalFileSizeColumn(),
            TransferSpeedColumn(),
            TextColumn("{task.fields[extra_description]}"),
        )
        panel = Panel(
            Group(main_download_progress_ui, artifact_download_progress_ui),
            title=f"Run {run_id}",
            subtitle="",
            highlight=True,
        )
        with Live(panel):
            main_task = main_download_progress_ui.add_task(description="", total=None, extra_description="")

            def update_progress(progress: DownloadProgress) -> None:
                """Update progress bar for file downloads."""
                if progress.run:
                    panel.title = (
                        f"Run {progress.run.run_id} of {progress.run.application_id} "
                        f"(version: {progress.run.version_number})"
                    )
                    panel.subtitle = f"Triggered at {progress.run.submitted_at.strftime('%a, %x %X')}"
                    if progress.item_count:
                        panel.subtitle += f" with {progress.item_count} " + (
                            "item" if progress.item_count == 1 else "items"
                        )
                    if progress.run.state is RunState.TERMINATED:
                        status_text = application_run_status_to_str(progress.run.state)
                        panel.subtitle += f", status: {status_text} ({progress.run.termination_reason})."
                    else:
                        panel.subtitle += f", status: {application_run_status_to_str(progress.run.state)}."
                main_download_progress_ui.update(
                    main_task,
                    description=(
                        progress.status
                        if progress.status is not DownloadProgressState.DOWNLOADING or not progress.total_artifact_index
                        else (
                            f"Downloading artifact {progress.total_artifact_index + 1} "
                            f"of {progress.total_artifact_count}"
                        )
                    ).ljust(50),
                )
                if progress.artifact_path:
                    task_key = str(progress.artifact_path.absolute())
                    if task_key not in download_tasks:
                        download_tasks[task_key] = artifact_download_progress_ui.add_task(
                            f"{progress.artifact_path.name}".ljust(50),
                            total=progress.artifact_size,
                            extra_description=f"Item {progress.item.external_id if progress.item else 'unknown'}",
                        )

                    artifact_download_progress_ui.update(
                        download_tasks[task_key],
                        total=progress.artifact_size,
                        advance=progress.artifact_downloaded_chunk_size,
                    )

                if (
                    progress.item_count
                    and progress.item_index is not None
                    and progress.artifact_count
                    and progress.artifact_index is not None
                ):
                    main_download_progress_ui.update(
                        main_task,
                        completed=progress.item_index * progress.artifact_count + progress.artifact_index + 1,
                        total=float(progress.total_artifact_count) if progress.total_artifact_count else 0.0,
                    )

            destination_directory = Service().application_run_download(
                run_id=run_id,
                destination_directory=destination_directory,
                create_subdirectory_for_run=create_subdirectory_for_run,
                create_subdirectory_per_item=create_subdirectory_per_item,
                wait_for_completion=wait_for_completion,
                qupath_project=qupath_project,
                download_progress_callable=update_progress,
            )

            main_download_progress_ui.update(main_task, completed=100, total=100)

        message = f"Downloaded results of run '{run_id}' to '{destination_directory}'"
        logger.info(message)
        console.print(message, style="info")
    except NotFoundException as e:
        logger.warning("Run with ID '%s' not found: %s", run_id, e)
        console.print(f"[warning]Warning:[/warning] Run with ID '{run_id}' not found.")
        sys.exit(2)
    except ValueError as e:
        logger.warning("Bad input to download results of run with ID '%s': %s", run_id, e)
        console.print(f"[warning]Warning:[/warning] Bad input to download results of run with ID '{run_id}': {e}")
        sys.exit(2)
    except Exception as e:
        logger.exception("Failed to download results of run with ID '%s'", run_id)
        console.print(
            f"[error]Error:[/error] Failed to download results of run with ID '{run_id}': {type(e).__name__}: {e}"
        )
        sys.exit(1)


@result_app.command("delete")
def result_delete(
    run_id: Annotated[str, typer.Argument(..., help="Id of the run to delete results for")],
) -> None:
    """Delete results of run."""
    logger.debug("Deleting results for run with ID '%s'", run_id)

    try:
        Service().application_run_delete(run_id)
        logger.info("Deleted run with ID '%s'.", run_id)
        console.print(f"Results for run with ID '{run_id}' have been deleted.")
    except NotFoundException:
        logger.warning("Results for with ID '%s' not found.", run_id)
        console.print(f"[warning]Warning:[/warning] Run with ID '{run_id}' not found.")
        sys.exit(2)
    except Exception as e:
        logger.exception("Failed to delete run with ID '%s'", run_id)
        console.print(f"[bold red]Error:[/bold red] Failed to delete results for with ID '{run_id}': {e}")
        sys.exit(1)
