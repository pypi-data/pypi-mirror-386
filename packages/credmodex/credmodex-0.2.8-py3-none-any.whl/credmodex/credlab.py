import sys
import os
import warnings
from typing import Union, Literal

from pprint import pprint, pformat
import pandas as pd
import numpy as np
import sklearn

import plotly.graph_objects as go
from scipy.stats import chi2_contingency

sys.path.append(os.path.abspath('.'))
from credmodex.discriminancy import *
from credmodex.models import BaseModel
from credmodex.utils import *
from credmodex.config import *


__all__ = [
    'CredLab'
]


class CredLab:
    def __init__(self, df:pd.DataFrame=None, target:str=None, features:Union[list[str],str]=None, 
                 key_columns:list[str]=[],
                 test_size:float=0.1, out_of_time:float|str=0.2, 
                 seed:int=42, suppress_warnings:bool=False):

        if isinstance(features,str):
            features = [features]
        if target is None:
            target = DEFAULT_FORBIDDEN_COLS['target']

        if (df is None):
            raise ValueError("DataFrame cannot be None")
        self.raw_df = df.copy(deep=True)
        if (not isinstance(target, str)) or (not isinstance(features, list)):
            raise ValueError("target must be a string and features must be a list of strings")
        # The self.df contains only the columns target + features
        self.key_columns = key_columns
        self.forbidden_cols = get_forbidden_cols(additional_cols=key_columns)
        features = [f for f in features 
                    if f in df.columns 
                    and f not in self.forbidden_cols]
        
        if ('id' not in df.columns):
            df['id'] = range(len(df))

        must_columns = list(set(self.forbidden_cols) & set(self.raw_df.columns.to_list()))
        self.df = df[features + must_columns].copy(deep=True) if features and target else None
        if (self.df is None):
            raise ValueError("Both `target` and `[features]` must be provided.")
        
        self.id = DEFAULT_FORBIDDEN_COLS['id']
        self.target = target
        self.features = features
        self.suppress_warnings = suppress_warnings
        self.seed = seed
        np.random.seed(self.seed)

        self.models = {}
        self.predictions = {}
        self.metrics = {}

        self.test_size = test_size
        self.time_column = DEFAULT_FORBIDDEN_COLS['date']
        if self.time_column not in self.df.columns:
            out_of_time = None
            self.time_column = None
        self.out_of_time = out_of_time
        self.train_test_split()

    
    def train_test_split(self):
        self.df = self.df.copy()

        if (self.out_of_time is None) or (self.time_column is None):
            self.df['split'] = 'on_time'

        elif isinstance(self.out_of_time, str):
            self.df[self.time_column] = pd.to_datetime(self.df[self.time_column])
            self.df = self.df.sort_values(by=[self.time_column]).reset_index(drop=True)

            on_time = self.df[self.df[self.time_column] <= self.out_of_time].index.to_list()
            oot = self.df[self.df[self.time_column] > self.out_of_time].index.to_list()
            
            self.df.loc[on_time, 'split'] = 'on_time'
            self.df.loc[oot, 'split'] = 'oot'

            null_target_mask = self.df[self.target].isna()
            self.df.loc[(self.df['split'] == 'on_time') & null_target_mask, 'split'] = 'ttd'
            self.df.loc[(self.df['split'] == 'oot') & null_target_mask, 'split'] = 'out'

        elif isinstance(self.out_of_time, float):
            self.df[self.time_column] = pd.to_datetime(self.df[self.time_column])
            self.df = self.df.sort_values(by=[self.time_column]).reset_index(drop=True)

            # Define the cut-off date for the split
            self.df['scaled'] = (self.df[self.time_column] - self.df[self.time_column].min()) / (self.df[self.time_column].max() - self.df[self.time_column].min())
            target_data_value = self.df[self.time_column].min() + (1-self.out_of_time) * (self.df[self.time_column].max() - self.df[self.time_column].min())
            cutoff_date = (self.df[self.time_column] - target_data_value).abs().idxmin()
            cutoff_date = self.df.loc[cutoff_date, self.time_column]

            # Filter data for the training and testing sets based on the cutoff date
            on_time = self.df[self.df[self.time_column] <= cutoff_date]
            oot = self.df[self.df[self.time_column] > cutoff_date]

            # Separate features and target
            on_time = on_time.index.to_list()
            oot = oot.index.to_list()
            del self.df['scaled']

            self.df.loc[on_time, 'split'] = 'on_time'
            self.df.loc[oot, 'split'] = 'oot'

            null_target_mask = self.df[self.target].isna()
            self.df.loc[(self.df['split'] == 'on_time') & null_target_mask, 'split'] = 'ttd'
            self.df.loc[(self.df['split'] == 'oot') & null_target_mask, 'split'] = 'out'

        else:
            raise ValueError("´´out_of_time´´ must be a float or a string representing a date.")

        X = self.df[self.df['split'] == 'on_time'].index.to_list()
        train, test = sklearn.model_selection.train_test_split(X, test_size=self.test_size, random_state=self.seed)

        self.df.loc[train, 'split'] = 'train'
        self.df.loc[test, 'split'] = 'test'

        self.train = self.df[self.df['split'] == 'train']
        self.test = self.df[self.df['split'] == 'test']

        self.X_train = self.df[self.df['split'] == 'train'][self.features]
        self.X_test = self.df[self.df['split'] == 'test'][self.features]
        self.y_train = self.df[self.df['split'] == 'train'][self.target]
        self.y_test = self.df[self.df['split'] == 'test'][self.target]


    def plot_train_test_split(self, split:list[Literal['train', 'test', 'oot', 'ttd', 'out']]=['train', 'test', 'oot', 'ttd', 'out'],
                              graph_lib:str='plotly', freq='%Y-%m', width:int=900, height:int=450):
        self.df.loc[:, 'id_'] = 1
        self.grouped = self.df.groupby([pd.to_datetime(self.df[self.time_column]).dt.strftime(f'{freq}'),'split']).agg({'id_': 'count'}).reset_index()
        list_ = []
        if 'train' in split:
            list_.append([self.grouped[self.grouped['split'] == 'train'], 'Train', '#292929'])
        if 'test' in split:
            list_.append([self.grouped[self.grouped['split'] == 'test'], 'Test', '#704cae'])
        if 'oot' in split:
            list_.append([self.grouped[self.grouped['split'] == 'oot'], 'OoT', '#8edb29'])
        if 'ttd' in split:
            list_.append([self.grouped[self.grouped['split'] == 'ttd'], 'TtD', '#43dfd5'])
        if 'out' in split:
            list_.append([self.grouped[self.grouped['split'] == 'out'], 'OuT', '#e84f70'])

        if graph_lib == 'plotly':
            fig = go.Figure()
            for trace in list_:
                fig.add_trace(go.Bar(
                    x=trace[0][self.time_column],
                    y=trace[0]['id_'],
                    name=trace[1], marker=dict(color=trace[-1])
                ))
            from credmodex.utils.design import plotly_main_layout
            plotly_main_layout(fig, title='Train-Test Split', x='Time', y='Count', 
                height=height, width=width, barmode='stack'
            )
            del self.df['id_']
            return fig
        elif graph_lib == 'matplotlib':
            raise NotImplementedError("Matplotlib plotting is not implemented yet.")


    def add_model(self, model:type='LogisticRegression', treatment:type=None, name:str=None, doc:str=None, seed:int=42):

        if name is None:
            name = f'{model.__class__.__name__}_{len(self.models)+1}'
        
        base_model = BaseModel(
            model=model, treatment=treatment, df=self.df, doc=doc, seed=seed,
            features=self.features, target=self.target, predict_type='prob', 
            name=name, suppress_warnings=self.suppress_warnings, key_columns=self.key_columns
            )
        self.models[name] = base_model
        setattr(self, name, base_model)

        #self.model is always the last model added!
        self.model = base_model
        
        return model


    def eval_discriminancy(self, method:Union[str,type]='iv', split:list=['train','test','oot'], conditions:list=[]):
        if method is None:
            raise ValueError("Method cannot be None. Input a str or a Discriminancy class.")
        df = self.df.copy()
        
        if not isinstance(split, list):
            split = [split]
        df = df[df['split'].isin(split)]

        for condition in conditions:
            df = df.query(condition)
        if df.empty:
            print("DataFrame is empty after applying conditions!")
            return None
        
        if isinstance(method, str): method = method.lower().strip()

        if ('iv' in method) or (method == IV_Discriminant):
            return IV_Discriminant(df, self.target, self.features)
        
        if ('ks' in method) or (method == KS_Discriminant):
            return KS_Discriminant(df, self.target, self.features)
        
        if ('psi' in method) or (method == PSI_Discriminant):
            return PSI_Discriminant(df, self.target, self.features)
        
        if ('gini' in method) or (method == GINI_Discriminant):
            return GINI_Discriminant(df, self.target, self.features)
        
        if ('corr' in method) or (method == Correlation):
            return Correlation(df, self.target, self.features)


    def eval_goodness_of_fit(self, method:Union[str,type]='gini', model:Union[type]=None,
                             comparison_cols:list[str]=[]):
        if model is None:
            try: model = self.model
            except: raise ModuleNotFoundError('There is no model to evaluate!')
        
        if isinstance(method, str): method = method.lower().strip()

        eval_methods = {
            'iv': IV_Discriminant,
            'ks': KS_Discriminant,
            'psi': PSI_Discriminant,
            'gini': GINI_Discriminant,
            'corr': Correlation,
            'good': GoodnessFit,
        }

        # Single method execution
        if method != 'relatory':
            for key, func in eval_methods.items():
                if (key in method) or (method == func):
                    try: return func(df=model.df, target=self.target, features=['score'])
                    except: return func
            
        if ('relatory' in method):
            for func in [KS_Discriminant, PSI_Discriminant, GINI_Discriminant]:
                try: func(df=model.df, target=self.target, features=['score']).plot().show()
                except: ...
            print('\n=== Kolmogorov Smirnov ===')
            print(KS_Discriminant(df=model.df, target=self.target, features=['score']+comparison_cols).table())
            print('\n=== Population Stability ===')
            print(PSI_Discriminant(df=model.df, target=self.target, features=['score']+comparison_cols).table())
            print('\n=== Gini Lorenz ===')
            print(GINI_Discriminant(df=model.df, target=self.target, features=['score']+comparison_cols).table())
            print('\n=== Information Value ===')
            print(IV_Discriminant(df=model.df, target=self.target, features=['score']+comparison_cols).table())
            print('\n=== Hosmer Lemeshow ===') 
            pprint(GoodnessFit.hosmer_lemeshow(y_pred=model.df['score'], y_true=model.df[model.target], info=True))
            print('\n=== Deviance Odds ===') 
            pprint(GoodnessFit.deviance_odds(y_pred=model.df['score'], y_true=model.df[model.target], info=True))
            print('\n=== Gini Variance ===') 
            pprint(GoodnessFit.gini_variance(y_pred=model.df['score'], y_true=model.df[model.target], info=True))


    def model_relatory_notebook(self, model:Union[type]=None, rating:Union[type]=None,
                                comparison_cols:list[str]=[]):
        if model is None:
            try: model = self.model
            except: raise ModuleNotFoundError('There is no model to evaluate!')
        
        print(f'{'':=^100}\n{' SCORE ':=^100}\n{'':=^100}')
        for func in [KS_Discriminant, PSI_Discriminant, GINI_Discriminant]:
            try: func(df=model.df, target=self.target, features=['score']).plot().show()
            except: ...
        print('\n=== Kolmogorov Smirnov ===')
        print(KS_Discriminant(df=model.df, target=self.target, features=['score']+comparison_cols).table())
        print('\n=== Population Stability ===')
        print(PSI_Discriminant(df=model.df, target=self.target, features=['score']+comparison_cols).table())
        print('\n=== Gini Lorenz ===')
        print(GINI_Discriminant(df=model.df, target=self.target, features=['score']+comparison_cols).table())
        print('\n=== Information Value ===')
        print(IV_Discriminant(df=model.df, target=self.target, features=['score']+comparison_cols).table())
        print('\n=== Hosmer Lemeshow ===') 
        pprint(GoodnessFit.hosmer_lemeshow(y_pred=model.df['score'], y_true=model.df[model.target], info=True))
        print('\n=== Deviance Odds ===') 
        pprint(GoodnessFit.deviance_odds(y_pred=model.df['score'], y_true=model.df[model.target], info=True))
        print('\n=== Gini Variance ===') 
        pprint(GoodnessFit.gini_variance(y_pred=model.df['score'], y_true=model.df[model.target], info=True))

        if rating is None:
            try: rating = model.rating
            except: 
                print('There is no rating to evaluate!')
                return

        for key, rating in model.ratings.items():
            print(f'\n{'':=^100}\n{f' {key} ':=^100}\n{'':=^100}')

            rating.plot_gains_per_risk_group().show()
            rating.plot_stability_in_time().show()
            try: KS_Discriminant(df=rating.df, target=self.target, features=['rating']).plot().show()
            except: ...
            try: PSI_Discriminant(df=rating.df, target=self.target, features=['rating']).plot().show()
            except: ...
            print('\n=== Kolmogorov Smirnov ===')
            print(KS_Discriminant(df=rating.df, target=self.target, features=['rating']+comparison_cols).table())
            print('\n=== Population Stability ===')
            print(PSI_Discriminant(df=rating.df, target=self.target, features=['rating']+comparison_cols).table())
            print('\n=== Information Value ===')
            print(IV_Discriminant(df=rating.df, target=self.target, features=['rating']+comparison_cols).table())


    def eval_best_model(self, sort:str='ks', split:Literal['train','test','oot']=['train','test','oot']):
        if isinstance(split, str):
            split = [split]
        metrics_dict = {}

        for model_name, model in self.models.items():
            if (split is not None):
                y_true = model.y_true(split=split)
                y_pred = model.y_pred(split=split)
                dff = model.df[(self.model.df['split'].isin(split)) & (model.df[model.target].notna())].copy(deep=True)
            else:
                y_true = model.y_true()
                y_pred = model.y_pred()
                dff = model.df[model.df[model.target].notna()].copy(deep=True)

            auc, auc_variance = GoodnessFit.delong_roc_variance(y_true=y_true, y_pred=y_pred)
            gini_info = GoodnessFit.gini_variance(y_true=y_true, y_pred=y_pred, info=True)
            gini = gini_info['Gini']
            hosmer_lemershow = GoodnessFit.hosmer_lemeshow(y_true=y_true, y_pred=y_pred, info=True, g=8)
            brier_score = GoodnessFit.brier_score(y_true=y_true, y_pred=y_pred)
            ece = GoodnessFit.expected_calibration_error(y_true=y_true, y_pred=y_pred, n_bins=10)
            log_likelihood = GoodnessFit.log_likelihood(y_true=y_true, y_pred=y_pred)
            aic = GoodnessFit.aic(y_true=y_true, y_pred=y_pred, n_features=model.n_features)
            bic = GoodnessFit.bic(y_true=y_true, y_pred=y_pred, n_features=model.n_features, sample_size=len(dff))
            wald_test = GoodnessFit.wald_test(y_true=y_true, y_pred=y_pred, info=True)
            deviance_odds = GoodnessFit.deviance_odds(y_true=y_true, y_pred=y_pred, info=True)

            try: iv = IV_Discriminant(dff, model.target, ['score']).value('score', final_value=True)
            except: iv = np.nan
            try: ks = KS_Discriminant(dff, model.target, ['score']).value('score', final_value=True)
            except: ks = np.nan
            try: psi = PSI_Discriminant(dff, model.target, ['score']).value('score', final_value=True)
            except: psi = np.nan

            contingency_table = pd.crosstab(y_pred, y_true)
            chi2_stat, p_val_chi2, _, _ = chi2_contingency(contingency_table)
            if (p_val_chi2 < 0.05): chi2 = 'Significant Discr.'
            else: chi2 = 'No Significant Discr.'

            metrics_dict[model_name] = {
                'iv': iv,
                'ks': ks,
                'psi': psi,
                'chi2': chi2,
                'auc': auc,
                'auc variance': auc_variance,
                'gini': gini,
                'hosmer-lemeshow': hosmer_lemershow['HL'],
                'hosmer conclusion': hosmer_lemershow['conclusion'],
                'brier': brier_score,
                'ece': ece,
                'wald test': wald_test['conclusion'],
                'deviance odds power': deviance_odds['power'],
                'log-likelihood': round(log_likelihood,1),
                'aic': round(aic,1),
                'bic': round(bic,1),
            }

        # Create DataFrame and transpose it so model names are columns
        dff = pd.DataFrame(metrics_dict)
        dff.loc['relative likelihood',:] = GoodnessFit.relative_likelihood(aic_values=list(dff.loc['aic',:].values))
        dff = dff.loc[['relative likelihood'] + [i for i in dff.index if i != 'relative likelihood']]

        try:
            sort = sort.lower()
            if (sort is not None) and (sort in [s.lower() for s in dff.index]):
                dff = dff.T.sort_values(by=sort, ascending=False).T
        except:
            ...

        return dff


    def eval_best_rating(self, sort:str='ks', split:Literal['train','test','oot']=['train','test','oot']):
        if isinstance(split, str):
            split = [split]
        dff = pd.DataFrame()
        for model_name, model in self.models.items():
            try: 
                dff_ = model.eval_best_rating(split=split)
                dff = pd.concat([dff, dff_], axis=1)
            except: 
                ...
        
        try:
            sort = sort.lower()
            if (sort is not None) and (sort in [s.lower() for s in dff.index]):
                dff = dff.T.sort_values(by=sort, ascending=False).T
        except:
            ...

        return dff


    def models_relatory_pdf(self, comparison_cols:list[str]=[], pdf_name='project_report'):
        if (len(self.models.items()) < 1):
            raise TypeError('There are no Models available! Please, add a Model with ``.add_model()``')
        
        try:
            from credmodex.utils import pdf_report
        except ImportError as e:
            raise ImportError("PDF generation requires `fpdf`. Please install it with `pip install fpdf`.") from e
        pdf = pdf_report.PDF_Report()

        pdf.add_chapter_model_page(text=f'{pdf.reference_name_page}')
        pdf.add_page()

        fig = self.plot_train_test_split()
        fig.update_layout(margin=dict(l=70, r=70, t=70, b=70))
        img_path = pdf.save_plotly_to_image(fig)
        pdf.add_image(img_path, w=180)
        os.remove(img_path)

        best_model_table = self.eval_best_model(sort='ks')
        pdf.add_dataframe_split(best_model_table, chunk_size=3, skip_page=3)
            
        for model_name, model in self.models.items():
            pdf.add_chapter_model_page(text=model_name)
            pdf = model.model_relatory_pdf(
                comparison_cols=comparison_cols,
                pdf=pdf, save_pdf=False
            )

        pdf.output(f"{pdf_name}.pdf")


    def get_rating_df(self):
        df_ = pd.DataFrame(self.df[['id', self.target, 'date', 'split']])
        for model_name, model in self.models.items():
            for rating_name, rating in model.ratings.items():
                df_ = df_.merge(
                    rating.df[['id','rating']].rename(columns={'rating': f'{model_name}.{rating_name}'}), 
                    on='id', how='inner'
                )

        self.rating_df = df_




if __name__ == "__main__":
    ...