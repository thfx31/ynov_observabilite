# TP Observabilité : Automatisation du monitoring avec Zabbix 7.0

Mise en place d'une infrastructure de monitoring auto-adaptative utilisant Zabbix et Docker. Le système détecte automatiquement les nouveaux serveurs (auto-scaling) et les intègre dans un dashboard dynamique.

![Aperçu du Dashboard Dynamique](img/autoscalling.png)

---

## 1. Déploiement de l'infrastructure


**Docker Compose (Stack Serveur)**

Le fichier docker-compose.yml déploie le serveur Zabbix, une base de données PostgreSQL, l'interface Web (Nginx) et un agent local.

```bash
docker-compose up -d
```

**Note** : L'interface est accessible sur http://localhost:8080 (Admin / zabbix).

---

## 2. Configuration de l'Auto-Scaling (Auto-Registration)

Pour que les nouveaux serveurs soient ajoutés automatiquement, nous utilisons l'Active Agent Auto-Registration.

**Etapes de configuration dans l'interface :**

- Menu : Alerts > Actions > Autoregistration actions
- Action : Créer une règle nommée "Auto-Registration Linux"
- Condition : Host name contains Server-Auto
    - Opérations :
        - Add host : Crée l'objet dans l'inventaire
        - Add to host groups : Linux server
        - Link to templates : Linux by Zabbix agent active

&nbsp;
**Simulation d'un nouveau serveur :**

Pour simuler l'ajout d'une machine dans le cluster, on lance un conteneur agent avec des variables d'environnement spécifiques :
```bash
docker run -d --name agent-scaling-1 \
  --network <NOM_DU_RESEAU_DOCKER> \
  -e ZBX_HOSTNAME=Server-Auto-Test \
  -e ZBX_SERVER_ACTIVE=zabbix-server \
  zabbix/zabbix-agent:7.0-alpine-latest
```

---

## 3. Dashboard dynamique

**Configuration des Widgets :**
Add widget -> type Graph -> Name CPU Load
- Dataset : 
    - host patterns : ```Server-Auto-"```
    - item pattern : ```Linux Load Average```

Dès qu'un serveur finit son auto-registration :
- Il apparaît dans la liste du Host Navigator
- En cliquant dessus, le graphique CPU Load se met à jour instantanément pour afficher ses données propres.

---

## 4. Monitoring de microservices Python

### Architecture

Trois microservices Flask (user, product, order) sont déployés via Docker Compose. Chaque microservice est accompagné d'un agent Zabbix dédié en sidecar, connecté au réseau Zabbix existant.

```
┌─────────────────────────────────────────────────────────┐
│  docker-compose.yml          réseau: zabbix-net         │
│  ┌──────────────┐  ┌───────────┐  ┌──────────────────┐  │
│  │ zabbix-server│  │ zabbix-db │  │    zabbix-web    │  │
│  │   :10051     │  │ (postgres)│  │     :8080        │  │
│  └──────────────┘  └───────────┘  └──────────────────┘  │
├─────────────────────────────────────────────────────────┤
│  docker-compose-microservices.yml   external: zabbix-net│
│                                                         │
│  ┌──────────────────┐  ┌────────────────────────────┐   │
│  │  user_service    │  │  zabbix-agent-user         │   │
│  │  Flask :5003     │  │  ZBX_HOSTNAME=user_service │   │
│  └──────────────────┘  └────────────────────────────┘   │
│  ┌──────────────────┐  ┌────────────────────────────┐   │
│  │  product_service │  │  zabbix-agent-product      │   │
│  │  Flask :5002     │  │  ZBX_HOSTNAME=product_svc  │   │
│  └──────────────────┘  └────────────────────────────┘   │
│  ┌──────────────────┐  ┌────────────────────────────┐   │
│  │  order_service   │  │  zabbix-agent-order        │   │
│  │  Flask :5001     │  │  ZBX_HOSTNAME=order_svc    │   │
│  └──────────────────┘  └────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Réseau partagé

Le compose Zabbix déclare un réseau avec un nom fixe pour permettre le partage :

```yaml
# dans docker-compose.yml
networks:
  zabbix-net:
    driver: bridge
    name: zabbix-net
```

Le compose microservices s'y connecte en `external` :

```yaml
# dans docker-compose-microservices.yml
networks:
  zabbix-net:
    external: true
```

### Déploiement

```bash
# 1. Lancer la stack Zabbix (crée le réseau zabbix-net)
docker compose -f docker-compose.yml up -d

# 2. Lancer les microservices + leurs agents
cd microservice_python
docker compose -f docker-compose-microservices.yml up -d --build
```

### Auto-registration des microservices

L'auto-registration est configurée de la même manière que pour les agents de scaling (section 2), avec une condition adaptée :

- Menu : Alerts > Actions > Autoregistration actions
- Condition : Host name contains `_service`
- Opérations :
    - Add to host groups : Microservices (créer le groupe)
    - Link to templates : Linux by Zabbix agent active

Les agents utilisent `ZBX_SERVER_ACTIVE`, ce qui déclenche l'enregistrement automatique dès le démarrage du conteneur.

### Vérification

```bash
# Vérifier que les agents contactent le serveur
docker logs zabbix-agent-user
docker logs zabbix-agent-product
docker logs zabbix-agent-order
```

Le message `active checks #1 started` confirme la connexion. Si `host [xxx] not found` apparaît, l'action d'auto-registration n'a pas encore été créée ou la condition ne matche pas le hostname.

### Endpoints des microservices

| Service | URL | Méthodes |
|---------|-----|----------|
| User    | http://localhost:5003/user | GET, POST, DELETE |
| Product | http://localhost:5002/product | GET |
| Order   | http://localhost:5001/order | GET |

**Test des endpoints :**

```bash
# === User Service ===

# Lister les utilisateurs
curl http://localhost:5003/user

# Créer un utilisateur
curl -X POST http://localhost:5003/user \
  -H "Content-Type: application/json" \
  -d '{"id": "1", "name": "Thomas"}'

# Supprimer un utilisateur
curl -X DELETE "http://localhost:5003/user?id=1"

# === Product Service ===

# Lister les produits
curl http://localhost:5002/product

# === Order Service ===

# Lister les commandes
curl http://localhost:5001/order
```

---

## 5. Troubleshooting

Pour vérifier la communication entre un nouvel agent et le serveur :
```bash
docker logs agent-scaling-1
```
- ```active checks #1 started``` : connexion réussie
- ```host [Server-Auto-Test] not found``` : l'agent contacte le serveur mais l'action d'Auto-registration n'est pas encore active