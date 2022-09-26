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
    m_view_cw = DeepSearch(schema, 'continuousWidth', verbose_level=2).get('matched_paths', {})
    m_view_cw = set(m_view_cw).intersection(set([
        "root['config']['view']['continuousWidth']"
    ]))
    
    # 1.2. Match top level config "discreteWidth". Value is either number or object 
    m_view_dw = DeepSearch(schema, 'discreteWidth', verbose_level=2).get('matched_paths', {})
    m_view_dw = set(m_view_dw).intersection(set([
        "root['config']['view']['discreteWidth']", 
        "root['config']['view']['discreteWidth']['step']",
    ]))
    if len(m_view_cw) == 2: 
        # One of the paths is a prefix of the other
        m_view_dw.remove("root['config']['view']['discreteWidth']")
        
    # 1.3 Match top level config "step"  
    m_view_step = DeepSearch(schema, 'step', verbose_level=2).get('matched_paths', {})
    m_view_step = set(m_view_step).intersection(set([
        "root['config']['view']['step']"
    ]))
    # ----------------------------------------------------------------------------
    # 2. View level config 
    
    # 2.1. Match view level "width" mapping to a number  
    m_w = DeepSearch(schema, 'width', verbose_level=2).get('matched_paths', {})
    keep_keys = set()
    for p, v in m_w.items(): 
        if p.endswith("['width']"): 
            assert v != "container" 
            assert is_number(v) 
            keep_keys.add(p) 
    m_w = {p for p, v in m_w.items() if p in keep_keys} 
    
    # 2.2. Match view level "width" mapping to an object  
    m_w_step = DeepSearch(schema, 'step', verbose_level=2).get('matched_paths', {})
    keep_keys = set()
    for p, v in m_w_step.items(): 
        if p.endswith("['width']['step']"): 
            assert is_number(v) 
            keep_keys.add(p) 
    m_w_step = {p for p, v in m_w_step.items() if p in keep_keys} 
    # ----------------------------------------------------------------------------
    # 3. Mark specific properties 

    # 3.1. Radius properties for arc marks 
    m_radius = set() 
    for key in ["innerRadius", "outerRadius"]: 
        m = DeepSearch(schema, key, verbose_level=2).get('matched_paths', {})
        for k, v in m.items(): 
            if not k.endswith(f"['{key}']") or not float(v): 
                raise ValueError(f"Value for mark property {k} must be number")
        m_radius = m_radius.union(list(m.keys())) 

    # ----------------------------------------------------------------------------
    # 4. Disallow certain types of autosize 
    if schema.get("autosize", {}).get("type", None) in ['fit', 'fit-x', 'fit-y']: 
        raise ValueError("autosize fit not allowed")
    
    # ----------------------------------------------------------------------------
    # 5. Combine all different path types together. Convert from string form 
    #    to list of attribute accesses. 
    wpaths = []
    for wpath_str in (
        m_view_cw
        .union(m_view_dw)
        .union(m_view_step)
        .union(m_w) 
        .union(m_w_step)
    ): 
        # Properties that directly control width have no multiplier 
        wpath = [list(e)[0] for e in _path_to_elements(wpath_str)]
        wpaths.append({"path": wpath[1:], "factor": 1})
    for wpath_str in m_radius: 
        # Properties that control the radius of marks for arc marks have a multiplier of .5 
        # This is because for every 1 pixel we want to decrease width, we should decrease 
        # the radius by .5 pixels. 
        wpath = [list(e)[0] for e in _path_to_elements(wpath_str)]
        wpaths.append({"path": wpath[1:], "factor": 2})

    return wpaths 