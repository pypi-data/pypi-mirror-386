"""
Trajectopy - Trajectory Evaluation in Python

Gereon Tombrink, 2025
tombrink@igg.uni-bonn.de
"""

import logging
from dataclasses import dataclass, field
from typing import List, Tuple, Union

import numpy as np
from scipy.sparse import csr_matrix, lil_matrix

from trajectopy.core.utils import sparse_least_squares

# logger configuration
logger = logging.getLogger("root")


@dataclass
class Interval:
    start: float
    end: float
    values: List[float] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.values)

    @property
    def length(self) -> float:
        return self.end - self.start

    @property
    def coefficients(self) -> List[np.ndarray]:
        return [self._compute_c(v) for v in self.values]

    def _compute_c(self, value: float) -> np.ndarray:
        """
        Helper function to compute the coefficients for cubic approximation
        """
        relative_length = value - self.start
        interval_length = self.end - self.start
        interval_ratio = relative_length / interval_length

        c0 = 1 - 3 * interval_ratio**2 + 2 * interval_ratio**3
        c1 = relative_length * (1 - 2 * interval_ratio + interval_ratio**2)
        c2 = 3 * interval_ratio**2 - 2 * interval_ratio**3
        c3 = relative_length * (interval_ratio**2 - interval_ratio)

        return np.array([c0, c1, c2, c3])


class Intervals:
    def __init__(self):
        self.intervals: list[Interval] = []


class CubicApproximation:
    """
    Class for piecewise cubic approximation
    """

    def __init__(
        self, function_of: np.ndarray, values: np.ndarray, min_win_size: float = 0.25, min_obs: int = 3
    ) -> None:
        """
        Inititalization of a new CubicApproximation class object
        """
        self.function_of = function_of
        self.values = values
        self.min_win_size = min_win_size
        self.min_obs = max(3, min_obs)

        # fit results
        self.parameters: Union[np.ndarray, None] = None
        self.est_obs: Union[np.ndarray, None] = None
        self.residuals: Union[np.ndarray, None] = None
        self.interval_steps: Union[np.ndarray, None] = None

        # compute approximation
        self._cubic_approx()

    def eval(self, locations: np.ndarray) -> np.ndarray:
        """
        Evaluate the cubic approximation at specified locations
        """
        if self.interval_steps is None or self.parameters is None:
            raise ValueError("Approximation not yet computed")

        if np.min(locations) > np.max(self.interval_steps) or np.max(locations) < np.min(self.interval_steps):
            raise ValueError("Evaluation locations are outside of the approximation interval")

        # function
        f_vals = self.parameters[::2]
        # first derivative
        f_deriv_vals = self.parameters[1::2]

        interval_indices = np.searchsorted(self.interval_steps, locations)
        int_start = self.interval_steps[interval_indices - 1]
        int_end = self.interval_steps[interval_indices]

        relative_length = locations - int_start
        interval_length = int_end - int_start

        c0, c1, c2, c3 = self._compute_c(relative_length, interval_length)

        return (
            f_vals[interval_indices - 1] * c0
            + f_deriv_vals[interval_indices - 1] * c1
            + f_vals[interval_indices] * c2
            + f_deriv_vals[interval_indices] * c3
        )

    def _cubic_approx(self) -> None:
        """
        Approximation using piece-wise cubic polynomials
        """
        var_red = self.function_of - self.function_of[0]

        intervals: list[Interval] = []
        current_interval_obj = Interval(start=0.0, end=0.0)

        for i, x_value in enumerate(var_red):
            current_interval_obj.values.append(x_value)
            current_interval_obj.end = x_value

            if len(current_interval_obj) >= self.min_obs and current_interval_obj.length > self.min_win_size:
                intervals.append(current_interval_obj)
                current_interval_obj = Interval(start=x_value, end=x_value)

            if (i == len(var_red) - 1) and (
                len(current_interval_obj) < self.min_obs or current_interval_obj.length < self.min_win_size
            ):
                intervals[-1].end = current_interval_obj.end
                intervals[-1].values.extend(current_interval_obj.values)

        logger.info(
            "Average observation count per interval: %.2f",
            len(var_red) / len(intervals),
        )

        t_final = [0.0] + [interval.end for interval in intervals]

        # Design matrix (jacobian)
        a_design = self._design_matrix(intervals)

        # least squares
        logger.info("Approximation using piece-wise cubic polynomials via least-squares method.")
        xS, lS, residuals = sparse_least_squares(csr_matrix(a_design), self.values[:, None])

        # store results
        self.parameters = xS
        self.est_obs = lS
        self.residuals = residuals
        self.interval_steps = t_final + self.function_of[0]

    @staticmethod
    def _compute_c(relative_length: float, interval_length: float) -> Tuple[float, float, float, float]:
        """
        Helper function to compute the coefficients for cubic approximation
        """
        interval_ratio = relative_length / interval_length

        c0 = 1 - 3 * interval_ratio**2 + 2 * interval_ratio**3
        c1 = relative_length * (1 - 2 * interval_ratio + interval_ratio**2)
        c2 = 3 * interval_ratio**2 - 2 * interval_ratio**3
        c3 = relative_length * (interval_ratio**2 - interval_ratio)

        return c0, c1, c2, c3

    def _design_matrix(self, intervals: List[Interval]) -> lil_matrix:
        rows = len(self.function_of)
        columns = 2 * len(intervals) + 2

        a_design = lil_matrix((rows, columns), dtype=float)

        row_offset = 0
        for i, interval in enumerate(intervals):
            matrix = np.array(interval.coefficients)

            column_start = i * 2
            column_end = column_start + 4

            a_design[row_offset : row_offset + len(matrix), column_start:column_end] = matrix
            row_offset += len(matrix)

        return a_design


def piecewise_cubic(
    function_of: np.ndarray,
    values: np.ndarray,
    min_win_size: float = 0.25,
    min_obs: int = 25,
    return_approx_objects: bool = False,
) -> Union[Tuple[np.ndarray, List[CubicApproximation]], np.ndarray]:
    """
    Approximates a piecewise cubic function for a given set of input values.

    Args:
        function_of (np.ndarray): The input values to approximate the function for.
        values (np.ndarray): The output values corresponding to the input values.
        int_size (float, optional): The interval size for the approximation. Defaults to 0.15.
        min_obs (int, optional): The minimum number of observations required for the approximation. Defaults to 25.
        return_approx_objects (bool, optional): Whether to return the list of CubicApproximation objects along with the approximated values. Defaults to False.

    Returns:
        Union[np.ndarray, Tuple[list[CubicApproximation], np.ndarray]]: The approximated values. If `return_approx_objects` is True, returns a tuple containing the approximated values and the list of CubicApproximation objects.
    """
    # Cubic spline approximation
    # least squares
    approx_list = [
        CubicApproximation(function_of, values[:, i], min_win_size, min_obs) for i in range(values.shape[1])
    ]

    approx_values = np.column_stack([ap.est_obs for ap in approx_list if ap.est_obs is not None])

    return (approx_values, approx_list) if return_approx_objects else approx_values
