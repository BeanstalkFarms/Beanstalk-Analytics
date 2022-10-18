import os 
from typing import Tuple, Dict, List

from subgrounds.subgrounds import Subgrounds, Subgraph
from pandas import DataFrame
from IPython.display import display 
from IPython.core.display import HTML

from .constants import ADDRS_SILO_TOKENS, DECIMALS_SILO_TOKENS


def is_number(v): 
    return type(v) == int or type(v) == float 

def dict_invert(d: Dict): 
    """Inverts the key value mapping of a dict."""
    return {v: k for k, v in d.items()}

def remove_keys(d: Dict, rm_keys): 
    """Returns dict with all keys in rm_keys removed."""
    return {k: v for k, v in d.items() if k not in rm_keys}

def all_attrs(obj, ignore_keys=None): 
    """Retrieves list of all non private / builtin attributes of an object.
    
    Useful for getting all properties of a subgrounds query entity, rather 
    than specifying which subset of data properties to query for. 
    """
    ignore_keys = ignore_keys or []
    return [
        getattr(obj, attr) for attr in dir(obj)
        if not (
            attr.startswith("_") or attr.startswith("__") or attr in ignore_keys
        )
    ]

def filter_by_prefix(df: DataFrame, prefix: str): 
    # Remove all columns that don't start with prefix 
    return df.drop([col for col in df.columns if not col.startswith(prefix)])

def remove_prefix(df: DataFrame, prefix: str):
    # Remove a prefix from all columns 
    cols = [c for c in df.columns]
    for i, c in enumerate(cols): 
        if c.startswith(prefix): 
            cols[i] = c[len(prefix):]
    df.columns = cols 
    return df 

def remove_prefixes(df: DataFrame, prefixes: List[str]):
    for p in prefixes: 
        df = remove_prefix(df, p)
    return df 


def add_silo_token_name_adjust_precision(df, token_col, token_amount_cols, token_name_col="silo_token_name"):
    """Creates a column for silo token name by performing a lookup based on address. 
    Modifies the amount related field for each silo token by a token specific precision. 
    """
    token_names = dict_invert(ADDRS_SILO_TOKENS) 
    df[token_name_col] = df[token_col].apply(lambda token_addr: token_names[token_addr]) 
    for token_name in ADDRS_SILO_TOKENS:
        row_mask = df[token_name_col] == token_name
        df.loc[row_mask, token_amount_cols] = df.loc[row_mask, token_amount_cols] / DECIMALS_SILO_TOKENS[token_name]


def ddf(df: DataFrame, **kwargs): 
    # jupyter notebook dataframe plotting utility 
    kwargs = kwargs or dict(
        float_format=lambda v: f"{round(v, 3)}",
        show_dimensions=True
    )
    return display(HTML(df.to_html(**kwargs)))

def load_subgraph(subgraph_host=None, subgraph_type=None) -> Tuple[Subgrounds, Subgraph]: 
    """Helper for initializing subgrounds and subgraph objects. 
    
    TODO: arg to select from different subgraph url's
    """
    sg = Subgrounds()
    bs: Subgraph = sg.load_subgraph(os.environ['SUBGRAPH_URL'])
    return sg, bs 


