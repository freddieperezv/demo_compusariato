import os
from io import StringIO
import base64
import logging
from lxml import etree
from lxml.etree import fromstring, DocumentInvalid

try:
    from suds.client import Client
except ImportError:
    logging.getLogger('xades.sri').info('Instalar libreria suds-jurko')

from ..models import utils
from .xades import CheckDigit

SCHEMAS = {
    'out_invoice': 'schemas/factura.xsd',
    'out_refund': 'schemas/nota_credito.xsd',
    'withdrawing': 'schemas/retencion.xsd',
    'delivery': 'schemas/guia_remision.xsd',
    'out_debit': 'schemas/nota_debito.xsd',
    'liq_purchase': 'schemas/Liquidacion_Compra.xsd'
    #'in_refund': 'schemas/nota_debito.xsd'
}


class DocumentXML(object):
    _schema = False
    document = False

    @classmethod
    def __init__(self, document, type='out_invoice', env='1'):
        """
        document: XML representation
        type: determinate schema
        """
        self.SriService = SriService
        self.SriService.set_active_env(env)
        parser = etree.XMLParser(ns_clean=True, recover=True, encoding='utf-8')
        self.document = fromstring(document.encode(), parser=parser)
        self.type_document = type
        self._schema = SCHEMAS[self.type_document]
        self.signed_document = False
        self.logger = logging.getLogger('xades.sri')

    @classmethod
    def validate_xml(self):
        """
        Validar esquema XML
        """
        self.logger.info('Validacion de esquema')
        self.logger.debug(etree.tostring(self.document, pretty_print=True))
        file_path = os.path.join(os.path.dirname(__file__), self._schema)
        schema_file = open(file_path)
        xmlschema_doc = etree.parse(schema_file)
        xmlschema = etree.XMLSchema(xmlschema_doc)
        try:
            xmlschema.assertValid(self.document)
        except Exception as e:
            return e.args

    @classmethod
    def send_receipt(self, document):
        """
        Metodo que envia el XML al WS
        """
        self.logger.info('Enviando documento para recepcion SRI')
        buf = StringIO()
        buf.write(document.decode())
        buffer_xml = base64.encodebytes(buf.getvalue().encode())
        errores = []
        try:
            client = Client(self.SriService.get_active_ws()[0], timeout=900)
            self.logger.info(self.SriService.get_active_ws()[0])
            self.logger.debug(buffer_xml)
            result = client.service.validarComprobante(buffer_xml.decode())
            self.logger.debug('Estado de respuesta documento: %s' % result)
            if result.estado == 'RECIBIDA':
                return []
            validate_attr = lambda m, attr: hasattr(m, attr) and m[attr] or ''
            for comp in result.comprobantes['comprobante']:
                for m in comp['mensajes']['mensaje']:
                    errores.append(f"""
                    <div>identificador: {validate_attr(m, 'identificador')} </div>
                    <div>informacionAdicional: {validate_attr(m, 'informacionAdicional')}</div>
                    <div>mensaje: {validate_attr(m, 'mensaje')}</div>
                    <div>tipo: {validate_attr(m, 'tipo')}</div>
                    """)
        except Exception as e:
            errores.append(f"""
            <div>identificador: undefined </div>
            <div>informacionAdicional: {e.args}</div>
            <div>mensaje: Error Indefinido</div>
            <div>tipo: Error</div>
            """)
        return errores

    @classmethod
    def get_auth(self, clave_acceso):
        client = Client(self.SriService.get_active_ws()[1])
        self.logger.info(self.SriService.get_active_ws()[1])
        return client.service.autorizacionComprobante(clave_acceso)

    def request_authorization(self, access_key):
        messages = []
        client = Client(self.SriService.get_active_ws()[1], timeout=900)
        self.logger.info(self.SriService.get_active_ws()[1])
        result = client.service.autorizacionComprobante(access_key)
        autorizacion = result.autorizaciones[0][0]
        for m in autorizacion.mensajes and autorizacion.mensajes[0] or []:
            self.logger.error('{0} {1} {2}'.format(
                m.identificador, m.mensaje, m.tipo, m.informacionAdicional)
            )
            messages.append(
                f"""
                <div>identificador: {m.identificador} </div>
                <div>informacionAdicional: {m.informacionAdicional}</div>
                <div>mensaje: {m.mensaje}</div>
                <div>tipo: {m.tipo}</div>
            """)
        return autorizacion, messages


class SriService(object):

    __AMBIENTE_PRUEBA = '1'
    __AMBIENTE_PROD = '2'
    __ACTIVE_ENV = False
    # revisar el utils
    __WS_TEST_RECEIV = 'https://celcer.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline?wsdl'  # noqa
    __WS_TEST_AUTH = 'https://celcer.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline?wsdl'  # noqa
    __WS_RECEIV = 'https://cel.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline?wsdl'  # noqa
    __WS_AUTH = 'https://cel.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline?wsdl'  # noqa

    __WS_TESTING = (__WS_TEST_RECEIV, __WS_TEST_AUTH)
    __WS_PROD = (__WS_RECEIV, __WS_AUTH)

    _WSDL = {
        __AMBIENTE_PRUEBA: __WS_TESTING,
        __AMBIENTE_PROD: __WS_PROD
    }
    __WS_ACTIVE = __WS_TESTING

    @classmethod
    def set_active_env(self, env_service):
        if env_service == self.__AMBIENTE_PRUEBA:
            self.__ACTIVE_ENV = self.__AMBIENTE_PRUEBA
        else:
            self.__ACTIVE_ENV = self.__AMBIENTE_PROD
        self.__WS_ACTIVE = self._WSDL[self.__ACTIVE_ENV]

    @classmethod
    def get_active_env(self):
        return self.__ACTIVE_ENV

    @classmethod
    def get_env_test(self):
        return self.__AMBIENTE_PRUEBA

    @classmethod
    def get_env_prod(self):
        return self.__AMBIENTE_PROD

    @classmethod
    def get_ws_test(self):
        return self.__WS_TEST_RECEIV, self.__WS_TEST_AUTH

    @classmethod
    def get_ws_prod(self):
        return self.__WS_RECEIV, self.__WS_AUTH

    @classmethod
    def get_active_ws(self):
        return self.__WS_ACTIVE

    @classmethod
    def create_access_key(self, values):
        """
        values: tuple ([], [])
        """
        env = self.get_active_env()
        dato = ''.join(values[0] + [env] + values[1])
        modulo = CheckDigit.compute_mod11(dato)
        access_key = ''.join([dato, str(modulo)])
        return access_key
