# Copyright (C) 2019  Renato Lima - Akretion <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, models

from ..constants.fiscal import (
    DOCUMENT_ISSUER_COMPANY,
)


class FiscalDocumentMixinMethods(models.AbstractModel):
    """
    Provides the method implementations for l10n_br_fiscal.document.mixin.

    These methods are extracted into this separate mixin due to the way
    l10n_br_fiscal.document.line is incorporated into account.move
    by the l10n_br_account module (decorator pattern).

    Specifically:
    - In l10n_br_account, fields from l10n_br_fiscal.document
      are added to account.move using Odoo's `_inherits` (composition)
      mechanism.
    - The methods in *this* mixin, however, are intended to be inherited
      using the standard `_inherit` mechanism.

    This separation is crucial because `_inherits` handles field composition
    but does not inherit methods. Thus, `_inherit` is used to bring in
    these methods. If these methods were defined in the same class as the
    fields of l10n_br_fiscal.document.mixin (which are subject to
    `_inherits`), and account.move.line also used `_inherit` on that
    single class, the fields would be duplicated.
    """

    _name = "l10n_br_fiscal.document.mixin.methods"
    _description = "Fiscal Document Mixin Methods"

    def _prepare_br_fiscal_dict(self, default=False):
        self.ensure_one()
        fields = self.env["l10n_br_fiscal.document.mixin"]._fields.keys()

        # we now read the record fiscal fields except the m2m tax:
        vals = self._convert_to_write(self.read(fields)[0])

        # remove id field to avoid conflicts
        vals.pop("id", None)

        if default:  # in case you want to use new rather than write later
            return {f"default_{k}": vals[k] for k in vals.keys()}
        return vals

    @api.onchange("document_type_id")
    def _onchange_document_type_id(self):
        if self.document_type_id and self.issuer == DOCUMENT_ISSUER_COMPANY:
            self.document_serie_id = self.document_type_id.get_document_serie(
                self.company_id, self.fiscal_operation_id
            )

    @api.depends("fiscal_operation_id")
    def _compute_document_type_id(self):
        for doc in self.filtered(lambda doc: doc.fiscal_operation_id):
            if doc.issuer == DOCUMENT_ISSUER_COMPANY and not doc.document_type_id:
                doc.document_type_id = doc.company_id.document_type_id

    def _get_amount_lines(self):
        """Get object lines instances used to compute fiscal fields"""
        return self.mapped(self._get_fiscal_lines_field_name())

    def _get_product_amount_lines(self):
        fiscal_line_ids = self._get_amount_lines()
        return fiscal_line_ids.filtered(lambda line: line.product_id.type != "service")

    @api.model
    def _get_amount_fields(self):
        """Get all fields with 'amount_' prefix"""
        fields = self.env["l10n_br_fiscal.document.mixin"]._fields.keys()
        prefixes = ("amount_", "fiscal_amount_")
        amount_fields = [f for f in fields if f.startswith(prefixes)]
        return amount_fields

    @api.depends("document_serie_id", "issuer")
    def _compute_document_serie(self):
        for doc in self:
            if doc.document_serie_id and doc.issuer == DOCUMENT_ISSUER_COMPANY:
                doc.document_serie = doc.document_serie_id.code
            elif doc.document_serie is None:
                doc.document_serie = False

    @api.depends("document_type_id", "issuer")
    def _compute_document_serie_id(self):
        for doc in self:
            if (
                not doc.document_serie_id
                and doc.document_type_id
                and doc.issuer == DOCUMENT_ISSUER_COMPANY
            ):
                doc.document_serie_id = doc.document_type_id.get_document_serie(
                    doc.company_id, doc.fiscal_operation_id
                )
            elif doc.document_serie_id is None:
                doc.document_serie_id = False

    @api.model
    def _get_fiscal_lines_field_name(self):
        return "fiscal_line_ids"

    def _get_fiscal_amount_field_dependencies(self):
        """
        Dynamically get the list of field dependencies.
        """
        if self._abstract:
            return []
        o2m_field_name = self._get_fiscal_lines_field_name()
        target_fields = []
        for field in self._get_amount_fields():
            if (
                field.replace("amount_", "")
                in getattr(self, o2m_field_name)._fields.keys()
            ):
                target_fields.append(field.replace("amount_", ""))

        return [o2m_field_name] + [
            f"{o2m_field_name}.{target_field}" for target_field in target_fields
        ]

    @api.depends(lambda self: self._get_fiscal_amount_field_dependencies())
    def _compute_fiscal_amount(self):
        """
        Compute and sum various fiscal amounts from the document lines.

        This method iterates over fields prefixed with 'amount_' (as determined
        by `_get_amount_fields`) and sums corresponding values from the lines
        retrieved by `_get_amount_lines`.

        It handles cases where delivery costs (freight, insurance, other) are
        defined at the document total level rather than per line.
        """

        fields = self._get_amount_fields()
        for doc in self.filtered(lambda m: m.fiscal_operation_id):
            values = {key: 0.0 for key in fields}
            for line in doc._get_amount_lines():
                for field in fields:
                    if field in line._fields.keys():
                        values[field] += line[field]
                    if field.replace("amount_", "") in line._fields.keys():
                        # FIXME this field creates an error in invoice form
                        if field == "amount_financial_discount_value":
                            values["amount_financial_discount_value"] += (
                                0  # line.financial_discount_value
                            )
                        else:
                            values[field] += line[field.replace("amount_", "")]

            # Valores definidos pelo Total e não pela Linha
            if (
                doc.company_id.delivery_costs == "total"
                or doc.force_compute_delivery_costs_by_total
            ):
                values["amount_freight_value"] = doc.amount_freight_value
                values["amount_insurance_value"] = doc.amount_insurance_value
                values["amount_other_value"] = doc.amount_other_value

            doc.update(values)

    def _get_fiscal_partner(self):
        """
        Hook method to determine the fiscal partner for the document.

        This method is designed to be overridden in implementing models if the
        partner relevant for fiscal purposes (e.g., for tax calculations,
        final consumer status) is different from the main `partner_id`
        of the document record. For instance, an invoice might use a specific
        invoicing contact derived from the main partner.

        :return: A `res.partner` recordset representing the fiscal partner.
        """

        self.ensure_one()
        return self.partner_id

    @api.onchange("partner_id")
    def _onchange_partner_id_fiscal(self):
        partner = self._get_fiscal_partner()
        if partner:
            self.ind_final = partner.ind_final
            for line in self._get_amount_lines():
                # reload fiscal data, operation line, cfop, taxes, etc.
                line._onchange_fiscal_operation_id()

    @api.depends("fiscal_operation_id")
    def _compute_operation_name(self):
        for doc in self:
            if doc.fiscal_operation_id:
                doc.operation_name = doc.fiscal_operation_id.name
            else:
                doc.operation_name = False

    @api.depends("fiscal_operation_id")
    def _compute_comment_ids(self):
        for doc in self:
            if doc.fiscal_operation_id:
                doc.comment_ids = doc.fiscal_operation_id.comment_ids
            elif doc.comment_ids is None:
                doc.comment_ids = []

    def _distribute_amount_to_lines(self, amount_field_name, line_field_name):
        for record in self:
            if not (
                record.delivery_costs == "total"
                or record.force_compute_delivery_costs_by_total
            ):
                continue
            lines = record._get_product_amount_lines()
            if not lines:
                continue
            amount_to_distribute = record[amount_field_name]
            total_gross = sum(lines.mapped("price_gross"))
            if total_gross > 0:
                distributed_amount = 0
                for line in lines[:-1]:
                    proportional_amount = record.currency_id.round(
                        amount_to_distribute * (line.price_gross / total_gross)
                    )
                    line[line_field_name] = proportional_amount
                    distributed_amount += proportional_amount
                lines[-1][line_field_name] = amount_to_distribute - distributed_amount
            else:
                lines.write({line_field_name: 0.0})
                if lines:
                    lines[0][line_field_name] = amount_to_distribute

    def _inverse_amount_freight(self):
        self._distribute_amount_to_lines("amount_freight_value", "freight_value")

    def _inverse_amount_insurance(self):
        self._distribute_amount_to_lines("amount_insurance_value", "insurance_value")

    def _inverse_amount_other(self):
        self._distribute_amount_to_lines("amount_other_value", "other_value")
