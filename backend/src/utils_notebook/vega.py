import json
import builtins 
from functools import partial
from typing import Optional, List 

import altair as alt 
import pandas as pd 
from palettable.tableau import Tableau_20
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


def possibly_override(data = None, defaults = None, override = False):
    defaults = defaults or {}
    data = data or {} 
    # Mix by default, override optionally 
    return {**defaults, **data} if not override else data 


def chart(
    df: pd.DataFrame, 
    timestamp_col: str, 
    # metrics associated with left and right axes 
    lmetrics: List[str], 
    rmetrics: List[str] = None, 
    # strategy_fns to plot metrics on left and right axes 
    lstrategy = 'line', 
    rstrategy = 'line', 
    # mapping of strategy to stack layer order when rendering     
    lorder = None, 
    rorder = None, 
    # mapping of strategy to mark properties 
    lmark_kwargs = None, 
    rmark_kwargs = None, 
    # mapping of strategy to extra encodings 
    l_yscales = None, 
    r_yscales = None, 
    # Axis parameters 
    xaxis_kwargs = None, 
    xaxis_kwargs_override: bool = False, 
    yaxis_left_kwargs: dict = None, 
    yaxis_right_kwargs: dict = None, 
    # Chart parameters 
    title: str = '', 
    colors = None,      
    tooltip_formats = None, 
    tooltip_format_default: str = ",d", 
    tooltip_metrics = None, 
    dual_axes: bool = False, 
    show_exploit_rule: bool = True, 
    exploit_day: int = 17, # must be either 16 or 17
    width: int = 700, 
    hide_legend: bool = False, 
    selection_nearest: alt.selection = None, 
    create_selection: bool = True, 
    add_selection: bool = True, 
    return_selection: bool = False,     
    base_hook = None, 
): 
    """Creates a chart with a shared time axis and up to two y axes 
        
    Assumes that data is in long-wide format (i.e. df was processed with function wide_to_longwide)
    """
    rmetrics = rmetrics or []
    assert not set(lmetrics).intersection(set(rmetrics)), "Same metric on two axes"
    metrics = (lmetrics + rmetrics) if not tooltip_metrics else tooltip_metrics
    tooltip_formats = tooltip_formats or {}
    xaxis_kwargs = possibly_override(
        xaxis_kwargs, XAXIS_DEFAULTS, override=xaxis_kwargs_override
    )
    yaxis_left_kwargs = yaxis_left_kwargs or {}
    yaxis_right_kwargs = yaxis_right_kwargs or {}
    lmark_kwargs = lmark_kwargs or {} 
    rmark_kwargs = rmark_kwargs or {}
    l_yscales = l_yscales or {}
    r_yscales = r_yscales or {}
    # Selection for nearest point. We either use an existing instance passed in by the user 
    # or create a new instance. Using an existing instance allows a selection to be shared 
    # across charts, which can be useful for creating interactions between linked views 
    assert not (create_selection and selection_nearest), "Can't create new selection while specifying existing one" 
    if create_selection: 
        selection_nearest = alt.selection_single(
            fields=[timestamp_col], nearest=True, on='mouseover', empty='none', clear='mouseout'
        )
    
    # Color scale is shared by metrics, regardless of what axis they belong to. User can 
    # either specify the desired colors for each metric or let defaults be used. 
    color_scale = (
        alt.Scale(domain=metrics, range=[colors[m] for m in metrics])
        if colors else 
        alt.Scale(domain=metrics)
    )
    
    
    base = (
        alt.Chart(df)
        .transform_calculate(stack_order=stack_order_expr("variable", metrics))
        .encode(x=alt.X(f"{timestamp_col}:O", axis=alt.Axis(**xaxis_kwargs)))
        .properties(title=title, width=width)
    )
    if base_hook: 
        base = base_hook(base)
        
    cbase = (
        base
        .encode(
            color=alt.Color("variable:N", scale=color_scale, legend=None if hide_legend else alt.Legend(title=None)), 
            order=alt.Order('stack_order:Q', sort='ascending'),
        )
    )

    class Strategies: 

        @staticmethod
        def _get_encode_kwargs(yscale_kwargs):
            yscale = alt.Scale(**yscale_kwargs) if yscale_kwargs else None
            encode_kwargs = dict() if not yscale else dict(scale=yscale)
            return encode_kwargs

        @staticmethod
        def line(base, axis, mark_kwargs, yscale_kwargs):
            encode_kwargs = Strategies._get_encode_kwargs(yscale_kwargs)
            return (
                base 
                .mark_line(**mark_kwargs)
                .encode(y=alt.Y("value:Q", axis=axis, **encode_kwargs))
            )
        
        @staticmethod
        def point(base, axis, mark_kwargs, yscale_kwargs):
            encode_kwargs = Strategies._get_encode_kwargs(yscale_kwargs)
            return (
                base 
                .mark_point(**mark_kwargs)
                .encode(y=alt.Y("value:Q", axis=axis, **encode_kwargs))
            )
        
        @staticmethod
        def stack_area(base, axis, mark_kwargs, yscale_kwargs):
            encode_kwargs = Strategies._get_encode_kwargs(yscale_kwargs)
            return (
                base 
                .mark_area(**mark_kwargs)
                .encode(y=alt.Y("value:Q", axis=axis, **encode_kwargs))
            )
            
        @staticmethod
        def stack_bar(base, axis, mark_kwargs, yscale_kwargs):
            encode_kwargs = Strategies._get_encode_kwargs(yscale_kwargs)
            return (
                base 
                .mark_bar(**mark_kwargs)
                .encode(y=alt.Y("value:Q", axis=axis, **encode_kwargs))
            )

    strategy_fns = {
        "line": Strategies.line, 
        "point": Strategies.point, 
        "stack_area": Strategies.stack_area, 
        "stack_bar": Strategies.stack_bar,
    }
    
    left_wrapper = dict(chart=None)
    right_wrapper = dict(chart=None)
    chart_specs = [
        (lstrategy, lmetrics, yaxis_left_kwargs, lorder, lmark_kwargs, l_yscales, left_wrapper), 
    ]
    if rmetrics: 
        chart_specs.append(
            (rstrategy, rmetrics, yaxis_right_kwargs, rorder, rmark_kwargs, r_yscales, right_wrapper)
        )
    for strategy, smetrics, axis_kwargs, order, mark_kwargs, yscales, chart_wrapper in chart_specs:
        match type(strategy): 
            case builtins.str: 
                # Apply a single strategy to all metrics on this axis 
                strat_fn = strategy_fns[strategy]
                strat_mark_kwargs = mark_kwargs.get(strategy, {})
                strat_yscales = yscales.get(strategy, {})
                chart_wrapper['chart'] = strat_fn(
                    cbase.transform_filter(condition_union("==", "|", smetrics)),
                    alt.Axis(**axis_kwargs), 
                    strat_mark_kwargs, 
                    strat_yscales, 
                ) 
            case builtins.list: 
                # Apply strategies on a per-metric basis 
                assert len(strategy) == len(smetrics)
                df_strategy_metric = pd.DataFrame(dict(strategy=strategy, metrics=smetrics))
                layers = []
                order_default = {
                    "stack_area": 0, 
                    "stack_bar": 1,
                    "line": 2, 
                    "point": 3, 
                }
                order = order or order_default
                ax = alt.Axis(**axis_kwargs)
                for strategy, df_sm in sorted(
                    df_strategy_metric.groupby("strategy"), key=lambda e: order[e[0]]
                ): 
                    sub_metrics = df_sm.metrics.values.tolist()
                    strat_fn = strategy_fns[strategy]
                    strat_mark_kwargs = mark_kwargs.get(strategy, {})
                    strat_yscales = yscales.get(strategy, {})
                    layer = strat_fn(
                        cbase.transform_filter(condition_union("==", "|", sub_metrics)), 
                        ax, 
                        strat_mark_kwargs,
                        strat_yscales
                    ) 
                    layers.append(layer)
                chart_wrapper['chart'] = alt.layer(*layers)  
            case _: 
                raise ValueError(f"Invalid strategy {strategy}")
            
    left = left_wrapper['chart']
    right = right_wrapper['chart']

    tooltip_metrics = tooltip_metrics or metrics 
    nearest = (
        # selection captures nearest timestamp (for current mouse position) 
        # tooltip rendered uses this data point (pivoted, so we have all data for this timestamp) 
        base
        .transform_pivot('variable', value='value', groupby=[timestamp_col])
        .mark_rule(color="#878787")
        .encode(
            tooltip=(
                [alt.Tooltip(f'{timestamp_col}:O', timeUnit="yearmonthdate", title="date")] + 
                [alt.Tooltip(f'{m}:Q', format=tooltip_formats.get(m, tooltip_format_default)) for m in tooltip_metrics]
            ), 
            opacity=alt.condition(selection_nearest, alt.value(1), alt.value(0))
        )
    )
    if add_selection: 
        nearest = nearest.add_selection(selection_nearest)
    

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

    # Compose plot 
    if not rmetrics: 
        if show_exploit_rule: 
            c = left + rule_exploit + nearest
        else: 
            c = left + nearest
    else: 
        if show_exploit_rule: 
            # It matters that the rules are layered with right instead of left, not sure why. 
            # Parentheses are important in case where dual_axes is True 
            c = left + (right + rule_exploit + nearest)
        else: 
            # It matters that the rules are layered with right instead of left, not sure why. 
            # Parentheses are important in case where dual_axes is True 
            c = left + (right + nearest)
    if dual_axes: 
        assert rmetrics, "Can't have two axes if you didn't specify rmetrics" 
        c = (
            c
            .resolve_scale(y="independent")
            .resolve_axis(y="independent")
        )
    return c if not return_selection else (c, selection_nearest)


