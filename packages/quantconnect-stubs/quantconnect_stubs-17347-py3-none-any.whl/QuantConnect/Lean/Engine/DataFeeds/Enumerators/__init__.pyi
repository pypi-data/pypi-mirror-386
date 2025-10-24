from typing import overload
from enum import IntEnum
import abc
import datetime
import typing

import QuantConnect
import QuantConnect.Data
import QuantConnect.Data.Auxiliary
import QuantConnect.Data.Consolidators
import QuantConnect.Data.Market
import QuantConnect.Data.UniverseSelection
import QuantConnect.Interfaces
import QuantConnect.Lean.Engine.DataFeeds
import QuantConnect.Lean.Engine.DataFeeds.Enumerators
import QuantConnect.Lean.Engine.Results
import QuantConnect.Python
import QuantConnect.Securities
import QuantConnect.Util
import System
import System.Collections
import System.Collections.Generic

QuantConnect_Lean_Engine_DataFeeds_Enumerators_EnqueueableEnumerator_T = typing.TypeVar("QuantConnect_Lean_Engine_DataFeeds_Enumerators_EnqueueableEnumerator_T")
QuantConnect_Lean_Engine_DataFeeds_Enumerators_FilterEnumerator_T = typing.TypeVar("QuantConnect_Lean_Engine_DataFeeds_Enumerators_FilterEnumerator_T")
QuantConnect_Lean_Engine_DataFeeds_Enumerators_SortEnumerator_TKey = typing.TypeVar("QuantConnect_Lean_Engine_DataFeeds_Enumerators_SortEnumerator_TKey")
QuantConnect_Lean_Engine_DataFeeds_Enumerators_RefreshEnumerator_T = typing.TypeVar("QuantConnect_Lean_Engine_DataFeeds_Enumerators_RefreshEnumerator_T")
QuantConnect_Lean_Engine_DataFeeds_Enumerators_SynchronizingEnumerator_T = typing.TypeVar("QuantConnect_Lean_Engine_DataFeeds_Enumerators_SynchronizingEnumerator_T")
QuantConnect_Lean_Engine_DataFeeds_Enumerators_RateLimitEnumerator_T = typing.TypeVar("QuantConnect_Lean_Engine_DataFeeds_Enumerators_RateLimitEnumerator_T")
QuantConnect_Lean_Engine_DataFeeds_Enumerators_ScannableEnumerator_T = typing.TypeVar("QuantConnect_Lean_Engine_DataFeeds_Enumerators_ScannableEnumerator_T")
QuantConnect_Lean_Engine_DataFeeds_Enumerators__EventContainer_Callable = typing.TypeVar("QuantConnect_Lean_Engine_DataFeeds_Enumerators__EventContainer_Callable")
QuantConnect_Lean_Engine_DataFeeds_Enumerators__EventContainer_ReturnType = typing.TypeVar("QuantConnect_Lean_Engine_DataFeeds_Enumerators__EventContainer_ReturnType")


class EnqueueableEnumerator(typing.Generic[QuantConnect_Lean_Engine_DataFeeds_Enumerators_EnqueueableEnumerator_T], System.Object, System.Collections.Generic.IEnumerator[QuantConnect_Lean_Engine_DataFeeds_Enumerators_EnqueueableEnumerator_T]):
    """
    An implementation of IEnumerator{T} that relies on the
    enqueue method being called and only ends when stop
    is called
    """

    @property
    def count(self) -> int:
        """Gets the current number of items held in the internal queue"""
        ...

    @property
    def has_finished(self) -> bool:
        """Returns true if the enumerator has finished and will not accept any more data"""
        ...

    @property
    def current(self) -> QuantConnect_Lean_Engine_DataFeeds_Enumerators_EnqueueableEnumerator_T:
        """Gets the element in the collection at the current position of the enumerator."""
        ...

    def __init__(self, blocking: bool = False) -> None:
        """
        Initializes a new instance of the EnqueueableEnumerator{T} class
        
        :param blocking: Specifies whether or not to use the blocking behavior
        """
        ...

    def dispose(self) -> None:
        """Performs application-defined tasks associated with freeing, releasing, or resetting unmanaged resources."""
        ...

    def enqueue(self, data: QuantConnect_Lean_Engine_DataFeeds_Enumerators_EnqueueableEnumerator_T) -> None:
        """
        Enqueues the new data into this enumerator
        
        :param data: The data to be enqueued
        """
        ...

    def move_next(self) -> bool:
        """
        Advances the enumerator to the next element of the collection.
        
        :returns: true if the enumerator was successfully advanced to the next element; false if the enumerator has passed the end of the collection.
        """
        ...

    def reset(self) -> None:
        """Sets the enumerator to its initial position, which is before the first element in the collection."""
        ...

    def stop(self) -> None:
        """
        Signals the enumerator to stop enumerating when the items currently
        held inside are gone. No more items will be added to this enumerator.
        """
        ...


class FilterEnumerator(typing.Generic[QuantConnect_Lean_Engine_DataFeeds_Enumerators_FilterEnumerator_T], System.Object, System.Collections.Generic.IEnumerator[QuantConnect_Lean_Engine_DataFeeds_Enumerators_FilterEnumerator_T]):
    """Enumerator that allow applying a filtering function"""

    @property
    def current(self) -> QuantConnect_Lean_Engine_DataFeeds_Enumerators_FilterEnumerator_T:
        """Gets the current item in the FilterEnumerator"""
        ...

    def __init__(self, enumerator: System.Collections.Generic.IEnumerator[QuantConnect_Lean_Engine_DataFeeds_Enumerators_FilterEnumerator_T], filter: typing.Callable[[QuantConnect_Lean_Engine_DataFeeds_Enumerators_FilterEnumerator_T], bool]) -> None:
        """
        Creates a new instance
        
        :param enumerator: The underlying enumerator to filter on
        :param filter: The filter to apply
        """
        ...

    def dispose(self) -> None:
        """Disposes the FilterEnumerator"""
        ...

    def move_next(self) -> bool:
        """Moves the FilterEnumerator to the next item"""
        ...

    def reset(self) -> None:
        """Resets the FilterEnumerator"""
        ...


class SynchronizingBaseDataEnumerator(QuantConnect.Lean.Engine.DataFeeds.Enumerators.SynchronizingEnumerator[QuantConnect.Data.BaseData]):
    """
    Represents an enumerator capable of synchronizing other base data enumerators in time.
    This assumes that all enumerators have data time stamped in the same time zone
    """

    @overload
    def __init__(self, *enumerators: typing.Union[System.Collections.Generic.IEnumerator[QuantConnect.Data.BaseData], typing.Iterable[System.Collections.Generic.IEnumerator[QuantConnect.Data.BaseData]]]) -> None:
        """
        Initializes a new instance of the SynchronizingBaseDataEnumerator class
        
        :param enumerators: The enumerators to be synchronized. NOTE: Assumes the same time zone for all data
        """
        ...

    @overload
    def __init__(self, enumerators: typing.List[System.Collections.IEnumerator]) -> None:
        """
        Initializes a new instance of the SynchronizingBaseDataEnumerator class
        
        :param enumerators: The enumerators to be synchronized. NOTE: Assumes the same time zone for all data
        """
        ...

    def get_instance_time(self, instance: QuantConnect.Data.BaseData) -> datetime.datetime:
        """
        Gets the Timestamp for the data
        
        
        This codeEntityType is protected.
        """
        ...


