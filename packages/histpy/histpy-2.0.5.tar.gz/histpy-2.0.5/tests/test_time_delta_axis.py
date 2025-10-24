from astropy.units import Quantity

from histpy import TimeAxis, Axis, TimeDeltaAxis

import numpy as np

import pytest

from astropy.time import Time, TimeDelta
from astropy import units as u

precision = 0.01*u.ns # Expected from Time
precision_sec = precision.to_value(u.s)
precision_sec_decimals = int(np.round(-np.log10(precision.to_value(u.s))))

def arr_eq(a:TimeDelta,b:TimeDelta):
    """
    Like np.arr_eq but for Time
    """
    return a.size == b.size and np.all(a == b)

def arr_approx(a:TimeDelta,b:TimeDelta):
    """
    Like np.arr_eq but for Time
    """
    return a.size == b.size and np.all(np.abs((a-b).sec) < precision_sec)

def delta_arr_approx(a:TimeDelta,b:Quantity):
    """
    Like np.arr_eq but for Time
    """
    return a.size == b.size and np.all(np.abs(a.sec - b.to_value(u.s)) < precision_sec)

def test_axis_init():

    # basic initialization
    x = TimeDelta([1.,2.,3.,4.,5.]*u.s)
    a = TimeDeltaAxis(x, label='Foo')

    assert len(a) == 5
    assert a.axis_scale == 'linear'

    # copies by default
    assert arr_eq(a.edges, x) and a.edges is not x

    # no copy
    b = TimeDeltaAxis(x, 'Foo', copy=False)

    assert b.edges is x

    # initialize from another axis
    c = TimeDeltaAxis(b)
    assert b == c

    # initialize with change of label
    c = TimeDeltaAxis(b, label='Bar')
    assert c.label == 'Bar'

    # later change of label
    c.label = 'Baz'
    assert c.label == 'Baz'

    # Only linear currently allowed
    # Fix this if other scales are implemented
    # in a sensible way for time values
    with pytest.raises(ValueError):
        c = TimeDeltaAxis(b, scale='log')

    # initialize with change of label
    c = TimeDeltaAxis(b, label='other')
    assert c.label == 'other'

    # change label after init
    c.label = 'another'
    assert c.label == 'another'

    # test copy
    c = TimeDeltaAxis(b, label='Foo')
    d = c.copy()
    assert c == d and not c._edges is d._edges

    # test replace_edges
    c = TimeDeltaAxis(x)
    edges = TimeDelta([1,2,3]*u.s)

    d = c.replace_edges(edges)
    assert arr_eq(d.edges, edges) and d.edges is not edges

    d = c.replace_edges(edges, copy=False)
    assert arr_eq(d.edges, edges) and d.edges is edges

    with pytest.raises(TypeError): # checks for invalid edges
        edges = np.array([0,1,2])
        d = c.replace_edges(edges)

    with pytest.raises(ValueError): # checks for invalid edges
        edges = TimeDelta([1, 0, 2]*u.s)
        d = c.replace_edges(edges)

    # validation of edge array

    with pytest.raises(ValueError):
        a = TimeDeltaAxis(TimeDelta([[0, 1, 2], [0, 1, 2]], format = 'jd')) # multi-dimensional array

    with pytest.raises(ValueError):
        a = TimeDeltaAxis(TimeDelta([0], format = 'jd')) # need two edges for a bin

    with pytest.raises(ValueError):
        a = TimeDeltaAxis(TimeDelta([1, 2, 1]*u.s)) # edges must be monotonically increasing

    # Init from a regular axis with time units
    a = Axis([0,2,3]*u.s)
    b = TimeDeltaAxis(a)
    assert b == TimeDeltaAxis(a.edges)

    # Init from quantity
    x = [1., 2., 3., 4., 5.] * u.s
    a = TimeDeltaAxis(x, label='Foo')

    assert a == TimeDeltaAxis(TimeDelta(x), label='Foo')

