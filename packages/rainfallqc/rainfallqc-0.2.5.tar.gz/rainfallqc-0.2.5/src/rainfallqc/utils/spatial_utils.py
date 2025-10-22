# -*- coding: utf-8 -*-
"""
All spatial operations.

Classes and functions ordered alphabetically.
"""

import numpy as np
import xarray as xr

EARTH_RADIUS_KM = 6371.0  # Radius of the Earth in kilometers


def compute_spatial_mean_xr(data: xr.Dataset, var_name: str) -> xr.Dataset:
    """
    Get the value at the nearest ETCCDI grid cell to the gauge coordinates.

    Parameters
    ----------
    data
        Data with variable to compute mean from. Should have lat/lon and time (as axis 0)
    var_name :
        Variable to make mean value of

    Returns
    -------
    data :
        Data with spatial mean

    """
    # 1. Transpose so time is at 0-th index
    data = data.transpose("time", ...)

    # 2. Mask invalid data
    data_masked = np.ma.masked_invalid(data[var_name])

    # 3. Compute lat/lon mean
    data[f"{var_name}_mean"] = (
        ("lat", "lon"),
        np.ma.mean(data_masked, axis=0),
    )  # axis 0 is time
    return data


def haversine(lon1: xr.DataArray, lat1: xr.DataArray, lon2: np.ndarray | float, lat2: np.ndarray | float) -> float:
    """
    Great circle distance (km) between two points on Earth.

    Parameters
    ----------
    lon1 : xr.DataArray
        Longitude of point 1
    lat1 : xr.DataArray
        Latitude of point 1
    lon2 : np.ndarray | float
        Longitude of point 2
    lat2 : np.ndarray | float
        Latitude of point 2

    Returns
    -------
    distance : float
        Distance between the two points in km

    """
    # convert lat2 and lon2 to numpy arrays for safety
    lon2 = np.asarray(lon2, dtype=np.float64)
    lat2 = np.asarray(lat2, dtype=np.float64)

    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    return EARTH_RADIUS_KM * c
