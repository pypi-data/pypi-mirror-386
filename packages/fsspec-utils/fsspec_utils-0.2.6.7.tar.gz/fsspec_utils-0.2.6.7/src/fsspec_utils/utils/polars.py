import numpy as np
import polars as pl
import polars.selectors as cs
import re

from .datetime import get_timedelta_str, get_timestamp_column

# Pre-compiled regex patterns (identical to original)
INTEGER_REGEX = r"^[-+]?\d+$"
FLOAT_REGEX = r"^[-+]?(?:\d*[.,])?\d+(?:[eE][-+]?\d+)?$"
BOOLEAN_REGEX = r"^(true|false|1|0|yes|ja|no|nein|t|f|y|j|n|ok|nok)$"
BOOLEAN_TRUE_REGEX = r"^(true|1|yes|ja|t|y|j|ok)$"
# Make 8-digit pattern more restrictive to exclude obvious non-dates
DATETIME_REGEX = (
    r"^("
    r"\d{4}-\d{2}-\d{2}"  # ISO: 2023-12-31
    r"|"
    r"\d{2}/\d{2}/\d{4}"  # US: 12/31/2023
    r"|"
    r"\d{2}\.\d{2}\.\d{4}"  # German: 31.12.2023
    r"|"
    # Only match 8-digit numbers that look like reasonable dates
    r"(?:19|20)\d{6}"  # Years 1900-2099: 20231231
    r")"
    r"([ T]\d{2}:\d{2}(:\d{2}(\.\d{1,6})?)?)?"  # Optional time: 23:59[:59[.123456]]
    r"([+-]\d{2}:?\d{2}|Z|UTC)?"  # Optional timezone: +01:00, -0500, Z, UTC
    r"$"
)

# Float32 range limits
F32_MIN = float(np.finfo(np.float32).min)
F32_MAX = float(np.finfo(np.float32).max)


def _clean_string_expr(col_name: str) -> pl.Expr:
    """Create expression to clean string values."""
    return (
        pl.col(col_name)
        .str.strip_chars()
        .replace(
            {
                "-": None,
                "": None,
                "None": None,
                "none": None,
                "NONE": None,
                "NaN": None,
                "Nan": None,
                "nan": None,
                "NAN": None,
                "N/A": None,
                "n/a": None,
                "null": None,
                "Null": None,
                "NULL": None,
            }
        )
    )


def _can_downcast_to_float32(series: pl.Series) -> bool:
    """Check if float values are within Float32 range."""
    finite_values = series.filter(series.is_finite())
    if finite_values.is_empty():
        return True

    min_val, max_val = finite_values.min(), finite_values.max()
    return F32_MIN <= min_val <= max_val <= F32_MAX


def _optimize_numeric_column(
    series: pl.Series,
    shrink: bool,
    allow_unsigned: bool = True,
    allow_null: bool = True,
) -> pl.Expr:
    """Optimize numeric column types, optionally converting to unsigned if all values >= 0."""
    col_name = series.name
    expr = pl.col(col_name)
    dtype = series.dtype
    if series.is_null().all():
        # If all values are null, cast to Null type if allow_null is True
        if allow_null:
            return expr.cast(pl.Null())

    if not allow_unsigned:
        # If unsigned types are not allowed, ensure we use signed integer types
        if dtype.is_integer() and not dtype.is_signed_integer():
            return expr.cast(pl.Int64)

    if (
        allow_unsigned
        and dtype.is_integer()
        and (series.min() is not None)
        and series.min() >= 0
    ):
        # Convert to unsigned integer type, shrink if requested
        if shrink:
            return expr.cast(pl.UInt64).shrink_dtype()
        else:
            return expr.cast(pl.UInt64)

    if not shrink:
        return expr

    if dtype == pl.Float64 and not _can_downcast_to_float32(series):
        return expr

    return expr.shrink_dtype()


