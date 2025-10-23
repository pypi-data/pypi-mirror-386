"""Generic utils for interacting with Afero IoT API or the responses."""

from typing import Any


def percentage_to_ordered_list_item[_T](ordered_list: list[_T], percentage: int) -> _T:
    """Find the item that most closely matches the percentage in an ordered list.

    When using this utility for fan speeds, do not include "off"

    Given the list: ["low", "medium", "high", "very_high"], this
    function will return the following when the item is passed
    in:

        1-25: low
        26-50: medium
        51-75: high
        76-100: very_high
    """
    if not (list_len := len(ordered_list)):
        raise ValueError("The ordered list is empty")

    for offset, speed in enumerate(ordered_list):
        list_position = offset + 1
        upper_bound = (list_position * 100) // list_len
        if percentage <= upper_bound:
            return speed

    return ordered_list[-1]


def ordered_list_item_to_percentage[_T](ordered_list: list[_T], item: _T) -> int:
    """Determine the percentage of an item in an ordered list.

    When using this utility for fan speeds, do not include "off"

    Given the list: ["low", "medium", "high", "very_high"], this
    function will return the following when the item is passed
    in:

        low: 25
        medium: 50
        high: 75
        very_high: 100

    """
    if item not in ordered_list:
        raise ValueError(f'The item "{item}" is not in "{ordered_list}"')

    list_len = len(ordered_list)
    list_position = ordered_list.index(item) + 1
    return (list_position * 100) // list_len


def process_range(range_vals: dict) -> list[Any]:
    """Process a range to determine what's supported.

    :param range_vals: Result from functions["values"][x]
    """
    supported_range = []
    range_min = range_vals["range"]["min"]
    range_max = range_vals["range"]["max"]
    range_step = range_vals["range"]["step"]
    if range_min == range_max:
        supported_range.append(range_max)
    else:
        supported_range = list(float_range(range_min, range_max, range_step))
    if range_max not in supported_range:
        supported_range.append(range_max)
    return supported_range


def float_range(start, stop, step):
    """Create a generator that yields a range as float."""
    while start < stop:
        yield start
        start += step


def process_function(
    functions: list[dict], func_class: str, func_instance: str | None = None
) -> list[Any]:
    """Generate a list of whatever you are searching for.

    :param functions: List of functions for the given device
    :param func_class: functionClass to search
    :param func_instance: functionInstance to search
    """
    results = []
    for function in functions:
        if function["functionClass"] != func_class:
            continue
        if func_instance and function.get("functionInstance") != func_instance:
            continue
        if function["type"] == "numeric":
            results = process_range(function["values"][0])
        elif function["type"] == "category":
            for value in function["values"]:
                results.append(value["name"])
        break
    return results
