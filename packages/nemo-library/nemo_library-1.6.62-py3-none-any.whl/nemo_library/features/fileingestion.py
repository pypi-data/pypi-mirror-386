import gzip
import logging
from pathlib import Path
import re
import shutil
import os
import tempfile
import time
import json
import requests
import boto3
from botocore.exceptions import NoCredentialsError
import pandas as pd

from nemo_library.features.nemo_persistence_api import (
    createColumns,
    getColumns,
    getProjectID,
)
from nemo_library.features.nemo_persistence_api import createProjects
from nemo_library.model.column import Column
from nemo_library.model.project import Project
from nemo_library.utils.config import Config
from nemo_library.utils.utils import (
    get_internal_name,
    log_error,
)
from nemo_library.features.import_configuration import ImportConfigurations

__all__ = ["ReUploadDataFrame", "ReUploadFile", "synchronizeCsvColsAndImportedColumns"]


def ReUploadDataFrame(
    config: Config,
    projectname: str,
    df: pd.DataFrame,
    update_project_settings: bool = True,
    datasource_ids: list[dict] | None = None,
    global_fields_mapping: list[dict] | None = None,
    version: int = 2,
    trigger_only: bool = False,
    import_configuration: ImportConfigurations | None = None,
    format_data: bool = True,
) -> None:

    # Default ImportConfigurations
    if import_configuration is None:
        import_configuration = ImportConfigurations()

    # format data? we need to import first and then use the upload dataframe api
    if format_data:
        df = _format_data(df, import_configuration)

    # check if project exists
    if not getProjectID(config, projectname):
        logging.info(f"Project {projectname} not found - create it")
        createProjects(config=config, projects=[Project(displayName=projectname)])

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file_path = os.path.join(temp_dir, "tempfile.csv")

        df.to_csv(
            temp_file_path,
            index=False,
            sep=import_configuration.field_delimiter,
            na_rep="",
            escapechar=import_configuration.escape_character,
            lineterminator=import_configuration.record_delimiter,
            quotechar=import_configuration.optionally_enclosed_by,
            encoding="UTF-8",
            doublequote=False,
        )
        logging.info(f"file {temp_file_path} written. Number of records: {len(df)}")

        ReUploadFile(
            config=config,
            projectname=projectname,
            filename=temp_file_path,
            update_project_settings=update_project_settings,
            datasource_ids=datasource_ids,
            global_fields_mapping=global_fields_mapping,
            version=version,
            trigger_only=trigger_only,
            import_configuration=import_configuration,
            format_data=False,  # already formatted, if parameter was given
        )
        logging.info(f"upload to project {projectname} completed")


