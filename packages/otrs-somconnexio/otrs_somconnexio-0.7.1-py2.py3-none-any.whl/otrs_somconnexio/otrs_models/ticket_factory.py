from otrs_somconnexio.otrs_models.adsl_ticket import ADSLTicket
from otrs_somconnexio.otrs_models.fiber_ticket import FiberTicket
from otrs_somconnexio.otrs_models.mobile_ticket import MobileTicket, MobilePausedTicket
from otrs_somconnexio.otrs_models.router_4G_ticket import Router4GTicket
from otrs_somconnexio.otrs_models.switchboard_ticket import SwitchboardTicket
from otrs_somconnexio.otrs_models.switchboard_header_ticket import (
    SwitchboardHeaderTicket,
)
from otrs_somconnexio.exceptions import ServiceTypeNotAllowedError


class TicketFactory(object):
    """This factory is to generate the concrete ticket with his internal logic based on
    the service of the EticomContract.
    """

    def __init__(self, service_data, customer_data, responsible_data=None):
        self.service_data = service_data
        self.customer_data = customer_data
        self.responsible_data = responsible_data

    def build(self):
        """Create a OTRS Process Ticket with the information of the ServiceData and return it."""

        if self.service_data.service_type == "adsl":
            TicketClass = ADSLTicket
        elif self.service_data.service_type == "fiber":
            TicketClass = FiberTicket
        elif self.service_data.service_type == "mobile":
            if self.service_data.is_grouped_with_fiber and (
                self.service_data.type == "portability"
                or self.service_data.is_from_pack
            ):
                TicketClass = MobilePausedTicket
            else:
                TicketClass = MobileTicket
        elif self.service_data.service_type == "4G":
            TicketClass = Router4GTicket
        elif self.service_data.service_type == "header_switchboard":
            TicketClass = SwitchboardHeaderTicket
        elif self.service_data.service_type == "switchboard":
            TicketClass = SwitchboardTicket
        else:
            raise ServiceTypeNotAllowedError(
                self.service_data.order_id, self.service_data.service_type
            )

        return TicketClass(
            service_data=self.service_data,
            customer_data=self.customer_data,
            responsible_data=self.responsible_data,
        )
