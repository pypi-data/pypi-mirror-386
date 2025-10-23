import pandas as pd


def upsert(df: pd.DataFrame, *primary_keys: str, record: dict, verify_integrity=False) -> pd.DataFrame:
    original_index = df.index.names if isinstance(df.index, pd.MultiIndex) else [df.index.name]
    original_index = [col for col in original_index if col is not None]

    if original_index: df = df.reset_index()

    condition = pd.Series(True, index=df.index)
    for key in primary_keys:
        if key not in df.columns:
            raise KeyError(f"Primary key '{key}' not found in DataFrame columns")
        condition &= (df[key] == record[key])

    match_indices = df[condition].index

    if not match_indices.empty:
        for col, value in record.items():
            if col in df.columns:
                df.loc[match_indices, col] = value
            else:
                df[col] = None
                df.loc[match_indices, col] = value
    else:
        new_row = pd.DataFrame([record])
        df = pd.concat([df, new_row], ignore_index=True)

    if original_index:
        df = df.set_index(original_index, verify_integrity=verify_integrity)

    return df
