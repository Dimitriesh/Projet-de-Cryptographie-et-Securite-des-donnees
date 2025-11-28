#!/usr/bin/env python3
"""
Module de gestion de la base de données SQLite
============================================

Ce module contient toutes les fonctions nécessaires pour gérer la base de données
de l'application de messagerie sécurisée. Il gère les utilisateurs, les messages
et les conversations.

Author: Équipe de développement
Date: 2024
Version: 1.0
"""

import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Gestionnaire de base de données pour l'application de messagerie sécurisée.
    
    Cette classe encapsule toutes les opérations de base de données et fournit
    une interface simple pour interagir avec les données de l'application.
    
    Attributes:
        db_path (str): Chemin vers le fichier de base de données SQLite
        connection (sqlite3.Connection): Connexion active à la base de données
    """
    
    def __init__(self, db_path: str = 'secure_messaging.db'):
        """
        Initialise le gestionnaire de base de données.
        
        Args:
            db_path (str): Chemin vers le fichier de base de données
        """
        self.db_path = db_path
        self.connection = None
        self.connect()
        self.initialize_database()
    
    def connect(self) -> None:
        """
        Établit une connexion à la base de données SQLite.
        
        Raises:
            sqlite3.Error: En cas d'erreur de connexion
        """
        try:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row  # Pour accéder aux colonnes par nom
            logger.info(f"Connexion établie avec la base de données: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Erreur lors de la connexion à la base de données: {e}")
            raise
    
    @contextmanager
    def get_cursor(self):
        """
        Gestionnaire de contexte pour obtenir un curseur de base de données.
        
        Yields:
            sqlite3.Cursor: Curseur pour exécuter les requêtes SQL
        """
        if not self.connection:
            self.connect()
        
        cursor = self.connection.cursor()
        try:
            yield cursor
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Erreur lors de l'exécution de la requête: {e}")
            raise
        finally:
            cursor.close()
    
    def initialize_database(self) -> None:
        """
        Crée les tables nécessaires si elles n'existent pas.
        
        Tables créées:
        - users: Informations des utilisateurs
        - messages: Messages échangés entre utilisateurs
        - conversations: Métadonnées des conversations
        """
        with self.get_cursor() as cursor:
            # Table des utilisateurs
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    email TEXT PRIMARY KEY,
                    password_hash TEXT NOT NULL,
                    name TEXT NOT NULL,
                    birthday TEXT,
                    phone_number TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_login DATETIME
                )
            ''')
            
            # Table des messages
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender_email TEXT NOT NULL,
                    receiver_email TEXT NOT NULL,
                    content TEXT NOT NULL,
                    mac TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_read BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (sender_email) REFERENCES users(email),
                    FOREIGN KEY (receiver_email) REFERENCES users(email)
                )
            ''')
            
            # Table des conversations
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user1_email TEXT NOT NULL,
                    user2_email TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_message_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_message_id INTEGER,
                    UNIQUE(user1_email, user2_email),
                    FOREIGN KEY (user1_email) REFERENCES users(email),
                    FOREIGN KEY (user2_email) REFERENCES users(email),
                    FOREIGN KEY (last_message_id) REFERENCES messages(id)
                )
            ''')
            
            # Index pour améliorer les performances
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender_email)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_receiver ON messages(receiver_email)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversations_users ON conversations(user1_email, user2_email)')
            
            logger.info("Base de données initialisée avec succès")
    
    def create_user(self, email: str, password_hash: str, name: str, 
                   birthday: str = None, phone_number: str = None) -> bool:
        """
        Crée un nouvel utilisateur dans la base de données.
        
        Args:
            email (str): Adresse email de l'utilisateur (clé primaire)
            password_hash (str): Hash du mot de passe
            name (str): Nom complet de l'utilisateur
            birthday (str, optional): Date de naissance (format YYYY-MM-DD)
            phone_number (str, optional): Numéro de téléphone
            
        Returns:
            bool: True si l'utilisateur a été créé, False sinon
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute('''
                    INSERT INTO users (email, password_hash, name, birthday, phone_number)
                    VALUES (?, ?, ?, ?, ?)
                ''', (email, password_hash, name, birthday, phone_number))
                logger.info(f"Utilisateur créé: {email}")
                return True
        except sqlite3.IntegrityError:
            logger.warning(f"Tentative de création d'un utilisateur existant: {email}")
            return False
    
    def get_user(self, email: str) -> Optional[Dict]:
        """
        Récupère les informations d'un utilisateur par son email.
        
        Args:
            email (str): Adresse email de l'utilisateur
            
        Returns:
            Optional[Dict]: Dictionnaire contenant les informations de l'utilisateur
                          ou None si l'utilisateur n'existe pas
        """
        with self.get_cursor() as cursor:
            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()
            return dict(user) if user else None
    
    def authenticate_user(self, email: str, password_hash: str) -> bool:
        """
        Authentifie un utilisateur avec son email et mot de passe hashé.
        
        Args:
            email (str): Adresse email de l'utilisateur
            password_hash (str): Hash du mot de passe
            
        Returns:
            bool: True si l'authentification réussit, False sinon
        """
        with self.get_cursor() as cursor:
            cursor.execute(
                'SELECT email FROM users WHERE email = ? AND password_hash = ?',
                (email, password_hash)
            )
            result = cursor.fetchone()
            
            if result:
                # Mettre à jour la dernière connexion
                cursor.execute(
                    'UPDATE users SET last_login = ? WHERE email = ?',
                    (datetime.now().isoformat(), email)
                )
                logger.info(f"Authentification réussie pour: {email}")
                return True
            else:
                logger.warning(f"Échec d'authentification pour: {email}")
                return False
    
    def create_message(self, sender_email: str, receiver_email: str, 
                      content: str, mac: str, position: int) -> Optional[int]:
        """
        Enregistre un nouveau message dans la base de données.
        
        Args:
            sender_email (str): Email de l'expéditeur
            receiver_email (str): Email du destinataire
            content (str): Contenu du message
            mac (str): Code d'authentification du message
            position (int): Position du message dans la conversation
            
        Returns:
            Optional[int]: ID du message créé ou None en cas d'erreur
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute('''
                    INSERT INTO messages (sender_email, receiver_email, content, mac, position)
                    VALUES (?, ?, ?, ?, ?)
                ''', (sender_email, receiver_email, content, mac, position))
                
                message_id = cursor.lastrowid
                
                # Créer ou mettre à jour la conversation
                self._update_conversation(sender_email, receiver_email, message_id)
                
                logger.info(f"Message créé: {sender_email} -> {receiver_email}")
                return message_id
        except sqlite3.Error as e:
            logger.error(f"Erreur lors de la création du message: {e}")
            return None
    
    def get_conversation_messages(self, user1_email: str, user2_email: str) -> List[Dict]:
        """
        Récupère tous les messages d'une conversation entre deux utilisateurs.
        
        Args:
            user1_email (str): Email du premier utilisateur
            user2_email (str): Email du second utilisateur
            
        Returns:
            List[Dict]: Liste des messages de la conversation, triés par timestamp
        """
        with self.get_cursor() as cursor:
            cursor.execute('''
                SELECT id, sender_email, receiver_email, content, mac, position, timestamp, is_read
                FROM messages 
                WHERE (sender_email = ? AND receiver_email = ?) 
                   OR (sender_email = ? AND receiver_email = ?)
                ORDER BY timestamp ASC
            ''', (user1_email, user2_email, user2_email, user1_email))
            
            messages = cursor.fetchall()
            return [dict(message) for message in messages]
    
    def get_user_conversations(self, user_email: str) -> List[Dict]:
        """
        Récupère toutes les conversations d'un utilisateur.
        
        Args:
            user_email (str): Email de l'utilisateur
            
        Returns:
            List[Dict]: Liste des conversations triées par dernière activité
        """
        with self.get_cursor() as cursor:
            cursor.execute('''
                SELECT 
                    c.id,
                    CASE 
                        WHEN c.user1_email = ? THEN c.user2_email 
                        ELSE c.user1_email 
                    END as other_user_email,
                    u.name as other_user_name,
                    c.last_message_time,
                    m.content as last_message_content,
                    m.sender_email as last_message_sender
                FROM conversations c
                JOIN users u ON u.email = CASE 
                    WHEN c.user1_email = ? THEN c.user2_email 
                    ELSE c.user1_email 
                END
                LEFT JOIN messages m ON m.id = c.last_message_id
                WHERE c.user1_email = ? OR c.user2_email = ?
                ORDER BY c.last_message_time DESC
            ''', (user_email, user_email, user_email, user_email))
            
            conversations = cursor.fetchall()
            return [dict(conv) for conv in conversations]
    
    def mark_messages_as_read(self, user_email: str, other_user_email: str) -> None:
        """
        Marque tous les messages d'une conversation comme lus pour un utilisateur.
        
        Args:
            user_email (str): Email de l'utilisateur qui lit les messages
            other_user_email (str): Email de l'autre utilisateur de la conversation
        """
        with self.get_cursor() as cursor:
            cursor.execute('''
                UPDATE messages 
                SET is_read = TRUE 
                WHERE receiver_email = ? AND sender_email = ? AND is_read = FALSE
            ''', (user_email, other_user_email))
            logger.info(f"Messages marqués comme lus: {other_user_email} -> {user_email}")
    
    def get_unread_message_count(self, user_email: str, other_user_email: str) -> int:
        """
        Compte le nombre de messages non lus dans une conversation.
        
        Args:
            user_email (str): Email de l'utilisateur
            other_user_email (str): Email de l'autre utilisateur
            
        Returns:
            int: Nombre de messages non lus
        """
        with self.get_cursor() as cursor:
            cursor.execute('''
                SELECT COUNT(*) FROM messages 
                WHERE receiver_email = ? AND sender_email = ? AND is_read = FALSE
            ''', (user_email, other_user_email))
            return cursor.fetchone()[0]
    
    def _update_conversation(self, user1_email: str, user2_email: str, message_id: int) -> None:
        """
        Met à jour ou crée une conversation entre deux utilisateurs.
        
        Args:
            user1_email (str): Email du premier utilisateur
            user2_email (str): Email du second utilisateur
            message_id (int): ID du dernier message
        """
        # Ordonner les emails pour garantir l'unicité
        sorted_users = sorted([user1_email, user2_email])
        
        with self.get_cursor() as cursor:
            cursor.execute('''
                INSERT OR REPLACE INTO conversations 
                (user1_email, user2_email, last_message_time, last_message_id)
                VALUES (?, ?, ?, ?)
            ''', (sorted_users[0], sorted_users[1], datetime.now().isoformat(), message_id))
    
    def search_users(self, query: str) -> List[Dict]:
        """
        Recherche des utilisateurs par nom ou email.
        
        Args:
            query (str): Terme de recherche
            
        Returns:
            List[Dict]: Liste des utilisateurs correspondants
        """
        with self.get_cursor() as cursor:
            search_pattern = f"%{query}%"
            cursor.execute('''
                SELECT email, name FROM users 
                WHERE name LIKE ? OR email LIKE ?
                LIMIT 50
            ''', (search_pattern, search_pattern))
            
            users = cursor.fetchall()
            return [dict(user) for user in users]
    
    def get_message_by_id(self, message_id: int) -> Optional[Dict]:
        """
        Récupère un message par son ID.
        
        Args:
            message_id (int): ID du message
            
        Returns:
            Optional[Dict]: Dictionnaire du message ou None si non trouvé
        """
        with self.get_cursor() as cursor:
            cursor.execute('SELECT * FROM messages WHERE id = ?', (message_id,))
            message = cursor.fetchone()
            return dict(message) if message else None
    
    def close(self) -> None:
        """
        Ferme la connexion à la base de données.
        """
        if self.connection:
            self.connection.close()
            logger.info("Connexion à la base de données fermée")
    
    def __del__(self):
        """
        Destructeur pour s'assurer que la connexion est fermée.
        """
        self.close()


# Instance globale du gestionnaire de base de données
db_manager = DatabaseManager()

def get_db_manager() -> DatabaseManager:
    """
    Fonction utilitaire pour obtenir l'instance du gestionnaire de base de données.
    
    Returns:
        DatabaseManager: Instance du gestionnaire de base de données
    """
    return db_manager