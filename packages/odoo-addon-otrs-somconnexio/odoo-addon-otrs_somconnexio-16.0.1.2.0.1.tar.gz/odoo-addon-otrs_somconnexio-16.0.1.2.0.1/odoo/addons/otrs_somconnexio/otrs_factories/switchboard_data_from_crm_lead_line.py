from otrs_somconnexio.otrs_models.switchboard_data import SwitchboardData

from .base_data_from_crm_lead_line import BaseDataFromCRMLeadLine


class SwitchboardDataFromCRMLeadLine(BaseDataFromCRMLeadLine):
    DataModel = SwitchboardData

    def __init__(self, crm_lead_line):
        super().__init__(crm_lead_line)
        self.product = crm_lead_line.product_id
        self.isp_info = crm_lead_line.switchboard_isp_info

    def _get_data(self):
        sb_data = super()._get_data()
        sb_data.pop("previous_provider")
        sb_data.update(
            {
                "technology": "Switchboard",
                "icc": self.isp_info.icc,
                "has_sim": self.isp_info.has_sim,
                "landline": self.isp_info.phone_number,
                "mobile_phone_number": self.isp_info.mobile_phone_number,
                "extension": self.isp_info.extension,
                "agent_name": self.isp_info.agent_name,
                "agent_email": self.isp_info.agent_email,
                "previous_owner_vat": self.isp_info.previous_owner_vat_number or "",
                "previous_owner_name": self.isp_info.previous_owner_first_name or "",
                "previous_owner_surname": self.isp_info.previous_owner_name or "",
                "shipment_address": self.isp_info.delivery_full_street,
                "shipment_city": self.isp_info.delivery_city,
                "shipment_zip": self.isp_info.delivery_zip_code,
                "shipment_subdivision": self.isp_info.delivery_state_id.name,
                "additional_products": self._products_to_string(
                    self.isp_info.additional_product_ids
                ),
            }
        )
        return sb_data

    def _products_to_string(self, products):
        """
        Converts a recordset of products to a comma-separated string
        of their default_codes.
        """
        if not products.exists():
            return ""
        filtered_products = products.filtered(lambda p: p.exists() and p.default_code)
        return ",".join(product.default_code for product in filtered_products)
