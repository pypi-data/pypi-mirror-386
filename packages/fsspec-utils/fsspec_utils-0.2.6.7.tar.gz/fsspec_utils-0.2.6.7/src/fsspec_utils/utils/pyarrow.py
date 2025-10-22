import concurrent.futures
from collections import defaultdict

import numpy as np
import polars as pl
import pyarrow as pa
import pyarrow.compute as pc
import re

# Pre-compiled regex patterns (identical to original)
INTEGER_REGEX = r"^[-+]?\d+$"
FLOAT_REGEX = r"^[-+]?(?:\d*[.,])?\d+(?:[eE][-+]?\d+)?$"
BOOLEAN_REGEX = r"^(true|false|1|0|yes|ja|no|nein|t|f|y|j|n|ok|nok)$"
BOOLEAN_TRUE_REGEX = r"^(true|1|yes|ja|t|y|j|ok)$"
DATETIME_REGEX = (
    r"^("
    r"\d{4}-\d{2}-\d{2}"  # ISO: 2023-12-31
    r"|"
    r"\d{2}/\d{2}/\d{4}"  # US: 12/31/2023
    r"|"
    r"\d{2}\.\d{2}\.\d{4}"  # German: 31.12.2023
    r"|"
    r"\d{8}"  # Compact: 20231231
    r")"
    r"([ T]\d{2}:\d{2}(:\d{2}(\.\d{1,6})?)?)?"  # Optional time: 23:59[:59[.123456]]
    r"([+-]\d{2}:?\d{2}|Z|UTC)?"  # Optional timezone: +01:00, -0500, Z, UTC
    r"$"
)

# Float32 range limits
F32_MIN = float(np.finfo(np.float32).min)
F32_MAX = float(np.finfo(np.float32).max)


def convert_large_types_to_normal(schema: pa.Schema) -> pa.Schema:
    """
    Convert large types in a PyArrow schema to their standard types.

    Args:
        schema (pa.Schema): The PyArrow schema to convert.

    Returns:
        pa.Schema: A new PyArrow schema with large types converted to standard types.
    """
    # Define mapping of large types to standard types
    type_mapping = {
        pa.large_string(): pa.string(),
        pa.large_binary(): pa.binary(),
        pa.large_utf8(): pa.utf8(),
        pa.large_list(pa.null()): pa.list_(pa.null()),
        pa.large_list_view(pa.null()): pa.list_view(pa.null()),
    }
    # Convert fields
    new_fields = []
    for field in schema:
        field_type = field.type
        # Check if type exists in mapping
        if field_type in type_mapping:
            new_field = pa.field(
                name=field.name,
                type=type_mapping[field_type],
                nullable=field.nullable,
                metadata=field.metadata,
            )
            new_fields.append(new_field)
        # Handle large lists with nested types
        elif isinstance(field_type, pa.LargeListType):
            new_field = pa.field(
                name=field.name,
                type=pa.list_(
                    type_mapping[field_type.value_type]
                    if field_type.value_type in type_mapping
                    else field_type.value_type
                ),
                nullable=field.nullable,
                metadata=field.metadata,
            )
            new_fields.append(new_field)
        # Handle dictionary with large_string, large_utf8, or large_binary values
        elif isinstance(field_type, pa.DictionaryType):
            new_field = pa.field(
                name=field.name,
                type=pa.dictionary(
                    field_type.index_type,
                    type_mapping[field_type.value_type]
                    if field_type.value_type in type_mapping
                    else field_type.value_type,
                    field_type.ordered,
                ),
                # nullable=field.nullable,
                metadata=field.metadata,
            )
            new_fields.append(new_field)
        else:
            new_fields.append(field)

    return pa.schema(new_fields)


def dominant_timezone_per_column(
    schemas: list[pa.Schema],
) -> dict[str, tuple[str | None, str | None]]:
    """
    For each timestamp column (by name) across all schemas, detect the most frequent timezone (including None).
    If None and a timezone are tied, prefer the timezone.
    Returns a dict: {column_name: dominant_timezone}
    """
    from collections import Counter, defaultdict

    tz_counts = defaultdict(Counter)
    units = {}

    for schema in schemas:
        for field in schema:
            if pa.types.is_timestamp(field.type):
                tz = field.type.tz
                name = field.name
                tz_counts[name][tz] += 1
                # Track unit for each column (assume consistent)
                if name not in units:
                    units[name] = field.type.unit

    dominant = {}
    for name, counter in tz_counts.items():
        most_common = counter.most_common()
        if not most_common:
            continue
        top_count = most_common[0][1]
        # Find all with top_count
        top_tzs = [tz for tz, cnt in most_common if cnt == top_count]
        # If tie and one is not None, prefer not-None
        if len(top_tzs) > 1 and any(tz is not None for tz in top_tzs):
            tz = next(tz for tz in top_tzs if tz is not None)
        else:
            tz = most_common[0][0]
        dominant[name] = (units[name], tz)
    return dominant


