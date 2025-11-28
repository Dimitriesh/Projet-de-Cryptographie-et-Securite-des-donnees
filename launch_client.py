#!/usr/bin/env python3
"""
Script de lancement du client de messagerie sécurisée
===================================================

Ce script simplifie le lancement du client avec des options de configuration.

Usage:
    python launch_client.py [options]

Author: Équipe de développement
Date: 2024
Version: 1.0
"""

import sys
import argparse
from gui import WhatsAppStyleGUI

def main():
    """
    Point d'entrée principal du script de lancement client.
    """
    parser = argparse.ArgumentParser(
        description="🔐 Client de messagerie sécurisée",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  python launch_client.py                    # Lancement normal
  python launch_client.py --server 192.168.1.100  # IP serveur spécifique
  python launch_client.py --offline          # Mode hors ligne
        """
    )
    
    parser.add_argument(
        "--server", 
        default=None, 
        help="Adresse IP du serveur (remplace la configuration par défaut)"
    )
    
    parser.add_argument(
        "--port", 
        type=int, 
        default=12345, 
        help="Port du serveur (défaut: 12345)"
    )
    
    parser.add_argument(
        "--offline", 
        action="store_true", 
        help="Démarrer en mode hors ligne"
    )
    
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Activer le mode debug"
    )
    
    args = parser.parse_args()
    
    # Configuration du logging si debug
    if args.debug:
        import logging
        logging.basicConfig(level=logging.DEBUG)
    
    print("🚀 Lancement du client de messagerie sécurisée...")
    
    try:
        # Créer l'interface graphique
        app = WhatsAppStyleGUI()
        
        # Configurer les paramètres selon les arguments
        if args.server:
            app.server_host = args.server
        if args.port:
            app.server_port = args.port
        if args.offline:
            app.is_online_mode = False
            # Passer directement à l'écran de connexion en mode hors ligne
            app.setup_login_screen()
        
        # Lancer l'application
        app.run()
        
    except KeyboardInterrupt:
        print("\\n👋 Application fermée par l'utilisateur")
        
    except Exception as e:
        print(f"\\n❌ Erreur critique: {e}")
        import logging
        logging.error(f"Erreur critique: {e}", exc_info=True)
        sys.exit(1)
    
    finally:
        print("\\n🔚 Client fermé")

if __name__ == "__main__":
    main()