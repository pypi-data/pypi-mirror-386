import sys
import os
import pandas as pd
import numpy as np

from functools import partial
import warnings

from typing import Union, Callable, Dict, Tuple, List, Literal

sys.path.append(os.path.abspath('.'))
from credmodex.rating import CH_Binning
from credmodex.config import *


__all__ = [
    'TreatentFunc'
]


def _normalize_dtype(dtype):
    if pd.api.types.is_string_dtype(dtype):
        return 'string'
    elif pd.api.types.is_numeric_dtype(dtype):
        return 'numeric'
    elif pd.api.types.is_datetime64_any_dtype(dtype):
        return 'datetime'
    elif pd.api.types.is_bool_dtype(dtype):
        return 'bool'
    else:
        return str(dtype)


def _check_dtype_mismatches(df_expected: pd.DataFrame, df_actual: pd.DataFrame, columns: list, suppress_warnings: bool = False, context: str = "transform"):
    expected_dtypes = df_expected[columns].dtypes.to_dict()
    actual_dtypes = df_actual.dtypes.to_dict()

    mismatches = {
        col: (expected_dtypes[col], actual_dtypes.get(col))
        for col in columns
        if col in actual_dtypes and _normalize_dtype(expected_dtypes[col]) != _normalize_dtype(actual_dtypes[col])
    }

    if mismatches and not suppress_warnings:
        warnings.warn(
            f"[{context}] Column type mismatches found: {mismatches}",
            category=UserWarning
        )


def _ensure_columns_exist(df: pd.DataFrame, expected_columns: list, suppress_warnings: bool = False, context: str = "transform"):
    missing = [col for col in expected_columns if col not in df.columns]
    for col in missing:
        df[col] = pd.NA
        if not suppress_warnings:
            warnings.warn(
                f"Column '{col}' is missing in DataFrame during `{context}` and was added with NaN values.",
                category=UserWarning
            )
    return df


def _check_cols(df: pd.DataFrame = None, cols: tuple = None):
    if df is None:
        raise ValueError("You must pass a valid DataFrame.")
    if cols is None:
        raise ValueError("You must specify a column or list of columns.")
    if not isinstance(cols, tuple):
        cols = tuple([cols] if isinstance(cols, str) else cols)
    for c in cols:
        if c not in df.columns:
            raise ValueError(f"Column '{c}' not found in the DataFrame. Available columns: {df.columns.tolist()}")
    return cols


def _check_str_cols(df:pd.DataFrame=None, cols:tuple=None):
    cols = _check_cols(df, cols)
    cols = tuple([c for c in cols 
                  if (c in df.select_dtypes(exclude=["number", "datetime"]).columns.tolist()) 
                  and (c not in TreatmentFunc().forbidden_cols)])
    return cols


def _check_float_cols(df:pd.DataFrame=None, cols:tuple=None):
    cols = _check_cols(df, cols)
    cols = tuple([c for c in cols 
                 if (c in df.select_dtypes(include=["number"]).columns.tolist()) 
                 and (c not in TreatmentFunc().forbidden_cols)])
    return cols


def _check_datetime_cols(df:pd.DataFrame=None, cols:tuple=None):
    cols = _check_cols(df, cols)
    cols = tuple([c for c in cols 
                  if (c in df.select_dtypes(include=["datetime"]).columns.tolist()) 
                  and (c not in TreatmentFunc().forbidden_cols)])
    return cols


def min_max_dict_normalize(data_dict:dict):
    values = list(data_dict.values())
    min_val = min(values)
    max_val = max(values)
    
    # Avoid division by zero if all values are the same
    if min_val == max_val:
        return {k: 0.0 for k in data_dict}
    
    normalized_dict = {
        k: (v - min_val) / (max_val - min_val)
        for k, v in data_dict.items()
    }
    
    return normalized_dict


