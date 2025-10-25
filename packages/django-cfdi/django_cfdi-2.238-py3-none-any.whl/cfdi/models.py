import requests, json, subprocess
from django.db import models
from .settings import (
    CFDI_DB_TABLE, XML_DIR, PRODIGIA_AUTH, TMP_DIR,
)

from django.contrib.auth.models import User
from django.utils.functional import cached_property
from django.contrib.postgres.fields import ArrayField
from .functions import to_int, to_datetime
from django.db.models import JSONField
import datetime
import os
from django.conf import settings

PRODIGIA_PASS = PRODIGIA_AUTH["prod"]["password"]
try:
    with open("/tmp/prodigia", "r") as f:
        PRODIGIA_PASS = f.read().strip()
except:
    pass

class Cfdi(models.Model):

    TIPOS_RELACION = (
        ("01", "01 Nota de crédito de los documentos relacionados"),
        ("02", "02 Nota de débito de los documentos relacionados"),
        ("03", "03 Devolución de mercancía sobre facturas o traslados previos"),
        ("04", "04 Sustitución de los CFDI previos"),
        ("05", "05 Traslados de mercancias facturados previamente"),
        ("06", "06 Factura generada por los traslados previos"),
        ("07", "07 CFDI por aplicación de anticipo"),
        ("08", "08 Factura generada por pagos en parcialidades"),
        ("09", "09 Factura generada por pagos diferidos"),
    )
    
    cfdi_xml = models.TextField()
    cfdi_error = models.TextField()
    cfdi_qrcode = models.TextField()
    acuse_cancelacion = models.TextField()
    cfdi_uuid = models.CharField(max_length=255, blank=True)
    cfdi_fecha_timbrado = models.DateTimeField(null=True)
    cfdi_fecha_cancelacion_sat = models.DateTimeField(null=True)
    cfdi_sello_digital = models.TextField()
    cfdi_no_certificado_sat = models.TextField()
    cfdi_sello_sat = models.TextField()
    cadena_original_complemento = models.TextField()
    cfdi_status = models.TextField()
    inicio_conexion_pac = models.DateTimeField(null=True)
    fin_conexion_pac = models.DateTimeField(null=True)
    inicio_timbrado = models.DateTimeField(null=True)
    fin_timbrado = models.DateTimeField(null=True)
    folio = models.IntegerField(null=True)
    serie = models.CharField(max_length=10)
    tipo_comprobante = models.CharField(max_length=2)
    motivo_cancelacion_cfdi = models.CharField(max_length=2, null=True)
    tipo_relacion = models.CharField(max_length=2, choices=TIPOS_RELACION, null=True, blank=True)
    cfdis_relacionados = models.ManyToManyField(
        "self", 
        related_name='documentos_relacion', 
        symmetrical=False
    )
    extra = JSONField(null=True, default=dict)

    
    def get_extra(self):
        import json
        if not self.extra:
            return {}

        try:
            return json.loads(self.extra)
        except Exception as e:
            return {}

    def add_extra(self, **kwargs):
        extra = self.extra or {}
        extra.update(kwargs)
        self.extra = extra

    @cached_property
    def uuid_relacionado_cancelacion(self):
        extra = self.extra
        if extra and extra.get("uuid_cfdi_relacionado"):
            return extra["uuid_cfdi_relacionado"]

        r = self.documentos_relacion.first()
        if r:
            return r.cfdi_uuid


    def get_folio_serie(self):
        txt = ""
        if self.serie:
            txt += self.serie
        if self.folio:
            txt += str(self.folio)
        return txt

    @property
    def xml(self):
        return self.cfdi_xml

    def cancelar_cfdi(self, config, timbrado_prueba=None, v33=False):
        from .functions import obtener_cancelacion_cfdi_base
        from .classes import CFDI
        if not self.cfdi_uuid:
            raise ValueError("El recibo no tiene UUID.")


        try:
            uuid_relacionado = self.forzar_uuid_cancelacion
        except Exception:
            uuid_relacionado = None
            rel = self.documentos_relacion.filter(
                cfdi_uuid__gt=""
            ).first()
            if rel:
                uuid_relacionado = rel.cfdi_uuid


        cfdi = obtener_cancelacion_cfdi_base(
            config, 
            uuid=self.cfdi_uuid,
            xml=self.cfdi_xml,
            timbrado_prueba=timbrado_prueba, 
            motivo_cancelacion=self.motivo_cancelacion_cfdi,
            uuid_relacionado=uuid_relacionado,

        )

        cancelado, error_cancelacion = cfdi.cancelar_cfdi()
        if cancelado:
            self.cancelado = True
            self.acuse_cancelacion = cfdi.acuse_cancelacion
            self.save()

        return [cancelado, error_cancelacion]

    class Meta:
        db_table = CFDI_DB_TABLE


    def get_total_tiempo_timbrado(self):
        if self.inicio_conexion_pac and self.fin_conexion_pac and self.inicio_timbrado and self.fin_timbrado:
            dif_conexion = (self.fin_conexion_pac - self.inicio_conexion_pac)
            dif_timbrado = (self.fin_timbrado - self.inicio_timbrado)
            dif = dif_conexion + dif_timbrado
            return "%s.%06d" % (dif.seconds, dif.microseconds)

    def set_folio(self):
        if not self.folio:
            instance = self.__class__.objects.filter(
                tipo_comprobante=self.tipo_comprobante,
                serie=self.serie,
            ).order_by("-folio").first()
            
            if instance and not instance.folio:
                instance.folio = 0
            self.folio = (instance.folio + 1) if instance else 1

    def xml_name(self):
        if self.cfdi_uuid:
            return "%s.xml" % self.cfdi_uuid

        return "%s.xml" % (self.folio or self.id)

    def get_xml_binary_file(self):
        return {
            'name':"%s.xml" % (self.cfdi_uuid),
            'data':self.cfdi_xml.encode("utf-8"),
            'content_type':"application/xml",
        }

    def xml_path(self, clave):
        d = "%s/%s" % (XML_DIR, clave)
        if not os.path.exists(d):
            os.makedirs(d)

        return "%s/%s" % (d, self.xml_name())

    def crear_xml_timbrado(self, clave="dmspitic"):
        with open(self.xml_path(clave=clave), 'w', encoding="utf8") as f:
            f.write(self.cfdi_xml)
        

    def generar_xml(self, cfdi, dividendos=False):

        #Si ya trae algún error definido ya no continua
        if self.cfdi_status:
            self.save()
            return 

        self.tipo_comprobante = cfdi.TipoDeComprobante
        self.serie = cfdi.Serie
        if cfdi.Folio:
            self.folio = cfdi.Folio
        else:
            self.set_folio()
            cfdi.Folio = self.folio

        if dividendos:
            cfdi.generar_xml_retencion_dividendos()
        else:
            cfdi.generar_xml()
        error_sello = cfdi.generar_sello()
        if error_sello:
            self.cfdi_status = error_sello
            self.save()
            return 
        cfdi.sellar_xml()
        timbrado = cfdi.timbrar_xml()
        #Se Guardan los tiempos de timbrado
        self.inicio_conexion_pac = cfdi.inicio_conexion_pac
        self.fin_conexion_pac = cfdi.fin_conexion_pac
        self.inicio_timbrado = cfdi.inicio_timbrado
        self.fin_timbrado = cfdi.fin_timbrado

        if not timbrado:
            self.cfdi_status = cfdi.cfdi_status
            self.cfdi_xml = cfdi.xml
            self.save()
        else:
            self.cfdi_xml = cfdi.cfdi_xml
            self.cfdi_qrcode = cfdi.cfdi_qrcode
            self.cfdi_sello_digital = cfdi.cfdi_sello_digital
            self.cfdi_uuid = cfdi.cfdi_uuid
            self.cfdi_sello_sat = cfdi.cfdi_sello_sat
            self.cadena_original_complemento = cfdi.cadena_original_complemento
            self.cfdi_fecha_timbrado = cfdi.cfdi_fecha_timbrado
            self.cfdi_no_certificado_sat = cfdi.cfdi_no_certificado_sat
            self.save()




