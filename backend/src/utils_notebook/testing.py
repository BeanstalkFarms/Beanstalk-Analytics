import json 
from collections import Counter

import pandas as pd 


def validate_season_series(
    df: pd.DataFrame, 
    season_col_name: str = "season", 
    allow_missing: bool = False, 
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
        if count != count_expected and not (allow_missing and count == 0): 
            wrong_count.append({"season": s, "count": count})
    wrong_order = szns.values.tolist() != list(sorted(szns))
    issues = []
    if wrong_order: 
        issues.append("Order of series is not monotonically increasing\n")
    if missing and not allow_missing:
        issues.append(f"Missing: {json.dumps(missing, indent=4)}\n")
    if wrong_count: 
        issues.append(f"Incorrect Count: {json.dumps(wrong_count, indent=4)}\n")
    if issues: 
        raise ValueError(f"Season axis incorrect\n{''.join(issues)}")