# Copyright 2024-2025 MOSTLY AI
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import logging
import math
import uuid
import zipfile
from pathlib import Path
from typing import Literal

import pandas as pd

from mostlyai.sdk._data.base import ForeignKey, NonContextRelation, Schema
from mostlyai.sdk._data.dtype import is_timestamp_dtype
from mostlyai.sdk._data.file.base import LocalFileContainer
from mostlyai.sdk._data.file.table.csv import CsvDataTable
from mostlyai.sdk._data.file.table.parquet import ParquetDataTable
from mostlyai.sdk._data.non_context import PartitionedDataset, assign_non_context_fks_randomly, match_non_context
from mostlyai.sdk._data.progress_callback import ProgressCallback, ProgressCallbackWrapper
from mostlyai.sdk._data.util.common import (
    IS_NULL,
    NON_CONTEXT_COLUMN_INFIX,
)
from mostlyai.sdk._local.storage import get_model_label
from mostlyai.sdk.domain import Generator, ModelType, SyntheticDataset

_LOG = logging.getLogger(__name__)

# FK processing constants
FK_MIN_CHILDREN_BATCH_SIZE = 10
FK_PARENT_BATCH_SIZE = 1000


def execute_step_finalize_generation(
    *,
    schema: Schema,
    is_probe: bool,
    job_workspace_dir: Path,
    update_progress: ProgressCallback | None = None,
) -> dict[str, int]:
    # get synthetic table usage
    usages = dict()
    for table_name, table in schema.tables.items():
        usages.update({table_name: table.row_count})
    # short circuit for probing
    delivery_dir = job_workspace_dir / "FinalizedSyntheticData"
    if is_probe:
        for table_name in schema.tables:
            finalize_table_generation(
                generated_data_schema=schema,
                target_table_name=table_name,
                delivery_dir=delivery_dir,
                export_csv=False,
                job_workspace_dir=job_workspace_dir,
            )
        return usages

    random_samples_dir = job_workspace_dir / "RandomSamples"
    zip_dir = job_workspace_dir / "ZIP"

    # calculate total datapoints (rows × columns) across all tables
    total_datapoints = sum(table.row_count * len(table.columns) for table in schema.tables.values())
    export_csv = total_datapoints < 100_000_000  # only export CSV if datapoints < 100M

    with ProgressCallbackWrapper(update_progress, description="Finalize generation") as progress:
        # init progress with total_count; +4 for the 4 steps below
        progress.update(completed=0, total=len(schema.tables) + 4)

        for tgt in schema.tables:
            finalize_table_generation(
                generated_data_schema=schema,
                target_table_name=tgt,
                delivery_dir=delivery_dir,
                export_csv=export_csv,
                job_workspace_dir=job_workspace_dir,
            )
            progress.update(advance=1)

        _LOG.info("export random samples")
        export_random_samples(
            delivery_dir=delivery_dir,
            random_samples_dir=random_samples_dir,
        )
        progress.update(advance=1)

        _LOG.info("export synthetic data to excel")
        export_data_to_excel(delivery_dir=delivery_dir, output_dir=zip_dir)
        progress.update(advance=1)

        _LOG.info("zip parquet synthetic data")
        zip_data(delivery_dir=delivery_dir, format="parquet", out_dir=zip_dir)
        progress.update(advance=1)

        if export_csv:
            _LOG.info("zip csv synthetic data")
            zip_data(delivery_dir=delivery_dir, format="csv", out_dir=zip_dir)
            progress.update(advance=1)

        return usages


def update_total_rows(synthetic_dataset: SyntheticDataset, usages: dict[str, int]) -> None:
    for table_name, total_rows in usages.items():
        table = next(t for t in synthetic_dataset.tables if t.name == table_name)
        table.total_rows = total_rows


def format_datetime(df: pd.DataFrame) -> pd.DataFrame:
    for column in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[column]):
            df[column] = df[column].dt.strftime("%Y-%m-%d %H:%M:%S")
    return df


