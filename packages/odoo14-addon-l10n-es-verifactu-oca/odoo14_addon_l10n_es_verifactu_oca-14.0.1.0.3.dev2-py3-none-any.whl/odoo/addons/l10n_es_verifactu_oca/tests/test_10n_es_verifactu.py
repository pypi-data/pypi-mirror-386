# Copyright 2024 Aures TIC - Almudena de La Puente
# Copyright 2024 FactorLibre - Luis J. Salvatierra
# Copyright 2025 ForgeFlow S.L.
# Copyright 2025 Process Control - Jorge Luis López
# Copyright 2025 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
import json
from datetime import datetime
from hashlib import sha256
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlparse

from freezegun import freeze_time

from odoo.exceptions import UserError
from odoo.modules.module import get_resource_path

from .common import TestVerifactuCommon


class TestL10nEsAeatVerifactu(TestVerifactuCommon):
    def test_verifactu_hash_code(self):
        # based on AEAT VERI*FACTU documentation
        # https://www.agenciatributaria.es/static_files/AEAT_Desarrolladores/EEDD/IVA/VERI-FACTU/Veri-Factu_especificaciones_huella_hash_registros.pdf  # noqa: B950
        expected_hash = (
            "6FA5B3FA912C71B23C274952AA00E13A5F40F0CEE466640FFAAD041FA8B79BFF"
        )
        verifactu_hash_string = (
            "IDEmisorFactura=89890001K&"
            "NumSerieFactura=12345678/G33&"
            "FechaExpedicionFactura=01-01-2026&"
            "TipoFactura=F1&"
            "CuotaTotal=12.35&"
            "ImporteTotal=123.45&"
            "Huella=&"
            "FechaHoraHusoGenRegistro=2026-01-01T19:20:30+01:00"
        )
        sha_hash_code = sha256(verifactu_hash_string.encode("utf-8"))
        hash_code = sha_hash_code.hexdigest().upper()
        self.assertEqual(hash_code, expected_hash)

    def _create_and_test_invoice_verifactu_dict(
        self, name, inv_type, lines, extra_vals, module=None
    ):
        vals = []
        tax_names = []
        for line in lines:
            taxes = self.env["account.tax"]
            for tax in line[1]:
                if "." in tax:
                    xml_id = tax
                else:
                    xml_id = "l10n_es.{}_account_tax_template_{}".format(
                        self.company.id, tax
                    )
                taxes += self.env.ref(xml_id)
                tax_names.append(tax)
            vals.append({"price_unit": line[0], "taxes": taxes})
        return self._compare_verifactu_dict(
            "verifactu_{}_{}_dict.json".format(inv_type, "_".join(tax_names)),
            name,
            inv_type,
            vals,
            extra_vals=extra_vals,
            module=module,
        )

    def _compare_verifactu_dict(
        self, json_file, name, inv_type, lines, extra_vals=None, module=None
    ):
        """Helper method for creating an invoice according arguments, and
        comparing the expected verifactu dict with .
        """
        module = module or "l10n_es_verifactu_oca"
        vals = {
            "name": name,
            "partner_id": self.partner.id,
            "invoice_date": "2026-01-01",
            "move_type": inv_type,
            "invoice_line_ids": [],
        }
        for line in lines:
            vals["invoice_line_ids"].append(
                (
                    0,
                    0,
                    {
                        "product_id": self.product.id,
                        "account_id": self.account_expense.id,
                        "name": "Test line",
                        "price_unit": line["price_unit"],
                        "quantity": 1,
                        "tax_ids": [(6, 0, line["taxes"].ids)],
                    },
                )
            )
        if extra_vals:
            vals.update(extra_vals)
        invoice = self.env["account.move"].create(vals)
        self._activate_certificate(self.certificate_password)
        first_now = datetime(2026, 1, 1, 19, 20, 30)
        with patch(
            "odoo.addons.l10n_es_verifactu_oca.models.account_move.datetime"
        ) as mock_datetime:
            mock_datetime.now.return_value = first_now
            with freeze_time(first_now):
                invoice.action_post()
        result_dict = invoice._get_verifactu_invoice_dict()
        result_dict["RegistroAlta"].pop("FechaHoraHusoGenRegistro")
        result_dict["RegistroAlta"].pop("TipoHuella")
        result_dict["RegistroAlta"].pop("Huella")
        path = get_resource_path(module, "tests/json", json_file)
        if not path:
            raise Exception("Incorrect JSON file: %s" % json_file)
        with open(path, "r") as f:
            expected_dict = json.loads(f.read())
        self.assertEqual(expected_dict, result_dict)
        entry = invoice.last_verifactu_invoice_entry_id
        # Verify integration workflow
        self.assertTrue(entry, "Invoice should have verifactu entry")
        self.assertTrue(entry.aeat_json_data, "Should have JSON data")
        return invoice

    def test_get_verifactu_invoice_data(self):
        mapping = [
            (
                "TEST001",
                "out_invoice",
                [(100, ["s_iva10b"]), (200, ["s_iva21s"])],
                {
                    "fiscal_position_id": self.fp_nacional.id,
                    "verifactu_registration_key": self.fp_registration_key_01.id,
                    "verifactu_registration_date": "2026-01-01 19:20:30",
                },
            ),
            (
                "TEST002",
                "out_refund",
                [(100, ["s_iva10b"]), (100, ["s_iva10b"]), (200, ["s_iva21s"])],
                {
                    "fiscal_position_id": self.fp_nacional.id,
                    "verifactu_registration_key": self.fp_registration_key_01.id,
                    "verifactu_registration_date": "2026-01-01 19:20:30",
                },
            ),
            (
                "TEST003",
                "out_invoice",
                [(200, ["s_iva21s", "s_req52"])],
                {
                    "fiscal_position_id": self.fp_recargo.id,
                    "verifactu_registration_key": self.fp_registration_key_01.id,
                    "verifactu_registration_date": "2026-01-01 19:20:30",
                },
            ),
        ]
        for name, inv_type, lines, extra_vals in mapping:
            self._create_and_test_invoice_verifactu_dict(
                name, inv_type, lines, extra_vals
            )
        return

    def test_verifactu_start_date(self):
        self.company.verifactu_start_date = "2018-01-01"
        invoice1 = self.invoice.copy({"invoice_date": "2019-01-01"})
        self.assertTrue(invoice1.verifactu_enabled)
        invoice2 = self.invoice.copy({"invoice_date": "2017-01-01"})
        invoice2.invoice_date = "2017-01-01"
        self.assertFalse(invoice2.verifactu_enabled)
        self.company.verifactu_start_date = False
        self.assertTrue(invoice2.verifactu_enabled)