def standardize_schema_timezones_by_majority(
    schemas: list[pa.Schema],
) -> list[pa.Schema]:
    """
    For each timestamp column (by name) across all schemas, set the timezone to the most frequent (with tie-breaking).
    Returns a new list of schemas with updated timestamp timezones.
    """
    dom = dominant_timezone_per_column(schemas)
    new_schemas = []
    for schema in schemas:
        fields = []
        for field in schema:
            if pa.types.is_timestamp(field.type) and field.name in dom:
                unit, tz = dom[field.name]
                fields.append(
                    pa.field(
                        field.name,
                        pa.timestamp(unit, tz),
                        field.nullable,
                        field.metadata,
                    )
                )
            else:
                fields.append(field)
        new_schemas.append(pa.schema(fields, schema.metadata))
    return new_schemas


def standardize_schema_timezones(
    schemas: list[pa.Schema], timezone: str | None = None
) -> list[pa.Schema]:
    """
    Standardize timezone info for all timestamp columns in a list of PyArrow schemas.

    Args:
        schemas (list of pa.Schema): List of PyArrow schemas.
        timezone (str or None): If None, remove timezone from all timestamp columns.
                                If str, set this timezone for all timestamp columns.
                                If "auto", use the most frequent timezone across schemas.

    Returns:
        list of pa.Schema: New schemas with standardized timezone info.
    """
    if timezone == "auto":
        # Use the most frequent timezone for each column
        return standardize_schema_timezones_by_majority(schemas)
    new_schemas = []
    for schema in schemas:
        fields = []
        for field in schema:
            if pa.types.is_timestamp(field.type):
                fields.append(
                    pa.field(
                        field.name,
                        pa.timestamp(field.type.unit, timezone),
                        field.nullable,
                        field.metadata,
                    )
                )
            else:
                fields.append(field)
        new_schemas.append(pa.schema(fields, schema.metadata))
    return new_schemas


def _is_type_compatible(type1: pa.DataType, type2: pa.DataType) -> bool:
    """
    Check if two PyArrow types can be automatically promoted by pyarrow.unify_schemas.

    Returns True if types are compatible for automatic promotion, False if manual casting is needed.
    """
    # Null types are compatible with everything
    if pa.types.is_null(type1) or pa.types.is_null(type2):
        return True

    # Same types are always compatible
    if type1 == type2:
        return True

    # Numeric type compatibility
    # Integer types can be promoted within signed/unsigned categories and to floats
    if pa.types.is_integer(type1) and pa.types.is_integer(type2):
        # Both signed or both unsigned - can promote to larger type
        type1_signed = not pa.types.is_unsigned_integer(type1)
        type2_signed = not pa.types.is_unsigned_integer(type2)
        return type1_signed == type2_signed

    # Integer to float compatibility
    if (pa.types.is_integer(type1) and pa.types.is_floating(type2)) or (
        pa.types.is_floating(type1) and pa.types.is_integer(type2)
    ):
        return True

    # Float to float compatibility
    if pa.types.is_floating(type1) and pa.types.is_floating(type2):
        return True

    # Temporal type compatibility
    # Date types
    if pa.types.is_date(type1) and pa.types.is_date(type2):
        return True

    # Time types
    if pa.types.is_time(type1) and pa.types.is_time(type2):
        return True

    # Timestamp types (different precisions can be unified)
    if pa.types.is_timestamp(type1) and pa.types.is_timestamp(type2):
        return True

    # String vs binary types - these are incompatible
    if (pa.types.is_string(type1) or pa.types.is_large_string(type1)) and (
        pa.types.is_binary(type2) or pa.types.is_large_binary(type2)
    ):
        return False
    if (pa.types.is_binary(type1) or pa.types.is_large_binary(type1)) and (
        pa.types.is_string(type2) or pa.types.is_large_string(type2)
    ):
        return False

    # String/numeric types are incompatible
    if (pa.types.is_string(type1) or pa.types.is_large_string(type1)) and (
        pa.types.is_integer(type1) or pa.types.is_floating(type1)
    ):
        return False
    if (pa.types.is_string(type2) or pa.types.is_large_string(type2)) and (
        pa.types.is_integer(type2) or pa.types.is_floating(type2)
    ):
        return False

    # Struct types - only compatible if field names and types are compatible
    if isinstance(type1, pa.StructType) and isinstance(type2, pa.StructType):
        if len(type1) != len(type2):
            return False
        # Check if field names match
        if set(f.name for f in type1) != set(f.name for f in type2):
            return False
        # Check if corresponding field types are compatible
        for f1, f2 in zip(type1, type2):
            if f1.name != f2.name:
                return False
            if not _is_type_compatible(f1.type, f2.type):
                return False
        return True

    # List types - only compatible if element types are compatible
    if isinstance(type1, pa.ListType) and isinstance(type2, pa.ListType):
        return _is_type_compatible(type1.value_type, type2.value_type)

    # Dictionary types - generally incompatible unless identical
    if isinstance(type1, pa.DictionaryType) and isinstance(type2, pa.DictionaryType):
        return (
            type1.value_type == type2.value_type
            and type1.index_type == type2.index_type
        )

    # All other combinations are considered incompatible
    return False