def _detect_timezone_from_sample(
    series: pl.Series, sample_size: int = 100
) -> str | None:
    """Efficiently detect the most common timezone from a sample of datetime strings.

    Args:
        series: Series containing datetime strings
        sample_size: Maximum number of values to sample (for performance)

    Returns:
        The most common timezone string, or None if most values are timezone-naive
    """
    # Sample the data for performance
    sample_size = min(sample_size, len(series))
    if sample_size == 0:
        return None

    # Take a sample from the series
    if len(series) <= sample_size:
        sample = series
    else:
        # Take every nth item to get a representative sample
        step = len(series) // sample_size
        sample = series[::step][:sample_size]

    # Drop null values
    sample = sample.drop_nulls()
    if sample.is_empty():
        return None

    # Extract timezone information
    timezones = []
    utc_count = 0
    naive_count = 0

    for val in sample:
        val_str = str(val)

        # Check for timezone patterns
        if val_str.endswith("Z"):
            timezones.append("UTC")
            utc_count += 1
        elif "+00:00" in val_str:
            timezones.append("UTC")
            utc_count += 1
        elif "+0000" in val_str:
            timezones.append("UTC")
            utc_count += 1
        elif re.search(r"[+-]\d{2}:?\d{2}$", val_str):
            # Extract timezone offset
            match = re.search(r"([+-]\d{2}:?\d{2})$", val_str)
            if match:
                tz = match.group(1)
                if tz == "+00:00" or tz == "+0000":
                    timezones.append("UTC")
                    utc_count += 1
                else:
                    timezones.append(tz)
        else:
            naive_count += 1

    # Determine the most common timezone
    if not timezones:
        # All values are timezone-naive
        return None

    # Count timezone occurrences
    from collections import Counter

    tz_counts = Counter(timezones)

    # If most values are timezone-naive, return None
    if naive_count > len(sample) / 2:
        return None

    # Get the most common timezone
    most_common_tz, most_common_count = tz_counts.most_common(1)[0]

    # If there's a tie, prefer UTC
    if most_common_count == utc_count and utc_count > 0:
        return "UTC"

    # If the most common timezone appears in more than 30% of non-naive values, use it
    if most_common_count >= len(timezones) * 0.3:
        return most_common_tz

    # Default to UTC if we have any timezone information
    return "UTC"