class ITradableDatesNotifier(metaclass=abc.ABCMeta):
    """
    Interface which will provide an event handler
    who will be fired with each new tradable day
    """

    @property
    @abc.abstractmethod
    def new_tradable_date(self) -> _EventContainer[typing.Callable[[System.Object, QuantConnect.NewTradableDateEventArgs], typing.Any], typing.Any]:
        """Event fired when there is a new tradable date"""
        ...

    @new_tradable_date.setter
    def new_tradable_date(self, value: _EventContainer[typing.Callable[[System.Object, QuantConnect.NewTradableDateEventArgs], typing.Any], typing.Any]) -> None:
        ...


class StrictDailyEndTimesEnumerator(System.Object, System.Collections.Generic.IEnumerator[QuantConnect.Data.BaseData]):
    """Enumerator that will handle adjusting daily strict end times if appropriate"""

    @property
    def current(self) -> QuantConnect.Data.BaseData:
        """Current value of the enumerator"""
        ...

    def __init__(self, underlying: System.Collections.Generic.IEnumerator[QuantConnect.Data.BaseData], security_exchange_hours: QuantConnect.Securities.SecurityExchangeHours, local_start_time: typing.Union[datetime.datetime, datetime.date]) -> None:
        """Creates a new instance"""
        ...

    def dispose(self) -> None:
        """Dispose the enumerator"""
        ...

    def move_next(self) -> bool:
        """Move to the next date"""
        ...

    def reset(self) -> None:
        """Reset the enumerator"""
        ...


class QuoteBarFillForwardEnumerator(System.Object, System.Collections.Generic.IEnumerator[QuantConnect.Data.BaseData]):
    """
    The QuoteBarFillForwardEnumerator wraps an existing base data enumerator
    If the current QuoteBar has null Bid and/or Ask bars, it copies them from the previous QuoteBar
    """

    @property
    def current(self) -> QuantConnect.Data.BaseData:
        """Gets the element in the collection at the current position of the enumerator."""
        ...

    def __init__(self, enumerator: System.Collections.Generic.IEnumerator[QuantConnect.Data.BaseData]) -> None:
        """Initializes a new instance of the FillForwardEnumerator class"""
        ...

    def dispose(self) -> None:
        """Performs application-defined tasks associated with freeing, releasing, or resetting unmanaged resources."""
        ...

    def move_next(self) -> bool:
        """
        Advances the enumerator to the next element of the collection.
        
        :returns: true if the enumerator was successfully advanced to the next element; false if the enumerator has passed the end of the collection.
        """
        ...

    def reset(self) -> None:
        """Sets the enumerator to its initial position, which is before the first element in the collection."""
        ...


class SortEnumerator(typing.Generic[QuantConnect_Lean_Engine_DataFeeds_Enumerators_SortEnumerator_TKey], System.Object, System.Collections.Generic.IEnumerator[QuantConnect.Data.BaseData]):
    """
    Provides an enumerator for sorting collections of BaseData objects based on a specified property.
    The sorting occurs lazily, only when enumeration begins.
    """

    @property
    def current(self) -> QuantConnect.Data.BaseData:
        """Gets the current BaseData element in the collection."""
        ...

    def __init__(self, data: typing.List[QuantConnect.Data.BaseData], key_selector: typing.Callable[[QuantConnect.Data.BaseData], QuantConnect_Lean_Engine_DataFeeds_Enumerators_SortEnumerator_TKey] = None) -> None:
        """
        Initializes a new instance of the SortEnumerator{TKey} class.
        
        :param data: The collection of BaseData to enumerate over.
        :param key_selector: A function that defines the key to sort by. Defaults to sorting by BaseData.end_time.
        """
        ...

    def dispose(self) -> None:
        """Releases all resources used by the SortEnumerator{TKey} and suppresses finalization."""
        ...

    def move_next(self) -> bool:
        """
        Advances the enumerator to the next element of the collection.
        
        :returns: true if the enumerator was successfully advanced to the next element;
        false if the enumerator has passed the end of the collection.
        """
        ...

    def reset(self) -> None:
        """Resets the enumerator to its initial position, which is before the first element in the collection."""
        ...

    @staticmethod
    def try_wrap_sort_enumerator(pre_sorted: bool, data: typing.List[QuantConnect.Data.BaseData]) -> System.Collections.Generic.IEnumerator[QuantConnect.Data.BaseData]:
        """
        Static method to wrap an enumerable with the sort enumerator.
        
        :param pre_sorted: Indicates if the data is pre-sorted.
        :param data: The data to be wrapped into the enumerator.
        :returns: An enumerator over the BaseData.
        """
        ...


class ConcatEnumerator(System.Object, System.Collections.Generic.IEnumerator[QuantConnect.Data.BaseData]):
    """Enumerator that will concatenate enumerators together sequentially enumerating them in the provided order"""

    @property
    def current(self) -> QuantConnect.Data.BaseData:
        """The current BaseData object"""
        ...

    @current.setter
    def current(self, value: QuantConnect.Data.BaseData) -> None:
        ...

    @property
    def can_emit_null(self) -> bool:
        """True if emitting a null data point is expected"""
        ...

    @can_emit_null.setter
    def can_emit_null(self, value: bool) -> None:
        ...

    def __init__(self, skip_duplicate_end_times: bool, *enumerators: typing.Union[System.Collections.Generic.IEnumerator[QuantConnect.Data.BaseData], typing.Iterable[System.Collections.Generic.IEnumerator[QuantConnect.Data.BaseData]]]) -> None:
        """
        Creates a new instance
        
        :param skip_duplicate_end_times: True will skip data points from enumerators if before or at the last end time
        :param enumerators: The sequence of enumerators to concatenate. Note that the order here matters, it will consume enumerators
        and dispose of them, even if they return true and their current is null, except for the last which will be kept!
        """
        ...

    def dispose(self) -> None:
        """Performs application-defined tasks associated with freeing, releasing, or resetting unmanaged resources."""
        ...

    def move_next(self) -> bool:
        """
        Advances the enumerator to the next element of the collection.
        
        :returns: True if the enumerator was successfully advanced to the next element; false if the enumerator has passed the end of the collection.
        """
        ...

    def reset(self) -> None:
        """Sets the enumerator to its initial position, which is before the first element in the collection."""
        ...


class LastPointTracker(System.Object):
    """Tracks the last data point received by an enumerator."""

    @property
    def last_data_point(self) -> QuantConnect.Data.BaseData:
        """Tracks the last data point received by the enumerator."""
        ...

    @last_data_point.setter
    def last_data_point(self, value: QuantConnect.Data.BaseData) -> None:
        ...


