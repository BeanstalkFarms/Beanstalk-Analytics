import json 
from collections import Counter

import pandas as pd 


def assert_complete_season_axis(
    df: pd.DataFrame, 
    season_col_name: str = "season", 
    count_expected: int = 1, 
): 
    """Asserts that the season series within a df is complete (no gaps)

    Can handle both wide and long form data through count_expected parameter. 
    - Should be >1 for long form data. 
    - Should be 1 for wide form data. 
    """
    szns = df[season_col_name]
    szn_min = szns.min()
    szn_max = szns.max()
    counter = Counter(szns.values.tolist())
    missing = []
    wrong_count = []
    for s in range(szn_min, szn_max): 
        count = counter[s]
        if count == 0: 
            missing.append(s)
        if count != count_expected: 
            wrong_count.append({"season": s, "count": count})
    wrong_order = szns.values.tolist() != list(sorted(szns))
    if missing or wrong_count or wrong_order: 
        issues = []
        if wrong_order: 
            issues.append("Order of series is not monotonically increasing\n")
        if missing:
            issues.append(f"Missing: {json.dumps(missing, indent=4)}\n")
        if wrong_count: 
            issues.append(f"Incorrect Count: {json.dumps(wrong_count, indent=4)}\n")
        raise ValueError(f"Season axis incorrect\n{''.join(issues)}")
