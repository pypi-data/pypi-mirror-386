import os
import json
import tempfile
import asyncio
from datetime import datetime
from typing import Dict, Any

import click
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from watchman_agent_v2.core.services.api.assets_api import AssetAPIClient
from watchman_agent_v2.core.config.config_manager import ConfigManager
from watchman_agent_v2.core.utils.log_manager import LogManager
from watchman_agent_v2.core.utils.service_manager import ServiceManager


@click.command()
@click.option('--host', default='0.0.0.0', help="Adresse IP d'écoute du serveur")
@click.option('--port', default=8000, type=int, help="Port d'écoute du serveur")
@click.option('--reload', is_flag=True, help="Mode rechargement automatique pour le développement")
@click.option('-d', '--detach', is_flag=True, help="Exécution du serveur en arrière-plan")
@click.option('--install-service', is_flag=True, help="Installer comme service système (redémarrage automatique)")
@click.option('--uninstall-service', is_flag=True, help="Désinstaller le service système")
@click.option('--service-status', is_flag=True, help="Afficher l'état du service système")
def server(host: str, port: int, reload: bool, detach: bool, install_service: bool, uninstall_service: bool, service_status: bool):
    """
    Lance un serveur FastAPI pour recevoir des données d'inventaire via webhook.

    Le serveur expose un endpoint POST /api/v1/inventory qui:
    1. Reçoit des données JSON d'inventaire
    2. Les sauvegarde dans un fichier temporaire
    3. Les envoie à l'API externe via AssetAPIClient

    Options de service système:
    - --install-service: Installe comme service système (Windows/Linux/macOS)
    - --uninstall-service: Désinstalle le service système
    - --service-status: Affiche l'état du service
    """

    # Gestion des services système
    service_manager = ServiceManager("watchman-agent-server")

    if service_status:
        status = service_manager.get_service_status()
        click.echo(f"🔍 État du service '{service_manager.service_name}':")
        click.echo(f"   Installé: {'✅' if status['installed'] else '❌'}")
        click.echo(f"   En cours: {'✅' if status['running'] else '❌'}")
        if status['output']:
            click.echo(f"   Détails: {status['output']}")
        return

    if install_service:
        click.echo(f"Installation du service système sur {service_manager.system}...")
        success = service_manager.install_service(host, port,
            "Watchman Agent Inventory Server - Service de réception d'inventaire")

        if success:
            click.echo(f"Service installé avec succès!")
            click.echo(f"Démarrage du service...")
            if service_manager.start_service():
                click.echo(f"Service démarré!")
                click.echo(f"Le serveur est maintenant accessible sur http://{host}:{port}")
                click.echo(f"Le service redémarrera automatiquement après un reboot")
            else:
                click.echo(f"❌ Échec du démarrage du service")
        else:
            click.echo(f"❌ Échec de l'installation du service")
        return

    if uninstall_service:
        click.echo(f"🗑️  Désinstallation du service système...")
        success = service_manager.uninstall_service()

        if success:
            click.echo(f"✅ Service désinstallé avec succès!")
        else:
            click.echo(f"❌ Échec de la désinstallation du service")
        return

    if detach:
        pid_file = os.path.expanduser("~/.watchman_agent_server.pid")
        log_file = os.path.expanduser("~/watchman_agent_server.log")

        # Construire la commande à lancer en arrière-plan
        cmd = ["watchman-agent", "server"]
        cmd.extend(["--host", host])
        cmd.extend(["--port", str(port)])
        if reload:
            cmd.append("--reload")

        from watchman_agent_v2.core.utils.launch_detached import launch_detached
        launch_detached(cmd, "server", log_file)
        return

    try:
        app = create_fastapi_app()

        click.echo(f"🚀 Démarrage du serveur d'inventaire sur http://{host}:{port}")
        click.echo(f"📡 Endpoint disponible: http://{host}:{port}/api/v1/inventory")
        click.echo("Appuyez sur Ctrl+C pour arrêter le serveur")

        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )

    except Exception as e:
        LogManager.error(f"Erreur lors du démarrage du serveur: {e}")
        click.echo(f"❌ Erreur: {e}", err=True)
        raise


