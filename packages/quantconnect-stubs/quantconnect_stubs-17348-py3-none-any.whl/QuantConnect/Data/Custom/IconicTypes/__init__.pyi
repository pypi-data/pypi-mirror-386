from typing import overload
from enum import IntEnum
import datetime
import typing

import QuantConnect
import QuantConnect.Data
import QuantConnect.Data.Custom.IconicTypes
import QuantConnect.Data.Market


class IndexedLinkedData(QuantConnect.Data.IndexedBaseData):
    """
    Data type that is indexed, i.e. a file that points to another file containing the contents
    we're looking for in a Symbol.
    """

    @property
    def count(self) -> int:
        """Example data property"""
        ...

    @count.setter
    def count(self, value: int) -> None:
        ...

    def data_time_zone(self) -> typing.Any:
        """
        Set the data time zone to UTC
        
        :returns: Time zone as UTC.
        """
        ...

    def default_resolution(self) -> QuantConnect.Resolution:
        """
        Sets the default resolution to Second
        
        :returns: Resolution.Second.
        """
        ...

    def get_source(self, config: QuantConnect.Data.SubscriptionDataConfig, date: datetime.datetime, is_live_mode: bool) -> QuantConnect.Data.SubscriptionDataSource:
        """
        Gets the source of the index file
        
        :param config: Configuration object
        :param date: Date of this source file
        :param is_live_mode: Is live mode
        :returns: SubscriptionDataSource indicating where data is located and how it's stored.
        """
        ...

    def get_source_for_an_index(self, config: QuantConnect.Data.SubscriptionDataConfig, date: datetime.datetime, index: str, is_live_mode: bool) -> QuantConnect.Data.SubscriptionDataSource:
        """
        Determines the actual source from an index contained within a ticker folder
        
        :param config: Subscription configuration
        :param date: Date
        :param index: File to load data from
        :param is_live_mode: Is live mode
        :returns: SubscriptionDataSource pointing to the article.
        """
        ...

    def is_sparse_data(self) -> bool:
        """
        Indicates whether the data source is sparse.
        If false, it will disable missing file logging.
        
        :returns: true.
        """
        ...

    def reader(self, config: QuantConnect.Data.SubscriptionDataConfig, line: str, date: datetime.datetime, is_live_mode: bool) -> QuantConnect.Data.BaseData:
        """
        Creates an instance from a line of JSON containing article information read from the `content` directory
        
        :param config: Subscription configuration
        :param line: Line of data
        :param date: Date
        :param is_live_mode: Is live mode
        """
        ...

    def requires_mapping(self) -> bool:
        """
        Indicates whether the data source can undergo
        rename events/is tied to equities.
        
        :returns: true.
        """
        ...

    def supported_resolutions(self) -> typing.List[QuantConnect.Resolution]:
        """
        Gets a list of all the supported Resolutions
        
        :returns: All resolutions.
        """
        ...


class IndexedLinkedData2(QuantConnect.Data.IndexedBaseData):
    """
    Data type that is indexed, i.e. a file that points to another file containing the contents
    we're looking for in a Symbol.
    """

    @property
    def count(self) -> int:
        """Example data property"""
        ...

    @count.setter
    def count(self, value: int) -> None:
        ...

    def data_time_zone(self) -> typing.Any:
        """
        Set the data time zone to UTC
        
        :returns: Time zone as UTC.
        """
        ...

    def default_resolution(self) -> QuantConnect.Resolution:
        """
        Sets the default resolution to Second
        
        :returns: Resolution.Second.
        """
        ...

    def get_source(self, config: QuantConnect.Data.SubscriptionDataConfig, date: datetime.datetime, is_live_mode: bool) -> QuantConnect.Data.SubscriptionDataSource:
        """
        Gets the source of the index file
        
        :param config: Configuration object
        :param date: Date of this source file
        :param is_live_mode: Is live mode
        :returns: SubscriptionDataSource indicating where data is located and how it's stored.
        """
        ...

    def get_source_for_an_index(self, config: QuantConnect.Data.SubscriptionDataConfig, date: datetime.datetime, index: str, is_live_mode: bool) -> QuantConnect.Data.SubscriptionDataSource:
        """
        Determines the actual source from an index contained within a ticker folder
        
        :param config: Subscription configuration
        :param date: Date
        :param index: File to load data from
        :param is_live_mode: Is live mode
        :returns: SubscriptionDataSource pointing to the article.
        """
        ...

    def is_sparse_data(self) -> bool:
        """
        Indicates whether the data source is sparse.
        If false, it will disable missing file logging.
        
        :returns: true.
        """
        ...

    def reader(self, config: QuantConnect.Data.SubscriptionDataConfig, line: str, date: datetime.datetime, is_live_mode: bool) -> QuantConnect.Data.BaseData:
        """
        Creates an instance from a line of JSON containing article information read from the `content` directory
        
        :param config: Subscription configuration
        :param line: Line of data
        :param date: Date
        :param is_live_mode: Is live mode
        """
        ...

    def requires_mapping(self) -> bool:
        """
        Indicates whether the data source can undergo
        rename events/is tied to equities.
        
        :returns: true.
        """
        ...

    def supported_resolutions(self) -> typing.List[QuantConnect.Resolution]:
        """
        Gets a list of all the supported Resolutions
        
        :returns: All resolutions.
        """
        ...


