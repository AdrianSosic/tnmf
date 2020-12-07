"""
Author: Adrian Sosic
"""

import numpy as np
from typing import Union, Tuple


def normalize(arr: np.array, axis: Union[int, Tuple[int]] = 0) -> np.array:
	"""
	Normalizes a given array such that the sum of its values along the specified axis sum to one.

	Parameters
	----------
	arr : np.array
		The array to be normalized.
	axis : int or tuple of int
		The axis (or axes) along which the array shall be normalized.

	Returns
	-------
	The normalized array.
	"""
	return arr / np.sum(arr, axis=axis, keepdims=True)


def shift(arr: np.array, step: int) -> np.array:
	"""
	Shifts the given array a certain number of steps along the last axis, filling the empty places with zeros.

	Parameters
	----------
	arr : np.array
		The array to be shifted.
	step : int
		The number of steps the array shall be shifted.

	Returns
	-------
	The shifted (and zero-padded) array.
	"""
	arr = np.roll(arr, step)
	if step < 0:
		arr[..., step:] = 0
	elif step > 0:
		arr[..., :step-1] = 0
	return arr
