# coding: utf-8
import unittest
from mock import Mock, patch

from otrs_somconnexio.otrs_models.fiber_ticket import FiberTicket
from otrs_somconnexio.otrs_models.configurations.provision.fiber_ticket import (
    FiberTicketConfiguration,
)


class FiberTicketTestCase(unittest.TestCase):
    def setUp(self):
        self.responsible_data = Mock(spec=["email"])

    @patch("otrs_somconnexio.otrs_models.provision_ticket.Ticket")
    def test_build_ticket(self, MockTicket):
        customer_data = Mock(spec=["id"])
        service_data = Mock(spec=["order_id", "technology"])

        expected_ticket_arguments = {
            "Title": "Ticket#{} - Només fibra".format(service_data.order_id),
            "Type": FiberTicketConfiguration.type,
            "QueueID": FiberTicketConfiguration.queue_id,
            "State": FiberTicketConfiguration.state,
            "SLA": FiberTicketConfiguration.SLA,
            "Service": FiberTicketConfiguration.service,
            "Priority": FiberTicketConfiguration.priority,
            "CustomerUser": customer_data.id,
            "CustomerID": customer_data.id,
            "Responsible": self.responsible_data.email,
        }

        FiberTicket(service_data, customer_data, self.responsible_data)._build_ticket()
        MockTicket.assert_called_with(expected_ticket_arguments)

    @patch("otrs_somconnexio.otrs_models.provision_ticket.Ticket")
    def test_build_ticket_mixed(self, MockTicket):
        customer_data = Mock(spec=["id"])
        service_data = Mock(spec=["order_id", "technology"])
        service_data.technology = "Mixta"
        expected_ticket_arguments = {
            "Title": "Ticket#{} - Fibra mixta".format(service_data.order_id),
            "Type": FiberTicketConfiguration.type,
            "QueueID": FiberTicketConfiguration.queue_id,
            "State": FiberTicketConfiguration.state,
            "SLA": FiberTicketConfiguration.SLA,
            "Service": FiberTicketConfiguration.service,
            "Priority": FiberTicketConfiguration.priority,
            "CustomerUser": customer_data.id,
            "CustomerID": customer_data.id,
            "Responsible": self.responsible_data.email,
        }

        FiberTicket(service_data, customer_data, self.responsible_data)._build_ticket()
        MockTicket.assert_called_with(expected_ticket_arguments)

    @patch("otrs_somconnexio.otrs_models.provision_ticket.ProvisionArticle")
    def test_build_article(self, MockInternetArticle):
        customer_data = Mock(spec=[])
        service_data = Mock(spec=["order_id", "notes", "technology"])

        mock_mobile_article = MockInternetArticle.return_value

        FiberTicket(service_data, customer_data, self.responsible_data)._build_article()

        MockInternetArticle.assert_called_with(
            service_data.technology, service_data.order_id, "fiber", service_data.notes
        )
        mock_mobile_article.call.assert_called_once()

    @patch("otrs_somconnexio.otrs_models.fiber_ticket.FiberDynamicFields")
    def test_build_dynamic_fields(self, MockFiberDynamicFields):
        customer_data = Mock(spec=[])
        service_data = Mock(spec=["order_id"])

        mock_fiber_dynamic_fields = MockFiberDynamicFields.return_value

        FiberTicket(
            service_data, customer_data, self.responsible_data
        )._build_dynamic_fields()

        MockFiberDynamicFields.assert_called_with(
            service_data,
            customer_data,
            FiberTicketConfiguration.process_id,
            FiberTicketConfiguration.activity_id,
        )
        mock_fiber_dynamic_fields.all.assert_called_once()

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
                "previous_contract_address",
                "previous_contract_phone",
                "previous_contract_pon",
                "previous_contract_fiber_speed",
                "iban",
                "email",
                "previous_service",
                "contact_phone",
                "phone_number",
                "keep_landline",
                "previous_provider",
                "previous_owner_vat",
                "previous_owner_name",
                "previous_owner_surname",
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
                "activation_notes",
                "adsl_coverage",
                "mm_fiber_coverage",
                "asociatel_fiber_coverage",
                "orange_fiber_coverage",
                "vdf_fiber_coverage",
                "type",
                "product",
                "previous_internal_provider",
                "mobile_pack_contracts",
                "all_grouped_SIMS_recieved",
                "has_grouped_mobile_with_previous_owner",
                "technology",
                "sales_team",
                "product_ba_mm",
                "confirmed_documentation",
            ]
        )

        mock_otrs_client = Mock(spec=["create_otrs_process_ticket"])
        mock_otrs_client.create_otrs_process_ticket.return_value.id = 123
        mock_otrs_client.create_otrs_process_ticket.return_value.number = "#123"
        MockOTRSClient.return_value = mock_otrs_client

        ticket = FiberTicket(service_data, customer_data, self.responsible_data)
        ticket.create()

        mock_otrs_client.create_otrs_process_ticket.assert_called_once()

        self.assertEqual(ticket.id, 123)
        self.assertEqual(ticket.number, "#123")
        self.assertEqual(ticket.otrs_configuration.type, "Petición")
        self.assertEqual(ticket.otrs_configuration.SLA, "No pendent resposta")
        self.assertEqual(
            ticket.otrs_configuration.service, "Banda Ancha::Fibra::Provisió Fibra"
        )
