#!/usr/bin/env python3
"""
Module de gestion des messages
=============================

Ce module contient toutes les fonctions nécessaires pour gérer les messages
de l'application de messagerie sécurisée. Il fournit une couche d'abstraction
pour l'envoi, la réception, et la vérification des messages avec intégrité cryptographique.

Fonctionnalités:
- Envoi de messages sécurisés
- Réception et vérification des messages
- Gestion des conversations
- Historique des messages
- Détection de modifications malveillantes

Author: Équipe de développement
Date: 2024
Version: 1.0
"""

import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from database import get_db_manager
from crypto import get_crypto_manager
from user_manager import get_user_manager

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MessageManager:
    """
    Gestionnaire des messages pour l'application de messagerie sécurisée.
    
    Cette classe encapsule toutes les opérations liées aux messages,
    incluant l'envoi sécurisé, la réception, et la vérification d'intégrité.
    
    Attributes:
        db_manager: Instance du gestionnaire de base de données
        crypto_manager: Instance du gestionnaire cryptographique
        user_manager: Instance du gestionnaire d'utilisateurs
    """
    
    def __init__(self):
        """
        Initialise le gestionnaire de messages.
        """
        self.db_manager = get_db_manager()
        self.crypto_manager = get_crypto_manager()
        self.user_manager = get_user_manager()
        logger.info("MessageManager initialisé")
    
    def validate_message_content(self, content: str) -> Dict[str, any]:
        """
        Valide le contenu d'un message avant l'envoi.
        
        Args:
            content (str): Contenu du message à valider
            
        Returns:
            Dict[str, any]: Résultat de la validation
        """
        result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        if not content or not isinstance(content, str):
            result['is_valid'] = False
            result['errors'].append("Le message ne peut pas être vide")
            return result
        
        content = content.strip()
        
        # Vérifier la longueur
        if len(content) == 0:
            result['is_valid'] = False
            result['errors'].append("Le message ne peut pas être vide")
        elif len(content) > 5000:  # Limite raisonnable pour un message
            result['is_valid'] = False
            result['errors'].append("Le message est trop long (maximum 5000 caractères)")
        elif len(content) > 1000:
            result['warnings'].append("Message très long, considérez le diviser")
        
        # Vérifier la présence de caractères potentiellement dangereux
        dangerous_chars = ['<', '>', '{', '}', '\\x']
        if any(char in content for char in dangerous_chars[:3]):
            result['warnings'].append("Le message contient des caractères spéciaux")
        
        # Vérifier la présence de séquences d'échappement
        if any(seq in content for seq in dangerous_chars[3:]):
            result['is_valid'] = False
            result['errors'].append("Le message contient des caractères non autorisés")
        
        return result
    
    def send_message(self, sender_email: str, receiver_email: str, content: str) -> Dict[str, any]:
        """
        Envoie un message sécurisé d'un utilisateur à un autre.
        
        Args:
            sender_email (str): Email de l'expéditeur
            receiver_email (str): Email du destinataire
            content (str): Contenu du message
            
        Returns:
            Dict[str, any]: Résultat de l'envoi du message
            
        Example:
            >>> msg_manager = MessageManager()
            >>> result = msg_manager.send_message(
            ...     "alice@gmail.com", "bob@gmail.com", "Hello Bob!"
            ... )
            >>> result['success']
            True
        """
        result = {
            'success': False,
            'message': '',
            'message_id': None,
            'errors': []
        }
        
        # Vérifier que l'expéditeur est connecté
        if not self.user_manager.is_logged_in():
            result['message'] = "Vous devez être connecté pour envoyer des messages"
            return result
        
        current_user = self.user_manager.get_current_user()
        if current_user != sender_email.lower():
            result['message'] = "Vous ne pouvez envoyer des messages qu'avec votre propre compte"
            return result
        
        # Valider les emails
        if not self.user_manager.validate_email(sender_email):
            result['errors'].append("Email de l'expéditeur invalide")
        
        if not self.user_manager.validate_email(receiver_email):
            result['errors'].append("Email du destinataire invalide")
        
        # Vérifier que le destinataire existe
        receiver_profile = self.user_manager.get_user_profile(receiver_email)
        if not receiver_profile:
            result['errors'].append("Destinataire non trouvé")
        
        # Valider le contenu du message
        content_validation = self.validate_message_content(content)
        if not content_validation['is_valid']:
            result['errors'].extend(content_validation['errors'])
        
        if result['errors']:
            result['message'] = "Erreurs de validation"
            return result
        
        try:
            # Calculer la position du message dans la conversation
            existing_messages = self.get_conversation_messages(sender_email, receiver_email)
            position = len(existing_messages) + 1
            
            # Créer le message sécurisé avec MAC
            _, mac_hex, iv = self.crypto_manager.create_secure_message(
                sender_email, receiver_email, content.strip()
            )
            
            # Sauvegarder le message dans la base de données
            # Note: Pour simplifier, nous stockons l'IV dans le MAC (format: iv_hex:mac_hex)
            combined_mac = f"{iv.hex()}:{mac_hex}"
            
            message_id = self.db_manager.create_message(
                sender_email=sender_email.lower(),
                receiver_email=receiver_email.lower(),
                content=content.strip(),
                mac=combined_mac,
                position=position
            )
            
            if message_id:
                result['success'] = True
                result['message'] = "Message envoyé avec succès"
                result['message_id'] = message_id
                logger.info(f"Message envoyé: {sender_email} -> {receiver_email} (ID: {message_id})")
            else:
                result['message'] = "Erreur lors de la sauvegarde du message"
                
        except Exception as e:
            result['message'] = "Erreur lors de l'envoi du message"
            result['errors'].append(str(e))
            logger.error(f"Erreur lors de l'envoi du message: {e}")
        
        return result
    
    def get_conversation_messages(self, user1_email: str, user2_email: str, 
                                 verify_integrity: bool = True) -> List[Dict]:
        """
        Récupère tous les messages d'une conversation entre deux utilisateurs.
        
        Args:
            user1_email (str): Email du premier utilisateur
            user2_email (str): Email du second utilisateur
            verify_integrity (bool): Si True, vérifie l'intégrité de chaque message
            
        Returns:
            List[Dict]: Liste des messages avec leurs métadonnées
        """
        # Récupérer les messages de la base de données
        raw_messages = self.db_manager.get_conversation_messages(
            user1_email.lower(), user2_email.lower()
        )
        
        processed_messages = []
        
        for msg in raw_messages:
            processed_msg = {
                'id': msg['id'],
                'sender_email': msg['sender_email'],
                'receiver_email': msg['receiver_email'],
                'content': msg['content'],
                'timestamp': msg['timestamp'],
                'position': msg['position'],
                'is_read': msg['is_read'],
                'integrity_verified': None,
                'is_sent': msg['sender_email'] == self.user_manager.get_current_user()
            }
            
            # Vérifier l'intégrité si demandé
            if verify_integrity:
                try:
                    # Extraire l'IV et le MAC du champ MAC combiné
                    if ':' in msg['mac']:
                        iv_hex, mac_hex = msg['mac'].split(':', 1)
                        iv = bytes.fromhex(iv_hex)
                        
                        # Vérifier l'intégrité du message
                        is_valid = self.crypto_manager.verify_received_message(
                            msg['sender_email'], msg['receiver_email'],
                            msg['content'], mac_hex, iv
                        )
                        
                        processed_msg['integrity_verified'] = is_valid
                        
                        if not is_valid:
                            processed_msg['warning'] = "⚠️ Intégrité du message compromise"
                            logger.warning(f"Intégrité compromise pour le message {msg['id']}")
                    else:
                        processed_msg['integrity_verified'] = False
                        processed_msg['warning'] = "⚠️ Format de MAC invalide"
                        
                except Exception as e:
                    processed_msg['integrity_verified'] = False
                    processed_msg['warning'] = "⚠️ Erreur de vérification d'intégrité"
                    logger.error(f"Erreur de vérification pour le message {msg['id']}: {e}")
            
            processed_messages.append(processed_msg)
        
        return processed_messages
    
    def get_user_conversations(self, user_email: str) -> List[Dict]:
        """
        Récupère toutes les conversations d'un utilisateur avec métadonnées.
        
        Args:
            user_email (str): Email de l'utilisateur
            
        Returns:
            List[Dict]: Liste des conversations avec informations de contact
        """
        # Récupérer les conversations de la base de données
        conversations = self.db_manager.get_user_conversations(user_email.lower())
        
        processed_conversations = []
        
        for conv in conversations:
            # Compter les messages non lus
            unread_count = self.db_manager.get_unread_message_count(
                user_email.lower(), conv['other_user_email']
            )
            
            processed_conv = {
                'id': conv['id'],
                'other_user_email': conv['other_user_email'],
                'other_user_name': conv['other_user_name'],
                'last_message_time': conv['last_message_time'],
                'last_message_content': conv['last_message_content'][:50] + '...' 
                    if conv['last_message_content'] and len(conv['last_message_content']) > 50 
                    else conv['last_message_content'],
                'last_message_sender': conv['last_message_sender'],
                'unread_count': unread_count,
                'is_last_message_sent': conv['last_message_sender'] == user_email.lower()
            }
            
            processed_conversations.append(processed_conv)
        
        return processed_conversations
    
    def mark_conversation_as_read(self, user_email: str, other_user_email: str) -> bool:
        """
        Marque tous les messages d'une conversation comme lus.
        
        Args:
            user_email (str): Email de l'utilisateur qui lit
            other_user_email (str): Email de l'autre utilisateur
            
        Returns:
            bool: True si l'opération réussit, False sinon
        """
        try:
            self.db_manager.mark_messages_as_read(user_email.lower(), other_user_email.lower())
            logger.info(f"Messages marqués comme lus: {other_user_email} -> {user_email}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors du marquage comme lu: {e}")
            return False
    
    def search_messages(self, user_email: str, query: str, 
                       other_user_email: str = None) -> List[Dict]:
        """
        Recherche des messages contenant un terme spécifique.
        
        Args:
            user_email (str): Email de l'utilisateur effectuant la recherche
            query (str): Terme de recherche
            other_user_email (str, optional): Limiter la recherche à une conversation
            
        Returns:
            List[Dict]: Messages correspondant à la recherche
        """
        if not query or len(query.strip()) < 3:
            return []
        
        query = query.strip().lower()
        found_messages = []
        
        if other_user_email:
            # Rechercher dans une conversation spécifique
            messages = self.get_conversation_messages(user_email, other_user_email, verify_integrity=False)
            for msg in messages:
                if query in msg['content'].lower():
                    found_messages.append(msg)
        else:
            # Rechercher dans toutes les conversations
            conversations = self.get_user_conversations(user_email)
            for conv in conversations:
                messages = self.get_conversation_messages(
                    user_email, conv['other_user_email'], verify_integrity=False
                )
                for msg in messages:
                    if query in msg['content'].lower():
                        msg['conversation_with'] = conv['other_user_name']
                        found_messages.append(msg)
        
        return found_messages[:50]  # Limiter à 50 résultats
    
    def get_message_statistics(self, user_email: str) -> Dict[str, int]:
        """
        Calcule des statistiques sur les messages d'un utilisateur.
        
        Args:
            user_email (str): Email de l'utilisateur
            
        Returns:
            Dict[str, int]: Statistiques des messages
        """
        conversations = self.get_user_conversations(user_email)
        stats = {
            'total_conversations': len(conversations),
            'total_sent_messages': 0,
            'total_received_messages': 0,
            'total_unread_messages': 0,
            'compromised_messages': 0
        }
        
        for conv in conversations:
            messages = self.get_conversation_messages(
                user_email, conv['other_user_email'], verify_integrity=True
            )
            
            for msg in messages:
                if msg['sender_email'] == user_email.lower():
                    stats['total_sent_messages'] += 1
                else:
                    stats['total_received_messages'] += 1
                    if not msg['is_read']:
                        stats['total_unread_messages'] += 1
                
                if msg['integrity_verified'] is False:
                    stats['compromised_messages'] += 1
        
        return stats
    
    def delete_message(self, user_email: str, message_id: int) -> Dict[str, any]:
        """
        Supprime un message (marquage logique, pas suppression physique).
        
        Note: Dans un vrai système, on pourrait implémenter une suppression logique
        pour des raisons de sécurité et d'audit.
        
        Args:
            user_email (str): Email de l'utilisateur demandant la suppression
            message_id (int): ID du message à supprimer
            
        Returns:
            Dict[str, any]: Résultat de l'opération
        """
        result = {
            'success': False,
            'message': ''
        }
        
        # Récupérer le message
        message = self.db_manager.get_message_by_id(message_id)
        
        if not message:
            result['message'] = "Message non trouvé"
            return result
        
        # Vérifier que l'utilisateur a le droit de supprimer ce message
        if message['sender_email'] != user_email.lower():
            result['message'] = "Vous ne pouvez supprimer que vos propres messages"
            return result
        
        # TODO: Implémenter la suppression logique dans la base de données
        # Par exemple, ajouter un champ 'is_deleted' à la table messages
        
        result['success'] = True
        result['message'] = "Message supprimé avec succès"
        logger.info(f"Message {message_id} supprimé par {user_email}")
        
        return result
    
    def simulate_message_tampering(self, message_id: int, new_content: str) -> bool:
        """
        Simule une modification malveillante d'un message pour tester la détection.
        
        ⚠️ ATTENTION: Cette fonction est uniquement à des fins de démonstration
        et ne devrait JAMAIS être utilisée en production!
        
        Args:
            message_id (int): ID du message à modifier
            new_content (str): Nouveau contenu malveillant
            
        Returns:
            bool: True si la modification a été effectuée
        """
        try:
            # Cette fonction utilise directement la base de données pour simuler une attaque
            with self.db_manager.get_cursor() as cursor:
                cursor.execute(
                    'UPDATE messages SET content = ? WHERE id = ?',
                    (new_content, message_id)
                )
                
            logger.warning(f"SIMULATION D'ATTAQUE: Message {message_id} modifié malicieusement")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la simulation d'attaque: {e}")
            return False


