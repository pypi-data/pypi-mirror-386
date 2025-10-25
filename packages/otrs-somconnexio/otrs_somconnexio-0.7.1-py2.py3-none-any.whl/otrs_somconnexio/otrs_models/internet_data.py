class InternetData(object):
    def __init__(
        self,
        order_id,
        contact_phone,
        phone_number,
        iban,
        email,
        service_address,
        service_city,
        service_zip,
        service_subdivision,
        service_subdivision_code,
        shipment_address,
        shipment_city,
        shipment_zip,
        shipment_subdivision,
        previous_service,
        previous_provider,
        previous_internal_provider,
        previous_owner_vat,
        previous_owner_name,
        previous_owner_surname,
        notes,
        activation_notes,
        product,
        adsl_coverage,
        mm_fiber_coverage,
        asociatel_fiber_coverage,
        vdf_fiber_coverage,
        orange_fiber_coverage,
        type,
        technology,
        sales_team,
        previous_contract_address="",
        previous_contract_phone="",
        mobile_pack_contracts="",
        confirmed_documentation=False,
    ):
        # Common all the Tickets
        self.order_id = order_id
        self.phone_number = phone_number
        self.iban = iban
        self.email = email
        self.previous_provider = previous_provider
        self.previous_internal_provider = previous_internal_provider
        self.previous_owner_vat = previous_owner_vat
        self.previous_owner_name = previous_owner_name
        self.previous_owner_surname = previous_owner_surname
        self.product = product
        self.technology = technology
        self.contact_phone = contact_phone
        self.sales_team = sales_team
        self.notes = notes
        self.activation_notes = activation_notes
        self.confirmed_documentation = confirmed_documentation

        # Common Internet the Tickets
        self.service_address = service_address
        self.service_city = service_city
        self.service_zip = service_zip
        self.service_subdivision = service_subdivision
        self.service_subdivision_code = service_subdivision_code
        self.shipment_address = shipment_address
        self.shipment_city = shipment_city
        self.shipment_zip = shipment_zip
        self.shipment_subdivision = shipment_subdivision
        self.previous_service = previous_service
        self.adsl_coverage = adsl_coverage
        self.mm_fiber_coverage = mm_fiber_coverage
        self.asociatel_fiber_coverage = asociatel_fiber_coverage
        self.vdf_fiber_coverage = vdf_fiber_coverage
        self.orange_fiber_coverage = orange_fiber_coverage
        self.type = type
        self.previous_contract_address = previous_contract_address
        self.previous_contract_phone = previous_contract_phone

        # Pack Tickets
        self.mobile_pack_contracts = mobile_pack_contracts