def test_axis_index():

    x = TimeDelta([1.,2.,3.,4.,5.]*u.s)
    a = TimeDeltaAxis(x, label='Foo')

    b = a[1:3]
    assert arr_eq(b.edges, x[1:4])

    b = a[1:100] # values past end of array are clipped when slicing
    assert arr_eq(b.edges, x[1:5])

    b = a[1:-1]
    assert arr_eq(b.edges, x[1:4])

    b = a[-2:-1]
    assert arr_eq(b.edges, x[2:4])

    b = a[2]
    assert arr_eq(b.edges, x[2:4])

    b = a[-1]
    assert arr_eq(b.edges, x[3:5])

    b = a[::2]
    assert arr_eq(b.edges, TimeDelta([1., 3., 5.]*u.s))

    b = a[1::2]
    assert arr_eq(b.edges, TimeDelta([2., 4.]*u.s))

    with pytest.raises(IndexError):
        a[0:0] # empty bin list

    with pytest.raises(IndexError):
        a[3:2] # reversed order

    with pytest.raises(IndexError):
        a[1:3:-1] # non-positive stride

    with pytest.raises(TypeError):
        # non-int, non-slice
        a[np.zeros(len(x) + 1, dtype=bool)]

def test_conversion_to_axis_units():

    # With no numeric formats
    x = TimeDelta([0,1]*u.d)
    a = TimeDeltaAxis(x)

    # Drop units. Defaults to JD
    assert a.to() == Axis([0,1])

    # Convert to the default day
    assert a.to(u.day) == Axis([0,1]*u.day)

    # Convert to something else
    assert a.to(u.s) == Axis([0,1]*u.day).to(u.s)

    # With numeric formats
    x = TimeDelta(TimeDelta([0, 1], format = 'sec'))
    a = TimeDeltaAxis(x)

    # Drop units. Default to current numeric format
    assert a.to() == Axis([0.,1.])

    # With units
    assert a.to(u.s) == Axis([0,1]*u.s)

    # Convert to something else
    assert a.to(u.day) == Axis([0,1]*u.s).to(u.day)

    # convert axis without unit to compatible time unit
    with pytest.raises(TypeError):
        a.to(unit=u.dimensionless_unscaled) # cannot convert Time to dimensionless unit

    with pytest.raises(TypeError):
        a.to(unit=u.m) # cannot convert Time to non-unit time

def test_bad_init():

    # I added this check no make it less error-prone

    with pytest.raises(TypeError):
        a = Axis(TimeDelta([0,1]*u.s))

    with pytest.raises(TypeError):
        a = Axis([TimeDelta(0*u.s), TimeDelta(1*u.s)])

    with pytest.raises(ValueError):
        a = TimeDeltaAxis([TimeDelta(0*u.s), TimeDelta(1*u.s)])


def test_axis_array():

    # With no numeric formats
    from datetime import timedelta

    # Create a timedelta
    delta0 = timedelta(days=0, hours=0, minutes=0)
    delta1 = timedelta(days=1, hours=0, minutes=0)


    x = TimeDelta([delta0, delta1])
    a = TimeDeltaAxis(x, label='Foo', scale='linear')

    y = np.array(a)

    # Default to JD
    assert np.array_equal(y, [0,1])

    # With numeric formats
    x = TimeDelta([0,1], format='sec')
    a = TimeDeltaAxis(x)

    y = np.array(a)

    # Defaults to the current numeric format
    assert np.array_equal(y, [0,1])

def test_axis_compare():

    x = TimeDelta([0,1,2], format = 'sec')
    a = TimeDeltaAxis(x, label='Foo')

    b = TimeDeltaAxis(x, label='Foo')
    assert a == b

    b = TimeDeltaAxis(x[:-1], label='Foo')
    assert a != b

    b = TimeDeltaAxis(x, label='Bar')
    assert a != b

def test_axis_findbin():

    # Test sub-ns precision

    x = TimeDelta([1.,2.,3.,4.,5.]*u.ns)
    a = TimeDeltaAxis(x)

    b = a.find_bin(TimeDelta(1.5*u.ns))
    assert(b == 0)

    # You can use quantities
    b = a.find_bin(4.5*u.ns)
    assert(b == 3)

    b = a.find_bin(2*u.ns)
    assert(b == 1)

    b = a.find_bin(2*u.ns, right=True)
    assert(b == 0)

    b = a.find_bin(0*u.ns) # underflow
    assert(b == -1)

    b = a.find_bin(6*u.ns) # overflow
    assert(b == a.nbins)


    # find_bin can take arrays
    b = a.find_bin([0.5, 1.5, 2.5, 3.5]*u.ns)
    assert(np.array_equal(b, [-1, 0, 1, 2]))

    # Bare values can be converted to TimeDelta using astropy default (jd)
    assert a.find_bin(3) == a.find_bin(3*u.d)

