# Copyright 2025 MOSTLY AI
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

"""
Provides analysis functionality of the engine
"""

import logging
import time
from collections.abc import Iterable
from pathlib import Path
from typing import Any, Literal

import numpy as np
import pandas as pd
from joblib import Parallel, cpu_count, delayed, parallel_config

from mostlyai.engine._common import (
    ANALYZE_REDUCE_MIN_MAX_N,
    ARGN_COLUMN,
    ARGN_PROCESSOR,
    ARGN_TABLE,
    CTXFLT,
    CTXSEQ,
    TABLE_COLUMN_INFIX,
    TGT,
    ProgressCallback,
    ProgressCallbackWrapper,
    dp_quantiles,
    get_stochastic_rare_threshold,
    is_a_list,
    is_sequential,
    read_json,
    write_json,
)
from mostlyai.engine._encoding_types.language.categorical import (
    analyze_language_categorical,
    analyze_reduce_language_categorical,
)
from mostlyai.engine._encoding_types.language.datetime import (
    analyze_language_datetime,
    analyze_reduce_language_datetime,
)
from mostlyai.engine._encoding_types.language.numeric import analyze_language_numeric, analyze_reduce_language_numeric
from mostlyai.engine._encoding_types.language.text import (
    analyze_reduce_text,
    analyze_text,
)
from mostlyai.engine._encoding_types.tabular.categorical import (
    analyze_categorical,
    analyze_reduce_categorical,
)
from mostlyai.engine._encoding_types.tabular.character import (
    analyze_character,
    analyze_reduce_character,
)
from mostlyai.engine._encoding_types.tabular.datetime import (
    analyze_datetime,
    analyze_reduce_datetime,
)
from mostlyai.engine._encoding_types.tabular.itt import analyze_itt, analyze_reduce_itt
from mostlyai.engine._encoding_types.tabular.lat_long import (
    analyze_latlong,
    analyze_reduce_latlong,
)
from mostlyai.engine._encoding_types.tabular.numeric import (
    analyze_numeric,
    analyze_reduce_numeric,
)
from mostlyai.engine._workspace import (
    PathDesc,
    Workspace,
    ensure_workspace_dir,
    reset_dir,
)
from mostlyai.engine.domain import DifferentialPrivacyConfig, ModelEncodingType
from mostlyai.engine.random_state import set_random_state

_LOG = logging.getLogger(__name__)

_VALUE_PROTECTION_ENCODING_TYPES = (
    ModelEncodingType.tabular_categorical,
    ModelEncodingType.tabular_numeric_digit,
    ModelEncodingType.tabular_numeric_discrete,
    ModelEncodingType.tabular_numeric_binned,
    ModelEncodingType.tabular_datetime,
    ModelEncodingType.tabular_datetime_relative,
    ModelEncodingType.language_categorical,
    ModelEncodingType.language_numeric,
    ModelEncodingType.language_datetime,
)


