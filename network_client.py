#!/usr/bin/env python3
"""
Client réseau pour la messagerie sécurisée en temps réel
======================================================

Ce module implémente la couche réseau du client qui se connecte au serveur
central via sockets TCP pour permettre la communication en temps réel.

Fonctionnalités:
- Connexion au serveur via sockets TCP
- Authentification sécurisée
- Envoi et réception de messages en temps réel
- Gestion des notifications
- Reconnexion automatique
- Communication asynchrone

Author: Équipe de développement
Date: 2024
Version: 1.0
"""

import socket
import json
import threading
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Callable
from queue import Queue, Empty

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NetworkClient")

class NetworkClient:
    """
    Client réseau pour la communication avec le serveur de messagerie.
    
    Cette classe gère la connexion TCP avec le serveur central et
    permet la communication bidirectionnelle en temps réel.
    
    Attributes:
        server_host (str): Adresse IP du serveur
        server_port (int): Port du serveur
        socket: Socket de connexion TCP
        is_connected: État de la connexion
        is_authenticated: État de l'authentification
        receive_thread: Thread de réception des messages
        message_queue: Queue des messages reçus
        callbacks: Callbacks pour différents types d'événements
    """
    
    def __init__(self, server_host: str = "127.0.0.1", server_port: int = 12345):
        """
        Initialise le client réseau.
        
        Args:
            server_host (str): Adresse IP du serveur
            server_port (int): Port du serveur
        """
        self.server_host = server_host
        self.server_port = server_port
        self.socket = None
        self.is_connected = False
        self.is_authenticated = False
        self.current_user = None
        
        # Threads et communication
        self.receive_thread = None
        self.is_running = False
        self.message_queue = Queue()
        
        # Callbacks pour les événements
        self.callbacks = {
            "on_message": None,
            "on_notification": None,
            "on_user_status": None,
            "on_connection_lost": None,
            "on_connected": None,
            "on_auth_success": None,
            "on_auth_failed": None
        }
        
        # Reconnexion automatique
        self.auto_reconnect = True
        self.reconnect_delay = 5  # secondes
        
        logger.info(f"Client initialisé pour {server_host}:{server_port}")
    
    def set_callback(self, event: str, callback: Callable):
        """
        Définit un callback pour un type d'événement.
        
        Args:
            event (str): Type d'événement (on_message, on_notification, etc.)
            callback (Callable): Fonction à appeler lors de l'événement
        """
        if event in self.callbacks:
            self.callbacks[event] = callback
            logger.debug(f"Callback défini pour {event}")
        else:
            logger.warning(f"Type d'événement non reconnu: {event}")
    
    def connect(self) -> bool:
        """
        Établit une connexion TCP avec le serveur.
        
        Returns:
            bool: True si la connexion réussit, False sinon
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)  # Timeout de 10 secondes
            self.socket.connect((self.server_host, self.server_port))
            
            self.is_connected = True
            self.is_running = True
            
            # Démarrer le thread de réception
            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receive_thread.start()
            
            logger.info(f"Connexion établie avec {self.server_host}:{self.server_port}")
            
            # Appeler le callback de connexion
            if self.callbacks["on_connected"]:
                self.callbacks["on_connected"]()
            
            return True
            
        except socket.error as e:
            logger.error(f"Erreur de connexion: {e}")
            self.is_connected = False
            return False
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la connexion: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """
        Ferme la connexion avec le serveur.
        """
        self.is_running = False
        self.is_connected = False
        self.is_authenticated = False
        self.auto_reconnect = False
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        
        logger.info("Déconnecté du serveur")
    
    def _receive_loop(self):
        """
        Boucle de réception des messages du serveur.
        Fonctionne dans un thread séparé.
        """
        while self.is_running and self.is_connected:
            try:
                # Recevoir les données
                data = self.socket.recv(4096)
                if not data:
                    logger.warning("Connexion fermée par le serveur")
                    break
                
                # Décoder et traiter le message
                try:
                    message = json.loads(data.decode('utf-8'))
                    self._process_received_message(message)
                except json.JSONDecodeError as e:
                    logger.error(f"Message JSON invalide reçu: {e}")
                
            except socket.timeout:
                continue
            except socket.error as e:
                if self.is_running:
                    logger.error(f"Erreur de réception: {e}")
                break
            except Exception as e:
                logger.error(f"Erreur inattendue dans la réception: {e}")
                break
        
        # Connexion perdue
        self._handle_connection_lost()
    
    def _process_received_message(self, message: dict):
        """
        Traite un message reçu du serveur.
        
        Args:
            message (dict): Message JSON reçu
        """
        msg_type = message.get("type")
        
        try:
            if msg_type == "auth_success":
                self.is_authenticated = True
                self.current_user = message.get("user", {}).get("email")
                logger.info("Authentification réussie")
                if self.callbacks["on_auth_success"]:
                    self.callbacks["on_auth_success"](message)
                # Mettre le message dans la queue pour _wait_for_response
                self.message_queue.put(message)
            
            elif msg_type == "auth_failed":
                self.is_authenticated = False
                logger.warning("Échec d'authentification")
                if self.callbacks["on_auth_failed"]:
                    self.callbacks["on_auth_failed"](message)
                # Mettre le message dans la queue pour _wait_for_response
                self.message_queue.put(message)
            
            elif msg_type == "new_message":
                logger.info(f"Nouveau message de {message.get('sender_email')}")
                if self.callbacks["on_message"]:
                    self.callbacks["on_message"](message)
            
            elif msg_type == "user_status":
                user_email = message.get("user_email")
                status = message.get("status")
                logger.debug(f"Statut utilisateur: {user_email} -> {status}")
                if self.callbacks["on_user_status"]:
                    self.callbacks["on_user_status"](message)
            
            elif msg_type in ["conversations", "messages", "search_results"]:
                # Réponses aux requêtes
                self.message_queue.put(message)
            
            elif msg_type == "error":
                logger.error(f"Erreur serveur: {message.get('message')}")
                self.message_queue.put(message)
            
            elif msg_type == "pong":
                # Réponse au ping
                pass
            
            else:
                logger.debug(f"Type de message non géré: {msg_type}")
                self.message_queue.put(message)
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement du message {msg_type}: {e}")
    
    def _handle_connection_lost(self):
        """
        Gère la perte de connexion avec le serveur.
        """
        logger.warning("Connexion perdue avec le serveur")
        self.is_connected = False
        self.is_authenticated = False
        
        # Appeler le callback de perte de connexion
        if self.callbacks["on_connection_lost"]:
            self.callbacks["on_connection_lost"]()
        
        # Tentative de reconnexion automatique
        if self.auto_reconnect:
            self._attempt_reconnection()
    
    def _attempt_reconnection(self):
        """
        Tente une reconnexion automatique au serveur.
        """
        logger.info("Tentative de reconnexion automatique...")
        
        retry_count = 0
        max_retries = 10
        
        while self.auto_reconnect and retry_count < max_retries:
            try:
                time.sleep(self.reconnect_delay)
                
                if self.connect():
                    logger.info("Reconnexion réussie")
                    return True
                
                retry_count += 1
                logger.info(f"Échec de reconnexion {retry_count}/{max_retries}")
                
            except Exception as e:
                logger.error(f"Erreur lors de la reconnexion: {e}")
                retry_count += 1
        
        logger.error("Échec de reconnexion après plusieurs tentatives")
        return False
    
    def send_message(self, message: dict) -> bool:
        """
        Envoie un message JSON au serveur.
        
        Args:
            message (dict): Message à envoyer
            
        Returns:
            bool: True si l'envoi réussit, False sinon
        """
        if not self.is_connected or not self.socket:
            logger.error("Pas de connexion active pour envoyer le message")
            return False
        
        try:
            json_data = json.dumps(message)
            self.socket.send(json_data.encode('utf-8'))
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du message: {e}")
            return False
    
    def authenticate(self, email: str, password: str) -> Optional[dict]:
        """
        Authentifie l'utilisateur auprès du serveur.
        
        Args:
            email (str): Email de l'utilisateur
            password (str): Mot de passe
            
        Returns:
            Optional[dict]: Réponse du serveur ou None si erreur
        """
        message = {
            "type": "authenticate",
            "email": email,
            "password": password
        }
        
        if self.send_message(message):
            # Attendre la réponse
            return self._wait_for_response(["auth_success", "auth_failed"], timeout=10)
        return None
    
    def register(self, email: str, password: str, name: str, 
                birthday: str = None, phone_number: str = None) -> Optional[dict]:
        """
        Inscrit un nouvel utilisateur.
        
        Args:
            email (str): Email
            password (str): Mot de passe
            name (str): Nom complet
            birthday (str, optional): Date de naissance
            phone_number (str, optional): Numéro de téléphone
            
        Returns:
            Optional[dict]: Réponse du serveur
        """
        message = {
            "type": "register",
            "email": email,
            "password": password,
            "name": name,
            "birthday": birthday,
            "phone_number": phone_number
        }
        
        if self.send_message(message):
            return self._wait_for_response(["registration_success", "registration_failed"], timeout=10)
        return None
    
    def send_chat_message(self, receiver_email: str, content: str) -> Optional[dict]:
        """
        Envoie un message de chat à un autre utilisateur.
        
        Args:
            receiver_email (str): Email du destinataire
            content (str): Contenu du message
            
        Returns:
            Optional[dict]: Réponse du serveur
        """
        if not self.is_authenticated:
            logger.error("Non authentifié pour envoyer des messages")
            return None
        
        message = {
            "type": "send_message",
            "receiver_email": receiver_email,
            "content": content
        }
        
        if self.send_message(message):
            return self._wait_for_response(["message_sent", "error"], timeout=5)
        return None
    
    def get_conversations(self) -> Optional[dict]:
        """
        Récupère la liste des conversations de l'utilisateur.
        
        Returns:
            Optional[dict]: Liste des conversations
        """
        if not self.is_authenticated:
            return None
        
        message = {"type": "get_conversations"}
        
        if self.send_message(message):
            return self._wait_for_response(["conversations"], timeout=5)
        return None
    
    def get_messages(self, other_user_email: str) -> Optional[dict]:
        """
        Récupère les messages d'une conversation.
        
        Args:
            other_user_email (str): Email de l'autre utilisateur
            
        Returns:
            Optional[dict]: Messages de la conversation
        """
        if not self.is_authenticated:
            return None
        
        message = {
            "type": "get_messages",
            "other_user_email": other_user_email
        }
        
        if self.send_message(message):
            return self._wait_for_response(["messages"], timeout=5)
        return None
    
    def search_users(self, query: str) -> Optional[dict]:
        """
        Recherche des utilisateurs.
        
        Args:
            query (str): Terme de recherche
            
        Returns:
            Optional[dict]: Résultats de recherche
        """
        if not self.is_authenticated:
            return None
        
        message = {
            "type": "search_users",
            "query": query
        }
        
        if self.send_message(message):
            return self._wait_for_response(["search_results"], timeout=5)
        return None
    
    def ping(self) -> bool:
        """
        Envoie un ping au serveur pour tester la connexion.
        
        Returns:
            bool: True si le serveur répond, False sinon
        """
        message = {"type": "ping"}
        
        if self.send_message(message):
            response = self._wait_for_response(["pong"], timeout=3)
            return response is not None
        return False
    
    def _wait_for_response(self, expected_types: List[str], timeout: int = 5) -> Optional[dict]:
        """
        Attend une réponse spécifique du serveur.
        
        Args:
            expected_types (List[str]): Types de messages attendus
            timeout (int): Timeout en secondes
            
        Returns:
            Optional[dict]: Message reçu ou None si timeout
        """
        start_time = time.time()
        
        # Vider d'abord la queue des anciens messages du bon type
        while not self.message_queue.empty():
            try:
                old_message = self.message_queue.get_nowait()
                if old_message.get("type") in expected_types:
                    return old_message
                # Remettre les autres messages
                self.message_queue.put(old_message)
                break  # Éviter une boucle infinie
            except Empty:
                break
        
        while time.time() - start_time < timeout:
            try:
                message = self.message_queue.get(timeout=0.1)
                if message.get("type") in expected_types:
                    return message
                else:
                    # Remettre le message dans la queue s'il ne correspond pas
                    self.message_queue.put(message)
            except Empty:
                continue
            except Exception as e:
                logger.error(f"Erreur lors de l'attente de réponse: {e}")
                break
        
        logger.warning(f"Timeout en attendant une réponse de type {expected_types}")
        return None
    
    def is_server_reachable(self) -> bool:
        """
        Vérifie si le serveur est accessible.
        
        Returns:
            bool: True si le serveur est accessible
        """
        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(3)
            result = test_socket.connect_ex((self.server_host, self.server_port))
            test_socket.close()
            return result == 0
        except:
            return False
    
    def get_connection_info(self) -> dict:
        """
        Retourne les informations de connexion.
        
        Returns:
            dict: Informations de connexion
        """
        return {
            "server_host": self.server_host,
            "server_port": self.server_port,
            "is_connected": self.is_connected,
            "is_authenticated": self.is_authenticated,
            "current_user": self.current_user,
            "auto_reconnect": self.auto_reconnect
        }


def test_connection(host: str = "127.0.0.1", port: int = 12345) -> bool:
    """
    Teste la connexion avec le serveur.
    
    Args:
        host (str): Adresse du serveur
        port (int): Port du serveur
        
    Returns:
        bool: True si la connexion est possible
    """
    try:
        client = NetworkClient(host, port)
        return client.is_server_reachable()
    except:
        return False


if __name__ == "__main__":
    # Test simple du client
    import argparse
    
    parser = argparse.ArgumentParser(description="Test du client réseau")
    parser.add_argument("--host", default="127.0.0.1", help="Adresse du serveur")
    parser.add_argument("--port", type=int, default=12345, help="Port du serveur")
    parser.add_argument("--test", action="store_true", help="Tester la connexion")
    
    args = parser.parse_args()
    
    if args.test:
        print(f"Test de connexion à {args.host}:{args.port}...")
        if test_connection(args.host, args.port):
            print("✅ Serveur accessible")
        else:
            print("❌ Serveur non accessible")
    else:
        # Test interactif basique
        client = NetworkClient(args.host, args.port)
        
        if client.connect():
            print("✅ Connexion établie")
            
            # Test ping
            if client.ping():
                print("✅ Ping successful")
            else:
                print("❌ Ping failed")
            
            client.disconnect()
        else:
            print("❌ Connexion impossible")