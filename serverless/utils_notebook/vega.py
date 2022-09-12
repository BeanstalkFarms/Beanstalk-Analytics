import json
import altair as alt 
from IPython.display import JSON

def condition_union(op_compare, op_join, values): 
    assert op_compare in ['==', '!=']
    assert op_join in ['|', '&']
    expr = f" {op_join} ".join([f"datum.variable {op_compare} '{v}'" for v in values])
    return expr 

def output_chart(c: alt.Chart): 
    return JSON(json.loads(c.to_json()))