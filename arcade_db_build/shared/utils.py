#!/usr/bin/env python3

from lxml import etree as ET
import functools


@functools.cache
def get_sub_elements(parent_element: ET._Element, tag_name: str) -> list[ET._Element]:
    return parent_element.findall(tag_name)
