"""
Statistically compare fields along the time axis
"""
import numpy as np
import pandas as pd
from typing import Optional
from canopy.core.field import Field
from canopy.util.checks import check_field_contains_layers, check_indices_match


def compare_ts(field1: Field, field2: Field,
               layers1: Optional[list[str] | str] = None, layers2: Optional[list[str] | str] = None,
               tolerance: int | float = 1.e-6) -> pd.DataFrame:
    """Statistically compare two fields along the time axes

    NaN values in either of the series are ignored. The field indices must be equal.

    The comparison calculates the following metrics:
        - ME: Mean Error
        - MAE: Mean Absolute Error
        - MSE: Mean Squared Error
        - RMSE: Root Mean Squared Error
        - r: Correlation coefficient
        - R2: Coefficient of determination

    Parameters
    ----------
    field1 : Field
        One of the two fields to compare. In the case of observation vs. simulation, this field
        represents the OBSERVED DATA.
    field2 : Field
        One of the two fields to compare. In the case of observation vs. simulation, this field
        represents the MODELED DATA.
    layers1 : str | list[str]
        A string or list of strings to select the layers from field1 to be compared. If None, all
        of the field's layers are used.
    layers2 : str | list[str]
        A string or list of strings to select the layers from field2 to be compared. If None, all
        of the field's layers are used.
    tolerance : int | float
        Tolerance for comparison of the two gridlists

    Returns
    -------
    A pandas DataFrame with the metrics for each gridcell, and each pairs of layers

    Notes
    -----
    The layers are compared in the order that they are passed to the function, and their name has no
    effect on the comparison. For example, if layers1 = ['C3G', 'C4G'] and layers2 = ['C4G', 'C3G'],
    field1's 'C3G' layer will be compared to field2's 'C4G' layer, and viceversa.
    """

    if isinstance(layers1, str):
        layers1 = [layers1]
    if isinstance(layers2, str):
        layers2 = [layers2]

    # Check that indices match
    check_indices_match(field1, field2, tolerance = tolerance)

    if layers1 is None:
        layers1 = field1.data.columns
        df1 = field1.data.copy(deep=False)
    else:
        check_field_contains_layers(field1, layers1, 'field1')
        df1 = field1.data[layers1].copy(deep=False)
    if layers2 is None:
        layers2 = field2.data.columns
        df2 = field2.data.copy(deep=False)
    else:
        check_field_contains_layers(field2, layers2, 'field2')
        df2 = field2.data[layers2].copy(deep=False)

    # Check layer lists have the same length
    if len(layers1) != len(layers2):
        raise ValueError("'layers1' and 'layers2' must have equal lenght.")

    # Since it's already checked that indices match to a certain tolerance, make df2.index
    #   equal to df1.index so that groupby operations work as intended
    index2 = df2.index
    df2.index = df1.index

    layer_comp = [f'{x} v {y}' for x, y in zip(layers1, layers2)]
    coordinate_indices = df1.index.names[:2]

    # Residuals
    e = df1 - df2

    # Residual squares
    e2 = e**2

    # Count
    count = e.groupby(coordinate_indices).count()
    count.columns = [layer_comp, ['n']*len(layer_comp)]

    # Mean error
    me = e.groupby(coordinate_indices).mean()
    me.columns = [layer_comp, ['ME']*len(layer_comp)]

    # Mean absolute error
    mae = e.abs().groupby(coordinate_indices).mean()
    mae.columns = [layer_comp, ['MAE']*len(layer_comp)]

    # Mean squared error
    mse = e2.groupby(coordinate_indices).mean()
    mse.columns = [layer_comp, ['MSE']*len(layer_comp)]

    # Root mean squared error
    rmse = np.sqrt(mse)
    rmse.columns = [layer_comp, ['RMSE']*len(layer_comp)]

    # Correlation coefficient
    corr = df1.unstack(coordinate_indices).corrwith(df2.unstack(coordinate_indices)).unstack(0)
    corr.columns = [layer_comp, ['r']*len(layer_comp)]

    # Coefficient of determination
    #   Let y_1, y_2, y_3, ... be a series of observations, and f_1, f_2, f_3, ... the corresponding
    #   modeled quantities. The coefficient of determination, R^2, is defined as
    #   R^2 = 1 - ss_{res}/ss_{tot},
    #   where
    #     ss_res = \sum_i {(y_i - f_i)^2} = \sum e^2
    #   is the sum of squared residuals, and
    #     ss_tot = \sum_i {(y_i - \bar{y})^2}
    #   is the total sum of squares (\bar{y} is the mean of the y_i).
    #   See https://en.wikipedia.org/wiki/Coefficient_of_determination
    ss_tot = ((df1 - df1.groupby(coordinate_indices).mean())**2).groupby(coordinate_indices).sum()
    ss_res = e2.groupby(coordinate_indices).sum()
    r2 = 1. - ss_res/ss_tot
    r2 = r2.replace([np.inf, -np.inf], np.nan)
    r2.columns = [layer_comp, ['R2']*len(layer_comp)]

    stats = pd.concat([count, me, mae, mse, rmse, corr, r2], axis=1)
    stats.columns.names = ['layer', 'stats']
    stats = stats.sort_values(axis=1, by='layer', kind='mergesort')

    return stats