class UnlinkedData(QuantConnect.Data.BaseData):
    """Data source that is unlinked (no mapping) and takes any ticker when calling AddData"""

    any_ticker: bool
    """If true, we accept any ticker from the AddData call"""

    @property
    def ticker(self) -> str:
        """Example data"""
        ...

    @ticker.setter
    def ticker(self, value: str) -> None:
        ...

    def data_time_zone(self) -> typing.Any:
        """
        Set the data time zone to UTC
        
        :returns: Time zone as UTC.
        """
        ...

    def default_resolution(self) -> QuantConnect.Resolution:
        """
        Sets the default resolution to Second
        
        :returns: Resolution.Second.
        """
        ...

    def get_source(self, config: QuantConnect.Data.SubscriptionDataConfig, date: datetime.datetime, is_live_mode: bool) -> QuantConnect.Data.SubscriptionDataSource:
        """
        Return the path string source of the file. This will be converted to a stream
        
        :param config: Configuration object
        :param date: Date of this source file
        :param is_live_mode: true if we're in live mode, false for backtesting mode
        :returns: String path of source file.
        """
        ...

    def is_sparse_data(self) -> bool:
        """
        Indicates whether the data source is sparse.
        If false, it will disable missing file logging.
        
        :returns: true.
        """
        ...

    def reader(self, config: QuantConnect.Data.SubscriptionDataConfig, line: str, date: datetime.datetime, is_live_mode: bool) -> QuantConnect.Data.BaseData:
        """
        Creates UnlinkedData objects using the subscription data config setup as well as the date.
        
        :param config: Subscription data config setup object
        :param line: Line of the source document
        :param date: Date of the requested data
        :param is_live_mode: true if we're in live mode, false for backtesting mode
        :returns: Instance of the UnlinkedData object generated by this line of the CSV.
        """
        ...

    def requires_mapping(self) -> bool:
        """
        Indicates whether the data source can undergo
        rename events/is tied to equities.
        
        :returns: true.
        """
        ...

    def supported_resolutions(self) -> typing.List[QuantConnect.Resolution]:
        """
        Gets a list of all the supported Resolutions
        
        :returns: All resolutions.
        """
        ...


class LinkedData(QuantConnect.Data.BaseData):
    """Data source that is linked (tickers that can have renames or be delisted)"""

    @property
    def count(self) -> int:
        """Example data"""
        ...

    @count.setter
    def count(self, value: int) -> None:
        ...

    def data_time_zone(self) -> typing.Any:
        """
        Set the data time zone to UTC
        
        :returns: Time zone as UTC.
        """
        ...

    def default_resolution(self) -> QuantConnect.Resolution:
        """
        Sets the default resolution to Second
        
        :returns: Resolution.Second.
        """
        ...

    def get_source(self, config: QuantConnect.Data.SubscriptionDataConfig, date: datetime.datetime, is_live_mode: bool) -> QuantConnect.Data.SubscriptionDataSource:
        """Return the URL string source of the file. This will be converted to a stream"""
        ...

    def is_sparse_data(self) -> bool:
        """
        Indicates whether the data source is sparse.
        If false, it will disable missing file logging.
        
        :returns: true.
        """
        ...

    def reader(self, config: QuantConnect.Data.SubscriptionDataConfig, line: str, date: datetime.datetime, is_live_mode: bool) -> QuantConnect.Data.BaseData:
        """
        Reader converts each line of the data source into BaseData objects. Each data type creates its own factory method, and returns a new instance of the object
        each time it is called. The returned object is assumed to be time stamped in the config.ExchangeTimeZone.
        """
        ...

    def requires_mapping(self) -> bool:
        """
        Indicates whether the data source can undergo
        rename events/is tied to equities.
        
        :returns: true.
        """
        ...

    def supported_resolutions(self) -> typing.List[QuantConnect.Resolution]:
        """
        Gets a list of all the supported Resolutions
        
        :returns: All resolutions.
        """
        ...


class UnlinkedDataTradeBar(QuantConnect.Data.Market.TradeBar):
    """Data source that is unlinked (no mapping) and takes any ticker when calling AddData"""

    any_ticker: bool
    """If true, we accept any ticker from the AddData call"""

    def __init__(self) -> None:
        """Creates a new instance of an UnlinkedTradeBar"""
        ...

    def data_time_zone(self) -> typing.Any:
        """
        Set the data time zone to UTC
        
        :returns: Time zone as UTC.
        """
        ...

    def default_resolution(self) -> QuantConnect.Resolution:
        """
        Sets the default resolution to Second
        
        :returns: Resolution.Second.
        """
        ...

    def get_source(self, config: QuantConnect.Data.SubscriptionDataConfig, date: datetime.datetime, is_live_mode: bool) -> QuantConnect.Data.SubscriptionDataSource:
        """
        Get Source for Custom Data File
        >> What source file location would you prefer for each type of usage:
        
        :param config: Configuration object
        :param date: Date of this source request if source spread across multiple files
        :param is_live_mode: true if we're in live mode, false for backtesting mode
        :returns: String source location of the file.
        """
        ...

    def is_sparse_data(self) -> bool:
        """
        Indicates whether the data source is sparse.
        If false, it will disable missing file logging.
        
        :returns: true.
        """
        ...

    def reader(self, config: QuantConnect.Data.SubscriptionDataConfig, line: str, date: datetime.datetime, is_live_mode: bool) -> QuantConnect.Data.BaseData:
        """
        Fetch the data from the storage and feed it line by line into the engine.
        
        :param config: Symbols, Resolution, DataType,
        :param line: Line from the data file requested
        :param date: Date of this reader request
        :param is_live_mode: true if we're in live mode, false for backtesting mode
        :returns: Enumerable iterator for returning each line of the required data.
        """
        ...

    def requires_mapping(self) -> bool:
        """
        Indicates whether the data source can undergo
        rename events/is tied to equities.
        
        :returns: true.
        """
        ...

    def supported_resolutions(self) -> typing.List[QuantConnect.Resolution]:
        """
        Gets a list of all the supported Resolutions
        
        :returns: All resolutions.
        """
        ...


