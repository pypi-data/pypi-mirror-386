def flatten_list(lst):
    result = []
    for i in lst:
        if isinstance(i, list):
            result.extend(flatten_list(i))
        else:
            result.append(i)
    return result

def remove_duplicates(lst):
    return list(dict.fromkeys(lst))

def chunk_list(lst, n):
    return [lst[i:i+n] for i in range(0, len(lst), n)]
def sum_nested(lst):
    total = 0
    for i in lst:
        if isinstance(i, list):
            total += sum_nested(i)
        else:
            total += i
    return total

def filter_by_type(lst, typ):
    return [x for x in lst if isinstance(x, typ)]

def rotate_list(lst, n):
    n = n % len(lst)
    return lst[-n:] + lst[:-n]

def find_duplicates(lst):
    seen = set()
    duplicates = set()
    for x in lst:
        if x in seen:
            duplicates.add(x)
        else:
            seen.add(x)
    return list(duplicates)
