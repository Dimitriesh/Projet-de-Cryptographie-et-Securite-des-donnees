# 🔐 Secure Messaging Platform - WhatsApp Style

Une application de messagerie sécurisée moderne avec interface WhatsApp utilisant **Message Authentication Codes (MAC)** pour garantir l'intégrité et l'authenticité des messages.  
Développée dans le cadre d'un projet académique en cryptographie appliquée.

---

## 🧩 Vue d'ensemble

Cette plateforme permet aux utilisateurs d'échanger des messages de manière sécurisée avec une interface moderne similaire à WhatsApp.  
Chaque message est vérifié avec un **MAC (Message Authentication Code)** avant d'être affiché, garantissant:
- **Intégrité** – les messages ne peuvent pas être modifiés sans détection  
- **Authenticité** – le destinataire peut vérifier que les messages proviennent bien de l'expéditeur légitime  
- **Interface moderne** – expérience utilisateur intuitive de type WhatsApp

---

## ⚙️ Fonctionnalités

### 🔒 Sécurité
- Chiffrement des messages avec CBC-MAC utilisant AES-256
- Vérification d'intégrité en temps réel
- Authentification sécurisée des utilisateurs
- Détection automatique des messages compromis

### 💬 Interface Utilisateur
- Interface moderne type WhatsApp avec CustomTkinter
- Liste des conversations avec contacts
- Bulles de messages avec indicateurs d'état
- Notifications de messages non lus
- Recherche dans les conversations

### 🗄️ Données
- Base de données SQLite locale sécurisée
- Gestion des utilisateurs et conversations
- Historique complet des messages
- Métadonnées de vérification d'intégrité

---

## 📁 Architecture Modulaire

```
Projet-de-Cryptographie-et-Securite-des-donnees/
├── main.py                 # Point d'entrée principal
├── gui.py                  # Interface graphique WhatsApp Style
├── database.py             # Gestionnaire de base de données
├── crypto.py               # Module cryptographique (CBC-MAC)
├── user_manager.py         # Gestion des utilisateurs
├── message_manager.py      # Gestion des messages
├── requirements.txt        # Dépendances Python
└── README.md              # Cette documentation
```

### 🏗️ Composants

1. **database.py** - Gestionnaire de base de données SQLite
   - Gestion des utilisateurs, messages et conversations
   - Connexions sécurisées avec gestion d'erreurs
   - Index optimisés pour les performances

2. **crypto.py** - Module cryptographique
   - Implémentation du CBC-MAC avec AES-256
   - Génération de clés partagées déterministes
   - Vérification d'intégrité des messages

3. **user_manager.py** - Gestion des utilisateurs
   - Inscription avec validation complète
   - Authentification sécurisée
   - Gestion des profils utilisateurs

4. **message_manager.py** - Gestion des messages
   - Envoi de messages avec MAC
   - Vérification d'intégrité automatique
   - Historique des conversations

5. **gui.py** - Interface graphique moderne
   - Design WhatsApp avec CustomTkinter
   - Conversations en temps réel
   - Indicateurs visuels d'intégrité

---

## 🧠 Principe Cryptographique

Le projet démontre l'utilisation des **Message Authentication Codes (MACs)** pour garantir des communications sécurisées.

### Processus de sécurisation d'un message

1. **Génération de clé partagée**:
   ```
   key = SHA256(sorted(email1 + email2))
   ```

2. **Calcul du CBC-MAC**:
   ```
   MAC = CBC-AES-256(key, padded_message, IV)[-16:]
   ```

3. **Stockage sécurisé**:
   ```
   stored_data = {content, MAC, IV, metadata}
   ```

4. **Vérification d'intégrité**:
   ```
   calculated_MAC = CBC-AES-256(key, received_message, stored_IV)
   is_valid = (calculated_MAC == stored_MAC)
   ```

---

## 🚀 Installation et Utilisation

### Prérequis
- Python 3.8 ou supérieur
- pip (gestionnaire de packages Python)

### Installation

1. **Cloner le projet**:
   ```bash
   git clone <repository-url>
   cd Projet-de-Cryptographie-et-Securite-des-donnees
   ```

2. **Installer les dépendances**:
   ```bash
   pip install -r requirements.txt
   ```

### Utilisation en Réseau Local (Recommandé)

#### 1. Démarrer le serveur

Sur la machine qui hébergera le serveur :

```bash
# Lancement simple (écoute sur toutes les interfaces)
python launch_server.py

# Lancement avec options
python launch_server.py --port 8080        # Port personnalisé
python launch_server.py --local            # IP locale uniquement
python launch_server.py --info             # Afficher les infos réseau
```

Le serveur affichera les informations de connexion :
```
🔗 INFORMATIONS DE CONNEXION POUR LES CLIENTS
===============================================
📱 Pour connecter les clients :
   • Sur cette machine : 127.0.0.1:12345
   • Sur le réseau local : 192.168.1.100:12345
```

#### 2. Lancer les clients

Sur chaque machine cliente :

```bash
# Lancement normal (avec configuration dans l'interface)
python launch_client.py

# Avec adresse serveur prédéfinie
python launch_client.py --server 192.168.1.100

# Mode hors ligne (base de données locale)
python launch_client.py --offline
```

### Utilisation Hors Ligne (Mode Legacy)

Pour utiliser l'ancienne interface sans réseau :

```bash
python main.py --offline
```

### Options Avancées

