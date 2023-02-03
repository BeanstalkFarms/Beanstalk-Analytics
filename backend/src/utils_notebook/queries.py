import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from subgrounds.subgrounds import Subgrounds, Subgraph
from subgrounds.subgraph import SyntheticField
from subgrounds.pagination import ShallowStrategy

from .utils import remove_prefix
from .testing import validate_season_series
from .constants import ADDR_BEANSTALK


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


def get_last_row(row):
    return row.iloc[-1]


def adjust_precision(df, precisions):
    for col in df.columns:
        precision = precisions.get(col)
        if precision:
            df[col] = df[col] / precision


@dataclass
class QueryManager:

    sg: Subgrounds
    bs: Subgraph

    def query_seasons(self, extra_cols=None, **kwargs):
        """Returns dataframe of form 

        #   Column     Dtype         
        ---  ------     -----         
        0   season     int64         
        1   timestamp  datetime64[ns]

        You can add more columns to this df via extra_cols 
        """
        sg = self.sg
        bs = self.bs
        # Create sythetic field for timestamp
        bs.Season.timestamp = bs.Season.createdAt
        precisions = {
            "beans": 1e6
        }
        query_kwargs_default = {"orderBy": "season", "orderDirection": "asc"}
        query_kwargs = {**query_kwargs_default, **kwargs}
        extra_cols = extra_cols or []
        q = bs.Query.seasons(first=100000, **query_kwargs)
        df = sg.query_df(
            [
                q.season,
                q.timestamp,
                *[getattr(q, col) for col in extra_cols]
            ],
            pagination_strategy=ShallowStrategy
        )
        df = remove_prefix(df, "seasons_")
        adjust_precision(df, precisions)
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
                df.loc[i, 'timestamp'] = df.loc[2, 'timestamp'] - \
                    ((2-i) * pd.Timedelta(1, 'h'))
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
        q = bs.Query.rewards(orderBy="blockNumber",
                             orderDirection="asc", first=100000)
        df = sg.query_df(
            [
                q.season,
                q.reward_fertilized_beans,
            ],
            pagination_strategy=ShallowStrategy
        )
        df = remove_prefix(df, 'rewards_').sort_values(
            'season').reset_index(drop=True)
        szns = df.season.unique()
        missing_szns = [i for i in range(
            df.season.min(), df.season.max()) if i not in szns]
        df_missing_szns = pd.DataFrame(
            [{"season": i, "reward_fertilized_beans": 0} for i in missing_szns])
        df = pd.concat([df, df_missing_szns]).sort_values(
            'season').reset_index(drop=True)
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
        df['sprouts'] = ((df.supply * df.end_bpf).cumsum() -
                         df.sprouts_rinsable).ffill()
        df['rinsable_percent'] = df.sprouts_rinsable / \
            (df.sprouts_rinsable + df.sprouts).ffill()
        df['fertilizer_total'] = 77000000
        df['fertilizer_active'] = df.supply.cumsum().ffill()
        df['fertilizer_available'] = (
            df.fertilizer_total - df.fertilizer_active).ffill()
        # Remove duplicate season 6074, which is expected since we joined in values from fertilizer tokens
        df = df.sort_values(["season", "end_bpf"], ascending=[
                            True, False]).reset_index(drop=True)
        assert df.season.min() == 6074
        assert len(df.loc[df.season == 6074]) == 2
        df = df.iloc[1:, :]
        df = df[[
            'season', 'timestamp',
            'reward_fertilized_sprouts', 'sprouts_rinsable', 'sprouts', 'rinsable_percent',
            'fertilizer_total', 'fertilizer_active', 'fertilizer_available',
        ]]
        assert not df.isnull().values.any()
        validate_season_series(df)
        return df

    def query_field_daily_snapshots(self, fields=None):
        sg = self.sg
        bs = self.bs
        bs.FieldDailySnapshot.timestamp = bs.FieldDailySnapshot.createdAt
        precisions = {
            'id': None,
            'deltaHarvestablePods': 1e6,
            'deltaHarvestedPods': 1e6,
            'harvestablePods': 1e6,
            'harvestedPods': 1e6,
            'deltaPods': 1e6,
            'deltaSoil': 1e6,
            'numberOfSowers': None,
            'numberOfSows': None,
            'podIndex': 1e6,
            'podRate': None,
            'realRateOfReturn': None,
            'season': None,
            'sownBeans': 1e6,
            'timestamp': None,
            'numberOfSowers': None,
            'numberOfSows': None,
            'unharvestablePods': 1e6,
            'soil': 1e6,
            'sownBeans': 1e6,
            'temperature': None,
        }
        aggs = {
            'id': get_last_row,
            'deltaHarvestablePods': 'sum',
            'deltaHarvestedPods': 'sum',
            'harvestablePods': 'max',
            'harvestedPods': 'max',
            'deltaPods': 'sum',
            'deltaSoil': 'sum',
            'numberOfSowers': 'sum',
            'numberOfSows': 'sum',
            'podIndex': get_last_row,
            'podRate': get_last_row,
            'realRateOfReturn': get_last_row,
            'sownBeans': 'sum',
            'timestamp': "max",
            'numberOfSowers': get_last_row,
            'numberOfSows': get_last_row,
            'unharvestablePods': 'max',
            'soil': get_last_row,
            'sownBeans': 'max',
            'temperature': get_last_row,
        }
        fields = fields or list(precisions.keys())
        if "season" not in fields:
            fields.append("season")
        if "timestamp" not in fields:
            fields.append("timestamp")
        fs = bs.Query.fieldDailySnapshots(
            orderBy="createdAt",
            orderDirection="asc",
            first=10000,
            where={"field": ADDR_BEANSTALK}
        )
        df = sg.query_df(
            [getattr(fs, key) for key in fields],
            pagination_strategy=ShallowStrategy
        )
        df = remove_prefix(df, "fieldDailySnapshots_")
        adjust_precision(df, precisions)
        if "timestamp" in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        # Perform aggregations to deal with duplicate seasons (pauses in beanstalk)
        df = (
            df
            .sort_values("timestamp")
            .reset_index(drop=True)
            .groupby('season')
            .agg({k: v for k, v in aggs.items() if k in df.columns})
            .reset_index()
        )
        validate_season_series(df, allow_missing=True)
        return df

    def _silo_emissions_pre_replant(self) -> pd.DataFrame:
        """Temporary solution to subgraph not having silo emissions pre-replant 

        Data was downloaded from dune 
        """
        with (Path(__file__).parents[0] / Path('data/SupplyIncrease.json')).open('r') as f:
            records = json.loads(f.read())['records']
        return pd.DataFrame(records)

    def query_silo_daily_snapshots(self, fields=None):
        sg = self.sg
        bs = self.bs
        bs.SiloDailySnapshot.timestamp = bs.SiloDailySnapshot.createdAt
        precisions = {
            'deltaBeanMints': 1e6,
        }
        aggs = {
            'deltaBeanMints': 'sum',
        }
        fields = fields or list(precisions.keys())
        if "season" not in fields:
            fields.append("season")
        if "timestamp" not in fields:
            fields.append("timestamp")
        silo_snaps = bs.Query.siloDailySnapshots(
            orderBy="createdAt",
            orderDirection="asc",
            first=100000,
            where={
                "silo": ADDR_BEANSTALK,
                "season_gte": 6074  # TODO: remove this condition once silo history exists in subgraph
            }
        )
        df = sg.query_df(
            [getattr(silo_snaps, key) for key in fields],
            pagination_strategy=ShallowStrategy
        )
        df = remove_prefix(df, "siloDailySnapshots_")
        # Combine pre and post replant data (no seasons in common so outer join)
        df = df.merge(self._silo_emissions_pre_replant(), how="outer",)
        adjust_precision(df, precisions)
        # Perform aggregations to deal with duplicate seasons (pauses in beanstalk)
        df = (
            df
            .sort_values("timestamp")
            .reset_index()
            .groupby('season')
            .agg({k: v for k, v in aggs.items() if k in df.columns})
            .reset_index()
        )
        validate_season_series(df, allow_missing=True)
        return df