class TreatmentFunc:
    def __init__(self, df:pd.DataFrame=pd.DataFrame(), target:str=None, features:list[str]=None,
                 split: Union[str, List[str]] = None,
                 key_columns:list[str]=[], include_features:bool=True, suppress_warnings:bool=False):
        self.raw_df = df.copy(deep=True)
        self.df = df.copy(deep=True)

        if split is not None:
            if isinstance(split, str):
                split = [split]
            self.raw_df = self.raw_df[self.raw_df['split'].isin(split)]
            self.df = self.df[self.df['split'].isin(split)]

        if target is None:
            target = DEFAULT_FORBIDDEN_COLS['target']
        self.target = target
        
        self.time_col = DEFAULT_FORBIDDEN_COLS['date']
        self.features = features
        self.include_features = include_features
        self.key_columns = key_columns
        self.forbidden_cols = get_forbidden_cols(additional_cols=key_columns)
        self.pipeline = {}
        self.suppress_warnings = suppress_warnings

        self.methods = {
            'fillna': self.fillna,
            'fillna_all': self.fillna_all,
            'exclude_columns': self.exclude_columns,
            'include_columns': self.include_columns,
            # 'dummy_bin_str': self.dummy_bin_str,
            'sequential_bin_str': self.sequential_bin_str,
            'normalize_bin_str': self.normalize_bin_str,
            'normalize_float': self.normalize_float,
            'exclude_str_columns': self.exclude_str_columns,
            'exclude_nan_rows': self.exclude_nan_rows,
            'datetime_parser': self.datetime_parser,
            'auto': self.auto,
        }

        self.forbidden_cols = [col for col in self.forbidden_cols if col in self.df.columns]
        if self.features is not None and self.include_features:
            self.combined_cols = list(dict.fromkeys(self.features + self.forbidden_cols))
            self.raw_df = self.raw_df.loc[:, self.combined_cols]
            self.df = self.df.loc[:, self.combined_cols]


    def fit(self, strategy):
        df = self.raw_df.copy(deep=True)  # Use this as a working df to carry forward changes
        self.raw_df_columns_ = list(dict.fromkeys(df.columns.tolist() + self.forbidden_cols))
        self.strategy = strategy

        for cols, funcs in strategy.items():
            if isinstance(cols, str):
                cols = (cols,)
            if not isinstance(funcs, (list, tuple)):
                funcs = [funcs]
            
            for col in cols:
                for func in funcs:
                    if isinstance(func, str):
                        if func not in self.methods:
                            raise ValueError(f"Method '{func}' not found in available methods: {list(self.methods.keys())}")
                        method = self.methods[func]
                        method_func = method()
                    else:
                        method_func = func

                    fitted_info = method_func(df=df, cols=col, target=self.target, fit=True)
                    self.pipeline.setdefault(col, []).append((method_func, fitted_info))
                    df = method_func(df=df, cols=col, target=self.target, fit=False, fitted_info=fitted_info)
            
        self.df = self.transform(self.raw_df)
        self.df_columns_ = self.df.columns.tolist()
        self.features = [col for col in self.df_columns_ if col not in self.forbidden_cols]


    def transform(self, df: pd.DataFrame = None):
        if df is None:
            df = self.raw_df.copy(deep=True)
        else:
            df = df.copy(deep=True)

        if hasattr(self, "raw_df_columns_"):
            df = _ensure_columns_exist(df, self.raw_df_columns_, self.suppress_warnings, context="raw_df_columns_")

            if self.include_features:
                df = df[self.raw_df_columns_]

            _check_dtype_mismatches(self.raw_df, df, self.raw_df_columns_, self.suppress_warnings, context="raw_df_columns_")

        # Apply transformations
        for col, steps in self.pipeline.items():
            for method_func, fitted_info in steps:
                df = method_func(df=df, cols=col, target=self.target, fit=False, fitted_info=fitted_info)

        if hasattr(self, "df_columns_"):
            df = _ensure_columns_exist(df, self.df_columns_, self.suppress_warnings, context="df_columns_")

            new_columns = [col for col in df.columns if col not in self.df_columns_]
            for col in new_columns:
                if not self.suppress_warnings:
                    warnings.warn(
                        f"Column {col} is new and was not present in fit(). Be cautious.",
                        category=UserWarning
                    )

            df = df[self.df_columns_]
            _check_dtype_mismatches(self.df, df, self.df_columns_, self.suppress_warnings, context="df_columns_")

        return df


    def fillna(self, value=0):
        def _fillna(df, cols, target, fit=True, fitted_info=None):
            cols = _check_cols(df, cols)
            if fit:
                return value
            else:
                for col in cols:
                    df[col] = df[col].fillna(fitted_info)
                return df
        _fillna.__method_name__ = 'fillna'
        return _fillna


    def fillna_all(self, value: Union[float, Literal['mode', 'mean']] = 'mode'):
        """
        Fill NA for *all* non-forbidden columns using either 'mode', 'mean', or a scalar fallback.
        Guarantees that fitted_info has no None values (so transform never calls fillna(None)).
        """
        def _fillna(df, cols, target=None, fit=True, fitted_info=None):
            if fit:
                fill_values = {}
                # iterate only over columns we are allowed to touch
                for col in [c for c in df.columns.to_list() if c not in self.forbidden_cols]:
                    col_dtype = df[col].dtype

                    # helper: choose a safe default if needed
                    def _fallback_for_dtype():
                        # numeric
                        if pd.api.types.is_numeric_dtype(col_dtype):
                            return 0
                        # boolean
                        if pd.api.types.is_bool_dtype(col_dtype):
                            return False
                        # datetime
                        if pd.api.types.is_datetime64_any_dtype(col_dtype):
                            # keep NaNs if we can't infer (fill with the column's min not ideal)
                            # Use the most common timestamp if available, else leave NaNs (handled by skipping later)
                            mode_ts = df[col].mode()
                            return mode_ts.iloc[0] if not mode_ts.empty else pd.NaT
                        # strings/objects
                        return ""  # empty string

                    if value == 'mode':
                        mode_series = df[col].mode(dropna=True)
                        fill_val = mode_series.iloc[0] if not mode_series.empty else _fallback_for_dtype()

                    elif value == 'mean':
                        if pd.api.types.is_numeric_dtype(col_dtype):
                            mean_val = df[col].mean(skipna=True)
                            # mean() returns scalar; may be NaN if all-NaN
                            if pd.isna(mean_val):
                                fill_val = _fallback_for_dtype()
                            else:
                                fill_val = mean_val
                        else:
                            # for non-numerics, fall back to mode
                            mode_series = df[col].mode(dropna=True)
                            fill_val = mode_series.iloc[0] if not mode_series.empty else _fallback_for_dtype()
                    else:
                        # user provided a scalar default
                        fill_val = value

                    # Ensure we never store None (pd.NaT is fine; we will skip filling datetimes with NaT)
                    if fill_val is None:
                        fill_val = _fallback_for_dtype()

                    fill_values[col] = fill_val

                return fill_values

            else:
                # apply learned fill values safely
                for col, fill_val in fitted_info.items():
                    # If datetime and fill_val is NaT, skip (fillna with NaT is a no-op and can error in some versions)
                    if pd.api.types.is_datetime64_any_dtype(df[col].dtype) and pd.isna(fill_val):
                        continue
                    df[col] = df[col].fillna(fill_val)
                return df

        _fillna.__method_name__ = 'fillna'
        return _fillna


    def exclude_columns(self):
        def _exclude_columns(df, cols, target, fit=True, fitted_info=None):
            cols_checked = _check_cols(df, cols)
            if fit:
                return True
            else:
                for col in cols_checked:
                    if (col in df.columns) and (col not in self.forbidden_cols):
                        del df[col]
                return df
        _exclude_columns.__method_name__ = 'exclude_columns'
        return _exclude_columns


    def include_columns(self):
        def _include_columns(df, cols, target, fit=True, fitted_info=None):
            cols_checked = _check_cols(df, cols)
            if fit:
                return True
            else:
                df = df.loc[:, df.columns.isin(list(cols_checked) + TreatmentFunc().forbidden_cols)]
                return df
        _include_columns.__method_name__ = 'include_columns'
        return _include_columns


    # def dummy_bin_str(self, min_n_bins=2, max_n_bins=10):
        def _dummy_bin_str(df, cols, target, fit=True, fitted_info=None):
            df = df.copy(deep=True)
            cols_checked = _check_str_cols(df, cols)

            if fit:
                bins = CH_Binning(
                    min_n_bins=min_n_bins, max_n_bins=max_n_bins,
                    dtype='categorical'
                )
                df[cols_checked[0]] = bins.fit(x=df[cols_checked[0]], y=df[target])
                return bins.bins_map
            else:
                ...

                return df
        _dummy_bin_str.__method_name__ = 'dummy_bin_str'
        return _dummy_bin_str


    def sequential_bin_str(self, min_n_bins=2, max_n_bins=10):
        def _sequential_bin_str(df, cols, target, fit=True, fitted_info=None):
            df = df.copy(deep=True)
            cols_checked = _check_str_cols(df, cols)

            if fit:
                binning = CH_Binning(
                    min_n_bins=min_n_bins, max_n_bins=max_n_bins,
                    dtype='categorical', transform_func='sequence'
                )
                df[cols_checked[0]] = binning.fit(x=df[cols_checked[0]], y=df[target])
                return binning
            else:
                for col in cols_checked:
                    df[col] = fitted_info.transform(df[col])
                return df
        _sequential_bin_str.__method_name__ = 'sequential_bin_str'
        return _sequential_bin_str


    def normalize_bin_str(self, min_n_bins=2, max_n_bins=10):
        def _normalize_bin_str(df, cols, target, fit=True, fitted_info=None):
            df = df.copy(deep=True)
            cols_checked = _check_str_cols(df, cols)

            if fit:
                binning = CH_Binning(
                    min_n_bins=min_n_bins, max_n_bins=max_n_bins,
                    dtype='categorical', transform_func='normalize'
                )
                df[cols_checked[0]] = binning.fit(x=df[cols_checked[0]], y=df[target])
                return binning
            else:
                for col in cols_checked:
                    df[col] = fitted_info.transform(df[col])
                return df
        _normalize_bin_str.__method_name__ = 'normalize_bin_str'
        return _normalize_bin_str


    def normalize_float(self, min_value=None, max_value=None, clip=True):
        """
        Min–max normalize numeric columns to [0, 1].

        - If `min_value`/`max_value` are provided (scalars), they override the fitted min/max.
        - Guards against zero/NaN ranges (constant or all-NaN columns) by returning 0.0.
        - Keeps output as float; optionally clips to [0, 1].
        """
        def _normalize_float(df, cols, target, fit=True, fitted_info=None):
            cols_checked = _check_float_cols(df, cols)

            if fit:
                col = cols_checked[0]  # this method is applied per-column by the pipeline
                col_min = df[col].min(skipna=True)
                col_max = df[col].max(skipna=True)

                # allow user-provided global bounds
                if min_value is not None:
                    col_min = float(min_value)
                if max_value is not None:
                    col_max = float(max_value)

                return {
                    'min': float(col_min) if pd.notna(col_min) else 0.0,
                    'max': float(col_max) if pd.notna(col_max) else 0.0,
                    'clip': bool(clip),
                }

            else:
                for col in cols_checked:
                    # coerce to float (Series is already numeric per _check_float_cols, but be safe)
                    s = pd.to_numeric(df[col], errors='coerce').astype('float64')

                    vmin = fitted_info['min']
                    vmax = fitted_info['max']
                    rng = vmax - vmin

                    # safe normalization
                    if not np.isfinite(rng) or rng == 0:
                        # constant/all-NaN -> just set to 0.0
                        s = s.where(s.notna(), 0.0)  # keep existing non-NaNs as NaN prior to fill
                        s = 0.0
                    else:
                        s = (s - vmin) / rng

                    if fitted_info['clip']:
                        s = s.clip(lower=0.0, upper=1.0)

                    df[col] = s

                return df

        _normalize_float.__method_name__ = 'normalize_float'
        return _normalize_float


    def exclude_str_columns(self):
        def _exclude_str_columns(df, cols, target, fit=True, fitted_info=None):
            if fit:
                return True
            else:
                for col in df.columns.tolist():
                    if (col in df.select_dtypes(include=['object', 'string']).columns.tolist()) and (col not in self.forbidden_cols):
                        del df[col]
                return df
        _exclude_str_columns.__method_name__ = 'exclude_str_columns'
        return _exclude_str_columns


    def exclude_nan_rows(self,):
        def _exclude_nan_rows(df, cols, target, fit=True, fitted_info=None):
            cols_checked = _check_cols(df, cols)
            if fit:
                return True
            else:
                df = df.dropna(subset=cols)
                return df
        _exclude_nan_rows.__method_name__ = 'exclude_nan_rows'
        return _exclude_nan_rows


    def datetime_parser(self, strftime=r'%Y-%m-%d'):
        def _datetime_parser(df, cols, target, fit=True, fitted_info=None):
            cols_checked = _check_datetime_cols(df, cols)
            if fit:
                return {'strftime': strftime}
            else:
                for col in cols_checked:
                    df[col] = df[col].dt.strftime(fitted_info['strftime'])
                return df
        _datetime_parser.__method_name__ = 'datetime_parser'
        return _datetime_parser


    def auto(self):
        def _auto(df, cols, target, fit=True, fitted_info=None):
            return None
        _auto.__method_name__ = 'auto'
        return _auto

    @property
    def pipeline_summary(self):
        summary = {}
        for col, steps in self.pipeline.items():
            summary[col] = []
            for func, fitted_info in steps:
                # Try to get a readable name
                if hasattr(func, '__method_name__'):
                    name = func.__method_name__
                elif hasattr(func, '__name__'):
                    name = func.__name__
                elif hasattr(func, '__class__'):
                    name = func.__class__.__name__
                else:
                    name = str(func)
                summary[col].append((name, fitted_info))
        return summary
