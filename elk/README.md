# Documentation Stack ELK
**TP Observabilité — Ynov M2 Cloud, Sécurité et Infrastructure**

---

## 1. Présentation

La Stack ELK est un ensemble d'outils open source permettant la collecte, le stockage et la visualisation de logs et de traces distribuées.

| Composant | Rôle | Description |
|-----------|------|-------------|
| **Elasticsearch** | Moteur de recherche | Stockage et indexation des logs et des traces |
| **Logstash** | Collecte & traitement | Ingère, transforme et route les logs |
| **Kibana** | Visualisation | Interface web pour explorer et créer des dashboards |
| **Filebeat** | Agent de collecte | Lit les logs Docker et les transmet à Logstash |
| **Jaeger** | Tracing distribué | Collecte, stocke et visualise les traces OpenTelemetry |

---

## 2. Architecture

```
Conteneurs Docker (stdout)
       ↓
   Filebeat  ←── lit /var/lib/docker/containers
       ↓
   Logstash  ←── parse, filtre, enrichit (extrait trace_id/span_id)
       ↓
 Elasticsearch ←── stocke et indexe (logs + traces Jaeger)
     ↓   ↑
  Kibana   ←── visualise et analyse les logs
  Jaeger   ←── reçoit les traces OTLP (port 4317) des apps Python
               visualise les traces sur http://localhost:16686
```

---

## 3. Prérequis

- Docker Engine + Docker Compose
- `git`
- `nc` (netcat)
- `vm.max_map_count` configuré (requis par Elasticsearch)

