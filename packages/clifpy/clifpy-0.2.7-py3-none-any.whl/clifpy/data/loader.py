"""
Demo dataset loading functions for pyCLIF.

Provides easy access to sample CLIF data for testing and demonstration.
Similar to sklearn's toy datasets but specific to CLIF format.
"""

import os
import pandas as pd
from typing import Dict, Optional, List, Union
from pathlib import Path

from ..clif_orchestrator import ClifOrchestrator


DEMO_TABLES = [
    'patient',
    'hospitalization',
    'adt',
    'labs',
    'vitals',
    'respiratory_support',
    'position',
    'medication_admin_continuous',
    'patient_assessments'
]


def _get_demo_data_path() -> str:
    """Get the path to demo data directory."""
    # Get the path relative to this file
    current_dir = Path(__file__).parent
    demo_path = current_dir / 'clif_demo'
    return str(demo_path.absolute())


def _load_demo_table(table_name: str, return_raw: bool = False) -> Union[pd.DataFrame, object]:
    """
    Load a single demo table.
    
    Parameters:
        table_name (str): Name of the table (e.g., 'patient', 'labs')
        return_raw (bool): If True, return raw DataFrame. If False, return table object.
        
    Returns:
        Union[pd.DataFrame, table_object]: Either raw DataFrame or wrapped table object
    """
    demo_path = _get_demo_data_path()
    file_path = os.path.join(demo_path, f'clif_{table_name}.parquet')
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Demo data file not found: {file_path}")
    
    # Load raw data
    df = pd.read_parquet(file_path)
    
    if return_raw:
        return df
    
    # Import table classes here to avoid circular imports
    from ..tables.patient import Patient
    from ..tables.adt import Adt
    from ..tables.hospitalization import Hospitalization
    from ..tables.labs import Labs
    from ..tables.vitals import Vitals
    from ..tables.respiratory_support import RespiratorySupport
    from ..tables.position import Position
    from ..tables.medication_admin_continuous import MedicationAdminContinuous
    from ..tables.patient_assessments import PatientAssessments

    # Return wrapped table object
    table_classes = {
        'patient': Patient,
        'adt': Adt,
        'hospitalization': Hospitalization,
        'labs': Labs,
        'vitals': Vitals,
        'respiratory_support': RespiratorySupport,
        'position': Position,
        'medication_admin_continuous': MedicationAdminContinuous,
        'patient_assessments': PatientAssessments
    }
    
    if table_name in table_classes:
        # Create table object with proper parameters
        table_obj = table_classes[table_name](
            data_directory=str(_get_demo_data_path()),
            filetype="parquet",
            timezone="UTC",
            output_directory=None,  # Will use default
            data=df  # Pass the loaded DataFrame
        )
        return table_obj
    else:
        raise ValueError(f"Unknown table name: {table_name}. Available: {list(table_classes.keys())}")


def load_demo_clif(
    tables: Optional[List[str]] = None,
    timezone: str = "UTC",
    verbose: bool = False
) -> ClifOrchestrator:
    """
    Load a CLIF orchestrator populated with demo data.
    
    Parameters
    ----------
    tables : List[str], optional
        List of tables to load. If None, loads all available.
    timezone : str, default="UTC"
        Timezone for datetime conversion.
    verbose : bool, default=False
        If True, show detailed loading messages.
        
    Returns
    -------
    ClifOrchestrator
        Initialized orchestrator with demo data
        
    Examples
    --------
    >>> from clifpy.data import load_demo_clif
    >>> demo_clif = load_demo_clif()
    >>> sorted(demo_clif.get_loaded_tables())
    """
    available_tables = set(DEMO_TABLES)

    if tables is None:
        tables_to_load = list(DEMO_TABLES)
    else:
        unknown_tables = sorted(set(tables) - available_tables)
        if unknown_tables:
            raise ValueError(
                "Unknown table name(s): " + ", ".join(unknown_tables) +
                f". Available demo tables: {sorted(available_tables)}"
            )
        tables_to_load = list(dict.fromkeys(tables))

    orchestrator = ClifOrchestrator(
        data_directory=_get_demo_data_path(),
        filetype="parquet",
        timezone=timezone,
        output_directory=None
    )

    if verbose:
        print("Loading demo CLIF tables:", ", ".join(tables_to_load))

    orchestrator.initialize(tables=tables_to_load)

    if verbose:
        print("Loaded tables:", ", ".join(orchestrator.get_loaded_tables()))

    return orchestrator


# Individual table loading functions
def load_demo_patient(return_raw: bool = False):
    """
    Load demo patient data.
    
    Parameters
    ----------
    return_raw : bool, default=False
        If True, return raw DataFrame. If False, return patient object.
        
    Returns
    -------
    Union[pd.DataFrame, patient]
        Patient data
        
    Examples
    --------
    >>> from clifpy.data import load_demo_patient
    >>> patient_data = load_demo_patient()
    >>> print(f"Number of patients: {len(patient_data.df)}")
    >>> 
    >>> # Get raw DataFrame
    >>> patient_df = load_demo_patient(return_raw=True)
    >>> print(patient_df.head())
    """
    return _load_demo_table('patient', return_raw)


