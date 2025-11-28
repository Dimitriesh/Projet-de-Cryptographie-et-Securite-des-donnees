#!/usr/bin/env python3
"""
Script de lancement du serveur de messagerie sécurisée
====================================================

Ce script simplifie le lancement du serveur avec différentes options
et affiche les informations de connexion pour les clients.

Usage:
    python launch_server.py [options]

Author: Équipe de développement
Date: 2024
Version: 1.0
"""

import socket
import sys
import argparse
from server import SecureMessagingServer, get_local_ip

def get_network_interfaces():
    """
    Récupère les interfaces réseau disponibles.
    
    Returns:
        dict: Dictionnaire des interfaces réseau
    """
    interfaces = {}
    
    # IP locale
    try:
        local_ip = get_local_ip()
        interfaces['local'] = local_ip
    except:
        interfaces['local'] = '127.0.0.1'
    
    # Interface localhost
    interfaces['localhost'] = '127.0.0.1'
    
    return interfaces

def display_connection_info(host, port):
    """
    Affiche les informations de connexion pour les clients.
    
    Args:
        host (str): Adresse du serveur
        port (int): Port du serveur
    """
    interfaces = get_network_interfaces()
    
    print("\\n" + "=" * 80)
    print("🔗 INFORMATIONS DE CONNEXION POUR LES CLIENTS")
    print("=" * 80)
    
    if host == "0.0.0.0":
        print("Le serveur écoute sur toutes les interfaces réseau.")
        print("\\n📱 Pour connecter les clients :")
        
        # Connexion locale
        print(f"   • Sur cette machine : 127.0.0.1:{port}")
        
        # Connexion réseau local
        if 'local' in interfaces and interfaces['local'] != '127.0.0.1':
            print(f"   • Sur le réseau local : {interfaces['local']}:{port}")
            print(f"     (utilisez cette adresse depuis d'autres machines)")
        
        print("\\n🔧 Configuration dans l'application cliente :")
        print(f"   • Adresse serveur : {interfaces['local']}:{port}")
        print(f"   • Port : {port}")
        
    else:
        print(f"Le serveur écoute sur : {host}:{port}")
        print(f"\\n📱 Adresse pour les clients : {host}:{port}")
    
    print("\\n📋 Instructions :")
    print("   1. Lancez l'application cliente : python main.py")
    print("   2. Configurez l'adresse du serveur")
    print("   3. Créez un compte ou connectez-vous")
    print("   4. Commencez à échanger des messages !")
    
    print("=" * 80 + "\\n")

def main():
    """
    Point d'entrée principal du script de lancement.
    """
    parser = argparse.ArgumentParser(
        description="🔐 Serveur de messagerie sécurisée",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  python launch_server.py                    # Serveur sur toutes les interfaces
  python launch_server.py --local            # Serveur sur IP locale uniquement  
  python launch_server.py --port 8080        # Port personnalisé
  python launch_server.py --localhost        # Localhost uniquement
        """
    )
    
    parser.add_argument(
        "--host", 
        default="0.0.0.0", 
        help="Adresse IP d'écoute (défaut: 0.0.0.0 - toutes les interfaces)"
    )
    
    parser.add_argument(
        "--port", 
        type=int, 
        default=12345, 
        help="Port d'écoute (défaut: 12345)"
    )
    
    parser.add_argument(
        "--local", 
        action="store_true", 
        help="Écouter uniquement sur l'IP locale"
    )
    
    parser.add_argument(
        "--localhost", 
        action="store_true", 
        help="Écouter uniquement sur localhost (127.0.0.1)"
    )
    
    parser.add_argument(
        "--info", 
        action="store_true", 
        help="Afficher uniquement les informations réseau"
    )
    
    args = parser.parse_args()
    
    # Déterminer l'adresse d'écoute
    if args.localhost:
        host = "127.0.0.1"
    elif args.local:
        host = get_local_ip()
    else:
        host = args.host
    
    # Si on veut juste les infos
    if args.info:
        display_connection_info(host, args.port)
        return
    
    # Vérifier que le port est disponible
    try:
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        test_socket.bind((host, args.port))
        test_socket.close()
    except socket.error as e:
        print(f"❌ Erreur: Le port {args.port} est déjà utilisé sur {host}")
        print(f"   Détails: {e}")
        print("\\n💡 Solutions:")
        print("   • Utilisez un autre port avec --port XXXX")
        print("   • Arrêtez l'application qui utilise ce port")
        sys.exit(1)
    
    # Afficher les informations de lancement
    print("🚀 Lancement du serveur de messagerie sécurisée...")
    print(f"   Adresse: {host}")
    print(f"   Port: {args.port}")
    
    # Afficher les informations de connexion
    display_connection_info(host, args.port)
    
    try:
        # Créer et démarrer le serveur
        server = SecureMessagingServer(host, args.port)
        server.start()
        
    except KeyboardInterrupt:
        print("\\n\\n👋 Arrêt du serveur demandé par l'utilisateur")
        print("Au revoir!")
        
    except Exception as e:
        print(f"\\n❌ Erreur critique du serveur: {e}")
        import logging
        logging.error(f"Erreur critique: {e}", exc_info=True)
        sys.exit(1)
    
    finally:
        print("\\n🔚 Serveur arrêté")

if __name__ == "__main__":
    main()