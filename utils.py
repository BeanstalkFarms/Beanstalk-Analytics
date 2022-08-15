import pandas as pd 
from pandas import DataFrame
from IPython.display import display 
from IPython.core.display import HTML

def all_attrs(value, ignore_keys=None): 
    # Retrieves all non private / builtin attributes of an object as a list 
    # Useful for querying all entity properties for subgrounds field paths 
    ignore_keys = ignore_keys or []
    attrs = []
    for key in dir(value): 
        if not (key.startswith("_") or key.startswith("__") or key in ignore_keys): 
            attrs.append(getattr(value, key))
    return attrs

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


def ddf(df: DataFrame, **kwargs): 
    # jupyter notebook dataframe plotting utility 
    kwargs = kwargs or dict(
        float_format=lambda v: f"{round(v, 3)}",
        show_dimensions=True
    )
    return display(HTML(df.to_html(**kwargs)))