def analyze(
    *,
    value_protection: bool = True,
    differential_privacy: DifferentialPrivacyConfig | None = None,
    workspace_dir: str | Path = "engine-ws",
    update_progress: ProgressCallback | None = None,
) -> None:
    """
    Generates (privacy-safe) column-level statistics of the original data, that has been `split` into the workspace.
    This information is required for encoding the original as well as for decoding the generating data.

    Creates the following folder structure within the `workspace_dir`:

    - `ModelStore/tgt-stats/stats.json`: Column-level statistics for target data
    - `ModelStore/ctx-stats/stats.json`: Column-level statistics for context data (if context is provided).

    Args:
        value_protection: Whether to enable value protection for rare values.
        workspace_dir: Path to workspace directory containing partitioned data.
        update_progress: Optional callback to update progress during analysis.
    """

    _LOG.info("ANALYZE started")
    t0 = time.time()
    with ProgressCallbackWrapper(update_progress) as progress:
        # build paths based on workspace dir
        workspace_dir = ensure_workspace_dir(workspace_dir)
        workspace = Workspace(workspace_dir)

        tgt_keys = workspace.tgt_keys.read()
        tgt_context_key = tgt_keys.get("context_key")
        ctx_keys = workspace.ctx_keys.read()
        ctx_primary_key = ctx_keys.get("primary_key")
        ctx_root_key = ctx_keys.get("root_key")

        has_context = workspace.ctx_data_path.exists()

        reset_dir(workspace.tgt_stats_path)
        if has_context:
            reset_dir(workspace.ctx_stats_path)

        tgt_pqt_partitions = workspace.tgt_data.fetch_all()
        if has_context:
            ctx_pqt_partitions = workspace.ctx_data.fetch_all()
            if len(tgt_pqt_partitions) != len(ctx_pqt_partitions):
                raise RuntimeError("partition files for tgt and ctx do not match")
        else:
            ctx_pqt_partitions = []

        _LOG.info(f"analyzing {len(tgt_pqt_partitions)} partitions in parallel")
        tgt_encoding_types = workspace.tgt_encoding_types.read()
        ctx_encoding_types = workspace.ctx_encoding_types.read()

        for i in range(len(tgt_pqt_partitions)):
            _analyze_partition(
                tgt_partition_file=tgt_pqt_partitions[i],
                tgt_stats_path=workspace.tgt_stats_path,
                tgt_encoding_types=tgt_encoding_types,
                tgt_context_key=tgt_context_key,
                ctx_partition_file=ctx_pqt_partitions[i] if has_context else None,
                ctx_stats_path=workspace.ctx_stats_path if has_context else None,
                ctx_encoding_types=ctx_encoding_types,
                ctx_primary_key=ctx_primary_key if has_context else None,
                ctx_root_key=ctx_root_key,
                n_jobs=min(16, max(1, cpu_count() - 1)),
            )
            progress.update(completed=i, total=len(tgt_pqt_partitions) + 1)

        # combine partition statistics
        _LOG.info("combine partition statistics")
        # no need to split epsilon because training will have max_epsilon - value_protection_epsilon as the budget
        value_protection_epsilon = (
            differential_privacy.value_protection_epsilon if value_protection and differential_privacy else None
        )
        if has_context:
            dp_tgt_ratio = float(len(tgt_encoding_types) + 1) / (len(tgt_encoding_types) + len(ctx_encoding_types) + 1)
            dp_ctx_ratio = float(len(ctx_encoding_types)) / (len(tgt_encoding_types) + len(ctx_encoding_types) + 1)
        _analyze_reduce(
            all_stats=workspace.tgt_all_stats,
            out_stats=workspace.tgt_stats,
            keys=tgt_keys,
            mode="tgt",
            value_protection=value_protection,
            # further split epsilon and delta if context is present
            value_protection_epsilon=value_protection_epsilon * dp_tgt_ratio
            if value_protection_epsilon is not None and has_context
            else value_protection_epsilon,
        )
        if has_context:
            _analyze_reduce(
                all_stats=workspace.ctx_all_stats,
                out_stats=workspace.ctx_stats,
                keys=ctx_keys,
                mode="ctx",
                value_protection=value_protection,
                value_protection_epsilon=value_protection_epsilon * dp_ctx_ratio
                if value_protection_epsilon is not None and has_context
                else value_protection_epsilon,
            )

        # clean up partition-wise stats files, as they contain non-protected values
        for file in workspace.tgt_all_stats.fetch_all():
            file.unlink()
        for file in workspace.ctx_all_stats.fetch_all():
            file.unlink()
    _LOG.info(f"ANALYZE finished in {time.time() - t0:.2f}s")