def postprocess_temp_columns(df: pd.DataFrame, table_name: str, schema: Schema):
    """
    1. remove the suffix of non-context temporary columns `.{parent_table_name}._is_null`
    2. in these columns, replace "True" with a UUID and "False" with pd.NA
    """

    # a variation of mostlyai.sdk._data.non_context.postproc_non_context()
    for relation in schema.relations:
        if not isinstance(relation, NonContextRelation) or relation.child.table != table_name:
            continue
        suffix = NON_CONTEXT_COLUMN_INFIX.join(["", relation.parent.table, IS_NULL])
        temp_columns = [column for column in df.columns if column.endswith(suffix)]
        # fill in some random UUIDs for
        # note: these columns contains strings of boolean values
        for col in temp_columns:
            df[col] = df[col].apply(lambda x: f"mostly{str(uuid.uuid4())[6:]}" if x == "False" else pd.NA)
        # remove suffix
        df.rename(
            columns={c: c.removesuffix(suffix) for c in temp_columns},
            inplace=True,
        )

    return df


def restore_column_order(df: pd.DataFrame, table_name: str, schema: Schema):
    # keep columns in its original order but ignore those which does not exist in the dataframe
    # (e.g., LANGUAGE columns)
    original_columns = [column for column in schema.tables[table_name].columns if column in df.columns]
    df = df[original_columns]
    return df


def export_random_samples_per_table(
    delivery_parquet_dir: Path,
    random_samples_json_path: Path,
    table_name: str,
    schema: Schema | None = None,
    limit: int = 100,
):
    """
    Export random samples of a table from the first parquet file in delivery_parquet_dir
    """
    try:
        # fetch a single parquet file
        parquet_path = next(delivery_parquet_dir.glob("*.parquet"))
    except StopIteration:
        parquet_path = None

    if parquet_path:
        df = pd.read_parquet(parquet_path).sample(frac=1).head(n=limit)
        df = format_datetime(df)
        if schema:
            df = postprocess_temp_columns(df, table_name, schema)
            df = restore_column_order(df, table_name, schema)
        df.to_json(random_samples_json_path, orient="records")
        _LOG.info(f"Export {len(df)} random samples to `{random_samples_json_path}`")


def export_random_samples(
    delivery_dir: Path,
    random_samples_dir: Path,
    limit: int = 100,
):
    """
    Export random samples of all the tables in the delivery directory
    """
    random_samples_dir.mkdir(exist_ok=True, parents=True)
    for path in delivery_dir.glob("*"):
        table_name = path.name
        export_random_samples_per_table(
            delivery_parquet_dir=delivery_dir / table_name / "parquet",
            random_samples_json_path=random_samples_dir / f"{table_name}.json",
            table_name=table_name,
            limit=limit,
        )


def filter_and_order_columns(data: pd.DataFrame, table_name: str, schema: Schema) -> pd.DataFrame:
    """Keep only original columns in the right order."""
    tgt_cols = schema.tables[table_name].columns or data.columns
    drop_cols = [c for c in tgt_cols if c not in data]
    if drop_cols:
        _LOG.info(f"remove columns from final output: {', '.join(drop_cols)}")
    keep_cols = [c for c in tgt_cols if c in data]
    return data[keep_cols]


def write_batch_outputs(
    data: pd.DataFrame, table_name: str, batch_counter: int, pqt_path: Path, csv_path: Path | None
) -> None:
    """Write batch to parquet and optionally CSV."""
    batch_filename = f"part.{batch_counter:06d}.parquet"
    _LOG.info(f"store post-processed batch {batch_counter} ({len(data)} rows) as PQT")
    pqt_post = ParquetDataTable(path=pqt_path / batch_filename, name=table_name)
    pqt_post.write_data(data)

    if csv_path:
        _LOG.info(f"store post-processed batch {batch_counter} as CSV")
        csv_post = CsvDataTable(path=csv_path / f"{table_name}.csv", name=table_name)
        csv_post.write_data(data, if_exists="append")


