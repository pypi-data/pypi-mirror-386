from typing import Optional

import numpy as np

from classy_blocks.cbtyping import PointType, VectorType
from classy_blocks.construct.curves.curve import CurveBase
from classy_blocks.optimize.clamps.clamp import ClampBase
from classy_blocks.util import functions as f


class CurveClamp(ClampBase):
    """Clamp that restricts point movement during optimization
    to a predefined curve.

    The curve parameter that corresponds to given vertex's position
    is obtained automatically by minimization. To provide a better starting
    point in case minimization fails or produces wrong results,
    an initial parameter can be supplied."""

    def __init__(
        self,
        position: PointType,
        curve: CurveBase,
        initial_param: Optional[float] = None,
    ):
        position = np.array(position)

        if initial_param is not None:
            initial = [initial_param]
        else:
            initial = [curve.get_closest_param(position)]

        super().__init__(position, lambda t: curve.get_point(t[0]), [list(curve.bounds)], initial)

    @property
    def initial_guess(self):
        return self.initial_params


class LineClamp(ClampBase):
    """Clamp that restricts point movement
    during optimization to a line, defined by 2 points;

    Parameter 't' goes from 0 at point_1 to <d> at point_2
    where <d> is the distance between the two points
    (and beyond if different bounds are specified)."""

    def __init__(
        self, position: PointType, point_1: PointType, point_2: PointType, bounds: Optional[tuple[float, float]] = None
    ):
        position = np.array(position)
        point_1 = np.array(point_1)
        point_2 = np.array(point_2)

        def function(t):
            return point_1 + t[0] * f.unit_vector(point_2 - point_1)

        if bounds is None:
            bounds = (0, f.norm(point_2 - point_1))

        super().__init__(position, function, [list(bounds)])

    @property
    def initial_guess(self) -> list[float]:
        # Finding the closest point on a line is reliable enough
        # so that specific initial parameters are not needed
        return [0]


class RadialClamp(ClampBase):
    """Clamp that restricts point movement during optimization
    to a circular trajectory, defined by center, normal and
    vertex position at clamp initialization.

    Parameter t goes from 0 at initial vertex position to 2*<r>*pi
    at the same position all the way around the circle (with radius <r>)"""

    def __init__(
        self, position: PointType, center: PointType, normal: VectorType, bounds: Optional[list[float]] = None
    ):
        position = np.array(position)
        initial_point = np.copy(position)

        if bounds is not None:
            clamp_bounds = [bounds]
        else:
            clamp_bounds = None

        # Clamps that move points linearly have a clear connection
        # <delta_params> - <delta_position>.
        # With rotation, this strongly depends on the radius of the point.
        # To conquer that, divide params by radius
        radius = f.point_to_line_distance(center, normal, position)

        super().__init__(
            position, lambda params: f.rotate(initial_point, params[0] / radius, normal, center), clamp_bounds
        )

    @property
    def initial_guess(self):
        return [0]