def _optimize_string_column(
    series: pl.Series,
    shrink_numerics: bool,
    time_zone: str | None = None,
    allow_null: bool = True,
    allow_unsigned: bool = True,
    force_timezone: str | None = None,
) -> pl.Expr:
    """Convert string column to appropriate type based on content analysis.

    Änderung:
    Platzhalter-/Null-ähnliche Werte ("", "-", "None", "NaN", "null", usw.)
    blockieren nicht mehr die Erkennung (Int/Float/Bool/Datetime). Für die
    Musterprüfung werden sie herausgefiltert. Bei erfolgreichem Cast werden sie
    durch das Cleaning (`_clean_string_expr`) zu Null. Fallback belässt die
    Originalwerte (kein erzwungenes Nullen, wie angefragt).
    """
    col_name = series.name
    cleaned_expr = _clean_string_expr(col_name)

    # Check if all values are actually null (including null-like strings)
    cleaned_series = series.to_frame().select(_clean_string_expr(col_name)).to_series()
    if cleaned_series.is_null().all():
        if allow_null:
            # Return a column of nulls with Null type
            return pl.lit(None, dtype=pl.Null()).alias(col_name)
        return pl.col(col_name)

    stripped = series.drop_nulls().str.strip_chars()

    # Liste der Platzhalter-Werte muss mit _clean_string_expr konsistent bleiben
    null_like_values = [
        "-",
        "",
        "None",
        "none",
        "NONE",
        "NaN",
        "Nan",
        "nan",
        "NAN",
        "N/A",
        "n/a",
        "null",
        "Null",
        "NULL",
    ]

    detector_values = stripped.filter(~stripped.is_in(null_like_values))

    # Wenn nach Herausfiltern nichts mehr übrig bleibt → Spalte nur Platzhalter
    if detector_values.is_empty():
        if allow_null:
            return pl.col(col_name).cast(pl.Null())
        return pl.col(col_name)

    lower_detector = detector_values.str.to_lowercase()

    # Integer-Erkennung (vor Datetime, um 8-stellige Zahlen zu erfassen)
    if detector_values.str.contains(INTEGER_REGEX).all():
        # Cast to Int64 first to ensure valid conversion
        int_expr = cleaned_expr.cast(pl.Int64)

        # Check if we should use unsigned integers
        if allow_unsigned:
            # Check if all original string values are non-negative
            # (excluding null-like values that were cleaned)
            if detector_values.min() is not None and detector_values.min() >= "0":
                # Convert to UInt64 first, then shrink if needed
                uint_expr = int_expr.cast(pl.UInt64)
                if shrink_numerics:
                    return uint_expr.shrink_dtype().alias(col_name)
                return uint_expr.alias(col_name)

        # Fall back to signed integers
        if shrink_numerics:
            return int_expr.shrink_dtype().alias(col_name)
        return int_expr.alias(col_name)

    # Float-Erkennung
    if detector_values.str.contains(FLOAT_REGEX).all():
        float_expr = (
            cleaned_expr.str.replace_all(",", ".").cast(pl.Float64).alias(col_name)
        )
        if shrink_numerics:
            temp_floats = detector_values.str.replace_all(",", ".").cast(
                pl.Float64, strict=False
            )
            if _can_downcast_to_float32(temp_floats):
                return float_expr.shrink_dtype().alias(col_name)
        return float_expr

    # Boolean-Erkennung
    if lower_detector.str.contains(BOOLEAN_REGEX).all():
        return (
            cleaned_expr.str.to_lowercase()
            .str.contains(BOOLEAN_TRUE_REGEX)
            .alias(col_name)
        )

    # Datetime-Erkennung mit Polars' eingebauter Format-Erkennung
    if detector_values.str.contains(DATETIME_REGEX).all():
        try:
            # Prüfe ob gemischte Zeitzonen vorhanden sind
            has_tz = series.str.contains(r"(Z|UTC|[+-]\d{2}:\d{2}|[+-]\d{4})$").any()

            if has_tz:
                # Bei gemischten Zeitzonen, verwende eager parsing auf Series-Ebene
                import re

                def normalize_datetime_string(s):
                    """Normalisiere verschiedene Zeitzone-Formate für das Parsen."""
                    if not s:
                        return s

                    s = str(s).strip()
                    # Entferne Zeitzonen-Informationen, da Polars diese nicht gemischt verarbeiten kann
                    s = re.sub(r"Z$", "", s)
                    s = re.sub(r"UTC$", "", s)
                    s = re.sub(r"([+-]\d{2}:\d{2})$", "", s)
                    s = re.sub(r"([+-]\d{4})$", "", s)
                    return s

                # Normalisiere die Zeitzone-Formate
                normalized_series = series.map_elements(
                    normalize_datetime_string, return_dtype=pl.String
                )

                # Parse mit force_timezone falls angegeben
                if force_timezone is not None:
                    dt_series = normalized_series.str.to_datetime(
                        time_zone=force_timezone, time_unit="us"
                    )
                else:
                    # Erkenne die häufigste Zeitzone
                    detected_tz = _detect_timezone_from_sample(series)
                    if detected_tz is not None:
                        dt_series = normalized_series.str.to_datetime(
                            time_zone=detected_tz, time_unit="us"
                        )
                    else:
                        dt_series = normalized_series.str.to_datetime(time_unit="us")

                # Konvertiere zurück zu Expr
                return pl.lit(dt_series).alias(col_name)
            else:
                # Keine gemischten Zeitzonen - normales expression-basiertes Parsen
                dt_expr = cleaned_expr.str.to_datetime(strict=False, time_unit="us")

                # Wende force_timezone an falls angegeben
                if force_timezone is not None:
                    dt_expr = dt_expr.dt.replace_time_zone(force_timezone)

                return dt_expr.alias(col_name)
        except Exception as e:  # pragma: no cover - defensive
            # Log error for debugging
            import logging

            logging.debug(f"Datetime parsing failed for column {col_name}: {e}")
            pass

    # Kein Cast → Original behalten
    return pl.col(col_name)