def chart_address_value_table(
    df: pd.DataFrame, 
    value_field: str, 
    nrows=15
):
    radio_sort_dir = alt.binding_radio(name="Sort Direction:", options=['asc', 'desc'])
    slider = alt.binding_range(min=1, max=len(df) - nrows, step=1, name='Scroll Offset:')
    select_scroll = alt.selection_single(
        name="scroller", fields=['offset'], bind=slider, init={'offset': 1}
    )
    select_radio_sort_dir = alt.selection_single(
        name="sortdir", fields=["sort_dir"], bind=radio_sort_dir, init={"sort_dir": "desc"}
    )

    table_base = (
        alt.Chart(df)
        .transform_joinaggregate(rc="count(*)")
        .transform_window(sort=[{"field": value_field}], frame=[None, 0], sort_field="row_number(*)")
        .transform_calculate(sort_num="sortdir.sort_dir[0] === 'asc' ? datum.sort_field : (datum.rc - datum.sort_field + 1)")
        .transform_fold(['address', value_field])
        .transform_filter(
            f"""
            datum.sort_num >= parseInt(scroller.offset)
            && datum.sort_num < (parseInt(scroller.offset) + {nrows})
            """
        )
        .encode(
            x=alt.X(
                "key:N", 
                axis=alt.Axis(
                    orient="top", 
                    labelAngle=0, 
                    title=None, 
                    domain=False, 
                    ticks=False, 
                    labelFontWeight=600, 
                    labelFontSize=12
                ), 
            ),
            y=alt.Y("sort_num:O", axis=None), 
        )
    ) 

    table_rect = (
        table_base
        .mark_rect(stroke="black")
        .encode(
            color=alt.condition("datum.sort_num % 2 === 0", alt.value("#e3e3e3"), alt.value("#ffffff")), 
            href="href"
        )
    ) 
    table_text = (
        table_base
        .transform_calculate(
            # label="datum.value"
            label=f"""
            datum.key === 'address' ? datum.value : 
            datum.key === '{value_field}' ? format(datum.value, ',d') : 
            datum.value 
            """
        )
        .mark_text()
        .encode(text='label:N')
    ) 

    c = (
        alt.layer(table_rect, table_text)
        .add_selection(select_scroll, select_radio_sort_dir)
        .properties(width=750)
    )
    return c 