def _find_common_numeric_type(types: set[pa.DataType]) -> pa.DataType | None:
    """
    Find the optimal common numeric type for a set of numeric types.

    Returns None if types are not numeric or cannot be unified.
    """
    if not types:
        return None

    # Check if ALL types are numeric
    if not all(pa.types.is_integer(t) or pa.types.is_floating(t) for t in types):
        return None

    # Filter only numeric types
    numeric_types = [
        t for t in types if pa.types.is_integer(t) or pa.types.is_floating(t)
    ]
    if not numeric_types:
        return None

    # Check for mixed signed/unsigned integers
    signed_ints = [
        t
        for t in numeric_types
        if pa.types.is_integer(t) and not pa.types.is_unsigned_integer(t)
    ]
    unsigned_ints = [t for t in numeric_types if pa.types.is_unsigned_integer(t)]
    floats = [t for t in numeric_types if pa.types.is_floating(t)]

    # If we have floats, promote to the largest float type
    if floats:
        if any(t == pa.float64() for t in floats):
            return pa.float64()
        return pa.float32()

    # If we have mixed signed and unsigned integers, must promote to float
    if signed_ints and unsigned_ints:
        # Find the largest integer to determine float precision needed
        all_ints = signed_ints + unsigned_ints
        bit_widths = []
        for t in all_ints:
            if t == pa.int8() or t == pa.uint8():
                bit_widths.append(8)
            elif t == pa.int16() or t == pa.uint16():
                bit_widths.append(16)
            elif t == pa.int32() or t == pa.uint32():
                bit_widths.append(32)
            elif t == pa.int64() or t == pa.uint64():
                bit_widths.append(64)

        max_width = max(bit_widths) if bit_widths else 32
        # Use float64 for 64-bit integers to preserve precision
        return pa.float64() if max_width >= 64 else pa.float32()

    # Only signed integers - find largest
    if signed_ints:
        if pa.int64() in signed_ints:
            return pa.int64()
        elif pa.int32() in signed_ints:
            return pa.int32()
        elif pa.int16() in signed_ints:
            return pa.int16()
        else:
            return pa.int8()

    # Only unsigned integers - find largest
    if unsigned_ints:
        if pa.uint64() in unsigned_ints:
            return pa.uint64()
        elif pa.uint32() in unsigned_ints:
            return pa.uint32()
        elif pa.uint16() in unsigned_ints:
            return pa.uint16()
        else:
            return pa.uint8()

    return None


def _analyze_string_vs_numeric_conflict(
    string_type: pa.DataType, numeric_type: pa.DataType
) -> pa.DataType:
    """
    Analyze string vs numeric type conflict and determine best conversion strategy.

    For now, defaults to string type as it's the safest option.
    In a more sophisticated implementation, this could analyze actual data content
    to make an informed decision.
    """
    # Default strategy: convert to string to preserve all information
    # This could be enhanced with data sampling to determine optimal conversion
    return pa.string()


def _handle_temporal_conflicts(types: set[pa.DataType]) -> pa.DataType | None:
    """
    Handle conflicts between temporal types (date, time, timestamp).
    """
    if not types:
        return None

    # Check if ALL types are temporal
    if not all(pa.types.is_temporal(t) for t in types):
        return None

    # Filter temporal types
    temporal_types = [t for t in types if pa.types.is_temporal(t)]
    if not temporal_types:
        return None

    # If we have timestamps, they take precedence
    timestamps = [t for t in temporal_types if pa.types.is_timestamp(t)]
    if timestamps:
        # Find the highest precision timestamp
        # For simplicity, use the first one - in practice might want to find highest precision
        return timestamps[0]

    # If we have times, they take precedence over dates
    times = [t for t in temporal_types if pa.types.is_time(t)]
    if times:
        # Use the higher precision time
        if any(t == pa.time64() for t in times):
            return pa.time64()
        return pa.time32()

    # Only dates remain
    dates = [t for t in temporal_types if pa.types.is_date(t)]
    if dates:
        # Use the higher precision date
        if any(t == pa.date64() for t in dates):
            return pa.date64()
        return pa.date32()

    return None


def _find_conflicting_fields(schemas):
    """Find fields with conflicting types across schemas and categorize them."""
    seen = defaultdict(set)
    for schema in schemas:
        for field in schema:
            seen[field.name].add(field.type)

    conflicts = {}
    for name, types in seen.items():
        if len(types) > 1:
            # Analyze the conflict
            conflicts[name] = {
                "types": types,
                "compatible": True,  # Assume compatible until proven otherwise
                "target_type": None,  # Will be determined by promotion logic
            }

    return conflicts


