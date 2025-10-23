import logging
import pandas as pd
import urllib.request
from typing import Optional
from demandforge import RESULTS_DIR

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def _get_combined_load_data(country: str, year: int) -> pd.DataFrame:
    """Retrieves the combined load data for a given country and year.

    Downloads the data from a remote URL if it's not available locally.

    Args:
        country (str): The country code (e.g., 'DE').
        year (int): The reference year.

    Returns:
        pd.DataFrame: A pandas DataFrame with the combined load data.
    """
    file_name = f"combined_load_{country}_{year}.parquet"
    data_dir = RESULTS_DIR / "combined_load"
    data_dir.mkdir(parents=True, exist_ok=True)
    file_path = data_dir / file_name

    if not file_path.is_file():
        logging.info(f"'{file_path}' not found. Downloading from remote URL...")
        url = f"https://storage.googleapis.com/demandforge/{file_name}"
        try:
            urllib.request.urlretrieve(url, file_path)
            logging.info(f"Successfully downloaded '{file_path}'.")
        except urllib.error.URLError as e:
            logging.error(f"Failed to download {url}. Error: {e}")
            raise

    return pd.read_parquet(file_path)

def _calculate_total_energy_from_growth_rate(initial_energy: float, growth_rate: float, reference_year: int, target_year: int) -> float:
    """Calculates the total energy for a target year based on a growth rate."""
    return initial_energy * (1 + growth_rate) ** (target_year - reference_year)

def project_load_curve(
    reference_year: int,
    country: str,
    target_year: int,
    reference_ev_year: int = 2026,
    total_baseload_energy_target: Optional[float] = None,
    total_winter_thermosensitive_energy_target: Optional[float] = None,
    total_summer_thermosensitive_energy_target: Optional[float] = None,
    total_ev_energy_target: Optional[float] = None,
    baseload_yearly_growth_rate: Optional[float] = None,
    winter_thermosensitive_yearly_growth_rate: Optional[float] = None,
    summer_thermosensitive_yearly_growth_rate: Optional[float] = None,
    ev_yearly_growth_rate: Optional[float] = None
) -> pd.DataFrame:
    """Projects future country-level load curves based on a reference year and scaling factors.

    Args:
        reference_year (int): The year of the reference load curve data.
        country (str): The country for which to project the load.
        target_year (int): The year for which to project the load curve.
        reference_ev_year (int): The specific year to use for the reference EV load profile.
        total_baseload_energy_target (Optional[float]): Total baseload energy for the target year.
        total_winter_thermosensitive_energy_target (Optional[float]): Total winter thermosensitive energy for the target year.
        total_summer_thermosensitive_energy_target (Optional[float]): Total summer thermosensitive energy for the target year.
        total_ev_energy_target (Optional[float]): Total electric vehicle energy for the target year.
        baseload_yearly_growth_rate (Optional[float]): Yearly growth rate for the baseload.
        winter_thermosensitive_yearly_growth_rate (Optional[float]): Yearly growth rate for winter thermosensitive load.
        summer_thermosensitive_yearly_growth_rate (Optional[float]): Yearly growth rate for summer thermosensitive load.
        ev_yearly_growth_rate (Optional[float]): Yearly growth rate for electric vehicle load.

    Returns:
        pd.DataFrame: A pandas DataFrame with the projected total load curve.
    """
    df = _get_combined_load_data(country, reference_year)

    ev_col = f'ev_load_{reference_ev_year}'
    if ev_col not in df.columns:
        raise ValueError(f"EV load column '{ev_col}' not found in the data.")
    df['ev_load'] = df[ev_col]

    # Rename columns for easier processing
    df_processed = df[['baseload', 'winter_thermosensitive_load', 'summer_thermosensitive_load', 'ev_load']].copy()
    df_processed.columns = ['baseload', 'winter_thermosensitive', 'summer_thermosensitive', 'ev']

    targets = {}
    categories_info = {
        'baseload': {
            'col_name': 'baseload',
            'target_arg': total_baseload_energy_target,
            'growth_rate_arg': baseload_yearly_growth_rate
        },
        'winter_thermosensitive': {
            'col_name': 'winter_thermosensitive',
            'target_arg': total_winter_thermosensitive_energy_target,
            'growth_rate_arg': winter_thermosensitive_yearly_growth_rate
        },
        'summer_thermosensitive': {
            'col_name': 'summer_thermosensitive',
            'target_arg': total_summer_thermosensitive_energy_target,
            'growth_rate_arg': summer_thermosensitive_yearly_growth_rate
        },
        'ev': {
            'col_name': 'ev',
            'target_arg': total_ev_energy_target,
            'growth_rate_arg': ev_yearly_growth_rate
        }
    }

    for category, info in categories_info.items():
        target_val = info['target_arg']
        growth_rate_val = info['growth_rate_arg']
        col_name = info['col_name']

        if target_val is not None:
            targets[category] = target_val
            logging.debug(f"Using target energy for {category}: {target_val}")
        elif growth_rate_val is not None:
            initial_energy = df_processed[col_name].sum()
            calculated_target = _calculate_total_energy_from_growth_rate(
                initial_energy, growth_rate_val, reference_year, target_year
            )
            targets[category] = calculated_target
            logging.debug(f"Using growth rate for {category}. Initial energy: {initial_energy}, Growth rate: {growth_rate_val}, Calculated target: {calculated_target}")
        else:
            raise ValueError(f"Neither total energy target nor yearly growth rate provided for {category}.")

    df_proj = df_processed.copy()

    for category, target_energy in targets.items():
        reference_energy = df_proj[category].sum()
        if reference_energy == 0:
            logging.warning(f"Reference energy for '{category}' is zero. Cannot scale. Setting projected load to 0.")
            df_proj[f'{category}_projected'] = 0
            continue
        scaling_factor = target_energy / reference_energy
        df_proj[f'{category}_projected'] = df_proj[category] * scaling_factor
        logging.debug(f"Scaled {category} with factor {scaling_factor}. Reference energy: {reference_energy}, Target energy: {target_energy}")

    df_proj['total_load_projected'] = df_proj[[
        'baseload_projected',
        'winter_thermosensitive_projected',
        'summer_thermosensitive_projected',
        'ev_projected'
    ]].sum(axis=1)

    return df_proj
