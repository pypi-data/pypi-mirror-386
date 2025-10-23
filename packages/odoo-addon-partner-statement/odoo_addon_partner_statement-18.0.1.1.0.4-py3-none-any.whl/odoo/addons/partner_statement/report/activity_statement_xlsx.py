# Author: Christopher Ormaza
# Copyright 2021 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, models

from odoo.addons.report_xlsx_helper.report.report_xlsx_format import FORMATS


def copy_format(book, fmt):
    properties = [f[4:] for f in dir(fmt) if f[0:4] == "set_"]
    dft_fmt = book.add_format()
    return book.add_format(
        {
            k: v
            for k, v in fmt.__dict__.items()
            if k in properties and dft_fmt.__dict__[k] != v
        }
    )


class ActivityStatementXslx(models.AbstractModel):
    _name = "report.p_s.report_activity_statement_xlsx"
    _description = "Activity Statement XLSL Report"
    _inherit = "report.report_xlsx.abstract"

    def _get_report_name(self, report, data=False):
        company_id = data.get("company_id", False)
        report_name = _("Activity Statement")
        if company_id:
            company = self.env["res.company"].browse(company_id)
            suffix = f" - {company.name} - {company.currency_id.name}"
            report_name = report_name + suffix
        return report_name

    def _get_currency_header_row_data(self, partner, currency, data):
        return (
            [
                {
                    "col_pos": col_pos,
                    "sheet_func": "write",
                    "args": args,
                }
                for col_pos, args in enumerate(
                    [
                        (
                            _("Reference Number"),
                            FORMATS["format_theader_yellow_center"],
                        ),
                        (_("Date"), FORMATS["format_theader_yellow_center"]),
                    ]
                )
            ]
            + [
                {
                    "col_pos": 2,
                    "sheet_func": "merge_range",
                    "span": 1,
                    "args": (_("Description"), FORMATS["format_theader_yellow_center"]),
                },
            ]
            + [
                {
                    "col_pos": col_pos,
                    "sheet_func": "write",
                    "args": args,
                }
                for col_pos, args in enumerate(
                    [
                        (_("Original Amount"), FORMATS["format_theader_yellow_center"]),
                        (_("Applied Amount"), FORMATS["format_theader_yellow_center"]),
                        (_("Open Amount"), FORMATS["format_theader_yellow_center"]),
                    ],
                    4,
                )
            ]
        )

    def _get_currency_subheader_row_data(self, partner, currency, data):
        partner_data = data.get("data", {}).get(partner.id, {})
        currency_data = partner_data.get("currencies", {}).get(currency.id)
        return [
            {
                "col_pos": 1,
                "sheet_func": "write",
                "args": (
                    partner_data.get("prior_day"),
                    FORMATS["format_tcell_date_left"],
                ),
            },
            {
                "col_pos": 2,
                "sheet_func": "merge_range",
                "span": 3,
                "args": (_("Balance Forward"), FORMATS["format_tcell_left"]),
            },
            {
                "col_pos": 6,
                "sheet_func": "write",
                "args": (
                    currency_data.get("balance_forward"),
                    FORMATS["current_money_format"],
                ),
            },
        ]

    def _get_currency_line_row_data(self, partner, currency, data, line):
        format_tcell_left = FORMATS["format_tcell_left"]
        format_tcell_date_left = FORMATS["format_tcell_date_left"]
        format_distributed = FORMATS["format_distributed"]
        current_money_format = FORMATS["current_money_format"]
        name_to_show = (
            line.get("name", "") == "/" or not line.get("name", "")
        ) and line.get("ref", "")
        if line.get("name", "") and line.get("name", "") != "/":
            if not line.get("ref", ""):
                name_to_show = line.get("name", "")
            else:
                if (line.get("name", "") in line.get("ref", "")) or (
                    line.get("name", "") == line.get("ref", "")
                ):
                    name_to_show = line.get("name", "")
                elif line.get("ref", "") not in line.get("name", ""):
                    name_to_show = line.get("ref", "")
        return (
            [
                {
                    "col_pos": col_pos,
                    "sheet_func": "write",
                    "args": args,
                }
                for col_pos, args in enumerate(
                    [
                        (line.get("move_id", ""), format_tcell_left),
                        (line.get("date", ""), format_tcell_date_left),
                    ]
                )
            ]
            + [
                {
                    "col_pos": 2,
                    "sheet_func": "merge_range",
                    "span": 1,
                    "args": (name_to_show, format_distributed),
                },
            ]
            + [
                {
                    "col_pos": col_pos,
                    "sheet_func": "write",
                    "args": args,
                }
                for col_pos, args in enumerate(
                    [
                        (line.get("amount", ""), current_money_format),
                        (line.get("applied_amount", ""), current_money_format),
                        (line.get("open_amount", ""), current_money_format),
                    ],
                    4,
                )
            ]
        )

    def _get_currency_footer_row_data(self, partner, currency, data):
        partner_data = data.get("data", {}).get(partner.id, {})
        currency_data = partner_data.get("currencies", {}).get(currency.id)
        return [
            {
                "col_pos": 1,
                "sheet_func": "write",
                "args": (partner_data.get("end"), FORMATS["format_tcell_date_left"]),
            },
            {
                "col_pos": 2,
                "sheet_func": "merge_range",
                "span": 3,
                "args": (_("Ending Balance"), FORMATS["format_tcell_left"]),
            },
            {
                "col_pos": 6,
                "sheet_func": "write",
                "args": (
                    currency_data.get("amount_due"),
                    FORMATS["current_money_format"],
                ),
            },
        ]

    def _write_row_data(self, sheet, row_pos, row_data):
        for cell_data in row_data:
            sheet_func_name = cell_data.get("sheet_func", "")
            sheet_func = getattr(sheet, sheet_func_name, None)
            if callable(sheet_func):
                col_pos = cell_data["col_pos"]
                args = cell_data["args"]
                span = cell_data.get("span")
                if span:
                    args = row_pos, col_pos + span, *args
                sheet_func(row_pos, col_pos, *args)

    def _write_currency_header(self, row_pos, sheet, partner, currency, data):
        row_data = self._get_currency_header_row_data(partner, currency, data)
        self._write_row_data(sheet, row_pos, row_data)
        return row_pos

    def _write_currency_subheader(self, row_pos, sheet, partner, currency, data):
        row_data = self._get_currency_subheader_row_data(partner, currency, data)
        self._write_row_data(sheet, row_pos, row_data)
        return row_pos

    def _write_currency_line(self, row_pos, sheet, partner, currency, data, line):
        row_data = self._get_currency_line_row_data(partner, currency, data, line)
        self._write_row_data(sheet, row_pos, row_data)
        return row_pos

    def _write_currency_footer(self, row_pos, sheet, partner, currency, data):
        row_data = self._get_currency_footer_row_data(partner, currency, data)
        self._write_row_data(sheet, row_pos, row_data)
        return row_pos

    def _write_currency_lines(self, row_pos, sheet, partner, currency, data):
        partner_data = data.get("data", {}).get(partner.id, {})
        currency_data = partner_data.get("currencies", {}).get(currency.id)
        account_type = data.get("account_type", False)
        row_pos += 2
        statement_header = data["get_title"](
            partner,
            is_detailed=False,
            account_type=account_type,
            starting_date=partner_data.get("start"),
            ending_date=partner_data.get("end"),
            currency=currency.display_name,
        )
        sheet.merge_range(
            row_pos, 0, row_pos, 6, statement_header, FORMATS["format_left_bold"]
        )
        row_pos += 1
        row_pos = self._write_currency_header(row_pos, sheet, partner, currency, data)
        row_pos += 1
        row_pos = self._write_currency_subheader(
            row_pos, sheet, partner, currency, data
        )
        for line in currency_data.get("lines"):
            row_pos += 1
            row_pos = self._write_currency_line(
                row_pos, sheet, partner, currency, data, line
            )
        row_pos += 1
        row_pos = self._write_currency_footer(row_pos, sheet, partner, currency, data)
        return row_pos

    def _write_currency_buckets(self, row_pos, sheet, partner, currency, data):
        report_model = self.env["report.partner_statement.activity_statement"]
        partner_data = data.get("data", {}).get(partner.id, {})
        currency_data = partner_data.get("currencies", {}).get(currency.id)
        if currency_data.get("buckets"):
            row_pos += 2
            buckets_header = _("Aging Report at %(end)s in %(currency)s") % {
                "end": partner_data.get("end"),
                "currency": currency.display_name,
            }
            sheet.merge_range(
                row_pos, 0, row_pos, 6, buckets_header, FORMATS["format_right_bold"]
            )
            buckets_data = currency_data.get("buckets")
            buckets_labels = report_model._get_bucket_labels(
                partner_data.get("end"), data.get("aging_type")
            )
            row_pos += 1
            for i in range(len(buckets_labels)):
                sheet.write(
                    row_pos,
                    i,
                    buckets_labels[i],
                    FORMATS["format_theader_yellow_center"],
                )
            row_pos += 1
            sheet.write(
                row_pos,
                0,
                buckets_data.get("current", 0.0),
                FORMATS["current_money_format"],
            )
            sheet.write(
                row_pos,
                1,
                buckets_data.get("b_1_30", 0.0),
                FORMATS["current_money_format"],
            )
            sheet.write(
                row_pos,
                2,
                buckets_data.get("b_30_60", 0.0),
                FORMATS["current_money_format"],
            )
            sheet.write(
                row_pos,
                3,
                buckets_data.get("b_60_90", 0.0),
                FORMATS["current_money_format"],
            )
            sheet.write(
                row_pos,
                4,
                buckets_data.get("b_90_120", 0.0),
                FORMATS["current_money_format"],
            )
            sheet.write(
                row_pos,
                5,
                buckets_data.get("b_over_120", 0.0),
                FORMATS["current_money_format"],
            )
            sheet.write(
                row_pos,
                6,
                buckets_data.get("balance", 0.0),
                FORMATS["current_money_format"],
            )
        return row_pos

    def _size_columns(self, sheet, data):
        for i in range(7):
            sheet.set_column(0, i, 20)

    def generate_xlsx_report(self, workbook, data, objects):
        lang = objects.lang or self.env.user.partner_id.lang
        self = self.with_context(lang=lang)
        report_model = self.env["report.partner_statement.activity_statement"]
        self._define_formats(workbook)
        FORMATS["format_distributed"] = workbook.add_format({"align": "vdistributed"})
        company_id = data.get("company_id", False)
        if company_id:
            company = self.env["res.company"].browse(company_id)
        else:
            company = self.env.user.company_id
        data.update(report_model._get_report_values(data.get("partner_ids"), data))
        partners = self.env["res.partner"].browse(data.get("partner_ids"))
        sheet = workbook.add_worksheet(_("Activity Statement"))
        sheet.set_landscape()
        row_pos = 0
        sheet.merge_range(
            row_pos,
            0,
            row_pos,
            6,
            _("Statement of Account from %s") % (company.display_name,),
            FORMATS["format_ws_title"],
        )
        row_pos += 1
        sheet.write(row_pos, 1, _("Date:"), FORMATS["format_theader_yellow_right"])
        sheet.write(
            row_pos,
            2,
            data.get("data", {}).get(partners.ids[0], {}).get("today"),
            FORMATS["format_date_left"],
        )
        self._size_columns(sheet, data)
        for partner in partners:
            invoice_address = data.get(
                "get_inv_addr", lambda x: self.env["res.partner"]
            )(partner)
            row_pos += 3
            sheet.write(
                row_pos, 1, _("Statement to:"), FORMATS["format_theader_yellow_right"]
            )
            sheet.merge_range(
                row_pos,
                2,
                row_pos,
                3,
                invoice_address.display_name,
                FORMATS["format_left"],
            )
            if invoice_address.vat:
                sheet.write(
                    row_pos,
                    4,
                    _("VAT:"),
                    FORMATS["format_theader_yellow_right"],
                )
                sheet.write(
                    row_pos,
                    5,
                    invoice_address.vat,
                    FORMATS["format_left"],
                )
            row_pos += 1
            sheet.write(
                row_pos, 1, _("Statement from:"), FORMATS["format_theader_yellow_right"]
            )
            sheet.merge_range(
                row_pos,
                2,
                row_pos,
                3,
                company.partner_id.display_name,
                FORMATS["format_left"],
            )
            if company.vat:
                sheet.write(
                    row_pos,
                    4,
                    _("VAT:"),
                    FORMATS["format_theader_yellow_right"],
                )
                sheet.write(
                    row_pos,
                    5,
                    company.vat,
                    FORMATS["format_left"],
                )
            partner_data = data.get("data", {}).get(partner.id)
            currencies = partner_data.get("currencies", {}).keys()
            if currencies:
                row_pos += 1
            for currency_id in currencies:
                currency = self.env["res.currency"].browse(currency_id)
                if currency.position == "after":
                    money_string = (
                        "#,##0.%s " % ("0" * currency.decimal_places)
                        + f"[${currency.symbol}]"
                    )
                elif currency.position == "before":
                    money_string = f"[${currency.symbol}]" + " #,##0.%s" % (
                        "0" * currency.decimal_places
                    )
                FORMATS["current_money_format"] = workbook.add_format(
                    {"align": "right", "num_format": money_string}
                )
                row_pos = self._write_currency_lines(
                    row_pos, sheet, partner, currency, data
                )
                row_pos = self._write_currency_buckets(
                    row_pos, sheet, partner, currency, data
                )
