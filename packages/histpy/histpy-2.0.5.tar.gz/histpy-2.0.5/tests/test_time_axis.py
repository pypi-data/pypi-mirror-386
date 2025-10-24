from astropy.units import Quantity

from histpy import TimeAxis, Axis, TimeDeltaAxis

import numpy as np

import pytest
from pytest import approx

from astropy.time import Time, TimeDelta
from astropy import units as u

precision = 0.01*u.ns # Expected from Time
precision_sec = precision.to_value(u.s)
precision_sec_decimals = int(np.round(-np.log10(precision.to_value(u.s))))

def arr_eq(a:Time,b:Time):
    """
    Like np.arr_eq but for Time
    """
    return a.size == b.size and np.all(a == b)

def arr_approx(a:Time,b:Time):
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
    x = Time.now() + [1.,2.,3.,4.,5.]*u.s
    a = TimeAxis(x, label='Foo')

    assert len(a) == 5
    assert a.axis_scale == 'linear'

    # copies by default
    assert arr_eq(a.edges, x) and a.edges is not x

    # no copy
    b = TimeAxis(x, 'Foo', copy=False)

    assert b.edges is x

    # initialize from another axis
    c = TimeAxis(b)
    assert b == c

    # initialize with change of label
    c = TimeAxis(b, label='Bar')
    assert c.label == 'Bar'

    # later change of label
    c.label = 'Baz'
    assert c.label == 'Baz'

    # Only linear currently allowed
    # Fix this if other scales are implemented
    # in a sensible way for time values
    with pytest.raises(ValueError):
        c = TimeAxis(b, scale='log')

    # initialize with change of label
    c = TimeAxis(b, label='other')
    assert c.label == 'other'

    # change label after init
    c.label = 'another'
    assert c.label == 'another'

    # test copy
    c = TimeAxis(b, label='Foo')
    d = c.copy()
    assert c == d and not c._edges is d._edges

    # test replace_edges
    c = TimeAxis(x)
    edges = Time.now() - [3,2,1]*u.s

    d = c.replace_edges(edges)
    assert arr_eq(d.edges, edges) and d.edges is not edges

    d = c.replace_edges(edges, copy=False)
    assert arr_eq(d.edges, edges) and d.edges is edges

    with pytest.raises(TypeError): # checks for invalid edges
        edges = np.array([0,1,2])
        d = c.replace_edges(edges)

    with pytest.raises(ValueError): # checks for invalid edges
        edges = Time.now() + [1, 0, 2]*u.s
        d = c.replace_edges(edges)

    # validation of edge array

    with pytest.raises(ValueError):
        a = TimeAxis(Time([[0, 1, 2], [0, 1, 2]], format = 'jd')) # multi-dimensional array

    with pytest.raises(ValueError):
        a = TimeAxis(Time([0], format = 'jd')) # need two edges for a bin

    with pytest.raises(ValueError):
        a = TimeAxis(Time.now() + [1, 2, 1]*u.s) # edges must be monotonically increasing

    # Test 128 bit (sub-ns) precision
    # Something like this would fail as it's not monotonic withing double precision
    #a = TimeAxis(Time([2460787 + 2460787 + 0.1e-9/24/3600], format = 'jd'))
    # But this should work
    a = TimeAxis(Time(2460787, [0,.1e-9/24/3600], format = 'jd'))
    assert (a.edges[-1] - a.edges[0]).sec == approx(.1e-9, abs = precision_sec)

def test_axis_index():

    now = Time.now()
    x = now + [1.,2.,3.,4.,5.]*u.s
    a = TimeAxis(x, label='Foo')

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
    assert arr_eq(b.edges, now + [1., 3., 5.]*u.s)

    b = a[1::2]
    assert arr_eq(b.edges, now + [2., 4.]*u.s)

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
    x = Time(["2027-08-29 00:00:00", "2027-08-30 00:00:00"])
    a = TimeAxis(x)

    # Drop units. Defaults to JD
    assert a.to() == Axis([2461646.5, 2461647.5])

    # Convert to the default day
    assert a.to(u.day) == Axis([2461646.5, 2461647.5]*u.day)

    # Convert to something else
    assert a.to(u.s) == Axis([2461646.5, 2461647.5]*u.day).to(u.s)

    # Specify the format
    assert a.to(format = 'gps') == Axis(x.gps)

    with pytest.raises(ValueError):
        # Only numeric formats are allowed
        assert a.to(format='iso') == Axis(x.gps)

    # With numeric formats
    x = Time([1.50353282e+09, 1.50361922e+09], format = 'gps')
    a = TimeAxis(x)

    # Drop units. Default to current numeric format
    assert a.to() == Axis([1.50353282e+09, 1.50361922e+09])

    # With units
    assert a.to(u.s) == Axis([1.50353282e+09, 1.50361922e+09]*u.s)

    # Convert to something else
    assert a.to(u.day) == Axis([1.50353282e+09, 1.50361922e+09]*u.s).to(u.day)

    # convert axis without unit to compatible time unit
    with pytest.raises(TypeError):
        a.to(unit=u.dimensionless_unscaled) # cannot convert Time to dimensionless unit

    with pytest.raises(TypeError):
        a.to(unit=u.m) # cannot convert Time to non-unit time