class FillForwardEnumerator(System.Object, System.Collections.Generic.IEnumerator[QuantConnect.Data.BaseData]):
    """
    The FillForwardEnumerator wraps an existing base data enumerator and inserts extra 'base data' instances
    on a specified fill forward resolution
    """

    @property
    def use_strict_end_time(self) -> bool:
        """
        Whether to use strict daily end times
        
        
        This codeEntityType is protected.
        """
        ...

    @property
    def exchange(self) -> QuantConnect.Securities.SecurityExchange:
        """
        The exchange used to determine when to insert fill forward data
        
        
        This codeEntityType is protected.
        """
        ...

    @property
    def current(self) -> QuantConnect.Data.BaseData:
        """Gets the element in the collection at the current position of the enumerator."""
        ...

    def __init__(self, enumerator: System.Collections.Generic.IEnumerator[QuantConnect.Data.BaseData], exchange: QuantConnect.Securities.SecurityExchange, fill_forward_resolution: QuantConnect.Util.IReadOnlyRef[datetime.timedelta], is_extended_market_hours: bool, subscription_start_time: typing.Union[datetime.datetime, datetime.date], subscription_end_time: typing.Union[datetime.datetime, datetime.date], data_resolution: datetime.timedelta, data_time_zone: typing.Any, daily_strict_end_time_enabled: bool, data_type: typing.Type = None, last_point_tracker: QuantConnect.Lean.Engine.DataFeeds.Enumerators.LastPointTracker = None) -> None:
        """
        Initializes a new instance of the FillForwardEnumerator class that accepts
        a reference to the fill forward resolution, useful if the fill forward resolution is dynamic
        and changing as the enumeration progresses
        
        :param enumerator: The source enumerator to be filled forward
        :param exchange: The exchange used to determine when to insert fill forward data
        :param fill_forward_resolution: The resolution we'd like to receive data on
        :param is_extended_market_hours: True to use the exchange's extended market hours, false to use the regular market hours
        :param subscription_start_time: The start time of the subscription
        :param subscription_end_time: The end time of the subscription, once passing this date the enumerator will stop
        :param data_resolution: The source enumerator's data resolution
        :param data_time_zone: The time zone of the underlying source data. This is used for rounding calculations and
        is NOT the time zone on the BaseData instances (unless of course data time zone equals the exchange time zone)
        :param daily_strict_end_time_enabled: True if daily strict end times are enabled
        :param data_type: The configuration data type this enumerator is for
        :param last_point_tracker: A reference to the last point emitted before this enumerator is first enumerated
        """
        ...

    def dispose(self) -> None:
        """Performs application-defined tasks associated with freeing, releasing, or resetting unmanaged resources."""
        ...

    def move_next(self) -> bool:
        """
        Advances the enumerator to the next element of the collection.
        
        :returns: true if the enumerator was successfully advanced to the next element; false if the enumerator has passed the end of the collection.
        """
        ...

    def requires_fill_forward_data(self, fill_forward_resolution: datetime.timedelta, previous: QuantConnect.Data.BaseData, next: QuantConnect.Data.BaseData, fill_forward: typing.Optional[QuantConnect.Data.BaseData]) -> typing.Tuple[bool, QuantConnect.Data.BaseData]:
        """
        Determines whether or not fill forward is required, and if true, will produce the new fill forward data
        
        
        This codeEntityType is protected.
        
        :param fill_forward_resolution: 
        :param previous: The last piece of data emitted by this enumerator
        :param next: The next piece of data on the source enumerator
        :param fill_forward: When this function returns true, this will have a non-null value, null when the function returns false
        :returns: True when a new fill forward piece of data was produced and should be emitted by this enumerator.
        """
        ...

    def reset(self) -> None:
        """Sets the enumerator to its initial position, which is before the first element in the collection."""
        ...


class LiveAuxiliaryDataSynchronizingEnumerator(System.Object, System.Collections.Generic.IEnumerator[QuantConnect.Data.BaseData]):
    """
    Represents an enumerator capable of synchronizing live equity data enumerators in time.
    This assumes that all enumerators have data time stamped in the same time zone.
    """

    @property
    def current(self) -> QuantConnect.Data.BaseData:
        """Gets the element in the collection at the current position of the enumerator."""
        ...

    def __init__(self, time_provider: QuantConnect.ITimeProvider, exchange_time_zone: typing.Any, trade_bar_aggregator: System.Collections.Generic.IEnumerator[QuantConnect.Data.BaseData], aux_data_enumerators: typing.List[System.Collections.Generic.IEnumerator[QuantConnect.Data.BaseData]]) -> None:
        """
        Initializes a new instance of the LiveAuxiliaryDataSynchronizingEnumerator class
        
        :param time_provider: The source of time used to gauge when this enumerator should emit extra bars when null data is returned from the source enumerator
        :param exchange_time_zone: The time zone the raw data is time stamped in
        :param trade_bar_aggregator: The trade bar aggregator enumerator
        :param aux_data_enumerators: The auxiliary data enumerators
        """
        ...

    def dispose(self) -> None:
        """Performs application-defined tasks associated with freeing, releasing, or resetting unmanaged resources."""
        ...

    def move_next(self) -> bool:
        """
        Advances the enumerator to the next element of the collection.
        
        :returns: true if the enumerator was successfully advanced to the next element; false if the enumerator has passed the end of the collection.
        """
        ...

    def reset(self) -> None:
        """Sets the enumerator to its initial position, which is before the first element in the collection."""
        ...


class FrontierAwareEnumerator(System.Object, System.Collections.Generic.IEnumerator[QuantConnect.Data.BaseData]):
    """
    Provides an implementation of IEnumerator{BaseData} that will not emit
    data ahead of the frontier as specified by an instance of ITimeProvider.
    An instance of TimeZoneOffsetProvider is used to convert between UTC
    and the data's native time zone
    """

    @property
    def current(self) -> QuantConnect.Data.BaseData:
        """Gets the element in the collection at the current position of the enumerator."""
        ...

    def __init__(self, enumerator: System.Collections.Generic.IEnumerator[QuantConnect.Data.BaseData], time_provider: QuantConnect.ITimeProvider, offset_provider: QuantConnect.TimeZoneOffsetProvider) -> None:
        """
        Initializes a new instance of the FrontierAwareEnumerator class
        
        :param enumerator: The underlying enumerator to make frontier aware
        :param time_provider: The time provider used for resolving the current frontier time
        :param offset_provider: An offset provider used for converting the frontier UTC time into the data's native time zone
        """
        ...

    def dispose(self) -> None:
        """Performs application-defined tasks associated with freeing, releasing, or resetting unmanaged resources."""
        ...

    def move_next(self) -> bool:
        """
        Advances the enumerator to the next element of the collection.
        
        :returns: true if the enumerator was successfully advanced to the next element; false if the enumerator has passed the end of the collection.
        """
        ...

    def reset(self) -> None:
        """Sets the enumerator to its initial position, which is before the first element in the collection."""
        ...


class LiveSubscriptionEnumerator(System.Object, System.Collections.Generic.IEnumerator[QuantConnect.Data.BaseData]):
    """Enumerator that will subscribe through the provided data queue handler and refresh the subscription if any mapping occurs"""

    @property
    def current(self) -> QuantConnect.Data.BaseData:
        """The current data object instance"""
        ...

    def __init__(self, data_config: QuantConnect.Data.SubscriptionDataConfig, data_queue_handler: QuantConnect.Interfaces.IDataQueueHandler, handler: typing.Callable[[System.Object, System.EventArgs], typing.Any], is_expired: typing.Callable[[QuantConnect.Data.SubscriptionDataConfig], bool]) -> None:
        """Creates a new instance"""
        ...

    def dispose(self) -> None:
        """Disposes of the used enumerators"""
        ...

    def move_next(self) -> bool:
        """Advances the enumerator to the next element."""
        ...

    def reset(self) -> None:
        """Reset the IEnumeration"""
        ...


