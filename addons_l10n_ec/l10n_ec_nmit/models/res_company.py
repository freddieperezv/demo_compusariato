import base64, logging, subprocess, tempfile
from datetime import datetime
from OpenSSL import crypto
from odoo import _, api, fields, models, tools
from ..xades.xades import Xades
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)
KEY_TO_PEM_CMD = "openssl pkcs12 -nocerts -in %s -out %s -passin pass:%s -passout pass:%s"
STATES = {"unverified": [("readonly", False),]}


class Company(models.Model):
    _inherit = 'res.company'

    l10n_ec_accounting = fields.Selection(
        [("SI", "SI"),
         ("NO", "NO"),
         ], string="Obligado llevar Contabilidad",
        default="NO", readonly=False,
    )
    
    l10n_ec_certificate = fields.Binary('Certificate')
    l10n_ec_certificate_filename = fields.Char()
    l10n_ec_password = fields.Char('Certificate Password')
    l10n_ec_cert_private_key = fields.Text(
        string="Private Key",
        readonly=True
    )
    l10n_ec_cert_state = fields.Selection(
        [("unverified", "Unverified"),
         ("valid", "Valid"),
         ("expired", "Expired")
         ], string="Estado",
        default="unverified", readonly=True,
    )
    l10n_ec_cert_emision_date = fields.Date(
        string="Emission Date", readonly=True
    )
    l10n_ec_cert_expire_date = fields.Date(
        string="Expire date", readonly=True
    )
    l10n_ec_cert_subject_serial_number = fields.Char(
        string="Subject serial number", readonly=True
    )
    l10n_ec_cert_subject_common_name = fields.Char(
        string="Subject name", readonly=True
    )
    l10n_ec_cert_issuer_common_name = fields.Char(
        string="Issuer name", readonly=True
    )
    l10n_ec_cert_serial_number = fields.Char(
        string="Serial number", readonly=True
    )
    l10n_ec_cert_version = fields.Char(string="Version", readonly=True)
    taxpayer_number = fields.Char(string="Taxpayer Number")
    agent_number = fields.Char()
    micro_business = fields.Boolean()
    agent_ids = fields.One2many('account.agent', 'company_id')

    def convert_key_cer_to_pem(self):
        # TODO compute it from a python way
        with tempfile.NamedTemporaryFile(
                "wb", suffix=".key", prefix="edi.ec.tmp."
        ) as key_file, tempfile.NamedTemporaryFile(
            "rb", suffix=".key", prefix="edi.ec.tmp.") as keypem_file:
            key_file.write(self._get_filecontent)
            key_file.flush()
            subprocess.call((KEY_TO_PEM_CMD %(
                key_file.name, keypem_file.name,
                self.l10n_ec_password, self.l10n_ec_password
            )).split())
            key_pem = keypem_file.read().decode()
        return key_pem

    def _extract_x509(self, p12):
        is_digital_signature = False
        x509 = None
        x509_to_review = p12.get_certificate().to_cryptography()
        for exten in x509_to_review.extensions:
            if exten.oid._name == "keyUsage" and exten.value.digital_signature:
                is_digital_signature = True
                x509 = p12.get_certificate()
                break
        if not is_digital_signature:
            ca_certificates_list = p12.get_ca_certificates()
            if ca_certificates_list is not None:
                for x509_inst in ca_certificates_list:
                    x509_cryp = x509_inst.to_cryptography()
                    for exten in x509_cryp.extensions:
                        if exten.oid._name == "keyUsage" and exten.value.digital_signature:
                            x509 = x509_inst
        return x509

    @property
    def _get_filecontent(self):
        return base64.decodebytes(self.l10n_ec_certificate)

    def action_validate_and_load(self):
        """ Validates p12 file and Password """
        filecontent = self._get_filecontent
        try: p12 = crypto.load_pkcs12(filecontent, self.l10n_ec_password)
        except Exception as ex:
            _logger.warning(tools.ustr(ex))
            raise UserError(
                _(
                    "Error opening the signature, possibly the "
                    "signature key has been entered incorrectly"
                    " or the file is not supported. \n%s"
                ) % (tools.ustr(ex))
            )
        private_key = self.convert_key_cer_to_pem()
        start_index = private_key.find("Signing Key")
        if start_index >= 0: private_key = private_key[start_index:]
        start_index = private_key.find(
            "-----BEGIN ENCRYPTED PRIVATE KEY-----"
        )
        private_key = private_key[start_index:]
        cert = self._extract_x509(p12)
        issuer = cert.get_issuer()
        subject = cert.get_subject()
        self.write({
            "l10n_ec_cert_emision_date": datetime.strptime(
                cert.get_notBefore().decode("utf-8"), "%Y%m%d%H%M%SZ"),
            "l10n_ec_cert_expire_date": datetime.strptime(
                cert.get_notAfter().decode("utf-8"), "%Y%m%d%H%M%SZ"),
            "l10n_ec_cert_subject_common_name": subject.CN,
            "l10n_ec_cert_subject_serial_number": subject.serialNumber,
            "l10n_ec_cert_issuer_common_name": issuer.CN,
            "l10n_ec_cert_serial_number": cert.get_serial_number(),
            "l10n_ec_cert_version": cert.get_version(),
            "l10n_ec_cert_private_key": private_key,
            "l10n_ec_cert_state": "valid",
        })
        return True

    def action_sign(self, xml_string_data):
        xades = Xades()
        if not self.l10n_ec_certificate or not self.l10n_ec_password:
            raise UserError(_(
                "You must configure the data Localization"
            ))
        return xades.sign(
            xml_string_data,
            base64.decodebytes(self.l10n_ec_certificate), self.l10n_ec_password
        )

    @property
    def l10n_ec_env(self):
        IrDefault = self.env['ir.default'].sudo()
        return IrDefault.get(
            'res.config.settings', 'l10n_ec_env'
        ) or '1'