```bash
# Serveur
python launch_server.py --help

# Client  
python launch_client.py --help

# Tests et développement
python main.py --demo-data          # Créer des utilisateurs de test
python main.py --test               # Lancer les tests
python main.py --check-deps         # Vérifier les dépendances
```

---

## 👥 Guide d'utilisation

### Configuration Réseau

1. **Démarrer le serveur**:
   - Lancez `python launch_server.py` sur une machine du réseau
   - Notez l'adresse IP affichée (ex: 192.168.1.100:12345)
   - Le serveur reste actif et gère les connexions

2. **Configurer les clients**:
   - Lancez `python launch_client.py` sur chaque machine cliente
   - Saisissez l'adresse IP du serveur (192.168.1.100)
   - Port : 12345 (ou celui configuré)
   - Cliquez sur "Se connecter au serveur"

### Première utilisation

1. **Créer un compte**:
   - Après connexion au serveur, cliquez sur "Créer un nouveau compte"
   - Remplissez le formulaire d'inscription
   - Utilisez un email valide (gmail.com, yahoo.com, etc.)

2. **Se connecter**:
   - Entrez votre email et mot de passe
   - Cliquez sur "Se connecter"

3. **Démarrer une conversation**:
   - Cliquez sur "💬 Nouvelle conversation"
   - Entrez l'email d'un contact existant
   - Commencez à échanger des messages **en temps réel**

### Fonctionnalités Réseau

- **Messages en temps réel**: Les messages apparaissent instantanément
- **Statut en ligne**: 🟢 indique les contacts connectés
- **Synchronisation**: Toutes les conversations sont synchronisées
- **Mode hors ligne**: Bascule automatique si le serveur est indisponible

### Fonctionnalités de Sécurité

- **Vérification d'intégrité**: Messages compromis marqués en rouge avec ⚠️
- **Statut des messages**: ✓ pour vérifiés, ⚠️ pour compromis
- **Chiffrement**: CBC-MAC avec AES-256 pour chaque message
- **Messages non lus**: Compteur rouge sur les conversations

---

## 🔒 Sécurité

### Mesures de sécurité implémentées

1. **Cryptographie**:
   - AES-256 en mode CBC pour le calcul du MAC
   - Clés déterministes basées sur les emails des utilisateurs
   - IV (vecteur d'initialisation) aléatoire pour chaque message

2. **Authentification**:
   - Hachage SHA-256 des mots de passe
   - Validation côté client et serveur
   - Sessions utilisateur sécurisées

3. **Intégrité des données**:
   - Vérification automatique de chaque message
   - Détection des modifications malveillantes
   - Alertes visuelles pour les messages compromis

### Limitations (à des fins éducatives)

⚠️ **Important**: Cette application est développée à des fins éducatives. Pour un usage en production, les améliorations suivantes seraient nécessaires:

- Utilisation de HMAC au lieu de CBC-MAC pour une sécurité renforcée
- Échange de clés sécurisé (Diffie-Hellman, RSA)
- Chiffrement du contenu des messages (pas seulement MAC)
- Authentification à deux facteurs
- Audit et logging de sécurité

---

## 🧪 Tests et Démonstration

### Tests automatiques

```bash
# Lancer les tests de base
python main.py --test
```

### Démonstration de l'intégrité

1. **Créer des utilisateurs de test**:
   ```bash
   python main.py --demo-data
   ```
   Cela crée alice@gmail.com et bob@gmail.com (mot de passe: SecurePass123!)

2. **Tester la détection de modifications**:
   - Connectez-vous avec Alice
   - Envoyez un message à Bob
   - Modifiez manuellement le message dans la base de données
   - Observez la détection automatique de la corruption

### Base de données

L'application utilise SQLite avec le fichier `secure_messaging.db`. Vous pouvez l'examiner avec:

```bash
sqlite3 secure_messaging.db
.tables
.schema messages
```

---

## 📊 Structure de la Base de Données

### Table `users`
```sql
CREATE TABLE users (
    email TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    birthday TEXT,
    phone_number TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME
);
```

### Table `messages`
```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_email TEXT NOT NULL,
    receiver_email TEXT NOT NULL,
    content TEXT NOT NULL,
    mac TEXT NOT NULL,        -- Format: "iv_hex:mac_hex"
    position INTEGER NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN DEFAULT FALSE
);
```

### Table `conversations`
```sql
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user1_email TEXT NOT NULL,
    user2_email TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_message_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_message_id INTEGER
);
```

---

## 🐛 Dépannage

### Erreurs courantes

1. **"Module customtkinter not found"**:
   ```bash
   pip install customtkinter
   ```

2. **"Database locked"**:
   - Fermez toutes les instances de l'application
   - Redémarrez l'application

3. **"Permission denied"**:
   - Vérifiez les permissions du répertoire
   - Lancez avec des privilèges appropriés

### Logs

Les logs sont sauvegardés dans `secure_messaging.log` pour le débogage.

---

## 🤝 Contribution

Ce projet est développé à des fins éducatives. Pour contribuer:

1. Fork le projet
2. Créez une branche pour votre fonctionnalité
3. Commitez vos changements
4. Poussez vers la branche
5. Ouvrez une Pull Request

---

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.

---

## 👨‍💻 Auteurs

Développé dans le cadre d'un projet académique en cryptographie et sécurité des données.

---

## 📞 Support

Pour toute question ou problème:
- Consultez les logs dans `secure_messaging.log`
- Vérifiez la documentation des modules dans le code
- Utilisez `python main.py --help` pour l'aide

---

*🔐 Secure Messaging - Démonstration pratique de cryptographie appliquée*
