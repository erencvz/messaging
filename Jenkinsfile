// ─────────────────────────────────────────────────────────────────────────────
// Jenkinsfile — messaging-api CD Pipeline
// GitHub Actions bu pipeline'ı SHA_TAG parametresiyle tetikler.
//
// PLACEHOLDER'LAR:
//   IMAGE_BASE          → Docker Hub kullanıcı adın (YOUR_DOCKERHUB_USERNAME)
//   apinizer-*-project  → Her ortam için Jenkins credential'ı (aşağıya bak)
// ─────────────────────────────────────────────────────────────────────────────

pipeline {
    agent any

    parameters {
        string(name: 'SHA_TAG', defaultValue: 'latest', description: 'Docker image tag pushed by CI (e.g. sha-abc1234)')
    }

    environment {
        IMAGE_BASE = 'apinizeren/messaging'
    }

    stages {

        // ── Checkout ────────────────────────────────────────────────────────
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        // ══════════════════════════════════════════════════════════════════════
        // DEV
        // ══════════════════════════════════════════════════════════════════════

        stage('Deploy Dev') {
            steps {
                withCredentials([
                    file(credentialsId: 'kubeconfig',                variable: 'KUBECONFIG'),
                    string(credentialsId: 'apinizer-base-url',       variable: 'APINIZER_BASE_URL'),
                    string(credentialsId: 'apinizer-token',          variable: 'APINIZER_TOKEN'),
                    string(credentialsId: 'apinizer-dev-project',    variable: 'APINIZER_PROJECT'),
                    string(credentialsId: 'apinizer-dev-api-id',     variable: 'APINIZER_API_ID'),
                ]) {
                    sh """
                        cd k8s/overlays/dev
                        kustomize edit set image ${IMAGE_BASE}=${IMAGE_BASE}:${params.SHA_TAG}
                        kubectl --kubeconfig=\$KUBECONFIG apply -k .
                    """
                    apinizerTrigger('dev')
                }
            }
            post { failure { echo '❌ Deploy Dev başarısız.' } }
        }

        stage('Smoke Test Dev') {
            steps {
                withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                    smokeTest('messaging-dev')
                }
            }
            post { failure { echo '❌ Smoke Test Dev başarısız — pipeline durduruluyor.' } }
        }

        // ── Manual gate ─────────────────────────────────────────────────────
        stage('Approve Test') {
            steps {
                input message: 'Test ortamına deploy edilsin mi?', ok: 'Devam Et'
            }
        }

        // ══════════════════════════════════════════════════════════════════════
        // TEST
        // ══════════════════════════════════════════════════════════════════════

        stage('Deploy Test') {
            steps {
                withCredentials([
                    file(credentialsId: 'kubeconfig',                variable: 'KUBECONFIG'),
                    string(credentialsId: 'apinizer-base-url',       variable: 'APINIZER_BASE_URL'),
                    string(credentialsId: 'apinizer-token',          variable: 'APINIZER_TOKEN'),
                    string(credentialsId: 'apinizer-test-project',   variable: 'APINIZER_PROJECT'),
                    string(credentialsId: 'apinizer-test-api-id',    variable: 'APINIZER_API_ID'),
                ]) {
                    sh """
                        cd k8s/overlays/test
                        kustomize edit set image ${IMAGE_BASE}=${IMAGE_BASE}:${params.SHA_TAG}
                        kubectl --kubeconfig=\$KUBECONFIG apply -k .
                    """
                    apinizerTrigger('test')
                }
            }
            post { failure { echo '❌ Deploy Test başarısız.' } }
        }

        stage('Smoke Test Test') {
            steps {
                withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                    smokeTest('messaging-test')
                }
            }
            post { failure { echo '❌ Smoke Test (test) başarısız — pipeline durduruluyor.' } }
        }

        // ── Manual gate ─────────────────────────────────────────────────────
        stage('Approve UAT') {
            steps {
                input message: 'UAT ortamına deploy edilsin mi?', ok: 'Devam Et'
            }
        }

        // ══════════════════════════════════════════════════════════════════════
        // UAT
        // ══════════════════════════════════════════════════════════════════════

        stage('Deploy UAT') {
            steps {
                withCredentials([
                    file(credentialsId: 'kubeconfig',                variable: 'KUBECONFIG'),
                    string(credentialsId: 'apinizer-base-url',       variable: 'APINIZER_BASE_URL'),
                    string(credentialsId: 'apinizer-token',          variable: 'APINIZER_TOKEN'),
                    string(credentialsId: 'apinizer-uat-project',    variable: 'APINIZER_PROJECT'),
                    string(credentialsId: 'apinizer-uat-api-id',     variable: 'APINIZER_API_ID'),
                ]) {
                    sh """
                        cd k8s/overlays/uat
                        kustomize edit set image ${IMAGE_BASE}=${IMAGE_BASE}:${params.SHA_TAG}
                        kubectl --kubeconfig=\$KUBECONFIG apply -k .
                    """
                    apinizerTrigger('uat')
                }
            }
            post { failure { echo '❌ Deploy UAT başarısız.' } }
        }

        stage('Smoke Test UAT') {
            steps {
                withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                    smokeTest('messaging-uat')
                }
            }
            post { failure { echo '❌ Smoke Test UAT başarısız.' } }
        }
    }

    post {
        success { echo '✅ Pipeline başarıyla tamamlandı.' }
        failure { echo '💥 Pipeline başarısız oldu.' }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// HELPER FUNCTIONS
// ─────────────────────────────────────────────────────────────────────────────

def smokeTest(String namespace) {
    sh """
        export KUBECONFIG=\$KUBECONFIG

        NODE_IP=\$(kubectl get nodes \
            -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')

        NODE_PORT=\$(kubectl get svc messaging-api \
            -n ${namespace} \
            -o jsonpath='{.spec.ports[0].nodePort}')

        echo "Smoke test: http://\${NODE_IP}:\${NODE_PORT}/health"

        kubectl rollout status deployment/messaging-api \
            -n ${namespace} \
            --timeout=120s

        HTTP_STATUS=\$(curl -s -o /dev/null -w "%{http_code}" \
            "http://\${NODE_IP}:\${NODE_PORT}/health")

        if [ "\$HTTP_STATUS" != "200" ]; then
            echo "❌ /health döndü: \$HTTP_STATUS (beklenen: 200)"
            exit 1
        fi
        echo "✅ /health 200 OK — ${namespace}"
    """
}

def apinizerTrigger(String env) {
    sh """
        curl -f -s -X POST \
            "\${APINIZER_BASE_URL}/apiops/projects/\${APINIZER_PROJECT}/apiProxies/\${APINIZER_API_ID}/environments/${env}/" \
            -H "Authorization: Bearer \${APINIZER_TOKEN}" \
            -H "Content-Type: application/json" \
        || echo "⚠️  Apinizer trigger başarısız (${env}) — pipeline devam ediyor."
    """
}