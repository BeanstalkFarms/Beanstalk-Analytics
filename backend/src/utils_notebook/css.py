


def css_tooltip_timeseries_multi_colored(variables, colors): 
    css_lines = [
        "#vg-tooltip-element tr:nth-child(1) { font-weight: bold }", 
        "#vg-tooltip-element tr:nth-child(1) td:first-child { opacity: 0 }\n", 
    ]
    for i, m in enumerate(variables): 
        # i+2 bc css uses one based indexing and we also don't color timestamp (first element in tooltip)
        css_lines.append(
            "#vg-tooltip-element tr:nth-child(%d) td:first-child { color: %s; font-weight: bold; }\n" % (i+2, colors[m])
        )
    return css_lines