def setup_output_paths(delivery_dir: Path, target_table_name: str, export_csv: bool) -> tuple[Path, Path | None]:
    """Create output directories for parquet and optionally CSV."""
    pqt_path = delivery_dir / target_table_name / "parquet"
    pqt_path.mkdir(exist_ok=True, parents=True)
    _LOG.info(f"prepared {pqt_path=} for storing post-processed data as PQT files")

    csv_path = None
    if export_csv:
        csv_path = delivery_dir / target_table_name / "csv"
        csv_path.mkdir(exist_ok=True, parents=True)
        _LOG.info(f"prepared {csv_path=} for storing post-processed data as CSV file")

    return pqt_path, csv_path


def are_fk_models_available(job_workspace_dir: Path, target_table_name: str) -> bool:
    """Check if FK models are available for the given table."""
    fk_models_dir = job_workspace_dir / "FKModelsStore" / target_table_name
    has_fk_models = fk_models_dir.exists() and any(fk_models_dir.glob("*/model_weights.pt"))
    return has_fk_models


def process_table_with_random_fk_assignment(
    table_name: str,
    schema: Schema,
    pqt_path: Path,
    csv_path: Path | None,
) -> None:
    """Process table with random FK assignment, partition by partition."""
    table = schema.tables[table_name]
    dataset = PartitionedDataset(table)

    for partition_idx, _, partition_data in dataset.iter_partitions():
        _LOG.info(f"Processing partition {partition_idx + 1} ({len(partition_data)} rows)")
        processed_data = assign_non_context_fks_randomly(
            tgt_data=partition_data,
            generated_data_schema=schema,
            tgt=table_name,
        )
        processed_data = filter_and_order_columns(processed_data, table_name, schema)
        write_batch_outputs(processed_data, table_name, partition_idx, pqt_path, csv_path)


def calculate_optimal_child_batch_size_for_relation(
    parent_dataset: PartitionedDataset,
    children_dataset: PartitionedDataset,
    parent_batch_size: int,
    relation_name: str,
) -> int:
    """Calculate optimal child batch size for a specific FK relationship."""
    total_children = len(children_dataset)
    parent_size = len(parent_dataset)
    num_parent_batches = max(1, math.ceil(parent_size / parent_batch_size))

    # ideal batch size for full parent utilization
    ideal_batch_size = total_children // num_parent_batches

    # apply minimum batch size constraint
    optimal_batch_size = max(ideal_batch_size, FK_MIN_CHILDREN_BATCH_SIZE)

    # log utilization metrics
    num_child_batches = total_children // optimal_batch_size
    parent_utilization = min(num_child_batches / num_parent_batches * 100, 100)

    _LOG.info(
        f"[{relation_name}] Batch size optimization | "
        f"total_children: {total_children} | "
        f"parent_size: {parent_size} | "
        f"parent_batch_size: {parent_batch_size} | "
        f"parent_batches: {num_parent_batches} | "
        f"ideal_child_batch: {ideal_batch_size} | "
        f"optimal_child_batch: {optimal_batch_size} | "
        f"parent_utilization: {parent_utilization:.1f}%"
    )

    return optimal_batch_size


def assign_parent_partition_round_robin(
    parent_dataset: PartitionedDataset,
    child_batch_idx: int,
    parent_batch_size: int,
) -> pd.DataFrame:
    """Assign parent data partition using round robin strategy."""
    parent_dataset_size = len(parent_dataset)
    start_idx = (child_batch_idx * parent_batch_size) % parent_dataset_size
    end_idx = min(start_idx + parent_batch_size, parent_dataset_size)

    # handle wrap-around to beginning if batch spans end boundary
    if end_idx - start_idx < parent_batch_size and parent_dataset_size > parent_batch_size:
        first_part = parent_dataset[start_idx:end_idx]
        remaining_needed = parent_batch_size - (end_idx - start_idx)
        second_part = parent_dataset[0:remaining_needed]
        assigned_parent_data = pd.concat([first_part, second_part], ignore_index=True)
    else:
        assigned_parent_data = parent_dataset[start_idx:end_idx]

    return assigned_parent_data


