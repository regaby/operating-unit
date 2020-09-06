# © 2019 Eficent Business and IT Consulting Services S.L.
# - Jordi Ballester Alomar
# © 2019 Serpent Consulting Services Pvt. Ltd. - Sudhir Arya
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PosOrder(models.Model):
    _inherit = 'pos.order'

    operating_unit_id = fields.Many2one(
        comodel_name='operating.unit',
        string='Operating Unit',
        related='config_id.operating_unit_id',
    )

    crm_team_id = fields.Many2one(
        comodel_name='crm.team',
        related='config_id.crm_team_id',
        string="Sales Team",
        )

    def _create_invoice(self):
        self.ensure_one()
        Invoice = self.env['account.invoice']
        # Force company for all SUPERUSER_ID action
        local_context = dict(self.env.context, force_company=self.company_id.id, company_id=self.company_id.id)
        if self.invoice_id:
            return self.invoice_id

        if not self.partner_id:
            raise UserError(_('Please provide a partner for the sale.'))

        invoice = Invoice.new(self._prepare_invoice())
        invoice._onchange_partner_id()
        invoice.fiscal_position_id = self.fiscal_position_id

        inv = invoice._convert_to_write({name: invoice[name] for name in invoice._cache})
        # Tuve que comentar el sudo del create porque chocaba con un metodo check al crear la factura
        # _check_company_operating_unit: que verficaba el operating unit del usuario y al ser sudo tomaba el admin
        # new_invoice = Invoice.with_context(local_context).sudo().create(inv)
        new_invoice = Invoice.with_context(local_context).create(inv)
        message = _("This invoice has been created from the point of sale session: <a href=# data-oe-model=pos.order data-oe-id=%d>%s</a>") % (self.id, self.name)
        new_invoice.message_post(body=message)
        self.write({'invoice_id': new_invoice.id, 'state': 'invoiced'})

        for line in self.lines:
            self.with_context(local_context)._action_create_invoice_line(line, new_invoice.id)

        new_invoice.with_context(local_context).compute_taxes()
        self.sudo().write({'state': 'invoiced'})
        return new_invoice


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    operating_unit_id = fields.Many2one(related='order_id.operating_unit_id',
                                        string='Operating Unit')
