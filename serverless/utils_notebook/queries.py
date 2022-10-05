from dataclasses import dataclass

import numpy as np 
import pandas as pd 
from subgrounds.subgrounds import Subgrounds, Subgraph
from subgrounds.subgraph import SyntheticField
from subgrounds.pagination import ShallowStrategy

from .utils import remove_prefix
from .testing import validate_season_series


def synthetic_field_float_div_precision(
    Query, 
    new_field_name: str, 
    process_field_name: str, 
    precision: float 
): 
    setattr(
        Query, 
        new_field_name, 
        SyntheticField(
            lambda v: float(v) / precision, 
            SyntheticField.FLOAT, 
            getattr(Query, process_field_name) 
        ) 
    ) 


@dataclass
class QueryManager: 

    sg: Subgrounds
    bs: Subgraph 

    def query_seasons(self, extra_cols=None, where=None): 
        """Returns dataframe of form 
        
        #   Column     Dtype         
        ---  ------     -----         
        0   season     int64         
        1   timestamp  datetime64[ns]
        
        You can add more columns to this df via extra_cols 
        """
        sg = self.sg 
        bs = self.bs 
        extra_cols = extra_cols or []
        where = where or {}
        q = bs.Query.seasons(first=100000, where=where, orderBy="season", orderDirection="asc")
        df = sg.query_df(
            [
                q.season, 
                q.timestamp, 
                *[getattr(q, col) for col in extra_cols]
            ], 
            pagination_strategy=ShallowStrategy
        )
        df = remove_prefix(df, "seasons_")
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        df = df.sort_values("timestamp").reset_index(drop=True)
        incorrect_timestamps = df.loc[df.timestamp == '1970-01-01 00:00:00']
        if len(incorrect_timestamps): 
            """
            TODO
            Currently, the timestamps for seasons 0 and 1 are incorrectly 1970-01-01 00:00:00 
            While we wait for this to be fixed in the subgraph, we impute reasonable values
            """
            indices = incorrect_timestamps.index.values 
            assert set(indices) == set([0, 1]) 
            for i in indices: 
                df.loc[i,'timestamp'] = df.loc[2,'timestamp'] - ((2-i) * pd.Timedelta(1, 'h'))
        validate_season_series(df, allow_missing=False) 
        return df 

    def query_rewards_fertilizer(self): 
        """Returns dataframe of form 

        #   Column                   Dtype  
        ---  ------                   -----  
        0   season                   int64  
        1   reward_fertilized_beans  float64

        Season axis begins at 6076 (first season the Reward event was emitted)
        and has no missing values. 
        """
        sg = self.sg 
        bs = self.bs 
        synthetic_field_float_div_precision(
            bs.Reward, 'reward_fertilized_beans', 'toFertilizer', 1e6 
        )
        q = bs.Query.rewards(orderBy="blockNumber", orderDirection="asc", first=100000)
        df = sg.query_df(
            [
                q.season, 
                q.reward_fertilized_beans, 
            ], 
            pagination_strategy=ShallowStrategy
        )
        df = remove_prefix(df, 'rewards_').sort_values('season').reset_index(drop=True)
        szns = df.season.unique() 
        missing_szns = [i for i in range(df.season.min(), df.season.max()) if i not in szns] 
        df_missing_szns = pd.DataFrame([{"season": i, "reward_fertilized_beans": 0} for i in missing_szns])
        df = pd.concat([df, df_missing_szns]).sort_values('season').reset_index(drop=True)
        validate_season_series(df, allow_missing=False)
        return df 

    def query_fertilizer_tokens(self): 
        """Returns dataframe of form 

         #   Column     Dtype  
        ---  ------     -----  
        0   season     int64  
        1   supply     int64  
        2   humidity   float64 
        3   start_bpf  float64
        4   end_bpf    float64

        Season axis begins at 6074. Note that there are two entries for season 
        6074, for fertilizer issued pre-post replant. 
        """
        sg = self.sg 
        bs = self.bs 
        synthetic_field_float_div_precision(
            bs.FertilizerToken, 'start_bpf', 'startBpf', 1e6 
        )
        synthetic_field_float_div_precision(
            bs.FertilizerToken, 'end_bpf', 'id', 1e6 
        )
        ft = bs.Query.fertilizerTokens(
            first=100000, 
            orderBy="humidity", 
            orderDirection="desc"
        )
        df = sg.query_df(
            [
                ft.season, 
                ft.supply, 
                ft.humidity, 
                ft.start_bpf, 
                ft.end_bpf, 
            ],
            pagination_strategy=ShallowStrategy
        )
        return remove_prefix(df, "fertilizerTokens_")

    def query_barn(self): 
        """Returns dataframe of form 

        #   Column                     Dtype         
        ---  ------                     -----         
        0   season                     int64         
        1   timestamp                  datetime64[ns]
        2   reward_fertilized_sprouts  float64       
        3   sprouts_rinsable           float64       
        4   sprouts                    float64       
        5   rinsable_percent           float64       
        6   fertilizer_total           int64         
        7   fertilizer_active          float64       
        8   fertilizer_available       float64   

        Season axis begins at 6074 and has no missing values.     
        """
        df_szns = self.query_seasons(where={"season_gte": 6074})
        df_rewards_fert = self.query_rewards_fertilizer()
        df_fert_tokens = self.query_fertilizer_tokens()
        df = (
            df_szns
            .merge(df_rewards_fert, how="left", on="season")
            .merge(df_fert_tokens, how="left", on="season")
        ) 
        df = df.fillna(0)
        df = df.rename(columns={
            "reward_fertilized_beans": "reward_fertilized_sprouts", 
        })
        df['sprouts_rinsable'] = df.reward_fertilized_sprouts.cumsum()
        df['sprouts'] = ((df.supply * df.end_bpf).cumsum() - df.sprouts_rinsable).ffill()
        df['rinsable_percent'] = df.sprouts_rinsable / (df.sprouts_rinsable + df.sprouts).ffill()
        df['fertilizer_total'] = 77000000
        df['fertilizer_active'] = df.supply.cumsum().ffill()
        df['fertilizer_available'] = (df.fertilizer_total - df.fertilizer_active).ffill()
        # Remove duplicate season 6074, which is expected since we joined in values from fertilizer tokens 
        df = df.sort_values(["season", "end_bpf"], ascending=[True, False]).reset_index(drop=True)
        assert df.season.min() == 6074
        assert len(df.loc[df.season == 6074]) == 2
        df = df.iloc[1:,:] 
        df = df[[
            'season', 'timestamp', 
            'reward_fertilized_sprouts', 'sprouts_rinsable', 'sprouts', 'rinsable_percent', 
            'fertilizer_total', 'fertilizer_active', 'fertilizer_available',
        ]]
        assert not df.isnull().values.any()
        validate_season_series(df)
        return df 