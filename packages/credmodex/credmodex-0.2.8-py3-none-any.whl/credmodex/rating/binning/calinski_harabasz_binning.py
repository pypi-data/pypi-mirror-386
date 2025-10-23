from optbinning import OptimalBinning
from typing import Literal

import pandas as pd
import numpy as np

import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="sklearn")

from . import BaseBinning


__all__ = [
    'CH_Binning'
]


class CH_Binning():
    def __init__(self,  min_n_bins:int=2, max_n_bins:int=15, 
                 dtype:Literal['numerical','categorical']='numerical',
                 transform_func:Literal['alphabet','sequence','normalize']='alphabet',):
        self.max_n_bins = max_n_bins
        self.min_n_bins = min_n_bins
        self.dtype = dtype
        self.transform_func = transform_func


    def fit(self, x:list, y:list, metric:str='bins'):
        self.ch_model_ = -1
        self.ch_model_dict_ = {}
        for i in range(self.min_n_bins, self.max_n_bins+1):
            model_ = OptimalBinning(dtype=self.dtype, solver="cp", min_n_bins=i, max_n_bins=i)
            model_.fit(x, y)
            fitted_ = model_.transform(x, metric=metric)

            if self.dtype in {'categorical'}:
                df = pd.DataFrame({'bin': fitted_, 'target': y})
                bins_map = df.groupby('bin')['target'].mean().to_dict()

                y_pred = [bins_map[b] for b in fitted_]
            else:
                y_pred = x 
                bins_map = {}

            new_ch_model_ = CH_Binning.calinski_harabasz(y_pred=y_pred, bins=fitted_)
            self.ch_model_dict_[i] = new_ch_model_
            
            if (new_ch_model_ > self.ch_model_) and (~np.isinf(new_ch_model_)):
                self.ch_model_ = new_ch_model_
                self.n_bins_ = i
                self.model = model_
                self.bins_map = bins_map
                
        try:
            self.model == 0
        except: 
            raise TypeError('No optimum binning was found in the range interval for X and Y.')

            self._copy_model_attributes()
            
        return self.model


    def fit_transform(self, x:list, y:list, metric:str='bins'):
        self.fit(x, y, metric)
        return self.transform(x, metric)


    def transform(self, x:list, metric:str='bins'):
        if (self.dtype == 'numerical'):
            return self.model.transform(x, metric=metric)
        
        if (self.dtype == 'categorical'):
            pred_ = self.model.transform(x, metric=metric)
            
            # Do NOT modify bins_map again — reuse the one from fit
            if (self.transform_func == 'alphabet'):
                return self._convert_categorical(bins=self.bins_map, list_=pred_)
            elif (self.transform_func == 'sequence'):
                return self._convert_categorical_to_numerical(bins=self.bins_map, list_=pred_)
            elif (self.transform_func == 'normalize'):
                return self._convert_categorical_to_normal(bins=self.bins_map, list_=pred_)
        
        raise TypeError('Unsupported dtype or transform_func')


    def _copy_model_attributes(self):
        for attr in dir(self.model):
            if not attr.startswith('_') and not callable(getattr(self.model, attr)):
                setattr(self, attr, getattr(self.model, attr))


    def _map_to_alphabet(self, lst):
        result = {num: chr(65 + index) for index, num in enumerate(lst)}
        self.df['rating'] = self.df['rating'].map(result).fillna('-')
        return result


    def _convert_categorical(self, bins:dict, list_:list):
        bins = dict(sorted(bins.items(), key=lambda item: item[1]))
        letter = 0
        for key in list(bins.keys()):
            if key == 'Missing':
                bins[key] = 'None'
            else:
                bins[key] = chr(65 + letter)
                letter += 1

        self.bins_map = bins
        return [bins.get(label, 0.0) for label in list_]


    def _convert_categorical_to_numerical(self, bins:dict, list_:list):
        bins = dict(sorted(bins.items(), key=lambda item: item[1]))
        weight = [round(1-(i/len(bins.keys())),6) for i in range(len(bins.keys()))]
        for key, value in zip(bins.keys(), weight):
            bins[key] = value

        self.bins_map = bins
        return [bins.get(label, 0.0) for label in list_]


    def _convert_categorical_to_normal(self, bins:dict, list_:list):
        bins = dict(sorted(bins.items(), key=lambda item: item[1]))
        values = list(bins.values())
        _min = min(values)
        _max = max(values)
        for key, value in bins.items():
            bins[key] = round(abs((value - _max) / (_min - _max)),6)

        self.bins_map = bins
        return [bins.get(label, 0.0) for label in list_]
    

    def __str__(self):
        try:
            if ('Missing' in self.bins_map.keys()):
                return f"<CH_Binning: {self.n_bins_+1} bins={self.bins_map}>"
            else:
                return f"<CH_Binning: {self.n_bins_} bins={self.bins_map}>"
        except:
                return f"<CH_Binning: not>"
            

    def __repr__(self):
        return self.__str__()




    @staticmethod
    def calinski_harabasz(y_pred:list, bins:list):
        """
        Compute the Calinski-Harabasz score to evaluate the separation between binned groups.

        This score measures how well predicted probabilities are clustered by a given binning scheme.
        It is commonly used in clustering and binning evaluations to assess group distinctiveness.

        Parameters
        ----------
        y_pred : list
            Predicted probabilities or scores (continuous values).
        bins : list
            Corresponding bin labels for each prediction (can be strings or numeric identifiers).

        Returns
        -------
        float
            Calinski-Harabasz score, rounded to 4 decimal places.
            Returns `np.inf` if the denominator is zero (suggesting perfect separation).
            Returns `0` if the result is not a number (`NaN`).

        Notes
        -----
        The score is calculated as:

            CH = (BSS / (g - 1)) / (WSS / (n - g))

        where:
        - BSS = between-group sum of squares
        - WSS = within-group sum of squares
        - g = number of bins
        - n = total number of observations

        A higher score indicates better separation between the groups.
        """
        df = {
            "y_pred": y_pred,
            "bins": bins
        }
        df = pd.DataFrame(df)
        
        overall_mean = df['y_pred'].mean()
        n = len(df)
        g = df['bins'].nunique()

        bss = (
            df.groupby('bins')['y_pred']
            .apply(lambda x: len(x) * (x.mean() - overall_mean) ** 2)
            .sum()
        )

        wss = (
            df.groupby('bins')['y_pred']
            .apply(lambda x: ((x - x.mean()) ** 2).sum())
            .sum()
        )

        if ((wss / (n - g)) == 0):
            return np.inf

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            ch = (bss / (g - 1)) / (wss / (n - g))

        if np.isnan(ch):
            return 0
        
        return float(round(ch,4))