def test_axis_interp():

    def clamp(v:TimeDelta, lo:TimeDelta, hi:TimeDelta):

        # atleast_1d equivalent for Time
        if v.shape == ():
            v = v.reshape(-1)

        v[v > hi] = hi
        v[v < lo] = lo

        return v

    def res(b:TimeDelta, w:TimeDelta, c:TimeDelta):

        # Rearranged to work with Time.
        # Only deltas as meaningful not additions
        # return c[b[0]] * w[0] + c[b[1]] * w[1]

        return c[b[0]] + w[1]*(c[b[1]] - c[b[0]])

    x = TimeDelta([1., 2., 4., 8., 16.] * u.ns)

    # linear interpolation
    a = TimeDeltaAxis(x)
    c = a.centers
    e = a.edges

    # test interior values
    v = 5.*u.ns
    bins, weights = a.interp_weights(v)
    assert bins.shape == (2,) and weights.shape == (2,)
    assert np.all(bins >= 0) and np.all(bins < len(c))
    assert np.all(weights >= 0.) and np.all(weights <= 1.)
    assert np.all(res(bins, weights, c) == clamp(v, c[0], c[-1]))

    bins, weights = a.interp_weights_edges(v)
    assert bins.shape == (2,) and weights.shape == (2,)
    assert np.all(bins >= 0) and np.all(bins < len(e))
    assert np.all(weights >= 0.) and np.all(weights <= 1.)
    assert np.all(res(bins, weights, e) == clamp(v, e[0], e[-1]))

    v = 3. * u.ns
    bins, weights = a.interp_weights(v)
    assert np.all(bins >= 0) and np.all(bins < len(c))
    assert np.all(weights >= 0.) and np.all(weights <= 1.)
    assert np.all(res(bins, weights, c) == clamp(v, c[0], c[-1]))

    # test centers of boundary bins
    v = 1.5*u.ns
    bins, weights = a.interp_weights(v)
    assert np.all(bins >= 0) and np.all(bins < len(c))
    assert np.all(weights >= 0.) and np.all(weights <= 1.)
    assert np.all(res(bins, weights, c) == clamp(v, c[0], c[-1]))

    v = 12.*u.ns
    bins, weights = a.interp_weights(v)
    assert np.all(bins >= 0) and np.all(bins < len(c))
    assert np.all(weights >= 0.) and np.all(weights <= 1.)
    assert np.all(res(bins, weights, c) == clamp(v, c[0], c[-1]))

    # test exterior values
    v = 0.*u.ns
    bins, weights = a.interp_weights(v)
    assert np.all(bins >= 0) and np.all(bins < len(c))
    assert np.all(weights >= 0.) and np.all(weights <= 1.)
    assert np.all(res(bins, weights, c) == clamp(v, c[0], c[-1]))

    bins, weights = a.interp_weights_edges(v)
    assert np.all(bins >= 0) and np.all(bins < len(e))
    assert np.all(weights >= 0.) and np.all(weights <= 1.)
    assert np.all(res(bins, weights, e) == clamp(v, e[0], e[-1]))

    v = 20.*u.ns
    bins, weights = a.interp_weights(v)
    assert np.all(bins >= 0) and np.all(bins < len(c))
    assert np.all(weights >= 0.) and np.all(weights <= 1.)
    assert np.all(res(bins, weights, c) == clamp(v, c[0], c[-1]))

    # 0-D array should behave like scalar
    v = 5.*u.ns
    bins, weights = a.interp_weights(v)
    assert bins.shape == (2,) and weights.shape == (2,)
    assert np.all(bins >= 0) and np.all(bins < len(c))
    assert np.all(weights >= 0.) and np.all(weights <= 1.)
    assert np.all(res(bins, weights, c) == clamp(v, c[0], c[-1]))

    # 1-D array should behave like array
    v = [5.]*u.ns
    bins, weights = a.interp_weights(v)
    assert bins.shape == (2,1) and weights.shape == (2,1)
    assert np.all(bins >= 0) and np.all(bins < len(c))
    assert np.all(weights >= 0.) and np.all(weights <= 1.)
    assert np.all(res(bins, weights, c) == clamp(v, c[0], c[-1]))

    v = np.arange(0., 20.)*u.ns
    bins, weights = a.interp_weights(v)
    assert np.all(bins >= 0) and np.all(bins < len(c))
    assert np.all(weights >= 0.) and np.all(weights <= 1.)
    assert np.all(res(bins, weights, c) == clamp(v, c[0], c[-1]))

    # interp_weights result should preserve shape of input values,
    # even if they have unit dimensions
    v = np.array([ [ [ 3., 5., 9.], [2., 7., 0.] ] ])*u.ns
    bins, weights = a.interp_weights(v)
    assert bins.shape    == (2,) + v.shape
    assert weights.shape == (2,) + v.shape
    assert np.all(bins >= 0) and np.all(bins < len(c))
    assert np.all(weights >= 0.) and np.all(weights <= 1.)
    assert np.all(res(bins, weights, c) == clamp(v, c[0], c[-1]))

