# ⚙️ Auto-Ngrok Remote Administration Tool

A standalone Python-based Remote Administration Tool (RAT) featuring automated Ngrok tunneling and single-file compilation. Designed for simplified remote server administration and security testing.

> ⚠️ **DISCLAIMER / LEGAL NOTICE**
> 
> This project is developed **strictly for educational purposes and authorized penetration testing / remote administration**. Unauthorized access to computer systems is illegal. The developer assumes no liability and is not responsible for any misuse or damage caused by this program.

---

## ✨ Key Features

* **Automated Ngrok Tunneling:** Automatically establishes a secure reverse proxy using Ngrok on launch — no manual router port-forwarding required.
* **Single-File Binary:** Fully compatible with `PyInstaller` for bundling all dependencies into a single executable (`.exe`).
* **Remote Shell Access:** Execute commands and handle system interactions over secure socket tunnels.
* **Connection Resilience:** Built-in reconnection logic in case of network interruptions.

---

## 🛠️ Requirements

* **Python 3.8+**
* **Ngrok Auth Token** (Get your token at [ngrok.com](https://ngrok.com))

---

## 🚀 Getting Started

1. **Clone the Repository:**
   ```bash
   git clone [https://github.com/z1gres/auto-ngrok-rat.git](https://github.com/z1gres/auto-ngrok-rat.git)
   cd auto-ngrok-rat
