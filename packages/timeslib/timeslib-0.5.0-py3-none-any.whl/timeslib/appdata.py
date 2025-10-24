# -*- coding: utf-8 -*-
"""
Copyright 2019-2022 Olexandr Balyk

This file is part of Timeslib.

Timeslib is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Timeslib is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with Timeslib. If not, see <https://www.gnu.org/licenses/>.
"""

import json


def fix_appdata_file(
    filename: str,
    sort_id: str,
    sort_id_filter: str | None = None,
    reset_keys: dict | None = None,
) -> list[dict]:
    """
    Fix an application data file by sorting and resetting keys.
    """
    with open(filename, mode="rb") as f:
        data = json.load(f)
    # Hold valid ids
    valid_items = []

    for i in data:
        if sort_id_filter:
            if i[sort_id] in sort_id_filter:
                valid_items += [i[sort_id]]
        else:
            valid_items += [i[sort_id]]
    # Sort ids in ascending order
    valid_items.sort()
    # Hold sorted data
    sorted_data = []
    # Populate the list with sorted data
    for valid_item in valid_items:
        for i in data:
            if i[sort_id] == valid_item:
                sorted_data += [i]
    return reset_dict_keys(sorted_data, reset_keys)


def reset_dict_keys(
    dict_list: list[dict], keys_to_reset: dict | None = None
) -> list[dict]:
    """
    Reset specified keys in a list of dictionaries to given values.
    """
    output_data = []

    if keys_to_reset:
        for dictionary in dict_list:
            new_dictionary = dict()
            for k in dictionary.keys():
                if k not in keys_to_reset.keys():
                    new_dictionary[k] = dictionary[k]
                else:
                    new_dictionary[k] = keys_to_reset[k]
            output_data += [new_dictionary]
        return output_data
    else:
        return dict_list
