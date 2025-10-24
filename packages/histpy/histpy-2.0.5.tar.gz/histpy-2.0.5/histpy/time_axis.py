from typing import Union

import numpy as np

from .axis import Axis

from astropy.time import Time, TimeDelta, TimeNumeric
import astropy.units as u

import operator

import logging

from .time_axis_base import TimeAxisBase

logger = logging.getLogger(__name__)

class TimeAxis(TimeAxisBase):
    """
    Axis for astropy Time values.

    The main differences with a regular axis using e.g. GPS second, JD, etc. are:
    - Conversion from Time to the TimeAxis format and scale are performed automatically
    - Time internally stores two double values to achieve sub-ns precision
    - Histogram.plot() makes use of matplotlib's data formatter.

    Args:
    edges (array-like): Bin edges. Must be astropy Time objects
    label (str): Label for axis. If edges is an Axis object, this will
        override its label
    scale (str): Bin center mode. Only 'linear' is supported for TimeAxis.
    unit  (unit-like): This parameter has no effect for TimeAxis. It is
               kept for compatibility with the parent Axis class.
    copy (bool): True if edge array should be distinct from passed-in
                 edges; if False, will use same edge array if possible
    """

    _type = Time

    def to(self, unit:u.Unit = None, equivalencies=None, update=True, copy=True, format:str = None):
        """
        Transform to a regular Axis with units.

        .. warning::
            Transforming a TimeAxis to Axis with unit can result in loss of precision.
            Time internally stores the time in two double values.

         .. warning::
            The widths will **not** take into account leap second for some formats.

        Args:
            unit (unit-like): Unit to convert to. If None, it returns an axis without unit,
                only the bare values.
            equivalencies (list or tuple): A list of equivalence pairs to try if the units are not
                directly convertible.
            update (bool): This parameter has no effect for TimeAxis. It is
               kept for compatibility with the parent Axis class.
            copy (bool): This parameter has no effect for TimeAxis. It is
               kept for compatibility with the parent Axis class. Since Time internally stores
               the time using two doubles, new memory is always allocated.
            format:
                A format recognized by astropy.time.Time.to_value().
                Defaults to the edges Time format if they are of type
                TimeNumeric, otherwise it defaults for 'jd'
        Returns:
            Regular axis with units.
        """

        if equivalencies is None:
            equivalencies = []

        if unit is not None:
            unit = u.Unit(unit) # Parse (if needed) and check

            if not unit.is_equivalent(u.s, equivalencies = equivalencies):
                raise TypeError(f"Incompatible unit \"{unit}\". TimeAxis can only convert to time units. ")

        if format is None:
            time_subclass = Time.FORMATS[self.edges.format]

            if issubclass(time_subclass, TimeNumeric):
                format = self.edges.format
            else:
                format = 'jd'
                time_subclass = Time.FORMATS[format]

        else:
            time_subclass = Time.FORMATS[format]

        if not issubclass(time_subclass, TimeNumeric):
            raise ValueError(f"Format must be TimeNumeric. e.g. gps, unix, jd, mjd, decimalyear, jyear, etc.")

        return self._to(unit, format, equivalencies)

    @property
    def bounds(self):
        '''
        Start of [lower_bound, upper_bound] values for each bin.
        '''

        lower = self._edges[:-1]
        upper = self._edges[1:]

        # This keeps the Time internal format
        return Time(np.concatenate([lower, upper])).reshape(2,-1).T

    def _operation(self, other, operation):

        # Allow to get a difference with respect to a fixed time
        # This changes the axis type though
        if isinstance(other, Time) and operation in (operator.sub, operator.isub):

            from .time_delta_axis import TimeDeltaAxis

            if other.size != 1:
                raise ValueError("The time difference operand needs to be a scalar.")

            return TimeDeltaAxis(self.edges - other, label = self.label, copy = False)

        else:
            return super()._operation(other, operation)


