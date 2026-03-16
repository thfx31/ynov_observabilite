# Stack ELK — TP Observabilité Ynov M2

## Prérequis

- Docker + Docker Compose installés
- `git` installé
- `nc` (netcat) installé
- `vm.max_map_count` configuré (requis par Elasticsearch)

```bash
sudo sysctl -w vm.max_map_count=262144
# Permanent :
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
```

---

## Installation

```bash
git clone https://github.com/deviantony/docker-elk.git elk
cd elk
```

---

## Configuration

### 1. Pipeline Logstash

Remplacer le contenu de `logstash/pipeline/logstash.conf` :

```ruby
input {
  tcp {
    port => 50000
    codec => line
  }
}

filter {
  # Ignorer les lignes sans timestamp
  if [message] !~ /^\d{4}-\d{2}-\d{2}/ {
    drop { }
  }

  grok {
    match => {
      "message" => "%{TIMESTAMP_ISO8601:timestamp} - %{LOGLEVEL:level} - \[%{DATA:service}\] - %{GREEDYDATA:log_message}"
    }
  }

  # Nettoyer les séquences ANSI
  mutate {
    gsub => [
      "log_message", "\e\[[0-9;]*m", "",
      "log_message", "\[[0-9]+m", ""
    ]
  }

  date {
    match => ["timestamp", "yyyy-MM-dd HH:mm:ss,SSS"]
    target => "@timestamp"
  }

  mutate {
    remove_field => ["timestamp", "message", "event", "tags"]
  }
}

output {
  elasticsearch {
    hosts => ["http://elasticsearch:9200"]
    index => "ynov-logs-%{+YYYY.MM.dd}"
    user => "elastic"
    password => "changeme"
  }
}
```

---

## Démarrage

### 1. Initialiser les utilisateurs

```bash
docker compose up setup
```

### 2. Lancer la stack

```bash
docker compose up -d
```

### 3. Vérifier que tout est up

```bash
docker ps
```

Les conteneurs suivants doivent être en `Up` :
- `elk-elasticsearch-1`
- `elk-kibana-1`
- `elk-logstash-1`

---

## Injection des logs

```bash
cat logs/order_service.log | nc localhost 50000
cat logs/product_service.log | nc localhost 50000
cat logs/user_service.log | nc localhost 50000
```

Vérifier que les données sont bien indexées :

```bash
curl -s http://localhost:9200/_cat/indices -u elastic:changeme | grep ynov
```

---

## Kibana

Accès : [http://localhost:5601](http://localhost:5601)

- **Login** : `elastic`
- **Mot de passe** : `changeme`

### Créer le Data View

1. **Analytics → Discover**
2. **Create a data view**
3. Index pattern : `ynov-logs-*`
4. Timestamp field : `@timestamp`
5. **Save data view to Kibana**

---

## Dashboard

Accès : **Analytics → Dashboard → Create dashboard**

### Visualisation 1 — Répartition par service
- Type : **Pie**
- Slice by : `service.keyword`
- Metric : Count of records

### Visualisation 2 — Répartition par niveau de log
- Type : **Pie**
- Slice by : `level.keyword`
- Metric : Count of records

### Visualisation 3 — Volume par service
- Type : **Bar**
- Horizontal axis : `service.keyword`
- Vertical axis : Count of records

### Visualisation 4 — Erreurs et warnings par service
- Type : **Bar**
- Horizontal axis : `service.keyword`
- Vertical axis : Count of records
- Filtre KQL : `level.keyword : WARNING or level.keyword : ERROR`

---

## Structure du projet

```
elk/
├── .env                          # Mots de passe de la stack
├── docker-compose.yml            # Stack ELK
├── logstash/
│   └── pipeline/
│       └── logstash.conf         # Pipeline d'ingestion des logs
└── logs/                         # Fichiers de logs à analyser
    ├── order_service.log
    ├── product_service.log
    └── user_service.log
```

---

## Arrêt et nettoyage

```bash
# Arrêter la stack
docker compose down

# Arrêter et supprimer les volumes (repart de zéro)
docker compose down -v
```
