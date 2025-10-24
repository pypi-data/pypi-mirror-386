# Copyright (c) 2025, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

from dataclasses import dataclass
from itertools import chain
from typing import ClassVar, Dict

from ngcbase.api.pagination import pagination_helper_header_page_reference


def fetch_paginated_list(connection, url: str, *, org=None, operation_name=None):
    """Fetch a paginated list and order it by "updated" descending."""
    return sorted(
        chain.from_iterable(
            res
            for res in pagination_helper_header_page_reference(
                connection, url, org_name=org, operation_name=operation_name
            )
            if res
        ),
        key=lambda item: item.get("updated", ""),
        reverse=True,
    )


@dataclass
class _BaseItem:
    """Base class for use with `construct_item_metavar` and `make_item_type`."""

    _ALIAS_CONVERSIONS: ClassVar[dict[Dict[str, str]]] = {}

    def _to_dict(self):
        return {self._ALIAS_CONVERSIONS.get(key, key): value for key, value in vars(self).items() if value is not None}

    @classmethod
    def _from_dict(cls, obj):
        if isinstance(obj, cls):
            return obj
        reverse_conversions = {value: key for key, value in cls._ALIAS_CONVERSIONS.items()}
        kwargs = {reverse_conversions.get(key, key): value for key, value in obj.items()}
        return cls(**kwargs)
