# DoD Deployment Guide

Production deployment strategies and operational guidance for the Definition of Done automation system.

## Table of Contents
- [Deployment Overview](#deployment-overview)
- [Container Deployment](#container-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Environment Configuration](#environment-configuration)
- [Service Discovery](#service-discovery)
- [Scaling Strategies](#scaling-strategies)
- [Monitoring Setup](#monitoring-setup)
- [Backup and Recovery](#backup-and-recovery)

## Deployment Overview

The DoD automation system can be deployed in multiple configurations:

### Deployment Patterns
- **Standalone CLI**: Direct installation on developer machines
- **Centralized Service**: REST API service for team/enterprise use
- **CI/CD Integration**: Embedded in pipeline containers
- **Kubernetes Operator**: Cloud-native orchestrated deployment

### Architecture Tiers
```
┌─────────────────────────────────────┐
│           Load Balancer             │
├─────────────────────────────────────┤
│        DoD API Services             │
│    (Horizontal Pod Autoscaler)      │
├─────────────────────────────────────┤
│       Configuration Storage         │
│     (ConfigMaps, Secrets)           │
├─────────────────────────────────────┤
│      OpenTelemetry Collector        │
│   (Traces, Metrics, Logs)           │
├─────────────────────────────────────┤
│        Persistent Storage           │
│   (PVC, Object Storage)             │
└─────────────────────────────────────┘
```

## Container Deployment

### Docker Image Build

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ src/
COPY setup.py .
COPY README.md .

# Install uvmgr
RUN pip install -e .

# Create non-root user
RUN useradd -m -u 1000 uvmgr && chown -R uvmgr:uvmgr /app
USER uvmgr

# Set up health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD uvmgr dod status --json || exit 1

# Default command
CMD ["uvmgr", "dod", "serve"]

# Labels for metadata
LABEL org.opencontainers.image.title="uvmgr-dod"
LABEL org.opencontainers.image.description="Definition of Done automation system"
LABEL org.opencontainers.image.version="2.1.0"
LABEL org.opencontainers.image.vendor="Your Organization"
```

### Multi-Stage Build

```dockerfile
# Multi-stage Dockerfile for optimized production image
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt

# Copy source and build package
COPY . .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels .

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder stage
COPY --from=builder /build/wheels /wheels

# Install from wheels (much faster)
RUN pip install --no-cache /wheels/*

# Create non-root user
RUN useradd -m -u 1000 uvmgr
USER uvmgr

# Health check
HEALTHCHECK --interval=30s --timeout=10s \
  CMD uvmgr dod status --json || exit 1

EXPOSE 8080
CMD ["uvmgr", "dod", "serve", "--host", "0.0.0.0", "--port", "8080"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  uvmgr-dod:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8080:8080"
    environment:
      - DOD_CONFIG_PATH=/config/dod.yaml
      - OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
      - OTEL_SERVICE_NAME=uvmgr-dod
      - OTEL_SERVICE_VERSION=2.1.0
    volumes:
      - ./config:/config:ro
      - ./data:/data
      - ./logs:/app/logs
    depends_on:
      - otel-collector
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
    
  otel-collector:
    image: otel/opentelemetry-collector-contrib:latest
    ports:
      - "4317:4317"  # OTLP gRPC
      - "4318:4318"  # OTLP HTTP
      - "8888:8888"  # Metrics
    volumes:
      - ./otel-collector.yaml:/etc/otel-collector.yaml:ro
    command: ["--config=/etc/otel-collector.yaml"]
    
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes
    
  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"
      - "14268:14268"
    environment:
      - COLLECTOR_OTLP_ENABLED=true

volumes:
  redis-data:
```

## Kubernetes Deployment

### Namespace Setup

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: uvmgr-dod
  labels:
    name: uvmgr-dod
    app.kubernetes.io/name: uvmgr-dod
    app.kubernetes.io/version: "2.1.0"
```

### ConfigMap

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: uvmgr-dod-config
  namespace: uvmgr-dod
data:
  dod.yaml: |
    automation:
      enabled: true
      level: "supervised"
      parallel: true
      
    criteria:
      testing:
        enabled: true
        coverage_threshold: 80
      security:
        enabled: true
        vulnerability_threshold: "medium"
      devops:
        enabled: true
        provider: "kubernetes"
        
    ai:
      enabled: true
      insights: true
      
    telemetry:
      enabled: true
      endpoint: "http://otel-collector.uvmgr-dod.svc.cluster.local:4317"
      service_name: "uvmgr-dod"
      service_version: "2.1.0"
      
  otel-collector.yaml: |
    receivers:
      otlp:
        protocols:
          grpc:
            endpoint: 0.0.0.0:4317
          http:
            endpoint: 0.0.0.0:4318
    
    processors:
      batch:
        timeout: 1s
        send_batch_size: 1024
      memory_limiter:
        limit_mib: 512
        
    exporters:
      jaeger:
        endpoint: jaeger.monitoring.svc.cluster.local:14250
        tls:
          insecure: true
      prometheus:
        endpoint: "0.0.0.0:8889"
        
    service:
      pipelines:
        traces:
          receivers: [otlp]
          processors: [memory_limiter, batch]
          exporters: [jaeger]
        metrics:
          receivers: [otlp]
          processors: [memory_limiter, batch]
          exporters: [prometheus]
```

### Secrets

```yaml
# secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: uvmgr-dod-secrets
  namespace: uvmgr-dod
type: Opaque
stringData:
  ai-api-key: "your-ai-api-key"
  github-token: "your-github-token"
  otel-api-key: "your-otel-api-key"
```

### Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: uvmgr-dod
  namespace: uvmgr-dod
  labels:
    app.kubernetes.io/name: uvmgr-dod
    app.kubernetes.io/version: "2.1.0"
spec:
  replicas: 3
  selector:
    matchLabels:
      app.kubernetes.io/name: uvmgr-dod
  template:
    metadata:
      labels:
        app.kubernetes.io/name: uvmgr-dod
        app.kubernetes.io/version: "2.1.0"
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: uvmgr-dod
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: uvmgr-dod
        image: your-registry/uvmgr-dod:2.1.0
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8080
          name: http
          protocol: TCP
        env:
        - name: DOD_CONFIG_PATH
          value: /config/dod.yaml
        - name: OTEL_EXPORTER_OTLP_ENDPOINT
          value: "http://otel-collector:4317"
        - name: OTEL_SERVICE_NAME
          value: "uvmgr-dod"
        - name: AI_API_KEY
          valueFrom:
            secretKeyRef:
              name: uvmgr-dod-secrets
              key: ai-api-key
        volumeMounts:
        - name: config
          mountPath: /config
          readOnly: true
        - name: data
          mountPath: /data
        resources:
          limits:
            cpu: 1000m
            memory: 1Gi
          requests:
            cpu: 500m
            memory: 512Mi
        livenessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: http
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
      volumes:
      - name: config
        configMap:
          name: uvmgr-dod-config
      - name: data
        persistentVolumeClaim:
          claimName: uvmgr-dod-data
      terminationGracePeriodSeconds: 30
```

### Service

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: uvmgr-dod
  namespace: uvmgr-dod
  labels:
    app.kubernetes.io/name: uvmgr-dod
spec:
  type: ClusterIP
  ports:
  - port: 80
    targetPort: http
    protocol: TCP
    name: http
  selector:
    app.kubernetes.io/name: uvmgr-dod
```

### Horizontal Pod Autoscaler

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: uvmgr-dod
  namespace: uvmgr-dod
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: uvmgr-dod
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
      - type: Pods
        value: 4
        periodSeconds: 15
      selectPolicy: Max
```

### Ingress

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: uvmgr-dod
  namespace: uvmgr-dod
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
spec:
  tls:
  - hosts:
    - dod.your-domain.com
    secretName: uvmgr-dod-tls
  rules:
  - host: dod.your-domain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: uvmgr-dod
            port:
              number: 80
```

## Environment Configuration

### Development Environment

```yaml
# environments/development.yaml
metadata:
  namespace: uvmgr-dod-dev
  
spec:
  replicas: 1
  
  env:
    - name: DOD_LOG_LEVEL
      value: "DEBUG"
    - name: DOD_ENVIRONMENT
      value: "development"
    - name: OTEL_TRACES_SAMPLER_ARG
      value: "1.0"  # 100% sampling
      
  resources:
    limits:
      cpu: 500m
      memory: 512Mi
    requests:
      cpu: 250m
      memory: 256Mi
```

### Staging Environment

```yaml
# environments/staging.yaml
metadata:
  namespace: uvmgr-dod-staging
  
spec:
  replicas: 2
  
  env:
    - name: DOD_LOG_LEVEL
      value: "INFO"
    - name: DOD_ENVIRONMENT
      value: "staging"
    - name: OTEL_TRACES_SAMPLER_ARG
      value: "0.1"  # 10% sampling
      
  resources:
    limits:
      cpu: 1000m
      memory: 1Gi
    requests:
      cpu: 500m
      memory: 512Mi
```

### Production Environment

```yaml
# environments/production.yaml
metadata:
  namespace: uvmgr-dod-prod
  
spec:
  replicas: 5
  
  env:
    - name: DOD_LOG_LEVEL
      value: "WARN"
    - name: DOD_ENVIRONMENT
      value: "production"
    - name: OTEL_TRACES_SAMPLER_ARG
      value: "0.01"  # 1% sampling
      
  resources:
    limits:
      cpu: 2000m
      memory: 2Gi
    requests:
      cpu: 1000m
      memory: 1Gi
      
  nodeSelector:
    node-type: "compute-optimized"
    
  tolerations:
  - key: "dedicated"
    operator: "Equal"
    value: "dod-workload"
    effect: "NoSchedule"
```

## Service Discovery

### Kubernetes Service Discovery

```yaml
# service-discovery.yaml
apiVersion: v1
kind: Service
metadata:
  name: uvmgr-dod-discovery
  namespace: uvmgr-dod
  annotations:
    service.alpha.kubernetes.io/tolerate-unready-endpoints: "true"
spec:
  clusterIP: None  # Headless service
  ports:
  - port: 8080
    name: http
  selector:
    app.kubernetes.io/name: uvmgr-dod
---
apiVersion: v1
kind: Endpoints
metadata:
  name: uvmgr-dod-discovery
  namespace: uvmgr-dod
subsets:
- addresses:
  - ip: 10.0.0.1
    hostname: uvmgr-dod-1
  - ip: 10.0.0.2
    hostname: uvmgr-dod-2
  ports:
  - port: 8080
    name: http
```

### Consul Integration

```yaml
# consul-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: consul-config
data:
  config.json: |
    {
      "datacenter": "dc1",
      "data_dir": "/consul/data",
      "log_level": "INFO",
      "server": true,
      "bootstrap": true,
      "ui": true,
      "bind_addr": "0.0.0.0",
      "client_addr": "0.0.0.0",
      "retry_join": ["consul-0.consul.consul.svc.cluster.local"],
      "connect": {
        "enabled": true
      },
      "services": [
        {
          "name": "uvmgr-dod",
          "port": 8080,
          "check": {
            "http": "http://localhost:8080/health",
            "interval": "10s"
          }
        }
      ]
    }
```

## Scaling Strategies

### Vertical Scaling

```yaml
# vertical-pod-autoscaler.yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: uvmgr-dod-vpa
  namespace: uvmgr-dod
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: uvmgr-dod
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: uvmgr-dod
      minAllowed:
        cpu: 100m
        memory: 128Mi
      maxAllowed:
        cpu: 2000m
        memory: 4Gi
      controlledResources: ["cpu", "memory"]
```

### Cluster Autoscaling

```yaml
# cluster-autoscaler.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cluster-autoscaler-status
  namespace: kube-system
data:
  nodes.max: "20"
  nodes.min: "3"
  scale-down-delay-after-add: "10m"
  scale-down-unneeded-time: "10m"
  skip-nodes-with-local-storage: "false"
  skip-nodes-with-system-pods: "false"
```

### Load Testing

```yaml
# load-test.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: uvmgr-dod-load-test
spec:
  template:
    spec:
      containers:
      - name: load-test
        image: loadimpact/k6:latest
        command: ["k6", "run", "--vus", "100", "--duration", "5m", "/scripts/load-test.js"]
        volumeMounts:
        - name: test-scripts
          mountPath: /scripts
      volumes:
      - name: test-scripts
        configMap:
          name: load-test-scripts
      restartPolicy: Never
  backoffLimit: 4
```

## Monitoring Setup

### ServiceMonitor for Prometheus

```yaml
# servicemonitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: uvmgr-dod
  namespace: uvmgr-dod
  labels:
    app.kubernetes.io/name: uvmgr-dod
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: uvmgr-dod
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
```

### PrometheusRule

```yaml
# prometheusrule.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: uvmgr-dod
  namespace: uvmgr-dod
spec:
  groups:
  - name: uvmgr-dod.rules
    rules:
    - alert: DoD_High_Error_Rate
      expr: rate(dod_automations_total{success="false"}[5m]) > 0.1
      for: 2m
      labels:
        severity: warning
      annotations:
        summary: "High DoD automation error rate"
        description: "Error rate is {{ $value }} errors/second"
        
    - alert: DoD_Service_Down
      expr: up{job="uvmgr-dod"} == 0
      for: 1m
      labels:
        severity: critical
      annotations:
        summary: "DoD service is down"
        description: "DoD service has been down for more than 1 minute"
```

## Backup and Recovery

### Data Backup Strategy

```yaml
# backup-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: uvmgr-dod-backup
  namespace: uvmgr-dod
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: your-registry/backup-tool:latest
            env:
            - name: BACKUP_SOURCE
              value: "/data"
            - name: BACKUP_DESTINATION
              value: "s3://your-backup-bucket/uvmgr-dod"
            - name: AWS_ACCESS_KEY_ID
              valueFrom:
                secretKeyRef:
                  name: aws-credentials
                  key: access-key-id
            - name: AWS_SECRET_ACCESS_KEY
              valueFrom:
                secretKeyRef:
                  name: aws-credentials
                  key: secret-access-key
            volumeMounts:
            - name: data
              mountPath: /data
              readOnly: true
            command:
            - /bin/sh
            - -c
            - |
              echo "Starting backup..."
              tar -czf /tmp/uvmgr-dod-$(date +%Y%m%d).tar.gz /data
              aws s3 cp /tmp/uvmgr-dod-$(date +%Y%m%d).tar.gz $BACKUP_DESTINATION/
              echo "Backup completed"
          volumes:
          - name: data
            persistentVolumeClaim:
              claimName: uvmgr-dod-data
          restartPolicy: OnFailure
```

### Disaster Recovery

```bash
#!/bin/bash
# disaster-recovery.sh

set -e

echo "🚨 Starting DoD disaster recovery..."

# 1. Scale down current deployment
echo "📉 Scaling down current deployment..."
kubectl scale deployment uvmgr-dod --replicas=0 -n uvmgr-dod

# 2. Restore data from backup
echo "💾 Restoring data from backup..."
BACKUP_DATE=${1:-$(date +%Y%m%d)}
aws s3 cp s3://your-backup-bucket/uvmgr-dod/uvmgr-dod-${BACKUP_DATE}.tar.gz /tmp/
kubectl exec -n uvmgr-dod backup-pod -- tar -xzf /tmp/uvmgr-dod-${BACKUP_DATE}.tar.gz -C /

# 3. Verify configuration
echo "🔍 Verifying configuration..."
kubectl get configmap uvmgr-dod-config -n uvmgr-dod -o yaml

# 4. Scale up deployment
echo "📈 Scaling up deployment..."
kubectl scale deployment uvmgr-dod --replicas=3 -n uvmgr-dod

# 5. Wait for readiness
echo "⏳ Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=uvmgr-dod -n uvmgr-dod --timeout=300s

# 6. Verify health
echo "🏥 Verifying service health..."
kubectl exec -n uvmgr-dod deploy/uvmgr-dod -- uvmgr dod status

echo "✅ Disaster recovery completed successfully!"
```

### Blue-Green Deployment

```yaml
# blue-green-deployment.yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: uvmgr-dod
  namespace: uvmgr-dod
spec:
  replicas: 5
  strategy:
    blueGreen:
      activeService: uvmgr-dod-active
      previewService: uvmgr-dod-preview
      autoPromotionEnabled: false
      scaleDownDelaySeconds: 30
      prePromotionAnalysis:
        templates:
        - templateName: success-rate
        args:
        - name: service-name
          value: uvmgr-dod-preview
      postPromotionAnalysis:
        templates:
        - templateName: success-rate
        args:
        - name: service-name
          value: uvmgr-dod-active
  selector:
    matchLabels:
      app: uvmgr-dod
  template:
    metadata:
      labels:
        app: uvmgr-dod
    spec:
      containers:
      - name: uvmgr-dod
        image: your-registry/uvmgr-dod:2.1.0
        ports:
        - containerPort: 8080
```

This comprehensive deployment guide provides production-ready configurations for deploying the DoD automation system across various environments and platforms.