def _normalize_schema_types(schemas, conflicts):
    """Normalize schema types based on intelligent promotion rules."""
    # First, analyze all conflicts to determine target types
    promotions = {}

    for field_name, conflict_info in conflicts.items():
        types = conflict_info["types"]

        # Try to find a common type for compatible conflicts
        target_type = None

        # Check if all types are numeric and can be unified
        numeric_type = _find_common_numeric_type(types)
        if numeric_type is not None:
            target_type = numeric_type
            conflict_info["compatible"] = True
        # Check if all types are temporal and can be unified
        else:
            temporal_type = _handle_temporal_conflicts(types)
            if temporal_type is not None:
                target_type = temporal_type
                conflict_info["compatible"] = True
            else:
                # Check if any types are incompatible
                all_compatible = True
                type_list = list(types)
                for i in range(len(type_list)):
                    for j in range(i + 1, len(type_list)):
                        if not _is_type_compatible(type_list[i], type_list[j]):
                            all_compatible = False
                            break
                    if not all_compatible:
                        break

                conflict_info["compatible"] = all_compatible

                if all_compatible:
                    # Types are compatible but we don't have a specific rule
                    # Let PyArrow handle it automatically
                    target_type = None
                else:
                    # Types are incompatible - default to string for safety
                    target_type = pa.string()

        conflict_info["target_type"] = target_type
        if target_type is not None:
            promotions[field_name] = target_type

    # Apply the promotions to schemas
    normalized = []
    for schema in schemas:
        fields = []
        for field in schema:
            tgt = promotions.get(field.name)
            fields.append(field if tgt is None else field.with_type(tgt))
        normalized.append(pa.schema(fields, metadata=schema.metadata))

    return normalized


def _unique_schemas(schemas: list[pa.Schema]) -> list[pa.Schema]:
    """Get unique schemas from a list of schemas."""
    seen = {}
    unique = []
    for schema in schemas:
        key = schema.serialize().to_pybytes()
        if key not in seen:
            seen[key] = schema
            unique.append(schema)
    return unique


def _aggressive_fallback_unification(schemas: list[pa.Schema]) -> pa.Schema:
    """
    Aggressive fallback strategy for difficult unification scenarios.
    Converts all conflicting fields to strings as a last resort.
    """
    conflicts = _find_conflicting_fields(schemas)
    if not conflicts:
        # No conflicts, try direct unification
        try:
            return pa.unify_schemas(schemas, promote_options="permissive")
        except (pa.ArrowInvalid, pa.ArrowTypeError):
            pass

    # Convert all conflicting fields to strings
    for field_name, conflict_info in conflicts.items():
        conflict_info["target_type"] = pa.string()

    normalized_schemas = _normalize_schema_types(schemas, conflicts)
    try:
        return pa.unify_schemas(normalized_schemas, promote_options="permissive")
    except (pa.ArrowInvalid, pa.ArrowTypeError):
        # If even this fails, return first normalized schema
        return normalized_schemas[0]


def _remove_conflicting_fields(schemas: list[pa.Schema]) -> pa.Schema:
    """
    Remove fields that have type conflicts between schemas.
    Keeps only fields that have the same type across all schemas.

    Args:
        schemas (list[pa.Schema]): List of schemas to process.

    Returns:
        pa.Schema: Schema with only non-conflicting fields.
    """
    if not schemas:
        return pa.schema([])

    # Find conflicts
    conflicts = _find_conflicting_fields(schemas)
    conflicting_field_names = set(conflicts.keys())

    # Keep only non-conflicting fields from the first schema
    fields = []
    for field in schemas[0]:
        if field.name not in conflicting_field_names:
            fields.append(field)

    return pa.schema(fields)


def _remove_problematic_fields(schemas: list[pa.Schema]) -> pa.Schema:
    """
    Remove fields that cannot be unified across all schemas.
    This is a last resort when all other strategies fail.
    """
    if not schemas:
        return pa.schema([])

    # Find fields that exist in all schemas
    common_field_names = set(schemas[0].names)
    for schema in schemas[1:]:
        common_field_names &= set(schema.names)

    # Use fields from the first schema for common fields
    fields = []
    for field in schemas[0]:
        if field.name in common_field_names:
            fields.append(field)

    return pa.schema(fields)


def _log_conflict_summary(conflicts: dict, verbose: bool = False) -> None:
    """
    Log a summary of resolved conflicts for debugging purposes.
    """
    if not conflicts or not verbose:
        return

    print("Schema Unification Conflict Summary:")
    print("=" * 40)
    for field_name, conflict_info in conflicts.items():
        types_str = ", ".join(str(t) for t in conflict_info["types"])
        compatible = conflict_info["compatible"]
        target_type = conflict_info["target_type"]

        print(f"Field: {field_name}")
        print(f"  Types: {types_str}")
        print(f"  Compatible: {compatible}")
        print(f"  Target Type: {target_type}")
        print()


def _identify_empty_columns(table: pa.Table) -> list:
    """Identify columns that are entirely empty."""
    if table.num_rows == 0:
        return []

    empty_cols = []
    for col_name in table.column_names:
        column = table.column(col_name)
        if column.null_count == table.num_rows:
            empty_cols.append(col_name)

    return empty_cols