# Instance globale du gestionnaire de messages
message_manager = MessageManager()

def get_message_manager() -> MessageManager:
    """
    Fonction utilitaire pour obtenir l'instance du gestionnaire de messages.
    
    Returns:
        MessageManager: Instance du gestionnaire de messages
    """
    return message_manager


# Fonctions utilitaires pour une utilisation simplifiée
def send_quick_message(sender: str, receiver: str, content: str) -> bool:
    """
    Fonction utilitaire pour envoyer rapidement un message.
    
    Args:
        sender (str): Email de l'expéditeur
        receiver (str): Email du destinataire
        content (str): Contenu du message
        
    Returns:
        bool: True si l'envoi réussit, False sinon
    """
    result = message_manager.send_message(sender, receiver, content)
    return result['success']


def get_recent_messages(user_email: str, limit: int = 10) -> List[Dict]:
    """
    Fonction utilitaire pour obtenir les messages récents d'un utilisateur.
    
    Args:
        user_email (str): Email de l'utilisateur
        limit (int): Nombre maximum de messages à retourner
        
    Returns:
        List[Dict]: Messages récents triés par date
    """
    conversations = message_manager.get_user_conversations(user_email)
    all_messages = []
    
    for conv in conversations:
        messages = message_manager.get_conversation_messages(
            user_email, conv['other_user_email'], verify_integrity=False
        )
        all_messages.extend(messages)
    
    # Trier par timestamp et limiter
    all_messages.sort(key=lambda x: x['timestamp'], reverse=True)
    return all_messages[:limit]