def ReUploadFile(
    config: Config,
    projectname: str,
    filename: str,
    update_project_settings: bool = True,
    datasource_ids: list[dict] | None = None,
    global_fields_mapping: list[dict] | None = None,
    version: int = 2,
    trigger_only: bool = False,
    import_configuration: ImportConfigurations | None = None,
    format_data: bool = True,
) -> None:
    """
    Re-uploads a file to a specified project in the NEMO system and triggers data ingestion.

    Args:
        config (Config): Configuration object containing connection details and headers.
        projectname (str): The name of the project to which the file will be uploaded.
        filename (str): The path to the file to upload.
        update_project_settings (bool, optional): Whether to trigger the "analyze_table" task after ingestion (version 2 only). Defaults to True.
        datasource_ids (list[dict], optional): Data source identifiers for version 3 ingestion. Defaults to None.
        global_fields_mapping (list[dict], optional): Field mappings for version 3 ingestion. Defaults to None.
        version (int, optional): The ingestion version (2 or 3). Defaults to 2.
        trigger_only (bool, optional): If True, skips waiting for task completion. Defaults to False.

    Returns:
        None

    Raises:
        Exception: If any step of the file upload, data ingestion, or subsequent tasks fails.

    Notes:
        - Compresses the file into gzip format before uploading.
        - Retrieves temporary AWS S3 credentials from NEMO's Token Vendor and uploads the file to S3.
        - Sends a request to ingest the uploaded data and optionally waits for task completion.
        - Triggers "analyze_table" task if version 2 and `update_project_settings` is True.
        - Logs and raises exceptions for any errors encountered during the process.
    """

    # Default ImportConfigurations
    if import_configuration is None:
        import_configuration = ImportConfigurations()

    # HANA supports csv-files only. If the file has a different suffix, we need to convert this into csv first

    ext = Path(filename).suffix.lower()  # Holt die Endung und macht sie klein
    if ext != ".csv":
        if ext in [".xls", ".xlsx"]:
            df = pd.read_excel(filename)
        elif ext == ".json":
            df = pd.read_json(filename)
        elif ext in [".parquet"]:
            df = pd.read_parquet(filename)
        elif ext in [".h5", ".hdf"]:
            df = pd.read_hdf(filename)
        else:
            raise ValueError(
                f"File format {ext} not supported. Please use .csv, .xls, .xlsx, .json, .parquet, or .h5/.hdf files."
            )
        ReUploadDataFrame(
            config=config,
            projectname=projectname,
            df=df,
            update_project_settings=update_project_settings,
            datasource_ids=datasource_ids,
            global_fields_mapping=global_fields_mapping,
            version=version,
            trigger_only=trigger_only,
            import_configuration=import_configuration,
            format_data=format_data,
        )
        return  # stop procesisng here

    # format data? we need to import first and then use the upload dataframe api
    if format_data:
        df = pd.read_csv(
            filename,
            sep=import_configuration.field_delimiter,
        )
        ReUploadDataFrame(
            config=config,
            projectname=projectname,
            df=df,
            update_project_settings=update_project_settings,
            datasource_ids=datasource_ids,
            global_fields_mapping=global_fields_mapping,
            version=version,
            trigger_only=trigger_only,
            import_configuration=import_configuration,
            format_data=format_data,
        )
        return  # stop procesisng here

    project_id = None
    headers = None
    project_id = None
    gzipped_filename = None
    compress_level = 3
    try:
        filesize = _get_file_size(filename)

        logging.info(f"Size of the file: {filesize} MB")

        if filesize < 5:
            compress_level = 0
            logging.info(f"Compress Level: {compress_level}")

        project_id = getProjectID(config, projectname)
        if not project_id:
            logging.info(f"Project {projectname} not found - create it")
            createProjects(config=config, projects=[Project(displayName=projectname)])
            project_id = getProjectID(config, projectname)

        headers = config.connection_get_headers()

        logging.info(
            f"Upload of file '{filename}' into project '{projectname}' initiated..."
        )

        # Zip the file before uploading
        gzipped_filename = filename + ".gz"
        with open(filename, "rb") as f_in:
            with gzip.open(
                gzipped_filename, "wb", compresslevel=compress_level
            ) as f_out:
                shutil.copyfileobj(f_in, f_out)
        logging.info(f"File {filename} has been compressed to {gzipped_filename}")
        time.sleep(1)

        # Retrieve temporary credentials from NEMO TVM
        response = requests.get(
            config.get_config_nemo_url()
            + "/api/nemo-tokenvendor/InternalTokenVendor/sts/s3_policy",
            headers=headers,
        )

        if response.status_code != 200:
            raise Exception(
                f"Request failed. Status: {response.status_code}, error: {response.text}"
            )

        aws_credentials = json.loads(response.text)

        aws_access_key_id = aws_credentials["accessKeyId"]
        aws_secret_access_key = aws_credentials["secretAccessKey"]
        aws_session_token = aws_credentials["sessionToken"]

        # Create an S3 client
        s3 = boto3.client(
            "s3",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
        )

        try:
            # Upload the file
            s3filename = (
                config.get_tenant()
                + f"/ingestv{version}/"
                + os.path.basename(gzipped_filename)
            )
            s3.upload_file(
                gzipped_filename,
                "nemoinfrastructurestack-nemouploadbucketa98fe899-1s2ocvunlg3vs",
                s3filename,
            )
            logging.info(f"File {filename} uploaded successfully to s3 ({s3filename})")
        except FileNotFoundError:
            log_error(f"The file {filename} was not found.", FileNotFoundError)
        except NoCredentialsError:
            log_error(f"The file {filename} was not found.", NoCredentialsError)

        # Prepare data for ingestion

        data = {
            "project_id": project_id,
            "s3_filepath": f"s3://nemoinfrastructurestack-nemouploadbucketa98fe899-1s2ocvunlg3vs/{s3filename}",
            "configuration": import_configuration.to_dict(),
        }

        if version == 3:
            if datasource_ids is not None:
                data["data_source_identifiers"] = datasource_ids
            if global_fields_mapping is not None:
                data["global_fields_mappings"] = global_fields_mapping

        endpoint_url = (
            "/api/nemo-queue/ingest_data_kubernetes_v3"
            if version == 3
            else "/api/nemo-queue/ingest_data_kubernetes_v2"
        )

        response = requests.post(
            config.get_config_nemo_url() + endpoint_url,
            headers=headers,
            json=data,
        )
        if response.status_code != 200:
            raise Exception(
                f"Request failed. Status: {response.status_code}, error: {response.text}"
            )
        logging.info("Ingestion successful")

        # Wait for task to be completed if not trigger_only
        if version == 2 or not trigger_only:
            taskid = response.text.replace('"', "")
            while True:
                data = {
                    "sort_by": "submit_at",
                    "is_sort_ascending": "False",
                    "page": 1,
                    "page_size": 20,
                }
                response = requests.get(
                    config.get_config_nemo_url() + "/api/nemo-queue/task_runs",
                    headers=headers,
                    json=data,
                )
                if response.status_code != 200:
                    raise Exception(
                        f"Request failed. Status: {response.status_code}, error: {response.text}"
                    )
                resultjs = json.loads(response.text)
                df = pd.json_normalize(resultjs["records"])
                df_filtered = df[df["id"] == taskid]
                if len(df_filtered) != 1:
                    raise Exception(
                        f"Data ingestion request failed, task ID not found in tasks list"
                    )
                status = df_filtered["status"].iloc[0]
                logging.info(f"Status: {status}")
                if status == "failed":
                    log_error("Data ingestion request failed, status: FAILED")
                if status == "finished":
                    if version == 2:
                        records = df_filtered["records"].iloc[0]
                        logging.info(f"Ingestion finished. {records} records loaded")
                    else:
                        logging.info("Ingestion finished.")
                    break
                time.sleep(1 if version == 2 else 5)

        # Trigger Analyze Table Task for version 2 if required
        if version == 2 and update_project_settings:
            data = {
                "project_id": project_id,
            }
            response = requests.post(
                config.get_config_nemo_url()
                + "/api/nemo-queue/analyze_table_kubernetes",
                headers=headers,
                json=data,
            )
            if response.status_code != 200:
                raise Exception(
                    f"Request failed. Status: {response.status_code}, error: {response.text}"
                )
            logging.info("Analyze_table triggered")

            # Wait for task to be completed
            taskid = response.text.replace('"', "")
            while True:
                data = {
                    "sort_by": "submit_at",
                    "is_sort_ascending": "False",
                    "page": 1,
                    "page_size": 20,
                }
                response = requests.get(
                    config.get_config_nemo_url() + "/api/nemo-queue/task_runs",
                    headers=headers,
                    json=data,
                )
                if response.status_code != 200:
                    raise Exception(
                        f"Request failed. Status: {response.status_code}, error: {response.text}"
                    )
                resultjs = json.loads(response.text)
                df = pd.json_normalize(resultjs["records"])
                df_filtered = df[df["id"] == taskid]
                if len(df_filtered) != 1:
                    raise Exception(
                        f"Analyze_table request failed, task ID not found in tasks list"
                    )
                status = df_filtered["status"].iloc[0]
                logging.info(f"Status: {status}")
                if status == "failed":
                    log_error("Analyze_table request failed, status: FAILED")
                if status == "finished":
                    logging.info("Analyze_table finished.")
                    break
                time.sleep(1)

    except Exception as e:
        if project_id is None:
            log_error("Upload stopped, no project_id available")
        raise log_error(f"Upload aborted: {e}")

    finally:
        if gzipped_filename:
            os.remove(gzipped_filename)