def _analyze_partition(
    tgt_partition_file: Path,
    tgt_stats_path: Path,
    tgt_encoding_types: dict[str, ModelEncodingType],
    tgt_context_key: str | None = None,
    ctx_partition_file: Path | None = None,
    ctx_stats_path: Path | None = None,
    ctx_encoding_types: dict[str, ModelEncodingType] | None = None,
    ctx_primary_key: str | None = None,
    ctx_root_key: str | None = None,
    n_jobs: int = 1,
) -> None:
    """
    Calculates partial statistics about a single partition.

    If context exist, target and context partitions are analyzed jointly,
    thus single run can produce one or two partial statistics files.
    """

    has_context = ctx_partition_file is not None

    # read partitioned parquet file into memory
    tgt_df = pd.read_parquet(tgt_partition_file)
    partition_id = tgt_partition_file.name.split(".")[1]

    # get tgt context keys
    tgt_context_keys = (tgt_df[tgt_context_key] if tgt_context_key else pd.Series(range(tgt_df.shape[0]))).rename(
        "__ckey"
    )

    # get ctx primary keys
    if has_context:
        ctx_primary_keys = pd.read_parquet(ctx_partition_file, columns=[ctx_primary_key])[ctx_primary_key]
    else:
        ctx_primary_keys = tgt_context_keys.drop_duplicates()

    if ctx_root_key:
        ctx_root_keys = pd.read_parquet(ctx_partition_file, columns=[ctx_root_key])[ctx_root_key].rename("__rkey")
    else:
        ctx_root_keys = ctx_primary_keys.rename("__rkey")

    # analyze all target columns
    with parallel_config("loky", n_jobs=n_jobs):
        results = Parallel()(
            delayed(_analyze_col)(
                values=tgt_df[column],
                encoding_type=encoding_type,
                context_keys=tgt_context_keys,
            )
            for column, encoding_type in tgt_encoding_types.items()
        )
        tgt_column_stats = {column: stats for column, stats in zip(tgt_encoding_types.keys(), results)}

    # collect target sequence length stats
    tgt_seq_len = _analyze_seq_len(
        tgt_context_keys=tgt_context_keys,
        ctx_primary_keys=ctx_primary_keys,
    )

    # persist tgt stats
    tgt_stats_file = tgt_stats_path / f"part.{partition_id}.json"
    if "val" in partition_id:
        tgt_stats = {"no_of_training_records": 0, "no_of_validation_records": ctx_primary_keys.size}
    elif "trn" in partition_id:
        tgt_stats = {"no_of_training_records": ctx_primary_keys.size, "no_of_validation_records": 0}
    else:
        raise RuntimeError("partition file name must include 'trn' or 'val'")
    tgt_stats |= {
        "seq_len": tgt_seq_len,
        "columns": tgt_column_stats,
    }
    write_json(tgt_stats, tgt_stats_file)
    _LOG.info(f"analyzed target partition {partition_id} {tgt_df.shape}")

    if has_context:
        assert isinstance(ctx_partition_file, Path) and ctx_partition_file.exists()
        ctx_df = pd.read_parquet(ctx_partition_file)
        ctx_partition_id = ctx_partition_file.name.split(".")[1]
        if partition_id != ctx_partition_id:
            raise RuntimeError("partition files for tgt and ctx do not match")

        # analyze all context columns
        assert isinstance(ctx_encoding_types, dict)
        with parallel_config("loky", n_jobs=n_jobs):
            results = Parallel()(
                delayed(_analyze_col)(
                    values=ctx_df[column],
                    encoding_type=encoding_type,
                    root_keys=ctx_root_keys,
                )
                for column, encoding_type in ctx_encoding_types.items()
            )
            ctx_column_stats = {column: stats for column, stats in zip(ctx_encoding_types.keys(), results)}

        # persist context stats
        assert isinstance(ctx_stats_path, Path) and ctx_stats_path.exists()
        ctx_stats_file = ctx_stats_path / f"part.{partition_id}.json"
        ctx_stats = {
            "columns": ctx_column_stats,
        }
        write_json(ctx_stats, ctx_stats_file)
        _LOG.info(f"analyzed context partition {partition_id} {ctx_df.shape}")


