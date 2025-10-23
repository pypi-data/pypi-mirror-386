from __future__ import annotations
import os
from typing import Self, Any, IO, TypeVar
from dataclasses import dataclass
from numpy import typing as npt
import numpy as np
import resfo
import trimesh
import warnings
from matplotlib.path import Path
import heapq
from functools import cached_property


class InvalidEgridFileError(ValueError):
    pass


@dataclass
class MapAxes:
    """The axes of the map coordinate system.

    Usually, a corner-point grid contains x,y values that needs to be transformed
    into a map coordinate system (which could be :term:`UTM-coordinates`). That
    coordinate system is represented by MapAxes.

    Note that regardless of the size of the axes, when transforming from the grid
    coordinate system to the map coordinate system, scaling is not applied.

    Attributes:
        y_axis:
            A point along the map y axis.
        origin:
            The origin of the map coordinate system.
        x_axis:
            A point along the map x axis.
    """

    y_axis: tuple[np.float32, np.float32]
    origin: tuple[np.float32, np.float32]
    x_axis: tuple[np.float32, np.float32]

    def transform_map_points(
        self, points: npt.NDArray[np.float32]
    ) -> npt.NDArray[np.float32]:
        """Transforms points from map coordinates to grid coordinates.

        Scaling according to length of the axes is not applied.

        Returns:
            The given map points in the grid coordinate system.
        """
        translated = points - np.array([*self.origin, 0])
        tx = translated[:, 0]
        ty = translated[:, 1]
        x_vec = (self.x_axis[0] - self.origin[0], self.x_axis[1] - self.origin[1])
        y_vec = (self.y_axis[0] - self.origin[0], self.y_axis[1] - self.origin[1])
        x_norm = np.sqrt(x_vec[0] ** 2 + x_vec[1] ** 2)
        x_unit = (x_vec[0] / x_norm, x_vec[1] / x_norm)
        y_norm = np.sqrt(y_vec[0] ** 2 + y_vec[1] ** 2)
        y_unit = (y_vec[0] / y_norm, y_vec[1] / y_norm)
        norm = 1.0 / (x_unit[0] * y_unit[1] - x_unit[1] * y_unit[0])
        return np.column_stack(
            [
                (tx * y_unit[1] - ty * y_unit[0]) * norm,
                (-tx * x_unit[1] + ty * x_unit[0]) * norm,
                translated[:, 2],
            ]
        )


