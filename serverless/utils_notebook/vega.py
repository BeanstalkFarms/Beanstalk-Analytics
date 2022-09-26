import json
import altair as alt 
from IPython.display import JSON
from deepdiff import DeepSearch
from deepdiff.path import _path_to_elements

from .utils import is_number


def condition_union(op_compare, op_join, values): 
    assert op_compare in ['==', '!=']
    assert op_join in ['|', '&']
    expr = f" {op_join} ".join([f"datum.variable {op_compare} '{v}'" for v in values])
    return expr 

def output_chart(c: alt.Chart): 
    return JSON(json.loads(c.to_json()))
    

def compute_width_paths(schema: dict): 
    """Determine all paths through the schema to properties that determine chart width 
    
    These will be used by the frontend to perform dynamic width re-sizing.
    """
    # ----------------------------------------------------------------------------
    # 1. Top level config 
    # https://vega.github.io/vega-lite/docs/spec.html#config
    
    # 1.1. Match top level config "continuousWidth". Value is always a number.
    m_view_cw = {
        k: v for k, v in 
        DeepSearch(schema, 'continuousWidth', verbose_level=2).get('matched_paths', {}).items() 
        if k in set([
            "root['config']['view']['continuousWidth']"
        ])
    }
    
    # 1.2. Match top level config "discreteWidth". Value is either number or object 
    m_view_dw = {
        k: v for k, v in 
        DeepSearch(schema, 'discreteWidth', verbose_level=2).get('matched_paths', {}).items() 
        if k in set([
            "root['config']['view']['discreteWidth']", 
            "root['config']['view']['discreteWidth']['step']",
        ])
    }
    if len(m_view_dw) == 2: 
        # One of the paths is a prefix of the other
        m_view_dw.remove("root['config']['view']['discreteWidth']")
        
    # 1.3 Match top level config "step"  
    m_view_step = {
        k: v for k, v in 
        DeepSearch(schema, 'step', verbose_level=2).get('matched_paths', {}).items() 
        if k in set([
            "root['config']['view']['step']"
        ])
    }

    # ----------------------------------------------------------------------------
    # 2. View level config 
    
    # 2.1. Match view level "width" mapping to a number  
    m_w = {
        k: v for k, v in 
        DeepSearch(schema, 'width', verbose_level=2).get('matched_paths', {}).items() 
        if k.endswith("['width']")
    } 
    
    # 2.2. Match view level "width" mapping to an object  
    m_w_step = {
        k: v for k, v in 
        DeepSearch(schema, 'step', verbose_level=2).get('matched_paths', {}).items()
        if k.endswith("['width']['step']")
    } 

    # ----------------------------------------------------------------------------
    # 3. Mark specific properties 

    # 3.1. Radius properties for arc marks 
    m_radius = {
        **{
            k: v for k, v in 
            DeepSearch(schema, "innerRadius", verbose_level=2).get('matched_paths', {}).items()
            if k.endswith("['innerRadius']")
        }, 
        **{
            k: v for k, v in 
            DeepSearch(schema, "outerRadius", verbose_level=2).get('matched_paths', {}).items()
            if k.endswith("['outerRadius']")
        }
    } 

    # ----------------------------------------------------------------------------
    # 4. Disallow certain types of autosize 
    if schema.get("autosize", {}).get("type", None) in ['fit', 'fit-x', 'fit-y']: 
        raise ValueError("autosize fit not allowed")
    
    # ----------------------------------------------------------------------------
    # 5. Combine all different path types together. Convert from string form 
    #    to list of attribute accesses. 

    wpaths = []

    for wpath_key, wpath_value in {
        **m_view_cw,
        **m_view_dw,
        **m_view_step,
        **m_w,
        **m_w_step,
    }.items(): 
        # Properties that directly control width have no multiplier 
        wpath = [list(e)[0] for e in _path_to_elements(wpath_key)]
        wpaths.append({"path": wpath[1:], "factor": 1, "value": wpath_value})

    for wpath_key, wpath_value in m_radius.items(): 
        # Properties that control the radius of marks for arc marks have a multiplier of .5 
        # This is because for every 1 pixel we want to decrease width, we should decrease 
        # the radius by .5 pixels. 
        wpath = [list(e)[0] for e in _path_to_elements(wpath_key)]
        wpaths.append({"path": wpath[1:], "factor": 3.33, "value": wpath_value})

    return wpaths 