def string_pad_int(value, fixed_length=3):
    import math 
    if value == 0: 
        return '0' * fixed_length
    return (fixed_length - math.floor(math.log10(value)) - 1) * '0' + str(value)


def chart_bin_count_value_aggregate(
    df: pd.DataFrame, 
    value_field: str, 
    breakpoints: List[float], 
    width: int = 500, 
): 
    def classify(order, value):
        for i in range(1, len(breakpoints)):
            b0 = breakpoints[i-1] 
            b1 = breakpoints[i]
            if b0 <= value < b1: 
                if order: 
                    return i 
                else: 
                    if b1 == float('inf'): 
                        return f"{string_pad_int(i)}.{int(b0):,}+ {value_field}"
                    else: 
                        return f"{string_pad_int(i)}.{int(b0):,} - {int(b1):,} {value_field}"
            
    # pre-processing 
    df = df.groupby(by="address").sum().reset_index()
    df['class'] = df[value_field].apply(partial(classify, False))
    df = df.sort_values(value_field).reset_index(drop=True)
    df = df.dropna(subset="class")
    
    # Get the count of pod holders by classification 
    df_count_class = (
        df[['class', value_field]]
        .groupby('class').count()
        .reset_index()
        .rename(columns={value_field: "count"})
    )
    # Sum value held by each class of holders 
    df_class_value = (
        df[['class', value_field]]
        .groupby('class').sum()
        .reset_index()
    )

    color_domain = list(sorted(df_count_class['class'].unique()))
    color_range = [Tableau_20.hex_colors[i] for i in range(len(color_domain))]
        
    x = alt.X("class:O", axis=alt.Axis(title="Classification", labelExpr="split(datum.value, '.')[1]"))
    color = alt.Color(
        "class:O", 
        legend=None, 
        scale=alt.Scale(domain=color_domain, range=color_range)
    )
    selection = alt.selection_single(
        encodings=['x'], nearest=True, on='mouseover', empty='none', clear='mouseout'
    )

    # Chart count class 
    s = value_field.capitalize()
    base_count_class = (
        alt.Chart(
            df_count_class, 
            width=width, 
            title=f"Count Addresses by Classification"
        )
        .encode(x=x, y=alt.Y("count:Q", axis=alt.Axis(title="Unique Addresses")))
    )
    chart_count_class_histogram = (
        base_count_class
        .encode(
            color=color, 
            stroke=alt.condition(selection, alt.value("black"), alt.value("white"))
        )
        .mark_bar()
    )
    chart_count_class_text = (
        base_count_class
        .encode(
            text=alt.Text("count:Q", format=",d"),
            stroke=alt.value("black"), 
            strokeWidth=alt.condition(selection, alt.value(.6), alt.value(0)),
            color=alt.value("black")
        )
        .mark_text(color='black', dy=-10)
    )

    # Chart class value 
    base_class_value = (
        alt.Chart(df_class_value, width=width, title=f"Cumulative {s} by Classification")
        .encode(x=x, y=alt.Y(f"{value_field}:Q", axis=alt.Axis(title=s)))
    )
    chart_class_value_histogram = (
        base_class_value
        .encode(
            color=color,
            stroke=alt.condition(selection, alt.value("black"), alt.value("white")),
        )
        .mark_bar()
    )
    chart_class_value_text = (
        base_class_value
        .encode(
            text=alt.Text(f"{value_field}:Q", format=".3s"),
            stroke=alt.value("black"), 
            strokeWidth=alt.condition(selection, alt.value(.6), alt.value(0)),
        )
        .mark_text(color='black', dy=-10)
    )

    c = (
        alt.hconcat(
            alt.layer(chart_count_class_histogram, chart_count_class_text).add_selection(selection), 
            alt.layer(chart_class_value_histogram, chart_class_value_text).add_selection(selection), 
        )
    )
    return c 