def process_table_with_fk_models(
    *,
    table_name: str,
    schema: Schema,
    pqt_path: Path,
    csv_path: Path | None,
    parent_batch_size: int = FK_PARENT_BATCH_SIZE,
    job_workspace_dir: Path,
) -> None:
    """Process table with ML model-based FK assignment using natural dataset partitions and per-relationship batch sizes."""

    fk_models_workspace_dir = job_workspace_dir / "FKModelsStore" / table_name
    non_ctx_relations = [rel for rel in schema.non_context_relations if rel.child.table == table_name]
    children_table = schema.tables[table_name]
    children_dataset = PartitionedDataset(children_table)
    parent_datasets = {}
    for relation in non_ctx_relations:
        parent_table_name = relation.parent.table
        if parent_table_name not in parent_datasets:
            parent_table = schema.tables[parent_table_name]
            parent_datasets[parent_table_name] = PartitionedDataset(parent_table)

    # calculate optimal batch size for each relationship
    relationship_batch_sizes = {}
    for relation in non_ctx_relations:
        parent_table_name = relation.parent.table
        parent_dataset = parent_datasets[parent_table_name]
        relation_name = f"{relation.child.table}.{relation.child.column}->{parent_table_name}"

        optimal_batch_size = calculate_optimal_child_batch_size_for_relation(
            parent_dataset=parent_dataset,
            children_dataset=children_dataset,
            parent_batch_size=parent_batch_size,
            relation_name=relation_name,
        )
        relationship_batch_sizes[relation] = optimal_batch_size

    # process data using natural dataset partitions with buffering
    relationship_batch_indices = {relation: 0 for relation in non_ctx_relations}
    leftover_buffers = {}  # incomplete batches buffered for next partition

    total_partitions = len(children_dataset.files)

    for partition_idx, _, partition_data in children_dataset.iter_partitions():
        is_final_partition = partition_idx == total_partitions - 1

        _LOG.info(f"Processing partition {partition_idx + 1} ({len(partition_data)} rows)")

        for relation in non_ctx_relations:
            parent_table_name = relation.parent.table
            parent_dataset = parent_datasets[parent_table_name]
            relation_name = f"{relation.child.table}.{relation.child.column}->{parent_table_name}"
            optimal_batch_size = relationship_batch_sizes[relation]

            current_data = partition_data.copy()
            if relation in leftover_buffers:
                current_data = pd.concat([leftover_buffers[relation], current_data], ignore_index=True)
                del leftover_buffers[relation]

            _LOG.info(f"  Processing relationship {relation_name} with batch size {optimal_batch_size}")

            processed_chunks = []

            for chunk_start in range(0, len(current_data), optimal_batch_size):
                chunk_end = min(chunk_start + optimal_batch_size, len(current_data))
                chunk_data = current_data.iloc[chunk_start:chunk_end].copy()

                # process complete batches and final batches; buffer incomplete batches
                is_complete_batch = chunk_end - chunk_start == optimal_batch_size
                is_final_batch = is_final_partition and (chunk_end == len(current_data))

                if is_complete_batch or is_final_batch:
                    current_batch_idx = relationship_batch_indices[relation]
                    assigned_parent_data = assign_parent_partition_round_robin(
                        parent_dataset, current_batch_idx, parent_batch_size
                    )

                    processed_chunk = match_non_context(
                        fk_models_workspace_dir=fk_models_workspace_dir,
                        tgt_data=chunk_data,
                        parent_data=assigned_parent_data,
                        tgt_parent_key=relation.child.column,
                        parent_primary_key=relation.parent.column,
                        parent_table_name=parent_table_name,
                    )

                    processed_chunks.append(processed_chunk)
                    relationship_batch_indices[relation] += 1
                else:
                    leftover_buffers[relation] = chunk_data
                    break

            if processed_chunks:
                partition_data = pd.concat(processed_chunks, ignore_index=True)

            parent_datasets[parent_table_name].clear_cache()

        partition_data = filter_and_order_columns(partition_data, table_name, schema)

        write_batch_outputs(partition_data, table_name, partition_idx, pqt_path, csv_path)

        del partition_data


