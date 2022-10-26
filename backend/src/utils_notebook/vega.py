import json
from typing import Optional, List 

import altair as alt 
import pandas as pd 
from IPython.display import JSON, display, HTML 
from deepdiff import DeepSearch
from deepdiff.path import _path_to_elements


def condition_union(op_compare, op_join, values, key_var="variable"): 
    assert op_compare in ['==', '!=']
    assert op_join in ['|', '&']
    expr = f" {op_join} ".join([f"datum['{key_var}'] {op_compare} '{v}'" for v in values])
    return expr 


def stack_order_expr(col_var, col_values):
    expr_str = (
        ' '.join(
            [
                f"datum['{col_var}'] === '{m}' ? {i} : " 
                for i, m in enumerate(col_values)
            ]
        ) 
        + str(len(col_values))
    ) 
    return expr_str


def wide_to_longwide(
    df: pd.DataFrame, 
    join_col: str, 
    id_cols: List[str], 
    value_cols: List[str], 
    sort_col: Optional[str] = None
): 
    """Vega specific data transformation, useful for stacked area plot 
    
    1. Convert the df from wide form to long form via pd.DataFrame.melt.
    2. Join the columns that we converted to values when melting back on to the resulting data frame.
    
    This ensures that each row of the dataframe has columns storing all values for the row's unique 
    combination of values from id_cols. 
    
    This data representation is kinda wack but it's the only way to do nice tooltips for stacked area 
    plots in vega-lite so here we are. 
    """
    assert join_col in id_cols 
    df = (
        df
        .melt(id_vars=id_cols, value_vars=value_cols)
        .merge(df.loc[:,value_cols + [join_col]], on=join_col)
    ) 
    if sort_col: 
        df = df.sort_values(sort_col) 
    return df 


def apply_css(css): 
    """Applies css stylesheet to current cell output.
    
    Must be called prior to outputting display object in notebook cell. 
    Useful for applying custom styles to vega-lite charts.  
    """
    display(HTML(f"<style>{css}</style>"))
    

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


def output_chart(c: alt.Chart, css: Optional[str] = None): 
    """Applies css stylesheet to current cell output.
    
    Can be used prior to displaying vega-lite charts for custom styling. 
    """
    spec = json.loads(c.to_json())
    return JSON({
        "spec": spec, 
        "width_paths": compute_width_paths(spec),
        "css": css, 
    })


XAXIS_DEFAULTS = dict(
    formatType="time", 
    ticks=False, 
    labelExpr="timeFormat(toDate(datum.value), '%b %e, %Y')", 
    labelOverlap=True, 
    labelSeparation=50, 
    labelPadding=5, 
    title='Date', 
    labelAngle=0, 
)



def chart_stack_area_overlay_line_timeseries(
    df: pd.DataFrame, 
    timestamp_col: str, 
    metrics,
    area_metrics,
    title: str, 
    xaxis_kwargs = None, 
    xaxis_kwargs_override: bool = False, 
    yaxis_area_kwargs: dict = None, 
    yaxis_area_kwargs_override: bool = False, 
    yaxis_line_kwargs: dict = None, 
    yaxis_line_kwargs_override: bool = False, 
    color_map = None,      
    tooltip_formats = None, 
    separate_y_axes: bool = False, 
    show_exploit_rule: bool = True, 
    exploit_day: int = 17, # must be either 16 or 17
    width: int = 700, 
): 
    """Creates a stacked area plot with lines overlaid on top 
    
    Assumes that data is in long-wide format (i.e. df was processed with function wide_to_longwide)
    """
    tooltip_formats = tooltip_formats or {}

    # x axis kwargs 
    xaxis_kwargs = xaxis_kwargs or {}
    xaxis_kwargs = (
        {**XAXIS_DEFAULTS, **(xaxis_kwargs or {})} 
        if not xaxis_kwargs_override else 
        xaxis_kwargs 
    ) 
    # y axis area kwargs 
    yaxis_area_kwargs_default = dict() 
    yaxis_area_kwargs = yaxis_area_kwargs or {}
    yaxis_area_kwargs = (
        {**yaxis_area_kwargs_default, **(yaxis_area_kwargs or {})} 
        if not yaxis_area_kwargs_override else 
        yaxis_area_kwargs 
    ) 
    # y axis line kwargs 
    yaxis_line_kwargs_default = dict() 
    yaxis_line_kwargs = yaxis_line_kwargs or {}
    yaxis_line_kwargs = (
        {**yaxis_line_kwargs_default, **(yaxis_line_kwargs or {})} 
        if not yaxis_line_kwargs_override else 
        yaxis_line_kwargs 
    ) 
    
    # construct axes 
    xaxis = alt.Axis(**xaxis_kwargs)
    yaxis_area = alt.Axis(**yaxis_area_kwargs)
    yaxis_line = alt.Axis(**yaxis_line_kwargs) 
    
    # Shared x encoding channel (lines and area on same time axis) 
    x = alt.X(f"{timestamp_col}:O", axis=xaxis)

    # Optional custom color scale 
    if color_map: 
        color_scale = alt.Scale(domain=metrics, range=[color_map[m] for m in metrics])
    else: 
        color_scale = alt.Scale(domain=metrics)
        
    # Tooltips
    tooltips = (
        [alt.Tooltip(f'{timestamp_col}:O', timeUnit="yearmonthdate", title="date")] + 
        [alt.Tooltip(f'{m}:Q', format=tooltip_formats.get(m, ",d")) for m in metrics]
    )
    
    base = (
        alt.Chart(df)
        .encode(x=x)
        .properties(title=title, width=width)
    )
    
    assert exploit_day in [16, 17]
    rule_exploit = (
        # selection captures nearest timestamp (for current mouse position) 
        # tooltip rendered uses this data point (pivoted, so we have all data for this timestamp) 
        base
        .transform_pivot('variable', value='value', groupby=[timestamp_col])
        .transform_filter(f"""
            year(datum['{timestamp_col}']) === 2022 && 
            month(datum['{timestamp_col}']) === 3 && 
            date(datum['{timestamp_col}']) === {exploit_day} 
        """) # && warn(datetime(datum['{timestamp_col}']))
        .mark_rule(opacity=1, color='#474440', strokeDash=[2.5,1])
    )
        
    cbase = (
        base
        # Ensures that stacked area is in same order as input 'metrics' 
        .transform_calculate(stack_order=stack_order_expr("variable", metrics))
        .encode(
            color=alt.Color("variable:N", scale=color_scale, legend=alt.Legend(title=None)), 
            order=alt.Order('stack_order:Q', sort='ascending'),
        )
    )

    area = (
        cbase
        .transform_filter(condition_union("==", "|", area_metrics))
        .transform_calculate(sort_col=stack_order_expr("variable", metrics))
        .mark_area(point='transparent')
        .encode(y=alt.Y("value:Q", axis=yaxis_area), tooltip=tooltips)
    )

    line = (
        cbase
        .transform_filter(condition_union("!=", "&", area_metrics))
        .mark_line()
        .encode(y=alt.Y("value:Q", axis=yaxis_line))
    )
    
    if show_exploit_rule: 
        # Rule doesn't show up unless layered with line or area base. 
        c = area + alt.layer(line, rule_exploit)
    else: 
        c = area + line 
    if separate_y_axes: 
        c = (
            c
            .resolve_scale(y="independent")
            .resolve_axis(y="independent")
        )
    return c 