def _analyze_reduce(
    all_stats: PathDesc,
    out_stats: PathDesc,
    keys: dict[str, str],
    mode: Literal["tgt", "ctx"],
    value_protection: bool = True,
    value_protection_epsilon: float | None = None,
) -> None:
    """
    Reduces partial statistics.

    Regardless of the provided argument 'mode', the function sequentially
    iterates over columns and for each it reduces partial column
    statistics. Those reduction procedures are column encoding type
    dependent and are defined in separate submodules.
    The important point is that rare / extreme value protection is applied during this step.

    If target partial statistics are reduced, some additional stats are
    recorded such as training / validation records number, sequence lengths
    summary and others.
    """
    stats_files = all_stats.fetch_all()
    stats_list = [read_json(file) for file in stats_files]
    stats: dict[str, Any] = {"columns": {}}

    # check how many context tables have sequential context
    if mode == "ctx":
        ctxseq_stats = {}
        ctxseq_tables = []
        for column, column_stats in stats_list[0]["columns"].items():
            if "seq_len" in column_stats:
                table_name = column.split(TABLE_COLUMN_INFIX)[0]
                if table_name not in ctxseq_tables:
                    ctxseq_tables.append(table_name)
        n_ctxseq_tables = len(ctxseq_tables)
        _LOG.info(f"{n_ctxseq_tables = }")

    encoding_types = {
        column: column_stats.get("encoding_type") for column, column_stats in stats_list[0]["columns"].items()
    }

    # ctx: distribute the privacy budget across all columns + sequence lengths of n_ctxseq_tables
    # tgt: distribute the privacy budget across all columns + sequence length
    n_dp_splits = len(encoding_types) + n_ctxseq_tables if mode == "ctx" else len(encoding_types) + 1
    _LOG.info(f"{value_protection = }")
    if value_protection_epsilon is not None and n_dp_splits > 0:
        _LOG.info(f"epsilon for analyzing each column and sequence length: {value_protection_epsilon / n_dp_splits}")

    for column in encoding_types:
        encoding_type = encoding_types[column]
        column_stats_list = [item["columns"][column] for item in stats_list]
        column_stats_list = [
            column_stats
            for column_stats in column_stats_list
            if set(column_stats.keys()) - {"encoding_type"}  # skip empty partitions
        ]
        # all partitions are empty
        if not column_stats_list:
            # express that as {"encoding_type": ...} in stats
            stats["columns"][column] = {"encoding_type": encoding_type}
            continue

        value_protection_args = {
            "value_protection": value_protection,
            "value_protection_epsilon": value_protection_epsilon / n_dp_splits
            if value_protection_epsilon is not None
            else None,
        }
        analyze_reduce_column_args = {"stats_list": column_stats_list} | value_protection_args

        match encoding_type:
            case ModelEncodingType.tabular_categorical:
                stats_col = analyze_reduce_categorical(**analyze_reduce_column_args)
            case (
                ModelEncodingType.tabular_numeric_auto
                | ModelEncodingType.tabular_numeric_digit
                | ModelEncodingType.tabular_numeric_discrete
                | ModelEncodingType.tabular_numeric_binned
            ):
                stats_col = analyze_reduce_numeric(**analyze_reduce_column_args, encoding_type=encoding_type)
            case ModelEncodingType.tabular_datetime:
                stats_col = analyze_reduce_datetime(**analyze_reduce_column_args)
            case ModelEncodingType.tabular_datetime_relative:
                stats_col = analyze_reduce_itt(**analyze_reduce_column_args)
            case ModelEncodingType.tabular_character:
                stats_col = analyze_reduce_character(**analyze_reduce_column_args)
            case ModelEncodingType.tabular_lat_long:
                stats_col = analyze_reduce_latlong(**analyze_reduce_column_args)
            case ModelEncodingType.language_text:
                stats_col = analyze_reduce_text(**analyze_reduce_column_args)
            case ModelEncodingType.language_categorical:
                stats_col = analyze_reduce_text(**analyze_reduce_column_args) | analyze_reduce_language_categorical(
                    **analyze_reduce_column_args
                )
            case ModelEncodingType.language_numeric:
                stats_col = analyze_reduce_text(**analyze_reduce_column_args) | analyze_reduce_language_numeric(
                    **analyze_reduce_column_args
                )
            case ModelEncodingType.language_datetime:
                stats_col = analyze_reduce_text(**analyze_reduce_column_args) | analyze_reduce_language_datetime(
                    **analyze_reduce_column_args
                )
            case _:
                raise RuntimeError(f"unknown encoding type {encoding_type}")

        # store encoding type, if it's not present yet
        stats_col = {"encoding_type": encoding_type} | stats_col
        # store flag indicating whether value protection was applied
        if encoding_type in _VALUE_PROTECTION_ENCODING_TYPES:
            stats_col = {"value_protection": value_protection} | stats_col

        is_ctxseq_column = "seq_len" in column_stats_list[0]
        if is_ctxseq_column:
            table_name = column.split(TABLE_COLUMN_INFIX)[0]
            # only get the lengths from the first column of a ctxseq table and reuse the stats later
            if table_name not in ctxseq_stats:
                ctxseq_stats[table_name] = _analyze_reduce_seq_len(
                    stats_list=[column_stats_list[0]["seq_len"]], **value_protection_args
                )
                _LOG.info(f"analyzed sequence length for context table `{table_name}`")
            stats_col["seq_len"] = ctxseq_stats[table_name]

        is_language_column = encoding_type in (
            ModelEncodingType.language_text,
            ModelEncodingType.language_categorical,
            ModelEncodingType.language_numeric,
            ModelEncodingType.language_datetime,
        )

        if not is_language_column:
            # build mapping of original column name to ARGN table and column identifiers
            def get_table(qualified_column_name: str) -> str:
                # column names are assumed to be <table>::<column>
                return qualified_column_name.split(TABLE_COLUMN_INFIX)[0]

            def get_unique_tables(qualified_column_names: Iterable[str]) -> list[str]:
                duplicated_tables = [get_table(c) for c in qualified_column_names]
                return list(dict.fromkeys(duplicated_tables))

            unique_tables = get_unique_tables(encoding_types.keys())
            argn_identifiers: dict[str, tuple[str, str]] = {
                c: (f"t{unique_tables.index(get_table(qualified_column_name=c))}", f"c{idx}")
                for idx, c in enumerate(encoding_types.keys())
            }

            def get_argn_processor(mode, is_flat) -> str:
                if mode == "tgt":
                    return TGT
                else:  # mode == "ctx"
                    return CTXFLT if is_flat else CTXSEQ

            stats_col[ARGN_PROCESSOR] = get_argn_processor(mode, is_flat="seq_len" not in column_stats_list[0])
            (
                stats_col[ARGN_TABLE],
                stats_col[ARGN_COLUMN],
            ) = argn_identifiers[column]

        _LOG.info(
            f"analyzed column `{column}`: {stats_col['encoding_type']} "
            + (
                f"nchar_max={stats_col['nchar_max']} nchar_avg={stats_col['nchar_avg']}"
                if is_language_column
                else f"{stats_col['cardinalities']}"
            )
        )
        stats["columns"][column] = stats_col

    if mode == "tgt":
        # gather number of records and split into trn/val
        trn_cnt = sum(item["no_of_training_records"] for item in stats_list)
        val_cnt = sum(item["no_of_validation_records"] for item in stats_list)
        stats["no_of_training_records"] = trn_cnt
        stats["no_of_validation_records"] = val_cnt
        _LOG.info(f"analyzed {trn_cnt + val_cnt:,} records: {trn_cnt:,} training / {val_cnt:,} validation")
        # gather sequence length statistics
        stats["seq_len"] = _analyze_reduce_seq_len(
            stats_list=[item["seq_len"] for item in stats_list],
            value_protection=value_protection,
            value_protection_epsilon=value_protection_epsilon / n_dp_splits
            if value_protection_epsilon is not None
            else None,
        )
        seq_len_min = stats["seq_len"]["min"]
        seq_len_max = stats["seq_len"]["max"]
        # check whether data is sequential or not
        stats["is_sequential"] = seq_len_min != 1 or seq_len_max != 1
        _LOG.info(f"is_sequential: {stats['is_sequential']}")

    stats["keys"] = keys
    # TODO: store the actual epsilon spent, so that we can use the rest on training
    stats["value_protection_epsilon_spent"] = value_protection_epsilon

    # persist statistics
    _LOG.info(f"write statistics to `{out_stats.path}`")
    out_stats.write(stats)


