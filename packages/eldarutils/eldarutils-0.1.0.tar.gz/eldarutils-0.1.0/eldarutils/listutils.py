from collections import Counter

def remove_duplicates(lst):
    """Return list without duplicate elements."""
    return list(dict.fromkeys(lst))

def flatten(lst):
    """Flatten a nested list."""
    flat = []
    for item in lst:
        if isinstance(item, list):
            flat.extend(flatten(item))
        else:
            flat.append(item)
    return flat

def chunk(lst, size):
    """Split list into chunks of given size."""
    return [lst[i:i + size] for i in range(0, len(lst), size)]

def most_frequent(lst):
    """Return the most frequent element in the list."""
    return Counter(lst).most_common(1)[0][0] if lst else None

def least_frequent(lst):
    """Return the least frequent element in the list."""
    return Counter(lst).most_common()[-1][0] if lst else None

def unique_sorted(lst):
    """Return sorted list without duplicates."""
    return sorted(set(lst))

def split_by_type(lst):
    """Separate list elements by their type."""
    result = {}
    for item in lst:
        t = type(item).__name__
        result.setdefault(t, []).append(item)
    return result

def rotate(lst, n):
    """Rotate list n steps to the right."""
    if not lst:
        return []
    n = n % len(lst)
    return lst[-n:] + lst[:-n]

def intersection(lst1, lst2):
    """Return common elements between two lists."""
    return list(set(lst1) & set(lst2))

def difference(lst1, lst2):
    """Return elements in lst1 not in lst2."""
    return list(set(lst1) - set(lst2))