def _get_file_size(filepath: str):
    # filesize in byte
    filesize_in_byte = os.path.getsize(filepath)
    # byte to MB (1 MB = 1024 * 1024 Byte)
    filesize_in_mb = filesize_in_byte / (1024 * 1024)
    return filesize_in_mb


def _format_data(
    df: pd.DataFrame,
    import_configuration: ImportConfigurations,
) -> pd.DataFrame:
    # List of special characters that should be escaped
    SPECIAL_CHARS = [
        r'"',  # Standard straight double quotes
        r"“",  # Opening typographic double quotes
        r"”",  # Closing typographic double quotes
        r"„",  # German opening double quotes (low)
        r"'",  # Standard straight single quotes
        r"«",  # French double angle quotes (Guillemets, opening)
        r"»",  # French double angle quotes (Guillemets, closing)
        r"‹",  # Single angle quotes (Guillemets, opening)
        r"›",  # Single angle quotes (Guillemets, closing)
        r"‘",  # Opening typographic single quotes
        r"’",  # Closing typographic single quotes
    ]

    # Characters to remove completely (not escape)
    REMOVE_CHARS = [
        "\n",  # Line Feed
        "\r",  # Carriage Return
    ]

    # we don't escape the quoting character since this will be escaped by pandas to_csv later
    if import_configuration.optionally_enclosed_by in SPECIAL_CHARS:
        SPECIAL_CHARS.remove(import_configuration.optionally_enclosed_by)

    # Ensure escape character is included
    if import_configuration.escape_character not in SPECIAL_CHARS:
        SPECIAL_CHARS.append(import_configuration.escape_character)

    def escape_special_chars(value):
        if isinstance(value, str):
            # Escape special characters
            for char in SPECIAL_CHARS:
                value = re.sub(
                    re.escape(char),
                    f"{import_configuration.escape_character}{char}",
                    value,
                )
            # Remove characters that cannot be escaped
            for char in REMOVE_CHARS:
                value = value.replace(char, "")
        return value

    str_columns = df.select_dtypes(include=["object", "string"]).columns
    for col in str_columns:
        df[col] = df[col].map(escape_special_chars)

    return df


