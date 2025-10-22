import scipy.stats as ss
import statistics

class _data_group:
    def __init__(self, group_name, data_array):
        self.group_name = group_name
        self.data_array = data_array
    
    @property
    def name(self):
        return self.group_name
    
    @property
    def array(self):
        return self.data_array

def calc_quantiles(data: list|tuple) -> list:
    return statistics.quantiles(data, n=4)

def calc_mean(data: list|tuple) -> int|float:
    return statistics.mean(data)

def calc_median(data: list|tuple) -> int|float:
    return statistics.median(data)

def calc_stdev(data: list|tuple) -> float:
    return statistics.stdev(data)

def test_shapiroWilk(data: list, level: float = 0.05) -> dict:
    result = {"N":len(data)}
    result["stat"], result["p_val"] = [float(d) for d in ss.shapiro(data)]
    if result["p_val"] < level:
        result["level"] = f"*p<{level}"
    else:
        result["level"] = "n.s."
    
    print("* shapiro-Wilk test")
    print("--------------------------------")
    print(f"# data : {data}\n")
    print("--------------------------------")
    print("# result :")
    print(f"#\t データ数（N） : {len(data)}")
    print(f"#\t 検定統計量（W） : {result['stat'] :.2f}")
    print(f"#\t p値（p） : {result['p_val']:.2f} {result['level']}")
    print("--------------------------------")
    
    return result

def test_wilcoxon_signedRank(group1: list, group2: list, level: float = 0.05) -> dict:
    
    if not len(group1) == len(group2):
        raise ValueError(f"The lengths of the given sequences do not match. (group1:{len(group1)}, group2:{len(group2)})")
    
    result = {"group1":{},"group2":{}}
    
    result["group1"]["q1"],result["group1"]["q2"],result["group1"]["q3"] = calc_quantiles(group1, n=4)
    result["group2"]["q1"],result["group2"]["q2"],result["group2"]["q3"] = calc_quantiles(group2, n=4)
    
    result["N"] = len(group1)
    
    result["stat"], result["p_val"] = [float(d) for d in ss.wilcoxon(group1, group2)]
    print(result["p_val"])
    if result["p_val"] < level:
        result["level"] = f"*p<{level}"
    else:
        result["level"] = "n.s."

    print("* Wilcoxon Signed-Rank test")
    print("--------------------------------")
    print(f"# group1")
    print(f"#\t data : {group1}")
    print(f"#\t Median : {result['group1']['q2']}")
    print(f"#\t Q1, Q2, Q3 : {result['group1']['q1']}, {result['group1']['q2']}, {result['group1']['q3']}")
    print(f"# group2")
    print(f"#\t data : {group2}")
    print(f"#\t Median : {result['group2']['q2']}")
    print(f"#\t Q1, Q2, Q3 : {result['group2']['q1']}, {result['group2']['q2']}, {result['group2']['q3']}")
    print("--------------------------------")
    print("# result :")
    print(f"#\t データ数（N） : {len(group1)}")
    print(f"#\t 検定統計量（W） : {result['stat'] :.2f}")
    print(f"#\t p値（p） : {result['p_val']:.2f} {result['level']}")
    print("--------------------------------")
    
    return result

# def test_friedman(*data: list) -> dict:
#     if len(data) < 3:
#         raise TypeError(f"test_friedman() takes 3 or more argument but {len(data)} were given")
#     result = {}
    # for d in data:
        