class ScheduledEnumerator(System.Object, System.Collections.Generic.IEnumerator[QuantConnect.Data.BaseData]):
    """
    This enumerator will filter out data of the underlying enumerator based on a provided schedule.
    Will respect the schedule above the data, meaning will let older data through if the underlying provides none for the schedule date
    """

    @property
    def current(self) -> QuantConnect.Data.BaseData:
        """The current data point"""
        ...

    def __init__(self, underlying_enumerator: System.Collections.Generic.IEnumerator[QuantConnect.Data.BaseData], scheduled_times: typing.List[datetime.datetime], frontier_time_provider: QuantConnect.ITimeProvider, schedule_time_zone: typing.Any, start_time: typing.Union[datetime.datetime, datetime.date]) -> None:
        """
        Creates a new instance
        
        :param underlying_enumerator: The underlying enumerator to filter
        :param scheduled_times: The scheduled times to emit new data points
        :param frontier_time_provider: 
        :param schedule_time_zone: 
        :param start_time: the underlying request start time
        """
        ...

    def dispose(self) -> None:
        """Disposes of the underlying enumerator"""
        ...

    def move_next(self) -> bool:
        """
        Advances the enumerator to the next element of the collection.
        
        :returns: True if the enumerator was successfully advanced to the next element;
        false if the enumerator has passed the end of the collection.
        """
        ...

    def reset(self) -> None:
        """Resets the underlying enumerator"""
        ...


class PriceScaleFactorEnumerator(System.Object, System.Collections.Generic.IEnumerator[QuantConnect.Data.BaseData]):
    """
    This enumerator will update the SubscriptionDataConfig.price_scale_factor when required
    and adjust the raw BaseData prices based on the provided SubscriptionDataConfig.
    Assumes the prices of the provided IEnumerator are in raw mode.
    """

    @property
    def current(self) -> QuantConnect.Data.BaseData:
        """Last read BaseData object from this type and source"""
        ...

    def __init__(self, raw_data_enumerator: System.Collections.Generic.IEnumerator[QuantConnect.Data.BaseData], config: QuantConnect.Data.SubscriptionDataConfig, factor_file_provider: QuantConnect.Interfaces.IFactorFileProvider, live_mode: bool = False, end_date: typing.Optional[datetime.datetime] = None) -> None:
        """
        Creates a new instance of the PriceScaleFactorEnumerator.
        
        :param raw_data_enumerator: The underlying raw data enumerator
        :param config: The SubscriptionDataConfig to enumerate for.
        Will determine the DataNormalizationMode to use.
        :param factor_file_provider: The IFactorFileProvider instance to use
        :param live_mode: True, is this is a live mode data stream
        :param end_date: The enumerator end date
        """
        ...

    def dispose(self) -> None:
        """Dispose of the underlying enumerator."""
        ...

    def move_next(self) -> bool:
        """
        Advances the enumerator to the next element of the collection.
        
        :returns: True if the enumerator was successfully advanced to the next element;
        False if the enumerator has passed the end of the collection.
        """
        ...

    def reset(self) -> None:
        """Reset the IEnumeration"""
        ...


class RefreshEnumerator(typing.Generic[QuantConnect_Lean_Engine_DataFeeds_Enumerators_RefreshEnumerator_T], System.Object, System.Collections.Generic.IEnumerator[QuantConnect_Lean_Engine_DataFeeds_Enumerators_RefreshEnumerator_T]):
    """
    Provides an implementation of IEnumerator{T} that will
    always return true via MoveNext.
    """

    @property
    def current(self) -> QuantConnect_Lean_Engine_DataFeeds_Enumerators_RefreshEnumerator_T:
        """Gets the element in the collection at the current position of the enumerator."""
        ...

    def __init__(self, enumerator_factory: typing.Callable[[], System.Collections.Generic.IEnumerator[QuantConnect_Lean_Engine_DataFeeds_Enumerators_RefreshEnumerator_T]]) -> None:
        """
        Initializes a new instance of the RefreshEnumerator{T} class
        
        :param enumerator_factory: Enumerator factory used to regenerate the underlying
        enumerator when it ends
        """
        ...

    def dispose(self) -> None:
        """Performs application-defined tasks associated with freeing, releasing, or resetting unmanaged resources."""
        ...

    def move_next(self) -> bool:
        """
        Advances the enumerator to the next element of the collection.
        
        :returns: true if the enumerator was successfully advanced to the next element; false if the enumerator has passed the end of the collection.
        """
        ...

    def reset(self) -> None:
        """Sets the enumerator to its initial position, which is before the first element in the collection."""
        ...


class SynchronizingEnumerator(typing.Generic[QuantConnect_Lean_Engine_DataFeeds_Enumerators_SynchronizingEnumerator_T], System.Object, System.Collections.Generic.IEnumerator[QuantConnect_Lean_Engine_DataFeeds_Enumerators_SynchronizingEnumerator_T], metaclass=abc.ABCMeta):
    """
    Represents an enumerator capable of synchronizing other enumerators of type T in time.
    This assumes that all enumerators have data time stamped in the same time zone
    """

    @property
    def current(self) -> QuantConnect_Lean_Engine_DataFeeds_Enumerators_SynchronizingEnumerator_T:
        """Gets the element in the collection at the current position of the enumerator."""
        ...

    @overload
    def __init__(self, *enumerators: typing.Union[System.Collections.Generic.IEnumerator[QuantConnect_Lean_Engine_DataFeeds_Enumerators_SynchronizingEnumerator_T], typing.Iterable[System.Collections.Generic.IEnumerator[QuantConnect_Lean_Engine_DataFeeds_Enumerators_SynchronizingEnumerator_T]]]) -> None:
        """
        Initializes a new instance of the SynchronizingEnumerator{T} class
        
        
        This codeEntityType is protected.
        
        :param enumerators: The enumerators to be synchronized. NOTE: Assumes the same time zone for all data
        """
        ...

    @overload
    def __init__(self, enumerators: typing.List[System.Collections.Generic.IEnumerator[QuantConnect_Lean_Engine_DataFeeds_Enumerators_SynchronizingEnumerator_T]]) -> None:
        """
        Initializes a new instance of the SynchronizingEnumerator{T} class
        
        
        This codeEntityType is protected.
        
        :param enumerators: The enumerators to be synchronized. NOTE: Assumes the same time zone for all data
        """
        ...

    def dispose(self) -> None:
        """Performs application-defined tasks associated with freeing, releasing, or resetting unmanaged resources."""
        ...

    def get_instance_time(self, instance: QuantConnect_Lean_Engine_DataFeeds_Enumerators_SynchronizingEnumerator_T) -> datetime.datetime:
        """
        Gets the Timestamp for the data
        
        
        This codeEntityType is protected.
        """
        ...

    def move_next(self) -> bool:
        """
        Advances the enumerator to the next element of the collection.
        
        :returns: true if the enumerator was successfully advanced to the next element; false if the enumerator has passed the end of the collection.
        """
        ...

    def reset(self) -> None:
        """Sets the enumerator to its initial position, which is before the first element in the collection."""
        ...


class ITradableDateEventProvider(metaclass=abc.ABCMeta):
    """Interface for event providers for new tradable dates"""

    def get_events(self, event_args: QuantConnect.NewTradableDateEventArgs) -> typing.Iterable[QuantConnect.Data.BaseData]:
        """
        Called each time there is a new tradable day
        
        :param event_args: The new tradable day event arguments
        :returns: New corporate event if any.
        """
        ...

    def initialize(self, config: QuantConnect.Data.SubscriptionDataConfig, factor_file_provider: QuantConnect.Interfaces.IFactorFileProvider, map_file_provider: QuantConnect.Interfaces.IMapFileProvider, start_time: typing.Union[datetime.datetime, datetime.date]) -> None:
        """
        Initializes the event provider instance
        
        :param config: The SubscriptionDataConfig
        :param factor_file_provider: The factor file provider to use
        :param map_file_provider: The MapFile provider to use
        :param start_time: Start date for the data request
        """
        ...