class TestL10nEsAeatVerifactuQR(TestVerifactuCommon):
    def _get_required_qr_params(self):
        """Helper to generate the required QR code parameters."""
        return {
            "nif": self.invoice.company_id.partner_id._parse_aeat_vat_info()[2],
            "numserie": self.invoice.name,
            "fecha": self.invoice._get_verifactu_date(self.invoice.invoice_date),
            "importe": f"{self.invoice.amount_total:.2f}",  # noqa
        }

    def test_verifactu_qr_generation(self):
        """
        Test the generation of the QR code image for the invoice.
        """
        self._activate_certificate(self.certificate_password)
        self.invoice.action_post()
        qr_code = self.invoice.verifactu_qr
        self.assertTrue(qr_code, "QR code should be generated for the invoice.")
        self.assertIsInstance(qr_code, bytes, "QR code should be in bytes format.")

    def test_verifactu_qr_url_format(self):
        """
        Test the format of the generated QR URL to ensure it meets expected criteria.
        """
        self._activate_certificate(self.certificate_password)
        self.invoice.action_post()
        qr_url = self.invoice.verifactu_qr_url
        self.assertTrue(qr_url, "QR URL should be generated for the invoice.")
        test_url = self.env.ref(
            "l10n_es_aeat.aeat_tax_agency_spain"
        ).verifactu_qr_base_url_test_address
        self.assertTrue(test_url, "Test URL should not be empty.")
        parsed_url = urlparse(qr_url)
        actual_params = parse_qs(parsed_url.query)
        expected_params = self._get_required_qr_params()
        for key, expected_value in expected_params.items():
            self.assertIn(
                key, actual_params, f"QR URL should contain the parameter: {key}"
            )
            self.assertEqual(
                actual_params[key][0],
                str(expected_value),
                f"QR URL parameter '{key}' should have value '{expected_value}', "
                "got '{actual_params[key][0]}' instead.",
            )

    def test_verifactu_qr_code_generation_on_draft(self):
        """
        Ensure that the QR code is not generated for invoices in draft state.
        """
        qr_code = self.invoice.verifactu_qr
        self.assertFalse(qr_code, "QR code should not be generated for draft invoices.")

    def test_verifactu_qr_code_after_update(self):
        """
        Test that the QR code is regenerated if the invoice details are updated.
        """
        self._activate_certificate(self.certificate_password)
        self.invoice.action_post()
        original_qr_code = self.invoice.verifactu_qr
        with self.assertRaises(UserError):
            self.invoice.button_cancel()
            self.invoice.button_draft()
            self.invoice.write(
                {
                    "invoice_line_ids": [
                        (
                            0,
                            0,
                            {
                                "product_id": self.product.id,
                                "account_id": self.account_expense.id,
                                "name": "Updated line",
                                "price_unit": 200,
                                "quantity": 1,
                            },
                        )
                    ]
                }
            )
            self.invoice.action_post()
            self.invoice.invalidate_model(["verifactu_qr_url", "verifactu_qr"])
            updated_qr_code = self.invoice.verifactu_qr
            self.assertNotEqual(
                original_qr_code,
                updated_qr_code,
                "QR code should be regenerated after invoice update.",
            )

    def test_send_invoices_to_verifactu(self):
        self._activate_certificate(self.certificate_password)
        self.invoice.action_post()
        with patch(
            "odoo.addons.l10n_es_verifactu_oca.models."
            "verifactu_invoice_entry.VerifactuInvoiceEntry._connect_verifactu"
        ) as mock_connect:
            mock_service = MagicMock()
            module = "l10n_es_verifactu_oca"
            json_file = "verifactu_mocked_response_1.json"
            path = get_resource_path(module, "tests/json", json_file)
            if not path:
                raise Exception("Incorrect JSON file: %s" % json_file)
            with open(path, "r") as f:
                response_dict = json.loads(f.read())
            # Update the response to match the actual invoice name
            response_dict["RespuestaLinea"][0]["IDFactura"][
                "NumSerieFactura"
            ] = self.invoice.name
            mock_service.RegFactuSistemaFacturacion.return_value = response_dict
            mock_connect.return_value = mock_service
            # Execute the cron job to send the invoice to VERI*FACTU
            self.env["verifactu.invoice.entry"]._cron_send_documents_to_verifactu()
            self.assertEqual(
                self.invoice.aeat_state,
                "sent",
                "Invoice should be marked as sent after VERI*FACTU processing.",
            )
            self.assertEqual(
                self.invoice.verifactu_csv,
                "A-Y23JP3582934",
                "CSV should be generated correctly after sending to VERI*FACTU.",
            )


