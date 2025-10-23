
import pandas as pd
import os
import duckdb
import pytz
from typing import Dict
import yaml
import logging
from .config import get_config_or_params

# Initialize logger for this module
logger = logging.getLogger('clifpy.utils.io')

# conn = duckdb.connect(database=':memory:')

def _cast_id_cols_to_string(df):
    id_cols = [c for c in df.columns if c.endswith("_id")]
    if id_cols:                                   # no-op if none found
        df[id_cols] = df[id_cols].astype("string")
    return df


def load_config(file_path: str) -> Dict:
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config


def load_parquet_with_tz(file_path, columns=None, filters=None, sample_size=None, verbose=False):
    # Extract just the filename for cleaner output
    filename = os.path.basename(file_path)
    if verbose:
        logger.info(f"Loading {filename}")
    con = duckdb.connect()
    # DuckDB >=0.9 understands the original zone if we ask for TIMESTAMPTZ
    con.execute("SET timezone = 'UTC';")          # read & return in UTC
    con.execute("SET pandas_analyze_sample=0;")   # avoid sampling issues

    sel = "*" if columns is None else ", ".join(columns)
    query = f"SELECT {sel} FROM parquet_scan('{file_path}')"

    if filters:                                  # optional WHERE clause
        clauses = []
        for col, val in filters.items():
            if isinstance(val, list):
                vals = ", ".join([f"'{v}'" for v in val])
                clauses.append(f"{col} IN ({vals})")
            else:
                clauses.append(f"{col} = '{val}'")
        query += " WHERE " + " AND ".join(clauses)
    if sample_size:
        query += f" LIMIT {sample_size}"

    df = con.execute(query).fetchdf()            # pandas DataFrame
    con.close()
    df = _cast_id_cols_to_string(df)         # cast id columns to string
    return df

def load_data(table_name, table_path, table_format_type, sample_size=None, columns=None, filters=None, site_tz=None, verbose=False) -> pd.DataFrame:
    """
    Load data from a file in the specified directory with the option to select specific columns and apply filters.

    Parameters
    ----------
    table_name : str
        The name of the table to load.
    table_path : str
        Path to the directory containing the data file.
    table_format_type : str
        Format of the data file (e.g., 'csv', 'parquet').
    sample_size : int, optional
        Number of rows to load.
    columns : list of str, optional
        List of column names to load.
    filters : dict, optional
        Dictionary of filters to apply.
    site_tz : str, optional
        Timezone string for datetime conversion, e.g., "America/New_York".
    verbose : bool, optional
        If True, show detailed loading messages. Default is False.

    Returns
    -------
    pd.DataFrame
        DataFrame containing the requested data.
    """
    # Determine the file path based on the directory and filetype
  
    file_path = os.path.join(table_path, 'clif_'+ table_name + '.' + table_format_type)
    
    # Load the data based on filetype
    if os.path.exists(file_path):
        if  table_format_type == 'csv':
            if verbose:
                logger.info('Loading CSV file')
            # For CSV, we can use DuckDB to read specific columns and apply filters efficiently
            con = duckdb.connect()
            # Build the SELECT clause
            select_clause = "*" if not columns else ", ".join(columns)
            # Start building the query
            query = f"SELECT {select_clause} FROM read_csv_auto('{file_path}')"
            # Apply filters
            if filters:
                filter_clauses = []
                for column, values in filters.items():
                    if isinstance(values, list):
                        # Escape single quotes and wrap values in quotes
                        values_list = ', '.join(["'" + str(value).replace("'", "''") + "'" for value in values])
                        filter_clauses.append(f"{column} IN ({values_list})")
                    else:
                        value = str(values).replace("'", "''")
                        filter_clauses.append(f"{column} = '{value}'")
                if filter_clauses:
                    query += " WHERE " + " AND ".join(filter_clauses)
            # Apply sample size limit
            if sample_size:
                query += f" LIMIT {sample_size}"
            # Execute the query and fetch the data
            df = con.execute(query).fetchdf()
            con.close()
        elif table_format_type == 'parquet':
            df = load_parquet_with_tz(file_path, columns, filters, sample_size, verbose)
        else:
            raise ValueError("Unsupported filetype. Only 'csv' and 'parquet' are supported.")
        # Extract just the filename for cleaner output
        filename = os.path.basename(file_path)
        if verbose:
            logger.info(f"Data loaded successfully from {filename}")
        df = _cast_id_cols_to_string(df) # Cast id columns to string
        
        # Convert datetime columns to site timezone if specified
        if site_tz:
            df = convert_datetime_columns_to_site_tz(df, site_tz, verbose)
        
        return df
    else:
        raise FileNotFoundError(f"The file {file_path} does not exist in the specified directory.")

def convert_datetime_columns_to_site_tz(df, site_tz_str, verbose=True):
    """
    Convert all datetime columns in the DataFrame to the specified site timezone.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame.
    site_tz_str : str
        Timezone string, e.g., "America/New_York". or "US/Central"
    verbose : bool
        Whether to print detailed output (default: True).

    Returns
    -------
    pd.DataFrame
        Modified DataFrame with datetime columns converted.
    """
    site_tz = pytz.timezone(site_tz_str)

    # Identify datetime-related columns
    dttm_columns = [col for col in df.columns if 'dttm' in col]

    if not dttm_columns:
        logger.debug("No datetime columns found in DataFrame")
        return df

    # Track conversion statistics
    converted_cols = []
    already_correct_cols = []
    naive_cols = []
    problem_cols = []

    for col in dttm_columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')
        if pd.api.types.is_datetime64tz_dtype(df[col]):
            current_tz = df[col].dt.tz
            # Compare timezone names/strings instead of timezone objects
            if str(current_tz) == str(site_tz):
                already_correct_cols.append(col)
                logger.debug(f"{col}: Already in timezone {current_tz}")
            else:
                null_before = df[col].isna().sum()
                df[col] = df[col].dt.tz_convert(site_tz)
                null_after = df[col].isna().sum()
                converted_cols.append(col)
                if null_before != null_after:
                    logger.warning(f"{col}: Null count changed during conversion ({null_before} → {null_after})")
                logger.debug(f"{col}: Converted from {current_tz} to {site_tz}")
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.tz_localize(site_tz, ambiguous=True, nonexistent='shift_forward')
            naive_cols.append(col)
            logger.warning(f"{col}: Naive datetime localized to {site_tz}. Please verify this is correct.")
        else:
            problem_cols.append(col)
            logger.warning(f"{col}: Expected datetime but found {df[col].dtype}")

    # Log summary based on verbosity
    if verbose and (converted_cols or naive_cols or problem_cols):
        summary_parts = []
        if converted_cols:
            summary_parts.append(f"{len(converted_cols)} converted to {site_tz}")
        if already_correct_cols:
            summary_parts.append(f"{len(already_correct_cols)} already correct")
        if naive_cols:
            summary_parts.append(f"{len(naive_cols)} naive dates localized")
        if problem_cols:
            summary_parts.append(f"{len(problem_cols)} problematic")

        logger.info(f"Timezone processing complete: {', '.join(summary_parts)}")

        if logger.isEnabledFor(logging.DEBUG):
            if converted_cols:
                logger.debug(f"Converted columns: {', '.join(converted_cols)}")
            if naive_cols:
                logger.debug(f"Naive columns: {', '.join(naive_cols)}")
            if problem_cols:
                logger.debug(f"Problem columns: {', '.join(problem_cols)}")

    return df
