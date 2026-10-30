"""分数查询。"""


def get_score(scores: dict, name: str):
    """返回 name 的分数；名字不存在时返回 None。"""
    return scores[name]