class TestVerifactuSendResponse(TestVerifactuCommon):
    def test_create_activity_on_exception(self):
        """
        Creates an activity whenever the connection with VERI*FACTU
        is not possible.
        """
        MailActivity = self.env["mail.activity"]
        ActivityType = self.env.ref(
            "l10n_es_verifactu_oca.mail_activity_data_exception"
        )
        # Send an invoice without a certificate
        self.invoice.action_post()
        self.env["verifactu.invoice.entry"]._cron_send_documents_to_verifactu()
        self.assertEqual(self.invoice.aeat_state, "not_sent")
        activity_1 = MailActivity.search(
            [
                ("activity_type_id", "=", ActivityType.id),
                ("res_model", "=", "verifactu.invoice.entry.response"),
            ]
        )
        self.assertTrue(activity_1, "An exception activity should have been created")
        self.invoice.resend_verifactu()
        self.env["verifactu.invoice.entry"]._cron_send_documents_to_verifactu()
        activity_2 = MailActivity.search(
            [
                ("activity_type_id", "=", ActivityType.id),
                ("res_model", "=", "verifactu.invoice.entry.response"),
            ]
        )
        self.assertEqual(
            len(activity_1),
            len(activity_2),
            "There should be only one exception activity created",
        )
        # Activate certificate and re-run the cron
        self._activate_certificate(self.certificate_password)
        self.env["verifactu.invoice.entry"]._cron_send_documents_to_verifactu()
        activity_done = (
            self.env["mail.activity"]
            .with_context(active_test=False)
            .search(
                [
                    ("activity_type_id", "=", ActivityType.id),
                    ("res_model", "=", "verifactu.invoice.entry.response"),
                ]
            )
        )
        # todo: fix this, it's not activity_done.has_recommended_activites,
        #  should check if it's not visible anymore to the user
        self.assertFalse(
            activity_done.has_recommended_activities,
            "The exception activity should not appear.",
        )

    def mock_verifactu_response(self, error_code, description):
        """Recreates a verifactu response"""
        return {
            "CSV": "dummy-csv",
            "RespuestaLinea": [
                {
                    "IDFactura": {
                        "NumSerieFactura": self.invoice.name,
                    },
                    "EstadoRegistro": "AceptadoConErrores",
                    "CodigoErrorRegistro": error_code,
                    "DescripcionErrorRegistro": description,
                }
            ],
        }

    @patch(
        "odoo.addons.l10n_es_verifactu_oca.models.verifactu_invoice_entry."
        "VerifactuInvoiceEntry._connect_verifactu"
    )
    def test_create_send_activity(self, mock_connect):
        """
        Create an activity whenever the response from VERI*FACTU indicates
        that incorrect invoices have been sent
        """
        MailActivity = self.env["mail.activity"]
        ActivityType = self.env.ref("mail.mail_activity_data_warning")
        mock_service = MagicMock()
        module = "l10n_es_verifactu_oca"
        json_file = "verifactu_mocked_response_2.json"
        path = get_resource_path(module, "tests/json", json_file)
        if not path:
            raise Exception("Incorrect JSON file: %s" % json_file)
        with open(path, "r") as f:
            response_dict = json.loads(f.read())
        # Update the response to match the actual invoice name
        response_dict["RespuestaLinea"][0]["IDFactura"][
            "NumSerieFactura"
        ] = self.invoice.name
        mock_service.RegFactuSistemaFacturacion.return_value = response_dict
        mock_connect.return_value = mock_service
        self.invoice.action_post()
        self.env["verifactu.invoice.entry"]._cron_send_documents_to_verifactu()
        activity = MailActivity.search(
            [
                ("activity_type_id", "=", ActivityType.id),
                ("res_model", "=", "verifactu.invoice.entry.response"),
                ("summary", "=", "Check incorrect invoices from VERI*FACTU"),
            ]
        )
        self.assertTrue(
            activity,
            "A warning activity should be created for 'AceptadoConErrores' response",
        )

    def test_aeat_mixin_helper_methods(self):
        """Test helper methods in aeat_mixin that need coverage"""
        # Test _change_date_format
        formatted_date = self.invoice._change_date_format("2024-03-15")
        self.assertEqual(formatted_date, "15-03-2024")

    def test_verifactu_configuration_checks(self):
        """Test VERI*FACTU configuration validation methods"""
        # Test without tax agency
        self.company.tax_agency_id = False
        with self.assertRaises(UserError) as cm:
            self.invoice._check_verifactu_configuration()
        self.assertIn("tax agency configured", str(cm.exception))

        # Restore tax agency for next test
        self.company.tax_agency_id = self.env.ref("l10n_es_aeat.aeat_tax_agency_spain")

        # Test without developer
        self.company.verifactu_developer_id = False
        with self.assertRaises(UserError) as cm:
            self.invoice._check_verifactu_configuration()
        self.assertIn("VERI*FACTU developer configured", str(cm.exception))

        # Restore developer for next test
        self.company.verifactu_developer_id = self.verifactu_developer

        # Test with non-Spanish country
        self.company.country_id = self.env.ref("base.us")
        with self.assertRaises(UserError) as cm:
            self.invoice._check_verifactu_configuration()
        self.assertIn("not registered in Spain", str(cm.exception))

    def test_verifactu_mixin_methods(self):
        """Test verifactu_mixin methods for better coverage"""
        # Test _get_verifactu_version
        version = self.invoice._get_verifactu_version()
        self.assertEqual(version, 1.0)

        # Test _compute_verifactu_refund_type
        self.invoice._compute_verifactu_refund_type()
        self.assertFalse(self.invoice.verifactu_refund_type)

        # Test _get_verifactu_accepted_tax_agencies
        agencies = self.invoice._get_verifactu_accepted_tax_agencies()
        self.assertIn("l10n_es_aeat.aeat_tax_agency_spain", agencies)
