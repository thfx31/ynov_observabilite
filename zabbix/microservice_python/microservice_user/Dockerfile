# Utiliser une image de base Python
FROM python:3.13-slim

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier le fichier de dépendances et les installer
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du code de l'application
COPY . .

# Définir la commande par défaut pour exécuter l’application
# {mon_service} doit être modifié en fonction de votre application !
CMD ["python", "user_service.py"]
