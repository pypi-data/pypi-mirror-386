from typing import Union

import numpy as np

from .axis import Axis

from astropy.time import Time, TimeDelta, TimeDeltaNumeric
import astropy.units as u

import operator

import logging

from .time_axis_base import TimeAxisBase

logger = logging.getLogger(__name__)


class TimeDeltaAxis(TimeAxisBase):
    """
    Axis for astropy TimeDelta values.

    The main differences with a regular axis using e.g. GPS second, JD, etc. are:
    - Time internally stores two double values to achieve sub-ns precision
    - Interaction with TimeAxis keep 128 bit precision
    - Histogram.plot() makes use of matplotlib's data formatter.

    Args:
    edges (array-like): Bin edges. Must be TimeDelta objects
    label (str): Label for axis. If edges is an Axis object, this will
        override its label
    scale (str): Bin center mode e.g. `"linear"` or `"log"`.
        See `axis_scale` property. If edges is an TimeDeltaAxis
        object, this will override its mode
    unit  (unit-like): This parameter has no effect for TimeDeltaAxis. It is
               kept for compatibility with the parent Axis class.
    copy (bool): True if edge array should be distinct from passed-in
                 edges; if False, will use same edge array if possible
    """

    _type = TimeDelta

    def __init__(self, edges: Union[Axis, TimeDelta, 'TimeDeltaAxis'], label=None, scale=None, unit=None, copy=True):

        # Attempt to convert time to TimeDelta using astropy defaults
        # before passing it to Base init
        if isinstance(edges, Axis) and not isinstance(edges, TimeDeltaAxis):
            edges = TimeDeltaAxis(edges.edges, copy=False)
        elif not isinstance(edges, (TimeDelta, TimeDeltaAxis)):
            edges = TimeDelta(edges, copy = False)

        super().__init__(edges, label, scale, unit, copy)

    def _to_default_format(self):

        time_subclass = TimeDelta.FORMATS[self.edges.format]

        if issubclass(time_subclass, TimeDeltaNumeric):
            format = self.edges.format
        else:
            format = 'jd'
            time_subclass = TimeDelta.FORMATS[format]

        return time_subclass, format

    def to(self, unit:u.Unit = None, equivalencies=None, update=True, copy=True):
        """
        Transform to a regular Axis with units.

        .. warning::
            Transforming a TimeDeltaAxis to Axis with unit can result in loss of precision.
            TimeDelta internally stores the time in two double values. Due to loss of
            precision, it's also possible that the resulting Axis would not have
            monotonically-increasing bin edges, and therefore
            this operations will fail. Use at your own risk

        Args:
            unit (unit-like): Unit to convert to. If None, it returns an axis with bare values
                in the current edges' TimeDelta format, if it's of the type numeric,
                otherwise the default format is 'jd'
            equivalencies (list or tuple): A list of equivalence pairs to try if the units are not
                directly convertible.
            update (bool): This parameter has no effect for TimeDeltaAxis. It is
               kept for compatibility with the parent Axis class.
            copy (bool): This parameter has no effect for TimeDeltaAxis. It is
               kept for compatibility with the parent Axis class. Since Time internally stores
               the time using two doubles, new memory is always allocated.
        Returns:
            Regular axis with units.
        """

        if equivalencies is None:
            equivalencies = []


        if unit is None:

            # Try to guess from current format
            _, format = self._to_default_format()

        else:
            unit = u.Unit(unit) # Parse (if needed) and check

            if not unit.is_equivalent(u.s, equivalencies = equivalencies):
                raise TypeError(f"Incompatible unit \"{unit}\". TimeDeltaAxis can only convert to time units. ")

            # Default. We'll convert unit anyway
            format = 'jd'

        return self._to(unit, format, equivalencies)

    def find_bin(self, value:Union[TimeDelta, u.Quantity], right:bool = False):
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

        # Convert to TimeDelta if needed
        # Adjust copy to prevent error with e.g. int, double values
        copy = True if not isinstance(value, (TimeDelta, u.Quantity)) else False
        value = TimeDelta(value, copy = copy)

        return super().find_bin(value, right)

    def _interp_weights(self, centers, values:TimeDelta):
        # Convert to TimeDelta if needed
        values = TimeDelta(values, copy=True) # copy since we'll modify it

        return super()._interp_weights(centers, values)

    @property
    def bounds(self):
        '''
        Start of [lower_bound, upper_bound] values for each bin.
        '''

        lower = self._edges[:-1]
        upper = self._edges[1:]

        # This doesn't keep the Time internal format
        # Concatenate doesn't seem to work for TimeDelta the
        # same way as for Time, or I'm missing something
        # Not a big deal though, I think
        return TimeDelta(np.concatenate([lower.jd1, upper.jd1]),np.concatenate([lower.jd2, upper.jd2]), format = 'jd').reshape(2,-1).T

    @property
    def label_with_unit(self):
        """
        Axis 'label [units]'
        """

        strs = []
        if self._label is not None:
            strs.append(f"{self._label}")

        # Use to() default for units, since that's what plot
        # uses
        _, format = self._to_default_format()

        strs.append(f"[{format}]")

        return " ".join(strs)

    def _ioperation(self, other, operation):

        # Attempt to transform to TimeDelta
        # Even bare values have a default unit (jd) in TimeDelta
        if not isinstance(other, (Time, TimeDelta, u.Quantity)):
            other = TimeDelta(other)

        return super()._ioperation(other, operation)

    def _operation(self, other, operation):

        # Allow to add a reference time
        # This changes the axis type though
        if isinstance(other, Time) and operation in (operator.add, operator.iadd):

            from .time_axis import TimeAxis

            if other.size != 1:
                raise ValueError("When adding a Time to a TimeDeltaAxis, the Time object needs to be a scalar.")

            return TimeAxis(other + self.edges, label = self.label, copy = False)

        else:
            return super()._operation(other, operation)

