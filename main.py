#!/usr/bin/env python3
"""
Point d'entrée principal de l'application de messagerie sécurisée
===============================================================

Ce fichier constitue le point d'entrée principal de l'application de messagerie
sécurisée. Il initialise tous les composants nécessaires et lance l'interface
utilisateur.

L'application offre:
- Une interface moderne de type WhatsApp avec CustomTkinter
- Authentification sécurisée des utilisateurs
- Chiffrement et vérification d'intégrité des messages avec CBC-MAC
- Base de données SQLite pour la persistance
- Architecture modulaire et bien documentée

Usage:
    python main.py

Prérequis:
    - Python 3.8+
    - customtkinter
    - cryptography
    - sqlite3 (inclus avec Python)

Author: Équipe de développement
Date: 2024
Version: 1.0
License: MIT

Sécurité:
Cette application est conçue à des fins éducatives pour démontrer
l'implémentation de la cryptographie appliquée. Pour un usage en
production, des améliorations de sécurité supplémentaires seraient
nécessaires.
"""

import sys
import os
import logging
from pathlib import Path

# Ajouter le répertoire courant au chemin Python pour les imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    # Imports des modules de l'application
    from gui import WhatsAppStyleGUI
    from database import get_db_manager
    from crypto import get_crypto_manager
    from user_manager import get_user_manager
    from message_manager import get_message_manager
except ImportError as e:
    print(f"Erreur d'import: {e}")
    print("Assurez-vous que tous les modules requis sont présents.")
    sys.exit(1)

