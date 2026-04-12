pipeline {
    agent any

    parameters {
        string(name: 'SHA_TAG',           defaultValue: 'latest',       description: 'Docker image tag pushed by CI (e.g. sha-abc1234)')
        string(name: 'OPENAPI_URL',       defaultValue: '',             description: 'Proxy olarak eklenecek OpenAPI/Swagger URL')
        string(name: 'PROXY_NAME',        defaultValue: 'messaging-api',description: 'Apinizer proxy adı')
        string(name: 'PROJECT_NAME_DEV',  defaultValue: 'dev-project',  description: 'Apinizer DEV proje adı')
        string(name: 'PROJECT_NAME_TEST', defaultValue: 'test-project', description: 'Apinizer TEST proje adı')
        string(name: 'PROJECT_NAME_UAT',  defaultValue: 'uat-project',  description: 'Apinizer UAT proje adı')
    }

    environment {
        IMAGE_BASE     = 'apinizeren/messaging'
        NODE_IP        = '167.86.118.166'
        DEV_NODE_PORT  = '30211'
        TEST_NODE_PORT = '30212'
        UAT_NODE_PORT  = '30213'

        APINIZER_URL   = credentials('apinizer-management-url')
        APINIZER_TOKEN = credentials('APINIZER_DEMO_TOKEN')
    }

    stages {

        stage('Checkout') {
            steps { checkout scm }
        }

        // ─── DEV ─────────────────────────────────────────────────────────────
        stage('Deploy Dev') {
            steps {
                withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                    sh """
                        export KUBECONFIG=\$KUBECONFIG
                        cd k8s/overlays/dev
                        kustomize edit set image ${IMAGE_BASE}=${IMAGE_BASE}:${params.SHA_TAG}
                        kubectl apply -k .
                    """
                }
            }
            post { failure { echo '❌ Deploy Dev başarısız.' } }
        }

        stage('Apinizer Sync Dev') {
            steps {
                script {
                    apinizerProxySync(
                        proxyName:   params.PROXY_NAME,
                        projectName: params.PROJECT_NAME_DEV,
                        openApiUrl:  params.OPENAPI_URL,
                        environment: 'dev'
                    )
                }
            }
            post { failure { echo '❌ Apinizer Sync Dev başarısız.' } }
        }

        stage('Smoke Test Dev') {
            steps {
                withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                    smokeTest('messaging-dev', env.DEV_NODE_PORT)
                }
            }
            post { failure { echo '❌ Smoke Test Dev başarısız — pipeline durduruluyor.' } }
        }

        stage('Approve Test') {
            steps {
                input message: 'Test ortamına deploy edilsin mi?', ok: 'Devam Et'
            }
        }

        // ─── TEST ─────────────────────────────────────────────────────────────
        stage('Deploy Test') {
            steps {
                withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                    sh """
                        export KUBECONFIG=\$KUBECONFIG
                        cd k8s/overlays/test
                        kustomize edit set image ${IMAGE_BASE}=${IMAGE_BASE}:${params.SHA_TAG}
                        kubectl apply -k .
                    """
                }
            }
            post { failure { echo '❌ Deploy Test başarısız.' } }
        }

        stage('Apinizer Sync Test') {
            steps {
                script {
                    apinizerProxySync(
                        proxyName:   params.PROXY_NAME,
                        projectName: params.PROJECT_NAME_TEST,
                        openApiUrl:  params.OPENAPI_URL,
                        environment: 'test'
                    )
                }
            }
            post { failure { echo '❌ Apinizer Sync Test başarısız.' } }
        }

        stage('Smoke Test Test') {
            steps {
                withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                    smokeTest('messaging-test', env.TEST_NODE_PORT)
                }
            }
            post { failure { echo '❌ Smoke Test (test) başarısız — pipeline durduruluyor.' } }
        }

        stage('Approve UAT') {
            steps {
                input message: 'UAT ortamına deploy edilsin mi?', ok: 'Devam Et'
            }
        }

        // ─── UAT ─────────────────────────────────────────────────────────────
        stage('Deploy UAT') {
            steps {
                withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                    sh """
                        export KUBECONFIG=\$KUBECONFIG
                        cd k8s/overlays/uat
                        kustomize edit set image ${IMAGE_BASE}=${IMAGE_BASE}:${params.SHA_TAG}
                        kubectl apply -k .
                    """
                }
            }
            post { failure { echo '❌ Deploy UAT başarısız.' } }
        }

        stage('Apinizer Sync UAT') {
            steps {
                script {
                    apinizerProxySync(
                        proxyName:   params.PROXY_NAME,
                        projectName: params.PROJECT_NAME_UAT,
                        openApiUrl:  params.OPENAPI_URL,
                        environment: 'uat'
                    )
                }
            }
            post { failure { echo '❌ Apinizer Sync UAT başarısız.' } }
        }

        stage('Smoke Test UAT') {
            steps {
                withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                    smokeTest('messaging-uat', env.UAT_NODE_PORT)
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
// Apinizer: Proxy oluştur/güncelle ve ortama deploy et
// ─────────────────────────────────────────────────────────────────────────────
def apinizerProxySync(Map args) {
    def proxyName   = args.proxyName
    def projectName = args.projectName
    def openApiUrl  = args.openApiUrl
    def environment = args.environment

    def baseUrl = env.APINIZER_URL
    def token   = env.APINIZER_TOKEN

    // 1) Proxy var mı kontrol et
    sh(
        script: """
            curl -s -o /tmp/apinizer_list.json -w "%{http_code}" \
                -H "Authorization: Bearer ${token}" \
                "${baseUrl}/apiops/projects/${projectName}/apiProxies/"
        """,
        returnStdout: true
    ).trim()

    def listBody   = readFile('/tmp/apinizer_list.json')
    def proxyExists = listBody.contains("\"${proxyName}\"")

    // 2a) Rollback snapshot (proxy varsa)
    if (proxyExists) {
        sh """
            curl -s -o /tmp/apinizer_backup_${environment}_${proxyName}.zip \
                -H "Authorization: Bearer ${token}" \
                "${baseUrl}/apiops/projects/${projectName}/apiProxies/${proxyName}/export/"
            echo "✅ Rollback snapshot alındı."
        """
        archiveArtifacts artifacts: "tmp/apinizer_backup_${environment}_${proxyName}.zip",
                         allowEmptyArchive: true
    }

   // 2b) Proxy oluştur veya güncelle
if (!proxyExists) {
    echo "ℹ️  Proxy bulunamadı → oluşturuluyor (${projectName}/${proxyName})"

    // Body'yi dosyaya yaz — shell interpolation sorununu önler
    writeFile file: '/tmp/apinizer_payload.json', text: """{
  "apiProxyName": "${proxyName}",
  "apiProxyCreationType": "OPEN_API",
  "specUrl": "${openApiUrl}",
  "deploy": false
}"""

    def createStatus = sh(
        script: """
            curl -s -o /tmp/apinizer_create.json -w "%{http_code}" \\
                -X POST \\
                -H "Authorization: Bearer ${token}" \\
                -H "Content-Type: application/json" \\
                -d @/tmp/apinizer_payload.json \\
                "${baseUrl}/apiops/projects/${projectName}/apiProxies/url/"
        """,
        returnStdout: true
    ).trim()

    echo "Apinizer create HTTP: ${createStatus}"
    if (!createStatus.startsWith('2')) {
        error("❌ Proxy oluşturma başarısız (HTTP ${createStatus}): ${readFile('/tmp/apinizer_create.json')}")
    }
} else {
    echo "ℹ️  Proxy mevcut → güncelleniyor (${projectName}/${proxyName})"

    writeFile file: '/tmp/apinizer_payload.json', text: """{
  "apiProxyName": "${proxyName}",
  "apiProxyCreationType": "OPEN_API",
  "specUrl": "${openApiUrl}",
  "reParse": true
}"""

    def updateStatus = sh(
        script: """
            curl -s -o /tmp/apinizer_update.json -w "%{http_code}" \\
                -X PUT \\
                -H "Authorization: Bearer ${token}" \\
                -H "Content-Type: application/json" \\
                -d @/tmp/apinizer_payload.json \\
                "${baseUrl}/apiops/projects/${projectName}/apiProxies/${proxyName}/"
        """,
        returnStdout: true
    ).trim()

    echo "Apinizer update HTTP: ${updateStatus}"
    if (!updateStatus.startsWith('2')) {
        error("❌ Proxy güncelleme başarısız (HTTP ${updateStatus}): ${readFile('/tmp/apinizer_update.json')}")
    }
}

    // 3) Ortama deploy et
    echo "🚀 Deploy ediliyor → ${projectName}/${proxyName} @ ${environment}"
    def deployStatus = sh(
        script: """
            curl -s -o /tmp/apinizer_deploy.json -w "%{http_code}" \
                -X POST \
                -H "Authorization: Bearer ${token}" \
                "${baseUrl}/apiops/projects/${projectName}/apiProxies/${proxyName}/environments/${environment}/"
        """,
        returnStdout: true
    ).trim()
    echo "Apinizer deploy HTTP: ${deployStatus}"
    if (!deployStatus.startsWith('2')) {
        error("❌ Apinizer deploy başarısız (HTTP ${deployStatus}): ${readFile('/tmp/apinizer_deploy.json')}")
    }

    echo "✅ Apinizer proxy ${environment} ortamına başarıyla deploy edildi."
}

// ─────────────────────────────────────────────────────────────────────────────
// Kubernetes rollout + /health kontrol
// ─────────────────────────────────────────────────────────────────────────────
def smokeTest(String namespace, String nodePort) {
    withEnv(["SMOKE_NAMESPACE=${namespace}", "SMOKE_PORT=${nodePort}"]) {
        sh '''
            export KUBECONFIG=$KUBECONFIG

            echo "Smoke test: http://$NODE_IP:${SMOKE_PORT}/health"

            kubectl rollout status deployment/messaging-api \
                -n ${SMOKE_NAMESPACE} \
                --timeout=120s

            echo "5 saniye bekleniyor..."
            sleep 5

            for i in 1 2 3; do
                HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
                    --connect-timeout 10 \
                    "http://$NODE_IP:${SMOKE_PORT}/health")

                echo "Deneme $i: $HTTP_STATUS"

                if [ "$HTTP_STATUS" = "200" ]; then
                    echo "✅ /health 200 OK — ${SMOKE_NAMESPACE}"
                    exit 0
                fi

                sleep 5
            done

            echo "❌ /health başarısız: $HTTP_STATUS (beklenen: 200)"
            exit 1
        '''
    }
}
