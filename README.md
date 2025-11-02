# 🔐 Local Secure Messaging Platform

A lightweight local messaging application that ensures **message integrity and authenticity** using **Message Authentication Codes (MAC)**.  
Developed as part of an academic project in applied cryptography.

---

## 🧩 Overview

This platform allows users on the same local network to exchange messages securely.  
Each message is verified with a **MAC (Message Authentication Code)** before being displayed, ensuring:
- **Integrity** – messages cannot be modified without detection.  
- **Authenticity** – the receiver can verify that messages come from the legitimate sender.

---

## ⚙️ Features

- 🔒 Local message exchange with integrity verification  
- 🧠 Implementation of CBC-MAC using AES  
- 🗄️ SQLite database for user and message storage  
- 🖥️ Simple graphical interface built with Tkinter 

---

## 🧠 Cryptographic Principle

The project demonstrates the use of **Message Authentication Codes (MACs)** to ensure secure communication.  
Each message `M` is processed as:

