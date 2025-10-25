# coding: utf-8
import unittest
from mock import Mock, patch

from otrs_somconnexio.otrs_models.router_4G_ticket import Router4GTicket
from otrs_somconnexio.otrs_models.configurations.provision.router_4G_ticket import (
    Router4GTicketConfiguration,
)


class Router4GTicketTestCase(unittest.TestCase):
    def setUp(self):
        self.responsible_data = Mock(spec=["email"])

    @patch("otrs_somconnexio.otrs_models.provision_ticket.Ticket")
    def test_build_ticket(self, MockTicket):
        customer_data = Mock(spec=["id"])
        service_data = Mock(spec=["order_id", "technology"])

        expected_ticket_arguments = {
            "Title": "Ticket#{} - Només 4G".format(service_data.order_id),
            "Type": Router4GTicketConfiguration.type,
            "QueueID": Router4GTicketConfiguration.queue_id,
            "State": Router4GTicketConfiguration.state,
            "SLA": False,
            "Service": False,
            "Priority": Router4GTicketConfiguration.priority,
            "CustomerUser": customer_data.id,
            "CustomerID": customer_data.id,
            "Responsible": self.responsible_data.email,
        }

        Router4GTicket(
            service_data, customer_data, self.responsible_data
        )._build_ticket()
        MockTicket.assert_called_with(expected_ticket_arguments)

    @patch("otrs_somconnexio.otrs_models.provision_ticket.ProvisionArticle")
    def test_build_article(self, MockInternetArticle):
        customer_data = Mock(spec=[])
        service_data = Mock(spec=["order_id", "notes", "technology"])

        mock_internet_article = MockInternetArticle.return_value

        Router4GTicket(
            service_data, customer_data, self.responsible_data
        )._build_article()

        MockInternetArticle.assert_called_with(
            service_data.technology, service_data.order_id, "4G", service_data.notes
        )
        mock_internet_article.call.assert_called_once()

    @patch("otrs_somconnexio.otrs_models.router_4G_ticket.Router4GDynamicFields")
    def test_build_dynamic_fields(self, MockRouter4GDynamicFields):
        customer_data = Mock(spec=[])
        service_data = Mock(spec=["order_id"])

        mock_internet_dynamic_fields = MockRouter4GDynamicFields.return_value

        Router4GTicket(
            service_data, customer_data, self.responsible_data
        )._build_dynamic_fields()

        MockRouter4GDynamicFields.assert_called_with(
            service_data,
            customer_data,
            Router4GTicketConfiguration.process_id,
            Router4GTicketConfiguration.activity_id,
        )
        mock_internet_dynamic_fields.all.assert_called_once()

    @patch("otrs_somconnexio.otrs_models.provision_ticket.OTRSClient")
    def test_create(self, MockOTRSClient):
        customer_data = Mock(
            spec=[
                "id",
                "first_name",
                "name",
                "vat_number",
                "has_active_contracts",
                "language",
            ]
        )
        service_data = Mock(
            spec=[
                "order_id",
                "iban",
                "email",
                "previous_service",
                "contact_phone",
                "phone_number",
                "previous_provider",
                "previous_owner_vat",
                "previous_owner_name",
                "previous_owner_surname",
                "previous_contract_address",
                "previous_contract_phone",
                "service_address",
                "service_city",
                "service_zip",
                "service_subdivision",
                "service_subdivision_code",
                "shipment_address",
                "shipment_city",
                "shipment_zip",
                "shipment_subdivision",
                "notes",
                "adsl_coverage",
                "mm_fiber_coverage",
                "asociatel_fiber_coverage",
                "orange_fiber_coverage",
                "vdf_fiber_coverage",
                "type",
                "product",
                "previous_internal_provider",
                "technology",
                "sales_team",
                "confirmed_documentation",
            ]
        )

        mock_otrs_client = Mock(spec=["create_otrs_process_ticket"])
        mock_otrs_client.create_otrs_process_ticket.return_value.id = 123
        mock_otrs_client.create_otrs_process_ticket.return_value.number = "#123"
        MockOTRSClient.return_value = mock_otrs_client

        ticket = Router4GTicket(service_data, customer_data, self.responsible_data)
        ticket.create()

        mock_otrs_client.create_otrs_process_ticket.assert_called_once()

        self.assertEqual(ticket.id, 123)
        self.assertEqual(ticket.number, "#123")
