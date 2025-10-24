from typing import overload
from enum import IntEnum
import datetime
import typing

import QuantConnect.Orders
import QuantConnect.Orders.TimeInForces
import QuantConnect.Securities


class GoodTilCanceledTimeInForce(QuantConnect.Orders.TimeInForce):
    """Good Til Canceled Time In Force - order does never expires"""

    def is_fill_valid(self, security: QuantConnect.Securities.Security, order: QuantConnect.Orders.Order, fill: QuantConnect.Orders.OrderEvent) -> bool:
        """
        Checks if an order fill is valid
        
        :param security: The security matching the order
        :param order: The order to be checked
        :param fill: The order fill to be checked
        :returns: Returns true if the order fill can be emitted, false otherwise.
        """
        ...

    def is_order_expired(self, security: QuantConnect.Securities.Security, order: QuantConnect.Orders.Order) -> bool:
        """
        Checks if an order is expired
        
        :param security: The security matching the order
        :param order: The order to be checked
        :returns: Returns true if the order has expired, false otherwise.
        """
        ...


class GoodTilDateTimeInForce(QuantConnect.Orders.TimeInForce):
    """Good Til Date Time In Force - order expires and will be cancelled on a fixed date/time"""

    @property
    def expiry(self) -> datetime.datetime:
        """The date/time on which the order will expire and will be cancelled"""
        ...

    def __init__(self, expiry: typing.Union[datetime.datetime, datetime.date]) -> None:
        """Initializes a new instance of the GoodTilDateTimeInForce class"""
        ...

    def get_forex_order_expiry_date_time(self, order: QuantConnect.Orders.Order) -> datetime.datetime:
        """Returns the expiry date and time (UTC) for a Forex order"""
        ...

    def is_fill_valid(self, security: QuantConnect.Securities.Security, order: QuantConnect.Orders.Order, fill: QuantConnect.Orders.OrderEvent) -> bool:
        """
        Checks if an order fill is valid
        
        :param security: The security matching the order
        :param order: The order to be checked
        :param fill: The order fill to be checked
        :returns: Returns true if the order fill can be emitted, false otherwise.
        """
        ...

    def is_order_expired(self, security: QuantConnect.Securities.Security, order: QuantConnect.Orders.Order) -> bool:
        """
        Checks if an order is expired
        
        :param security: The security matching the order
        :param order: The order to be checked
        :returns: Returns true if the order has expired, false otherwise.
        """
        ...


class DayTimeInForce(QuantConnect.Orders.TimeInForce):
    """Day Time In Force - order expires at market close"""

    def is_fill_valid(self, security: QuantConnect.Securities.Security, order: QuantConnect.Orders.Order, fill: QuantConnect.Orders.OrderEvent) -> bool:
        """
        Checks if an order fill is valid
        
        :param security: The security matching the order
        :param order: The order to be checked
        :param fill: The order fill to be checked
        :returns: Returns true if the order fill can be emitted, false otherwise.
        """
        ...

    def is_order_expired(self, security: QuantConnect.Securities.Security, order: QuantConnect.Orders.Order) -> bool:
        """
        Checks if an order is expired
        
        :param security: The security matching the order
        :param order: The order to be checked
        :returns: Returns true if the order has expired, false otherwise.
        """
        ...


