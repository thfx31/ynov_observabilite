# TP Observabilité — Ynov M2 Cloud, Sécurité et Infrastructure

Ce dépôt regroupe deux travaux pratiques sur l'observabilité des systèmes, couvrant deux approches complémentaires : la centralisation de logs et traces avec la stack ELK, et le monitoring d'infrastructure avec Zabbix.

---

## Projets

### 1. Stack ELK + Jaeger — Logs & Tracing distribué

**Dossier :** [elk/](elk/)
**Documentation complète :** [elk/README.md](elk/README.md)

Mise en place d'une pipeline d'observabilité basée sur la stack ELK (Elasticsearch, Logstash, Kibana) complétée par Filebeat pour la collecte des logs Docker et Jaeger pour le tracing distribué OpenTelemetry.

| Composant | Rôle |
|-----------|------|
| Elasticsearch | Stockage et indexation des logs et traces |
| Logstash | Ingestion, parsing et routage des logs |
| Kibana | Dashboards et exploration des logs |
| Filebeat | Collecte des logs Docker |
| Jaeger | Visualisation des traces distribuées (OTLP) |

Les applications Python instrumentées envoient leurs traces via OpenTelemetry, corrélables avec leurs logs dans Kibana via `trace_id` / `span_id`.

---

### 2. Zabbix 7.0 — Monitoring auto-adaptatif

**Dossier :** [zabbix/](zabbix/)
**Documentation complète :** [zabbix/README.md](zabbix/README.md)

Déploiement d'une infrastructure de monitoring auto-adaptative avec Zabbix 7.0. Le système détecte automatiquement les nouveaux serveurs (auto-scaling) via l'Active Agent Auto-Registration et les intègre dans un dashboard dynamique.

| Composant | Rôle |
|-----------|------|
| Zabbix Server | Collecte et traitement des métriques |
| PostgreSQL | Base de données Zabbix |
| Zabbix Web (Nginx) | Interface web sur http://localhost:8080 |
| Agents Zabbix | Monitoring des hôtes et microservices Python |

Trois microservices Flask (user, product, order) sont monitorés via des agents Zabbix en sidecar, connectés au réseau Zabbix existant.
