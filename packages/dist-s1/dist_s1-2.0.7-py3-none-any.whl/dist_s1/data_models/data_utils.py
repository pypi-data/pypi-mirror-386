from datetime import datetime
from pathlib import Path, PosixPath

import pandas as pd
import yaml
from distmetrics.model_load import get_model_context_length
from yaml import Dumper

from dist_s1.data_models.defaults import DEFAULT_MODEL_CONTEXT_LENGTH_MAXIMUM, DEFAULT_N_CONFIRMATION_OBSERVATIONS


def posix_path_encoder(dumper: Dumper, data: PosixPath) -> yaml.Node:
    return dumper.represent_scalar('tag:yaml.org,2002:str', str(data))


def none_encoder(dumper: Dumper, _: None) -> yaml.Node:
    return dumper.represent_scalar('tag:yaml.org,2002:null', '')


yaml.add_representer(PosixPath, posix_path_encoder)
yaml.add_representer(type(None), none_encoder)


def get_opera_id(opera_rtc_s1_tif_path: Path | str) -> str:
    stem = Path(opera_rtc_s1_tif_path).stem
    tokens = stem.split('_')
    opera_id = '_'.join(tokens[:-1])
    return opera_id


def get_burst_id(opera_rtc_s1_path: Path | str) -> str:
    opera_rtc_s1_path = Path(opera_rtc_s1_path)
    tokens = opera_rtc_s1_path.name.split('_')
    return tokens[3]


def get_sensor(opera_rtc_s1_path: Path | str) -> str:
    opera_rtc_s1_path = Path(opera_rtc_s1_path)
    tokens = opera_rtc_s1_path.name.split('_')
    return tokens[6]


def get_track_number(opera_rtc_s1_path: Path | str) -> str:
    burst_id = get_burst_id(opera_rtc_s1_path)
    track_number_str = burst_id.split('-')[0]
    track_number = int(track_number_str[1:])
    return track_number


def get_opera_id_without_proccessing_time(opera_rtc_s1_path: Path | str) -> str:
    if opera_rtc_s1_path is None:
        return None
    opera_rtc_s1_path = Path(opera_rtc_s1_path)
    tokens = opera_rtc_s1_path.name.split('_')
    return '_'.join(tokens[:5])


def compare_dist_s1_product_tag(src_key: str, src_val: str | None, other_tag_value: str | None) -> bool:
    if src_key in ['prior_dist_s1_product']:
        if (src_val is None) and (other_tag_value is None):
            return True
        elif src_val is None:
            return False
        else:
            return get_opera_id_without_proccessing_time(src_val) == get_opera_id_without_proccessing_time(
                other_tag_value
            )
    if src_key in ['pre_rtc_opera_ids', 'post_rtc_opera_ids']:
        ids = sorted(src_val.split(','))
        other_ids = sorted(other_tag_value.split(','))
        ids = list(map(get_opera_id_without_proccessing_time, ids))
        other_ids = list(map(get_opera_id_without_proccessing_time, other_ids))
        return ids == other_ids
    return src_val == other_tag_value


def get_acquisition_datetime(opera_rtc_s1_path: Path | str) -> datetime:
    opera_rtc_s1_path = Path(opera_rtc_s1_path)
    tokens = opera_rtc_s1_path.name.split('_')
    try:
        return pd.Timestamp(tokens[4], tz='UTC')
    except ValueError:
        raise ValueError(f"Datetime token in filename '{opera_rtc_s1_path.name}' is not correctly formatted.")


