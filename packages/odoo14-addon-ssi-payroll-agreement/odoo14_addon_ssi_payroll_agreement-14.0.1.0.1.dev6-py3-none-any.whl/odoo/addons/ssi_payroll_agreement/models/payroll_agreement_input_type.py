# Copyright 2025 OpenSynergy Indonesia
# Copyright 2025 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl-3.0-standalone.html).

from odoo import models


class PayrollAgreementInputType(models.Model):
    _name = "payroll_agreement_input_type"
    _inherit = [
        "mixin.master_data",
    ]
    _description = "Payroll Agreement Input Type"
