# Observabilité des systèmes - Projet

Bienvenue dans le projet en Observabilité des systèmes !

Dans ce README, vous trouverez un environnement d'application mock Python/Flask conçu pour tester vos compétences en matière d'observabilité et de surveillance.

## Votre Mission
Votre objectif est de construire une infrastructure de surveillance complète pour cette application. Vous devez mettre en œuvre une pile complète d'observabilité (par exemple, Prometheus, Grafana, Zabbix, stack ELK) pour collecter efficacement les métriques et les données de journalisation.

**Attention :** Le serveur API contient un "Simulateur de Chaos" et est intrinsèquement instable. Il connaîtra des incidents critiques à des intervalles aléatoires (tels qu'une forte utilisation du CPU, des fuites de mémoire ou des pannes soudaines). Votre pile de surveillance doit vous permettre de détecter ces problèmes le plus rapidement possible et de diagnostiquer la cause profonde à l'aide des journaux et des métriques.

## Fonctionnalités du Serveur pour le Cours
1. **Métriques** : Le serveur exécute [`prometheus-flask-exporter`](https://github.com/rycus86/prometheus_flask_exporter/tree/0.23.2) quibind automatiquement une route `/metrics` sur le port 5000. Les étudiants peuvent extraire cela en utilisant Prometheus pour visualiser les temps de réponse HTTP, les taux de demande, les fréquences d'erreurs 4xx/5xx, etc.
2. **Journaux** : Le serveur crée des journaux très détaillés (`server.log`) en utilisant différents niveaux de journalisation (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`).
3. **Incidents Aléatoires** : En arrière-plan, un thread exécute un "simulateur de chaos" qui finira par faire tomber le serveur, nécessitant que les étudiants surveillent les journaux et les métriques pour découvrir exactement pourquoi l'application a cessé de répondre (par exemple, pic de CPU à 100 %, erreur de mémoire ou panne explicite).

## Fonctionnalités du Client
- Simule un trafic web réaliste.
- Varie le taux de demande de manière aléatoire pour créer des pics de trafic intéressants dans Prometheus.
- Crée `client.log`, qui suit la latence et les codes de statut HTTP, simulant la perspective de l'utilisateur final.

## Structure du Projet
- `server/server.py` : Une API Python construite avec Flask. L'application expose automatiquement un point d'accès `/metrics` pour Prometheus et écrit des journaux détaillés à plusieurs niveaux dans `server.log`.
- `client/client.py` : Un client utilisateur simulé. Il consomme continuellement l'API, variant les taux de demande et générant des modèles de trafic réalistes. Il enregistre également les erreurs et la latence du point de vue de l'utilisateur dans `client.log`.
- `requirements.txt` : Les dépendances Python requises pour exécuter cette application.

## Instructions d'Installation

### Option 1 : Exécuter avec Docker (Recommandé)
C'est le moyen le plus rapide de démarrer l'environnement avec un bon réseau.

1. Assurez-vous d'avoir **Docker** et **Docker Compose** installés.
2. Exécutez la commande suivante depuis le répertoire racine :
   ```bash
   docker compose up --build
   ```
   > **Note :** L'API sera disponible sur `http://localhost:5000` et les métriques sur `http://localhost:5000/metrics`.

---

### Option 2 : Exécuter Localement
Si vous préférez exécuter les scripts Python directement sur votre machine hôte.

1. Installez les dépendances requises pour les deux composants :
   ```bash
   pip install -r server/requirements.txt
   pip install -r client/requirements.txt
   ```
2. Dans votre premier terminal, démarrez le **Serveur API** :
   ```bash
   cd server
   python server.py
   ```
   > **Note :** L'API sera disponible sur `http://localhost:5000` et les métriques seront exposées sur `http://localhost:5000/metrics`.

3. Dans un deuxième terminal, démarrez le **Client** :
   ```bash
   cd client
   python client.py
   ```

---

## Étapes Finales
Une fois les services en cours d'exécution :
1. Connectez votre pile d'observabilité (ElasticSearch / Logstash / Kibana / etc.).
2. Surveillez les métriques et les journaux (`server.log` et `client.log`).
3. Préparez-vous pour l'incident inévitable. Bonne chance !