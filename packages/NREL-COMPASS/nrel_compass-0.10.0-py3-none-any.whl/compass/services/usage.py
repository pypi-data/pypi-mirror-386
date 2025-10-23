"""Ordinances usage tracking utilities"""

import time
import logging
from collections import UserDict, deque
from functools import total_ordering


logger = logging.getLogger(__name__)


@total_ordering
class TimedEntry:
    """An entry that performs comparisons based on time added, not value

    Examples
    --------
    >>> a = TimedEntry(100)
    >>> a > 1000
    True
    """

    def __init__(self, value):
        """

        Parameters
        ----------
        value : object
            Some value to store as an entry.
        """
        self.value = value
        self._time = time.monotonic()

    def __eq__(self, other):
        return self._time == other

    def __lt__(self, other):
        return self._time < other

    def __hash__(self):
        return hash((self.value, self._time))


class TimeBoundedUsageTracker:
    """Track usage of a resource over time

    This class wraps a double-ended queue, and any inputs older than
    a certain time are dropped. Those values are also subtracted from
    the running total.

    References
    ----------
    https://stackoverflow.com/questions/51485656/efficient-time-bound-queue-in-python
    """

    def __init__(self, max_seconds=70):
        """

        Parameters
        ----------
        max_seconds : int, optional
            Maximum age in seconds of an element before it is dropped
            from consideration. By default, ``65``.
        """
        self.max_seconds = max_seconds
        self._total = 0
        self._q = deque()

    @property
    def total(self):
        """float: Total of all entries younger than `max_seconds`"""
        self._discard_old_values()
        return self._total

    def add(self, value):
        """Add a value to track

        Parameters
        ----------
        value : int or float
            A new value to add to the queue. It's total will be added to
            the running total, and it will live for `max_seconds` before
            being discarded.
        """
        self._q.append(TimedEntry(value))
        self._total += value

    def _discard_old_values(self):
        """Discard 'old' values from the queue"""
        cutoff_time = time.monotonic() - self.max_seconds
        try:
            while self._q[0] < cutoff_time:
                self._total -= self._q.popleft().value
        except IndexError:
            pass


class UsageTracker(UserDict):
    """Rate or API usage tracker"""

    UNKNOWN_MODEL_LABEL = "unknown_model"
    """Label used in the usage dictionary for unknown models"""

    def __init__(self, label, response_parser):
        """

        Parameters
        ----------
        label : str
            Top-level label to use when adding this usage information to
            another dictionary.
        response_parser : callable
            A callable that takes the current usage info (in dictionary
            format) and an LLm response as inputs, updates the usage
            dictionary with usage info based on the response, and
            returns the updated dictionary. See, for example,
            :func:`compass.services.openai.usage_from_response`.
        """
        super().__init__()
        self.label = label
        self.response_parser = response_parser

    def add_to(self, other):
        """Add the contents of this usage information to another dict

        The contents of this dictionary are stored under the `label`
        key that this object was initialized with.

        Parameters
        ----------
        other : dict
            A dictionary to add the contents of this one to.
        """
        other.update({self.label: {**self, "tracker_totals": self.totals}})

    @property
    def totals(self):
        """Compute total usage across all sub-labels

        Returns
        -------
        dict
            Dictionary containing usage information totaled across all
            sub-labels.
        """
        totals = {}
        for model, model_usage in self.items():
            total_model_usage = totals[model] = {}
            for report in model_usage.values():
                try:
                    sub_label_report = report.items()
                except AttributeError:
                    continue

                for tracked_value, count in sub_label_report:
                    total_model_usage[tracked_value] = (
                        total_model_usage.get(tracked_value, 0) + count
                    )
        return totals

    def update_from_model(
        self, model=None, response=None, sub_label="default"
    ):
        """Update usage from a model response

        Parameters
        ----------
        model : str, optional
            Name of model that usage is being recorded for. If ``None``
            or empty string, the usage will be placed under the
            :obj:`UsageTracker.UNKNOWN_MODEL_LABEL` label.
        response : object, optional
            Model call response, which either contains usage information
            or can be used to infer/compute usage. If ``None``, no
            update is made. By default, ``None``.
        sub_label : str, optional
            Optional label to categorize usage under. This can be used
            to track usage related to certain categories.
            By default, ``"default"``.
        """
        if response is None:
            return

        model_usage = self.setdefault(model or self.UNKNOWN_MODEL_LABEL, {})
        model_usage[sub_label] = self.response_parser(
            model_usage.get(sub_label, {}), response
        )
