# FastAPI GitOps POC with ArgoCD

This is a proof of concept demonstrating GitOps practices using:

- **FastAPI** - Python web framework
- **ArgoCD** - GitOps continuous delivery tool
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
┌─────────────┐
│ Kubernetes  │
│  Cluster    │
└──────┬──────┘
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
│   └── kustomization.yaml   # Kustomize configuration
├── argocd/
│   └── application.yaml     # ArgoCD application definition
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

### 3. Install Grafana Loki

```bash
# Install Loki using Helm
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
helm install loki grafana/loki-stack -n logging --create-namespace
```

### 4. Configure ArgoCD Application

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

### 5. Verify Deployment

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
```

## Logging with Loki

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
4. **Monitor**: Check ArgoCD UI and Loki for logs

## Application Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check (liveness probe)
- `GET /ready` - Readiness check
- `GET /api/items` - Sample API endpoint
- `GET /api/status` - Application status

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

## Next Steps

- Add CI/CD pipeline (GitHub Actions, GitLab CI, etc.)
- Create custom Grafana dashboards
- Add more FastAPI endpoints
- Implement authentication/authorization
- Add database integration
- Set up SSL/TLS certificates

## Resources

- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [Grafana Loki Documentation](https://grafana.com/docs/loki/latest/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