def _analyze_col(
    values: pd.Series,
    encoding_type: ModelEncodingType,
    root_keys: pd.Series | None = None,
    context_keys: pd.Series | None = None,
) -> dict:
    set_random_state(worker=True)

    stats: dict = {"encoding_type": encoding_type}

    if values.empty:
        # empty partition columns are expressed as {"encoding_type": ...} in partial stats
        return stats

    if root_keys is None:
        root_keys = pd.Series([str(i) for i in range(len(values))], name="root_keys")

    if is_sequential(values):
        # analyze sequential column
        non_empties = values.apply(lambda v: len(v) if is_a_list(v) else 1) > 0
        # generate serial context_keys, if context_keys are not provided
        context_keys = context_keys if context_keys is not None else pd.Series(range(len(values))).rename("__ckey")
        # explode non-empty values and keys in sync, reset index afterwards
        df = pd.concat(
            [values[non_empties], root_keys[non_empties], context_keys[non_empties]],
            axis=1,
        )
        df = df.explode(values.name).reset_index(drop=True)
        # analyze sequence lengths
        cnt_lengths = _analyze_seq_len(df[root_keys.name], root_keys)
        stats |= _analyze_flat_col(encoding_type, df[values.name], df[root_keys.name], df[context_keys.name]) | {
            "seq_len": cnt_lengths
        }
    else:
        # analyze flat column
        stats |= _analyze_flat_col(encoding_type, values, root_keys, context_keys)

    return stats