class DividendEventProvider(System.Object, QuantConnect.Lean.Engine.DataFeeds.Enumerators.ITradableDateEventProvider):
    """Event provider who will emit Dividend events"""

    @property
    def factor_file(self) -> QuantConnect.Data.Auxiliary.CorporateFactorProvider:
        """
        The current instance being used
        
        
        This codeEntityType is protected.
        """
        ...

    @property
    def config(self) -> QuantConnect.Data.SubscriptionDataConfig:
        """
        The associated configuration
        
        
        This codeEntityType is protected.
        """
        ...

    def get_events(self, event_args: QuantConnect.NewTradableDateEventArgs) -> typing.Iterable[QuantConnect.Data.BaseData]:
        """
        Check for dividends and returns them
        
        :param event_args: The new tradable day event arguments
        :returns: New Dividend event if any.
        """
        ...

    def initialize(self, config: QuantConnect.Data.SubscriptionDataConfig, factor_file_provider: QuantConnect.Interfaces.IFactorFileProvider, map_file_provider: QuantConnect.Interfaces.IMapFileProvider, start_time: typing.Union[datetime.datetime, datetime.date]) -> None:
        """
        Initializes this instance
        
        :param config: The SubscriptionDataConfig
        :param factor_file_provider: The factor file provider to use
        :param map_file_provider: The Data.Auxiliary.MapFile provider to use
        :param start_time: Start date for the data request
        """
        ...

    def initialize_factor_file(self) -> None:
        """
        Initializes the factor file to use
        
        
        This codeEntityType is protected.
        """
        ...


class SubscriptionFilterEnumerator(System.Object, System.Collections.Generic.IEnumerator[QuantConnect.Data.BaseData]):
    """Implements a wrapper around a base data enumerator to provide a final filtering step"""

    @property
    def data_filter_error(self) -> _EventContainer[typing.Callable[[System.Object, System.Exception], typing.Any], typing.Any]:
        """Fired when there's an error executing a user's data filter"""
        ...

    @data_filter_error.setter
    def data_filter_error(self, value: _EventContainer[typing.Callable[[System.Object, System.Exception], typing.Any], typing.Any]) -> None:
        ...

    @property
    def current(self) -> QuantConnect.Data.BaseData:
        """Gets the element in the collection at the current position of the enumerator."""
        ...

    def __init__(self, enumerator: System.Collections.Generic.IEnumerator[QuantConnect.Data.BaseData], security: QuantConnect.Securities.Security, end_time: typing.Union[datetime.datetime, datetime.date], extended_market_hours: bool, live_mode: bool, security_exchange_hours: QuantConnect.Securities.SecurityExchangeHours) -> None:
        """
        Initializes a new instance of the SubscriptionFilterEnumerator class
        
        :param enumerator: The source enumerator to be wrapped
        :param security: The security containing an exchange and data filter
        :param end_time: The end time of the subscription
        :param extended_market_hours: True if extended market hours are enabled
        :param live_mode: True if live mode
        :param security_exchange_hours: The security exchange hours instance to use
        """
        ...

    def dispose(self) -> None:
        """Performs application-defined tasks associated with freeing, releasing, or resetting unmanaged resources."""
        ...

    def move_next(self) -> bool:
        """
        Advances the enumerator to the next element of the collection.
        
        :returns: true if the enumerator was successfully advanced to the next element; false if the enumerator has passed the end of the collection.
        """
        ...

    def reset(self) -> None:
        """Sets the enumerator to its initial position, which is before the first element in the collection."""
        ...

    @staticmethod
    def wrap_for_data_feed(result_handler: QuantConnect.Lean.Engine.Results.IResultHandler, enumerator: System.Collections.Generic.IEnumerator[QuantConnect.Data.BaseData], security: QuantConnect.Securities.Security, end_time: typing.Union[datetime.datetime, datetime.date], extended_market_hours: bool, live_mode: bool, security_exchange_hours: QuantConnect.Securities.SecurityExchangeHours) -> QuantConnect.Lean.Engine.DataFeeds.Enumerators.SubscriptionFilterEnumerator:
        """
        Convenience method to wrap the enumerator and attach the data filter event to log and alery users of errors
        
        :param result_handler: Result handler reference used to send errors
        :param enumerator: The source enumerator to be wrapped
        :param security: The security who's data is being enumerated
        :param end_time: The end time of the subscription
        :param extended_market_hours: True if extended market hours are enabled
        :param live_mode: True if live mode
        :param security_exchange_hours: The security exchange hours instance to use
        :returns: A new instance of the SubscriptionFilterEnumerator class that has had it's data_filter_error
        event subscribed to to send errors to the result handler.
        """
        ...


class RateLimitEnumerator(typing.Generic[QuantConnect_Lean_Engine_DataFeeds_Enumerators_RateLimitEnumerator_T], System.Object, System.Collections.Generic.IEnumerator[QuantConnect_Lean_Engine_DataFeeds_Enumerators_RateLimitEnumerator_T]):
    """
    Provides augmentation of how often an enumerator can be called. Time is measured using
    an ITimeProvider instance and calls to the underlying enumerator are limited
    to a minimum time between each call.
    """

    @property
    def current(self) -> QuantConnect_Lean_Engine_DataFeeds_Enumerators_RateLimitEnumerator_T:
        """Gets the element in the collection at the current position of the enumerator."""
        ...

    def __init__(self, enumerator: System.Collections.Generic.IEnumerator[QuantConnect_Lean_Engine_DataFeeds_Enumerators_RateLimitEnumerator_T], time_provider: QuantConnect.ITimeProvider, minimum_time_between_calls: datetime.timedelta) -> None:
        """
        Initializes a new instance of the RateLimitEnumerator{T} class
        
        :param enumerator: The underlying enumerator to place rate limits on
        :param time_provider: Time provider used for determing the time between calls
        :param minimum_time_between_calls: The minimum time allowed between calls to the underlying enumerator
        """
        ...

    def dispose(self) -> None:
        """Performs application-defined tasks associated with freeing, releasing, or resetting unmanaged resources."""
        ...

    def move_next(self) -> bool:
        """
        Advances the enumerator to the next element of the collection.
        
        :returns: true if the enumerator was successfully advanced to the next element; false if the enumerator has passed the end of the collection.
        """
        ...

    def reset(self) -> None:
        """Sets the enumerator to its initial position, which is before the first element in the collection."""
        ...


class FastForwardEnumerator(System.Object, System.Collections.Generic.IEnumerator[QuantConnect.Data.BaseData]):
    """Provides the ability to fast forward an enumerator based on the age of the data"""

    @property
    def current(self) -> QuantConnect.Data.BaseData:
        """Gets the element in the collection at the current position of the enumerator."""
        ...

    def __init__(self, enumerator: System.Collections.Generic.IEnumerator[QuantConnect.Data.BaseData], time_provider: QuantConnect.ITimeProvider, time_zone: typing.Any, maximum_data_age: datetime.timedelta) -> None:
        """
        Initializes a new instance of the FastForwardEnumerator class
        
        :param enumerator: The source enumerator
        :param time_provider: A time provider used to determine age of data
        :param time_zone: The data's time zone
        :param maximum_data_age: The maximum age of data allowed
        """
        ...

    def dispose(self) -> None:
        """Performs application-defined tasks associated with freeing, releasing, or resetting unmanaged resources."""
        ...

    def move_next(self) -> bool:
        """
        Advances the enumerator to the next element of the collection.
        
        :returns: true if the enumerator was successfully advanced to the next element; false if the enumerator has passed the end of the collection.
        """
        ...

    def reset(self) -> None:
        """Sets the enumerator to its initial position, which is before the first element in the collection."""
        ...