def _get_column_expr(
    df: pl.DataFrame,
    col_name: str,
    shrink_numerics: bool = True,
    allow_unsigned: bool = True,
    allow_null: bool = True,
    time_zone: str | None = None,
    force_timezone: str | None = None,
) -> pl.Expr:
    """Generate optimization expression for a single column."""
    series = df[col_name]

    # Handle all-null columns
    if series.is_null().all():
        if allow_null:
            # If all values are null, cast to Null type if allow_null is True
            return pl.col(col_name).cast(pl.Null())

    # Process based on current type
    if series.dtype.is_numeric():
        return _optimize_numeric_column(
            series, shrink_numerics, allow_unsigned, allow_null
        )
    elif series.dtype == pl.Utf8:
        # korrigierter Aufruf: (series, shrink_numerics, time_zone, allow_null, allow_unsigned)
        return _optimize_string_column(
            series,
            shrink_numerics,
            time_zone,
            allow_null,
            allow_unsigned,
            force_timezone,
        )

    # Keep original for other types
    return pl.col(col_name)


def opt_dtype(
    df: pl.DataFrame,
    include: str | list[str] | None = None,
    exclude: str | list[str] | None = None,
    time_zone: str | None = None,
    shrink_numerics: bool = True,
    allow_unsigned: bool = True,
    allow_null: bool = True,
    strict: bool = False,
    *,
    force_timezone: str | None = None,
) -> pl.DataFrame:
    """
    Optimize data types of a Polars DataFrame for performance and memory efficiency.

    This function analyzes each column and converts it to the most appropriate
    data type based on content, handling string-to-type conversions and
    numeric type downcasting.

    Args:
        df: The Polars DataFrame to optimize.
        include: Column(s) to include in optimization (default: all columns).
        exclude: Column(s) to exclude from optimization.
        time_zone: Optional time zone hint during datetime parsing.
        shrink_numerics: Whether to downcast numeric types when possible.
        allow_unsigned: Whether to allow unsigned integer types.
        allow_null: Whether to allow columns with all null values to be cast to Null type.
        strict: If True, will raise an error if any column cannot be optimized.
        force_timezone: If set, ensure all parsed datetime columns end up with this timezone.

    Returns:
        DataFrame with optimized data types.
    """
    # Normalize include/exclude parameters
    if isinstance(include, str):
        include = [include]
    if isinstance(exclude, str):
        exclude = [exclude]

    # Determine columns to process
    cols_to_process = df.columns
    if include:
        cols_to_process = [col for col in include if col in df.columns]
    if exclude:
        cols_to_process = [col for col in cols_to_process if col not in exclude]

    # Generate optimization expressions for all columns
    expressions = []
    for col_name in cols_to_process:
        try:
            expressions.append(
                _get_column_expr(
                    df,
                    col_name,
                    shrink_numerics,
                    allow_unsigned,
                    allow_null,
                    time_zone,
                    force_timezone,
                )
            )
        except Exception as e:
            if strict:
                raise e
            # If strict mode is off, just keep the original column
            continue

    # Apply all transformations at once if any exist
    return df if not expressions else df.with_columns(expressions)


def unnest_all(df: pl.DataFrame, seperator="_", fields: list[str] | None = None):
    def _unnest_all(struct_columns):
        if fields is not None:
            return (
                df.with_columns(
                    [
                        pl.col(col).struct.rename_fields(
                            [
                                f"{col}{seperator}{field_name}"
                                for field_name in df[col].struct.fields
                            ]
                        )
                        for col in struct_columns
                    ]
                )
                .unnest(struct_columns)
                .select(
                    list(set(df.columns) - set(struct_columns))
                    + sorted(
                        [
                            f"{col}{seperator}{field_name}"
                            for field_name in fields
                            for col in struct_columns
                        ]
                    )
                )
            )

        return df.with_columns(
            [
                pl.col(col).struct.rename_fields(
                    [
                        f"{col}{seperator}{field_name}"
                        for field_name in df[col].struct.fields
                    ]
                )
                for col in struct_columns
            ]
        ).unnest(struct_columns)

    struct_columns = [col for col in df.columns if df[col].dtype == pl.Struct]  # noqa: F821
    while len(struct_columns):
        df = _unnest_all(struct_columns=struct_columns)
        struct_columns = [col for col in df.columns if df[col].dtype == pl.Struct]
    return df


def explode_all(df: pl.DataFrame | pl.LazyFrame):
    list_columns = [col for col in df.columns if df[col].dtype == pl.List]
    for col in list_columns:
        df = df.explode(col)
    return df