def unify_schemas(
    schemas: list[pa.Schema],
    use_large_dtypes: bool = False,
    timezone: str | None = None,
    standardize_timezones: bool = True,
    verbose: bool = False,
    remove_conflicting_columns: bool = False,
) -> pa.Schema:
    """
    Unify a list of PyArrow schemas into a single schema using intelligent conflict resolution.

    Args:
        schemas (list[pa.Schema]): List of PyArrow schemas to unify.
        use_large_dtypes (bool): If True, keep large types like large_string.
        timezone (str | None): If specified, standardize all timestamp columns to this timezone.
            If "auto", use the most frequent timezone across schemas.
            If None, remove timezone from all timestamp columns.
        standardize_timezones (bool): If True, standardize all timestamp columns to the most frequent timezone.
        verbose (bool): If True, print conflict resolution details for debugging.
        remove_conflicting_columns (bool): If True, allows removal of columns with type conflicts as a fallback
            strategy instead of converting them. Defaults to False.

    Returns:
        pa.Schema: A unified PyArrow schema.

    Raises:
        ValueError: If no schemas are provided.
    """
    if not schemas:
        raise ValueError("At least one schema must be provided for unification")

    # Early exit for single schema
    unique_schemas = _unique_schemas(schemas)
    if len(unique_schemas) == 1:
        result_schema = unique_schemas[0]
        if standardize_timezones:
            result_schema = standardize_schema_timezones([result_schema], timezone)[0]
        return (
            result_schema
            if use_large_dtypes
            else convert_large_types_to_normal(result_schema)
        )

    # Step 1: Find and resolve conflicts first
    conflicts = _find_conflicting_fields(unique_schemas)
    if conflicts and verbose:
        _log_conflict_summary(conflicts, verbose)

    if conflicts:
        # Normalize schemas using intelligent promotion rules
        unique_schemas = _normalize_schema_types(unique_schemas, conflicts)

    # Step 2: Attempt unification with conflict-resolved schemas
    try:
        unified_schema = pa.unify_schemas(unique_schemas, promote_options="permissive")

        # Step 3: Apply timezone standardization to the unified result
        if standardize_timezones:
            unified_schema = standardize_schema_timezones([unified_schema], timezone)[0]

        return (
            unified_schema
            if use_large_dtypes
            else convert_large_types_to_normal(unified_schema)
        )

    except (pa.ArrowInvalid, pa.ArrowTypeError) as e:
        # Step 4: Intelligent fallback strategies
        if verbose:
            print(f"Primary unification failed: {e}")
            print("Attempting fallback strategies...")

        # Fallback 1: Try aggressive string conversion for remaining conflicts
        try:
            fallback_schema = _aggressive_fallback_unification(unique_schemas)
            if standardize_timezones:
                fallback_schema = standardize_schema_timezones(
                    [fallback_schema], timezone
                )[0]
            if verbose:
                print("✓ Aggressive fallback succeeded")
            return (
                fallback_schema
                if use_large_dtypes
                else convert_large_types_to_normal(fallback_schema)
            )

        except Exception:
            if verbose:
                print("✗ Aggressive fallback failed")

        # Fallback 2: Remove conflicting fields (if enabled)
        if remove_conflicting_columns:
            try:
                non_conflicting_schema = _remove_conflicting_fields(unique_schemas)
                if standardize_timezones:
                    non_conflicting_schema = standardize_schema_timezones(
                        [non_conflicting_schema], timezone
                    )[0]
                if verbose:
                    print("✓ Remove conflicting fields fallback succeeded")
                return (
                    non_conflicting_schema
                    if use_large_dtypes
                    else convert_large_types_to_normal(non_conflicting_schema)
                )

            except Exception:
                if verbose:
                    print("✗ Remove conflicting fields fallback failed")

        # Fallback 3: Remove problematic fields that can't be unified
        try:
            minimal_schema = _remove_problematic_fields(unique_schemas)
            if standardize_timezones:
                minimal_schema = standardize_schema_timezones(
                    [minimal_schema], timezone
                )[0]
            if verbose:
                print("✓ Minimal schema (removed problematic fields) succeeded")
            return (
                minimal_schema
                if use_large_dtypes
                else convert_large_types_to_normal(minimal_schema)
            )

        except Exception:
            if verbose:
                print("✗ Minimal schema fallback failed")

        # Fallback 4: Return first schema as last resort
        if verbose:
            print("✗ All fallback strategies failed, returning first schema")

        first_schema = unique_schemas[0]
        if standardize_timezones:
            first_schema = standardize_schema_timezones([first_schema], timezone)[0]
        return (
            first_schema
            if use_large_dtypes
            else convert_large_types_to_normal(first_schema)
        )


def remove_empty_columns(table: pa.Table) -> pa.Table:
    """Remove columns that are entirely empty from a PyArrow table.

    Args:
        table (pa.Table): The PyArrow table to process.

    Returns:
        pa.Table: A new PyArrow table with empty columns removed.
    """
    empty_cols = _identify_empty_columns(table)
    if not empty_cols:
        return table
    return table.drop(empty_cols)