def finalize_table_generation(
    generated_data_schema: Schema,
    target_table_name: str,
    delivery_dir: Path,
    export_csv: bool,
    job_workspace_dir: Path,
) -> None:
    """
    Post-process the generated data for a given table.
    * handle non-context keys (using FK models if available)
    * handle reference keys
    * keep only needed columns, and in the right order
    * export to PARQUET, and optionally also to CSV (without col prefixes)
    """

    pqt_path, csv_path = setup_output_paths(delivery_dir, target_table_name, export_csv)
    fk_models_available = are_fk_models_available(job_workspace_dir, target_table_name)
    fk_models_failed = False

    if fk_models_available:
        try:
            _LOG.info(f"Assigning non context FKs (if exists) through FK models for table {target_table_name}")
            process_table_with_fk_models(
                table_name=target_table_name,
                schema=generated_data_schema,
                pqt_path=pqt_path,
                csv_path=csv_path,
                job_workspace_dir=job_workspace_dir,
            )
        except Exception as e:
            _LOG.error(f"Non context FKs assignment through FK models failed for table {target_table_name}: {e}")
            fk_models_failed = True

    if not fk_models_available or fk_models_failed:
        _LOG.info(f"Assigning non context FKs (if exists) through random assignment for table {target_table_name}")
        process_table_with_random_fk_assignment(
            table_name=target_table_name,
            schema=generated_data_schema,
            pqt_path=pqt_path,
            csv_path=csv_path,
        )


def export_data_to_excel(delivery_dir: Path, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    # gather data for export
    tables = {}
    is_truncated = False
    is_truncated_note1 = "Note, that this XLSX file only includes a limited number of synthetic samples for each table."
    is_truncated_note2 = "Please refer to alternative download formats, to access the complete generated dataset."
    for table_path in sorted(delivery_dir.glob("*")):
        table_name = table_path.name
        samples = None
        total_row_count = 0
        target_sample_count = 10_000

        for parquet_path in (table_path / "parquet").glob("*.parquet"):
            # fetch a single parquet file at a time
            df = pd.read_parquet(parquet_path)
            total_row_count += df.shape[0]
            if samples is None:
                # attempt to sample from the first partition
                samples = df.head(n=target_sample_count)
                samples = format_datetime(samples)
            else:
                # concatenate samples from different partitions if needed
                remaining_samples = target_sample_count - samples.shape[0]
                if remaining_samples > 0:
                    samples = pd.concat(
                        [samples, df.head(n=remaining_samples)],
                        axis=0,
                        ignore_index=True,
                    )
                else:
                    break

        samples = pd.DataFrame() if samples is None else samples

        _LOG.info(f"Exporting table {table_name}: sampling {samples.shape[0]} from {total_row_count} rows")
        tables[table_name] = {
            "data": samples,
            "no_of_included_samples": samples.shape[0],
            "no_of_total_samples": total_row_count,
        }
        if samples.shape[0] < total_row_count:
            is_truncated = True

    # define base format for the excel file
    base_format = {
        "font_color": "#434343",
        "font_name": "Verdana",
        "font_size": 7,
        "valign": "vcenter",
    }

    excel_output_path = Path(output_dir) / "synthetic-samples.xlsx"
    with pd.ExcelWriter(str(excel_output_path), engine="xlsxwriter") as writer:
        workbook = writer.book

        # add formats
        cell_format = workbook.add_format(base_format)
        header_format = workbook.add_format(base_format | {"bold": True, "align": "left"})
        int_format = workbook.add_format(base_format | {"num_format": "#,##0"})
        dt_format = workbook.add_format(base_format | {"num_format": "yyyy-mm-dd"})

        # write a Table of Contents
        toc_sheet_name = "_TOC_"
        worksheet = workbook.add_worksheet(toc_sheet_name)
        worksheet.set_column("A:A", width=40, cell_format=header_format)
        worksheet.set_column("B:C", width=20, cell_format=int_format)
        worksheet.write(0, 0, "Table")
        worksheet.write(0, 1, "No. of Included Samples")
        worksheet.write(0, 2, "No. of Total Samples")
        if is_truncated:
            worksheet.write(len(tables) + 3, 0, is_truncated_note1)
            worksheet.write(len(tables) + 4, 0, is_truncated_note2)
        for idx, (table_name, _) in enumerate(tables.items()):
            worksheet.write_url(
                idx + 1,
                0,
                url=f"internal:'{table_name}'!A1",
                string=table_name,
                cell_format=cell_format,
            )
            worksheet.write(idx + 1, 1, tables[table_name]["no_of_included_samples"])
            worksheet.write(idx + 1, 2, tables[table_name]["no_of_total_samples"])

        # write each DataFrame to a different sheet
        sheet_names_lower = [toc_sheet_name.lower()]
        for table_name, table in tables.items():
            df = table["data"]
            # create a valid sheet name
            sheet_name = table_name[:28]  # consider max sheet name length
            while sheet_name.lower() in sheet_names_lower:
                sheet_name += "_"  # make sheet name unique, with case ignored
            sheet_names_lower.append(sheet_name.lower())
            # add the worksheet
            worksheet = workbook.add_worksheet(sheet_name)
            # set formats, plus adjust the column width for better readability
            for i, column in enumerate(df.columns):
                if is_timestamp_dtype(df[column]):
                    format = dt_format
                else:
                    format = cell_format
                worksheet.set_column(
                    first_col=i,
                    last_col=i,
                    width=12,
                    cell_format=format,
                )
            # set format of header row
            worksheet.set_row(0, height=None, cell_format=header_format)
            # Set the autofilter
            worksheet.autofilter(0, 0, len(df), len(df.columns) - 1)
            # freeze the first row
            worksheet.freeze_panes(1, 0)
            # write column headers
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value)
            # write data
            for row_num, row in enumerate(df.values):
                for col_num, _ in enumerate(row):
                    value = df.iloc[row_num, col_num]
                    if not pd.isna(value):
                        worksheet.write(row_num + 1, col_num, df.iloc[row_num, col_num])


