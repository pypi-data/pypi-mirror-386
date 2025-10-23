from __future__ import annotations

import requests
from typing import Dict, Optional
from v7e_utils.utils.config import config
from dataclasses import dataclass
from base64 import b64encode
from v7e_utils.utils.nextclould import Nextcloud


def get_relative_path(absolute_path: str) -> str:
    if absolute_path:
        result = absolute_path.find('/files/')
        return absolute_path[result+7:]
    return ''


def parameter_convert(parameters: Dict) -> Dict:
    """
    Convierte un diccionario de parámetros a un formato específico.
    En el cual cada valor será parte de una lista.

    Args:
        parameters (dict): Un diccionario de parámetros.

    Returns:
        dict: Un nuevo diccionario con valores de parámetros en un formato específico.
    """
    keys = parameters.keys()
    result = {f"{key}": [parameters[key]] for key in keys}
    return result


@dataclass
class PfdParameters:
    """
    Clase de datos que representa parámetros para generar informes PDF.

    Args:
        output_file_name (str): Nombre del archivo PDF de salida.
        report_unit_uri (str): URI de la unidad de informe (Path del pdf a ejecutar).
        parameters (Optional[dict]): Diccionario opcional de parámetros de informe (por defecto: None).
        ftp_config (Optional[dict]): Diccionario opcional de configuración FTP (por defecto: None).
        ftp_output_path (Optional[str]): Ruta de salida FTP opcional (por defecto: None).
        username (Optional[str]): Nombre de usuario opcional para la autenticación jasperserver (por defecto: None).
        password (Optional[str]): Contraseña opcional para la autenticación jasperserver (por defecto: None).
    """
    output_file_name: str
    report_unit_uri: str
    parameters: Optional[dict] = None
    ftp_config: Optional[dict] = None
    ftp_output_path: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None


class Job:
    """
    Representa una tarea para generar un informe PDF.

    Args:
        config_parameters (PfdParameters): Parámetros de configuración para la tarea.

    Methods:
        generate_pdf_ftp_now(): Genera un informe PDF al instante y lo carga a través de FTP.\n
    """

    def __init__(self, config_parameters: PfdParameters) -> None:
        """
        Inicializa una instancia de la clase Job.

        Args:
            config_parameters (PfdParameters): Parámetros de configuración para la tarea.
        """
        self.output_file_name = config_parameters.output_file_name
        self.report_unit_uri = config_parameters.report_unit_uri
        self.parameters = config_parameters.parameters
        self.ftp_config = config_parameters.ftp_config
        self.ftp_output_path = config_parameters.ftp_output_path
        self.username = config_parameters.username if config_parameters.username else config.pdf.username
        self.password = config_parameters.password if config_parameters.password else config.pdf.password

    def generate_pdf_ftp_now(self, use_mkdir=True) -> requests.Response:
        """
        Genera un informe PDF al instante y lo carga a través de FTP.

        Returns:
            response (requests.Response): La respuesta del servidor después de la solicitud.
        """
        body = parameter_convert(self.parameters) if self.parameters else None
        data = config.pdf.default_body
        data["label"] = self.output_file_name
        data["baseOutputFilename"] = self.output_file_name
        data["source"]["reportUnitURI"] = self.report_unit_uri
        if body:
            data["source"]["parameters"]["parameterValues"] = body
        if self.ftp_config:
            data["repositoryDestination"]["outputFTPInfo"] = self.ftp_config
        if self.ftp_output_path:
            default_ftp = config.pdf.default_ftp
            default_ftp["folderPath"] = self.ftp_output_path
            data["repositoryDestination"]["outputFTPInfo"] = default_ftp

        headers = {
            "Content-Type": "application/job+json",
            "Authorization": "Basic " + b64encode(bytes(f"{self.username}:{self.password}", 'utf-8')).decode("utf-8")
        }

        # create directory if not exist before create pdf
        result = True
        if use_mkdir:
            nextcloud = Nextcloud()
            path = get_relative_path(
                data["repositoryDestination"]["outputFTPInfo"]["folderPath"])
            result = nextcloud.mkdir(path)
        if result:
            print(f"Url: {config.pdf.default_url}")
            print(f"Json: {data}")
            print(f"headers: {headers}")
            response = requests.put(
                url=config.pdf.default_url, json=data, headers=headers)
            return response
        raise requests.exceptions.HTTPError()
    
    def get_status_pdf(self, id:int) -> bool:
        """
        Devuelve el estado de la creacion del pdf.\n
        Nota solo indica si creo el pdf, no si lo envio al destinatario o ftp.
        
        Args:
            id (int): El identificador de la tarea.

        Returns:
            response (bool): La respuesta de la solicitud.
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Basic " + b64encode(bytes(f"{self.username}:{self.password}", 'utf-8')).decode("utf-8")
        }
        response = requests.get(
            url=f"{config.pdf.default_url}{str(id)}/state/", headers=headers)
        return not response.ok
