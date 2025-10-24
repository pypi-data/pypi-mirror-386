import numpy
import pandas

from pandas.api.extensions import ExtensionDtype

if hasattr(pandas.core.arrays, 'NumpyExtensionArray'):
  # Pandas >=2.1
  NumpyArrayBaseClass = pandas.core.arrays.NumpyExtensionArray
else:
  # Pandas <2.1
  NumpyArrayBaseClass = pandas.core.arrays.PandasArray

from .numpy_ import ndarray as xpress_ndarray
from .numpy_ import array as xpress_array


class ObjectDType(ExtensionDtype):
  """A Pandas dtype which stores the series data in an ObjectArray,
  which wraps an xpress.ndarray."""

  name = 'xpressobj'
  type = numpy.object_
  kind = 'O'
  na_value = pandas.NA

  @classmethod
  def construct_array_type(cls):
    return ObjectArray


class ObjectArray(NumpyArrayBaseClass):
  dtype = ObjectDType()
  _typ = 'extension'  # Prevent Pandas from recognising this as a NumPy array and circumventing our customizations

  def __init__(self, values, copy=False):
    """Pandas does not seem to call this constructor (it instead calls class methods
    like _from_sequence), but we have to provide one that is compatible with
    NumpyExtensionArray: this accepts either an ndarray or a NumpyExtensionArray"""

    if isinstance(values, NumpyArrayBaseClass):
      values = values._ndarray

    if not isinstance(values, numpy.ndarray):
      raise ValueError(f"'values' must be a NumPy array, not {type(values).__name__}")

    if copy:
      values = values.copy()

    # Make sure we have an xpress.ndarray
    if not isinstance(values, xpress_ndarray):
      values = values.view(xpress_ndarray)

    # Circumvent the superconstructor, which would override our dtype with a NumpyEADtype
    super(NumpyArrayBaseClass, self).__init__(values, self.dtype)

  @classmethod
  def _from_sequence(cls, scalars, *, dtype=None, copy=False):
    """Create an ObjectArray from the given data"""
    if not (
      isinstance(dtype, ObjectDType) or
      str(dtype) != 'xpressobj' or
      dtype is None
    ):
      raise TypeError(f"Cannot construct a '{cls.__name__}' with dtype '{dtype}'")

    # Constructor expects some kind of ndarray
    if not isinstance(scalars, numpy.ndarray):
      # Note we must copy when converting a non-ndarray to an ndarray
      scalars = xpress_array(scalars, dtype='O')
      # But then we do not need to copy again below
      copy = False

    # Constructor will convert numpy.ndarray into xpress.ndarray
    return cls(scalars, copy=copy)

  def to_numpy(self, dtype=None, copy=False, na_value=pandas._libs.lib.no_default):
    """When the series is converted to a NumPy array, return the underlying ndarray"""
    if na_value is not pandas._libs.lib.no_default:
      raise NotImplementedError('na_value arg of to_numpy is not implemented')
    return numpy.array(self._ndarray, dtype=dtype, copy=copy, subok=True)

  def _accumulate(self, name, *, skipna=True, **kwargs):
    """Implement cumsum/cumprod"""
    if name == 'cumsum':
      ufunc = numpy.add
    elif name == 'cumprod':
      ufunc = numpy.multiply
    else:
      return NotImplemented
    if skipna and self.isna().any():
      # Filter out N/A values
      data = self._ndarray[~self.isna()]
    else:
      data = self._ndarray
    acc = ufunc.accumulate(data)
    return type(self)(acc)

  def _apply_op_unwrapped(self, other, op):
    # For compatibility with Pandas, [NA] == [NA] should produce [False],
    # despite the scalar comparison NA == NA producing NA. This is an
    # intentional decision by Pandas. Note that None also behaves like NA.
    self_is_na = self.isna()
    other_is_scalar = not (isinstance(other, list) or hasattr(other, '__array__'))
    if other_is_scalar:
      if pandas.isna(other):
        # Return all false
        result = numpy.full(len(self), False, dtype='O')
        return type(self)(result)
      elif self.isna().any():
        # Start with the results for the NA values
        result = numpy.full(len(self), False, dtype='O')
        # Apply the operator to non-NA values
        result[~self_is_na] = self._apply_op_unwrapped_no_na(self[~self_is_na], other, op)
        return type(self)(result)
    else:
      # Non-scalar RHS
      either_is_na = self_is_na | pandas.isna(other)
      if either_is_na.any():
        # Start with the results for the NA values
        result = numpy.full(len(self), False, dtype='O')
        result[~either_is_na] = self._apply_op_unwrapped_no_na(self[~either_is_na], other[~either_is_na], op)
        return type(self)(result)
    # No NA values in either operand
    return self._apply_op_unwrapped_no_na(self, other, op)

  def _apply_op_unwrapped_no_na(self, lhs, rhs, op):
    if isinstance(rhs, NumpyArrayBaseClass):
      rhs = rhs._ndarray
    result = op(lhs._ndarray, rhs)
    if isinstance(result, numpy.ndarray):
      return self._wrap_ndarray_result(result)
    return result

  def _cmp_method(self, other, op):
    """Apply comparison operators to the underlying array, so that our custom
    <=, >=, and == implementations can produce constraints.

    Called by OpsMixin, inherited by NumpyExtensionArray.
    """
    return self._apply_op_unwrapped(other, op)

  def _logical_method(self, other, op):
    """Apply logical operators to the underlying array, so that our custom
     & and | implementations can produce nonlinear logical terms.

    Called by OpsMixin, inherited by NumpyExtensionArray.
    """
    return self._apply_op_unwrapped(other, op)