def synchronizeCsvColsAndImportedColumns(
    config: Config,
    projectname: str,
    filename: str,
) -> None:
    """
    Synchronizes the columns from a CSV file with the imported columns in a specified project.

    Args:
        config (Config): Configuration object containing connection details and headers.
        projectname (str): The name of the project where the synchronization will occur.
        filename (str): The path to the CSV file to synchronize.

    Returns:
        None

    Raises:
        RuntimeError: If there are issues retrieving imported columns or reading the CSV file.

    Notes:
        - Retrieves the existing imported columns in the project using `getImportedColumns`.
        - Reads the first line of the CSV file to get column names.
        - Compares the column names from the CSV file with the imported columns.
        - Creates new imported columns in the project for any CSV column names not already present.
        - Uses utility functions `display_name`, `internal_name`, and `import_name` to format column names.
    """
    cols = getColumns(config, projectname)
    cols_internal = [col.internalName for col in cols]

    # Read the first line of the CSV file to get column names
    with open(filename, "r") as file:
        first_line = file.readline().strip()

    # Split the first line into a list of column names
    csv_display_names = first_line.split(";")
    csv_display_names = [x.strip('"') for x in csv_display_names]

    # Check if a record exists in the DataFrame for each column
    new_columns = []
    for column_name in csv_display_names:

        # Check if the record with internal_name equal to the column name exists
        if get_internal_name(column_name) in cols_internal:
            logging.info(f"Record found for column '{column_name}' in the DataFrame.")
        else:
            logging.info(
                f"No record found for column '{column_name}' in the DataFrame - create it."
            )
            new_columns.append(
                Column(
                    displayName=column_name, dataType="string", columnType="ExportedColumn"
                )
            )

    if new_columns:
        createColumns(
            config=config, projectname=projectname, columns=new_columns
        )