def cast_schema(table: pa.Table, schema: pa.Schema) -> pa.Table:
    """
    Cast a PyArrow table to a given schema, updating the schema to match the table's columns.

    Args:
        table (pa.Table): The PyArrow table to cast.
        schema (pa.Schema): The target schema to cast the table to.

    Returns:
        pa.Table: A new PyArrow table with the specified schema.
    """
    # Filter schema fields to only those present in the table
    table_columns = set(table.schema.names)
    filtered_fields = [field for field in schema if field.name in table_columns]
    updated_schema = pa.schema(filtered_fields)
    return table.select(updated_schema.names).cast(updated_schema)


NULL_LIKE_STRINGS = {
    "",
    "-",
    "None",
    "none",
    "NONE",
    "NaN",
    "Nan",
    "nan",
    "NAN",
    "N/A",
    "n/a",
    "Null",
    "NULL",
    "null",
}


def _normalize_datetime_string(s: str) -> str:
    """
    Normalize a datetime string by removing timezone information.

    Args:
        s: Datetime string potentially containing timezone info

    Returns:
        str: Normalized datetime string without timezone
    """
    s = str(s).strip()
    s = re.sub(r"Z$", "", s)
    s = re.sub(r"UTC$", "", s)
    s = re.sub(r"([+-]\d{2}:\d{2})$", "", s)
    s = re.sub(r"([+-]\d{4})$", "", s)
    return s


def _detect_timezone_from_sample(series: pl.Series) -> str | None:
    """
    Detect the most common timezone from a sample of datetime strings.

    Args:
        series: Polars Series containing datetime strings

    Returns:
        str or None: Most common timezone found, or None if no timezone detected
    """
    import random

    # Sample up to 1000 values for performance
    sample_size = min(1000, len(series))
    if sample_size == 0:
        return None

    # Get random sample
    sample_indices = random.sample(range(len(series)), sample_size)
    sample_values = [series[i] for i in sample_indices if series[i] is not None]

    if not sample_values:
        return None

    # Extract timezones
    timezones = []
    for val in sample_values:
        val = str(val).strip()
        match = re.search(r"(Z|UTC|[+-]\d{2}:\d{2}|[+-]\d{4})$", val)
        if match:
            tz = match.group(1)
            if tz == "Z":
                timezones.append("UTC")
            elif tz == "UTC":
                timezones.append("UTC")
            elif tz.startswith("+") or tz.startswith("-"):
                # Normalize timezone format
                if ":" not in tz:
                    tz = tz[:3] + ":" + tz[3:]
                timezones.append(tz)

    if not timezones:
        return None

    # Count frequencies
    from collections import Counter

    tz_counts = Counter(timezones)

    # Return most common timezone
    return tz_counts.most_common(1)[0][0]


def _clean_string_array(array: pa.Array) -> pa.Array:
    """Trimmt Strings und ersetzt definierte Platzhalter durch Null (Python-basiert, robust)."""
    if len(array) == 0:
        return array
    # pc.utf8_trim_whitespace kann fehlen / unterschiedlich sein → fallback
    py = [None if v is None else str(v).strip() for v in array.to_pylist()]
    cleaned_list = [None if (v is None or v in NULL_LIKE_STRINGS) else v for v in py]
    return pa.array(cleaned_list, type=pa.string())


def _can_downcast_to_float32(array: pa.Array) -> bool:
    """Prüft Float32 Range (Python fallback)."""
    if len(array) == 0 or array.null_count == len(array):
        return True
    values = [
        v
        for v in array.to_pylist()
        if isinstance(v, (int, float)) and v not in (None, float("inf"), float("-inf"))
    ]
    if not values:
        return True
    mn, mx = min(values), max(values)
    return F32_MIN <= mn <= mx <= F32_MAX


def _get_optimal_int_type(
    array: pa.Array, allow_unsigned: bool, allow_null: bool = True
) -> pa.DataType:
    values = [v for v in array.to_pylist() if v is not None]
    if not values:
        return pa.null() if allow_null else pa.int8()
    min_val = min(values)
    max_val = max(values)
    if allow_unsigned and min_val >= 0:
        if max_val <= 255:
            return pa.uint8()
        if max_val <= 65535:
            return pa.uint16()
        if max_val <= 4294967295:
            return pa.uint32()
        return pa.uint64()
    if -128 <= min_val and max_val <= 127:
        return pa.int8()
    if -32768 <= min_val and max_val <= 32767:
        return pa.int16()
    if -2147483648 <= min_val and max_val <= 2147483647:
        return pa.int32()
    return pa.int64()