@dataclass
class CornerpointGrid:
    """
    A :term:`corner-point grid` is a tessellation of a 3D volumne where
    each cell is a hexahedron.

    Each cell is identified by a integer coordinate (i,j,k).
    For each i,j there is are four straight lines, defined by their end-points
    called a :term:`pillar`. The end-points form two surfaces, one
    for the top end-points and one for the bottom end points, which
    are in the CornerpointGrid.coord array.

    For the cell at position i,j,k, its eight corner vertices are defined by
    giving the z values along the pillars at [(i,j), (i+1, j), (i, j+1), (i+1, j+1)]
    which are in the CornerpointGrid.zcorn array.


    Attributes:
        coord:
            A (ni+1, nj+1, 2, 3) array where coord[i,j,0] is the top end point
            of the i,j pillar and coord[i,j,1] is the corresponding bottom end point.
        zcorn:
            A (ni, nj, nk, 8) array where zcorn[i,j,k] is the z value of
            the 8 corners of the cell at i,j,k.

        map_axes:
            Optionally each point is interpreted to be relative to some map
            coordinate system. Defaults to the unit coordinate system with
            origo at (0,0). The order of the corner z valus are as follows:
            [TSW, TSE, TNW, TNE, BSW, BSE, BNW, BNE] where N(orth) means higher y,
            E(east) means higer x, T(op) means lower z (when z is interpreted as depth).

    """

    coord: npt.NDArray[np.float32]
    zcorn: npt.NDArray[np.float32]
    map_axes: MapAxes | None = None

    @classmethod
    def read_egrid(cls, file_like: str | os.PathLike[str] | IO[Any]) -> Self:
        """Read the global grid from an .EGRID or .FEGRID file.

        If the EGRID contains Local Grid Refinements or Coarsening Groups,
        that is silently ignored and only the host grid is read. Radial grids
        are not supported and will cause InvalidEgridFileError to be raised.

        Args:
            file_like:
                The EGRID file, could either be a filename, patlike or an opened
                EGRID file. The function also handles formatted egrid files (.FEGRID).
                Whether the file is formatted or not is determined by looking at the
                extension a filepath is given and by whether the stream is a byte-stream
                (unformatted) or a text-stream when an opened file is given.
        Raises:
            InvalidEgridFileError:
                When the egrid file is not valid, or contains a radial grid.
            OSError:
                If the given filepath cannot be opened.

        """
        coord = None
        dims = None
        zcorn = None
        opened = False
        stream = None
        map_axes = None

        try:
            if isinstance(file_like, str):
                filename = file_like
                mode = "rt" if filename.lower().endswith("fegrid") else "rb"
                stream = open(filename, mode=mode)
                opened = True
            elif isinstance(file_like, os.PathLike):
                filename = str(file_like)
                mode = "rt" if filename.lower().endswith("fegrid") else "rb"
                stream = open(filename, mode=mode)
                opened = True
            else:
                filename = getattr(file_like, "name", "unknown stream")
                stream = file_like

            T = TypeVar("T", bound=np.generic)

            def validate_array(
                name: str,
                array: npt.NDArray[T] | resfo.MESS,
                min_length: int | None = None,
            ) -> npt.NDArray[T]:
                if array is resfo.MESS or isinstance(array, resfo.MESS):
                    raise InvalidEgridFileError(
                        f"Expected Array for keyword {name} in {filename} but got MESS"
                    )
                if min_length is not None and len(array) < min_length:
                    raise InvalidEgridFileError(
                        f"{name} in EGRID file {filename} contained too few elements"
                    )

                return array

            def optional_get(array: npt.NDArray[T] | None, index: int) -> T | None:
                if array is None:
                    return None
                if len(array) <= index:
                    return None
                return array[index]

            for entry in resfo.lazy_read(stream):
                kw = entry.read_keyword()
                match kw:
                    case "ZCORN   ":
                        zcorn = validate_array(kw, entry.read_array())
                    case "COORD   ":
                        coord = validate_array(kw, entry.read_array())
                    case "GRIDHEAD":
                        array = validate_array(kw, entry.read_array(), 4)
                        if (reference_number := optional_get(array, 4)) != 0:
                            warnings.warn(
                                f"The global grid in {filename} had "
                                f"reference number {reference_number}, expected 0."
                                " This could indicate that the grid being read"
                                " is actually an LGR grid."
                            )
                        if optional_get(array, 26) not in {0, None}:
                            raise InvalidEgridFileError(
                                f"EGRID file {filename} contains a radial grid"
                                " which is not supported by resfo-utilities."
                            )

                        dims = tuple(array[1:4])
                    case "MAPAXES ":
                        array = validate_array(kw, entry.read_array(), 6)
                        map_axes = MapAxes(
                            (array[0], array[1]),
                            (array[2], array[3]),
                            (array[4], array[5]),
                        )
                    case "ENDGRID ":
                        break

            if coord is None:
                raise InvalidEgridFileError(
                    f"EGRID file {filename} did not contain COORD"
                )
            if zcorn is None:
                raise InvalidEgridFileError(
                    f"EGRID file {filename} did not contain ZCORN"
                )
            if dims is None:
                raise InvalidEgridFileError(
                    f"EGRID file {filename} did not contain dimensions"
                )
        except resfo.ResfoParsingError as err:
            raise InvalidEgridFileError(f"Could not parse EGRID file: {err}") from err
        finally:
            if opened and stream is not None:
                stream.close()
        try:
            coord = np.swapaxes(coord.reshape((dims[1] + 1, dims[0] + 1, 2, 3)), 0, 1)
        except ValueError as err:
            raise InvalidEgridFileError(
                f"COORD size {len(coord)} did not match"
                f" grid dimensions {dims} in {filename}"
            ) from err
        try:
            zcorn = zcorn.reshape(2, dims[0], 2, dims[1], 2, dims[2], order="F")
            zcorn = np.moveaxis(zcorn, [1, 3, 5, 4, 2], [0, 1, 2, 3, 4])
            zcorn = zcorn.reshape((dims[0], dims[1], dims[2], 8))
        except ValueError as err:
            raise InvalidEgridFileError(
                f"ZCORN size {len(zcorn)} did not match"
                f" grid dimensions {dims} in {filename}"
            ) from err
        return cls(coord, zcorn, map_axes)

    def find_cell_containing_point(
        self, points: npt.ArrayLike, map_coordinates: bool = True
    ) -> list[tuple[float, float, float] | None]:
        """Find a cell in the grid which contains the given point.

        Args:
            points:
                The points to find cells for.
            map_coordinates:
                Whether points are in the map coordinate system.
                Defaults to True.

        Returns:
            list of i,j,k indecies for each point (or None if the
            point is not contained in any cell.
        """
        points = np.asarray(points)
        result: list[tuple[float, float, float] | None] = []
        if map_coordinates and self.map_axes is not None:
            points = self.map_axes.transform_map_points(points)

        # This algorithm will for each point p calculate the mesh surface that
        # is the intersection of the pillars with the plane z=p[2]. Then it searches
        # through the quad with a heuristical search that orders each neighbour by
        # the points manhattan distance to the bounding box.
        found = False
        # The use case that the previous point is close to the
        # next point is very common, so we optimize for that.
        prev_ij = None  # The i,j index the previous point was found at

        @dataclass
        class Quad:
            """The quad at index i,j"""

            mesh: npt.NDArray[np.float32]
            i: int
            j: int
            p: npt.NDArray[np.float32]

            @cached_property
            def vertices(self) -> npt.NDArray[np.float32]:
                return np.array(
                    [
                        self.mesh[self.i, self.j],
                        self.mesh[self.i + 1, self.j],
                        self.mesh[self.i + 1, self.j + 1],
                        self.mesh[self.i, self.j + 1],
                    ],
                    dtype=np.float32,
                )

            @cached_property
            def min_x(self) -> np.float32:
                return self.vertices[:, 0].min()

            @cached_property
            def min_y(self) -> np.float32:
                return self.vertices[:, 1].min()

            @cached_property
            def max_x(self) -> np.float32:
                return self.vertices[:, 0].max()

            @cached_property
            def max_y(self) -> np.float32:
                return self.vertices[:, 1].max()

            @cached_property
            def distance_from_bounds(self) -> np.float32:
                """Manhattan distance from the point to the quad bounding box."""
                x_dist = max(self.min_x - self.p[0], self.p[0] - self.max_x, 0)
                y_dist = max(self.min_y - self.p[1], self.p[1] - self.max_y, 0)
                return x_dist + y_dist

            def __lt__(self, other: object) -> bool:
                """Used to order elements in the search queue.

                The Quads are orderd by distance_from_bounds.
                """
                if not isinstance(other, Quad):
                    return False
                return bool(self.distance_from_bounds < other.distance_from_bounds)

        if self.zcorn.shape[0] <= 0 or self.zcorn.shape[1] <= 0:
            return [None] * len(points)

        for p in points:
            found = False
            mesh = self._pillars_z_plane_intersection(p[2])
            if prev_ij is None:
                queue = [Quad(mesh, 0, 0, p)]
            else:
                queue = [Quad(mesh, *prev_ij, p)]
            visited = set([(queue[0].i, queue[0].j)])
            while queue:
                node = heapq.heappop(queue)
                vertices = node.vertices
                i = node.i
                j = node.j

                # If the quad contains the point then search through each k index
                # for that quad
                if node.distance_from_bounds <= 0 and Path(vertices).contains_points(
                    [p[0:2]]
                ):
                    for k in range(self.zcorn.shape[2]):
                        zcorn = self.zcorn[i, j, k]
                        # Prune by bounding box first then check whether point_in_cell
                        if zcorn.min() <= p[2] <= zcorn.max() and self.point_in_cell(
                            p, i, j, k, map_coordinates=False
                        ):
                            prev_ij = (i, j)
                            result.append((i, j, k))
                            found = True
                            break
                    break

                # Add each neighbour to the queue if not visited
                for di in (-1, 0, 1):
                    ni = i + di
                    if ni < 0 or ni >= self.zcorn.shape[0]:
                        continue
                    for dj in (-1, 0, 1):
                        nj = j + dj
                        if nj < 0 or nj >= self.zcorn.shape[1]:
                            continue
                        if (ni, nj) not in visited:
                            heapq.heappush(queue, Quad(mesh, ni, nj, p))
                            visited.add((ni, nj))
            if not found:
                result.append(None)

        return result

    def point_in_cell(
        self,
        points: npt.ArrayLike,
        i: int,
        j: int,
        k: int,
        tolerance: float = 1e-6,
        map_coordinates: bool = True,
    ) -> npt.NDArray[np.bool_]:
        """Whether the points (x,y,z) is in the cell at (i,j,k).

        Param:
            points:
                x,y,z triple or array of x,y,z triples to be tested for containment.
            tolerance:
                The maximum distance to the cell boundary a point can have to
                be considered to be contained in the cell.
            map_coordinates:
                Whether the given points are in the mapaxes coordinate system,
                defaults to true.

        Returns:
            Array of boolean values for each triplet describing whether
            it is contained in the cell.
        """
        points = np.asarray(points)
        if len(points.shape) == 1:
            points = points[np.newaxis, :]
        if map_coordinates and self.map_axes is not None:
            points = self.map_axes.transform_map_points(points)
        pillar_vertices = np.concatenate(
            [
                self.coord[i, j, :],
                self.coord[i, j + 1, :],
                self.coord[i + 1, j, :],
                self.coord[i + 1, j + 1, :],
            ]
        )
        top = pillar_vertices[::2][[0, 2, 1, 3]]
        bot = pillar_vertices[1::2][[0, 2, 1, 3]]
        top_z = top[:, 2]
        bot_z = bot[:, 2]

        def twice(a: npt.NDArray[Any]) -> npt.NDArray[Any]:
            return np.concatenate([a, a])

        t = (self.zcorn[i, j, k] - twice(top_z)) / twice(bot_z - top_z)
        mesh = trimesh.Trimesh(
            vertices=twice(top) + t[:, np.newaxis] * twice(bot - top),
            faces=np.array(
                [
                    [0, 1, 2],
                    [1, 2, 3],
                    [0, 1, 5],
                    [0, 4, 5],
                    [0, 2, 6],
                    [0, 4, 6],
                    [4, 6, 5],
                    [5, 6, 7],
                    [1, 3, 7],
                    [1, 5, 7],
                    [2, 3, 7],
                    [2, 3, 6],
                ]
            ),
        )
        return mesh.contains(points) | (mesh.nearest.on_surface(points)[1] < tolerance)

    def _pillars_z_plane_intersection(self, z: np.float32) -> npt.NDArray[np.float32]:
        shape = self.coord.shape
        coord = self.coord.reshape(shape[0] * shape[1], shape[2] * shape[3])
        x1, y1, z1, x2, y2, z2 = coord.T
        t = (z - z1) / (z2 - z1)

        # Compute x and y for all lines
        x = x1 + t * (x2 - x1)
        y = y1 + t * (y2 - y1)

        # Result: (x, y) coordinates for all lines at z
        result = np.column_stack((x, y))
        return result.reshape(shape[0], shape[1], 2)