# Configuration du logging global
def setup_logging():
    """
    Configure le système de logging pour l'application.
    """
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler("secure_messaging.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Créer un logger pour l'application principale
    logger = logging.getLogger("SecureMessaging")
    return logger

def check_dependencies():
    """
    Vérifie que toutes les dépendances nécessaires sont installées.
    
    Returns:
        bool: True si toutes les dépendances sont présentes, False sinon
    """
    required_packages = {
        'customtkinter': 'customtkinter',
        'cryptography': 'cryptography',
        'sqlite3': 'sqlite3'
    }
    
    missing_packages = []
    
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        print("❌ Dépendances manquantes:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\\nInstallez les dépendances manquantes avec:")
        print("pip install " + " ".join(missing_packages))
        return False
    
    print("✅ Toutes les dépendances sont présentes")
    return True

def initialize_application():
    """
    Initialise tous les composants de l'application.
    
    Returns:
        bool: True si l'initialisation réussit, False sinon
    """
    try:
        logger = logging.getLogger("SecureMessaging")
        
        # Initialiser la base de données
        logger.info("Initialisation de la base de données...")
        db_manager = get_db_manager()
        
        # Initialiser le gestionnaire cryptographique
        logger.info("Initialisation du gestionnaire cryptographique...")
        crypto_manager = get_crypto_manager()
        
        # Initialiser le gestionnaire d'utilisateurs
        logger.info("Initialisation du gestionnaire d'utilisateurs...")
        user_manager = get_user_manager()
        
        # Initialiser le gestionnaire de messages
        logger.info("Initialisation du gestionnaire de messages...")
        message_manager = get_message_manager()
        
        logger.info("✅ Tous les composants initialisés avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation: {e}")
        return False

def create_demo_data():
    """
    Crée des données de démonstration pour tester l'application.
    
    Note: Cette fonction est optionnelle et seulement pour les tests
    """
    try:
        user_manager = get_user_manager()
        message_manager = get_message_manager()
        
        # Créer quelques utilisateurs de test
        demo_users = [
            {
                'email': 'alice@gmail.com',
                'password': 'SecurePass123!',
                'name': 'Alice Dupont',
                'birthday': '1990-05-15',
                'phone': '+33123456789'
            },
            {
                'email': 'bob@gmail.com',
                'password': 'SecurePass123!',
                'name': 'Bob Martin',
                'birthday': '1985-08-22',
                'phone': '+33987654321'
            }
        ]
        
        for user_data in demo_users:
            result = user_manager.register_user(**user_data)
            if result['success']:
                print(f"✅ Utilisateur de démonstration créé: {user_data['email']}")
        
        return True
        
    except Exception as e:
        # Si les utilisateurs existent déjà, ce n'est pas grave
        return True

def print_welcome_message():
    """
    Affiche le message de bienvenue et les informations de l'application.
    """
    print("=" * 60)
    print("🔐 SECURE MESSAGING - WHATSAPP STYLE")
    print("=" * 60)
    print("Une application de messagerie sécurisée avec:")
    print("  • Interface moderne type WhatsApp")
    print("  • Chiffrement et intégrité des messages (CBC-MAC)")
    print("  • Authentification sécurisée des utilisateurs")
    print("  • Architecture modulaire et documentée")
    print()
    print("Fonctionnalités:")
    print("  ✓ Inscription/Connexion d'utilisateurs")
    print("  ✓ Conversations en temps réel")
    print("  ✓ Vérification d'intégrité des messages")
    print("  ✓ Interface intuitive et moderne")
    print()
    print("Utilisation:")
    print("  1. Créez un compte ou connectez-vous")
    print("  2. Démarrez une conversation avec un email")
    print("  3. Envoyez des messages sécurisés")
    print("  4. L'intégrité est vérifiée automatiquement")
    print("=" * 60)

def print_help():
    """
    Affiche l'aide pour l'utilisation de l'application.
    """
    help_text = """
Usage: python main.py [OPTIONS]

Options:
  --help, -h          Afficher cette aide
  --demo-data         Créer des données de démonstration
  --version           Afficher la version
  --check-deps        Vérifier les dépendances uniquement

Exemples:
  python main.py                    # Lancer l'application normalement
  python main.py --demo-data        # Lancer avec données de test
  python main.py --check-deps       # Vérifier les dépendances

Pour plus d'informations, consultez le fichier README.md
"""
    print(help_text)

def main():
    """
    Fonction principale de l'application.
    """
    # Analyser les arguments de ligne de commande
    args = sys.argv[1:]
    
    if '--help' in args or '-h' in args:
        print_help()
        return
    
    if '--version' in args:
        print("Secure Messaging v1.0")
        print("Développé avec Python et CustomTkinter")
        return
    
    if '--check-deps' in args:
        check_dependencies()
        return
    
    # Configuration du logging
    logger = setup_logging()
    logger.info("=" * 50)
    logger.info("DÉMARRAGE DE L'APPLICATION SECURE MESSAGING")
    logger.info("=" * 50)
    
    # Vérifier les dépendances
    if not check_dependencies():
        logger.error("Impossible de continuer sans les dépendances requises")
        sys.exit(1)
    
    # Initialiser l'application
    if not initialize_application():
        logger.error("Échec de l'initialisation de l'application")
        sys.exit(1)
    
    # Créer des données de démonstration si demandé
    if '--demo-data' in args:
        logger.info("Création de données de démonstration...")
        create_demo_data()
    
    try:
        # Afficher le message de bienvenue
        print_welcome_message()
        
        # Lancer l'interface graphique
        logger.info("Lancement de l'interface graphique...")
        app = WhatsAppStyleGUI()
        
        # Démarrer la boucle principale
        logger.info("Application démarrée - Interface utilisateur active")
        app.run()
        
        logger.info("Application fermée normalement")
        
    except KeyboardInterrupt:
        logger.info("Application interrompue par l'utilisateur")
    except Exception as e:
        logger.error(f"Erreur inattendue: {e}", exc_info=True)
        print(f"❌ Erreur critique: {e}")
        sys.exit(1)
    finally:
        # Nettoyage des ressources si nécessaire
        logger.info("Nettoyage des ressources...")

def run_tests():
    """
    Lance une suite de tests de base pour vérifier le fonctionnement.
    
    Cette fonction peut être utilisée pour des tests de régression rapides.
    """
    print("🧪 Lancement des tests de base...")
    
    try:
        # Test de la cryptographie
        from crypto import get_crypto_manager
        crypto = get_crypto_manager()
        
        # Test de génération de clé
        key = crypto.generate_shared_key("test1@gmail.com", "test2@gmail.com")
        assert len(key) == 32, "Clé de taille incorrecte"
        
        # Test de MAC
        message = "Test message"
        iv = crypto.generate_iv()
        mac = crypto.calculate_cbc_mac(key, message.encode(), iv)
        assert len(mac) == 16, "MAC de taille incorrecte"
        
        # Test de vérification
        is_valid = crypto.verify_message_integrity(key, message.encode(), iv, mac)
        assert is_valid, "Vérification d'intégrité échouée"
        
        print("✅ Tests cryptographiques: OK")
        
        # Test de la base de données
        from database import get_db_manager
        db = get_db_manager()
        
        # Test de création d'utilisateur fictif
        test_email = f"test_{int(time.time())}@gmail.com"
        success = db.create_user(
            test_email, "test_hash", "Test User", "1990-01-01", "1234567890"
        )
        
        if success:
            # Test de récupération
            user = db.get_user(test_email)
            assert user is not None, "Utilisateur non trouvé après création"
            print("✅ Tests base de données: OK")
        
        print("✅ Tous les tests de base réussis!")
        return True
        
    except Exception as e:
        print(f"❌ Échec des tests: {e}")
        return False

if __name__ == "__main__":
    # Vérifier si on veut lancer les tests
    if '--test' in sys.argv:
        import time
        if run_tests():
            print("Tests terminés avec succès")
        else:
            print("Certains tests ont échoué")
            sys.exit(1)
    else:
        # Lancer l'application normale
        main()