class DescargaCfdi(models.Model):
    WEBSERVICE = 1
    SCRAPER = 2

    ST_PENDIENTE_ENVIAR = 1
    ST_PENDIENTE_CONSULTAR = 2
    ST_PENDIENTE = 3
    ST_FINALIZADO = 4
    ST_ERROR = 5
    ST_CANCELADO = 6

    METODOS_DESCARGA = (
        (WEBSERVICE, "Web service"),
        (SCRAPER, "SAT Scraper"),
    )

    creado = models.DateTimeField(auto_now_add=True)
    usuario_creado = models.ForeignKey(
        User,
        null=True,
        blank=True,
        related_name="%(class)s_creados",
        on_delete=models.PROTECT,
    )

    modificado = models.DateTimeField(auto_now=True)
    rfc_emisor = models.TextField(default="")
    rfc_receptor = models.TextField(default="")
    rfc_solicitante = models.TextField()
    fecha_inicio = models.DateField()
    fecha_final = models.DateField()
    respuesta_solicitud = models.TextField()
    numero_solicitud = models.TextField()
    status = models.IntegerField(choices=(
        (ST_PENDIENTE_ENVIAR, "Pendiente de enviar"),
        (ST_PENDIENTE_CONSULTAR, "Pendiente de consultar"),
        (ST_PENDIENTE, "Sigue pendiente"),
        (ST_FINALIZADO, "Finalizado"),
        (ST_ERROR, "Error al consultar solicitud descarga"),
        (ST_CANCELADO, "Cancelado"),
    ), default=1)
    respuesta_consulta = models.TextField()
    paquetes = models.TextField()
    tipo_solicitud = models.CharField(max_length=255, default="CFDI")
    archivos = ArrayField(models.CharField(max_length=255), default=list)
    pac = models.IntegerField(
        choices=(
            (1, "Miguelito"), #SIN PAC, CON LIBRERÍA 'cfdiclient'
            (2, "Prodigia"),
        ), 
        default=2,
    )
    metodo_descarga = models.IntegerField(
        null=True, 
        choices=METODOS_DESCARGA
    )

    def get_status_badge_css(self):
        css_classes = "badge badge-"
        if self.status in [self.ST_PENDIENTE_ENVIAR, self.ST_PENDIENTE_CONSULTAR, self.ST_PENDIENTE]:
            css_classes += "warning" 

        if self.status == self.ST_FINALIZADO:
            css_classes += "success" 

        if self.status == self.ST_ERROR:
            css_classes += "danger" 

        if self.status == self.ST_CANCELADO:
            css_classes += "secondary" 

        return css_classes

    @property
    def habilitar_consulta_status_descarga(self):
        if self.metodo_descarga == self.WEBSERVICE:
            return bool(self.numero_solicitud) and self.status in [
                self.ST_PENDIENTE_CONSULTAR, 
                self.ST_PENDIENTE
            ]
        
        return bool(self.status == self.ST_PENDIENTE)

    def consultar_status_descarga_scraper(self, rfc):
        import requests

        api_url = getattr(settings, "SAT_SCRAPPER_API_URL", None)
        api_key = getattr(settings, "SAT_SCRAPPER_API_KEY", None)
        timeout = getattr(settings, "SAT_SCRAPPER_TIMEOUT")

        if not self.numero_solicitud:
            return False

        url = f"{api_url}/consultar_descarga_cfdi/{rfc}/{self.numero_solicitud}/"

        try:
            headers = {"Api-key": api_key}
            api_response = requests.get(
                url, 
                params={"tipo_solicitud": self.tipo_solicitud},
                headers=headers,
                timeout=timeout,
            )
            if api_response.ok:
                json_response = api_response.json()
                self.respuesta_solicitud = api_response.text

                if json_response.get("status") in ["failure", "error"]:
                    self.status = self.ST_ERROR

                if json_response.get("paquetes"):
                    self.status = self.ST_FINALIZADO
                    self.respuesta_consulta = api_response.text

        except requests.exceptions.ReadTimeout as e:
            self.status = self.ST_PENDIENTE
            self.respuesta_solicitud = str(e)

        except Exception as e:
            self.respuesta_solicitud = ""
            self.status = self.ST_ERROR
        
        self.save()
    
    def cancelar_descarga_cfdi_scraper(self):
        import requests

        api_url = getattr(settings, "SAT_SCRAPPER_API_URL", None)
        api_key = getattr(settings, "SAT_SCRAPPER_API_KEY", None)
        timeout = getattr(settings, "SAT_SCRAPPER_TIMEOUT")

        if not self.numero_solicitud:
            return False

        url = f"{api_url}/cancelar_descarga_cfdi/{self.numero_solicitud}/"

        try:
            headers = {"Api-key": api_key}
            api_response = requests.get(
                url, 
                headers=headers,
                timeout=timeout,
            )
            if api_response.ok:
                self.respuesta_solicitud = api_response.text
                self.respuesta_consulta = api_response.text
                self.status = self.ST_CANCELADO
                
        except Exception as e:
            print(e)

        self.save()


    def get_dict_respuesta_solicitud(self):
        try:
            return json.loads(self.respuesta_solicitud)
        except Exception as e:
            return {}

    def get_error_mensaje(self):
        if self.metodo_descarga == DescargaCfdi.SCRAPER:
            respuesta_dict = self.get_dict_respuesta_solicitud()
            if respuesta_dict:
                error = (respuesta_dict.get("error") or "").lower()
                mensaje_error = (respuesta_dict.get("error") or "").lower()

                if error:
                    if "límite de descargas" in mensaje_error:
                        return "Se llegó al límite de descargas diarias, solo es posible descargar 2,000 CFDI por día con la página del SAT"
                
                if respuesta_dict.get("resumen") and respuesta_dict.get("resumen").get("mensaje"):
                    mensaje_error = (respuesta_dict.get("resumen").get("mensaje") or "").lower()

                    if "rfc o contraseña son incorrectos" in mensaje_error:
                        return "RFC o clave CIEC son incorrectos"
                    
                    if "ERROR_NO_SLOT_AVAILABLE" in mensaje_error.upper():
                        return "El servicio anti-captcha no esta disponible, intente generar de nuevo esta solicitud."
                    
                    if "captcha no válido" in mensaje_error:
                        return "Captcha no válido, intente de nuevo"
                    
                    if "ciec incorrecta" in mensaje_error:
                        return "La clave CIEC es incorrecta, debe actualizarla en Configuración Fiscal"

                return mensaje_error or error
                    
        else:
            if "Certificado Revocado o Caduco" in self.respuesta_solicitud:
                return "Certificado Revocado o Caduco, corrobore que la FIEL cargado sea la última y esté vigente"

        return "Error al consultar solicitud descarga"

    def solicitar_descarga_masiva_scraper(self, rfc, ciec_password):
        from django.conf import settings
        import requests

        api_url = getattr(settings, "SAT_SCRAPPER_API_URL", None)
        api_key = getattr(settings, "SAT_SCRAPPER_API_KEY", None)
        timeout = getattr(settings, "SAT_SCRAPPER_TIMEOUT")

        if timeout is None:
            # connect , read timeouts
            timeout = (4, 10)

        if not api_url:
            self.status = self.ST_ERROR
            self.respuesta_solicitud = "No se especificó settings.SAT_SCRAPPER_URL"
            self.save()
            return False
        
        if not api_key:
            self.status = self.ST_ERROR
            self.respuesta_solicitud = "No se especificó settings.SAT_SCRAPPER_API_KEY"
            self.save()
            return False

        try:
            headers = {"Api-key": api_key}
            tipo_descarga = "recibidos"

            if self.rfc_emisor:
                tipo_descarga = "emitidos"

            data = {
                "ciec_pass": ciec_password,
                "fecha_desde": self.fecha_inicio.isoformat(),
                "fecha_hasta": self.fecha_final.isoformat(),
                "rfc": rfc,
                "tipo_descarga": tipo_descarga, 
                "tipo_solicitud": self.tipo_solicitud, 
            }

            api_response = requests.post(
                f"{api_url}/solicitar_descarga_masiva/", 
                data=data, 
                headers=headers,
                timeout=timeout,
            )

            self.respuesta_solicitud = api_response.text
            
            if api_response.ok:
                json_response = api_response.json()
                self.numero_solicitud = json_response.get("id")

        except Exception as e:
            self.status = self.ST_ERROR
            self.respuesta_solicitud = str(e)
        
        if self.numero_solicitud:
            self.status = self.ST_PENDIENTE
        
        self.save()
        return self


    @cached_property
    def fiel(self):
        from cfdiclient import Fiel
        from django.core.files.base import ContentFile
        import requests

        if getattr(self, "path_fiel_cer", None):
            cer_der = open(self.path_fiel_cer, 'rb').read()
            key_der = open(self.path_fiel_key, 'rb').read()
        else:
            resource = requests.get(self.url_fiel_cer, timeout=3)
            cer_der = ContentFile(resource.content).read()
            resource = requests.get(self.url_fiel_key, timeout=3)
            key_der = ContentFile(resource.content).read()


        fiel = Fiel(cer_der, key_der, self.password_fiel)
        return fiel

    @property
    def token(self):
        from cfdiclient import Autenticacion
        auth = Autenticacion(self.fiel)
        return auth.obtener_token()
    
    @property
    def solicitud_object(self):
        if isinstance(self.respuesta_solicitud, dict):
            return self.respuesta_solicitud

        if self.respuesta_solicitud:
            try:        
                respuesta_solicitud = json.loads(self.respuesta_solicitud)
                return respuesta_solicitud
            except Exception:
                return {}
        return {}


    @property
    def consulta_object(self):
        if isinstance(self.respuesta_consulta, dict):
            return self.respuesta_consulta

        if self.respuesta_consulta:
            try:        
                respuesta_consulta = json.loads(self.respuesta_consulta)
                return respuesta_consulta
            except Exception:
                return {}
        return {}

    @property
    def mensaje(self):
        if self.metodo_descarga == self.WEBSERVICE:
            if self.pac == 1:
                if self.consulta_object:
                    mensajes = {
                        "300": "Usuario no válido",
                        "301": "XML mal formado",
                        "302": "Sello mal formado",
                        "303": "Sello no corresponde con RfcSolicitante",
                        "304": "Certificado revocado o caduco",
                        "305": "Certificado inválido",
                        "5000": "Solicitud recibida con éxito",
                        "5001": "Tercero no autorizado",
                        "5002": "Se agotó las solicitudes de por vida: Máximo para solicitudes con los mismos parámetros",
                        "5004": "No se encontró la solicitud",
                        "5005": "Solicitud duplicada: Si existe una solicitud vigente con los mismos parámetros",
                        "5006": "Error interno en el proceso",
                        "404": "Error no controlado: Reintentar más tarde la petición"
                    }
                    return mensajes.get(self.consulta_object["codigo_estado_solicitud"])
                    
                elif self.solicitud_object:
                    return self.solicitud_object["mensaje"]

        if self.metodo_descarga == self.SCRAPER:
            import json
            try:
                respuesta = json.loads(self.respuesta_solicitud)
                return respuesta.get("message")
            except Exception as e:
                pass

        return ""

    def status_solicitud(self):
        if not self.consulta_object:
            return "Sin Status"

        status = {        
           0:"Token invalido.",
           1:"Aceptada",
           2:"En proceso",
           3:"Terminada",
           4:"Error",
           5:"Rechazada",
           6:"Vencida",
        }
        return status.get(to_int(self.consulta_object["estado_solicitud"]))

    def get_lista_paquetes(self):
        #urls_paquete = []        
        jsondata = {}
        if self.metodo_descarga == self.SCRAPER:
            if self.respuesta_consulta:
                try:
                    jsondata = json.loads(self.respuesta_consulta)
                except json.JSONDecodeError:
                    pass
        else:
            if self.pac == 1:
                return self.archivos

            if not self.respuesta_solicitud:
                return []
            try:
                jsondata = json.loads(self.respuesta_consulta.split("|")[-1])
            except json.JSONDecodeError:
                return []

        return jsondata.get("paquetes", [])
    
        
    
    #cfdi_ultima_consulta = models.DateTimeField(null=True)

    def solicitar_descarga(self, rfc=None, ciec_password=None):
        if self.metodo_descarga == self.SCRAPER:
            if not rfc:
                self.status = self.ST_ERROR
                self.respuesta_solicitud = "No se especificó  RFC"
                self.save()
                return self
            
            if not ciec_password:
                self.status = self.ST_ERROR
                self.respuesta_solicitud = "No se especificó la contraseña CIEC"
                self.save()
                return self

            return self.solicitar_descarga_masiva_scraper(
                rfc=rfc, 
                ciec_password=ciec_password
            )

        from cfdiclient import SolicitaDescargaEmitidos, SolicitaDescargaRecibidos

        assert self.fecha_inicio
        assert self.fecha_final
        assert self.pfx_fiel
        assert self.password_fiel
        assert not self.numero_solicitud


        if self.pac == 2:
            self.solicitar_descarga_prodigia()
            return

        timeout = getattr(settings, "CFDI_SOLICITAR_DESCARGA_TIMEOUT", 30)

        if self.rfc_emisor:
            descarga = SolicitaDescargaEmitidos(self.fiel, timeout=timeout)
            solicitud = descarga.solicitar_descarga(
                self.token, 
                self.rfc_solicitante, 
                self.fecha_inicio, 
                self.fecha_final, 
                rfc_emisor=self.rfc_emisor,
                tipo_solicitud=self.tipo_solicitud,
            )
        else:
            descarga = SolicitaDescargaRecibidos(self.fiel, timeout=timeout)
            solicitud = descarga.solicitar_descarga(
                self.token, 
                self.rfc_solicitante, 
                self.fecha_inicio, 
                self.fecha_final, 
                rfc_receptor=self.rfc_receptor,
                tipo_solicitud=self.tipo_solicitud,
                estado_comprobante="Vigente",
            )

        self.respuesta_solicitud = solicitud

        if solicitud and solicitud.get("cod_estatus") == "5000":
            self.status = self.ST_PENDIENTE_CONSULTAR
            self.numero_solicitud = self.solicitud_object["id_solicitud"]
        else:
            #error
            self.status = self.ST_ERROR
        
        self.save()

    def solicitar_status_descarga(self, rfc=None):
        from cfdiclient import VerificaSolicitudDescarga

        if self.metodo_descarga == self.WEBSERVICE:
            if not self.numero_solicitud:
                raise ValueError("No hay número de solicitud")

            status = to_int(self.consulta_object.get("estado_solicitud"))
            """
            SI EL ESTADO QUE REGRESÓ  1 Y 2,
            ACEPTADA O EN PROCESO, SE SOLICITA EL STATUS DE LA DESCARGA
            """

            if self.consulta_object.get("codigo_estado_solicitud") == "5004":
                self.status = self.ST_FINALIZADO
                self.save()
                return 
                
            if status in [1,2] or self.status in [1,2]:
                if self.pac == 2:
                    self.solicitar_status_descarga_prodigia()

                timeout = getattr(settings, "CFDI_VERIFICAR_STATUS_DESCARGA_TIMEOUT", 30)
                verificacion = VerificaSolicitudDescarga(self.fiel, timeout=timeout)
                verificacion = verificacion.verificar_descarga(
                    self.token, 
                    self.rfc_solicitante, 
                    self.numero_solicitud
                )

                self.status = 3
                self.respuesta_consulta = json.dumps(verificacion)
                if verificacion and verificacion.get("cod_estatus") != "5000":
                    self.status = 5

                if verificacion and verificacion.get("estado_solicitud") == "3":
                    self.status = 4
                    self.descargar_paquetes()
                
                
                self.save()
        
        if self.metodo_descarga == self.SCRAPER:
            self.consultar_status_descarga_scraper(
                rfc=rfc, 
            )

    def descargar_paquetes(self):
        from cfdiclient import DescargaMasiva
        from django.core.files.storage import default_storage, \
            get_storage_class, FileSystemStorage
        from django.core.files.base import ContentFile
        import base64

        if not "estado_solicitud" in self.consulta_object:
            return
            
        status = to_int(self.consulta_object["estado_solicitud"])
        if status in [3] and self.consulta_object.get("paquetes") and not self.archivos:
            """
            SI EL ESTADO DE LA SOLICITUD ES 3,
            DESCARGA LOS PAQUETES EN ZIP Y LOS GUARDA EN
            LA PATH RECIBIDO (path_paquetes)
            """
            self.archivos = []
            for paq in self.consulta_object["paquetes"]:
                descarga = DescargaMasiva(self.fiel)
                descarga = descarga.descargar_paquete(
                    self.token, 
                    self.rfc_solicitante, 
                    paq
                )
                if descarga.get("cod_estatus") == "5000":
                    """
                    SI LA DESCARGA ES CORRECTA,
                    GUARDA EL ZIP
                    """

                    fechastr = to_datetime(datetime.datetime.today()).strftime("%m%Y")
                    filename = f'{self.path_paquetes}/{fechastr}/{paq}.zip'

                    filepath = default_storage.save(
                        filename, 
                        ContentFile(
                            base64.b64decode(descarga['paquete_b64'])
                        )
                    )
                    media_storage = get_storage_class()()    


                    if isinstance(media_storage, FileSystemStorage):
                        url = f"{self.base_url}{media_storage.url(filename)}"
                    else:
                        url = media_storage.url(filename)

                    self.archivos.append(url)
                else:
                    self.status = 5
                    self.respuesta_solicitud = descarga
                    #raise ValueError(descarga.get("mensaje"))

            self.save()

    def solicitar_descarga_prodigia(self):
        
        if not self.rfc_solicitante:
            raise ValueError("El RFC solicitante está vacío")

        if not self.rfc_solicitante in [self.rfc_emisor, self.rfc_receptor]:
            raise ValueError("El RFC solicitante debe ser igual al RFC emisor o al RFC receptor")

        data = {
            "rfcSolicitante": self.rfc_solicitante,
            "fechaInicio": self.fecha_inicio.strftime("%Y-%m-%d"),
            "fechaFinal": self.fecha_final.strftime("%Y-%m-%d"),
            "tipoSolicitud":self.tipo_solicitud,
            "pfx":self.pfx_fiel,
            "password": self.password_fiel,
            "usuario": PRODIGIA_AUTH["prod"]["usuario"],
            "passPade": PRODIGIA_PASS,
            "contrato": PRODIGIA_AUTH["prod"]["contrato_descarga_cfdi"],
        }

        if self.rfc_emisor:
            data["rfcEmisor"] = self.rfc_emisor

        if self.rfc_receptor:   
            data["rfcReceptor"] = self.rfc_receptor

        response = requests.post(
            "https://descargamasiva.pade.mx/api/solicitud/generar/",
            json=data,
            verify=False,
        )
        #self.respuesta_solicitud = f"{str(data)}|{response.text}"
        self.respuesta_solicitud = f"{response.text}"

        if response.ok:
            jd = json.loads(response.text)
            self.numero_solicitud = jd["numeroSolicitud"]
        else:
            raise Exception(self.respuesta_solicitud)
        
        self.status = 2
        self.save()



    def solicitar_status_descarga_prodigia(self):
        """
        Consulta el estatus de una solicitud de descarga
        """
        

        data = {   
            "numeroSolicitud": self.numero_solicitud,
            "usuario": PRODIGIA_AUTH["prod"]["usuario"],
            "passPade": PRODIGIA_PASS,
            "contrato": PRODIGIA_AUTH["prod"]["contrato_descarga_cfdi"],
        }

        response = requests.post(
            "https://descargamasiva.pade.mx/api/solicitud/estatus/",
            json=data,
            verify=False,
            timeout=15,
        )
        
        self.respuesta_consulta = f"{response.text}"
        if response.ok:
            if self.get_lista_paquetes():
                self.status = 4
            else:
                self.status = 3

        self.save()