def with_strftime_columns(
    df: pl.DataFrame | pl.LazyFrame,
    strftime: str | list[str],
    timestamp_column: str = "auto",
    column_names: str | list[str] | None = None,
):
    if timestamp_column is None or timestamp_column == "auto":
        timestamp_column = get_timestamp_column(df)
        if len(timestamp_column):
            timestamp_column = timestamp_column[0]

    if timestamp_column is None:
        raise ValueError("timestamp_column is not specified nor found in the dataframe")

    if isinstance(strftime, str):
        strftime = [strftime]
    if isinstance(column_names, str):
        column_names = [column_names]

    if column_names is None:
        column_names = [
            f"_strftime_{strftime_.replace('%', '').replace('-', '_')}_"
            for strftime_ in strftime
        ]
    # print("timestamp_column, with_strftime_columns", timestamp_column)
    return opt_dtype(
        df.with_columns(
            [
                pl.col(timestamp_column)
                .dt.strftime(strftime_)
                .fill_null(0)
                .alias(column_name)
                for strftime_, column_name in zip(strftime, column_names)
            ]
        ),
        include=column_names,
        strict=False,
    )


def with_truncated_columns(
    df: pl.DataFrame | pl.LazyFrame,
    truncate_by: str | list[str],
    timestamp_column: str = "auto",
    column_names: str | list[str] | None = None,
):
    if timestamp_column is None or timestamp_column == "auto":
        timestamp_column = get_timestamp_column(df)
        if len(timestamp_column):
            timestamp_column = timestamp_column[0]

        if timestamp_column is None:
            raise ValueError(
                "timestamp_column is not specified nor found in the dataframe"
            )
    if isinstance(truncate_by, str):
        truncate_by = [truncate_by]

    if isinstance(column_names, str):
        column_names = [column_names]

    if column_names is None:
        column_names = [
            f"_truncated_{truncate_.replace(' ', '_')}_" for truncate_ in truncate_by
        ]

    truncate_by = [
        get_timedelta_str(truncate_, to="polars") for truncate_ in truncate_by
    ]
    return df.with_columns(
        [
            pl.col(timestamp_column).dt.truncate(truncate_).alias(column_name)
            for truncate_, column_name in zip(truncate_by, column_names)
        ]
    )


def with_datepart_columns(
    df: pl.DataFrame | pl.LazyFrame,
    timestamp_column: str = "auto",
    year: bool = False,
    month: bool = False,
    week: bool = False,
    yearday: bool = False,
    monthday: bool = False,
    day: bool = False,
    weekday: bool = False,
    hour: bool = False,
    minute: bool = False,
    strftime: str | None = None,
):
    if strftime:
        if isinstance(strftime, str):
            strftime = [strftime]
        column_names = [
            f"_strftime_{strftime_.replace('%', '').replace('-', '_')}_"
            for strftime_ in strftime
        ]
    else:
        strftime = []
        column_names = []

    if year:
        strftime.append("%Y")
        column_names.append("year")
    if month:
        strftime.append("%m")
        column_names.append("month")
    if week:
        strftime.append("%W")
        column_names.append("week")
    if yearday:
        strftime.append("%j")
        column_names.append("year_day")
    if monthday:
        strftime.append("%d")
        column_names.append("day")
    if day:
        strftime.append("%d")
        column_names.append("day")
    if weekday:
        strftime.append("%a")
        column_names.append("week_day")
    if hour:
        strftime.append("%H")
        column_names.append("hour")
    if minute:
        strftime.append("%M")
        column_names.append("minute")

    column_names = [col for col in column_names if col not in df.columns]
    # print("timestamp_column, with_datepart_columns", timestamp_column)
    return with_strftime_columns(
        df=df,
        timestamp_column=timestamp_column,
        strftime=strftime,
        column_names=column_names,
    )


def with_row_count(
    df: pl.DataFrame | pl.LazyFrame,
    over: str | list[str] | None = None,
):
    if over:
        if len(over) == 0:
            over = None

    if isinstance(over, str):
        over = [over]

    if over:
        return df.with_columns(pl.lit(1).alias("row_nr")).with_columns(
            pl.col("row_nr").cum_sum().over(over)
        )
    else:
        return df.with_columns(pl.lit(1).alias("row_nr")).with_columns(
            pl.col("row_nr").cum_sum()
        )


