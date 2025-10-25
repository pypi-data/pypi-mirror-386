def merge_dicts(d1, d2):
    return {**d1, **d2}

def invert_dict(d):
    return {v: k for k, v in d.items()}

def flatten_dict(d, parent_key="", sep="."):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def deep_get(d, path):
    keys = path.split(".")
    for key in keys:
        if isinstance(d, dict) and key in d:
            d = d[key]
        else:
            return None
    return d
def count_values(d):
    from collections import Counter
    return Counter(d.values())

def most_common_value(d):
    from collections import Counter
    c = Counter(d.values())
    return c.most_common(1)[0][0] if c else None

def remove_keys_with_none(d):
    return {k:v for k,v in d.items() if v is not None}

def compare_dicts(d1, d2):
    diff = {}
    for key in d1.keys() | d2.keys():
        if d1.get(key) != d2.get(key):
            diff[key] = (d1.get(key), d2.get(key))
    return diff

def merge_nested(d1, d2):
    result = d1.copy()
    for k, v in d2.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = merge_nested(result[k], v)
        else:
            result[k] = v
    return result
