import operator
from typing import ClassVar, Union, Type, TypeVar

import numpy as np
from astropy.time import TimeDelta, Time

from histpy import Axis

import astropy.units as u

def _searchsorted_128bit(edges_int, edges_frac, values_int, values_frac, side = 'left'):
    """
    Sort first by the integer part and then the fracional part
    """

    dtype = [('int', float), ('frac', float)]
    edges = np.rec.fromarrays((edges_int, edges_frac), dtype=dtype)
    value = np.rec.fromarrays((values_int, values_frac), dtype=dtype)

    return np.searchsorted(edges, value, side)


_type = TypeVar('_time_type')
class TimeAxisBase(Axis):

    _type: ClassVar[Union[Type[Time], Type[TimeDelta]]]

    def __init__(self, edges:Union[_type, 'TimeAxisBase'], label=None, scale=None, unit=None, copy=True):

        if isinstance(edges, self.__class__):
            #Overrides
            label = edges._label if label is None else label

            scale = edges._scale if scale is None else scale

            # No validation needed since they are coming from another TimeAxis.
            edges = edges._edges

        elif isinstance(edges, self._type):

            self._validate_edges(edges)

        else:

            raise TypeError(f"{self.__class__.__name__} can only accept {self._type} or {self.__class__.__name__} objects as edges. "
                            f"Make sure you are providing a single {self._type} object storing the timestamp list "
                            "and not a list of {self._type} objects.")

        # The edges are stored as Time/TimeDelta, as opposed to e.g. storing the
        # GPS seconds as a regular Axis, because we want to keep sub-ns
        # precision. Time internally stores the time in two numbers
        # (JD and JD fraction) to achieve this precision.
        if copy:
            self._edges = edges.copy()
        else:
            self._edges = edges

        if unit is not None:
            raise ValueError(f"{self.__class__.__name__} doesn't accept units.")

        self._unit = None

        self._label = label

        if scale is not None and scale not in ['linear']:
            # I don't think symmetric and log make much sense for Time.
            # FIXME: For TimeDelta I think it can be useful, but it was tricky to
            #   implement properly with 128 bit definition.
            raise ValueError(f"Scale \"{scale}\" is not supported by the {self.__class__.__name__} class")

        self.axis_scale = 'linear'

    def _to(self, unit:u.Unit, format, equivalencies = None):
        """
        Each subclass handles default format

        Args:
            unit: desired unit
            format: registered TimeFormatNumeric ot TimeDeltaFormatNumeric
        Returns:

        """

        # Edge values in jd, but unitless
        edges = self._edges.to_value(format=format)

        # Transform to desired units, if needed
        if unit is not None:

            # Format's convertion factor to Julian day. See
            # https://github.com/astropy/astropy/blob/8c982fd20191ef696493f6aeb9ab62a3f35ac565/astropy/time/formats.py#L2212
            time_subclass = self._type.FORMATS[format]
            unit_day_frac = getattr(time_subclass, "unit", 1)

            if unit_day_frac != 1.:
                # Not a day
                edges = edges * unit_day_frac

            edges = u.Quantity(edges, u.d, copy=False)

            if unit is not u.d:
                edges = edges.to(unit, copy=False, equivalencies=equivalencies)

        try:
            new_axis = Axis(edges, label=self._label, copy=False, scale=self._scale)
        except ValueError as e:
            raise ValueError("Failed to convert to a regular axis. "
                             "This was likely caused by the loss of "
                             "precision when converting time to a double, "
                             "resulting in non strictly monotonically increasing edges").with_traceback(e.__traceback__)

        return new_axis

    @property
    def edges(self):
        return self._edges

    def replace_edges(self, edges, copy=True):
        """
        Replace edge array of self (see _copy documentation)
        """

        if not isinstance(edges, self._type):
            raise TypeError(f"{__class__.__name__} can only accept {self._type} objects as edges.")

        return self._copy(edges, copy)

    def find_bin(self, value:_type, right:bool = False):
        """
        Return the bin `value` corresponds to.

        Args:
            value:
               value(s) to bin
            right:
               If false, a bin strictly includes its left edge
               If true, a bin strictly includes its right edge
        Return:
            int: Bin number. -1 for underflow, `nbins` for overflow
        """

        if not isinstance(value, self._type):
            raise TypeError(f"{self.__class__.__name__}.find_bin() only supports {self._type} values, not type '{type(value)}'")

        dir = 'left' if right else 'right' # yes, really

        # While we could use np.searchsorted with Time directly, it
        # ended up being very slow. Instead, we use the recarrays
        # to keep the 128 bit precision.
        # The intitialization of these arrays for a decent size
        # "value" are negligible, so I didn't think it was worth to
        # cache the edges in this format.
        return _searchsorted_128bit(self._edges.jd1, self._edges.jd2, value.jd1, value.jd2, dir) - 1

    def _interp_weights(self, centers: _type, values: _type):
        """
        Use for either bin centers or bin edges
        """

        if self._scale != 'linear':
            raise ValueError(f"{self.__class__.__name__} can only handle linear interpolations")

        # scalar or 0-D array
        isscalar = values.shape == ()

        # atleast_1d equivalent for Time
        if values.shape == ():
            values = values.reshape(-1)

        # clamp out-of-range values to centers of edge bins
        values[values > centers[-1]] = centers[-1]
        values[values < centers[0]] = centers[0]

        # identify bin with greatest center <= each value;
        # this is the left flanking bin
        b0 = _searchsorted_128bit(centers.jd1, centers.jd2, values.jd1, values.jd2, side = 'left') - 1

        # assign value exactly at leftmost center to first bin
        b0[b0 == -1] = 0

        # compute interpolating weights
        w0 = ((centers[b0 + 1] - values) / (centers[1:]-centers[:-1])[b0]).to_value('')

        # materialize right bin and weight
        bins    = np.stack((b0, b0 + 1))
        weights = np.stack((w0, 1. - w0))

        # if just one value, return its bins/weights, rather than lists
        if isscalar:
            return ( bins[:,0], weights[:,0] )
        else:
            return ( bins, weights )

    @property
    def widths(self)->TimeDelta:
        """
        Width of each bin.

        Returns:
        TimeDelta between bins. TimeDelta contains 2 doubles
        internally, so sub-ns precision is possible.
        """

        return self._edges[1:] - self._edges[:-1]

    def __array__(self, dtype=None, copy=None):
        """
        Convert to numpy array with no units

        Args:
            dtype: numpy data type
            copy: Always makes a copy. Kept for compatibility

        Returns:
        Numpy array
        """

        # to() always makes a copy because internally the time is
        # stores in two doubles
        return self.to().__array__(dtype, copy = False)

    @property
    def lower_bounds(self):
        '''
        Lower bound of each bin
        '''

        return self._lower_bounds

    @property
    def upper_bounds(self):
        '''
        Upper bound of each bin
        '''

        return self._upper_bounds

    @property
    def lo_lim(self):
        """
        Overall lower bound
        """

        return self._lo_lim

    @property
    def hi_lim(self):
        """
        Overall upper bound of histogram
        """

        return self._hi_lim

    @property
    def centers(self):
        """
        Center of each bin, in linear domain and axis units, if any
        """

        if self._scale != 'linear':
            # Redundant check with __init__, just in case
            # the code is modified in the future
            raise ValueError(f"{self.__class__.__name__} only supports linear interpolation")

        return self._edges[:-1] + self.widths / 2

    def _get_centers(self):
        """
        Same as centers property. Override to reuse interp_weights method from Axis.
        """

        return self.centers

    def _ioperation(self, other, operation):

        if isinstance(other, u.Quantity):
            # Attempt to transform to TimeDelta
            other = TimeDelta(other)
        elif not isinstance(other, TimeDelta):
            raise TypeError(f"A {self.__class__.__name__} can only be shifted by a TimeDelta or a quantity with time units")

        if other.ndim == 1:
            raise ValueError("A TimeAxis can only be shifted by a scalar.")

        if operation not in (operator.isub, operator.sub, operator.iadd, operator.add):
            raise RuntimeError(f"Operation \"{operation}\" not supported by {self.__class__}.")

        self._edges = operation(self._edges, other)

        return self

    def _write(self, axes_group, name):
        """
        Save all needed information to recreate Axis into
        a HDF5 group.  Subclasses may override

        Returns: dataset holding axis
        """

        # We need to store both value to keep precision
        axis_set = axes_group.create_dataset(name,
                                             data = [self._edges.jd1, self._edges.jd2])

        self._write_metadata(axis_set)

        return axis_set

    def _write_metadata(self, axis_set):
        """
        Save extra metadata to existing dataset
        """

        super()._write_metadata(axis_set)

        if self._edges.scale is not None:
            axis_set.attrs['time_scale'] = self._edges.scale

        axis_set.attrs['time_format'] = self._edges.format

    @classmethod
    def _open(cls, dataset):
        """
        Create Axis from HDF5 dataset
        Written as a virtual constructor so that
        subclasses may override
        """

        metadata = cls._open_metadata(dataset)

        edges = np.asarray(dataset)

        # Get both values for full precision
        edges = cls._type(edges[0], edges[1], format = 'jd', scale = metadata['time_scale'])

        edges.format = metadata['time_format']

        new = cls.__new__(cls)
        cls.__init__(new,
                     edges=edges,
                     unit=metadata['unit'],
                     scale=metadata['scale'],
                     label=metadata['label'],
                     copy=False)

        return new

    @classmethod
    def _open_metadata(cls, dataset):
        """
        Returns unit, label and scale as a dictionary
        """

        metadata = super()._open_metadata(dataset)

        if 'time_scale' in dataset.attrs:
            metadata['time_scale'] = dataset.attrs['time_scale']
        else:
            metadata['time_scale'] = None

        metadata['time_format'] = dataset.attrs['time_format']

        return metadata