# def delta(
#     df1: pl.DataFrame | pl.LazyFrame,
#     df2: pl.DataFrame | pl.LazyFrame,
#     subset: str | list[str] | None = None,
#     eager: bool = False,
# ) -> pl.LazyFrame:
#     columns = sorted(set(df1.columns) & set(df2.columns))

#     if subset is None:
#         subset = columns
#     if isinstance(subset, str):
#         subset = [subset]

#     subset = sorted(set(columns) & set(subset))

#     if isinstance(df1, pl.LazyFrame) and isinstance(df2, pl.DataFrame):
#         df2 = df2.lazy()

#     elif isinstance(df1, pl.DataFrame) and isinstance(df2, pl.LazyFrame):
#         df1 = df1.lazy()

#     df = (
#         pl.concat(
#             [
#                 df1.select(columns)
#                 .with_columns(pl.lit(1).alias("df"))
#                 .with_row_count(),
#                 df2.select(columns)
#                 .with_columns(pl.lit(2).alias("df"))
#                 .with_row_count(),
#             ],
#             how="vertical_relaxed",
#         )
#         .filter((pl.count().over(subset) == 1) & (pl.col("df") == 1))
#         .select(pl.exclude(["df", "row_nr"]))
#     )

#     if eager and isinstance(df, pl.LazyFrame):
#         return df.collect()
#     return df


def drop_null_columns(df: pl.DataFrame | pl.LazyFrame) -> pl.DataFrame | pl.LazyFrame:
    """Remove columns with all null values from the DataFrame."""
    return df.select([col for col in df.columns if df[col].null_count() < df.height])


def _unique_schemas(schemas: list[pl.Schema]) -> list[pl.Schema]:
    unique = []
    for schema in schemas:
        if schema not in unique:
            unique.append(schema)
    return unique


def unify_schemas(dfs: list[pl.DataFrame | pl.LazyFrame]) -> pl.Schema:
    schemas = [df.schema for df in dfs]
    unique_schemas = _unique_schemas(schemas)
    if len(unique_schemas) == 1:
        return unique_schemas[0]
    else:
        return pl.concat(
            [pl.LazyFrame(schema=schema) for schema in unique_schemas],
            how="diagonal_relaxed",
        ).collect_schema()


def cast_relaxed(
    df: pl.DataFrame | pl.LazyFrame, schema: pl.Schema
) -> pl.DataFrame | pl.LazyFrame:
    if isinstance(df, pl.LazyFrame):
        columns = df.collect_schema().names()
    else:
        columns = df.schema.names()
    new_columns = [col for col in schema.names() if col not in columns]
    if len(new_columns):
        return df.with_columns(
            [pl.lit(None).alias(new_col) for new_col in new_columns]
        ).cast(schema)
    return df.cast(schema)


def delta(
    df1: pl.DataFrame | pl.LazyFrame,
    df2: pl.DataFrame | pl.LazyFrame,
    subset: list[str] | None = None,
    eager: bool = False,
) -> pl.DataFrame:
    s1 = df1.select(~cs.by_dtype(pl.Null())).collect_schema()
    s2 = df2.select(~cs.by_dtype(pl.Null())).collect_schema()

    columns = sorted(set(s1.names()) & set(s2.names()))

    if subset is None:
        subset = df1.columns
    if isinstance(subset, str):
        subset = [subset]

    subset = sorted(set(columns) & set(subset))

    if isinstance(df1, pl.LazyFrame) and isinstance(df2, pl.DataFrame):
        df2 = df2.lazy()

    elif isinstance(df1, pl.DataFrame) and isinstance(df2, pl.LazyFrame):
        df1 = df1.lazy()

    # cast to equal schema
    unified_schema = unify_schemas([df1.select(subset), df2.select(subset)])

    df1 = df1.cast_relaxed(unified_schema)
    df2 = df2.cast_relaxed(unified_schema)

    df = df1.join(df2, on=subset, how="anti", join_nulls=True)

    if eager and isinstance(df, pl.LazyFrame):
        return df.collect()

    return df