def load_demo_labs(return_raw: bool = False):
    """
    Load demo labs data.
    
    Parameters
    ----------
    return_raw : bool, default=False
        If True, return raw DataFrame. If False, return labs object.
        
    Returns
    -------
    Union[pd.DataFrame, labs]
        Labs data
    """
    return _load_demo_table('labs', return_raw)


def load_demo_vitals(return_raw: bool = False):
    """
    Load demo vitals data.
    
    Parameters
    ----------
    return_raw : bool, default=False
        If True, return raw DataFrame. If False, return vitals object.
        
    Returns
    -------
    Union[pd.DataFrame, vitals]
        Vitals data
    """
    return _load_demo_table('vitals', return_raw)


def load_demo_respiratory_support(return_raw: bool = False):
    """
    Load demo respiratory support data.
    
    Parameters
    ----------
    return_raw : bool, default=False
        If True, return raw DataFrame. If False, return respiratory_support object.
        
    Returns
    -------
    Union[pd.DataFrame, respiratory_support]
        Respiratory support data
    """
    return _load_demo_table('respiratory_support', return_raw)

def load_demo_position(return_raw: bool = False):
    """
    Load demo position data.
    
    Parameters
    ----------
    return_raw : bool, default=False
        If True, return raw DataFrame. If False, return position object.
        
    Returns
    -------
    Union[pd.DataFrame, position]
        Position data
    """
    return _load_demo_table('position', return_raw)


def load_demo_adt(return_raw: bool = False):
    """
    Load demo ADT data.
    
    Parameters
    ----------
    return_raw : bool, default=False
        If True, return raw DataFrame. If False, return adt object.
        
    Returns
    -------
    Union[pd.DataFrame, adt]
        ADT data
    """
    return _load_demo_table('adt', return_raw)


def load_demo_hospitalization(return_raw: bool = False):
    """
    Load demo hospitalization data.
    
    Parameters
    ----------
    return_raw : bool, default=False
        If True, return raw DataFrame. If False, return hospitalization object.
        
    Returns
    -------
    Union[pd.DataFrame, hospitalization]
        Hospitalization data
    """
    return _load_demo_table('hospitalization', return_raw)

def load_demo_medication_admin_continuous(return_raw: bool = False):
    """
    Load demo medication admin continuous data.
    
    Parameters
    ----------
    return_raw : bool, default=False
        If True, return raw DataFrame. If False, return medication_admin_continuous object.
        
    Returns
    -------
    Union[pd.DataFrame, medication_admin_continuous]
        Medication admin continuous data
    """
    return _load_demo_table('medication_admin_continuous', return_raw)

def load_demo_patient_assessments(return_raw: bool = False):
    """
    Load demo patient assessments data.
    
    Parameters
    ----------
    return_raw : bool, default=False
        If True, return raw DataFrame. If False, return patient_assessments object.
        
    Returns
    -------
    Union[pd.DataFrame, patient_assessments]
        Patient assessments data
    """
    return _load_demo_table('patient_assessments', return_raw)


def list_demo_datasets() -> Dict[str, Dict[str, Union[int, str]]]:
    """
    List all available demo datasets with basic information.
    
    Returns
    -------
    Dict
        Information about each demo dataset
        
    Examples
    --------
    >>> from clifpy.data import list_demo_datasets
    >>> datasets_info = list_demo_datasets()
    >>> for name, info in datasets_info.items():
    ...     print(f"{name}: {info['rows']} rows, {info['size']}")
    """
    demo_path = _get_demo_data_path()
    datasets_info = {}
    
    # Only include implemented tables
    for table_name in DEMO_TABLES:
        file_path = os.path.join(demo_path, f'clif_{table_name}.parquet')
        if os.path.exists(file_path):
            try:
                df = pd.read_parquet(file_path)
                file_size = os.path.getsize(file_path)
                
                # Convert file size to human readable format
                if file_size < 1024:
                    size_str = f"{file_size} B"
                elif file_size < 1024 * 1024:
                    size_str = f"{file_size / 1024:.1f} KB"
                else:
                    size_str = f"{file_size / (1024 * 1024):.1f} MB"
                
                datasets_info[table_name] = {
                    'rows': len(df),
                    'columns': len(df.columns),
                    'size': size_str,
                    'file_path': file_path
                }
            except Exception as e:
                datasets_info[table_name] = {
                    'error': str(e),
                    'file_path': file_path
                }
    
    return datasets_info


def get_demo_summary() -> None:
    """
    Print a summary of all available demo datasets.
    
    Examples
    --------
    >>> from clifpy.data import get_demo_summary
    >>> get_demo_summary()
    """
    datasets_info = list_demo_datasets()
    
    print("🏥 pyCLIF Demo Datasets Summary")
    print("=" * 50)
    
    total_rows = 0
    for name, info in datasets_info.items():
        if 'error' not in info:
            print(f"{name:30} | {info['rows']:6,} rows | {info['columns']:2} cols | {info['size']:>8}")
            total_rows += info['rows']
        else:
            print(f"{name:30} | ERROR: {info['error']}")
    
    print("=" * 50)
    print(f"{'Total records':30} | {total_rows:6,} rows")
    print()
    print("📖 Usage examples:")
    print("  from clifpy.data import load_demo_clif, load_demo_patient")
    print("  clif_demo = load_demo_clif()  # Load all tables")
    print("  patient_data = load_demo_patient()  # Load single table")
    print("  raw_df = load_demo_labs(return_raw=True)  # Get raw DataFrame")
