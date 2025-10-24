import re

def normalize_brackets(text: str) -> str:
    """ normalize brackets.
    """
    
    bracket_map = {
        "「": '"', "」": '"',
        "『": '"', "』": '"',
        "【": "[", "】": "]",
        "《": "<", "》": ">",
        "〈": "<", "〉": ">",
        "｛": "{", "｝": "}",
        "〔": "(", "〕": ")",
    }
    pattern = "[" + "".join(bracket_map.keys()) + "]"
    return re.sub(pattern, lambda m: bracket_map[m.group()], text)


def split_list(lst: list, chunk_size: int) -> list[list]:
    """ split list with given chunk_size.
    """
    
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]