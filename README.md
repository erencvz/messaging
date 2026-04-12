# messaging-api

FastAPI tabanlı in-memory mesajlaşma API'si. CI/CD: GitHub Actions → Jenkins → Kubernetes (Kustomize). API gateway entegrasyonu Apinizer üzerinden sağlanır.

---

## Proje Yapısı

```
messaging-api/
├── app/
│   └── main.py                   # FastAPI uygulaması
├── tests/
│   └── test_api.py               # pytest testleri
├── k8s/
│   ├── base/
│   │   ├── deployment.yaml
│   │   ├── service.yaml          # NodePort tipi servis
│   │   └── kustomization.yaml
│   └── overlays/
│       ├── dev/kustomization.yaml
│       ├── test/kustomization.yaml
│       └── uat/kustomization.yaml
├── .github/
│   └── workflows/
│       └── ci.yaml               # GitHub Actions: test → build → Jenkins trigger
├── Dockerfile
├── Jenkinsfile                   # Declarative pipeline: dev → test → uat
├── requirements.txt
└── README.md
```

---

## Placeholder'lar — Nerede Değiştirilecek

| Placeholder    | Açıklama                        | Dosya(lar)                                                                                     |
|----------------|---------------------------------|------------------------------------------------------------------------------------------------|
| `YOUR_ORG`     | GitHub organizasyon adı         | `Dockerfile`, `k8s/overlays/*/kustomization.yaml`, `.github/workflows/ci.yaml`, `Jenkinsfile` |
| `YOUR_REPO`    | GitHub repo adı (Jenkins job)   | `.github/workflows/ci.yaml` → `curl` satırındaki job URL'i                                    |
| `YOUR_PROJECT` | Apinizer proje adı              | `Jenkinsfile` → `environment { APINIZER_PROJECT = 'YOUR_PROJECT' }` satırı                    |

> **Not:** Apinizer URL'indeki `{env}` segmenti (`dev`, `test`, `uat`) Apinizer ortam adlarınızla eşleşmiyorsa `Jenkinsfile`'daki `apinizerTrigger()` çağrılarını güncelleyin.

---

## Kurulum Adımları

### 1. Kubernetes — Namespace'leri Oluştur

```bash
kubectl create namespace messaging-dev
kubectl create namespace messaging-test
kubectl create namespace messaging-uat
```

### 2. GitHub Secrets

Repo → **Settings → Secrets and variables → Actions → New repository secret**

| Secret Adı       | Değer                                              |
|------------------|----------------------------------------------------|
| `GITHUB_TOKEN`   | Otomatik sağlanır (ek işlem gerekmez)              |
| `JENKINS_URL`    | `https://jenkins.example.com`                      |
| `JENKINS_USER`   | Jenkins kullanıcı adı                              |
| `JENKINS_TOKEN`  | Jenkins API token (User → Configure → API Token)  |

### 3. Jenkins Credentials

Jenkins → **Manage Jenkins → Credentials → System → Global → Add Credentials**

| ID                       | Tür           | Açıklama                             |
|--------------------------|---------------|--------------------------------------|
| `kubeconfig`             | Secret File   | Cluster erişimi için kubeconfig      |
| `apinizer-base-url`      | Secret Text   | `https://apinizer.example.com`       |
| `apinizer-token`         | Secret Text   | Apinizer Bearer token                |
| `apinizer-dev-api-id`    | Secret Text   | Dev ortamındaki API proxy adı/ID     |
| `apinizer-test-api-id`   | Secret Text   | Test ortamındaki API proxy adı/ID    |
| `apinizer-uat-api-id`    | Secret Text   | UAT ortamındaki API proxy adı/ID     |

### 4. Jenkins Pipeline Job Oluştur

1. Jenkins → **New Item → Pipeline**
2. Job adı: `YOUR_REPO` (ci.yaml'daki URL ile eşleşmeli)
3. **Pipeline → Definition:** Pipeline script from SCM
4. SCM: Git, repo URL'ini gir
5. Script Path: `Jenkinsfile`
6. **"This project is parameterized"** → String Parameter: `SHA_TAG`, default: `latest`
7. **"Trigger builds remotely"** → token'ı Jenkins API token ile aynı yapabilirsin

### 5. Apinizer — Proxy Backend URL'leri

Her ortamda Apinizer proxy'sinin backend URL'i, servisin NodePort'una işaret etmelidir:

```
http://<K8S_NODE_IP>:<NodePort>
```

NodePort numarasını öğrenmek için:

```bash
kubectl get svc messaging-api -n messaging-dev -o jsonpath='{.spec.ports[0].nodePort}'
```

Her ortam için Apinizer'da ayrı bir proxy tanımlamanız gerekir (dev/test/uat backend URL'leri farklı namespace'lere işaret eder ama aynı node IP'sini kullanır; NodePort numaraları farklı olacaktır çünkü her namespace'de bağımsız bir servis vardır).

### 6. Sıfırdan Kurulum Özeti

```bash
# 1. Repo oluştur ve kodu push et
git init && git remote add origin https://github.com/YOUR_ORG/YOUR_REPO.git
git add . && git commit -m "initial commit"

# 2. Placeholder'ları değiştir (YOUR_ORG, YOUR_REPO, YOUR_PROJECT)
# 3. Namespace'leri oluştur (yukarıdaki kubectl komutları)
# 4. GitHub Secrets ekle
# 5. Jenkins credentials ekle
# 6. Jenkins pipeline job oluştur
# 7. Apinizer'da 3 ortam için proxy tanımla, backend URL'lerini NodePort'lara yönlendir

# İlk deploy tetiklemek için:
git push origin main
```

---

## Deployment Akışı

```
git push → main
    │
    ▼
GitHub Actions: test job
    │ (pytest pass)
    ▼
GitHub Actions: build job
    ├─ Docker image build (sha-<short_sha> + latest tag)
    ├─ ghcr.io push
    └─ Jenkins curl trigger (SHA_TAG=sha-<short_sha>)
            │
            ▼
        Jenkins Pipeline
            │
            ├─ [auto] Deploy Dev
            │       └─ kustomize image update → kubectl apply → Apinizer sync
            ├─ [auto] Smoke Test Dev (/health 200 OK kontrolü)
            │
            ├─ [MANUAL] Approve Test ← Jenkins UI onayı
            │
            ├─ [auto] Deploy Test + Apinizer sync
            ├─ [auto] Smoke Test Test
            │
            ├─ [MANUAL] Approve UAT ← Jenkins UI onayı
            │
            ├─ [auto] Deploy UAT + Apinizer sync
            └─ [auto] Smoke Test UAT
```

---

## Lokal Geliştirme

```bash
pip install -r requirements.txt

# Uygulamayı çalıştır
uvicorn app.main:app --reload

# Testleri çalıştır
pytest tests/ -v

# Swagger UI
open http://localhost:8000/docs
```

---

## API Endpoint'leri

| Method | Path        | Açıklama                        |
|--------|-------------|---------------------------------|
| POST   | /messages   | Yeni mesaj ekle                 |
| GET    | /messages   | Tüm mesajları listele           |
| GET    | /info       | version, environment, build_sha |
| GET    | /health     | `{"status": "ok"}`             |
| GET    | /docs       | Swagger UI                      |
| GET    | /openapi.json | OpenAPI spec                  |
