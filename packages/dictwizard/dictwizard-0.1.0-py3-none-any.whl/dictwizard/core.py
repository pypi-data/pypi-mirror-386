def merge_dicts(d1, d2):
    """İki dictionary-i birləşdirir."""
    return {**d1, **d2}

def invert_dict(d):
    """Açar və dəyərləri dəyişdirir."""
    return {v: k for k, v in d.items()}

def filter_dict(d, keys):
    """Yalnız seçilmiş açarları saxlayır."""
    return {k: v for k, v in d.items() if k in keys}

def flatten_dict(d, parent_key="", sep="."):
    """Nested dictionary-ləri tək səviyyəyə salır."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def deep_get(d, path):
    """'a.b.c' formasında dərin açarlara giriş."""
    keys = path.split(".")
    for key in keys:
        if isinstance(d, dict) and key in d:
            d = d[key]
        else:
            return None
    return d

def deep_update(d, path, value):
    """'a.b.c' formasında dərin açara yeni dəyər verir."""
    keys = path.split(".")
    current = d
    for key in keys[:-1]:
        current = current.setdefault(key, {})
    current[keys[-1]] = value
    return d

def dict_diff(d1, d2):
    """İki dict arasındakı fərqləri qaytarır."""
    diff = {}
    for key in d1.keys() | d2.keys():
        if d1.get(key) != d2.get(key):
            diff[key] = (d1.get(key), d2.get(key))
    return diff