# class CH_Binning(BaseBinning):
#     def __init__(self, min_n_bins:int=2, max_n_bins:int=15, n_bins:int=None,
#                  dtype:Literal['numerical','categorical']='numerical',
#                  transform_func:Literal['alphabet','sequence','normalize']='alphabet'):
#         super().__init__(min_n_bins=min_n_bins, max_n_bins=max_n_bins, n_bins=n_bins,
#                          dtype=dtype, transform_func=transform_func, solver='calinski-harabasz')


#     def _fit(self, x:list, y:list=None, n_bins:int=5):
#         self.optbin_model_ = OptimalBinning(dtype=self.dtype, solver="cp", 
#                                     min_n_bins=n_bins, max_n_bins=n_bins)
#         self.optbin_model_.fit(x, y)
#         return self


#     def _transform(self, x:list):
#         if (self.dtype == 'numerical'):
#             pred_ = self.optbin_model_.transform(x, metric='bins')
#             return pred_
#         if (self.dtype == 'categorical'):
#             pred_ = self.optbin_model_.transform(x, metric='bins')
#             if (self.transform_func == 'alphabet'):
#                 pred_ = self._convert_categorical(bins=self.bins_map, list_=pred_)
#             elif (self.transform_func == 'sequence'):
#                 pred_ = self._convert_categorical_to_numerical(bins=self.bins_map, list_=pred_)
#             elif (self.transform_func == 'normalize'):
#                 pred_ = self._convert_categorical_to_normal(bins=self.bins_map, list_=pred_)
#             return pred_
#         raise TypeError('No suport for this ``dtype``')


#     def _convert_categorical(self, bins:dict, list_:list):
#         bins = dict(sorted(bins.items(), key=lambda item: item[1]))
#         letter = 0
#         for key in list(bins.keys()):
#             if key == 'Missing':
#                 bins[key] = 'None'
#             else:
#                 bins[key] = chr(65 + letter)
#                 letter += 1

#         self.bins_map = bins
#         return [bins[label] for label in list_]


#     def _convert_categorical_to_numerical(self, bins:dict, list_:list):
#         bins = dict(sorted(bins.items(), key=lambda item: item[1]))
#         weight = [round(1-(i/len(bins.keys())),6) for i in range(len(bins.keys()))]
#         for key, value in zip(bins.keys(), weight):
#             bins[key] = value

#         self.bins_map = bins
#         return [bins[label] for label in list_]


#     def _convert_categorical_to_normal(self, bins:dict, list_:list):
#         bins = dict(sorted(bins.items(), key=lambda item: item[1]))
#         values = list(bins.values())
#         _min = min(values)
#         _max = max(values)
#         for key, value in bins.items():
#             bins[key] = round(abs((value - _max) / (_min - _max)),6)

#         self.bins_map = bins
#         return [bins[label] for label in list_]








# if __name__ == '__main__':
#     df = {
#         'Grade': [0]*(95+309) + [1]*(187+224) + [2]*(549+299) + [3]*(1409+495) + [4]*(3743+690) + [5]*(4390+424) + [6]*(2008+94) + [7]*(593+8),
#         'y_true': [0]*95+[1]*309 + [0]*187+[1]*224 + [0]*549+[1]*299 + [0]*1409+[1]*495 + [0]*3743+[1]*690 + [0]*4390+[1]*424 + [0]*2008+[1]*94 + [0]*593+[1]*8,
#         'y_pred': [309/(95+309)]*(95+309) + [224/(187+224)]*(187+224) + [299/(549+299)]*(549+299) + [495/(1409+495)]*(1409+495) + [690/(3743+690)]*(3743+690) + [424/(4390+424)]*(4390+424) + [94/(2008+94)]*(2008+94) + [8/(593+8)]*(593+8)
#     }
#     df = pd.DataFrame(df)

#     model = CH_Binning()
#     model.fit(df['y_pred'], df['y_true'])
#     print(model.transform(df['y_pred'],))