def test_bad_init():

    # I added this check no make it less error-prone

    with pytest.raises(TypeError):
        a = Axis(Time(["2027-08-29 00:00:00", "2027-08-30 00:00:00"]))

    with pytest.raises(TypeError):
        a = Axis([Time("2027-08-29 00:00:00"), Time("2027-08-30 00:00:00")])

    with pytest.raises(TypeError):
        a = TimeAxis([Time("2027-08-29 00:00:00"), Time("2027-08-30 00:00:00")])

def test_axis_array():

    # With no numeric formats
    x = Time(["2027-08-29 00:00:00", "2027-08-30 00:00:00"])
    a = TimeAxis(x, label='Foo', scale='linear')

    y = np.array(a)

    # Default to JD
    assert np.array_equal(y, [2461646.5, 2461647.5])

    # With numeric formats
    x = Time([1.50353282e+09, 1.50361922e+09], format='gps')
    a = TimeAxis(x)

    y = np.array(a)

    # Defaults to the current numeric format
    assert np.array_equal(y, [1.50353282e+09, 1.50361922e+09])

def test_axis_compare():

    x = Time(["2027-08-29 00:00:00", "2027-08-30 00:00:00", "2027-09-01 00:00:00"])
    a = TimeAxis(x, label='Foo')

    b = TimeAxis(x, label='Foo')
    assert a == b

    b = TimeAxis(x[:-1], label='Foo')
    assert a != b

    b = TimeAxis(x, label='Bar')
    assert a != b

def test_axis_findbin():

    # Test sub-ns precision

    t0 = Time(2461646, format = 'jd')
    x = t0 + [1.,2.,3.,4.,5.]*u.ns
    a = TimeAxis(x)

    b = a.find_bin(t0 + 1.5*u.ns)
    assert(b == 0)

    b = a.find_bin(t0 + 4.5*u.ns)
    assert(b == 3)

    b = a.find_bin(t0 + 2*u.ns)
    assert(b == 1)

    b = a.find_bin(t0 + 2*u.ns, right=True)
    assert(b == 0)

    b = a.find_bin(t0 + 0*u.ns) # underflow
    assert(b == -1)

    b = a.find_bin(t0 + 6*u.ns) # overflow
    assert(b == a.nbins)


    # find_bin can take arrays
    b = a.find_bin(t0 + [0.5, 1.5, 2.5, 3.5]*u.ns)
    assert(np.array_equal(b, [-1, 0, 1, 2]))

    # cannot use bare values
    with pytest.raises(TypeError):
        a.find_bin(3)

    # cannot use values with units
    with pytest.raises(TypeError):
        a.find_bin(3*u.s)

def test_axis_interp():

    def clamp(v:Time, lo:Time, hi:Time):

        # atleast_1d equivalent for Time
        if v.shape == ():
            v = v.reshape(-1)

        v[v > hi] = hi
        v[v < lo] = lo

        return v

    def res(b:Time, w:Time, c:Time):

        # Rearranged to work with Time.
        # Only deltas as meaningful not additions
        # return c[b[0]] * w[0] + c[b[1]] * w[1]

        return c[b[0]] + w[1]*(c[b[1]] - c[b[0]])

    t0 = Time(2461646, format='jd')
    x = t0 + [1., 2., 4., 8., 16.] * u.ns

    # linear interpolation
    a = TimeAxis(x)
    c = a.centers
    e = a.edges

    # test interior values
    v = t0 + 5.*u.ns
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

    v = t0 + 3. * u.ns
    bins, weights = a.interp_weights(v)
    assert np.all(bins >= 0) and np.all(bins < len(c))
    assert np.all(weights >= 0.) and np.all(weights <= 1.)
    assert np.all(res(bins, weights, c) == clamp(v, c[0], c[-1]))

    # test centers of boundary bins
    v = t0 + 1.5*u.ns
    bins, weights = a.interp_weights(v)
    assert np.all(bins >= 0) and np.all(bins < len(c))
    assert np.all(weights >= 0.) and np.all(weights <= 1.)
    assert np.all(res(bins, weights, c) == clamp(v, c[0], c[-1]))

    v = t0 + 12.*u.ns
    bins, weights = a.interp_weights(v)
    assert np.all(bins >= 0) and np.all(bins < len(c))
    assert np.all(weights >= 0.) and np.all(weights <= 1.)
    assert np.all(res(bins, weights, c) == clamp(v, c[0], c[-1]))

    # test exterior values
    v = t0 + 0.*u.ns
    bins, weights = a.interp_weights(v)
    assert np.all(bins >= 0) and np.all(bins < len(c))
    assert np.all(weights >= 0.) and np.all(weights <= 1.)
    assert np.all(res(bins, weights, c) == clamp(v, c[0], c[-1]))

    bins, weights = a.interp_weights_edges(v)
    assert np.all(bins >= 0) and np.all(bins < len(e))
    assert np.all(weights >= 0.) and np.all(weights <= 1.)
    assert np.all(res(bins, weights, e) == clamp(v, e[0], e[-1]))

    v = t0 + 20.*u.ns
    bins, weights = a.interp_weights(v)
    assert np.all(bins >= 0) and np.all(bins < len(c))
    assert np.all(weights >= 0.) and np.all(weights <= 1.)
    assert np.all(res(bins, weights, c) == clamp(v, c[0], c[-1]))

    # 0-D array should behave like scalar
    v = t0 + 5.*u.ns
    bins, weights = a.interp_weights(v)
    assert bins.shape == (2,) and weights.shape == (2,)
    assert np.all(bins >= 0) and np.all(bins < len(c))
    assert np.all(weights >= 0.) and np.all(weights <= 1.)
    assert np.all(res(bins, weights, c) == clamp(v, c[0], c[-1]))

    # 1-D array should behave like array
    v = t0 + [5.]*u.ns
    bins, weights = a.interp_weights(v)
    assert bins.shape == (2,1) and weights.shape == (2,1)
    assert np.all(bins >= 0) and np.all(bins < len(c))
    assert np.all(weights >= 0.) and np.all(weights <= 1.)
    assert np.all(res(bins, weights, c) == clamp(v, c[0], c[-1]))

    v = t0 + np.arange(0., 20.)*u.ns
    bins, weights = a.interp_weights(v)
    assert np.all(bins >= 0) and np.all(bins < len(c))
    assert np.all(weights >= 0.) and np.all(weights <= 1.)
    assert np.all(res(bins, weights, c) == clamp(v, c[0], c[-1]))

    # interp_weights result should preserve shape of input values,
    # even if they have unit dimensions
    v = t0 + np.array([ [ [ 3., 5., 9.], [2., 7., 0.] ] ])*u.ns
    bins, weights = a.interp_weights(v)
    assert bins.shape    == (2,) + v.shape
    assert weights.shape == (2,) + v.shape
    assert np.all(bins >= 0) and np.all(bins < len(c))
    assert np.all(weights >= 0.) and np.all(weights <= 1.)
    assert np.all(res(bins, weights, c) == clamp(v, c[0], c[-1]))

