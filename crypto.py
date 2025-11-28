#!/usr/bin/env python3
"""
Module de cryptographie pour la messagerie sécurisée
==================================================

Ce module contient toutes les fonctions cryptographiques nécessaires pour
garantir l'intégrité et l'authentification des messages. Il implémente
le CBC-MAC avec AES pour l'authentification des messages.

Fonctionnalités:
- Calcul du CBC-MAC
- Génération de clés partagées
- Padding des messages
- Vérification d'intégrité

Author: Équipe de développement
Date: 2024
Version: 1.0

Sécurité:
Ce module utilise des algorithmes cryptographiques reconnus et des
bibliothèques sécurisées pour garantir la protection des données.
"""

import hashlib
import secrets
import logging
from typing import Tuple, Union
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CryptoManager:
    """
    Gestionnaire des opérations cryptographiques pour la messagerie sécurisée.
    
    Cette classe encapsule toutes les opérations de cryptographie nécessaires
    pour sécuriser les communications entre utilisateurs.
    
    Constants:
        BLOCK_SIZE (int): Taille des blocs AES (16 octets)
        KEY_SIZE (int): Taille des clés AES (32 octets pour AES-256)
        IV_SIZE (int): Taille du vecteur d'initialisation (16 octets)
    """
    
    BLOCK_SIZE = 16  # AES block size in bytes
    KEY_SIZE = 32    # AES-256 key size in bytes
    IV_SIZE = 16     # Initialization vector size in bytes
    
    def __init__(self):
        """
        Initialise le gestionnaire cryptographique.
        """
        logger.info("CryptoManager initialisé avec AES-256 et CBC-MAC")
    
    def generate_shared_key(self, user1_email: str, user2_email: str) -> bytes:
        """
        Génère une clé partagée déterministe basée sur les emails des utilisateurs.
        
        Cette méthode génère une clé partagée en utilisant SHA-256 sur la
        concaténation ordonnée des emails. Cela garantit que les deux
        utilisateurs obtiennent la même clé pour leur conversation.
        
        Args:
            user1_email (str): Email du premier utilisateur
            user2_email (str): Email du second utilisateur
            
        Returns:
            bytes: Clé partagée de 32 octets (256 bits)
            
        Note:
            Les emails sont triés alphabétiquement pour garantir que
            generate_shared_key(A, B) == generate_shared_key(B, A)
        """
        # Trier les emails pour garantir la consistance
        sorted_emails = sorted([user1_email.lower(), user2_email.lower()])
        key_material = (''.join(sorted_emails)).encode('utf-8')
        
        # Générer la clé avec SHA-256
        key = hashlib.sha256(key_material).digest()
        
        logger.debug(f"Clé partagée générée pour: {sorted_emails[0]} <-> {sorted_emails[1]}")
        return key
    
    def pad_message(self, message: bytes) -> bytes:
        """
        Applique un padding PKCS7 au message pour s'adapter à la taille des blocs.
        
        Le padding PKCS7 ajoute des octets à la fin du message pour que sa
        taille soit un multiple de la taille des blocs AES (16 octets).
        
        Args:
            message (bytes): Message à padder
            
        Returns:
            bytes: Message avec padding appliqué
            
        Example:
            >>> crypto = CryptoManager()
            >>> message = b"Hello"
            >>> padded = crypto.pad_message(message)
            >>> len(padded) % 16 == 0
            True
        """
        if not isinstance(message, bytes):
            raise TypeError("Le message doit être de type bytes")
        
        pad_length = self.BLOCK_SIZE - (len(message) % self.BLOCK_SIZE)
        padding = bytes([pad_length]) * pad_length
        
        return message + padding
    
    def unpad_message(self, padded_message: bytes) -> bytes:
        """
        Supprime le padding PKCS7 d'un message.
        
        Args:
            padded_message (bytes): Message avec padding
            
        Returns:
            bytes: Message original sans padding
            
        Raises:
            ValueError: Si le padding est invalide
        """
        if not isinstance(padded_message, bytes):
            raise TypeError("Le message doit être de type bytes")
        
        if len(padded_message) == 0 or len(padded_message) % self.BLOCK_SIZE != 0:
            raise ValueError("Taille de message invalide pour le dépadding")
        
        pad_length = padded_message[-1]
        
        if pad_length > self.BLOCK_SIZE:
            raise ValueError("Longueur de padding invalide")
        
        # Vérifier que tous les octets de padding sont corrects
        padding = padded_message[-pad_length:]
        if not all(b == pad_length for b in padding):
            raise ValueError("Padding PKCS7 invalide")
        
        return padded_message[:-pad_length]
    
    def generate_iv(self) -> bytes:
        """
        Génère un vecteur d'initialisation (IV) cryptographiquement sécurisé.
        
        Returns:
            bytes: IV aléatoire de 16 octets
        """
        return secrets.token_bytes(self.IV_SIZE)
    
    def calculate_cbc_mac(self, key: bytes, message: bytes, iv: bytes) -> bytes:
        """
        Calcule le CBC-MAC d'un message en utilisant AES.
        
        Le CBC-MAC (Cipher Block Chaining Message Authentication Code) est
        calculé en chiffrant le message en mode CBC et en prenant le dernier
        bloc chiffré comme MAC.
        
        Args:
            key (bytes): Clé de chiffrement (32 octets pour AES-256)
            message (bytes): Message à authentifier
            iv (bytes): Vecteur d'initialisation (16 octets)
            
        Returns:
            bytes: CBC-MAC du message (16 octets)
            
        Raises:
            ValueError: Si les paramètres ont une taille invalide
            
        Example:
            >>> crypto = CryptoManager()
            >>> key = crypto.generate_shared_key("user1@email.com", "user2@email.com")
            >>> message = b"Message secret"
            >>> iv = crypto.generate_iv()
            >>> mac = crypto.calculate_cbc_mac(key, message, iv)
            >>> len(mac) == 16
            True
        """
        if len(key) != self.KEY_SIZE:
            raise ValueError(f"La clé doit faire {self.KEY_SIZE} octets")
        
        if len(iv) != self.IV_SIZE:
            raise ValueError(f"L'IV doit faire {self.IV_SIZE} octets")
        
        if not isinstance(message, bytes):
            raise TypeError("Le message doit être de type bytes")
        
        # Appliquer le padding au message
        padded_message = self.pad_message(message)
        
        # Créer le chiffreur AES en mode CBC
        cipher = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        # Chiffrer le message
        ciphertext = encryptor.update(padded_message) + encryptor.finalize()
        
        # Le MAC est le dernier bloc du texte chiffré
        mac = ciphertext[-self.BLOCK_SIZE:]
        
        logger.debug(f"CBC-MAC calculé pour un message de {len(message)} octets")
        return mac
    
    def verify_message_integrity(self, key: bytes, message: bytes, 
                                iv: bytes, expected_mac: bytes) -> bool:
        """
        Vérifie l'intégrité d'un message en comparant son MAC.
        
        Args:
            key (bytes): Clé de chiffrement
            message (bytes): Message à vérifier
            iv (bytes): Vecteur d'initialisation utilisé
            expected_mac (bytes): MAC attendu
            
        Returns:
            bool: True si l'intégrité est vérifiée, False sinon
        """
        try:
            calculated_mac = self.calculate_cbc_mac(key, message, iv)
            
            # Comparaison sécurisée contre les attaques temporelles
            return secrets.compare_digest(calculated_mac, expected_mac)
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification d'intégrité: {e}")
            return False
    
    def create_secure_message(self, sender_email: str, receiver_email: str, 
                             content: str) -> Tuple[str, str, bytes]:
        """
        Crée un message sécurisé avec son MAC.
        
        Args:
            sender_email (str): Email de l'expéditeur
            receiver_email (str): Email du destinataire
            content (str): Contenu du message
            
        Returns:
            Tuple[str, str, bytes]: (contenu, MAC en hex, IV utilisé)
        """
        if not content.strip():
            raise ValueError("Le contenu du message ne peut pas être vide")
        
        # Générer la clé partagée
        shared_key = self.generate_shared_key(sender_email, receiver_email)
        
        # Générer un IV aléatoire
        iv = self.generate_iv()
        
        # Convertir le contenu en bytes
        message_bytes = content.encode('utf-8')
        
        # Calculer le MAC
        mac = self.calculate_cbc_mac(shared_key, message_bytes, iv)
        
        logger.info(f"Message sécurisé créé: {sender_email} -> {receiver_email}")
        return content, mac.hex(), iv
    
    def verify_received_message(self, sender_email: str, receiver_email: str,
                               content: str, mac_hex: str, iv: bytes) -> bool:
        """
        Vérifie un message reçu en validant son MAC.
        
        Args:
            sender_email (str): Email de l'expéditeur
            receiver_email (str): Email du destinataire
            content (str): Contenu du message
            mac_hex (str): MAC en représentation hexadécimale
            iv (bytes): Vecteur d'initialisation utilisé
            
        Returns:
            bool: True si le message est authentique, False sinon
        """
        try:
            # Reconstituer la clé partagée
            shared_key = self.generate_shared_key(sender_email, receiver_email)
            
            # Convertir le MAC hex en bytes
            expected_mac = bytes.fromhex(mac_hex)
            
            # Convertir le contenu en bytes
            message_bytes = content.encode('utf-8')
            
            # Vérifier l'intégrité
            is_valid = self.verify_message_integrity(
                shared_key, message_bytes, iv, expected_mac
            )
            
            if is_valid:
                logger.info(f"Message vérifié avec succès: {sender_email} -> {receiver_email}")
            else:
                logger.warning(f"Échec de vérification du message: {sender_email} -> {receiver_email}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du message: {e}")
            return False
    
    def hash_password(self, password: str, salt: bytes = None) -> Tuple[str, bytes]:
        """
        Hache un mot de passe avec un sel pour le stockage sécurisé.
        
        Args:
            password (str): Mot de passe en clair
            salt (bytes, optional): Sel à utiliser. Si None, un nouveau sel est généré
            
        Returns:
            Tuple[str, bytes]: (hash hexadécimal, sel utilisé)
        """
        if salt is None:
            salt = secrets.token_bytes(32)
        
        # Utiliser PBKDF2 avec SHA-256 pour le hachage
        from hashlib import pbkdf2_hmac
        
        password_bytes = password.encode('utf-8')
        hash_bytes = pbkdf2_hmac('sha256', password_bytes, salt, 100000)
        
        return hash_bytes.hex(), salt
    
    def verify_password(self, password: str, hash_hex: str, salt: bytes) -> bool:
        """
        Vérifie un mot de passe contre son hash.
        
        Args:
            password (str): Mot de passe en clair à vérifier
            hash_hex (str): Hash stocké en hexadécimal
            salt (bytes): Sel utilisé pour le hachage
            
        Returns:
            bool: True si le mot de passe est correct, False sinon
        """
        try:
            calculated_hash, _ = self.hash_password(password, salt)
            return secrets.compare_digest(calculated_hash, hash_hex)
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du mot de passe: {e}")
            return False


