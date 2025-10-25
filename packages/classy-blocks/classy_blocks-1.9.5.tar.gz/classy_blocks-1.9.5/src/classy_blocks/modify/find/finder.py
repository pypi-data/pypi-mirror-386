from typing import Optional

import numpy as np

from classy_blocks.cbtyping import PointType
from classy_blocks.items.vertex import Vertex
from classy_blocks.mesh import Mesh
from classy_blocks.util import constants
from classy_blocks.util import functions as f


class FinderBase:
    """Base class for locating Mesh vertices"""

    def __init__(self, mesh: Mesh):
        self.mesh = mesh

    def _find_by_position(self, position: PointType, radius: Optional[float] = None) -> set[Vertex]:
        """Returns a list of vertices that are
        inside a sphere of given radius; if that is not given,
        constants.TOL is taken"""

        found_vertices: set[Vertex] = set()

        if radius is None:
            radius = constants.TOL

        # TODO: optimize with octree/kdtree
        position = np.array(position)

        for vertex in self.mesh.vertices:
            if f.norm(vertex.position - position) < radius:
                found_vertices.add(vertex)

        return found_vertices
