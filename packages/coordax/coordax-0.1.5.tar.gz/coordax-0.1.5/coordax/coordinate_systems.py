# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Coordinate systems for use on coordax.Field objects.

``Coordinate`` objects define a discretization schema, dimension names and
provide methods & coordinate field values to facilitate computations.
"""
from __future__ import annotations

import abc
import collections
from collections.abc import Iterable
import dataclasses
import itertools
import typing
from typing import Any, Self, TYPE_CHECKING, TypeAlias, TypeVar

from coordax import utils
import jax
import numpy as np
# TODO(shoyer): consider making Xarray an optional dependency of core Coordax
import xarray

if TYPE_CHECKING:
  # import only under TYPE_CHECKING to avoid circular dependency
  # pylint: disable=g-bad-import-order
  from coordax import fields


Pytree: TypeAlias = Any
Sequence = collections.abc.Sequence


@utils.export
@dataclasses.dataclass(frozen=True)
class NoCoordinateMatch:
  """For use when a coordinate does not match an xarray.Coordinates object."""

  reason: str


@utils.export
class Coordinate(abc.ABC):
  """Abstract class for coordinate objects.

  Coordinate subclasses are expected to obey several invariants:
  1. Dimension names may not be repeated: `len(set(dims)) == len(dims)`
  2. All dimensions must be named: `len(shape) == len(dims)`

  Every non-abstract Coordinate subclass must be registered as a "static"
  pytree node, e.g., by decorating the class with
  `@jax.tree_util.register_static`. Static pytrees nodes must implement
  `__hash__` and `__eq__` according to the requirements of keys in Python
  dictionaries. This is easiest to acheive with frozen dataclasses, but care
  must be taken when working with np.ndarray attributes.

  TODO(shoyer): add documentation examples, including a version using ArrayKey
  to wrap np.ndarray attributions.
  """

  @property
  @abc.abstractmethod
  def dims(self) -> tuple[str | None, ...]:
    """Dimension names of the coordinate.

    All subclasses must return a tuple of dimension names as strings, with the
    exception of `DummyAxis`.
    """
    raise NotImplementedError()

  @property
  @abc.abstractmethod
  def shape(self) -> tuple[int, ...]:
    """Shape of the coordinate."""
    raise NotImplementedError()

  @property
  @abc.abstractmethod
  def fields(self) -> dict[str, fields.Field]:
    """A maps from field names to their values."""

  @property
  def sizes(self) -> dict[str, int]:
    """Sizes of all dimensions on this coordinate."""
    return {
        dim: size for dim, size in zip(self.dims, self.shape) if dim is not None
    }

  @property
  def ndim(self) -> int:
    """Dimensionality of the coordinate."""
    return len(self.dims)

  @property
  def axes(self) -> tuple[Coordinate, ...]:
    """Tuple of one-dimensional Coordinate objects for each dimension."""
    if self.ndim == 1:
      return (self,)
    else:
      return tuple(SelectedAxis(self, i) for i in range(self.ndim))

  def to_xarray(self) -> dict[str, xarray.Variable]:
    """Convert this coordinate into xarray variables."""
    variables = {}
    dims_set = {dim for dim in self.dims if dim is not None}
    for name, coord_field in self.fields.items():
      if set(coord_field.dims) <= dims_set:
        # xarray.DataArray coordinate dimensions must be a subset of the
        # dimensions of the associated DataArray, which is not necessarily a
        # constraint for coordax.Field.
        variables[name] = xarray.Variable(coord_field.dims, coord_field.data)
    return variables

  @classmethod
  def from_xarray(
      cls, dims: tuple[str, ...], coords: xarray.Coordinates
  ) -> Self | NoCoordinateMatch:
    """Construct a matching Coordax coordinate from xarray, if possible.

    Args:
      dims: tuple of dimension names. Only the leading dimensions should be
        checks for a match.
      coords: xarray.Coordinates object providing dimension sizes and coordinate
        values.

    Returns:
      A matching instance of this coordinate or `NoCoordinateMatch` if this
      coordinate does not match the xarray dimensions and coordinates.
    """
    raise NotImplementedError('from_xarray not implemented')


@dataclasses.dataclass(frozen=True)
class ArrayKey:
  """Wrapper for a numpy array to make it hashable."""

  value: np.ndarray

  def __eq__(self, other):
    return (
        isinstance(self, ArrayKey)
        and self.value.dtype == other.value.dtype
        and self.value.shape == other.value.shape
        and (self.value == other.value).all()
    )

  def __hash__(self) -> int:
    return hash((self.value.shape, self.value.tobytes()))


@utils.export
@jax.tree_util.register_static
@dataclasses.dataclass(frozen=True)
class Scalar(Coordinate):
  """Zero dimensional sentinel coordinate used to label stand alone scalars."""

  @property
  def dims(self) -> tuple[str, ...]:
    return ()

  @property
  def shape(self) -> tuple[int, ...]:
    return ()

  @property
  def fields(self) -> dict[str, fields.Field]:
    return {}


@utils.export
@jax.tree_util.register_static
@dataclasses.dataclass(frozen=True)
class SelectedAxis(Coordinate):
  """Coordinate that exposes one dimension of a multidimensional coordinate."""

  coordinate: Coordinate
  axis: int

  def __post_init__(self):
    if self.axis >= self.coordinate.ndim:
      raise ValueError(
          f'Dimension {self.axis=} of {self.coordinate=} is out of bounds'
      )
    if self.coordinate.dims[self.axis] is None:
      raise ValueError(
          f'dimension {self.axis=} of {self.coordinate=} is not named'
      )

  @property
  def dims(self) -> tuple[str, ...]:
    """Dimension names of the coordinate."""
    dim = self.coordinate.dims[self.axis]
    assert dim is not None
    return (dim,)

  @property
  def shape(self) -> tuple[int, ...]:
    """Shape of the coordinate."""
    return (self.coordinate.shape[self.axis],)

  @property
  def fields(self) -> dict[str, fields.Field]:
    """A maps from field names to their values."""
    return self.coordinate.fields

  def __repr__(self):
    return f'coordax.SelectedAxis({self.coordinate!r}, axis={self.axis})'

  def to_xarray(self) -> dict[str, xarray.Variable]:
    """Convert this coordinate into xarray variables."""
    # Override the default method to avoid restricting variables to only those
    # along the selected axis.
    return self.coordinate.to_xarray()


def _expand_coordinates(*coordinates: Coordinate) -> tuple[Coordinate, ...]:
  """Expands coordinates, removing CartesianProducts and Scalars."""
  expanded = []
  for c in coordinates:
    if isinstance(c, CartesianProduct):
      expanded.extend(c.coordinates)
    elif isinstance(c, Scalar):
      pass
    else:
      expanded.append(c)
  return tuple(expanded)


def _consolidate_coordinates(
    *coordinates: Coordinate,
) -> tuple[Coordinate, ...]:
  """Consolidates coordinates, removing SelectedAxes when possible."""
  axes = []
  result = []

  def reset_axes():
    result.extend(axes)
    axes[:] = []

  def append_axis(c):
    axes.append(c)
    if len(axes) == c.coordinate.ndim:
      # sucessful consolidation
      result.append(c.coordinate)
      axes[:] = []

  for c in coordinates:
    if isinstance(c, SelectedAxis) and c.axis == 0:
      # new SelectedAxis to consider consolidating
      reset_axes()
      append_axis(c)
    elif (
        isinstance(c, SelectedAxis)
        and axes
        and c.axis == len(axes)
        and c.coordinate == axes[-1].coordinate
    ):
      # continued SelectedAxis to consolidate
      append_axis(c)
    else:
      # coordinate cannot be consolidated
      reset_axes()
      result.append(c)

  reset_axes()

  return tuple(result)


def canonicalize(*coordinates: Coordinate) -> tuple[Coordinate, ...]:
  """Canonicalize coordinates into a minimum equivalent collection."""
  coordinates = _expand_coordinates(*coordinates)
  coordinates = _consolidate_coordinates(*coordinates)
  existing_dims = collections.Counter()
  for c in coordinates:
    existing_dims.update([d for d in c.dims if d is not None])
  repeated_dims = [dim for dim, count in existing_dims.items() if count > 1]
  if repeated_dims:
    raise ValueError(f'coordinates contain {repeated_dims=}')
  return coordinates


T = TypeVar('T')


def _concat_tuples(tuples: Iterable[tuple[T, ...]]) -> tuple[T, ...]:
  """Concatenates tuples."""
  return tuple(itertools.chain(*tuples))


K = TypeVar('K')
V = TypeVar('V')


def _merge_dicts(dicts: Iterable[dict[K, V]]) -> dict[K, V]:
  """Merges dicts."""
  result = {}
  for d in dicts:
    result.update(d)
  return result


@utils.export
@jax.tree_util.register_static
@dataclasses.dataclass(frozen=True)
class CartesianProduct(Coordinate):
  """Coordinate defined as the outer product of independent coordinates."""

  coordinates: tuple[Coordinate, ...]

  def __post_init__(self):
    coordinates = canonicalize(*self.coordinates)
    object.__setattr__(self, 'coordinates', coordinates)

  def __eq__(self, other):
    # TODO(shoyer): require exact equality of coordinate types?
    if not isinstance(other, CartesianProduct):
      return len(self.coordinates) == 1 and self.coordinates[0] == other
    return isinstance(other, CartesianProduct) and self.axes == other.axes

  @property
  def dims(self) -> tuple[str | None, ...]:
    return _concat_tuples(c.dims for c in self.coordinates)

  @property
  def shape(self) -> tuple[int, ...]:
    """Returns the shape of the coordinate axes."""
    return _concat_tuples(c.shape for c in self.coordinates)

  @property
  def fields(self) -> dict[str, fields.Field]:
    """Returns a mapping from field names to their values."""
    return _merge_dicts(c.fields for c in self.coordinates)

  @property
  def axes(self) -> tuple[Coordinate, ...]:
    """Returns a tuple of Axis objects for each dimension."""
    return _concat_tuples(c.axes for c in self.coordinates)


@utils.export
@jax.tree_util.register_static
@dataclasses.dataclass(frozen=True)
class SizedAxis(Coordinate):
  """One dimensional coordinate with fixed size but no associated fields."""

  name: str
  size: int

  @property
  def dims(self) -> tuple[str, ...]:
    return (self.name,)

  @property
  def shape(self) -> tuple[int, ...]:
    return (self.size,)

  @property
  def fields(self) -> dict[str, fields.Field]:
    return {}

  def __repr__(self):
    return f'coordax.SizedAxis({self.name!r}, size={self.size})'

  @classmethod
  def from_xarray(
      cls, dims: tuple[str, ...], coords: xarray.Coordinates
  ) -> Self | NoCoordinateMatch:
    dim = dims[0]
    if dim in coords:
      return NoCoordinateMatch(
          'can only reconstruct SizedAxis objects from xarray dimensions'
          ' without associated coordinate variables, but found a coordinate'
          f' variable for dimension {dim!r}'
      )
    for name, coord in coords.variables.items():
      if dim in coord.dims:
        return NoCoordinateMatch(
            'can only reconstruct SizedAxis objects from xarray dimensions'
            ' if the dimensions is not found on any coordinate variables, but '
            f' found a coordinate variable for dimension {dim!r} on {name!r}'
        )
    return cls(dim, size=coords.sizes[dim])


@utils.export
@dataclasses.dataclass(frozen=True)
class DummyAxis(Coordinate):
  """Dummy coordinate for dimensions without associated coordinate values.

  DummyAxis are placeholders for dimensions that do not have associated
  coordinate values. They are automatically dropped from the Field constructor,
  but are useful for specifying how to construct fields with missing dimension
  names and/or coordinates.
  """

  name: str | None
  size: int

  @property
  def dims(self) -> tuple[str | None, ...]:
    return (self.name,)

  @property
  def shape(self) -> tuple[int, ...]:
    return (self.size,)

  @property
  def fields(self) -> dict[str, fields.Field]:
    return {}

  def __repr__(self):
    return f'coordax.DummyAxis({self.name!r}, size={self.size})'

  @classmethod
  def from_xarray(
      cls, dims: tuple[str, ...], coords: xarray.Coordinates
  ) -> Self | NoCoordinateMatch:
    dim = dims[0]
    for name, coord in coords.variables.items():
      if dim in coord.dims:
        return NoCoordinateMatch(
            f'cannot omit a Coordinate object for dimension {dim!r}'
            f' because it is used by at least one coordinate variable: {name!r}'
        )
    return cls(name=dim, size=coords.sizes[dim])


# TODO(dkochkov): consider storing tuple values instead of np.ndarray (which
# could be exposed as a property).
@utils.export
@jax.tree_util.register_static
@dataclasses.dataclass(frozen=True)
class LabeledAxis(Coordinate):
  """One dimensional coordinate with custom coordinate values."""

  name: str
  ticks: np.ndarray

  def __post_init__(self):
    object.__setattr__(self, 'ticks', np.asarray(self.ticks))
    if self.ticks.ndim != 1:
      raise ValueError(f'ticks must be a 1D array, got {self.ticks.shape=}')

  @property
  def dims(self) -> tuple[str, ...]:
    return (self.name,)

  @property
  def shape(self) -> tuple[int, ...]:
    return self.ticks.shape

  @property
  def fields(self) -> dict[str, fields.Field]:
    # needs local import to avoid circular dependency
    from coordax import fields  # pylint: disable=g-import-not-at-top

    return {self.name: fields.wrap(self.ticks, self)}

  def _components(self):
    return (self.name, ArrayKey(self.ticks))

  def __eq__(self, other):
    return (
        isinstance(other, LabeledAxis)
        and self._components() == other._components()
    )

  def __hash__(self) -> int:
    return hash(self._components())

  def __repr__(self):
    return f'coordax.LabeledAxis({self.name!r}, ticks={self.ticks!r})'

  @classmethod
  def from_xarray(
      cls, dims: tuple[str, ...], coords: xarray.Coordinates
  ) -> Self | NoCoordinateMatch:
    dim = dims[0]
    if dim not in coords:
      return NoCoordinateMatch(
          f'no associated coordinate for dimension {dim!r}'
      )
    if coords[dim].ndim != 1:
      return NoCoordinateMatch(f'coordinate for dimension {dim!r} is not 1D')
    return cls(dim, coords[dim].data)


@utils.export
def compose(*coordinates: Coordinate) -> Coordinate:
  """Compose coordinates into a unified coordinate system."""
  product = CartesianProduct(coordinates)
  match len(product.coordinates):
    case 0:
      return Scalar()
    case 1:
      return product.coordinates[0]
    case _:
      return product


@utils.export
def insert_axes(
    coordinate: Coordinate,
    indices_to_axes: dict[int, Coordinate],
) -> Coordinate:
  """Returns `coordinate` with extra axes inserted at specified positions."""
  indices_to_axes = indices_to_axes.copy()
  ndim = coordinate.ndim + len(indices_to_axes)
  normalize_idx = lambda i: i + ndim if i < 0 else i
  indices_to_axes = {normalize_idx(i): ax for i, ax in indices_to_axes.items()}
  if any(i < 0 or i >= ndim for i in indices_to_axes.keys()):
    raise ValueError(f'invalid index in {indices_to_axes.keys()=}')

  axes = list(coordinate.axes)
  for index_to_insert_at, axis in sorted(indices_to_axes.items()):
    axes.insert(index_to_insert_at, axis)
  return compose(*axes)


@utils.export
def replace_axes(
    coordinate: Coordinate,
    to_replace: Coordinate,
    replace_with: Coordinate,
) -> Coordinate:
  """Returns `coordinate` with `to_replace` replaced by `replace_with`.

  Args:
    coordinate: The coordinate system to modify.
    to_replace: A contiguous part of the coordinate system to be replaced.
    replace_with: The new coordinate to insert.

  Returns:
    A new coordinate object with `to_replace` substituted by `replace_with`.

  Raises:
    ValueError: If `to_replace` is not a contiguous part of `coordinate`.
  """
  if not to_replace.dims:
    raise ValueError(f'`to_replace` must have dimensions, got {to_replace}')

  # find where the sub-tuple `to_replace.axes` starts in `coordinate.axes`.
  start_index = -1
  for i in range(len(coordinate.axes) - len(to_replace.axes) + 1):
    if coordinate.axes[i : i + len(to_replace.axes)] == to_replace.axes:
      start_index = i
      break

  if start_index == -1:
    raise ValueError(
        f'coordinate {coordinate=} does not contiguously contain {to_replace=}'
    )

  end_index = start_index + len(to_replace.axes)
  axes = list(coordinate.axes)
  axes[start_index:end_index] = replace_with.axes
  return compose(*axes)


def from_xarray(
    data_array: xarray.DataArray,
    coord_types: Sequence[type[Coordinate]] = (LabeledAxis, DummyAxis),
) -> Coordinate:
  """Convert the coordinates of an xarray.DataArray into a coordax.Coordinate.

  Args:
    data_array: xarray.DataArray whose coordinates should be converted.
    coord_types: sequence of coordax.Coordinate subclasses with `from_xarray`
      methods defined. The first coordinate class that returns a coordinate
      object (indicating a match) will be used. By default, coordinates will use
      only generic coordax.LabeledAxis objects. CardesianProduct type is omitted
      from this sequence since it is introduced by the compose() method.

  Returns:
    A coordax.Coordinate object representing the coordinates of the input
    DataArray.
  """
  dims = data_array.dims
  coords = []

  if not all(isinstance(dim, str) for dim in dims):
    raise TypeError(
        'can only convert DataArray objects with string dimensions to Field'
    )
  dims = typing.cast(tuple[str, ...], dims)

  if not coord_types:
    raise ValueError('coord_types must be non-empty')

  def get_next_match():
    reasons = []
    for coord_type in coord_types:
      if coord_type == CartesianProduct or coord_type == Scalar:
        continue
      result = coord_type.from_xarray(dims, data_array.coords)
      if isinstance(result, Coordinate):
        return result
      assert isinstance(result, NoCoordinateMatch)
      coord_name = coord_type.__module__ + '.' + coord_type.__name__
      reasons.append(f'{coord_name}: {result.reason}')

    reasons_str = '\n'.join(reasons)
    raise ValueError(
        'failed to convert xarray.DataArray to coordax.Field, because no '
        f'coordinate type matched the dimensions starting with {dims}:\n'
        f'{data_array}\n\n'
        f'Reasons why coordinate matching failed:\n{reasons_str}'
    )

  while dims:
    coord = get_next_match()
    coords.append(coord)
    assert coord.ndim > 0  # dimensions will shrink by at least one
    dims = dims[coord.ndim :]

  return compose(*coords)