def create_fastapi_app() -> FastAPI:
    """Crée et configure l'application FastAPI"""
    app = FastAPI(
        title="Watchman Agent Inventory Server",
        description="Serveur de réception des données d'inventaire",
        version="1.0.0"
    )

    @app.post("/api/v1/inventory")
    async def receive_inventory(request: Request):
        """
        Endpoint pour recevoir les données d'inventaire

        Body: JSON contenant les données d'inventaire
        Returns: Confirmation de réception et statut d'envoi à l'API
        """
        try:
            # Récupération des données JSON
            inventory_data = await request.json()
            inventory_data=inventory_data.get('data', inventory_data)

            # Validation basique de la structure
            if not isinstance(inventory_data, dict) or 'assets' not in inventory_data:
                raise HTTPException(
                    status_code=400,
                    detail="Format JSON invalide. Structure attendue: {'assets': [...]}"
                )

            # Ajout de métadonnées de réception
            inventory_data['webhook_received_at'] = datetime.now().isoformat()
            inventory_data['webhook_server_info'] = {
                'version': '1.0.0',
                'received_from': str(request.client.host) if request.client else 'unknown'
            }

            # Sauvegarde dans un fichier temporaire
            temp_file_path = await save_inventory_to_temp_file(inventory_data)

            # Envoi à l'API externe
            success, report, error_message = await send_to_external_api(temp_file_path)

            # Nettoyage du fichier temporaire
            try:
                os.unlink(temp_file_path)
            except OSError:
                LogManager.warning(f"Impossible de supprimer le fichier temporaire: {temp_file_path}")

            # Réponse selon le résultat de l'envoi
            if success:
                LogManager.info(f"Inventaire reçu et envoyé avec succès - {len(inventory_data.get('assets', []))} assets")
                return JSONResponse(
                    status_code=201,
                    content={
                        "status": "success",
                        "message": "Inventaire reçu et transmis avec succès",
                        "assets_count": len(inventory_data.get('assets', [])),
                        "report": report,
                        "timestamp": datetime.now().isoformat()
                    }
                )
            else:
                LogManager.error(f"Échec de l'envoi à l'API externe: {error_message}")
                return JSONResponse(
                    status_code=500,
                    content={
                        "status": "error",
                        "message": f"Inventaire reçu mais échec de transmission: {error_message}",
                        "assets_count": len(inventory_data.get('assets', [])),
                        "timestamp": datetime.now().isoformat()
                    }
                )

        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Corps de requête JSON invalide"
            )
        except Exception as e:
            LogManager.error(f"Erreur lors du traitement de l'inventaire: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Erreur interne du serveur: {str(e)}"
            )

    @app.get("/health")
    async def health_check():
        """Endpoint de vérification de l'état du serveur"""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        }

    @app.get("/")
    async def root():
        """Endpoint racine avec informations de l'API"""
        return {
            "service": "Watchman Agent Inventory Server",
            "version": "1.0.0",
            "endpoints": {
                "inventory": "/api/v1/inventory",
                "health": "/health"
            },
            "timestamp": datetime.now().isoformat()
        }

    return app


async def save_inventory_to_temp_file(inventory_data: Dict[str, Any]) -> str:
    """
    Sauvegarde les données d'inventaire dans un fichier temporaire JSON

    Args:
        inventory_data: Données d'inventaire à sauvegarder

    Returns:
        str: Chemin vers le fichier temporaire créé
    """
    try:
        # Création d'un fichier temporaire avec suffixe JSON
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.json',
            prefix='inventory_',
            delete=False,
            encoding='utf-8'
        ) as temp_file:
            json.dump(inventory_data, temp_file, ensure_ascii=False, indent=2)
            temp_file_path = temp_file.name

        LogManager.info(f"Données d'inventaire sauvegardées dans: {temp_file_path}")
        return temp_file_path

    except Exception as e:
        LogManager.error(f"Erreur lors de la sauvegarde du fichier temporaire: {e}")
        raise


async def send_to_external_api(file_path: str) -> tuple[bool, dict, str]:
    """
    Envoie le fichier d'inventaire à l'API externe

    Args:
        file_path: Chemin vers le fichier à envoyer

    Returns:
        tuple: (success, report, error_message)
    """
    try:
        # Récupération de la configuration
        config_manager = ConfigManager()
        config = config_manager.config
        client_id=config['api']['client_id']
        client_secret=config_manager.decrypt(config['api']['client_secret'])

        # Récupération des credentials depuis la config
        credentials={
                    "AGENT-ID": client_id,
                    "AGENT-SECRET": client_secret}

        # Validation des credentials
        if not any(credentials.values()):
            error_msg = "Aucune authentification configurée (api_key, client_id/client_secret)"
            LogManager.error(error_msg)
            return False, {}, error_msg

        # Envoi via AssetAPIClient
        client = AssetAPIClient(credentials)
        success, report, error_message = client.send_assets(file_path)

        if success:
            LogManager.info("Fichier d'inventaire envoyé avec succès à l'API externe")
        else:
            LogManager.error(f"Échec de l'envoi à l'API externe: {error_message}")

        return success, report or {}, error_message or ""

    except Exception as e:
        error_msg = f"Erreur lors de l'envoi à l'API externe: {str(e)}"
        LogManager.error(error_msg)
        return False, {}, error_msg


if __name__ == '__main__':
    server()