# FastAPI GitOps POC with ArgoCD and Prometheus

This is a proof of concept demonstrating GitOps practices using:

- **FastAPI** - Python web framework
- **ArgoCD** - GitOps continuous delivery tool
- **Prometheus** - Monitoring and metrics collection
- **Grafana Loki** - Log aggregation system
- **Kubernetes** - Container orchestration

## Architecture Overview

```
┌─────────────┐
│   GitHub    │
│  Repository │
└──────┬──────┘
       │
       │ Git Push
       ▼
┌─────────────┐
│   ArgoCD    │
│  (GitOps)   │
└──────┬──────┘
       │
       │ Sync
       ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│ Kubernetes  │────▶│  Prometheus  │────▶│   Grafana   │
│  Cluster    │     │  (Metrics)   │     │ (Dashboard) │
└──────┬──────┘     └──────────────┘     └─────────────┘
       │
       │ Logs
       ▼
┌─────────────┐
│   Loki      │
│  (Logs)     │
└─────────────┘
```

## Project Structure

```
.
├── app/
│   ├── main.py              # FastAPI application
│   └── requirements.txt     # Python dependencies
├── k8s/
│   ├── namespace.yaml       # Kubernetes namespace
│   ├── configmap.yaml       # Application configuration
│   ├── deployment.yaml      # Application deployment
│   ├── service.yaml         # Kubernetes service
│   ├── service-monitor.yaml # Prometheus ServiceMonitor
│   └── kustomization.yaml   # Kustomize configuration
├── argocd/
│   └── application.yaml     # ArgoCD application definition
├── monitoring/
│   └── prometheus-config.yaml # Prometheus configuration
├── logging/
│   ├── loki-config.yaml     # Loki configuration
│   └── promtail-config.yaml # Promtail configuration
├── Dockerfile               # Container image definition
└── README.md               # This file
```

## Prerequisites

- Kubernetes cluster (minikube, kind, or cloud provider)
- kubectl configured to access your cluster
- Docker (for building images)
- ArgoCD installed in your cluster
- Prometheus Operator installed (for ServiceMonitor)
- Grafana Loki and Promtail installed (for logging)

## Setup Instructions

### 1. Build and Push Docker Image

```bash
# Build the Docker image
docker build -t fastapi-demo:latest .

# Tag for your registry (replace with your registry)
docker tag fastapi-demo:latest your-registry/fastapi-demo:latest

# Push to registry
docker push your-registry/fastapi-demo:latest
```

**Note**: Update the image in `k8s/deployment.yaml` with your registry path.

### 2. Install ArgoCD

```bash
# Create ArgoCD namespace
kubectl create namespace argocd

# Install ArgoCD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for ArgoCD to be ready
kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n argocd

# Get ArgoCD admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

# Port forward to access ArgoCD UI
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Access ArgoCD UI at: https://localhost:8080

- Username: `admin`
- Password: (from the command above)

### 3. Install Prometheus Operator

```bash
# Install Prometheus Operator using Helm
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring --create-namespace
```

### 4. Install Grafana Loki

```bash
# Install Loki using Helm
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
helm install loki grafana/loki-stack -n logging --create-namespace
```

### 5. Configure ArgoCD Application

1. Update `argocd/application.yaml` with your Git repository URL:

   ```yaml
   source:
     repoURL: https://github.com/your-username/infra_stucture_poc.git
     targetRevision: main
   ```

2. Apply the ArgoCD application:

   ```bash
   kubectl apply -f argocd/application.yaml
   ```

3. Or create it via ArgoCD CLI:
   ```bash
   argocd app create fastapi-demo \
     --repo https://github.com/your-username/infra_stucture_poc.git \
     --path k8s \
     --dest-server https://kubernetes.default.svc \
     --dest-namespace fastapi-demo \
     --sync-policy automated \
     --self-heal
   ```

### 6. Verify Deployment

```bash
# Check ArgoCD application status
kubectl get application -n argocd

# Check pods
kubectl get pods -n fastapi-demo

# Check services
kubectl get svc -n fastapi-demo

# Port forward to test the application
kubectl port-forward svc/fastapi-demo -n fastapi-demo 8000:80

# Test endpoints
curl http://localhost:8000/
curl http://localhost:8000/health
curl http://localhost:8000/metrics
```

## Monitoring

### Prometheus Metrics

The FastAPI application exposes Prometheus metrics at `/metrics` endpoint. Prometheus will automatically scrape these metrics using the ServiceMonitor.

Access Prometheus:

```bash
kubectl port-forward svc/prometheus-kube-prometheus-prometheus -n monitoring 9090:9090
```

Visit: http://localhost:9090

### Grafana Dashboards

Access Grafana:

```bash
kubectl port-forward svc/prometheus-grafana -n monitoring 3000:80
```

Default credentials:

- Username: `admin`
- Password: `prom-operator` (or check the secret)

Add Prometheus as a data source:

- URL: `http://prometheus-kube-prometheus-prometheus.monitoring.svc.cluster.local:9090`

### Logging with Loki

Access Loki:

```bash
kubectl port-forward svc/loki -n logging 3100:3100
```

Add Loki as a Grafana data source:

- URL: `http://loki.logging.svc.cluster.local:3100`

Query logs in Grafana using LogQL:

```
{app="fastapi-demo"}
```

## GitOps Workflow

1. **Make Changes**: Update code or Kubernetes manifests
2. **Commit & Push**: Push changes to Git repository
3. **ArgoCD Sync**: ArgoCD automatically detects changes and syncs to cluster
4. **Monitor**: Check ArgoCD UI and Prometheus/Grafana for status

## Application Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check (liveness probe)
- `GET /ready` - Readiness check
- `GET /api/items` - Sample API endpoint
- `GET /api/status` - Application status
- `GET /metrics` - Prometheus metrics

## Customization

### Update Application

1. Modify `app/main.py`
2. Build new Docker image
3. Update image tag in `k8s/deployment.yaml`
4. Commit and push to Git
5. ArgoCD will automatically deploy the changes

### Scale Application

Update `replicas` in `k8s/deployment.yaml` and push to Git.

### Environment Variables

Update `k8s/configmap.yaml` and push to Git.

## Troubleshooting

### Check ArgoCD Sync Status

```bash
kubectl get application fastapi-demo -n argocd -o yaml
```

### View Application Logs

```bash
kubectl logs -n fastapi-demo -l app=fastapi-demo
```

### Check Prometheus Targets

Access Prometheus UI → Status → Targets

### Check ServiceMonitor

```bash
kubectl get servicemonitor -n fastapi-demo
```

## Next Steps

- Add CI/CD pipeline (GitHub Actions, GitLab CI, etc.)
- Set up alerting rules in Prometheus
- Create custom Grafana dashboards
- Add more FastAPI endpoints
- Implement authentication/authorization
- Add database integration
- Set up SSL/TLS certificates

## Resources

- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Loki Documentation](https://grafana.com/docs/loki/latest/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
