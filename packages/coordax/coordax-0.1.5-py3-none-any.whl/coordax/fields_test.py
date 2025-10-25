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
import dataclasses
import functools
import math
import operator
import re
import textwrap

from absl.testing import absltest
from absl.testing import parameterized
import chex
import coordax
from coordax import ndarrays
from coordax import testing
import jax
import jax.numpy as jnp
import numpy as np


class FieldTest(parameterized.TestCase):

  @parameterized.named_parameters(
      dict(
          testcase_name='view_with_name',
          array=np.arange(5 * 3).reshape((5, 3)),
          tags=('i', 'j'),
          untags=('i',),
          expected_dims=(None, 'j'),
          expected_named_shape={'j': 3},
          expected_positional_shape=(5,),
          expected_coord_field_keys=set(),
      ),
      dict(
          testcase_name='view_with_name_and_coord',
          array=np.arange(5 * 3).reshape((5, 3, 1)),
          tags=('i', 'j', coordax.LabeledAxis('k', np.arange(1))),
          untags=('j',),
          expected_dims=('i', None, 'k'),
          expected_named_shape={'i': 5, 'k': 1},
          expected_positional_shape=(3,),
          expected_coord_field_keys=set(['k']),
      ),
  )
  def test_field_properties(
      self,
      array: np.ndarray,
      tags: tuple[str | coordax.Coordinate, ...],
      untags: tuple[str | coordax.Coordinate, ...],
      expected_dims: tuple[str | int, ...],
      expected_named_shape: dict[str, int],
      expected_positional_shape: tuple[int, ...],
      expected_coord_field_keys: set[str],
  ):
    """Tests that field properties are correctly set."""
    field = coordax.Field(array).tag(*tags)
    if untags:
      field = field.untag(*untags)
    testing.assert_field_properties(
        actual=field,
        data=array,
        dims=expected_dims,
        named_shape=expected_named_shape,
        positional_shape=expected_positional_shape,
        coord_field_keys=expected_coord_field_keys,
    )

  def test_field_constructor_default_coords(self):
    field = coordax.Field(np.zeros((2, 3, 4)), dims=('x', None, 'z'))
    expected_coords = {}
    self.assertEqual(field.axes, expected_coords)

  def test_field_constructor_invalid(self):
    product_xy = coordax.CartesianProduct(
        (coordax.SizedAxis('x', 2), coordax.SizedAxis('y', 3))
    )
    with self.assertRaisesWithLiteralMatch(
        ValueError,
        'all coordinates in the axes dict must be 1D, got'
        " CartesianProduct(coordinates=(coordax.SizedAxis('x', size=2),"
        " coordax.SizedAxis('y', size=3))) for dimension x. Consider using"
        ' Field.tag() instead to associate multi-dimensional coordinates.',
    ):
      coordax.Field(np.zeros(3), axes={'x': product_xy})

    with self.assertRaisesWithLiteralMatch(
        ValueError,
        "coordinate under key 'x' in the axes dict must have dims=('x',) but"
        " got coord.dims=('y',)",
    ):
      coordax.Field(
          np.zeros((2, 3)),
          dims=('x', 'y'),
          axes={
              'x': coordax.SizedAxis('y', 2),
              'y': coordax.SizedAxis('x', 3),
          },
      )

    with self.assertRaisesWithLiteralMatch(
        ValueError,
        'axis keys must be a subset of the named dimensions of the'
        " underlying named array, got axis keys {'y'} vs data"
        " dimensions {'x'}",
    ):
      coordax.Field(
          np.zeros(3), dims=('x',), axes={'y': coordax.SizedAxis('y', 3)}
      )

    with self.assertRaisesWithLiteralMatch(
        ValueError,
        textwrap.dedent("""\
            inconsistent size for dimension 'x' between data and coordinates: 3 vs 4 on named array vs coordinate:
            NamedArray(
                data=array([0., 0., 0.]),
                dims=('x',),
            )
            coordax.SizedAxis('x', size=4)"""),
    ):
      coordax.Field(
          np.zeros(3), dims=('x',), axes={'x': coordax.SizedAxis('x', 4)}
      )

  def test_field_coordinate_property(self):
    x = coordax.LabeledAxis('x', np.arange(2))
    field = coordax.wrap(np.zeros((2, 3)), x, 'y')
    expected_coord = coordax.compose_coordinates(x, coordax.DummyAxis('y', 3))
    self.assertEqual(field.coordinate, expected_coord)

  def test_field_treedef_independent_of_tag_order(self):
    x, y = coordax.SizedAxis('x', 2), coordax.SizedAxis('y', 3)
    field_a = coordax.wrap(np.ones((2, 3)), None, y)
    field_a = field_a.tag(x)
    field_b = coordax.wrap(np.ones((2, 3)), x, None)
    field_b = field_b.tag(y)
    chex.assert_trees_all_equal(field_a, field_b)

  def test_field_binary_op_sum_simple(self):
    field_a = coordax.wrap(np.arange(2 * 3 * 4).reshape((2, 4, 3)))
    field_b = coordax.wrap(np.arange(2 * 3 * 4).reshape((2, 4, 3)))
    actual = operator.add(field_a, field_b)
    expected_result = coordax.wrap(np.arange(2 * 3 * 4).reshape((2, 4, 3)) * 2)
    testing.assert_fields_allclose(actual=actual, desired=expected_result)

  def test_field_binary_op_sum_aligned(self):
    field_a = coordax.wrap(np.arange(2 * 3).reshape((2, 3)), 'x', 'y')
    field_b = coordax.wrap(np.arange(2 * 3)[::-1].reshape((3, 2)), 'y', 'x')
    actual = operator.add(field_a, field_b)
    expected_result = coordax.wrap(np.array([[5, 4, 3], [7, 6, 5]]), 'x', 'y')
    testing.assert_fields_allclose(actual=actual, desired=expected_result)

  def test_field_binary_op_product_aligned(self):
    field_a = coordax.wrap(np.arange(2 * 3).reshape((2, 3))).tag('x', 'y')
    field_b = coordax.wrap(np.arange(2), 'x')
    actual = operator.mul(field_a, field_b)
    expected_result = coordax.wrap(
        np.arange(2 * 3).reshape((2, 3)) * np.array([[0], [1]])
    ).tag('x', 'y')
    testing.assert_fields_allclose(actual=actual, desired=expected_result)

  def test_field_repr(self):
    expected = "<Field dims=('x', 'y') shape=(2, 3) axes={'y': LabeledAxis} >"
    actual = coordax.wrap(
        np.array([[1, 2, 3], [4, 5, 6]]),
        'x',
        coordax.LabeledAxis('y', np.array([7, 8, 9])),
    )
    self.assertEqual(repr(actual), expected)

  @parameterized.named_parameters(
      dict(
          testcase_name='_name_&_name',
          array=np.arange(4),
          tags=('idx',),
          untags=('idx',),
      ),
      dict(
          testcase_name='coord_&_name',
          array=np.arange(4),
          tags=(coordax.SizedAxis('idx', 4),),
          untags=('idx',),
      ),
      dict(
          testcase_name='coord_&_coord',
          array=np.arange(4),
          tags=(coordax.SizedAxis('idx', 4),),
          untags=(coordax.SizedAxis('idx', 4),),
      ),
      dict(
          testcase_name='names_&_partial_name',
          array=np.arange(2 * 3).reshape((2, 3)),
          tags=('x', 'y'),
          untags=('x',),
          full_unwrap=False,
      ),
      dict(
          testcase_name='names_&_dummy_axes',
          array=np.arange(2 * 3).reshape((2, 3)),
          tags=('x', 'y'),
          untags=(coordax.DummyAxis('x', 2), coordax.DummyAxis('y', 3)),
          full_unwrap=True,
      ),
      dict(
          testcase_name='product_coord_&_product_coord',
          array=np.arange(2 * 3).reshape((2, 3)),
          tags=(
              coordax.compose_coordinates(
                  coordax.SizedAxis('x', 2),
                  coordax.SizedAxis('y', 3),
              ),
          ),
          untags=(
              coordax.compose_coordinates(
                  coordax.SizedAxis('x', 2),
                  coordax.SizedAxis('y', 3),
              ),
          ),
          full_unwrap=True,
      ),
      dict(
          testcase_name='product_coord_&_names',
          array=np.arange(2 * 3).reshape((2, 3)),
          tags=(
              coordax.compose_coordinates(
                  coordax.SizedAxis('x', 2),
                  coordax.SizedAxis('y', 3),
              ),
          ),
          untags=('x', 'y'),
          full_unwrap=True,
      ),
      dict(
          testcase_name='mixed_&_names',
          array=np.arange(2 * 3 * 4).reshape((2, 4, 3)),
          tags=('x', coordax.SizedAxis('y', 4), 'z'),
          untags=('y', 'z'),
          full_unwrap=False,
      ),
      dict(
          testcase_name='mixed_&_wrong_names',
          array=np.arange(2 * 3 * 4).reshape((2, 4, 3)),
          tags=('x', coordax.SizedAxis('y_prime', 4), 'z'),
          untags=('y', 'z'),
          full_unwrap=False,
          should_raise_on_untag=True,
      ),
      dict(
          testcase_name='coord_&_wrong_coord_value',
          array=np.arange(9),
          tags=(coordax.LabeledAxis('z', np.arange(9)),),
          untags=(coordax.LabeledAxis('z', np.arange(9) + 1),),
          full_unwrap=False,
          should_raise_on_untag=True,
      ),
      dict(
          testcase_name='scalar',
          array=np.array(3.14, dtype=np.float32),
          tags=(coordax.Scalar(),),
          untags=(coordax.Scalar(),),
          full_unwrap=True,
          should_raise_on_untag=False,
      ),
      dict(
          testcase_name='coord_&_duplicate_scalar',
          array=np.arange(9),
          tags=(
              coordax.Scalar(),
              coordax.LabeledAxis('z', np.arange(9)),
          ),
          untags=(coordax.Scalar(), coordax.Scalar()),
          full_unwrap=False,
          should_raise_on_untag=False,
      ),
  )
  def test_tag_then_untag_by(
      self,
      array: np.ndarray,
      tags: tuple[str | coordax.Coordinate, ...],
      untags: tuple[str | coordax.Coordinate, ...],
      should_raise_on_untag: bool = False,
      full_unwrap: bool = True,
  ):
    """Tests that tag and untag on Field work as expected."""
    with self.subTest('tag'):
      field = coordax.Field(array).tag(*tags)
      expected_dims = sum(
          [
              tag.dims if isinstance(tag, coordax.Coordinate) else (tag,)
              for tag in tags
          ],
          start=tuple(),
      )
      chex.assert_trees_all_equal(field.dims, expected_dims)

    with self.subTest('untag'):
      if should_raise_on_untag:
        with self.assertRaises(ValueError):
          field.untag(*untags)
      else:
        untagged = field.untag(*untags)
        if full_unwrap:
          unwrapped = untagged.unwrap()
          np.testing.assert_array_equal(unwrapped, array)

  def test_broadcast_like(self):
    x = coordax.LabeledAxis('x', np.linspace(0, 1, 4))
    y = coordax.LabeledAxis('y', np.linspace(5, 10, 5))
    z = coordax.LabeledAxis('z', np.linspace(0, np.pi, 7))
    yxz = coordax.compose_coordinates(y, x, z)
    field = coordax.wrap(np.arange(4), x)
    other = coordax.wrap(np.ones((5, 4, 7)), yxz)
    expected_data = np.tile(np.arange(4)[np.newaxis, :, np.newaxis], (5, 1, 7))
    actual = field.broadcast_like(other)
    expected = coordax.wrap(expected_data, yxz)
    testing.assert_fields_allclose(actual=actual, desired=expected)

    actual = field.broadcast_like(other.untag('y'))
    expected = coordax.wrap(expected_data, yxz).untag('y')
    testing.assert_fields_allclose(actual=actual, desired=expected)

  def test_broadcast_like_invalid_coords(self):
    x = coordax.LabeledAxis('x', np.linspace(0, 1, 4, endpoint=False))
    x_mismatch = coordax.LabeledAxis('x', np.linspace(0, 1, 4, endpoint=True))
    field = coordax.wrap(np.arange(4), x)
    other = coordax.wrap(np.ones((1, 4)), 'y', x_mismatch)
    with self.assertRaisesRegex(
        ValueError,
        re.escape(
            'cannot broadcast field because axes corresponding to dimension '
            f"'x' do not match: {x} vs {x_mismatch}"
        )
    ):
      field.broadcast_like(other)

  def test_broadcast_to_coordinate(self):
    x, y = coordax.SizedAxis('x', 4), coordax.SizedAxis('y', 5)
    z = coordax.LabeledAxis('z', np.linspace(0, np.pi, 7))
    field = coordax.wrap(np.arange(4), x)
    yxz = coordax.compose_coordinates(y, x, z)
    expected_data = np.tile(np.arange(4)[np.newaxis, :, np.newaxis], (5, 1, 7))
    actual = field.broadcast_like(yxz)
    expected = coordax.wrap(expected_data, yxz)
    testing.assert_fields_allclose(actual=actual, desired=expected)

  def test_cmap_cos(self):
    """Tests that cmap works as expected."""
    inputs = (
        coordax.wrap(np.arange(2 * 3 * 4).reshape((2, 4, 3)))
        .tag('x', 'y', 'z')
        .untag('x')
    )
    actual = coordax.cmap(jnp.cos)(inputs)
    expected_values = jnp.cos(inputs.data)
    testing.assert_field_properties(
        actual=actual,
        data=expected_values,
        dims=(None, 'y', 'z'),
        shape=expected_values.shape,
        coord_field_keys=set(),
    )

  def test_cmap_norm(self):
    """Tests that cmap works as expected."""
    inputs = (
        coordax.wrap(np.arange(2 * 3 * 5).reshape((2, 3, 5)))
        .tag('x', coordax.LabeledAxis('y', np.arange(3)), 'z')
        .untag('x', 'z')
    )
    actual = coordax.cmap(jnp.linalg.norm)(inputs)
    expected_values = jnp.linalg.norm(inputs.data, axis=(0, 2))
    testing.assert_field_properties(
        actual=actual,
        data=expected_values,
        dims=('y',),
        shape=expected_values.shape,
        coord_field_keys=set(['y']),
    )

  def test_cmap_out_axes_options(self):
    data = np.arange(2 * 3 * 4).reshape((2, 3, 4))
    x_axis = coordax.LabeledAxis('x', np.arange(2))
    z_axis = coordax.LabeledAxis('z', np.arange(4))
    field = coordax.wrap(data, x_axis, None, z_axis)

    with self.subTest('leading'):
      expected = coordax.wrap(data.transpose(0, 2, 1), x_axis, z_axis, None)
      actual = coordax.cmap(lambda x: x, out_axes='leading')(field)
      testing.assert_fields_allclose(actual, expected)

    with self.subTest('trailing'):
      expected = coordax.wrap(data.transpose(1, 0, 2), None, x_axis, z_axis)
      actual = coordax.cmap(lambda x: x, out_axes='trailing')(field)
      testing.assert_fields_allclose(actual, expected)

    with self.subTest('same_as_input'):
      expected = field
      actual = coordax.cmap(lambda x: x, out_axes='same_as_input')(field)
      testing.assert_fields_allclose(actual, expected)

  def test_cpmap_example(self):
    data = np.arange(2 * 3 * 4).reshape((2, 3, 4))
    x_axis = coordax.LabeledAxis('x', np.arange(2))
    y_axis = coordax.LabeledAxis('y', np.arange(4))
    field = coordax.wrap(data, x_axis, None, y_axis)

    def normalize_fn(array_slice):
      return array_slice / jnp.linalg.norm(array_slice)

    actual = coordax.cpmap(normalize_fn)(field)

    expected_data = data / jnp.linalg.norm(data, axis=1)[:, np.newaxis, :]
    expected = coordax.wrap(expected_data, x_axis, None, y_axis)
    testing.assert_fields_allclose(actual, expected)

  def test_jit(self):
    trace_count = 0

    @jax.jit
    def f(x):
      nonlocal trace_count
      trace_count += 1
      return x

    field = coordax.wrap(np.arange(3), 'x')
    actual = f(field)
    testing.assert_fields_allclose(actual=actual, desired=field)
    self.assertEqual(trace_count, 1)

    f(field + 1)  # should not be traced again
    self.assertEqual(trace_count, 1)

  def test_jax_transforms(self):
    """Tests that vmap/scan work with Field with leading positional axes."""
    x_coord = coordax.LabeledAxis('x', np.array([2, 3, 7]))
    batch, length = 4, 10
    vmap_axis = coordax.SizedAxis('vmap', batch)
    scan_axis = coordax.LabeledAxis('scan', np.arange(length))

    def initialize(data):
      return coordax.wrap(data, x_coord)

    def body_fn(c, _):
      return (c + 1, c)

    with self.subTest('scan'):
      data = np.zeros(x_coord.shape)
      init = initialize(data)
      _, scanned = jax.lax.scan(body_fn, init, length=length)
      scanned = scanned.tag(scan_axis)
      testing.assert_field_properties(
          actual=scanned,
          dims=('scan', 'x'),
          shape=(length,) + x_coord.shape,
      )

    with self.subTest('vmap'):
      batch_data = np.zeros(vmap_axis.shape + x_coord.shape)
      batch_init = jax.vmap(initialize)(batch_data)
      batch_init = batch_init.tag(vmap_axis)
      testing.assert_field_properties(
          batch_init, dims=('vmap', 'x'), shape=batch_data.shape
      )

    with self.subTest('vmap_of_scan'):
      batch_data = np.zeros(vmap_axis.shape + x_coord.shape)
      batch_init = jax.vmap(initialize)(batch_data)
      scan_fn = functools.partial(jax.lax.scan, body_fn, length=length)
      _, scanned = jax.vmap(scan_fn, in_axes=0)(batch_init)
      scanned = scanned.tag(vmap_axis, scan_axis)
      testing.assert_field_properties(
          actual=scanned,
          dims=('vmap', 'scan', 'x'),
          shape=(batch, length) + x_coord.shape,
      )

    with self.subTest('scan_of_vmap'):
      batch_data = np.zeros(vmap_axis.shape + x_coord.shape)
      batch_init = jax.vmap(initialize)(batch_data)
      vmapped_body_fn = jax.vmap(body_fn)
      scan_fn = functools.partial(jax.lax.scan, vmapped_body_fn, length=length)
      _, scanned = scan_fn(batch_init)
      scanned = scanned.tag(scan_axis, vmap_axis)
      testing.assert_field_properties(
          actual=scanned,
          dims=('scan', 'vmap', 'x'),
          shape=(length, batch) + x_coord.shape,
      )

  def test_tag_and_untag_function(self):
    data = np.arange(2 * 3).reshape((2, 3))
    inputs = {'a': coordax.Field(data), 'b': 42}

    expected = {'a': coordax.wrap(data, 'x', 'y'), 'b': 42}
    tagged = coordax.tag(inputs, 'x', 'y')
    jax.tree.map(np.testing.assert_array_equal, tagged, expected)

    untagged = coordax.untag(tagged, 'x', 'y')
    jax.tree.map(np.testing.assert_array_equal, untagged, inputs)

  def test_dummy_axis_named(self):
    axis = coordax.DummyAxis(name='x', size=5)
    expected = coordax.Field(np.arange(5), dims=('x',))

    actual = coordax.Field(np.arange(5)).tag(axis)
    testing.assert_fields_equal(actual, expected)

    actual = coordax.Field(np.arange(5), dims=('x',), axes={'x': axis})
    testing.assert_fields_equal(actual, expected)

  def test_dummy_axis_unnamed(self):
    axis = coordax.DummyAxis(name=None, size=5)
    expected = coordax.Field(np.arange(5), dims=(None,))
    actual = coordax.Field(np.arange(5)).tag(axis)
    testing.assert_fields_equal(actual, expected)

  def test_dummy_axis_cartesian_product(self):
    x = coordax.DummyAxis(name='x', size=2)
    y = coordax.DummyAxis(name=None, size=3)
    z = coordax.SizedAxis('z', 4)
    product = coordax.CartesianProduct((x, y, z))
    expected = coordax.Field(
        np.zeros((2, 3, 4)), dims=('x', None, 'z'), axes={'z': z}
    )
    actual = coordax.Field(np.zeros((2, 3, 4))).tag(product)
    testing.assert_fields_equal(actual, expected)

  def test_dummy_axis_error_handling(self):
    axis = coordax.DummyAxis(name='x', size=5)

    expected_messsage = textwrap.dedent("""\
        inconsistent size for dimension 'x' between data and coordinates: 4 vs 5 on named array vs coordinate:
        NamedArray(
            data=array([0, 1, 2, 3]),
            dims=('x',),
        )
        coordax.DummyAxis('x', size=5)""")

    with self.assertRaisesWithLiteralMatch(ValueError, expected_messsage):
      coordax.Field(np.arange(4)).tag(axis)

    with self.assertRaisesWithLiteralMatch(ValueError, expected_messsage):
      coordax.Field(np.arange(4), dims=('x',), axes={'x': axis})

  def test_shape_struct_field(self):
    x, y = coordax.DummyAxis('x', 2), coordax.LabeledAxis('y', np.arange(3))
    dummy_data = jax.ShapeDtypeStruct(x.shape + y.shape, jnp.float32)

    with self.subTest('fully_labeled'):
      f = coordax.shape_struct_field(x, y)
      testing.assert_field_properties(
          actual=f,
          dims=('x', 'y'),
          named_shape={'x': 2, 'y': 3},
          positional_shape=(),
          coord_field_keys=set(['y']),
      )
      self.assertEqual(f.data, dummy_data)

    with self.subTest('partially_labeled'):
      f = coordax.shape_struct_field(coordax.DummyAxis(None, 2), y)
      testing.assert_field_properties(
          actual=f,
          dims=(None, 'y'),
          named_shape={'y': 3},
          positional_shape=(2,),
          coord_field_keys=set(['y']),
      )
      self.assertEqual(f.data, dummy_data)

  def test_shape_struct_field_as_eval_shape_arg(self):
    x, y = coordax.DummyAxis('x', 2), coordax.LabeledAxis('y', np.arange(3))
    f = coordax.shape_struct_field(x, y)

    def fn_on_field(x: coordax.Field):
      return coordax.cmap(jnp.stack)([x, x])

    out_shape = jax.eval_shape(fn_on_field, f)
    testing.assert_field_properties(
        actual=out_shape,
        dims=(None, 'x', 'y'),
        named_shape={'x': 2, 'y': 3},
        positional_shape=(2,),
    )

  def test_duckarray(self):

    @jax.tree_util.register_dataclass
    @dataclasses.dataclass
    class Duck(ndarrays.NDArray):
      a: jnp.ndarray
      b: jnp.ndarray

      @property
      def shape(self) -> tuple[int, ...]:
        return self.a.shape

      @property
      def size(self) -> int:
        return math.prod(self.a.shape)

      @property
      def ndim(self) -> int:
        return len(self.a.shape)

      def __getitem__(self, value):
        return Duck(self.a[value], self.b[value])

      def transpose(self, axes: tuple[int, ...]):
        return Duck(self.a.transpose(axes), self.b.transpose(axes))

      def __add__(self, other: int):
        # intentionally implement something funny, that is not equal to
        # jax.tree.map(jnp.add, self, other)
        return Duck(self.a * other, self.b * other)

    duck = Duck(a=jnp.array([1, 2]), b=jnp.array([3, 4]))
    field = coordax.Field(duck)
    np.testing.assert_array_equal(field.data.a, jnp.array([1, 2]))
    np.testing.assert_array_equal(field.data.b, jnp.array([3, 4]))
    self.assertEqual(field.shape, (2,))
    self.assertIsNone(field.dtype)

    def is_duck_identity(x):
      self.assertIsInstance(x, Duck)
      return x

    result = coordax.cmap(is_duck_identity)(field)
    testing.assert_fields_equal(result, field)

    expected = coordax.Field(duck + 2)
    actual = field + 2
    testing.assert_fields_equal(actual, expected)

    actual = jax.jit(coordax.cmap(lambda x: x + 2))(field)
    testing.assert_fields_equal(actual, expected)

    array_2d = jax.tree.map(lambda x: x[jnp.newaxis, :], field).tag('x', 'y')
    expected = coordax.Field(
        Duck(a=jnp.array([[1], [2]]), b=jnp.array([[3], [4]])), dims=('y', 'x')
    )
    actual = array_2d.order_as('y', 'x')
    testing.assert_fields_equal(actual, expected)

    actual = coordax.wrap_like(expected.data, expected)
    testing.assert_fields_equal(actual, expected)

    array_3d = jax.tree.map(lambda x: x[jnp.newaxis, ...], array_2d)
    actual = jax.vmap(lambda x: x.order_as('y', 'x'))(array_3d).tag('z')
    expected = coordax.Field(
        Duck(a=jnp.array([[[1], [2]]]), b=jnp.array([[[3], [4]]])),
        dims=('z', 'y', 'x'),
    )
    testing.assert_fields_equal(actual, expected)

    x = coordax.LabeledAxis('x', np.array([np.e, np.pi]))
    y = coordax.LabeledAxis('y', np.linspace(0, 1, 2))
    other = coordax.wrap(
        Duck(a=jnp.zeros((2, 2)), b=jnp.zeros((2, 2))), x, y
    )
    actual = field.tag(x).broadcast_like(other)
    expected = coordax.wrap(
        Duck(a=jnp.array([[1, 1], [2, 2]]), b=jnp.array([[3, 3], [4, 4]])),
        x, y
    )
    testing.assert_fields_equal(actual, expected)

    actual = field.tag(y).broadcast_like(other)
    expected = coordax.wrap(
        Duck(a=jnp.array([[1, 2], [1, 2]]), b=jnp.array([[3, 4], [3, 4]])),
        x, y
    )
    testing.assert_fields_equal(actual, expected)

  def test_cmap_with_custom_vmap(self):

    @dataclasses.dataclass
    class NonPytree:
      a: jnp.ndarray

    def custom_vmap(fun, in_axes, out_axes, **kwargs):
      def mapped_fun(*args) -> jax.Array:
        leaves, argdef = jax.tree.flatten(args)
        leaves = [x.a if isinstance(x, NonPytree) else x for x in leaves]
        args = jax.tree.unflatten(argdef, leaves)
        return jax.vmap(fun, in_axes, out_axes, **kwargs)(*args)
      return mapped_fun

    def foo(x, y):
      assert y.ndim == 1  # will only run under vmap on 2d inputs.
      return x + y

    i_grid = coordax.LabeledAxis('i', np.arange(7))
    y = coordax.wrap(jnp.arange(5 * 7).reshape((5, 7)), None, i_grid)
    array_x = jnp.arange(5)[::-1]
    expected = coordax.cmap(foo)(array_x, y)
    actual = coordax.cmap(foo, vmap=custom_vmap)(NonPytree(a=array_x), y)
    testing.assert_fields_allclose(actual, expected)

  def test_get_coordinate(self):
    axes = {
        'x': coordax.LabeledAxis('x', np.arange(2)),
        'y': coordax.LabeledAxis('y', 2 + np.arange(3)),
        'z': coordax.LabeledAxis('z', 3 * np.arange(4)),
    }
    field = coordax.Field(
        np.arange(2 * 3 * 4).reshape((2, 3, 4)),
        dims=('x', 'y', 'z'),
        axes=axes,
    )
    with self.subTest('default'):
      actual = coordax.get_coordinate(field)
      expected = coordax.compose_coordinates(
          *[axes[d] for d in ['x', 'y', 'z']]
      )
      self.assertEqual(actual, expected)

    with self.subTest('with_positional_dims'):
      actual = coordax.get_coordinate(field.untag('y'))
      expected = coordax.compose_coordinates(
          axes['x'], coordax.DummyAxis(None, 3), axes['z']
      )
      self.assertEqual(actual, expected)

    with self.subTest('with_name_only_dims'):
      actual = coordax.get_coordinate(field.untag('y', 'z').tag('g', 'h'))
      expected = coordax.compose_coordinates(
          axes['x'],
          coordax.DummyAxis('g', 3),
          coordax.DummyAxis('h', 4),
      )
      self.assertEqual(actual, expected)

    with self.subTest('with_positional_dims_and_missing_axes=skip'):
      actual = coordax.get_coordinate(
          field.untag('x', 'z'), missing_axes='skip'
      )
      expected = axes['y']
      self.assertEqual(actual, expected)

    with self.subTest('with_name_only_dims_and_missing_axes=skip'):
      actual = coordax.get_coordinate(
          field.untag('x', 'z').tag('g', 'h'), missing_axes='skip'
      )
      expected = axes['y']  # since 'g' and 'h' are dummy axes.
      self.assertEqual(actual, expected)

    with self.subTest('with_positional_dims_and_missing_axes=error'):
      expected_message = (
          "field.dims=('x', 'y', None) has unnamed dims and"
          " missing_axes='error'"
      )
      with self.assertRaisesWithLiteralMatch(ValueError, expected_message):
        coordax.get_coordinate(field.untag('z'), missing_axes='error')


if __name__ == '__main__':
  absltest.main()
