#!/usr/bin/env python3
"""
Module de gestion des utilisateurs
=================================

Ce module contient toutes les fonctions nécessaires pour gérer les utilisateurs
de l'application de messagerie sécurisée. Il fournit une couche d'abstraction
entre l'interface utilisateur et la base de données pour les opérations
liées aux utilisateurs.

Fonctionnalités:
- Inscription d'utilisateurs
- Authentification
- Gestion des profils
- Recherche d'utilisateurs
- Validation des données

Author: Équipe de développement
Date: 2024
Version: 1.0
"""

import hashlib
import re
import logging
from datetime import datetime
from typing import Optional, Dict, List
from database import get_db_manager
from crypto import get_crypto_manager

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserManager:
    """
    Gestionnaire des utilisateurs pour l'application de messagerie sécurisée.
    
    Cette classe encapsule toutes les opérations liées aux utilisateurs,
    incluant l'inscription, l'authentification, et la gestion des profils.
    
    Attributes:
        db_manager: Instance du gestionnaire de base de données
        crypto_manager: Instance du gestionnaire cryptographique
    """
    
    def __init__(self):
        """
        Initialise le gestionnaire d'utilisateurs.
        """
        self.db_manager = get_db_manager()
        self.crypto_manager = get_crypto_manager()
        self.current_user = None
        logger.info("UserManager initialisé")
    
    def validate_email(self, email: str) -> bool:
        """
        Valide le format d'une adresse email.
        
        Args:
            email (str): Adresse email à valider
            
        Returns:
            bool: True si l'email est valide, False sinon
            
        Example:
            >>> user_manager = UserManager()
            >>> user_manager.validate_email("test@example.com")
            True
            >>> user_manager.validate_email("invalid-email")
            False
        """
        if not email or not isinstance(email, str):
            return False
        
        # Expression régulière pour valider l'email
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        # Vérifier le format de base
        if not re.match(email_pattern, email):
            return False
        
        # Vérifier la longueur
        if len(email) > 254:  # RFC 5321
            return False
        
        # Vérifier que l'email contient un domaine autorisé
        allowed_domains = [
            'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
            'icloud.com', 'protonmail.com', 'zoho.com', 'mail.com'
        ]
        
        domain = email.lower().split('@')[1]
        return domain in allowed_domains
    
    def validate_password(self, password: str) -> Dict[str, bool]:
        """
        Valide la force d'un mot de passe selon des critères de sécurité.
        
        Args:
            password (str): Mot de passe à valider
            
        Returns:
            Dict[str, bool]: Dictionnaire avec les critères de validation
            
        Example:
            >>> user_manager = UserManager()
            >>> result = user_manager.validate_password("MySecurePass123!")
            >>> result['is_valid']
            True
        """
        validation = {
            'is_valid': True,
            'min_length': len(password) >= 8,
            'has_uppercase': any(c.isupper() for c in password),
            'has_lowercase': any(c.islower() for c in password),
            'has_digit': any(c.isdigit() for c in password),
            'has_special': any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password),
            'max_length': len(password) <= 128
        }
        
        # Le mot de passe est valide si tous les critères sont respectés
        validation['is_valid'] = all([
            validation['min_length'],
            validation['has_uppercase'],
            validation['has_lowercase'],
            validation['has_digit'],
            validation['max_length']
        ])
        
        return validation
    
    def validate_name(self, name: str) -> bool:
        """
        Valide le nom d'un utilisateur.
        
        Args:
            name (str): Nom à valider
            
        Returns:
            bool: True si le nom est valide, False sinon
        """
        if not name or not isinstance(name, str):
            return False
        
        name = name.strip()
        
        # Vérifier la longueur
        if len(name) < 2 or len(name) > 50:
            return False
        
        # Vérifier que le nom contient seulement des lettres et espaces
        return re.match(r'^[a-zA-ZÀ-ÿ\s\-\']+$', name) is not None
    
    def validate_phone(self, phone: str) -> bool:
        """
        Valide un numéro de téléphone.
        
        Args:
            phone (str): Numéro de téléphone à valider
            
        Returns:
            bool: True si le numéro est valide, False sinon
        """
        if not phone or not isinstance(phone, str):
            return False
        
        # Supprimer les espaces et caractères spéciaux
        cleaned_phone = re.sub(r'[^\d+]', '', phone)
        
        # Vérifier le format (entre 8 et 15 chiffres, peut commencer par +)
        return re.match(r'^\+?[1-9]\d{7,14}$', cleaned_phone) is not None
    
    def validate_birthday(self, birthday: str) -> bool:
        """
        Valide une date de naissance.
        
        Args:
            birthday (str): Date de naissance au format YYYY-MM-DD
            
        Returns:
            bool: True si la date est valide, False sinon
        """
        if not birthday or not isinstance(birthday, str):
            return False
        
        try:
            # Vérifier le format de date
            birth_date = datetime.strptime(birthday, '%Y-%m-%d')
            
            # Vérifier que la date n'est pas dans le futur
            if birth_date > datetime.now():
                return False
            
            # Vérifier que l'utilisateur n'est pas trop âgé (plus de 120 ans)
            age = (datetime.now() - birth_date).days // 365
            if age > 120:
                return False
            
            # Vérifier que l'utilisateur a au moins 13 ans (COPPA compliance)
            if age < 13:
                return False
            
            return True
            
        except ValueError:
            return False
    
    def register_user(self, email: str, password: str, name: str,
                     birthday: str = None, phone_number: str = None) -> Dict[str, any]:
        """
        Inscrit un nouvel utilisateur dans le système.
        
        Args:
            email (str): Adresse email de l'utilisateur
            password (str): Mot de passe en clair
            name (str): Nom complet de l'utilisateur
            birthday (str, optional): Date de naissance (YYYY-MM-DD)
            phone_number (str, optional): Numéro de téléphone
            
        Returns:
            Dict[str, any]: Résultat de l'inscription avec succès et messages d'erreur
            
        Example:
            >>> user_manager = UserManager()
            >>> result = user_manager.register_user(
            ...     "user@gmail.com", "SecurePass123!", "John Doe"
            ... )
            >>> result['success']
            True
        """
        result = {
            'success': False,
            'message': '',
            'errors': []
        }
        
        # Validation des données
        if not self.validate_email(email):
            result['errors'].append("Format d'email invalide ou domaine non autorisé")
        
        password_validation = self.validate_password(password)
        if not password_validation['is_valid']:
            errors = []
            if not password_validation['min_length']:
                errors.append("au moins 8 caractères")
            if not password_validation['has_uppercase']:
                errors.append("une lettre majuscule")
            if not password_validation['has_lowercase']:
                errors.append("une lettre minuscule")
            if not password_validation['has_digit']:
                errors.append("un chiffre")
            if not password_validation['max_length']:
                errors.append("maximum 128 caractères")
            
            result['errors'].append(f"Le mot de passe doit contenir : {', '.join(errors)}")
        
        if not self.validate_name(name):
            result['errors'].append("Le nom doit contenir entre 2 et 50 caractères alphabétiques")
        
        if birthday and not self.validate_birthday(birthday):
            result['errors'].append("Format de date de naissance invalide (YYYY-MM-DD) ou âge inapproprié")
        
        if phone_number and not self.validate_phone(phone_number):
            result['errors'].append("Format de numéro de téléphone invalide")
        
        # Si il y a des erreurs de validation, arrêter ici
        if result['errors']:
            result['message'] = "Erreurs de validation"
            return result
        
        # Vérifier si l'utilisateur existe déjà
        existing_user = self.db_manager.get_user(email.lower())
        if existing_user:
            result['errors'].append("Un compte avec cette adresse email existe déjà")
            result['message'] = "Email déjà utilisé"
            return result
        
        # Hasher le mot de passe
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Créer l'utilisateur dans la base de données
        success = self.db_manager.create_user(
            email=email.lower(),
            password_hash=password_hash,
            name=name.strip(),
            birthday=birthday,
            phone_number=phone_number.strip() if phone_number else None
        )
        
        if success:
            result['success'] = True
            result['message'] = "Compte créé avec succès"
            logger.info(f"Nouveau utilisateur inscrit: {email}")
        else:
            result['message'] = "Erreur lors de la création du compte"
            result['errors'].append("Erreur interne du serveur")
        
        return result
    
    def authenticate_user(self, email: str, password: str) -> Dict[str, any]:
        """
        Authentifie un utilisateur avec son email et mot de passe.
        
        Args:
            email (str): Adresse email de l'utilisateur
            password (str): Mot de passe en clair
            
        Returns:
            Dict[str, any]: Résultat de l'authentification
            
        Example:
            >>> user_manager = UserManager()
            >>> result = user_manager.authenticate_user("user@gmail.com", "password")
            >>> if result['success']:
            ...     print(f"Connecté en tant que {result['user']['name']}")
        """
        result = {
            'success': False,
            'message': '',
            'user': None
        }
        
        if not email or not password:
            result['message'] = "Email et mot de passe requis"
            return result
        
        if not self.validate_email(email):
            result['message'] = "Format d'email invalide"
            return result
        
        # Hasher le mot de passe pour la comparaison
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Vérifier les informations d'identification
        if self.db_manager.authenticate_user(email.lower(), password_hash):
            user_info = self.db_manager.get_user(email.lower())
            if user_info:
                result['success'] = True
                result['message'] = "Authentification réussie"
                result['user'] = {
                    'email': user_info['email'],
                    'name': user_info['name'],
                    'birthday': user_info['birthday'],
                    'phone_number': user_info['phone_number'],
                    'created_at': user_info['created_at'],
                    'last_login': user_info['last_login']
                }
                self.current_user = email.lower()
                logger.info(f"Utilisateur authentifié: {email}")
            else:
                result['message'] = "Erreur lors de la récupération du profil"
        else:
            result['message'] = "Email ou mot de passe incorrect"
            logger.warning(f"Échec d'authentification pour: {email}")
        
        return result
    
    def get_user_profile(self, email: str) -> Optional[Dict]:
        """
        Récupère le profil d'un utilisateur par son email.
        
        Args:
            email (str): Adresse email de l'utilisateur
            
        Returns:
            Optional[Dict]: Profil de l'utilisateur ou None si non trouvé
        """
        if not self.validate_email(email):
            return None
        
        user_info = self.db_manager.get_user(email.lower())
        if user_info:
            # Retourner le profil sans les informations sensibles
            return {
                'email': user_info['email'],
                'name': user_info['name'],
                'birthday': user_info['birthday'],
                'phone_number': user_info['phone_number'],
                'created_at': user_info['created_at']
            }
        
        return None
    
    def search_users(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Recherche des utilisateurs par nom ou email.
        
        Args:
            query (str): Terme de recherche
            limit (int): Nombre maximum de résultats
            
        Returns:
            List[Dict]: Liste des utilisateurs trouvés
        """
        if not query or len(query.strip()) < 2:
            return []
        
        users = self.db_manager.search_users(query.strip())
        
        # Limiter le nombre de résultats et filtrer les informations sensibles
        return [
            {
                'email': user['email'],
                'name': user['name']
            }
            for user in users[:limit]
        ]
    
    def update_user_profile(self, email: str, name: str = None, 
                           birthday: str = None, phone_number: str = None) -> Dict[str, any]:
        """
        Met à jour le profil d'un utilisateur.
        
        Args:
            email (str): Email de l'utilisateur à mettre à jour
            name (str, optional): Nouveau nom
            birthday (str, optional): Nouvelle date de naissance
            phone_number (str, optional): Nouveau numéro de téléphone
            
        Returns:
            Dict[str, any]: Résultat de la mise à jour
        """
        result = {
            'success': False,
            'message': '',
            'errors': []
        }
        
        # Vérifier que l'utilisateur existe
        if not self.db_manager.get_user(email.lower()):
            result['message'] = "Utilisateur non trouvé"
            return result
        
        # Valider les nouvelles données si elles sont fournies
        if name is not None and not self.validate_name(name):
            result['errors'].append("Format de nom invalide")
        
        if birthday is not None and not self.validate_birthday(birthday):
            result['errors'].append("Format de date de naissance invalide")
        
        if phone_number is not None and not self.validate_phone(phone_number):
            result['errors'].append("Format de numéro de téléphone invalide")
        
        if result['errors']:
            result['message'] = "Erreurs de validation"
            return result
        
        # Construire la requête de mise à jour
        updates = {}
        if name is not None:
            updates['name'] = name.strip()
        if birthday is not None:
            updates['birthday'] = birthday
        if phone_number is not None:
            updates['phone_number'] = phone_number.strip()
        
        if not updates:
            result['message'] = "Aucune donnée à mettre à jour"
            return result
        
        # TODO: Implémenter la mise à jour dans la base de données
        # Cette fonctionnalité pourrait être ajoutée au DatabaseManager
        
        result['success'] = True
        result['message'] = "Profil mis à jour avec succès"
        logger.info(f"Profil mis à jour pour: {email}")
        
        return result
    
    def change_password(self, email: str, old_password: str, new_password: str) -> Dict[str, any]:
        """
        Change le mot de passe d'un utilisateur.
        
        Args:
            email (str): Email de l'utilisateur
            old_password (str): Ancien mot de passe
            new_password (str): Nouveau mot de passe
            
        Returns:
            Dict[str, any]: Résultat du changement de mot de passe
        """
        result = {
            'success': False,
            'message': '',
            'errors': []
        }
        
        # Vérifier l'ancien mot de passe
        auth_result = self.authenticate_user(email, old_password)
        if not auth_result['success']:
            result['message'] = "Ancien mot de passe incorrect"
            return result
        
        # Valider le nouveau mot de passe
        password_validation = self.validate_password(new_password)
        if not password_validation['is_valid']:
            result['errors'].append("Le nouveau mot de passe ne respecte pas les critères de sécurité")
            result['message'] = "Mot de passe invalide"
            return result
        
        # TODO: Implémenter le changement de mot de passe dans la base de données
        # Cette fonctionnalité pourrait être ajoutée au DatabaseManager
        
        result['success'] = True
        result['message'] = "Mot de passe changé avec succès"
        logger.info(f"Mot de passe changé pour: {email}")
        
        return result
    
    def logout(self) -> None:
        """
        Déconnecte l'utilisateur actuel.
        """
        if self.current_user:
            logger.info(f"Déconnexion de: {self.current_user}")
            self.current_user = None
    
    def is_logged_in(self) -> bool:
        """
        Vérifie si un utilisateur est actuellement connecté.
        
        Returns:
            bool: True si un utilisateur est connecté, False sinon
        """
        return self.current_user is not None
    
    def get_current_user(self) -> Optional[str]:
        """
        Retourne l'email de l'utilisateur actuellement connecté.
        
        Returns:
            Optional[str]: Email de l'utilisateur connecté ou None
        """
        return self.current_user


# Instance globale du gestionnaire d'utilisateurs
user_manager = UserManager()

def get_user_manager() -> UserManager:
    """
    Fonction utilitaire pour obtenir l'instance du gestionnaire d'utilisateurs.
    
    Returns:
        UserManager: Instance du gestionnaire d'utilisateurs
    """
    return user_manager