```bash
# Temporaire
sudo sysctl -w vm.max_map_count=262144

# Permanent
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

---

## 4. Structure du projet

```
elk/
├── docker-compose.yml          # Stack ELK + Jaeger
├── filebeat/
│   └── filebeat.yml            # Config collecte Docker
├── logstash/
│   ├── config/
│   │   └── logstash.yml        # Config Logstash
│   └── pipeline/
│       └── logstash.conf       # Pipeline d'ingestion
├── logs/                       # Logs TP microservices
│   ├── order_service.log
│   ├── product_service.log
│   └── user_service.log
├── python_apps/                # Applications Python instrumentées OTel
│   ├── docker-compose.yml
│   ├── server/
│   └── client/
└── README.md
```

---

## 5. Configuration

### 5.1 Stack ELK (docker-compose.yml)

La sécurité est désactivée (`xpack.security.enabled=false`) pour simplifier le TP.

Points clés :
- `discovery.type=single-node` : nœud unique, pas de cluster
- `xpack.security.enabled=false` : pas d'authentification
- `ES_JAVA_OPTS=-Xms1g -Xmx1g` : limite RAM à 1 Go

### 5.2 Pipeline Logstash (logstash/pipeline/logstash.conf)

Le pipeline gère deux sources et deux formats de logs :

**Source 1 — Fichiers locaux** (logs TP microservices) via `input file`

**Source 2 — Beats** (logs Docker via Filebeat) via `input beats` sur le port 5044

**Formats supportés :**
- Avec `trace_id`/`span_id` : logs des apps Python server/client
- Sans `trace_id` : logs des microservices du TP

Un grok supplémentaire extrait `endpoint`, `http_code` et `latency_seconds` depuis les messages du client Python.

### 5.3 Jaeger (docker-compose.yml)

Jaeger utilise **Elasticsearch comme backend de stockage** (index `jaeger-*`), ce qui centralise logs et traces dans le même moteur.

Points clés :
- `SPAN_STORAGE_TYPE=elasticsearch` : traces stockées dans ES
- `COLLECTOR_OTLP_ENABLED=true` : accepte les traces au format OTLP (gRPC port 4317, HTTP port 4318)
- Jaeger ne démarre qu'une fois Elasticsearch déclaré **healthy** (healthcheck toutes les 10s, 20 tentatives max)

Les applications Python envoient leurs traces via la variable d'environnement `OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317`.

### 5.4 Filebeat (filebeat/filebeat.yml)

Collecte les logs de tous les conteneurs Docker via `/var/run/docker.sock` et les transmet à Logstash sur le port 5044.

> ⚠️ Le fichier `filebeat.yml` doit appartenir à root :
> ```bash
> sudo chown root:root filebeat/filebeat.yml
> ```

---

## 6. Démarrage

### Lancer la stack ELK

```bash
docker compose up -d
```

Vérifier que tous les conteneurs sont up :

```bash
docker ps
```

Conteneurs attendus : `elasticsearch`, `kibana`, `logstash`, `filebeat`, `jaeger`

> ℹ️ Jaeger démarre après Elasticsearch (healthcheck). Prévoir ~30s d'attente au premier démarrage.

### Lancer les applications Python

```bash
cd python_apps
docker compose up -d
```

### Injection manuelle des logs (TP microservices)

```bash
cat logs/order_service.log | nc localhost 50000
cat logs/product_service.log | nc localhost 50000
cat logs/user_service.log | nc localhost 50000
```

### Vérifier l'indexation

```bash
curl -s http://localhost:9200/_cat/indices | grep ynov
```

---

## 7. Interfaces web

| Interface | URL | Description |
|-----------|-----|-------------|
| **Kibana** | http://localhost:5601 | Dashboards logs |
| **Jaeger UI** | http://localhost:16686 | Visualisation des traces distribuées |

### Kibana

**Login :** `elastic`
**Mot de passe :** `changeme`

### Créer le Data View

Analytics → Discover → Create a data view

| Paramètre | Valeur |
|-----------|--------|
| Name | TP1 |
| Index pattern | `ynov-logs-*` |
| Timestamp field | `@timestamp` |

### Jaeger UI

Dans l'interface Jaeger (http://localhost:16686) :
1. Sélectionner un service (`api-server` ou `api-client`) dans le menu déroulant
2. Cliquer sur **Find Traces** pour lister les traces
3. Cliquer sur une trace pour voir le détail des spans et la propagation client → serveur

Le champ `trace_id` présent dans les logs Kibana correspond à l'ID de trace Jaeger — ce qui permet de corréler un log avec sa trace.

### Dashboards

| Visualisation | Type | Description |
|---------------|------|-------------|
| Répartition par service | Bar vertical stacked | Volume de logs par service avec breakdown par niveau |
| Latence par endpoint | Bar vertical | Latence moyenne en secondes par endpoint HTTP |
| Volume par endpoint | Bar vertical | Nombre de requêtes par endpoint |
| Proportion erreurs | Bar vertical percentage | Répartition des codes HTTP par service |
| Dernières erreurs | Table | Derniers événements WARNING/ERROR |
| Logs par span | Table | Tous les logs associés à un `span_id` donné |

### Corrélation Jaeger → Kibana via span_id

Le dashboard intègre un **contrôle `span_id`** permettant de filtrer dynamiquement les logs à partir d'un identifiant de span récupéré dans Jaeger.

**Workflow :**
1. Dans **Jaeger UI** (http://localhost:16686), naviguer jusqu'à une trace et copier le `span_id` d'un span d'intérêt
2. Dans **Kibana**, coller le `span_id` dans le contrôle de filtre du dashboard
3. La table **Logs par span** affiche tous les logs produits pendant l'exécution de ce span précis

Ce mécanisme permet de relier directement un span Jaeger à ses logs applicatifs, facilitant le diagnostic d'un appel spécifique sans avoir à filtrer manuellement.

---

## 8. Champs disponibles

| Champ | Type | Description |
|-------|------|-------------|
| `@timestamp` | date | Horodatage du log |
| `level` | keyword | Niveau : DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `service` | keyword | Nom du service émetteur |
| `log_message` | text | Message brut du log |
| `trace_id` | keyword | Identifiant de trace (logs Python) |
| `span_id` | keyword | Identifiant de span (logs Python) |
| `endpoint` | keyword | Endpoint HTTP (/data, /process...) |
| `http_code` | keyword | Code HTTP (200, 201, 404, 500...) |
| `latency_seconds` | float | Latence de la requête en secondes |
| `container.name` | keyword | Nom du conteneur Docker source |

---

## 9. Arrêt et nettoyage

```bash
# Arrêter la stack ELK
docker compose down

# Arrêter les apps Python
cd python_apps && docker compose down

# Tout supprimer (volumes inclus)
docker compose down -v

# Supprimer un index Elasticsearch
curl -X DELETE http://localhost:9200/ynov-logs-2026.03.16 -u elastic:changeme
```