import numpy
import _xpress


class ndarray(numpy.ndarray):
  """Ensures that the results of Xpress overloaded comparator
  operators do not get cast to Booleans"""

  def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
    """Called whenever a ufunc is invoked and at least one argument is an
    xpress.ndarray. Calls the correct ufunc implementation, then wraps
    the result in an xpress.ndarray."""
    args = []
    # Convert inputs from xpress.ndarray to numpy.ndarray to avoid
    # recursion into __array_ufunc__
    for i in inputs:
      if isinstance(i, ndarray):
        args.append(i.view(numpy.ndarray))
      else:
        args.append(i)
    # Convert outputs from xpress.ndarray to numpy.ndarray to avoid
    # recursion into __array_ufunc__
    out = kwargs.get('out')
    if out is not None:
      kwargs['out'] = tuple(
        o.view(numpy.ndarray) if isinstance(o, ndarray) else o
        for o in out
      )
    # Only invoke our ufunc if there is at least one object arg
    if any(isinstance(a, numpy.ndarray) and a.dtype.flags & 1 for a in args):
      if ufunc == numpy.less_equal:
        ufunc = _xpress.less_equal_obj
      elif ufunc == numpy.greater_equal:
        ufunc = _xpress.greater_equal_obj
      if ufunc == numpy.less:
        ufunc = _xpress.less_obj
      elif ufunc == numpy.greater:
        ufunc = _xpress.greater_obj
      elif ufunc == numpy.equal:
        ufunc = _xpress.equal_obj
      elif ufunc == numpy.not_equal:
        ufunc = _xpress.not_equal_obj
    res = getattr(ufunc, method)(*args, **kwargs)
    if isinstance(res, numpy.ndarray):
      # Convert array result from numpy.ndarray to xpress.ndarray
      return res.view(ndarray)
    else:
      # Scalar result
      return res


def array(*args, **kwargs):
  """Convenience function for constructing an xpress.ndarray"""
  return numpy.array(*args, **kwargs).view(ndarray)