def test_axis_properties():

    x = [1.,2.,3.,4.,5.]*u.ns
    a = TimeDeltaAxis(x, label='Foo', scale='linear')

    assert arr_eq(a.lower_bounds, [1, 2, 3, 4]*u.ns)
    assert arr_eq(a.upper_bounds, [2, 3, 4, 5]*u.ns)
    assert arr_approx(a.bounds, [[1,2], [2,3], [3,4], [4,5]]*u.ns)
    assert arr_eq(a.lo_lim, 1*u.ns)
    assert arr_eq(a.hi_lim, 5*u.ns)
    assert delta_arr_approx(a.widths, [1, 1, 1, 1]*u.ns)
    assert a.label_with_unit == 'Foo [jd]'

    # Label units can be second if initialized with seconds
    x = TimeDelta([1., 2., 3., 4., 5.], format = 'sec')
    a = TimeDeltaAxis(x, label='Foo', scale='linear')
    assert a.label_with_unit == 'Foo [sec]'


def test_axis_centers():

    x = np.array([1.,2.,3.,4.,5.])*u.ns
    a = TimeDeltaAxis(x, label='Foo', scale='linear')

    c = a.centers
    assert arr_approx(c, [1.5, 2.5, 3.5, 4.5]*u.ns)

def test_axis_math():

    x = TimeDelta(np.array([1.,2.,3.,4.,5.]) * u.ns)
    a = TimeDeltaAxis(x, label='Foo', scale='linear')

    # Out of place ops
    # Only shifts are allowed
    with pytest.raises(RuntimeError):
        # Use unit to bypass TypeError
        b = a * (2*u.s)

    with pytest.raises(RuntimeError):
        # Use unit to bypass TypeError
        b = a / (2*u.s)

    b = a + 2*u.ns
    assert arr_approx(b.edges, x + 2*u.ns)

    b = a - 2*u.ns
    assert arr_eq(b.edges, x - 2*u.ns)

    # You can only shift by scalars
    with pytest.raises(ValueError):
        # Use unit to bypass TypeError
        b = a + x

    # Add reference time to get a TimeAxis
    t0 = Time.now()
    b = a + t0
    assert b == TimeAxis(t0 + x, label='Foo', scale='linear')

    # But only a scalar
    with pytest.raises(ValueError):
        b = a + (Time.now() + [0,1]*u.s)

    # in place ops
    x = np.array([1., 2., 3., 4., 5.]) * u.ns
    a = TimeDeltaAxis(x, label='Foo', scale='linear')

    # Only shifts are allowed
    b = a.copy()
    with pytest.raises(RuntimeError):
        # Use unit to bypass TypeError
        b *= 2*u.s

    b = a.copy()
    with pytest.raises(RuntimeError):
        # Use unit to bypass TypeError
        b /= 2*u.s

    b = a.copy()
    b += 2 * u.ns
    assert arr_approx(b.edges, x + 2 * u.ns)

    b = a.copy()
    b -= 2*u.ns
    assert arr_approx(b.edges, x - 2 * u.ns)

    # You can only shift by scalars
    b = a.copy()
    with pytest.raises(ValueError):
        # Use unit to bypass TypeError
        b += x


# reading and writing functions are tested by Histogram read/write tests