# Instance globale du gestionnaire cryptographique
crypto_manager = CryptoManager()

def get_crypto_manager() -> CryptoManager:
    """
    Fonction utilitaire pour obtenir l'instance du gestionnaire cryptographique.
    
    Returns:
        CryptoManager: Instance du gestionnaire cryptographique
    """
    return crypto_manager


# Fonctions utilitaires pour une utilisation simplifiée
def create_message_mac(sender_email: str, receiver_email: str, content: str) -> Tuple[str, bytes]:
    """
    Fonction utilitaire pour créer rapidement un MAC pour un message.
    
    Args:
        sender_email (str): Email de l'expéditeur
        receiver_email (str): Email du destinataire
        content (str): Contenu du message
        
    Returns:
        Tuple[str, bytes]: (MAC en hex, IV utilisé)
    """
    _, mac_hex, iv = crypto_manager.create_secure_message(sender_email, receiver_email, content)
    return mac_hex, iv


def verify_message_mac(sender_email: str, receiver_email: str, content: str, 
                      mac_hex: str, iv: bytes) -> bool:
    """
    Fonction utilitaire pour vérifier rapidement un MAC de message.
    
    Args:
        sender_email (str): Email de l'expéditeur
        receiver_email (str): Email du destinataire
        content (str): Contenu du message
        mac_hex (str): MAC en hexadécimal
        iv (bytes): Vecteur d'initialisation
        
    Returns:
        bool: True si la vérification réussit, False sinon
    """
    return crypto_manager.verify_received_message(
        sender_email, receiver_email, content, mac_hex, iv
    )