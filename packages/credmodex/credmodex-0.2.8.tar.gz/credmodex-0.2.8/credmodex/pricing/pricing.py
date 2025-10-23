import sys
import os
import warnings

import pandas as pd
import plotly.io as pio

from typing import Literal
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

sys.path.append(os.path.abspath('..'))

from credmodex import DEFAULT_FORBIDDEN_COLS


__all__ = [
    'Pricing'
]


class Pricing():
    def __init__(
            self, 
            binary_target: float = None, 
            prob_target: float = None, 
            suppress_warnings: bool = False, 
            bad_payers: int = 1,
            optimizer_config: dict = {},
        ):
        
        self.binary_target = binary_target
        self.suppress_warnings = suppress_warnings
        self.prob_target = prob_target
        self.bad_payers = bad_payers

        self.col_id = DEFAULT_FORBIDDEN_COLS['id']
        self.col_rating = DEFAULT_FORBIDDEN_COLS['rating']
        self.col_loan_amount = DEFAULT_FORBIDDEN_COLS['loan_amount']
        self.col_term = DEFAULT_FORBIDDEN_COLS['term']
        self.col_target = DEFAULT_FORBIDDEN_COLS['target']
        self.col_split = DEFAULT_FORBIDDEN_COLS['split']
        self.col_date = DEFAULT_FORBIDDEN_COLS['date']

        self.optimizer_config = {
            'solver': 'glpk',
            'executable': None,
            'tee': False
        }
        for key, value in optimizer_config.items():
            self.optimizer_config[key] = value

        if self.binary_target is None:
            raise ValueError("You must specify a `binary_target` value.")
        
        if self.prob_target is None:
            if not self.suppress_warnings:
                warnings.warn(f"`prob_target` is not used in this method, therefore {self.binary_target} will be used.")
            self.prob_target = self.binary_target


    def add_approve_simulation(
            self, 
            df: pd.DataFrame, 
            name: str,
            max_cumul_target: float = 0.3,
            query=None,
            split: list[Literal['train', 'test', 'oot']] = None,
            initial_date: str = None,
            upto_date: str = None,
            *,
            mean_loan_amount_Regressor = None,
            split_swap_in = None,
        ) -> pd.DataFrame:
        
        if df is None:
            raise ValueError("You must specify a `df` value.")
        
        df = df.copy()
        
        if (query is not None):
            df = df.query(query)

        # Build extrapolated counts per rating (only if we have the split column)
        df_extrapolated = None
        if split_swap_in is not None and (self.col_split in df.columns):
            df_extrapolated = (
                df[df[self.col_split].isin(split_swap_in)]
                .groupby(self.col_rating, as_index=False)
                .agg(n_extrapolated=(self.col_id, 'size'))   # <- named aggregation
            )

        if (split is not None) and (self.col_split in df.columns):
            df = df[df[self.col_split].isin(split)]
        if (initial_date is not None):
            df = df[df[self.col_date] >= initial_date]
        if (upto_date is not None):
            df = df[df[self.col_date] <= upto_date]

        if (self.bad_payers == 0):
            df[self.binary_target] = df[self.binary_target].apply(lambda x: 1 if x == 0 else 0)
        
        # Ensure self.col_rating is sorted properly
        df = df.sort_values(by=self.col_rating, ascending=True)
        # df = df.dropna(subset=self.col_target)

        # Group by rating
        agg_df = df.groupby(self.col_rating).agg({
            self.col_id: 'size',
            self.col_term: 'mean',
            self.col_loan_amount: 'mean',
        }).reset_index()
        agg_df.columns = [self.col_rating, 'amount', f'mean_{self.col_term}', f'mean_{self.col_loan_amount}']

        agg_df['model'] = name

        # After you create agg_df and add model / rating_stats merges:
        if df_extrapolated is not None:
            agg_df = agg_df.merge(df_extrapolated, on=self.col_rating, how='left')
            agg_df['n_extrapolated'] = agg_df['n_extrapolated'].fillna(0).astype('Int64')

        # Add per-rating mean of prob_target (aligned by key, not by position)
        rating_stats = (
            df.groupby(self.col_rating)[self.prob_target]
            .mean()
            .reset_index()
            .rename(columns={self.prob_target: f'mean_{self.prob_target}'})
        )
        agg_df = agg_df.merge(rating_stats, on=self.col_rating, how='left')

        weighted_values = agg_df[f'mean_{self.prob_target}'] * agg_df['amount']
        cumulative_weighted_sum = weighted_values.cumsum()
        cumulative_weights = agg_df['amount'].cumsum()

        agg_df[f'cumul_{self.prob_target}'] = cumulative_weighted_sum / cumulative_weights

        if mean_loan_amount_Regressor is not None:
            prob_target_ = agg_df[f'mean_{self.prob_target}'].to_numpy().reshape(-1, 1)
            new_mean_loans_ = mean_loan_amount_Regressor.predict(prob_target_).round(2)
            agg_df.loc[:, f'mean_{self.col_loan_amount}'] = new_mean_loans_

        agg_df['production_payers'] = agg_df.apply(
            lambda row: int(row[f'mean_{self.col_loan_amount}'] * row['amount'])
            if pd.notnull(row[f'mean_{self.col_loan_amount}']) and pd.notnull(row['amount'])
            else 0,
            axis=1
        ).astype('Int64')
        agg_df[f'production_{self.prob_target}'] = (agg_df['production_payers'] - (agg_df['production_payers'] * agg_df[f'mean_{self.prob_target}'])).astype('Int64')

        agg_df['approved'] = agg_df[f'cumul_{self.prob_target}'].apply(lambda x: 0 if x >= max_cumul_target else 1)

        # Round the values
        col_term_mean = f'mean_{self.col_term}'
        agg_df[col_term_mean] = pd.to_numeric(agg_df[col_term_mean], errors='coerce')  # converte valores inválidos para NaN
        agg_df[col_term_mean] = agg_df[col_term_mean].round().astype('Int64')

        agg_df[f'mean_{self.col_loan_amount}'] = agg_df[f'mean_{self.col_loan_amount}'].astype(float).round(2)
        agg_df[f'mean_{self.col_loan_amount}'] = agg_df[f'mean_{self.col_loan_amount}'].astype(float).round(2)
        agg_df[f'mean_{self.prob_target}'] = agg_df[f'mean_{self.prob_target}'].round(4)
        agg_df[f'cumul_{self.prob_target}'] = agg_df[f'cumul_{self.prob_target}'].round(4)

        if name:
            setattr(self, name, agg_df)

        return agg_df
    

    def add_approve_simulations(
            self, 
            dfs: list[pd.DataFrame] = None, 
            names: list[str] = None,
            max_cumul_target: float = 0.3,
            objective_production: Literal['production_payers', 'production_prob']='production_payers',
            priority:list=None,
            alpha:float=0.1,
            queries:list[str] = None,
            split: list[Literal['train', 'test', 'oot']] = None,
            initial_date: str = None,
            upto_date: str = None,
            *,
            mean_loan_amount_Regressor = None,
            split_swap_in: list[Literal['train','test','oot']] = None,
        ) -> pd.DataFrame:
        
        import pyomo.environ as pyomo_env
        import pandas as pd

        # --- Input validation ---
        if not dfs:
            raise ValueError("You must specify a `dfs` value.")
        for df in dfs:
            if not isinstance(df, pd.DataFrame):
                raise ValueError("All items in `dfs` must be pandas DataFrames.")
        if not isinstance(max_cumul_target, (int, float)):
            raise ValueError("`max_cumul_target` must be a numeric value.")
        assert max_cumul_target > 0, "max_cumul_target must be greater than 0."
        assert max_cumul_target <= 1, "max_cumul_target must be less than or equal to 1."

        # Generate names if not provided
        if names is None:
            names = [str(i + 1) for i in range(len(dfs))]
        elif len(names) != len(dfs):
            raise ValueError("Length of `names` must match length of `dfs`.")
        
        if (queries is None):
            queries = [None] * len(dfs)

        # --- Aggregate simulation data ---
        agg_dfs = []
        idx = 0
        for df, name in zip(dfs, names):
            if self.col_rating not in df.columns:
                raise ValueError("Each DataFrame in `dfs` must contain a self.col_rating column.")
            current_df = self.add_approve_simulation(
                df=df, 
                name=name,
                max_cumul_target=max_cumul_target,
                query=queries[idx],
                split=split,
                initial_date=initial_date,
                upto_date=upto_date,
                mean_loan_amount_Regressor=mean_loan_amount_Regressor,
                split_swap_in=split_swap_in,
            )
            del current_df['approved']
            agg_dfs.append(current_df)
            idx += 1

        # Combine all dataframes
        df = pd.concat(agg_dfs, ignore_index=True)

        # if some models didn't produce n_extrapolated, create/fill for consistency
        if 'n_extrapolated' in df.columns:
            df['n_extrapolated'] = df['n_extrapolated'].fillna(0).astype('Int64')
        else:
            df['n_extrapolated'] = pd.Series([0]*len(df), dtype='Int64')

        df['row_id'] = df.index

        df['priority'] = 0
        if priority is not None:
            model_order = dict(zip(names, priority))
            df['priority'] = df['model'].map(model_order)
            priority_dict = df.set_index('row_id')['priority'].to_dict()
        else:
            priority_dict = df.set_index('row_id')['priority'].to_dict()

        # --- Build Pyomo model ---
        model = pyomo_env.ConcreteModel()

        # Sets
        model.R = pyomo_env.Set(initialize=df['row_id'].tolist())

        # Parameters
        amount = df.set_index('row_id')['amount'].to_dict()
        mean_target = df.set_index('row_id')[f'mean_{self.prob_target}'].to_dict()

        if objective_production == 'production_prob':
            objective_production = f'production_{self.prob_target}'
        production = df.set_index('row_id')[objective_production].to_dict()

        # Decision Variables: 1 = approve, 0 = reject
        model.x = pyomo_env.Var(model.R, within=pyomo_env.Binary)

        # --- Rating to numeric for sorting ---
        rating_order = {chr(65 + i): i + 1 for i in range(12)}  # A=1, ..., L=12
        df['rating_order'] = df[self.col_rating].map(rating_order)

        # --- Monotonicity constraints: enforce sorted approval ---
        model.monotonic_constraints = pyomo_env.ConstraintList()
        grouped = df.groupby('model')
        for model_name, group in grouped:
            sorted_group = group.sort_values(by='rating_order')
            indices = sorted_group['row_id'].tolist()
            for i in range(1, len(indices)):
                curr_id = indices[i]
                prev_id = indices[i - 1]
                model.monotonic_constraints.add(model.x[curr_id] <= model.x[prev_id])

        # --- Objective: Maximize production ---
        production = {k: (v if v is not None else 0) for k, v in production.items()}
        # Compute max possible production and priority for scaling
        total_prod_max = sum(production.values())
        total_priority_max = sum(priority_dict.values())

        # Avoid division by zero
        total_prod_max = total_prod_max if total_prod_max > 0 else 1
        total_priority_max = total_priority_max if total_priority_max > 0 else 1

        # Normalize both terms to [0, 1] and interpolate with alpha
        model.total_production = pyomo_env.Objective(
            expr=(1 - alpha) * (sum(production[i] * model.x[i] for i in model.R) / total_prod_max) +
                alpha * (sum(priority_dict[i] * model.x[i] for i in model.R) / total_priority_max),
            sense=pyomo_env.maximize
        )

        # --- Constraint: Risk weighted target ---
        def _risk_rule(m):
            # Filtra índices "ativos": precisam ter coeficiente na restrição
            # Evita NaN e zera.
            active = []
            for i in m.R:
                a = amount[i]
                mt = mean_target[i]
                # Se 'amount' for zero ou NaN, o termo some
                if a is None:
                    continue
                try:
                    _ = float(a)
                except Exception:
                    continue
                if a == 0:
                    continue
                # mt pode ser 0 sem problema; só removemos NaN
                try:
                    _ = float(mt)
                except Exception:
                    continue
                if mt != mt:  # NaN check
                    continue
                active.append(i)

            # 1) Se não há nenhum índice com coeficiente, a restrição seria trivial.
            if not active:
                return pyomo_env.Constraint.Feasible  # ou Constraint.Skip

            lhs = sum(mean_target[i] * amount[i] * m.x[i] for i in active)
            rhs = max_cumul_target * sum(amount[i] * m.x[i] for i in active)
            return lhs <= rhs

        model.risk_constraint = pyomo_env.Constraint(rule=_risk_rule)


        # --- Solve the model ---
        solver = pyomo_env.SolverFactory(self.optimizer_config['solver'], executable=self.optimizer_config['executable'])
        results = solver.solve(model, tee=self.optimizer_config['tee'])

        # --- Extract results ---
        df['approve'] = df['row_id'].apply(lambda i: int(pyomo_env.value(model.x[i])))

        # --- Final output ---
        df = df.sort_values(by=['approve', 'rating_order'], ascending=[False, True])
        df['weighted_sum'] = df[f'mean_{self.prob_target}'] * df['amount']
        df[f'cumul_{self.prob_target}'] = (df['weighted_sum'].cumsum() / df['amount'].cumsum()).round(4)
        del df['weighted_sum']

        cols = [
            'model',
            self.col_rating,
            f'cumul_{self.prob_target}',
            'approve',
            'amount',
            f'mean_{self.prob_target}',
            f'mean_{self.col_loan_amount}',
            objective_production,
        ]

        # keep n_extrapolated if we have it
        if 'n_extrapolated' in df.columns:
            # put it somewhere useful; e.g., right after rating
            cols.insert(2, 'n_extrapolated')

        return df[cols].reset_index(drop=True)


    def add_production_simulation(
            self,
            simulated_df: pd.DataFrame = None,
            df: pd.DataFrame = None, 
            name: str = None,
            split: list[Literal['train', 'test', 'oot', 'ttd', 'out']]=['out', 'ttd'],
            acceptance_percent:float = 1,
            query: str = NotImplemented,
            initial_date: str = None,
            upto_date: str = None,
        ) -> pd.DataFrame:

        if (simulated_df is None):
            raise ValueError(f"You need to input a `simulated_df`")

        df = df.copy(deep=True)

        if (query is not None):
            df = df.query(query)

        if (split is not None) and (self.col_split in df.columns):
            df = df[df[self.col_split].isin(split)]
        if (initial_date is not None):
            df = df[df[self.col_date] >= initial_date]
        if (upto_date is not None):
            df = df[df[self.col_date] <= upto_date]

        simulated_df = simulated_df[simulated_df['model'] == name]

        df = df.merge(simulated_df, on=self.col_rating, how='left')

        agg_dict = {
            self.col_id: 'count',
            'approve': 'mean',
            f'mean_{self.prob_target}': 'mean',
            f'mean_{self.col_loan_amount}': 'mean',
            f'cumul_{self.prob_target}': 'mean',
        }

        # Pass-through optional columns from the simulated_df
        passthrough_cols = []
        if 'n_extrapolated' in df.columns:
            agg_dict['n_extrapolated'] = 'first'   # or 'max'

        df = df.groupby(self.col_rating).agg(agg_dict).reset_index(drop=False)

        # rename columns back as before
        agg_named = {
            'id':                (self.col_id, 'count'),
            'approve':           ('approve', 'mean'),
            f'mean_{self.prob_target}':     (f'mean_{self.prob_target}', 'mean'),
            f'mean_{self.col_loan_amount}': (f'mean_{self.col_loan_amount}', 'mean'),
            f'cumul_{self.prob_target}':    (f'cumul_{self.prob_target}', 'mean'),
        }

        # Put n_extrapolated exactly where you want it (right after rating)
        if 'n_extrapolated' in df.columns:
            # Rebuild dict to ensure order: rating | n_extrapolated | id | approve | means...
            agg_named = {
                'n_extrapolated': ('n_extrapolated', 'first'),
                **agg_named
            }

        grouped = (
            df.groupby(self.col_rating, as_index=False)
            .agg(**agg_named)
        )

        # Reorder columns for readability
        cols = [self.col_rating]
        if 'n_extrapolated' in grouped.columns:
            cols += ['n_extrapolated']
        cols += ['id', 'approve',
                f'mean_{self.prob_target}', f'mean_{self.col_loan_amount}', f'cumul_{self.prob_target}']
        grouped = grouped[cols]
        
        df['production'] = pd.to_numeric(
            df['approve'] * df[self.col_id] * df[f'mean_{self.col_loan_amount}'] * acceptance_percent,
            errors='coerce'
        ).round().astype('Int64')

        df.loc['Total', [self.col_id, 'production']] = df.loc[:, [self.col_id, 'production']].sum()
        df[f'mean_{self.prob_target}'] = df[f'mean_{self.prob_target}'].round(4)
        
        return df


    def add_production_simulations(
            self,
            simulated_df: pd.DataFrame = None,
            dfs: list[pd.DataFrame] = None, 
            names: list[str] = None,
            split: list[Literal['train', 'test', 'oot', 'ttd', 'out']]=['out', 'ttd'],
            acceptance_percent: list[float] = None,
            queries: list[str] = None,
            initial_date: str = None,
            upto_date: str = None,
        ) -> pd.DataFrame:

        # --- Input validation ---
        if not dfs:
            raise ValueError("You must specify a `dfs` value.")
        for df in dfs:
            if not isinstance(df, pd.DataFrame):
                raise ValueError("All items in `dfs` must be pandas DataFrames.")

        # Generate names if not provided
        if names is None:
            names = [str(i + 1) for i in range(len(dfs))]
        elif len(names) != len(dfs):
            raise ValueError("Length of `names` must match length of `dfs`.")

        if (queries is None):
            queries = [None] * len(dfs)
        if (acceptance_percent is None):
            acceptance_percent = [1] * len(dfs)

        # --- Aggregate simulation data ---
        agg_dfs = []
        idx = 0
        for df, name in zip(dfs, names):
            current_df = self.add_production_simulation(
                simulated_df=simulated_df,
                df=df, 
                name=name,
                split=split,
                acceptance_percent=acceptance_percent[idx],
                query=queries[idx],
                initial_date=initial_date,
                upto_date=upto_date,
            )
            current_df = current_df.drop('Total', axis=0, errors='ignore')

            if current_df.empty:
                # nada para agregar deste 'name'
                idx += 1
                continue

            current_df.loc[:, 'model'] = name
            agg_dfs.append(current_df)
            idx += 1

        # Combine all dataframes
        df = pd.concat(agg_dfs, ignore_index=True)

        # existing totals
        df.loc['Total', [self.col_id, 'production']] = df[df['approve'] == 1].loc[:, [self.col_id, 'production']].sum()
        df.loc['Total', [f'cumul_{self.prob_target}']] = df[df['approve'] == 1].loc[:, [f'cumul_{self.prob_target}']].max()

        # optional: total for n_extrapolated across approved buckets
        if 'n_extrapolated' in df.columns:
            df.loc['Total', 'n_extrapolated'] = df[df['approve'] == 1]['n_extrapolated'].sum()

        df[f'mean_{self.col_loan_amount}'] = df[f'mean_{self.col_loan_amount}'].round(4)
        df[f'cumul_{self.prob_target}'] = df[f'cumul_{self.prob_target}'].round(4)

        return df


    def add_simulation(
            self, 
            dfs: list[pd.DataFrame] = None, 
            names: list[str] = None,
            max_cumul_target: float = 0.3,
            split_approved: list[Literal['train', 'test', 'oot']]=['train', 'test', 'oot'],
            split_production: list[Literal['train', 'test', 'oot', 'ttd', 'out']]=['out', 'ttd'],
            objective_production: Literal['production_payers', 'production_prob']='production_payers',
            priority:list=None,
            alpha:float=0.1,
            acceptance_percent: list[float] = None,
            queries: list[str] = None,
            initial_date: str = None,
            upto_date: str = None,
        ) -> pd.DataFrame:

        simulated_df = self.add_approve_simulations(
            dfs=dfs,
            names=names,
            max_cumul_target=max_cumul_target,
            objective_production=objective_production,
            priority=priority,
            alpha=alpha,
            queries=queries,
            split=split_approved,
            initial_date=initial_date,
            upto_date=upto_date,
        )

        result_df = self.add_production_simulations(
            simulated_df=simulated_df,
            dfs=dfs,
            names=names,
            split=split_production,
            acceptance_percent=acceptance_percent,
            queries=queries,
            initial_date=initial_date,
            upto_date=upto_date,
        )

        return result_df


    def swap_in_df_(
        self,
        df: pd.DataFrame, 
        name: str,
        max_cumul_target: float = 0.3,
        query=None,
        split: list[Literal['train','test','oot']] = ['oot'],
        *,
        initial_date: str | None = None,
        upto_date: str | None = None,
        backfill_only: bool = True,   # <- use means only when present
    ) -> pd.DataFrame:
        """
        Note: only with prob_target!
        """
        df = df.copy(deep=True)

        sim = self.add_approve_simulation(
            df=df,
            name=name,
            max_cumul_target=max_cumul_target,
            query=query,
            split=split,
            initial_date=initial_date,
            upto_date=upto_date,
        ).rename(columns={
            f'{self.col_rating}': self.col_rating,
            f'mean_{self.col_term}': f'__mean__{self.col_term}',
            f'mean_{self.col_loan_amount}': f'__mean__{self.col_loan_amount}',
            f'mean_{self.prob_target}': f'__mean__{self.prob_target}',
        })[[self.col_rating, f'__mean__{self.col_term}', f'__mean__{self.col_loan_amount}', f'__mean__{self.prob_target}']]

        # 1) Merge WITHOUT dropping originals
        df = df.merge(sim, on=self.col_rating, how='left')

        # 2) Decide replacement policy
        # Backfill: use bucket means only when present; otherwise keep row's own value
        for col in (self.col_term, self.col_loan_amount, self.prob_target):
            mean_col = f'__mean__{col}'
            if backfill_only:
                df[col] = df[mean_col].combine_first(df[col])
            else:
                # old behavior: always overwrite (may introduce NaNs if mean is missing)
                df[col] = df[mean_col]

            # drop temp mean column
            df.drop(columns=[mean_col], inplace=True)

        return df
    

    def swap_in_dfs_(
            self, 
            dfs: list[pd.DataFrame] = None, 
            queries: list[str] = [],
            split_swap_in: list[Literal['train', 'test', 'oot']] = ['oot'],
        ) -> pd.DataFrame:

        while len(queries) < len(dfs):
            queries.append(None)

        swap_in_dfs = []
        for idx, df in enumerate(dfs):
            current_df = self.swap_in_df_(
                df=df,
                name='x', # Arbitrary
                max_cumul_target=0.9, # Arbitrary
                query=queries[idx],
                split=split_swap_in,
            )
            swap_in_dfs.append(current_df)
        
        return swap_in_dfs


    def swap_in_simulations(
            self, 
            dfs: list[pd.DataFrame] = None, 
            names: list[str] = None,
            max_cumul_target: float = 0.3,
            objective_production: Literal['production_payers', 'production_prob'] = 'production_payers',
            priority:list = None,
            alpha:float = 0.1,
            acceptance_percent: list[float] = None,
            queries: list[str] = [],
            split_swap_in: list[Literal['train', 'test', 'oot']] = ['oot'],
            split_approved: list[Literal['train', 'test', 'oot']] = None,
            split_production: list[Literal['train', 'test', 'oot', 'ttd', 'out']] = None,
            initial_date: str = None,
            upto_date: str = None,
        ) -> pd.DataFrame:

        while len(queries) < len(dfs):
            queries.append(None)

        swap_in_dfs = self.swap_in_dfs_(
            dfs=dfs, 
            queries=queries,
            split_swap_in=split_swap_in,
        )

        simulated_df = self.add_approve_simulations(
            dfs=swap_in_dfs,
            names=names,
            max_cumul_target=max_cumul_target,
            objective_production=objective_production,
            priority=priority,
            alpha=alpha,
            queries=queries,
            split=split_approved,
            initial_date=initial_date,
            upto_date=upto_date,
        )

        result_df = self.add_production_simulations(
            simulated_df=simulated_df,
            dfs=swap_in_dfs,
            names=names,
            acceptance_percent=acceptance_percent,
            queries=queries,
            split=split_production,
            initial_date=initial_date,
            upto_date=upto_date,
        )

        return result_df


    @staticmethod
    def exemple_df(
            model, rating, amount, mean_target, mean_ticket
        ):
        df = pd.DataFrame({
            DEFAULT_FORBIDDEN_COLS['rating']: rating,
            'amount': amount,
            'mean_target': mean_target,
            f'mean_{DEFAULT_FORBIDDEN_COLS['loan_amount']}': mean_ticket,
        })

        df['weighted_sum'] = df['mean_target'] * df['amount']
        df['cumul_target'] = (df['weighted_sum'].cumsum() / df['amount'].cumsum()).round(4)
        del df['weighted_sum']

        df['production'] = (df[f'mean_{DEFAULT_FORBIDDEN_COLS['loan_amount']}'] * df['amount']).astype(int)
        df['model'] = model

        return df


