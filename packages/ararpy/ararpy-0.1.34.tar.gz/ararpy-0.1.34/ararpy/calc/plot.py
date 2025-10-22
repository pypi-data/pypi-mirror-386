#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
# ==========================================
# Copyright 2023 Yang
# ararpy - calc - plot
# ==========================================
#
#
#
"""
import traceback

import decimal
from math import exp, log, cos, acos, ceil, sqrt, atan, sin, gamma
# from typing import List, Any
# from scipy.optimize import fsolve
# from scipy.stats import distributions
import numpy as np

math_e = 2.718281828459045
math_pi = 3.141592653589793


def get_axis_scale(data: list, count=6, increment=None, extra_count=0, min_interval=1):
    """

    Parameters
    ----------
    data
    count
    increment
    extra_count
    min_interval

    Returns
    -------

    """
    if len(data) == 0:
        return 0, 1, 5, 0.2  # Default return
    _max = np.ma.masked_invalid(data).max()
    _min = np.ma.masked_invalid(data).min()
    if isinstance(_max, np.ma.core.MaskedConstant) or isinstance(_min, np.ma.core.MaskedConstant):
        return 0, 1, 5, 0.2  # Default return
    _max = float(_max); _min = float(_min)
    interval = (_max - _min) / count
    if interval == 0:
        interval = 10
    mag = 10 ** int(log(interval, 10)) if interval >= 1 else 10 ** (int(log(interval, 10)) - 1)
    if not increment:
        increment = decimal.Decimal(
            str(decimal.Decimal(int(interval / mag // min_interval) + min_interval) * decimal.Decimal(str(mag))))
    else:
        increment = decimal.Decimal(increment)
    start = decimal.Decimal(_min) // increment * increment
    if _min < 0:
        while start > _min:
            start -= increment
    else:
        while start + increment < _min:
            start += increment
    count = 0
    while count * increment + start < _max:
        count += 1
    end = decimal.Decimal(str(count + extra_count)) * decimal.Decimal(str(increment)) + start
    start -= decimal.Decimal(extra_count) * decimal.Decimal(str(increment))
    start = 0 if start < 0 <= _min else start
    count = (end - start) / increment
    return float(start), float(end), int(count), float(increment)