class CertificadoSello(models.Model):
    creado = models.DateTimeField(auto_now_add=True)
    numero = models.CharField(max_length=20, unique=True)
    rfc = models.CharField(max_length=13, default="")
    pem = models.TextField(default="")
    vigencia_inicio = models.DateField(null=True)
    vigencia_fin = models.DateField(null=True)
    
    def get_url_certificado(self):
        """
        Regresa la URL para descargar certificados del SAT a partir de un número
        de certificado

        >>> get_url_certificado("00001000000504204971")
        https://rdc.sat.gob.mx/rccf/000010/000005/04/20/49/00001000000504204971.cer
        """
        nc = self.numero
        url = "https://rdc.sat.gob.mx/rccf/"
        url += f"{nc[0:6]}/{nc[6:12]}/{nc[12:14]}/{nc[14:16]}/{nc[16:18]}/{nc}.cer" 
        return url
    
    def get_path(self):
        """
        Retorna un string con el path al archivo del certificado
        """
        path = os.path.join(TMP_DIR, f"{self.numero}.cer")

        if os.path.exists(path):
            return path
        
        if not self.pem:
            self.set_certificado()

        return path
            
    def set_certificado(self):
        """
        Consulta el certificado al sat y lo guarda en el 
        campo pem, adicional crea el archivo del certificado 
        en una carpeta temporal 
        """

        if not self.numero:
            raise Exception(
                f"El XML no tiene número de certificado"
            )

        path = os.path.join(TMP_DIR, f"{self.numero}.cer")
        url = self.get_url_certificado()

        try:
            response = requests.get(url=url)
            assert response.ok
        except Exception as e:
            raise Exception(
                f"Error al descargar el certificado de la siguiente "
                f"URL: {url} | error:{e}"
            )
        else:
            self.pem = response.content
            self.save()

            with open(path, "wb") as f:
                f.write(self.pem)

