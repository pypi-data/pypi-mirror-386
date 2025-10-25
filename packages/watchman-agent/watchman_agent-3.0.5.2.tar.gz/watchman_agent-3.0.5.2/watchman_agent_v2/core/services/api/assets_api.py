import json
import os
import re
import magic
from typing import Dict, Optional
import click
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
from watchman_agent_v2.core.services.api.api_client import APIClient
from watchman_agent_v2.core.services.api.exceptions import InventoryValidationError
from watchman_agent_v2.core.utils.log_manager import LogManager

class AssetAPIClient(APIClient):
    """
    Client spécialisé pour l'envoi de fichiers d'inventaire avec validation avancée
    """
    API_BASE_URL = 'https://api.watchman.bj/api/v2/'
    API_ENDPOINT = 'agent/webhook_v2/'
    ALLOWED_MIME_TYPES = {
        'text/csv': ['csv'],
        'application/json': ['json'],
        'text/plain': ['json'],
        'application/vnd.ms-excel': ['xls'],
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['xlsx']
    }

    def __init__(self, credentials: Dict[str, str]):
        full_endpoint = f"{self.API_BASE_URL.rstrip('/')}/{self.API_ENDPOINT.lstrip('/')}"
        super().__init__(full_endpoint, credentials)
        
        # Initialisation compatible multiplateforme
        try:
            # Tentative avec la classe Magic (python-magic standard)
            self.mime = magic.Magic(mime=True)
            self._use_class_method = True
        except (AttributeError, TypeError):
            # Fallback pour python-magic-bin
            self.mime = None
            self._use_class_method = False

    def _get_mime_type(self, file_path: str) -> str:
        """Obtient le type MIME d'un fichier - compatible toutes plateformes"""
        try:
            if self._use_class_method and self.mime:
                return self.mime.from_file(file_path)
            else:
                return magic.from_file(file_path, mime=True)
        except Exception as e:
            LogManager.warning(f"Impossible de détecter le MIME type de {file_path}: {e}")
            return self._get_mime_from_extension(file_path)

    def _get_mime_from_extension(self, file_path: str) -> str:
        """Fallback: détermine le MIME type à partir de l'extension"""
        _, ext = os.path.splitext(file_path)
        ext = ext.lower().lstrip('.')
        
        mime_map = {
            'csv': 'text/csv',
            'json': 'application/json',
            'xls': 'application/vnd.ms-excel',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'txt': 'text/plain'
        }
        
        return mime_map.get(ext, 'application/octet-stream')

    def send_assets(self, file_path: str) -> bool:
        """
        Envoie un fichier d'inventaire avec validation complète
        
        Args:
            file_path: Chemin vers le fichier à envoyer
            
        Returns:
            bool: True si l'envoi réussit
            
        Raises:
            InventoryValidationError: Si validation échoue
        """
        try:
            self._validate_file(file_path)
            
            # Obtention du type MIME avec la méthode compatible
            mime_type = self._get_mime_type(file_path)
            
            with open(file_path, 'rb') as f:
                multipart_data = MultipartEncoder(
                    fields={'file': (os.path.basename(file_path), f, mime_type)}
                )
                
                headers = {
                    'Content-Type': multipart_data.content_type,
                    **self.credentials
                }
                
                response = self.send_data(
                    data=multipart_data,
                    headers=headers
                )
                
                error_message = None
                response_data = response.json()
                report = response_data.get('report', {})
                code = response.status_code
                
                if code != 201:
                    try:
                        match = re.search(r"'message': ErrorDetail\(string='([^']*)'", response_data['detail'])
                        if match:
                            error_message = match.group(1)
                        else:
                            error_message = response_data['detail']
                    except:
                        error_message = "Serveur Error! Please contact Watchman developper"

            return response.status_code == 201, report, error_message

        except FileNotFoundError:
            click.echo(f"Fichier introuvable : {file_path}", err=True)
            raise
        except PermissionError:
            click.echo(f"Permission refusée pour : {file_path}", err=True)
            raise

    def _validate_file(self, file_path: str):
        """Valide le fichier selon les critères de sécurité"""
        # Vérification basique
        if not os.path.isfile(file_path):
            raise InventoryValidationError("Le chemin spécifié n'est pas un fichier valide")
            
        # Taille maximale 100MB
        max_size = 100 * 1024 * 1024
        file_size = os.path.getsize(file_path)
        if file_size > max_size:
            raise InventoryValidationError(f"Fichier trop volumineux ({file_size} > {max_size} bytes)")
            
        # Type MIME réel avec la méthode compatible
        mime_type = self._get_mime_type(file_path)
        extension = os.path.splitext(file_path)[1].lower().lstrip('.')
        
        if mime_type not in self.ALLOWED_MIME_TYPES:
            raise InventoryValidationError(f"Type MIME non autorisé : {mime_type}")
            
        if extension not in self.ALLOWED_MIME_TYPES[mime_type]:
            raise InventoryValidationError(f"Extension incohérente avec le type MIME : {extension} != {self.ALLOWED_MIME_TYPES[mime_type]}")

    def _calculate_checksum(self, file_path: str) -> str:
        """Calcule une empreinte sécurisée du fichier"""
        # Implémentation SHA-256
        import hashlib
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()

    def send_data(self, data, headers: Optional[Dict] = None):
        """Override pour gestion des fichiers"""
        try:
            return self.session.post(
                self.endpoint,
                data=data,
                headers=headers or {},
                timeout=30
            )
        except requests.exceptions.RequestException as e:
            click.echo(f"Erreur réseau : {str(e)}", err=True)
            raise