def _optimize_numeric_array(
    array: pa.Array, shrink: bool, allow_unsigned: bool = True, allow_null: bool = True
) -> pa.DataType:
    """
    Optimize numeric PyArrow array by downcasting when possible.
    Returns the optimal dtype.
    """

    if not shrink or len(array) == 0 or array.null_count == len(array):
        if allow_null:
            return pa.null()
        else:
            return array.type

    if pa.types.is_floating(array.type):
        if array.type == pa.float64() and _can_downcast_to_float32(array):
            return pa.float32()
        return array.type

    if pa.types.is_integer(array.type):
        return _get_optimal_int_type(array, allow_unsigned, allow_null)

    return array.type


_REGEX_CACHE: dict[str, re.Pattern] = {}


def _all_match_regex(array: pa.Array, pattern: str) -> bool:
    """Python Regex Matching (alle nicht-null Werte)."""
    if len(array) == 0 or array.null_count == len(array):
        return False
    if pattern not in _REGEX_CACHE:
        _REGEX_CACHE[pattern] = re.compile(pattern, re.IGNORECASE)
    rgx = _REGEX_CACHE[pattern]
    for v in array.to_pylist():
        if v is None:
            continue
        if not rgx.match(str(v)):
            return False
    return True


def _optimize_string_array(
    array: pa.Array,
    col_name: str,
    shrink_numerics: bool,
    time_zone: str | None = None,
    allow_unsigned: bool = True,
    allow_null: bool = True,
    force_timezone: str | None = None,
) -> tuple[pa.Array, pa.DataType]:
    """Analysiere String-Array und bestimme Ziel-Datentyp.

    Rückgabe: (bereinigtes_array, ziel_datentyp)
    Platzhalter-/Leerwerte blockieren keine Erkennung mehr.
    """
    if len(array) == 0 or array.null_count == len(array):
        return array, (pa.null() if allow_null else array.type)

    cleaned_array = _clean_string_array(array)

    # Werte für Erkennung: nur nicht-null
    non_null_list = [v for v in cleaned_array.to_pylist() if v is not None]
    if not non_null_list:
        return cleaned_array, (pa.null() if allow_null else array.type)
    non_null = pa.array(non_null_list, type=pa.string())

    try:
        # Boolean
        if _all_match_regex(non_null, BOOLEAN_REGEX):
            bool_values = [
                True if re.match(BOOLEAN_TRUE_REGEX, v, re.IGNORECASE) else False
                for v in non_null_list
            ]
            # Rekonstruiere vollständige Länge unter Erhalt der Nulls
            it = iter(bool_values)
            casted_full = [
                next(it) if v is not None else None for v in cleaned_array.to_pylist()
            ]
            return pa.array(casted_full, type=pa.bool_()), pa.bool_()

        # Integer
        if _all_match_regex(non_null, INTEGER_REGEX):
            int_values = [int(v) for v in non_null_list]
            optimized_type = _get_optimal_int_type(
                pa.array(int_values, type=pa.int64()), allow_unsigned, allow_null
            )
            it = iter(int_values)
            casted_full = [
                next(it) if v is not None else None for v in cleaned_array.to_pylist()
            ]
            return pa.array(casted_full, type=optimized_type), optimized_type

        # Float
        if _all_match_regex(non_null, FLOAT_REGEX):
            float_values = [float(v.replace(",", ".")) for v in non_null_list]
            base_arr = pa.array(float_values, type=pa.float64())
            target_type = pa.float64()
            if shrink_numerics and _can_downcast_to_float32(base_arr):
                target_type = pa.float32()
            it = iter(float_values)
            casted_full = [
                next(it) if v is not None else None for v in cleaned_array.to_pylist()
            ]
            return pa.array(casted_full, type=target_type), target_type

        # Datetime
        if _all_match_regex(non_null, DATETIME_REGEX):
            # Nutzung Polars für tolerant parsing mit erweiterter Format-Unterstützung
            pl_series = pl.Series(col_name, cleaned_array)

            # Prüfe ob gemischte Zeitzonen vorhanden sind
            has_tz = pl_series.str.contains(r"(Z|UTC|[+-]\d{2}:\d{2}|[+-]\d{4})$").any()

            if has_tz:
                # Bei gemischten Zeitzonen, verwende eager parsing auf Series-Ebene
                normalized_series = pl_series.map_elements(
                    _normalize_datetime_string, return_dtype=pl.String
                )

                if force_timezone is not None:
                    dt_series = normalized_series.str.to_datetime(
                        time_zone=force_timezone, time_unit="us"
                    )
                else:
                    detected_tz = _detect_timezone_from_sample(pl_series)
                    if detected_tz is not None:
                        dt_series = normalized_series.str.to_datetime(
                            time_zone=detected_tz, time_unit="us"
                        )
                    else:
                        dt_series = normalized_series.str.to_datetime(time_unit="us")

                converted = dt_series
            else:
                # Bei konsistenten Zeitzonen, verwende Polars' eingebaute Format-Erkennung
                if force_timezone is not None:
                    converted = pl_series.str.to_datetime(
                        time_zone=force_timezone, time_unit="us"
                    )
                else:
                    # Prüfe ob Zeitzonen vorhanden sind
                    has_any_tz = pl_series.str.contains(
                        r"(Z|UTC|[+-]\d{2}:\d{2}|[+-]\d{4})$"
                    ).any()
                    if has_any_tz:
                        # Automatische Zeitzonenerkennung
                        converted = pl_series.str.to_datetime(time_unit="us")
                    else:
                        # Ohne Zeitzonen
                        converted = pl_series.str.to_datetime(time_unit="us")

            return converted.to_arrow(), converted.to_arrow().type
    except Exception:  # pragma: no cover
        pass

    # Kein Cast
    return cleaned_array, pa.string()