def _analyze_flat_col(
    encoding_type: ModelEncodingType,
    values: pd.Series,
    root_keys: pd.Series,
    context_keys: pd.Series | None,
) -> dict:
    if encoding_type == ModelEncodingType.tabular_categorical:
        stats = analyze_categorical(values, root_keys, context_keys)
    elif encoding_type in [
        ModelEncodingType.tabular_numeric_auto,
        ModelEncodingType.tabular_numeric_digit,
        ModelEncodingType.tabular_numeric_discrete,
        ModelEncodingType.tabular_numeric_binned,
    ]:
        stats = analyze_numeric(values, root_keys, context_keys, encoding_type)
    elif encoding_type == ModelEncodingType.tabular_datetime:
        stats = analyze_datetime(values, root_keys, context_keys)
    elif encoding_type == ModelEncodingType.tabular_datetime_relative:
        stats = analyze_itt(values, root_keys, context_keys)
    elif encoding_type == ModelEncodingType.tabular_character:
        stats = analyze_character(values, root_keys, context_keys)
    elif encoding_type == ModelEncodingType.tabular_lat_long:
        stats = analyze_latlong(values, root_keys, context_keys)
    elif encoding_type == ModelEncodingType.language_text:
        stats = analyze_text(values, root_keys, context_keys)
    elif encoding_type == ModelEncodingType.language_categorical:
        stats = analyze_text(values, root_keys, context_keys) | analyze_language_categorical(
            values, root_keys, context_keys
        )
    elif encoding_type == ModelEncodingType.language_numeric:
        stats = analyze_text(values, root_keys, context_keys) | analyze_language_numeric(
            values, root_keys, context_keys
        )
    elif encoding_type == ModelEncodingType.language_datetime:
        stats = analyze_text(values, root_keys, context_keys) | analyze_language_datetime(
            values, root_keys, context_keys
        )
    else:
        raise RuntimeError(f"unknown encoding type: `{encoding_type}` for `{values.name}`")
    return stats


# SEQUENCE LENGTH


def _analyze_seq_len(
    tgt_context_keys: pd.Series,
    ctx_primary_keys: pd.Series,
) -> dict[str, Any]:
    # add extra mask record for each unique ctx_primary_key
    ctx_primary_keys = ctx_primary_keys.drop_duplicates()
    df_keys = pd.concat([tgt_context_keys, ctx_primary_keys]).to_frame()
    extra_rows = 1
    # count records per key
    values = df_keys.groupby(df_keys.columns[0]).size() - extra_rows
    # count records per sequence length
    cnt_lengths = values.value_counts().to_dict()
    stats = {"cnt_lengths": cnt_lengths}
    return stats


def _analyze_reduce_seq_len(
    stats_list: list[dict],
    value_protection: bool = True,
    value_protection_epsilon: float | None = None,
) -> dict:
    # gather sequence length counts
    cnt_lengths: dict[str, int] = {}
    for item in stats_list:
        for value, count in item["cnt_lengths"].items():
            cnt_lengths[value] = cnt_lengths.get(value, 0) + count
    # explode counts to np.array to gather statistics
    lengths = (
        np.sort(np.concatenate([np.repeat(int(k), v) for k, v in cnt_lengths.items()], axis=0))
        if len(cnt_lengths) > 0
        else np.empty(0)
    )
    min_length = max_length = median = None
    if value_protection:
        if len(lengths) < ANALYZE_REDUCE_MIN_MAX_N:
            # less or equal to 10 subjects; we need to protect all
            lengths = np.repeat(1, 10)
        else:
            # don't use DP quantiles if all lengths are 1 (non-sequential data)
            if value_protection_epsilon is not None and np.any(lengths != 1):
                quantiles = [0.01, 0.5, 0.99]
                min_length, median, max_length = dp_quantiles(lengths, quantiles, value_protection_epsilon)
                if median is None:  # protect all if DP quantiles are not available
                    lengths = np.repeat(1, 10)
                else:
                    min_length = int(min_length)
                    max_length = int(max_length)
                    median = int(median)
            else:
                lengths = lengths[
                    get_stochastic_rare_threshold(min_threshold=5) : -get_stochastic_rare_threshold(min_threshold=5)
                ]
    if median is None:
        # non-DP case
        min_length = int(np.min(lengths))
        max_length = int(np.max(lengths))
        median = int(np.median(lengths))
    stats = {
        # calculate min/max for GENERATE
        "min": min_length,
        "max": max_length,
        # calculate median for LSTM heuristic
        "median": median,
        "value_protection": value_protection,
    }
    return stats