class AuxiliaryDataEnumerator(System.Object, System.Collections.Generic.IEnumerator[QuantConnect.Data.BaseData]):
    """
    Auxiliary data enumerator that will, initialize and call the ITradableDateEventProvider.get_events
    implementation each time there is a new tradable day for every ITradableDateEventProvider
    provided.
    """

    @property
    def config(self) -> QuantConnect.Data.SubscriptionDataConfig:
        """
        The associated data configuration
        
        
        This codeEntityType is protected.
        """
        ...

    @property
    def current(self) -> QuantConnect.Data.BaseData:
        """Last read BaseData object from this type and source"""
        ...

    def __init__(self, config: QuantConnect.Data.SubscriptionDataConfig, factor_file_provider: QuantConnect.Interfaces.IFactorFileProvider, map_file_provider: QuantConnect.Interfaces.IMapFileProvider, tradable_date_event_providers: typing.List[QuantConnect.Lean.Engine.DataFeeds.Enumerators.ITradableDateEventProvider], tradable_day_notifier: QuantConnect.Lean.Engine.DataFeeds.Enumerators.ITradableDatesNotifier, start_time: typing.Union[datetime.datetime, datetime.date]) -> None:
        """
        Creates a new instance
        
        :param config: The SubscriptionDataConfig
        :param factor_file_provider: The factor file provider to use
        :param map_file_provider: The MapFile provider to use
        :param tradable_date_event_providers: The tradable dates event providers
        :param tradable_day_notifier: Tradable dates provider
        :param start_time: Start date for the data request
        """
        ...

    def dispose(self) -> None:
        """Dispose of the Stream Reader and close out the source stream and file connections."""
        ...

    def initialize(self) -> None:
        """
        Initializes the underlying tradable data event providers
        
        
        This codeEntityType is protected.
        """
        ...

    def move_next(self) -> bool:
        """
        Advances the enumerator to the next element.
        
        :returns: Always true.
        """
        ...

    def new_tradable_date(self, sender: typing.Any, event_args: QuantConnect.NewTradableDateEventArgs) -> None:
        """
        Handle a new tradable date, drives the ITradableDateEventProvider instances
        
        
        This codeEntityType is protected.
        """
        ...

    def reset(self) -> None:
        """Reset the IEnumeration"""
        ...


class MappingEventProvider(System.Object, QuantConnect.Lean.Engine.DataFeeds.Enumerators.ITradableDateEventProvider):
    """Event provider who will emit SymbolChangedEvent events"""

    @property
    def config(self) -> QuantConnect.Data.SubscriptionDataConfig:
        """
        The associated configuration
        
        
        This codeEntityType is protected.
        """
        ...

    @property
    def map_file(self) -> QuantConnect.Data.Auxiliary.MapFile:
        """
        The current instance being used
        
        
        This codeEntityType is protected.
        """
        ...

    def get_events(self, event_args: QuantConnect.NewTradableDateEventArgs) -> typing.Iterable[QuantConnect.Data.BaseData]:
        """
        Check for new mappings
        
        :param event_args: The new tradable day event arguments
        :returns: New mapping event if any.
        """
        ...

    def initialize(self, config: QuantConnect.Data.SubscriptionDataConfig, factor_file_provider: QuantConnect.Interfaces.IFactorFileProvider, map_file_provider: QuantConnect.Interfaces.IMapFileProvider, start_time: typing.Union[datetime.datetime, datetime.date]) -> None:
        """
        Initializes this instance
        
        :param config: The SubscriptionDataConfig
        :param factor_file_provider: The factor file provider to use
        :param map_file_provider: The Data.Auxiliary.MapFile provider to use
        :param start_time: Start date for the data request
        """
        ...

    def initialize_map_file(self) -> None:
        """
        Initializes the map file to use
        
        
        This codeEntityType is protected.
        """
        ...


class LiveMappingEventProvider(QuantConnect.Lean.Engine.DataFeeds.Enumerators.MappingEventProvider):
    """Event provider who will emit SymbolChangedEvent events"""

    def get_events(self, event_args: QuantConnect.NewTradableDateEventArgs) -> typing.Iterable[QuantConnect.Data.BaseData]:
        """Check for new mappings"""
        ...


class DelistingEventProvider(System.Object, QuantConnect.Lean.Engine.DataFeeds.Enumerators.ITradableDateEventProvider):
    """Event provider who will emit Delisting events"""

    @property
    def delisting_date(self) -> QuantConnect.Util.ReferenceWrapper[datetime.datetime]:
        """
        The delisting date
        
        
        This codeEntityType is protected.
        """
        ...

    @delisting_date.setter
    def delisting_date(self, value: QuantConnect.Util.ReferenceWrapper[datetime.datetime]) -> None:
        ...

    @property
    def map_file(self) -> QuantConnect.Data.Auxiliary.MapFile:
        """
        The current instance being used
        
        
        This codeEntityType is protected.
        """
        ...

    @property
    def config(self) -> QuantConnect.Data.SubscriptionDataConfig:
        """
        The associated configuration
        
        
        This codeEntityType is protected.
        """
        ...

    def get_events(self, event_args: QuantConnect.NewTradableDateEventArgs) -> typing.Iterable[QuantConnect.Data.BaseData]:
        """
        Check for delistings
        
        :param event_args: The new tradable day event arguments
        :returns: New delisting event if any.
        """
        ...

    def initialize(self, config: QuantConnect.Data.SubscriptionDataConfig, factor_file_provider: QuantConnect.Interfaces.IFactorFileProvider, map_file_provider: QuantConnect.Interfaces.IMapFileProvider, start_time: typing.Union[datetime.datetime, datetime.date]) -> None:
        """
        Initializes this instance
        
        :param config: The SubscriptionDataConfig
        :param factor_file_provider: The factor file provider to use
        :param map_file_provider: The Data.Auxiliary.MapFile provider to use
        :param start_time: Start date for the data request
        """
        ...

    def initialize_map_file(self) -> None:
        """
        Initializes the factor file to use
        
        
        This codeEntityType is protected.
        """
        ...