def test_axis_properties():

    t0 = Time(2461646, format='jd')
    x = t0 + [1.,2.,3.,4.,5.]*u.ns
    a = TimeAxis(x, label='Foo', scale='linear')

    assert arr_eq(a.lower_bounds, t0+[1, 2, 3, 4]*u.ns)
    assert arr_eq(a.upper_bounds, t0+[2, 3, 4, 5]*u.ns)
    assert arr_eq(a.bounds, t0+[[1,2], [2,3], [3,4], [4,5]]*u.ns)
    assert arr_eq(a.lo_lim, t0+1*u.ns)
    assert arr_eq(a.hi_lim, t0+5*u.ns)
    assert delta_arr_approx(a.widths, [1, 1, 1, 1]*u.ns)
    assert a.label_with_unit == 'Foo'

def test_axis_centers():

    t0 = Time.now()
    x = t0 + np.array([1.,2.,3.,4.,5.])*u.ns
    a = TimeAxis(x, label='Foo', scale='linear')

    c = a.centers
    assert arr_approx(c, t0 + [1.5, 2.5, 3.5, 4.5]*u.ns)

def test_axis_math():

    t0 = Time.now()

    x = t0 + np.array([1.,2.,3.,4.,5.]) * u.ns
    a = TimeAxis(x, label='Foo', scale='linear')

    # Out of place ops
    # Only shifts are allowed
    with pytest.raises(RuntimeError):
        # Use unit to bypass TypeError
        b = a * (2*u.s)

    with pytest.raises(RuntimeError):
        # Use unit to bypass TypeError
        b = a / (2*u.s)

    # Shifts only allowed with units or time delta
    with pytest.raises(TypeError):
        b = a + 2

    b = a + 2*u.ns
    assert arr_eq(b.edges, x + 2*u.ns)

    b = a - 2*u.ns
    assert arr_eq(b.edges, x - 2*u.ns)

    # You can only shift by scalars
    with pytest.raises(ValueError):
        # Use unit to bypass TypeError
        b = a + x.gps*u.s

    # Bad units
    with pytest.raises(ValueError):
        b = a + 1*u.m

    # Difference with respect to reference time
    b = a - t0
    assert b == TimeDeltaAxis(x - t0, label='Foo', scale='linear')

    with pytest.raises(ValueError):
        # only a single reference time alloweed
        b = a - (Time.now() + [0,1]*u.s)

    # in place ops
    x = t0 + np.array([1., 2., 3., 4., 5.]) * u.ns
    a = TimeAxis(x, label='Foo', scale='linear')

    # Shifts only allowed with units or time delta
    b = a.copy()
    with pytest.raises(TypeError):
        b += 2

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
    assert arr_eq(b.edges, x + 2 * u.ns)

    b = a.copy()
    b -= 2*u.ns
    assert arr_eq(b.edges, x - 2 * u.ns)

    # You can only shift by scalars
    b = a.copy()
    with pytest.raises(ValueError):
        # Use unit to bypass TypeError
        b += x.gps * u.s


# reading and writing functions are tested by Histogram read/write tests