def _process_column(
    array: pa.Array,
    col_name: str,
    shrink_numerics: bool,
    allow_unsigned: bool,
    time_zone: str | None = None,
    force_timezone: str | None = None,
) -> tuple[pa.Field, pa.Array]:
    """
    Process a single column for type optimization.
    Returns a pyarrow.Field with the optimal dtype.
    """
    # array = table[col_name]
    if array.null_count == len(array):
        return pa.field(col_name, pa.null()), array

    if pa.types.is_floating(array.type) or pa.types.is_integer(array.type):
        dtype = _optimize_numeric_array(array, shrink_numerics, allow_unsigned)
        return pa.field(col_name, dtype, nullable=array.null_count > 0), array
    elif pa.types.is_string(array.type) or pa.types.is_large_string(array.type):
        casted_array, dtype = _optimize_string_array(
            array,
            col_name,
            shrink_numerics,
            time_zone,
            allow_unsigned=allow_unsigned,
            allow_null=True,
            force_timezone=force_timezone,
        )
        return pa.field(
            col_name, dtype, nullable=casted_array.null_count > 0
        ), casted_array
    else:
        return pa.field(col_name, array.type, nullable=array.null_count > 0), array


def _process_column_for_opt_dtype(args):
    (
        array,
        col_name,
        cols_to_process,
        shrink_numerics,
        allow_unsigned,
        time_zone,
        strict,
        allow_null,
        force_timezone,
    ) = args
    try:
        if col_name in cols_to_process:
            field, array = _process_column(
                array,
                col_name,
                shrink_numerics,
                allow_unsigned,
                time_zone,
                force_timezone,
            )
            if pa.types.is_null(field.type):
                if allow_null:
                    array = pa.nulls(array.length(), type=pa.null())
                    return (col_name, field, array)
                else:
                    orig_type = array.type
                    # array = table[col_name]
                    field = pa.field(col_name, orig_type, nullable=True)
                    return (col_name, field, array)
            return (col_name, field, array)
        else:
            field = pa.field(col_name, array.type, nullable=True)
            # array = table[col_name]
            return (col_name, field, array)
    except Exception as e:
        if strict:
            raise e
        field = pa.field(col_name, array.type, nullable=True)
        return (col_name, field, array)


def opt_dtype(
    table: pa.Table,
    include: str | list[str] | None = None,
    exclude: str | list[str] | None = None,
    time_zone: str | None = None,
    shrink_numerics: bool = True,
    allow_unsigned: bool = True,
    use_large_dtypes: bool = False,
    strict: bool = False,
    allow_null: bool = True,
    *,
    force_timezone: str | None = None,
) -> pa.Table:
    """
    Optimize data types of a PyArrow Table for performance and memory efficiency.
    Returns a new table casted to the optimal schema.

    Args:
        table: The PyArrow table to optimize.
        include: Column(s) to include in optimization (default: all columns).
        exclude: Column(s) to exclude from optimization.
        time_zone: Optional time zone hint during datetime parsing.
        shrink_numerics: Whether to downcast numeric types when possible.
        allow_unsigned: Whether to allow unsigned integer types.
        use_large_dtypes: If True, keep large types like large_string.
        strict: If True, will raise an error if any column cannot be optimized.
        allow_null: If False, columns that only hold null-like values will not be converted to pyarrow.null().
        force_timezone: If set, ensure all parsed datetime columns end up with this timezone.
    """
    if isinstance(include, str):
        include = [include]
    if isinstance(exclude, str):
        exclude = [exclude]

    cols_to_process = table.column_names
    if include:
        cols_to_process = [col for col in include if col in table.column_names]
    if exclude:
        cols_to_process = [col for col in cols_to_process if col not in exclude]

    # Prepare arguments for parallel processing
    args_list = [
        (
            table[col_name],
            col_name,
            cols_to_process,
            shrink_numerics,
            allow_unsigned,
            time_zone,
            strict,
            allow_null,
            force_timezone,
        )
        for col_name in table.column_names
    ]

    # Parallelize column processing
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(executor.map(_process_column_for_opt_dtype, args_list))

    # Sort results to preserve column order
    results.sort(key=lambda x: table.column_names.index(x[0]))
    fields = [field for _, field, _ in results]
    arrays = [array for _, _, array in results]

    schema = pa.schema(fields)
    if use_large_dtypes:
        schema = convert_large_types_to_normal(schema)
    return pa.Table.from_arrays(arrays, schema=schema)