class LiveFillForwardEnumerator(QuantConnect.Lean.Engine.DataFeeds.Enumerators.FillForwardEnumerator):
    """
    An implementation of the FillForwardEnumerator that uses an ITimeProvider
    to determine if a fill forward bar needs to be emitted
    """

    def __init__(self, time_provider: QuantConnect.ITimeProvider, enumerator: System.Collections.Generic.IEnumerator[QuantConnect.Data.BaseData], exchange: QuantConnect.Securities.SecurityExchange, fill_forward_resolution: QuantConnect.Util.IReadOnlyRef[datetime.timedelta], is_extended_market_hours: bool, subscription_start_time: typing.Union[datetime.datetime, datetime.date], subscription_end_time: typing.Union[datetime.datetime, datetime.date], data_resolution: QuantConnect.Resolution, data_time_zone: typing.Any, daily_strict_end_time_enabled: bool, data_type: typing.Type = None, last_point_tracker: QuantConnect.Lean.Engine.DataFeeds.Enumerators.LastPointTracker = None) -> None:
        """
        Initializes a new instance of the LiveFillForwardEnumerator class that accepts
        a reference to the fill forward resolution, useful if the fill forward resolution is dynamic
        and changing as the enumeration progresses
        
        :param time_provider: The source of time used to gauage when this enumerator should emit extra bars when
        null data is returned from the source enumerator
        :param enumerator: The source enumerator to be filled forward
        :param exchange: The exchange used to determine when to insert fill forward data
        :param fill_forward_resolution: The resolution we'd like to receive data on
        :param is_extended_market_hours: True to use the exchange's extended market hours, false to use the regular market hours
        :param subscription_start_time: The start time of the subscription
        :param subscription_end_time: The end time of the subscription, once passing this date the enumerator will stop
        :param data_resolution: The source enumerator's data resolution
        :param data_time_zone: Time zone of the underlying source data
        :param daily_strict_end_time_enabled: True if daily strict end times are enabled
        :param data_type: The configuration data type this enumerator is for
        :param last_point_tracker: A reference to the last point emitted before this enumerator is first enumerated
        """
        ...

    @staticmethod
    def get_maximum_data_timeout(resolution: QuantConnect.Resolution) -> datetime.timedelta:
        """Helper method to know how much we should wait before fill forwarding a bar in live trading"""
        ...

    def requires_fill_forward_data(self, fill_forward_resolution: datetime.timedelta, previous: QuantConnect.Data.BaseData, next: QuantConnect.Data.BaseData, fill_forward: typing.Optional[QuantConnect.Data.BaseData]) -> typing.Tuple[bool, QuantConnect.Data.BaseData]:
        """
        Determines whether or not fill forward is required, and if true, will produce the new fill forward data
        
        
        This codeEntityType is protected.
        
        :param fill_forward_resolution: 
        :param previous: The last piece of data emitted by this enumerator
        :param next: The next piece of data on the source enumerator, this may be null
        :param fill_forward: When this function returns true, this will have a non-null value, null when the function returns false
        :returns: True when a new fill forward piece of data was produced and should be emitted by this enumerator.
        """
        ...


class LiveAuxiliaryDataEnumerator(QuantConnect.Lean.Engine.DataFeeds.Enumerators.AuxiliaryDataEnumerator):
    """Auxiliary data enumerator that will trigger new tradable dates event accordingly"""

    def __init__(self, config: QuantConnect.Data.SubscriptionDataConfig, factor_file_provider: QuantConnect.Interfaces.IFactorFileProvider, map_file_provider: QuantConnect.Interfaces.IMapFileProvider, tradable_date_event_providers: typing.List[QuantConnect.Lean.Engine.DataFeeds.Enumerators.ITradableDateEventProvider], start_time: typing.Union[datetime.datetime, datetime.date], time_provider: QuantConnect.ITimeProvider, security_cache: QuantConnect.Securities.SecurityCache) -> None:
        """
        Creates a new instance
        
        :param config: The SubscriptionDataConfig
        :param factor_file_provider: The factor file provider to use
        :param map_file_provider: The MapFile provider to use
        :param tradable_date_event_providers: The tradable dates event providers
        :param start_time: Start date for the data request
        :param time_provider: The time provider to use
        :param security_cache: The security cache
        """
        ...

    def move_next(self) -> bool:
        """Moves the LiveAuxiliaryDataEnumerator to the next item"""
        ...

    @staticmethod
    def try_create(data_config: QuantConnect.Data.SubscriptionDataConfig, time_provider: QuantConnect.ITimeProvider, security_cache: QuantConnect.Securities.SecurityCache, map_file_provider: QuantConnect.Interfaces.IMapFileProvider, file_provider: QuantConnect.Interfaces.IFactorFileProvider, start_time: typing.Union[datetime.datetime, datetime.date], enumerator: typing.Optional[System.Collections.Generic.IEnumerator[QuantConnect.Data.BaseData]]) -> typing.Tuple[bool, System.Collections.Generic.IEnumerator[QuantConnect.Data.BaseData]]:
        """
        Helper method to create a new instance.
        Knows which security types should create one and determines the appropriate delisting event provider to use
        """
        ...


class SynchronizingSliceEnumerator(QuantConnect.Lean.Engine.DataFeeds.Enumerators.SynchronizingEnumerator[QuantConnect.Data.Slice]):
    """
    Represents an enumerator capable of synchronizing other slice enumerators in time.
    This assumes that all enumerators have data time stamped in the same time zone
    """

    @overload
    def __init__(self, *enumerators: typing.Union[System.Collections.Generic.IEnumerator[QuantConnect.Data.Slice], typing.Iterable[System.Collections.Generic.IEnumerator[QuantConnect.Data.Slice]]]) -> None:
        """
        Initializes a new instance of the SynchronizingSliceEnumerator class
        
        :param enumerators: The enumerators to be synchronized. NOTE: Assumes the same time zone for all data
        """
        ...

    @overload
    def __init__(self, enumerators: typing.List[System.Collections.IEnumerator]) -> None:
        """
        Initializes a new instance of the SynchronizingSliceEnumerator class
        
        :param enumerators: The enumerators to be synchronized. NOTE: Assumes the same time zone for all data
        """
        ...

    def get_instance_time(self, instance: QuantConnect.Data.Slice) -> datetime.datetime:
        """
        Gets the Timestamp for the data
        
        
        This codeEntityType is protected.
        """
        ...


class LiveDividendEventProvider(QuantConnect.Lean.Engine.DataFeeds.Enumerators.DividendEventProvider):
    """Event provider who will emit SymbolChangedEvent events"""

    def get_events(self, event_args: QuantConnect.NewTradableDateEventArgs) -> typing.Iterable[QuantConnect.Data.BaseData]:
        """
        Check for dividends and returns them
        
        :param event_args: The new tradable day event arguments
        :returns: New Dividend event if any.
        """
        ...


class NewDataAvailableEventArgs(System.EventArgs):
    """Event args for when a new data point is ready to be emitted"""

    @property
    def data_point(self) -> QuantConnect.Data.IBaseData:
        """The new data point"""
        ...

    @data_point.setter
    def data_point(self, value: QuantConnect.Data.IBaseData) -> None:
        ...


class LiveDelistingEventProvider(QuantConnect.Lean.Engine.DataFeeds.Enumerators.DelistingEventProvider):
    """Delisting event provider implementation which will source the delisting date based on new map files"""

    def get_events(self, event_args: QuantConnect.NewTradableDateEventArgs) -> typing.Iterable[QuantConnect.Data.BaseData]:
        """
        Check for delistings
        
        :param event_args: The new tradable day event arguments
        :returns: New delisting event if any.
        """
        ...