def check_filename_format(filename: str, polarization: str) -> None:
    if polarization not in ['crosspol', 'copol']:
        raise ValueError(f"Polarization '{polarization}' is not valid; must be in ['crosspol', 'copol']")

    tokens = filename.split('_')
    if len(tokens) != 10:
        raise ValueError(f"File '{filename}' does not have 10 tokens")
    if tokens[0] != 'OPERA':
        raise ValueError(f"File '{filename}' first token is not 'OPERA'")
    if tokens[1] != 'L2':
        raise ValueError(f"File '{filename}' second token is not 'L2'")
    if tokens[2] != 'RTC-S1':
        raise ValueError(f"File '{filename}' third token is not 'RTC-S1'")
    if polarization == 'copol' and not (filename.endswith('_VV.tif') or filename.endswith('_HH.tif')):
        raise ValueError(f"File '{filename}' should end with '_VV.tif' or '_HH.tif' because it is copolarization")
    elif polarization == 'crosspol' and not (filename.endswith('_VH.tif') or filename.endswith('_HV.tif')):
        raise ValueError(f"File '{filename}' should end with '_VH.tif' or '_HV.tif' because it is crosspolarization")
    return True


def get_max_pre_imgs_per_burst_mw(model_context_length: int, max_anniversaries: int) -> tuple[int, int]:
    """Calculate max pre-images per burst for multi-window strategy.

    Parameters
    ----------
    model_context_length : int
        Maximum number of pre-images to use for baseline estimates
    max_anniversaries : int
        Number of anniversaries to use for multi-window

    Returns
    -------
    tuple[int, int]
        Max pre-images per burst for each window
    """
    max_pre_imgs_per_burst_mw = (model_context_length // max_anniversaries,) * max_anniversaries
    max_pre_imgs_per_burst_mw = max_pre_imgs_per_burst_mw[:-1] + (
        max_pre_imgs_per_burst_mw[-1] + model_context_length % max_anniversaries,
    )
    return max_pre_imgs_per_burst_mw


def check_dist_product_filename_format(filename: str) -> None:
    valid_suffixes = (
        'GEN-DIST-STATUS.tif',
        'GEN-METRIC-MAX.tif',
        'GEN-DIST-CONF.tif',
        'GEN-DIST-DATE.tif',
        'GEN-DIST-COUNT.tif',
        'GEN-DIST-PERC.tif',
        'GEN-DIST-DUR.tif',
        'GEN-DIST-LAST-DATE.tif',
        'GEN-DIST-STATUS.tif',
    )

    tokens = filename.split('_')
    if len(tokens) != 10:
        raise ValueError(f"File '{filename}' does not have 10 tokens")
    if tokens[0] != 'OPERA':
        raise ValueError(f"File '{filename}' first token is not 'OPERA'")
    if tokens[1] != 'L3':
        raise ValueError(f"File '{filename}' second token is not 'L3'")
    if tokens[2] != 'DIST-ALERT-S1':
        raise ValueError(f"File '{filename}' third token is not 'DIST-ALERT-S1'")
    if not any(filename.endswith(suffix) for suffix in valid_suffixes):
        raise ValueError(f"Filename '{filename}' must be a valid DIST-ALERT-S1 product: {valid_suffixes}")
    return True


def extract_rtc_metadata_from_path(path: str | Path) -> dict:
    file_path = Path(path)
    stem = file_path.stem
    return {
        'opera_id': '_'.join(stem.split('_')[:-1]),
        'polarization': stem.split('_')[-1],
        'path': str(path),
        'jpl_burst_id': get_burst_id(stem),
        'acq_dt': get_acquisition_datetime(stem),
    }


def get_polarization_from_row(row: pd.Series) -> str:
    loc_path_copol = row.loc_path_copol
    loc_path_crosspol = row.loc_path_crosspol
    copol = Path(loc_path_copol).stem.split('_')[-1]
    crosspol = Path(loc_path_crosspol).stem.split('_')[-1]
    return f'{copol}+{crosspol}'


def get_max_context_length_from_model_source(model_source: str, model_cfg_path: str | Path | None = None) -> int:
    return min(get_model_context_length(model_source, model_cfg_path), DEFAULT_MODEL_CONTEXT_LENGTH_MAXIMUM)


def get_confirmation_confidence_threshold(
    alert_low_conf_thresh: float, n_confirmation_obs: int = DEFAULT_N_CONFIRMATION_OBSERVATIONS
) -> float:
    return (n_confirmation_obs**2) * alert_low_conf_thresh