def zip_data(delivery_dir: Path, format: Literal["parquet", "csv"], out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = out_dir / f"synthetic-{format}-data.zip"

    # Choose the compression type based on the file format
    compression = zipfile.ZIP_STORED if format == "parquet" else zipfile.ZIP_DEFLATED

    with zipfile.ZipFile(zip_path, "w", compression) as zipf:
        for table_path in delivery_dir.glob("*"):
            table = table_path.name
            format_path = table_path / format
            for file in format_path.glob("*"):
                zip_loc = f"{table}/{file.relative_to(format_path)}"
                zipf.write(file, arcname=zip_loc)


def create_generation_schema(
    generator: Generator,
    job_workspace_dir: Path,
    step: Literal["pull_context_data", "finalize_generation", "deliver_data"],
) -> Schema:
    tables = {}
    for table in generator.tables:
        # create LocalFileContainer
        container = LocalFileContainer()
        model_label = get_model_label(table, ModelType.tabular, path_safe=True)
        location = str(job_workspace_dir / model_label / "SyntheticData")
        container.set_location(location)
        if step == "pull_context_data":
            columns = None  # HACK: read lazily prefixed columns from parquet file
            is_output = False  # enable lazy reading of properties
        elif step == "finalize_generation":
            columns = [c.name for c in table.columns if c.included]  # use un-prefixed column names
            is_output = False  # enable lazy reading of properties
        elif step == "deliver_data":
            columns = [c.name for c in table.columns if c.included]  # use un-prefixed column names
            is_output = True
        else:
            raise ValueError(f"Unsupported step: {step}")
        # create ParquetDataTable
        data_table = ParquetDataTable(container=container)
        data_table.name = table.name
        data_table.primary_key = table.primary_key
        data_table.columns = columns
        data_table.encoding_types = {c.name: c.model_encoding_type for c in table.columns if c.included}
        data_table.is_output = is_output
        data_table.foreign_keys = [
            ForeignKey(column=fk.column, referenced_table=fk.referenced_table, is_context=fk.is_context)
            for fk in table.foreign_keys or []
        ]
        tables[table.name] = data_table
    schema = Schema(tables=tables)
    schema.preprocess_schema_before_pull()
    return schema