class ScannableEnumerator(typing.Generic[QuantConnect_Lean_Engine_DataFeeds_Enumerators_ScannableEnumerator_T], System.Object, System.Collections.Generic.IEnumerator[QuantConnect_Lean_Engine_DataFeeds_Enumerators_ScannableEnumerator_T]):
    """An implementation of IEnumerator{T} that relies on "consolidated" data"""

    @property
    def current(self) -> QuantConnect_Lean_Engine_DataFeeds_Enumerators_ScannableEnumerator_T:
        """Gets the element in the collection at the current position of the enumerator."""
        ...

    def __init__(self, consolidator: typing.Union[QuantConnect.Data.Consolidators.IDataConsolidator, QuantConnect.Python.PythonConsolidator, datetime.timedelta], time_zone: typing.Any, time_provider: QuantConnect.ITimeProvider, new_data_available_handler: typing.Callable[[System.Object, System.EventArgs], typing.Any], is_period_based: bool = True) -> None:
        """
        Initializes a new instance of the ScannableEnumerator{T} class
        
        :param consolidator: Consolidator taking BaseData updates and firing events containing new 'consolidated' data
        :param time_zone: The time zone the raw data is time stamped in
        :param time_provider: The time provider instance used to determine when bars are completed and can be emitted
        :param new_data_available_handler: The event handler for a new available data point
        :param is_period_based: The consolidator is period based, this will enable scanning on move_next
        """
        ...

    def dispose(self) -> None:
        """Performs application-defined tasks associated with freeing, releasing, or resetting unmanaged resources."""
        ...

    def move_next(self) -> bool:
        """
        Advances the enumerator to the next element of the collection.
        
        :returns: true if the enumerator was successfully advanced to the next element; false if the enumerator has passed the end of the collection.
        """
        ...

    def reset(self) -> None:
        """Sets the enumerator to its initial position, which is before the first element in the collection."""
        ...

    def update(self, data: QuantConnect_Lean_Engine_DataFeeds_Enumerators_ScannableEnumerator_T) -> None:
        """
        Updates the consolidator
        
        :param data: The data to consolidate
        """
        ...


class SubscriptionDataEnumerator(System.Object, System.Collections.Generic.IEnumerator[QuantConnect.Lean.Engine.DataFeeds.SubscriptionData]):
    """An IEnumerator{SubscriptionData} which wraps an existing IEnumerator{BaseData}."""

    @property
    def current(self) -> QuantConnect.Lean.Engine.DataFeeds.SubscriptionData:
        """Gets the element in the collection at the current position of the enumerator."""
        ...

    def __init__(self, configuration: QuantConnect.Data.SubscriptionDataConfig, exchange_hours: QuantConnect.Securities.SecurityExchangeHours, offset_provider: QuantConnect.TimeZoneOffsetProvider, enumerator: System.Collections.Generic.IEnumerator[QuantConnect.Data.BaseData], is_universe: bool, daily_strict_end_time_enabled: bool) -> None:
        """
        Creates a new instance
        
        :param configuration: The subscription's configuration
        :param exchange_hours: The security's exchange hours
        :param offset_provider: The subscription's time zone offset provider
        :param enumerator: The underlying data enumerator
        :param is_universe: The subscription is a universe subscription
        :returns: A subscription data enumerator.
        """
        ...

    def dispose(self) -> None:
        """Performs application-defined tasks associated with freeing, releasing, or resetting unmanaged resources."""
        ...

    def move_next(self) -> bool:
        """
        Advances the enumerator to the next element of the collection.
        
        :returns: True if the enumerator was successfully advanced to the next element;
        False if the enumerator has passed the end of the collection.
        """
        ...

    def reset(self) -> None:
        """Sets the enumerator to its initial position, which is before the first element in the collection."""
        ...


class BaseDataCollectionAggregatorEnumerator(System.Object, System.Collections.Generic.IEnumerator[QuantConnect.Data.UniverseSelection.BaseDataCollection]):
    """
    Provides an implementation of IEnumerator{BaseDataCollection}
    that aggregates an underlying IEnumerator{BaseData} into a single
    data packet
    """

    @property
    def current(self) -> QuantConnect.Data.UniverseSelection.BaseDataCollection:
        """Gets the element in the collection at the current position of the enumerator."""
        ...

    def __init__(self, enumerator: System.Collections.Generic.IEnumerator[QuantConnect.Data.BaseData], symbol: typing.Union[QuantConnect.Symbol, str, QuantConnect.Data.Market.BaseContract], live_mode: bool = False) -> None:
        """
        Initializes a new instance of the BaseDataCollectionAggregatorEnumerator class
        This will aggregate instances emitted from the underlying enumerator and tag them with the
        specified symbol
        
        :param enumerator: The underlying enumerator to aggregate
        :param symbol: The symbol to place on the aggregated collection
        :param live_mode: True if running in live mode
        """
        ...

    def dispose(self) -> None:
        """Performs application-defined tasks associated with freeing, releasing, or resetting unmanaged resources."""
        ...

    def move_next(self) -> bool:
        """
        Advances the enumerator to the next element of the collection.
        
        :returns: true if the enumerator was successfully advanced to the next element; false if the enumerator has passed the end of the collection.
        """
        ...

    def reset(self) -> None:
        """Sets the enumerator to its initial position, which is before the first element in the collection."""
        ...


class SplitEventProvider(System.Object, QuantConnect.Lean.Engine.DataFeeds.Enumerators.ITradableDateEventProvider):
    """Event provider who will emit Split events"""

    @property
    def factor_file(self) -> QuantConnect.Data.Auxiliary.CorporateFactorProvider:
        """
        The current instance being used
        
        
        This codeEntityType is protected.
        """
        ...

    @property
    def config(self) -> QuantConnect.Data.SubscriptionDataConfig:
        """
        The associated configuration
        
        
        This codeEntityType is protected.
        """
        ...

    def get_events(self, event_args: QuantConnect.NewTradableDateEventArgs) -> typing.Iterable[QuantConnect.Data.BaseData]:
        """
        Check for new splits
        
        :param event_args: The new tradable day event arguments
        :returns: New split event if any.
        """
        ...

    def initialize(self, config: QuantConnect.Data.SubscriptionDataConfig, factor_file_provider: QuantConnect.Interfaces.IFactorFileProvider, map_file_provider: QuantConnect.Interfaces.IMapFileProvider, start_time: typing.Union[datetime.datetime, datetime.date]) -> None:
        """
        Initializes this instance
        
        :param config: The SubscriptionDataConfig
        :param factor_file_provider: The factor file provider to use
        :param map_file_provider: The Data.Auxiliary.MapFile provider to use
        :param start_time: Start date for the data request
        """
        ...

    def initialize_factor_file(self) -> None:
        """
        Initializes the factor file to use
        
        
        This codeEntityType is protected.
        """
        ...


class LiveSplitEventProvider(QuantConnect.Lean.Engine.DataFeeds.Enumerators.SplitEventProvider):
    """Event provider who will emit SymbolChangedEvent events"""

    def get_events(self, event_args: QuantConnect.NewTradableDateEventArgs) -> typing.Iterable[QuantConnect.Data.BaseData]:
        """
        Check for dividends and returns them
        
        :param event_args: The new tradable day event arguments
        :returns: New Dividend event if any.
        """
        ...


class _EventContainer(typing.Generic[QuantConnect_Lean_Engine_DataFeeds_Enumerators__EventContainer_Callable, QuantConnect_Lean_Engine_DataFeeds_Enumerators__EventContainer_ReturnType]):
    """This class is used to provide accurate autocomplete on events and cannot be imported."""

    def __call__(self, *args: typing.Any, **kwargs: typing.Any) -> QuantConnect_Lean_Engine_DataFeeds_Enumerators__EventContainer_ReturnType:
        """Fires the event."""
        ...

    def __iadd__(self, item: QuantConnect_Lean_Engine_DataFeeds_Enumerators__EventContainer_Callable) -> typing.Self:
        """Registers an event handler."""
        ...

    def __isub__(self, item: QuantConnect_Lean_Engine_DataFeeds_Enumerators__EventContainer_Callable) -> typing.Self:
        """Unregisters an event handler."""
        ...


