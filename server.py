#!/usr/bin/env python3
"""
Serveur de messagerie sécurisée en temps réel
===========================================

Ce module implémente un serveur central qui gère les connexions des clients
et permet l'échange de messages en temps réel sur un réseau local.

Le serveur:
- Accepte les connexions multiples via sockets TCP
- Gère l'authentification des utilisateurs
- Route les messages entre clients connectés
- Maintient une liste des utilisateurs en ligne
- Assure la persistance via la base de données

Author: Équipe de développement
Date: 2024
Version: 1.0
"""

import socket
import threading
import json
import logging
import signal
import sys
from datetime import datetime
from typing import Dict, List, Optional
from database import get_db_manager
from crypto import get_crypto_manager
from user_manager import get_user_manager
from message_manager import get_message_manager

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SecureMessagingServer")

class SecureMessagingServer:
    """
    Serveur de messagerie sécurisée pour communication en temps réel.
    
    Ce serveur gère les connexions de multiples clients et permet
    l'échange de messages sécurisés en temps réel sur un réseau local.
    
    Attributes:
        host (str): Adresse IP du serveur
        port (int): Port d'écoute du serveur
        socket: Socket principal du serveur
        clients: Dictionnaire des clients connectés
        is_running: État du serveur
    """
    
    def __init__(self, host: str = "0.0.0.0", port: int = 12345):
        """
        Initialise le serveur de messagerie.
        
        Args:
            host (str): Adresse IP d'écoute (0.0.0.0 pour toutes les interfaces)
            port (int): Port d'écoute
        """
        self.host = host
        self.port = port
        self.socket = None
        self.clients = {}  # {email: {"socket": socket, "thread": thread, "last_seen": datetime}}
        self.is_running = False
        
        # Gestionnaires
        self.db_manager = get_db_manager()
        self.crypto_manager = get_crypto_manager()
        self.user_manager = get_user_manager()
        self.message_manager = get_message_manager()
        
        # Configuration des signaux pour arrêt propre
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        logger.info(f"Serveur initialisé sur {host}:{port}")
    
    def signal_handler(self, signum, frame):
        """
        Gère les signaux pour un arrêt propre du serveur.
        """
        logger.info("Signal d'arrêt reçu, fermeture du serveur...")
        self.stop()
        sys.exit(0)
    
    def start(self):
        """
        Démarre le serveur et commence à écouter les connexions.
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(50)  # Permettre jusqu'à 50 connexions en attente
            
            self.is_running = True
            logger.info(f"🚀 Serveur démarré et en écoute sur {self.host}:{self.port}")
            
            print("=" * 60)
            print("🔐 SERVEUR DE MESSAGERIE SÉCURISÉE")
            print("=" * 60)
            print(f"Adresse: {self.host}:{self.port}")
            print("État: En ligne ✅")
            print("Clients connectés: 0")
            print("Appuyez sur Ctrl+C pour arrêter le serveur")
            print("=" * 60)
            
            while self.is_running:
                try:
                    client_socket, client_address = self.socket.accept()
                    logger.info(f"Nouvelle connexion de {client_address}")
                    
                    # Créer un thread pour gérer ce client
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address),
                        daemon=True
                    )
                    client_thread.start()
                    
                except socket.error as e:
                    if self.is_running:
                        logger.error(f"Erreur socket: {e}")
                
        except Exception as e:
            logger.error(f"Erreur lors du démarrage du serveur: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """
        Arrête le serveur et ferme toutes les connexions.
        """
        logger.info("Arrêt du serveur...")
        self.is_running = False
        
        # Fermer toutes les connexions clients
        for email, client_info in list(self.clients.items()):
            try:
                client_info["socket"].close()
            except:
                pass
        
        # Fermer le socket principal
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        
        logger.info("Serveur arrêté")
    
    def handle_client(self, client_socket: socket.socket, client_address: tuple):
        """
        Gère les communications avec un client spécifique.
        
        Args:
            client_socket: Socket de connexion avec le client
            client_address: Adresse du client (IP, port)
        """
        authenticated_user = None
        
        try:
            while self.is_running:
                # Recevoir les données du client
                data = client_socket.recv(4096)
                if not data:
                    break
                
                try:
                    # Décoder le message JSON
                    message = json.loads(data.decode('utf-8'))
                    response = self.process_message(message, authenticated_user)
                    
                    # Envoyer la réponse d'abord
                    if response:
                        client_socket.send(json.dumps(response).encode('utf-8'))
                    
                    # Si authentification réussie, enregistrer le client APRÈS avoir envoyé la réponse
                    if response.get("type") == "auth_success":
                        authenticated_user = message.get("email")
                        self.clients[authenticated_user] = {
                            "socket": client_socket,
                            "thread": threading.current_thread(),
                            "last_seen": datetime.now(),
                            "address": client_address
                        }
                        logger.info(f"Utilisateur authentifié: {authenticated_user} ({client_address})")
                        # Attendre un peu avant de broadcaster pour éviter les interférences
                        threading.Timer(0.1, lambda: self.broadcast_user_status(authenticated_user, "online")).start()
                        
                except json.JSONDecodeError:
                    logger.error(f"Message JSON invalide de {client_address}")
                except Exception as e:
                    logger.error(f"Erreur traitement message de {client_address}: {e}")
                    
        except Exception as e:
            logger.error(f"Erreur avec le client {client_address}: {e}")
        finally:
            # Nettoyer à la déconnexion
            if authenticated_user and authenticated_user in self.clients:
                del self.clients[authenticated_user]
                self.broadcast_user_status(authenticated_user, "offline")
                logger.info(f"Client déconnecté: {authenticated_user}")
            
            try:
                client_socket.close()
            except:
                pass
    
    def process_message(self, message: dict, authenticated_user: str) -> dict:
        """
        Traite un message reçu d'un client et retourne une réponse.
        
        Args:
            message: Message JSON reçu du client
            authenticated_user: Email de l'utilisateur authentifié (None si pas connecté)
            
        Returns:
            dict: Réponse à envoyer au client
        """
        msg_type = message.get("type")
        
        try:
            if msg_type == "authenticate":
                return self.handle_authentication(message)
            
            elif msg_type == "register":
                return self.handle_registration(message)
            
            elif msg_type == "send_message":
                if not authenticated_user:
                    return {"type": "error", "message": "Non authentifié"}
                return self.handle_send_message(message, authenticated_user)
            
            elif msg_type == "get_conversations":
                if not authenticated_user:
                    return {"type": "error", "message": "Non authentifié"}
                return self.handle_get_conversations(authenticated_user)
            
            elif msg_type == "get_messages":
                if not authenticated_user:
                    return {"type": "error", "message": "Non authentifié"}
                return self.handle_get_messages(message, authenticated_user)
            
            elif msg_type == "search_users":
                if not authenticated_user:
                    return {"type": "error", "message": "Non authentifié"}
                return self.handle_search_users(message)
            
            elif msg_type == "ping":
                return {"type": "pong", "timestamp": datetime.now().isoformat()}
            
            else:
                return {"type": "error", "message": "Type de message non reconnu"}
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement du message {msg_type}: {e}")
            return {"type": "error", "message": "Erreur interne du serveur"}
    
    def handle_authentication(self, message: dict) -> dict:
        """
        Gère l'authentification d'un utilisateur.
        """
        email = message.get("email")
        password = message.get("password")
        
        if not email or not password:
            return {"type": "auth_failed", "message": "Email et mot de passe requis"}
        
        result = self.user_manager.authenticate_user(email, password)
        
        if result["success"]:
            return {
                "type": "auth_success",
                "message": "Authentification réussie",
                "user": result["user"]
            }
        else:
            return {
                "type": "auth_failed",
                "message": result["message"]
            }
    
    def handle_registration(self, message: dict) -> dict:
        """
        Gère l'inscription d'un nouvel utilisateur.
        """
        result = self.user_manager.register_user(
            email=message.get("email", ""),
            password=message.get("password", ""),
            name=message.get("name", ""),
            birthday=message.get("birthday"),
            phone_number=message.get("phone_number")
        )
        
        if result["success"]:
            return {"type": "registration_success", "message": result["message"]}
        else:
            return {
                "type": "registration_failed", 
                "message": result["message"],
                "errors": result.get("errors", [])
            }
    
    def handle_send_message(self, message: dict, sender_email: str) -> dict:
        """
        Gère l'envoi d'un message entre utilisateurs.
        """
        receiver_email = message.get("receiver_email")
        content = message.get("content")
        
        if not receiver_email or not content:
            return {"type": "error", "message": "Destinataire et contenu requis"}
        
        # Envoyer le message via le gestionnaire
        result = self.message_manager.send_message(sender_email, receiver_email, content)
        
        if result["success"]:
            # Notifier le destinataire s'il est connecté
            self.notify_new_message(receiver_email, {
                "type": "new_message",
                "sender_email": sender_email,
                "receiver_email": receiver_email,
                "content": content,
                "message_id": result["message_id"],
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "type": "message_sent",
                "message": "Message envoyé avec succès",
                "message_id": result["message_id"]
            }
        else:
            return {"type": "error", "message": result["message"]}
    
    def handle_get_conversations(self, user_email: str) -> dict:
        """
        Récupère les conversations d'un utilisateur.
        """
        conversations = self.message_manager.get_user_conversations(user_email)
        
        # Ajouter le statut en ligne des contacts
        for conv in conversations:
            other_email = conv["other_user_email"]
            conv["is_online"] = other_email in self.clients
        
        return {
            "type": "conversations",
            "conversations": conversations
        }
    
    def handle_get_messages(self, message: dict, user_email: str) -> dict:
        """
        Récupère les messages d'une conversation.
        """
        other_user_email = message.get("other_user_email")
        
        if not other_user_email:
            return {"type": "error", "message": "Email du contact requis"}
        
        messages = self.message_manager.get_conversation_messages(
            user_email, other_user_email, verify_integrity=True
        )
        
        # Marquer les messages comme lus
        self.message_manager.mark_conversation_as_read(user_email, other_user_email)
        
        return {
            "type": "messages",
            "messages": messages
        }
    
    def handle_search_users(self, message: dict) -> dict:
        """
        Recherche des utilisateurs.
        """
        query = message.get("query", "")
        users = self.user_manager.search_users(query)
        
        return {
            "type": "search_results",
            "users": users
        }
    
    def notify_new_message(self, recipient_email: str, notification: dict):
        """
        Notifie un utilisateur connecté d'un nouveau message.
        
        Args:
            recipient_email: Email du destinataire
            notification: Données de notification à envoyer
        """
        if recipient_email in self.clients:
            try:
                client_socket = self.clients[recipient_email]["socket"]
                client_socket.send(json.dumps(notification).encode('utf-8'))
                logger.info(f"Notification envoyée à {recipient_email}")
            except Exception as e:
                logger.error(f"Erreur envoi notification à {recipient_email}: {e}")
                # Supprimer le client déconnecté
                if recipient_email in self.clients:
                    del self.clients[recipient_email]
    
    def broadcast_user_status(self, user_email: str, status: str):
        """
        Diffuse le statut d'un utilisateur à tous les clients connectés.
        
        Args:
            user_email: Email de l'utilisateur
            status: Nouveau statut ("online" ou "offline")
        """
        notification = {
            "type": "user_status",
            "user_email": user_email,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        
        # Envoyer à tous les clients connectés
        for email, client_info in list(self.clients.items()):
            if email != user_email:  # Ne pas notifier l'utilisateur lui-même
                try:
                    client_socket = client_info["socket"]
                    client_socket.send(json.dumps(notification).encode('utf-8'))
                except Exception as e:
                    logger.error(f"Erreur diffusion statut à {email}: {e}")
                    # Supprimer le client déconnecté
                    if email in self.clients:
                        del self.clients[email]
    
    def get_server_stats(self) -> dict:
        """
        Retourne les statistiques du serveur.
        
        Returns:
            dict: Statistiques du serveur
        """
        return {
            "is_running": self.is_running,
            "connected_clients": len(self.clients),
            "client_list": list(self.clients.keys()),
            "host": self.host,
            "port": self.port,
            "uptime": datetime.now().isoformat()
        }
    
    def print_status(self):
        """
        Affiche le statut actuel du serveur.
        """
        stats = self.get_server_stats()
        print("\\n" + "=" * 50)
        print("📊 STATUT DU SERVEUR")
        print("=" * 50)
        print(f"État: {'🟢 En ligne' if stats['is_running'] else '🔴 Hors ligne'}")
        print(f"Adresse: {stats['host']}:{stats['port']}")
        print(f"Clients connectés: {stats['connected_clients']}")
        if stats['client_list']:
            print("Utilisateurs en ligne:")
            for email in stats['client_list']:
                print(f"  • {email}")
        print("=" * 50 + "\\n")


def get_local_ip():
    """
    Obtient l'adresse IP locale de la machine.
    
    Returns:
        str: Adresse IP locale
    """
    try:
        # Se connecter à une adresse externe pour obtenir l'IP locale
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except:
        return "127.0.0.1"


def main():
    """
    Point d'entrée principal du serveur.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Serveur de messagerie sécurisée")
    parser.add_argument("--host", default="0.0.0.0", help="Adresse IP d'écoute")
    parser.add_argument("--port", type=int, default=12345, help="Port d'écoute")
    parser.add_argument("--local", action="store_true", help="Utiliser l'IP locale")
    
    args = parser.parse_args()
    
    # Déterminer l'adresse d'écoute
    host = args.host
    if args.local:
        host = get_local_ip()
    
    print("🔐 Initialisation du serveur de messagerie sécurisée...")
    
    try:
        server = SecureMessagingServer(host, args.port)
        
        # Afficher les informations de connexion
        local_ip = get_local_ip()
        print(f"\\n💡 Informations de connexion:")
        print(f"   • Adresse locale: {local_ip}:{args.port}")
        print(f"   • Adresse d'écoute: {host}:{args.port}")
        print(f"\\n🔧 Pour connecter les clients:")
        print(f"   • Sur cette machine: 127.0.0.1:{args.port}")
        print(f"   • Sur le réseau local: {local_ip}:{args.port}")
        print()
        
        # Démarrer le serveur
        server.start()
        
    except KeyboardInterrupt:
        print("\\n👋 Arrêt du serveur demandé par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur critique: {e}")
        logger.error(f"Erreur critique: {e}", exc_info=True)
    finally:
        print("🔚 Serveur arrêté")


if __name__ == "__main__":
    main()