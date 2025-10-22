import csv
from pathlib import Path
from .other import Conv_2dListTo1dList

# csv
def Get_csv2List(path :str|Path) -> list:
    with open(path, 'r') as csvfile:
        reader = csv.reader(csvfile)
        rows = [d for d in reader]
    data = []        
    for row in rows:
        tmp = []
        for d in row:
            if _is_type_int(d):
                tmp.append(int(d))
            elif _is_type_float(d):
                tmp.append(float(d))
            else:
                tmp.append(d)
        data.append(tmp)
    return data

# text
def Get_text2list(path :str|Path, delimiter :str) -> list:
    with open(path, 'r') as f:
        return f.read().split(delimiter)

def _is_type_int(target: str) -> bool:
    if not type(target) in [str, int]:
        return False
    try:
        int(target)
        return True
    except ValueError:
        return False

def _is_type_float(target: str) -> bool:
    if not type(target) in [str, float]:
        return False
    if _is_type_int(target):
           return False
       
    try:
        float(target)
        return True
    except ValueError:
        return False

# directory
def Get_dirList(path :str|Path) -> list:
    if type(path) is str:
        path = Path(path)
    return sorted([Path(f) for f in path.iterdir() if (path/f).is_dir()])

# file
def Get_fileList(path :str|Path) -> list:
    if type(path) is str:
        path = Path(path)
    return sorted([f for f in path.iterdir() if (path/f).is_file() and (not str(f).startswith("."))])

def Get_filepathList(path :str|Path):
    if type(path) is str:
        path = Path(path)
    return sorted([Path((path/f).absolute()) for f in path.iterdir() if (path/f).is_file() and (not str(f).startswith("."))])

def Get_uniqueList(targetList):
    return sorted(filter(lambda a: a != '',list(set(targetList))))

def Get_keysFromValue(d, val):
    return [k for k, v in d.items() if v == val]
