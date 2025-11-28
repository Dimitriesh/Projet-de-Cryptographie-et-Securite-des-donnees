#!/usr/bin/env python3
"""
Interface graphique pour la messagerie sécurisée - Style WhatsApp
===============================================================

Ce module contient l'interface graphique principale de l'application de messagerie
sécurisée. Il utilise CustomTkinter pour créer une interface moderne et intuitive
similaire à WhatsApp.

Fonctionnalités:
- Interface de connexion/inscription
- Liste des conversations avec contacts
- Zone de chat en temps réel
- Indicateurs de statut des messages
- Vérification d'intégrité visuelle
- Thème sombre moderne

Author: Équipe de développement
Date: 2024
Version: 1.0
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, scrolledtext, simpledialog
import threading
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from user_manager import get_user_manager
from message_manager import get_message_manager
from network_client import NetworkClient

# Configuration de CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class WhatsAppStyleGUI:
    """
    Interface graphique principale de style WhatsApp pour la messagerie sécurisée.
    
    Cette classe crée une interface utilisateur moderne et intuitive qui permet
    aux utilisateurs de communiquer de manière sécurisée tout en visualisant
    l'état d'intégrité des messages.
    
    Attributes:
        root: Fenêtre principale CustomTkinter
        user_manager: Gestionnaire des utilisateurs
        message_manager: Gestionnaire des messages
        current_user: Email de l'utilisateur connecté
        current_conversation: Email du contact actuel
        auto_refresh: Thread pour rafraîchissement automatique
    """
    
    def __init__(self):
        """
        Initialise l'interface graphique principale.
        """
        self.root = ctk.CTk()
        self.root.title("🔐 Secure Messaging - WhatsApp Style")
        self.root.geometry("1400x900")
        self.root.minsize(800, 600)
        
        # Managers
        self.user_manager = get_user_manager()
        self.message_manager = get_message_manager()
        
        # Client réseau
        self.network_client = None
        self.server_host = "127.0.0.1"
        self.server_port = 12345
        
        # État de l'application
        self.current_user = None
        self.current_conversation = None
        self.auto_refresh_thread = None
        self.is_running = True
        self.is_online_mode = False
        
        # Système de thème
        self.is_dark_theme = True
        self.theme_colors = self.get_theme_colors()
        
        # Widgets principaux
        self.main_frame = None
        self.sidebar = None
        self.chat_frame = None
        self.conversations_list = None
        self.messages_display = None
        self.message_input = None
        self.connection_status_label = None
        
        # Démarrer avec l'écran de configuration du serveur
        self.setup_server_config_screen()
        
        # Gérer la fermeture de l'application
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def get_theme_colors(self):
        """
        Retourne les couleurs selon le thème actuel.
        """
        if self.is_dark_theme:
            return {
                # Couleurs principales
                'bg_primary': "#1a1a1a",
                'bg_secondary': "#2d2d2d", 
                'bg_sidebar': "#242424",
                'bg_chat': "#1e1e1e",
                'bg_input': "#2a2a2a",
                
                # Couleurs de conversation
                'conv_normal': "#2d2d2d",
                'conv_hover': "#3a3a3a",
                'conv_selected': "#404040",
                
                # Couleurs de texte
                'text_primary': "#ffffff",
                'text_secondary': "#b0b0b0",
                'text_muted': "#808080",
                
                # Couleurs d'accent
                'accent_primary': "#0084ff",
                'accent_hover': "#006ee6",
                'success': "#25d366",
                'warning': "#ffbb33",
                'error': "#ff4444",
                
                # Messages
                'message_sent': "#0084ff",
                'message_received': "#3a3a3a",
                'message_compromised': "#ff4444"
            }
        else:
            return {
                # Couleurs principales
                'bg_primary': "#ffffff",
                'bg_secondary': "#f5f5f5",
                'bg_sidebar': "#f0f0f0", 
                'bg_chat': "#fafafa",
                'bg_input': "#ffffff",
                
                # Couleurs de conversation
                'conv_normal': "#ffffff",
                'conv_hover': "#e8f4fd",
                'conv_selected': "#d1ecf1",
                
                # Couleurs de texte
                'text_primary': "#1a1a1a",
                'text_secondary': "#4a4a4a",
                'text_muted': "#888888",
                
                # Couleurs d'accent
                'accent_primary': "#0084ff",
                'accent_hover': "#006ee6",
                'success': "#25d366",
                'warning': "#ff9500",
                'error': "#ff3b30",
                
                # Messages
                'message_sent': "#0084ff",
                'message_received': "#e5e5ea",
                'message_compromised': "#ff3b30"
            }
    
    def toggle_theme(self):
        """
        Bascule entre thème sombre et clair.
        """
        self.is_dark_theme = not self.is_dark_theme
        self.theme_colors = self.get_theme_colors()
        
        # Mettre à jour le thème CustomTkinter
        if self.is_dark_theme:
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")
        
        # Recharger l'interface actuelle
        self.refresh_theme()
    
    def refresh_theme(self):
        """
        Actualise les couleurs de l'interface selon le thème.
        """
        if hasattr(self, 'main_frame') and self.main_frame:
            # Recharger l'interface principale
            self.setup_main_interface()
        elif hasattr(self, 'sidebar') and self.sidebar:
            # Recharger seulement si on est dans l'interface principale
            self.setup_main_interface()
    
    def on_closing(self):
        """
        Gère la fermeture propre de l'application.
        """
        self.is_running = False
        
        # Fermer la connexion réseau
        if self.network_client:
            self.network_client.disconnect()
        
        # Arrêter les threads
        if self.auto_refresh_thread:
            self.auto_refresh_thread.join(timeout=1)
        
        self.root.destroy()
    
    def clear_window(self):
        """
        Efface tous les widgets de la fenêtre principale.
        """
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def setup_server_config_screen(self):
        """
        Crée l'écran de configuration du serveur.
        """
        self.clear_window()
        
        # Conteneur principal
        config_container = ctk.CTkFrame(self.root)
        config_container.place(relx=0.5, rely=0.5, anchor="center")
        
        # En-tête
        header_frame = ctk.CTkFrame(config_container, fg_color="transparent")
        header_frame.pack(pady=(40, 30), padx=50)
        
        title_label = ctk.CTkLabel(
            header_frame, 
            text="🌐 Configuration Réseau",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        title_label.pack()
        
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Configurez la connexion au serveur de messagerie",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        subtitle_label.pack(pady=(5, 0))
        
        # Formulaire de configuration
        form_frame = ctk.CTkFrame(config_container)
        form_frame.pack(pady=20, padx=50, fill="x")
        
        # Champs de configuration
        ctk.CTkLabel(
            form_frame, 
            text="Adresse du serveur",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(30, 5), anchor="w", padx=30)
        
        self.server_host_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="127.0.0.1 (local) ou IP du serveur",
            width=350,
            height=40,
            font=ctk.CTkFont(size=14)
        )
        self.server_host_entry.insert(0, self.server_host)
        self.server_host_entry.pack(pady=(0, 15), padx=30)
        
        ctk.CTkLabel(
            form_frame,
            text="Port du serveur", 
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(0, 5), anchor="w", padx=30)
        
        self.server_port_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="12345",
            width=350,
            height=40,
            font=ctk.CTkFont(size=14)
        )
        self.server_port_entry.insert(0, str(self.server_port))
        self.server_port_entry.pack(pady=(0, 20), padx=30)
        
        # Boutons de connexion
        connect_btn = ctk.CTkButton(
            form_frame,
            text="Se connecter au serveur",
            command=self.connect_to_server,
            width=350,
            height=45,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        connect_btn.pack(pady=(0, 10), padx=30)
        
        offline_btn = ctk.CTkButton(
            form_frame,
            text="Mode hors ligne (base de données locale)",
            command=self.start_offline_mode,
            width=350,
            height=45,
            font=ctk.CTkFont(size=16),
            fg_color="gray",
            hover_color="dark gray"
        )
        offline_btn.pack(pady=(0, 30), padx=30)
        
        # Status de connexion
        self.connection_status = ctk.CTkLabel(
            form_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.connection_status.pack(pady=(0, 10), padx=30)
    
    def connect_to_server(self):
        """
        Tente de se connecter au serveur configuré.
        """
        # Récupérer les paramètres
        try:
            self.server_host = self.server_host_entry.get().strip()
            self.server_port = int(self.server_port_entry.get().strip())
        except ValueError:
            messagebox.showerror("Erreur", "Port invalide")
            return
        
        if not self.server_host:
            messagebox.showerror("Erreur", "Adresse serveur requise")
            return
        
        self.connection_status.configure(text="🔄 Connexion en cours...", text_color="orange")
        self.root.update()
        
        # Créer le client réseau
        self.network_client = NetworkClient(self.server_host, self.server_port)
        
        # Configurer les callbacks
        self.setup_network_callbacks()
        
        # Tenter la connexion
        if self.network_client.connect():
            self.is_online_mode = True
            self.connection_status.configure(text="✅ Connexion réussie", text_color="green")
            self.root.after(1000, self.setup_login_screen)  # Aller à l'écran de connexion après 1s
        else:
            self.connection_status.configure(text="❌ Connexion échouée", text_color="red")
            messagebox.showerror("Erreur de connexion", 
                               f"Impossible de se connecter au serveur {self.server_host}:{self.server_port}")
    
    def start_offline_mode(self):
        """
        Démarre l'application en mode hors ligne.
        """
        self.is_online_mode = False
        self.network_client = None
        self.setup_login_screen()
    
    def setup_network_callbacks(self):
        """
        Configure les callbacks pour le client réseau.
        """
        if not self.network_client:
            return
        
        self.network_client.set_callback("on_message", self.on_network_message)
        self.network_client.set_callback("on_user_status", self.on_user_status_change)
        self.network_client.set_callback("on_connection_lost", self.on_connection_lost)
        self.network_client.set_callback("on_connected", self.on_network_connected)
    
    def on_network_message(self, message_data: dict):
        """
        Callback appelé quand un nouveau message arrive via le réseau.
        """
        # Programmer la mise à jour dans le thread principal
        self.root.after(0, lambda: self._handle_network_message(message_data))
    
    def _handle_network_message(self, message_data: dict):
        """
        Traite un message reçu via le réseau (dans le thread principal).
        """
        try:
            sender_email = message_data.get("sender_email")
            
            # Rafraîchir seulement si nécessaire
            needs_message_refresh = self.current_conversation == sender_email
            needs_conversation_refresh = True
            
            if needs_message_refresh:
                self.load_messages()
            
            if needs_conversation_refresh:
                self.load_conversations()
            
            # Notification visuelle pour les messages non visibles
            if sender_email != self.current_conversation:
                # Pourrait ajouter une notification toast ici
                pass
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement du message réseau: {e}")
    
    def on_user_status_change(self, status_data: dict):
        """
        Callback appelé quand le statut d'un utilisateur change.
        """
        # Programmer la mise à jour dans le thread principal
        self.root.after(0, lambda: self._handle_user_status_change(status_data))
    
    def _handle_user_status_change(self, status_data: dict):
        """
        Traite un changement de statut utilisateur (dans le thread principal).
        """
        try:
            # Rafraîchir la liste des conversations pour mettre à jour les statuts
            self.load_conversations()
        except Exception as e:
            logger.error(f"Erreur lors du traitement du changement de statut: {e}")
    
    def on_connection_lost(self):
        """
        Callback appelé quand la connexion au serveur est perdue.
        """
        self.root.after(0, self._handle_connection_lost)
    
    def _handle_connection_lost(self):
        """
        Traite la perte de connexion (dans le thread principal).
        """
        self.is_online_mode = False
        
        # Afficher une notification
        messagebox.showwarning(
            "Connexion perdue", 
            "La connexion au serveur a été perdue. L'application continue en mode hors ligne."
        )
        
        # Mettre à jour l'interface si nécessaire
        if hasattr(self, 'connection_status_label') and self.connection_status_label:
            self.connection_status_label.configure(text="🔴 Hors ligne", text_color="red")
    
    def on_network_connected(self):
        """
        Callback appelé quand la connexion au serveur est établie.
        """
        self.root.after(0, self._handle_network_connected)
    
    def _handle_network_connected(self):
        """
        Traite la connexion au serveur (dans le thread principal).
        """
        self.is_online_mode = True
        
        # Mettre à jour l'interface si nécessaire
        if hasattr(self, 'connection_status_label') and self.connection_status_label:
            self.connection_status_label.configure(text="🟢 En ligne", text_color="green")
    
    def setup_login_screen(self):
        """
        Crée l'écran de connexion avec design moderne.
        """
        self.clear_window()
        
        # Conteneur principal centré
        login_container = ctk.CTkFrame(self.root)
        login_container.place(relx=0.5, rely=0.5, anchor="center")
        
        # En-tête avec logo et titre
        header_frame = ctk.CTkFrame(login_container, fg_color="transparent")
        header_frame.pack(pady=(40, 30), padx=50)
        
        title_label = ctk.CTkLabel(
            header_frame, 
            text="🔐 Secure Messaging",
            font=ctk.CTkFont(size=36, weight="bold")
        )
        title_label.pack()
        
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="Messagerie chiffrée avec vérification d'intégrité",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        subtitle_label.pack(pady=(5, 0))
        
        # Formulaire de connexion
        form_frame = ctk.CTkFrame(login_container)
        form_frame.pack(pady=20, padx=50, fill="x")
        
        # Champs du formulaire
        ctk.CTkLabel(
            form_frame, 
            text="Adresse Email",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(30, 5), anchor="w", padx=30)
        
        self.login_email_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="votre.email@gmail.com",
            width=350,
            height=45,
            font=ctk.CTkFont(size=14)
        )
        self.login_email_entry.pack(pady=(0, 20), padx=30)
        
        ctk.CTkLabel(
            form_frame,
            text="Mot de passe",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(0, 5), anchor="w", padx=30)
        
        self.login_password_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="Votre mot de passe",
            show="*",
            width=350,
            height=45,
            font=ctk.CTkFont(size=14)
        )
        self.login_password_entry.pack(pady=(0, 30), padx=30)
        
        # Boutons d'action
        login_btn = ctk.CTkButton(
            form_frame,
            text="Se connecter",
            command=self.handle_login,
            width=350,
            height=45,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        login_btn.pack(pady=(0, 15), padx=30)
        
        register_btn = ctk.CTkButton(
            form_frame,
            text="Créer un nouveau compte",
            command=self.setup_register_screen,
            width=350,
            height=45,
            font=ctk.CTkFont(size=16),
            fg_color="transparent",
            border_width=2
        )
        register_btn.pack(pady=(0, 30), padx=30)
        
        # Permettre Enter pour se connecter
        self.login_password_entry.bind("<Return>", lambda e: self.handle_login())
    
    def setup_register_screen(self):
        """
        Crée l'écran d'inscription avec validation en temps réel.
        """
        self.clear_window()
        
        # Conteneur principal avec défilement
        main_container = ctk.CTkScrollableFrame(self.root)
        main_container.pack(fill="both", expand=True, padx=50, pady=30)
        
        # En-tête
        header_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        header_frame.pack(pady=(20, 40), fill="x")
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="Créer un nouveau compte",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        title_label.pack()
        
        # Formulaire d'inscription
        form_frame = ctk.CTkFrame(main_container)
        form_frame.pack(pady=20, padx=100, fill="x")
        
        # Champs du formulaire
        fields = [
            ("Nom complet", "reg_name_entry", "Jean Dupont"),
            ("Adresse Email", "reg_email_entry", "jean.dupont@gmail.com"),
            ("Mot de passe", "reg_password_entry", "", True),
            ("Confirmer le mot de passe", "reg_password_confirm_entry", "", True),
            ("Date de naissance", "reg_birthday_entry", "1990-01-15"),
            ("Numéro de téléphone", "reg_phone_entry", "+33123456789")
        ]
        
        for label_text, attr_name, placeholder, *show_args in fields:
            ctk.CTkLabel(
                form_frame,
                text=label_text,
                font=ctk.CTkFont(size=14, weight="bold")
            ).pack(pady=(20, 5), anchor="w", padx=30)
            
            entry = ctk.CTkEntry(
                form_frame,
                placeholder_text=placeholder,
                width=400,
                height=40,
                font=ctk.CTkFont(size=14),
                show="*" if show_args else ""
            )
            entry.pack(pady=(0, 10), padx=30)
            setattr(self, attr_name, entry)
        
        # Zone d'affichage des erreurs de validation
        self.validation_label = ctk.CTkLabel(
            form_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="red"
        )
        self.validation_label.pack(pady=10, padx=30)
        
        # Boutons
        button_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        button_frame.pack(pady=30, padx=30, fill="x")
        
        register_btn = ctk.CTkButton(
            button_frame,
            text="Créer le compte",
            command=self.handle_register,
            width=180,
            height=45,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        register_btn.pack(side="left", padx=(0, 10))
        
        back_btn = ctk.CTkButton(
            button_frame,
            text="Retour",
            command=self.setup_login_screen,
            width=180,
            height=45,
            font=ctk.CTkFont(size=16),
            fg_color="gray",
            hover_color="dark gray"
        )
        back_btn.pack(side="right", padx=(10, 0))
    
    def handle_login(self):
        """
        Gère le processus de connexion de l'utilisateur.
        """
        email = self.login_email_entry.get().strip()
        password = self.login_password_entry.get().strip()
        
        if not email or not password:
            messagebox.showerror("Erreur", "Veuillez remplir tous les champs")
            return
        
        # Authentifier selon le mode (en ligne ou hors ligne)
        if self.is_online_mode and self.network_client:
            # Authentification via le réseau
            response = self.network_client.authenticate(email, password)
            if response and response.get("type") == "auth_success":
                self.current_user = email.lower()
                user_info = response.get("user", {})
                messagebox.showinfo("Succès", f"Bienvenue, {user_info.get('name', email)}!")
                self.setup_main_interface()
            else:
                error_msg = response.get("message", "Erreur d'authentification") if response else "Erreur de réseau"
                messagebox.showerror("Erreur de connexion", error_msg)
        else:
            # Authentification locale
            result = self.user_manager.authenticate_user(email, password)
            if result['success']:
                self.current_user = email.lower()
                messagebox.showinfo("Succès", f"Bienvenue, {result['user']['name']}!")
                self.setup_main_interface()
            else:
                messagebox.showerror("Erreur de connexion", result['message'])
    
    def handle_register(self):
        """
        Gère le processus d'inscription d'un nouvel utilisateur.
        """
        # Récupérer les données du formulaire
        name = self.reg_name_entry.get().strip()
        email = self.reg_email_entry.get().strip()
        password = self.reg_password_entry.get().strip()
        password_confirm = self.reg_password_confirm_entry.get().strip()
        birthday = self.reg_birthday_entry.get().strip()
        phone = self.reg_phone_entry.get().strip()
        
        # Validation côté client
        if password != password_confirm:
            self.validation_label.configure(text="Les mots de passe ne correspondent pas")
            return
        
        # Inscription selon le mode
        if self.is_online_mode and self.network_client:
            # Inscription via le réseau
            response = self.network_client.register(
                email=email,
                password=password,
                name=name,
                birthday=birthday if birthday else None,
                phone_number=phone if phone else None
            )
            if response and response.get("type") == "registration_success":
                messagebox.showinfo("Succès", "Compte créé avec succès! Vous pouvez maintenant vous connecter.")
                self.setup_login_screen()
            else:
                error_text = response.get("message", "Erreur d'inscription") if response else "Erreur de réseau"
                if response and response.get("errors"):
                    error_text += "\\n" + "\\n".join(response["errors"])
                self.validation_label.configure(text=error_text)
        else:
            # Inscription locale
            result = self.user_manager.register_user(
                email=email,
                password=password,
                name=name,
                birthday=birthday if birthday else None,
                phone_number=phone if phone else None
            )
            
            if result['success']:
                messagebox.showinfo("Succès", "Compte créé avec succès! Vous pouvez maintenant vous connecter.")
                self.setup_login_screen()
            else:
                error_text = result['message']
                if result['errors']:
                    error_text += "\\n" + "\\n".join(result['errors'])
                self.validation_label.configure(text=error_text)
    
    def setup_main_interface(self):
        """
        Crée l'interface principale de type WhatsApp.
        """
        self.clear_window()
        
        # Conteneur principal
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Sidebar gauche pour les conversations
        self.setup_sidebar()
        
        # Zone de chat principale
        self.setup_chat_area()
        
        # Charger les conversations existantes
        self.load_conversations()
        
        # Démarrer le rafraîchissement automatique
        self.start_auto_refresh()
    
    def setup_sidebar(self):
        """
        Crée la barre latérale avec la liste des conversations.
        """
        self.sidebar = ctk.CTkFrame(
            self.main_frame, 
            width=400,
            fg_color=self.theme_colors['bg_sidebar']
        )
        self.sidebar.pack(side="left", fill="y", padx=(0, 5))
        self.sidebar.pack_propagate(False)
        
        # En-tête de la sidebar
        header = ctk.CTkFrame(self.sidebar, height=80)
        header.pack(fill="x", padx=10, pady=(10, 5))
        header.pack_propagate(False)
        
        # Informations utilisateur
        user_info = self.user_manager.get_user_profile(self.current_user)
        user_name = user_info['name'] if user_info else self.current_user
        
        user_label = ctk.CTkLabel(
            header,
            text=f"👤 {user_name}",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        user_label.pack(side="left", pady=20, padx=15)
        
        # Status de connexion et bouton de déconnexion
        status_frame = ctk.CTkFrame(header, fg_color="transparent")
        status_frame.pack(side="right", pady=20, padx=15)
        
        # Indicateur de statut de connexion
        status_text = "🟢 En ligne" if self.is_online_mode else "🔴 Hors ligne"
        status_color = "green" if self.is_online_mode else "orange"
        
        self.connection_status_label = ctk.CTkLabel(
            status_frame,
            text=status_text,
            font=ctk.CTkFont(size=10),
            text_color=status_color
        )
        self.connection_status_label.pack()
        
        # Bouton de basculement de thème
        theme_btn = ctk.CTkButton(
            status_frame,
            text="🌙" if self.is_dark_theme else "☀️",
            command=self.toggle_theme,
            width=40,
            height=35,
            font=ctk.CTkFont(size=16),
            fg_color=self.theme_colors['accent_primary'],
            hover_color=self.theme_colors['accent_hover']
        )
        theme_btn.pack(pady=(0, 5))
        
        logout_btn = ctk.CTkButton(
            status_frame,
            text="Déconnexion",
            command=self.handle_logout,
            width=100,
            height=35,
            font=ctk.CTkFont(size=12),
            fg_color=self.theme_colors['error'],
            hover_color="#cc3333" if self.is_dark_theme else "#ff1a1a"
        )
        logout_btn.pack()
        
        # Bouton nouvelle conversation
        new_conv_btn = ctk.CTkButton(
            self.sidebar,
            text="💬 Nouvelle conversation",
            command=self.new_conversation_dialog,
            width=350,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.theme_colors['success'],
            hover_color="#20b358" if self.is_dark_theme else "#1ea854"
        )
        new_conv_btn.pack(pady=10, padx=15)
        
        # Zone de recherche
        search_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        search_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="🔍 Rechercher des conversations...",
            width=350,
            height=35
        )
        self.search_entry.pack()
        self.search_entry.bind("<KeyRelease>", self.filter_conversations)
        
        # Liste des conversations
        self.conversations_list = ctk.CTkScrollableFrame(self.sidebar)
        self.conversations_list.pack(fill="both", expand=True, padx=10, pady=(5, 10))
    
    def setup_chat_area(self):
        """
        Crée la zone de chat principale.
        """
        self.chat_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color=self.theme_colors['bg_chat']
        )
        self.chat_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        # En-tête du chat
        self.chat_header = ctk.CTkFrame(self.chat_frame, height=80)
        self.chat_header.pack(fill="x", padx=10, pady=(10, 5))
        self.chat_header.pack_propagate(False)
        
        self.chat_title = ctk.CTkLabel(
            self.chat_header,
            text="Sélectionnez une conversation pour commencer",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="gray"
        )
        self.chat_title.pack(expand=True)
        
        # Zone d'affichage des messages
        self.messages_display = ctk.CTkScrollableFrame(self.chat_frame)
        self.messages_display.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Zone de saisie des messages
        self.setup_message_input()
    
    def setup_message_input(self):
        """
        Crée la zone de saisie des messages.
        """
        input_frame = ctk.CTkFrame(self.chat_frame, height=100)
        input_frame.pack(fill="x", padx=10, pady=(5, 10))
        input_frame.pack_propagate(False)
        
        # Zone de texte pour le message
        self.message_input = ctk.CTkTextbox(
            input_frame,
            height=60,
            font=ctk.CTkFont(size=14),
            wrap="word"
        )
        self.message_input.pack(side="left", fill="both", expand=True, padx=(15, 10), pady=15)
        
        # Bouton d'envoi
        send_btn = ctk.CTkButton(
            input_frame,
            text="Envoyer",
            command=self.send_message,
            width=100,
            height=60,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        send_btn.pack(side="right", padx=(0, 15), pady=15)
        
        # Permettre Ctrl+Enter pour envoyer
        self.message_input.bind("<Control-Return>", lambda e: self.send_message())
    
    def new_conversation_dialog(self):
        """
        Ouvre un dialogue pour démarrer une nouvelle conversation.
        """
        dialog = ctk.CTkInputDialog(
            text="Entrez l'adresse email du contact:",
            title="Nouvelle conversation"
        )
        email = dialog.get_input()
        
        if email:
            email = email.strip().lower()
            
            # Vérifier que l'utilisateur existe
            profile = self.user_manager.get_user_profile(email)
            if profile:
                self.select_conversation(email)
            else:
                messagebox.showerror("Erreur", "Utilisateur non trouvé")
    
    def load_conversations(self):
        """
        Charge et affiche la liste des conversations.
        """
        # Effacer la liste actuelle
        for widget in self.conversations_list.winfo_children():
            widget.destroy()
        
        # Récupérer les conversations selon le mode
        if self.is_online_mode and self.network_client:
            # Mode en ligne - récupérer via le réseau
            response = self.network_client.get_conversations()
            if response and response.get("type") == "conversations":
                conversations = response.get("conversations", [])
            else:
                conversations = []
        else:
            # Mode hors ligne - récupérer localement
            conversations = self.message_manager.get_user_conversations(self.current_user)
        
        if not conversations:
            # Afficher un message si pas de conversations
            no_conv_label = ctk.CTkLabel(
                self.conversations_list,
                text="Aucune conversation\\nCommencez en créant une nouvelle conversation",
                font=ctk.CTkFont(size=14),
                text_color="gray"
            )
            no_conv_label.pack(pady=50)
            return
        
        # Créer les éléments de conversation
        for conv in conversations:
            self.create_conversation_item(conv)
    
    def create_conversation_item(self, conversation: Dict):
        """
        Crée un élément de conversation dans la liste.
        
        Args:
            conversation (Dict): Données de la conversation
        """
        conv_frame = ctk.CTkFrame(
            self.conversations_list, 
            height=80,
            fg_color=self.theme_colors['conv_normal']
        )
        conv_frame.pack(fill="x", pady=2, padx=5)
        conv_frame.pack_propagate(False)
        
        # Fonction de clic et hover
        def on_click(event=None):
            self.select_conversation(conversation['other_user_email'])
        
        def on_enter(event=None):
            conv_frame.configure(fg_color=self.theme_colors['conv_hover'])
        
        def on_leave(event=None):
            conv_frame.configure(fg_color=self.theme_colors['conv_normal'])
        
        # Rendre le frame cliquable et avec hover
        conv_frame.bind("<Button-1>", on_click)
        conv_frame.bind("<Enter>", on_enter)
        conv_frame.bind("<Leave>", on_leave)
        
        # Conteneur principal
        main_container = ctk.CTkFrame(conv_frame, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Ligne supérieure: nom et heure
        top_line = ctk.CTkFrame(main_container, fg_color="transparent")
        top_line.pack(fill="x")
        
        # Nom de l'utilisateur
        name_label = ctk.CTkLabel(
            top_line,
            text=conversation['other_user_name'],
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        )
        name_label.pack(side="left")
        
        # Heure du dernier message
        if conversation['last_message_time']:
            try:
                time_obj = datetime.fromisoformat(conversation['last_message_time'])
                time_str = time_obj.strftime("%H:%M")
            except:
                time_str = ""
        else:
            time_str = ""
        
        time_label = ctk.CTkLabel(
            top_line,
            text=time_str,
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        time_label.pack(side="right")
        
        # Ligne inférieure: dernier message et badge non lu
        bottom_line = ctk.CTkFrame(main_container, fg_color="transparent")
        bottom_line.pack(fill="x")
        
        # Dernier message
        last_msg = conversation.get('last_message_content', '')
        if conversation.get('is_last_message_sent'):
            last_msg = f"Vous: {last_msg}"
        
        msg_label = ctk.CTkLabel(
            bottom_line,
            text=last_msg,
            font=ctk.CTkFont(size=12),
            text_color="gray",
            anchor="w"
        )
        msg_label.pack(side="left", fill="x", expand=True)
        
        # Propager les événements de clic et hover à tous les éléments
        widgets_to_bind = [main_container, top_line, bottom_line, name_label, time_label, msg_label]
        for widget in widgets_to_bind:
            widget.bind("<Button-1>", on_click)
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
        
        # Badge de messages non lus et statut en ligne
        status_frame = ctk.CTkFrame(bottom_line, fg_color="transparent")
        status_frame.pack(side="right")
        
        # Liste des widgets supplémentaires pour les événements
        additional_widgets = [status_frame]
        
        # Indicateur en ligne (seulement en mode réseau)
        if self.is_online_mode and conversation.get('is_online', False):
            online_indicator = ctk.CTkLabel(
                status_frame,
                text="🟢",
                font=ctk.CTkFont(size=8),
                width=15,
                height=15
            )
            online_indicator.pack(side="right", padx=(5, 0))
            additional_widgets.append(online_indicator)
        
        # Badge de messages non lus
        unread_count = conversation.get('unread_count', 0)
        if unread_count > 0:
            badge = ctk.CTkLabel(
                status_frame,
                text=str(unread_count),
                font=ctk.CTkFont(size=10, weight="bold"),
                fg_color="red",
                corner_radius=10,
                width=20,
                height=20
            )
            badge.pack(side="right", padx=(0, 5))
            additional_widgets.append(badge)
        
        # Ajouter les événements aux widgets supplémentaires
        for widget in additional_widgets:
            widget.bind("<Button-1>", on_click)
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
    
    def filter_conversations(self, event=None):
        """
        Filtre les conversations selon le terme de recherche.
        """
        query = self.search_entry.get().lower().strip()
        
        # Effacer la liste actuelle
        for widget in self.conversations_list.winfo_children():
            widget.destroy()
        
        # Récupérer toutes les conversations
        if self.is_online_mode and self.network_client:
            response = self.network_client.get_conversations()
            if response and response.get("type") == "conversations":
                all_conversations = response.get("conversations", [])
            else:
                all_conversations = []
        else:
            all_conversations = self.message_manager.get_user_conversations(self.current_user)
        
        # Filtrer selon la recherche
        if query and len(query) >= 1:
            filtered_conversations = []
            for conv in all_conversations:
                # Rechercher dans le nom et l'email
                name = conv.get('other_user_name', '').lower()
                email = conv.get('other_user_email', '').lower()
                last_message = conv.get('last_message_content', '').lower()
                
                if (query in name or query in email or query in last_message):
                    filtered_conversations.append(conv)
            
            conversations = filtered_conversations
        else:
            conversations = all_conversations
        
        # Afficher les conversations filtrées
        if not conversations:
            no_result_label = ctk.CTkLabel(
                self.conversations_list,
                text="Aucune conversation trouvée" if query else "Aucune conversation\nCommencez en créant une nouvelle conversation",
                font=ctk.CTkFont(size=14),
                text_color="gray"
            )
            no_result_label.pack(pady=50)
        else:
            for conv in conversations:
                self.create_conversation_item(conv)
    
    def select_conversation(self, other_user_email: str):
        """
        Sélectionne et affiche une conversation.
        
        Args:
            other_user_email (str): Email de l'autre utilisateur
        """
        self.current_conversation = other_user_email
        
        # Marquer les messages comme lus
        self.message_manager.mark_conversation_as_read(self.current_user, other_user_email)
        
        # Mettre à jour l'en-tête du chat
        user_profile = self.user_manager.get_user_profile(other_user_email)
        contact_name = user_profile['name'] if user_profile else other_user_email
        
        self.chat_title.configure(
            text=f"💬 {contact_name}",
            text_color="white"
        )
        
        # Charger et afficher les messages
        self.load_messages()
        
        # Recharger les conversations seulement si nécessaire (pour les compteurs non lus)
        self.load_conversations()
    
    def load_messages(self):
        """
        Charge et affiche les messages de la conversation actuelle.
        """
        if not self.current_conversation:
            return
        
        # Effacer les messages actuels
        for widget in self.messages_display.winfo_children():
            widget.destroy()
        
        # Récupérer les messages selon le mode
        if self.is_online_mode and self.network_client:
            # Mode en ligne - récupérer via le réseau
            response = self.network_client.get_messages(self.current_conversation)
            if response and response.get("type") == "messages":
                messages = response.get("messages", [])
            else:
                messages = []
        else:
            # Mode hors ligne - récupérer localement
            messages = self.message_manager.get_conversation_messages(
                self.current_user, self.current_conversation, verify_integrity=True
            )
        
        # Grouper les messages par date et afficher avec des délimiteurs
        self.display_messages_with_date_separators(messages)
        
        # Faire défiler vers le bas
        self.root.after(100, self._scroll_to_bottom)
    
    def display_messages_with_date_separators(self, messages):
        """
        Affiche les messages en les groupant par date avec des délimiteurs.
        
        Args:
            messages (List[Dict]): Liste des messages
        """
        from collections import defaultdict
        
        # Grouper les messages par date
        messages_by_date = defaultdict(list)
        
        for msg in messages:
            try:
                # Extraire la date du timestamp
                timestamp = msg.get('timestamp', '')
                if timestamp:
                    date_obj = datetime.fromisoformat(timestamp)
                    date_key = date_obj.strftime("%Y-%m-%d")
                    messages_by_date[date_key].append((date_obj, msg))
                else:
                    # Message sans timestamp, grouper sous "unknown"
                    messages_by_date['unknown'].append((None, msg))
            except:
                # En cas d'erreur de parsing, grouper sous "unknown"
                messages_by_date['unknown'].append((None, msg))
        
        # Trier les dates
        sorted_dates = sorted([d for d in messages_by_date.keys() if d != 'unknown'])
        if 'unknown' in messages_by_date:
            sorted_dates.append('unknown')
        
        # Afficher les messages groupés par date
        for date_key in sorted_dates:
            # Créer le délimiteur de date
            self.create_date_separator(date_key)
            
            # Trier les messages de la journée par heure
            day_messages = messages_by_date[date_key]
            if date_key != 'unknown':
                day_messages.sort(key=lambda x: x[0])  # Trier par datetime
            
            # Afficher les messages de la journée
            for date_obj, msg in day_messages:
                self.create_message_bubble(msg)
    
    def create_date_separator(self, date_key):
        """
        Crée un délimiteur de date pour séparer les messages.
        
        Args:
            date_key (str): Clé de date (format YYYY-MM-DD ou 'unknown')
        """
        # Conteneur du délimiteur
        separator_container = ctk.CTkFrame(self.messages_display, fg_color="transparent")
        separator_container.pack(fill="x", pady=15, padx=10)
        
        # Formater la date pour l'affichage
        if date_key == 'unknown':
            date_text = "Date inconnue"
        else:
            try:
                date_obj = datetime.strptime(date_key, "%Y-%m-%d")
                today = datetime.now().date()
                yesterday = today - timedelta(days=1)
                msg_date = date_obj.date()
                
                if msg_date == today:
                    date_text = "Aujourd'hui"
                elif msg_date == yesterday:
                    date_text = "Hier"
                else:
                    # Afficher la date complète
                    date_text = date_obj.strftime("%A %d %B %Y")
                    # Traduire les jours et mois en français
                    translations = {
                        'Monday': 'Lundi', 'Tuesday': 'Mardi', 'Wednesday': 'Mercredi',
                        'Thursday': 'Jeudi', 'Friday': 'Vendredi', 'Saturday': 'Samedi', 'Sunday': 'Dimanche',
                        'January': 'Janvier', 'February': 'Février', 'March': 'Mars', 'April': 'Avril',
                        'May': 'Mai', 'June': 'Juin', 'July': 'Juillet', 'August': 'Août',
                        'September': 'Septembre', 'October': 'Octobre', 'November': 'Novembre', 'December': 'Décembre'
                    }
                    for en, fr in translations.items():
                        date_text = date_text.replace(en, fr)
            except:
                date_text = date_key
        
        # Label de date avec style
        date_label = ctk.CTkLabel(
            separator_container,
            text=date_text,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=self.theme_colors['bg_secondary'],
            corner_radius=15,
            text_color=self.theme_colors['text_secondary']
        )
        date_label.pack(pady=5)
    
    def _scroll_to_bottom(self):
        """
        Fait défiler la zone de messages vers le bas.
        """
        try:
            self.messages_display._parent_canvas.yview_moveto(1.0)
        except:
            pass
    
    def create_message_bubble(self, message: Dict):
        """
        Crée une bulle de message dans la conversation.
        
        Args:
            message (Dict): Données du message
        """
        is_sent = message['is_sent']
        
        # Conteneur du message
        msg_container = ctk.CTkFrame(self.messages_display, fg_color="transparent")
        msg_container.pack(fill="x", pady=5, padx=10)
        
        # Bulle de message avec couleurs du thème
        if message.get('integrity_verified') is False:
            bubble_color = self.theme_colors['message_compromised']
        elif is_sent:
            bubble_color = self.theme_colors['message_sent']
        else:
            bubble_color = self.theme_colors['message_received']
        
        bubble_frame = ctk.CTkFrame(
            msg_container,
            fg_color=bubble_color,
            corner_radius=15
        )
        
        # Positionner la bulle
        if is_sent:
            bubble_frame.pack(side="right", padx=(50, 10))
        else:
            bubble_frame.pack(side="left", padx=(10, 50))
        
        # Contenu du message
        content_label = ctk.CTkLabel(
            bubble_frame,
            text=message['content'],
            font=ctk.CTkFont(size=14),
            wraplength=350,
            justify="left"
        )
        content_label.pack(padx=15, pady=(10, 5))
        
        # Informations du message (heure + statut)
        info_frame = ctk.CTkFrame(bubble_frame, fg_color="transparent")
        info_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        # Heure
        try:
            time_obj = datetime.fromisoformat(message['timestamp'])
            time_str = time_obj.strftime("%H:%M")
        except:
            time_str = ""
        
        time_label = ctk.CTkLabel(
            info_frame,
            text=time_str,
            font=ctk.CTkFont(size=10),
            text_color="lightgray"
        )
        time_label.pack(side="left")
        
        # Indicateur d'intégrité
        if message.get('integrity_verified') is False:
            warning_label = ctk.CTkLabel(
                info_frame,
                text="⚠️",
                font=ctk.CTkFont(size=12),
                text_color="yellow"
            )
            warning_label.pack(side="right")
        elif message.get('integrity_verified') is True:
            check_label = ctk.CTkLabel(
                info_frame,
                text="✓",
                font=ctk.CTkFont(size=12),
                text_color="lightgreen"
            )
            check_label.pack(side="right")
    
    def send_message(self):
        """
        Envoie un nouveau message dans la conversation actuelle.
        """
        if not self.current_conversation:
            messagebox.showerror("Erreur", "Sélectionnez une conversation")
            return
        
        content = self.message_input.get("1.0", "end").strip()
        if not content:
            return
        
        # Envoyer le message selon le mode
        if self.is_online_mode and self.network_client:
            # Mode en ligne - envoyer via le réseau
            response = self.network_client.send_chat_message(self.current_conversation, content)
            if response and response.get("type") == "message_sent":
                # Succès - effacer la zone de saisie
                self.message_input.delete("1.0", "end")
                
                # En mode réseau, on laisse les callbacks gérer les mises à jour
                # Mais on rafraîchit une seule fois pour voir notre propre message
                self.load_messages()
            else:
                error_msg = response.get("message", "Erreur d'envoi") if response else "Erreur de réseau"
                messagebox.showerror("Erreur d'envoi", error_msg)
        else:
            # Mode hors ligne - envoyer localement
            result = self.message_manager.send_message(
                self.current_user, self.current_conversation, content
            )
            
            if result['success']:
                # Effacer la zone de saisie
                self.message_input.delete("1.0", "end")
                
                # Recharger une seule fois
                self.load_messages()
                self.load_conversations()
            else:
                messagebox.showerror("Erreur d'envoi", result['message'])
    
    def start_auto_refresh(self):
        """
        Démarre le thread de rafraîchissement automatique.
        En mode réseau, on s'appuie sur les callbacks pour les notifications en temps réel.
        """
        if not self.auto_refresh_thread and not self.is_online_mode:
            # Seulement en mode hors ligne
            self.auto_refresh_thread = threading.Thread(
                target=self._auto_refresh_loop,
                daemon=True
            )
            self.auto_refresh_thread.start()
    
    def _auto_refresh_loop(self):
        """
        Boucle de rafraîchissement automatique des messages (mode hors ligne seulement).
        """
        while self.is_running and not self.is_online_mode:
            try:
                if self.current_conversation:
                    # Programmer le rafraîchissement dans le thread principal
                    self.root.after(0, self._safe_refresh)
                
                time.sleep(10)  # Rafraîchir toutes les 10 secondes en mode hors ligne
            except:
                break
    
    def _safe_refresh(self):
        """
        Rafraîchissement sécurisé dans le thread principal.
        """
        try:
            if self.current_conversation:
                self.load_messages()
            self.load_conversations()
        except:
            pass
    
    def handle_logout(self):
        """
        Gère la déconnexion de l'utilisateur.
        """
        self.is_running = False
        self.user_manager.logout()
        self.current_user = None
        self.current_conversation = None
        messagebox.showinfo("Déconnexion", "Vous avez été déconnecté avec succès")
        self.setup_login_screen()
    
    def run(self):
        """
        Lance la boucle principale de l'interface.
        """
        self.root.mainloop()


def main():
    """
    Point d'entrée principal de l'application GUI.
    """
    app = WhatsAppStyleGUI()
    app.run()


if __name__ == "__main__":
    main()