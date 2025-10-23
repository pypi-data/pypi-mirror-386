# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from lxml import etree

from odoo import _, api, models
from odoo.exceptions import AccessError
from odoo.tools import config


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def get_view(self, view_id=None, view_type="form", **options):
        result = super().get_view(view_id=view_id, view_type=view_type, **options)
        group = "sale_readonly_security.group_sale_readonly_security_admin"
        if view_type == "form" and not self.env.user.has_group(group):
            doc = etree.XML(result["arch"])
            for node in doc.xpath("//header"):
                node.set("invisible", "1")
            result["arch"] = etree.tostring(doc, encoding="unicode")
        return result

    @api.model
    def check_access(self, operation):
        """Simulate that you do not have ACLs so that the create, edit, and delete
        buttons are not displayed.
        """
        user = self.env.user
        group = "sale_readonly_security.group_sale_readonly_security_admin"
        test_condition = not config["test_enable"] or (
            config["test_enable"]
            and self.env.context.get("test_sale_readonly_security")
        )
        if (
            test_condition
            and operation != "read"
            and not self.env.su
            and not user.has_group(group)
        ):
            raise AccessError(
                _(
                    "Sorry, you are not allowed to create/edit sale orders. "
                    "Please contact your administrator for further information."
                )
            )

        return super().check_access(operation=operation)

    def _create_invoices(self, grouped=False, final=False, date=None):
        """Check if the user can do it, the method does not do a write() in sale.order,
        the computes set the corresponding values with compute methods.
        Apply the following logic: If user cannot modify a sale.order, cannot create
        an invoice.
        """
        self.env["sale.order"].check_access("write")
        return super()._create_invoices(grouped=grouped, final=final, date=date)