def partition_by(
    df: pl.DataFrame | pl.LazyFrame,
    timestamp_column: str | None = None,
    columns: str | list[str] | None = None,
    strftime: str | list[str] | None = None,
    timedelta: str | list[str] | None = None,
    num_rows: int | None = None,
) -> list[tuple[dict, pl.DataFrame | pl.LazyFrame]]:
    if columns is not None:
        if isinstance(columns, str):
            columns = [columns]
        columns_ = columns.copy()
    else:
        columns_ = []

    drop_columns = columns_.copy()

    if strftime is not None:
        if isinstance(strftime, str):
            strftime = [strftime]

        df = df.with_strftime_columns(
            timestamp_column=timestamp_column, strftime=strftime
        )
        strftime_columns = [
            f"_strftime_{strftime_.replace('%', '')}_" for strftime_ in strftime
        ]
        columns_ += strftime_columns
        drop_columns += strftime_columns

    if timedelta is not None:
        if isinstance(timedelta, str):
            timedelta = [timedelta]

        df = df.with_duration_columns(
            timestamp_column=timestamp_column, timedelta=timedelta
        )
        timedelta_columns = [f"_timedelta_{timedelta_}_" for timedelta_ in timedelta]
        columns_ += timedelta_columns
        drop_columns += timedelta_columns

    if columns_:
        # datetime_columns = {
        #     col: col in [col.lower() for col in columns_]
        #     for col in [
        #         "year",
        #         "month",
        #         "week",
        #         "yearday",
        #         "monthday",
        #         "weekday",
        #         "strftime",
        #     ]
        #     if col not in [table_col.lower() for table_col in df.columns]
        # }
        datetime_columns = [
            col.lower()
            for col in columns_
            if col
            in [
                "year",
                "month",
                "week",
                "yearday",
                "monthday",
                "weekday",
                "day",
                "hour",
                "minute",
                "strftime",
            ]
            and col not in df.columns
        ]

        datetime_columns = {
            col: col in datetime_columns
            for col in [
                "year",
                "month",
                "week",
                "yearday",
                "monthday",
                "weekday",
                "day",
                "hour",
                "minute",
                "strftime",
            ]
        }
        if any(datetime_columns.values()):
            df = df.with_datepart_columns(
                timestamp_column=timestamp_column, **datetime_columns
            )

        if isinstance(df, pl.LazyFrame):
            df = df.collect()
        columns_ = [col for col in columns_ if col in df.columns]

    if num_rows is not None:
        df = df.with_row_count_ext(over=columns_).with_columns(
            (pl.col("row_nr") - 1) // num_rows
        )
        columns_ += ["row_nr"]
        drop_columns += ["row_nr"]

    if columns_:
        partitions = [
            (p.select(columns_).unique().to_dicts()[0], p.drop(drop_columns))
            for p in df.partition_by(
                by=columns_,
                as_dict=False,
                maintain_order=True,
            )
        ]

        return partitions

    return [({}, df)]


pl.DataFrame.unnest_all = unnest_all
pl.DataFrame.explode_all = explode_all
pl.DataFrame.opt_dtype = opt_dtype
pl.DataFrame.with_row_count_ext = with_row_count
pl.DataFrame.with_datepart_columns = with_datepart_columns
pl.DataFrame.with_duration_columns = with_truncated_columns
pl.DataFrame.with_strftime_columns = with_strftime_columns
pl.DataFrame.cast_relaxed = cast_relaxed
pl.DataFrame.delta = delta
pl.DataFrame.partition_by_ext = partition_by
pl.DataFrame.drop_null_columns = drop_null_columns

pl.LazyFrame.unnest_all = unnest_all
pl.LazyFrame.explode_all = explode_all
pl.LazyFrame.opt_dtype = opt_dtype
pl.LazyFrame.with_row_count_ext = with_row_count
pl.LazyFrame.with_datepart_columns = with_datepart_columns
pl.LazyFrame.with_duration_columns = with_truncated_columns
pl.LazyFrame.with_strftime_columns = with_strftime_columns
pl.LazyFrame.delta = delta
pl.LazyFrame.cast_relaxed = cast_relaxed
pl.LazyFrame.partition_by_ext = partition_by
pl.LazyFrame.drop_null_columns = drop_null_columns
