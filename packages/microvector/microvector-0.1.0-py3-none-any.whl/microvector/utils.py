import logging
from typing import Any, Union, Literal


logging.basicConfig(
    format="%(levelname)-1s [%(filename)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d:%H:%M:%S",
    level=logging.INFO,
    force=True,
)

logger = logging.getLogger(__name__)

SimilarityMetrics = Literal["dot", "cosine", "euclidean", "derrida"]


def stringify_nonstring_target_values(
    collection: Union[list[Any], dict[Any, Any], str, int, float, bool], key: str
) -> Union[list[Any], dict[Any, Any], str, int, float, bool]:
    """
    Recursively convert the value of any key in the dictionary to a string.

    Example:

    result = stringify_nonstring_target_values([
        {"header": "Another header", "is_good": False, "deep": {"deep_key": 1}},
        {"header": "Third header", "is_good": True, "deep": {"deep_key": 2}},
    ]

    print(result)
    [
        {"header": "Another header", "is_good": "False", "deep": {"deep_key": "1"}},
        {"header": "Third header", "is_good": "True", "deep": {"deep_key": "2"}},
    ]
    """
    # leaf node
    if isinstance(collection, (str, int, float, bool)):
        return collection
    elif isinstance(collection, dict):
        # check if the key is in the dictionary
        if key in collection and isinstance(collection[key], (int, float, bool)):
            # convert the value to a string
            collection[key] = str(collection[key])
        # recursively call the function for each value in the dictionary
        else:
            for k, v in collection.items():
                collection[k] = stringify_nonstring_target_values(v, key)
    else:
        # recursively call the function for each item in the list
        for i in range(len(collection)):
            collection[i] = stringify_nonstring_target_values(collection[i], key)
    return collection
