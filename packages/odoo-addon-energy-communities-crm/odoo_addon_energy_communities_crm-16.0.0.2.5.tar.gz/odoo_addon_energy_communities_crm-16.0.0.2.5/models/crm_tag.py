from odoo import _, api, fields, models


class Tag(models.Model):
    _name = "crm.tag"
    _inherit = ["crm.tag", "user.currentcompany.mixin"]

    tag_ext_id = fields.Char("ID Ext tag", compute="compute_ext_id_tag")
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
    )

    _sql_constraints = [
        ("name_uniq", "unique(name, company_id)", "Tag must be unique per company!"),
    ]

    def compute_ext_id_tag(self):
        for record in self:
            res = record.get_external_id()
            record.tag_ext_id = ""
            if res.get(record.id):
                record.tag_ext_id = res.get(record.id)
