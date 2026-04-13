pipeline {
    agent any

    parameters {
        string(
            name: 'SHA_TAG',
            defaultValue: 'latest',
            description: 'Docker image tag pushed by CI (e.g. sha-abc1234)'
        )
    }

    environment {
        IMAGE_BASE      = 'apinizeren/messaging'
        NODE_IP         = '167.86.118.166'
        DEV_NODE_PORT   = '30211'
        TEST_NODE_PORT  = '30212'
        UAT_NODE_PORT   = '30213'

        APINIZER_URL    = credentials('apinizer-management-url')
        APINIZER_TOKEN  = credentials('APINIZER_DEMO_TOKEN')
        PROXY_NAME      = 'messaging-api'

        PROJECT_NAME_DEV  = 'dev-project'
        PROJECT_NAME_TEST = 'test-project'
        PROJECT_NAME_UAT  = 'uat-project'

        OPENAPI_URL_DEV  = "http://${NODE_IP}:${DEV_NODE_PORT}/openapi.json"
        OPENAPI_URL_TEST = "http://${NODE_IP}:${TEST_NODE_PORT}/openapi.json"
        OPENAPI_URL_UAT  = "http://${NODE_IP}:${UAT_NODE_PORT}/openapi.json"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        // ── DEV ──────────────────────────────────────────────────────────────

        stage('Deploy Dev') {
            steps {
                withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                    sh """
                        export KUBECONFIG=\$KUBECONFIG
                        cd k8s/overlays/dev
                        kustomize edit set image ${IMAGE_BASE}=${IMAGE_BASE}:${params.SHA_TAG}
                        kubectl apply -k .
                        kubectl rollout status deployment/messaging-api -n messaging-dev --timeout=120s
                    """
                }
            }
            post { failure { echo '❌ Deploy Dev başarısız.' } }
        }

        stage('Apinizer Sync Dev') {
            steps {
                script {
                    apinizerProxySync(
                        proxyName:   env.PROXY_NAME,
                        projectName: env.PROJECT_NAME_DEV,
                        openApiUrl:  env.OPENAPI_URL_DEV,
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
                input message: 'Test ortamına deploy edilsin mi?', ok: 'Proceed'
            }
        }

        // ── TEST ─────────────────────────────────────────────────────────────

        stage('Deploy Test') {
            steps {
                withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                    sh """
                        export KUBECONFIG=\$KUBECONFIG
                        cd k8s/overlays/test
                        kustomize edit set image ${IMAGE_BASE}=${IMAGE_BASE}:${params.SHA_TAG}
                        kubectl apply -k .
                        kubectl rollout status deployment/messaging-api -n messaging-test --timeout=120s
                    """
                }
            }
            post { failure { echo '❌ Deploy Test başarısız.' } }
        }

        stage('Apinizer Sync Test') {
            steps {
                script {
                    apinizerProxySync(
                        proxyName:   env.PROXY_NAME,
                        projectName: env.PROJECT_NAME_TEST,
                        openApiUrl:  env.OPENAPI_URL_TEST,
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
                input message: 'UAT ortamına deploy edilsin mi?', ok: 'Proceed'
            }
        }

        // ── UAT ──────────────────────────────────────────────────────────────

        stage('Deploy UAT') {
            steps {
                withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                    sh """
                        export KUBECONFIG=\$KUBECONFIG
                        cd k8s/overlays/uat
                        kustomize edit set image ${IMAGE_BASE}=${IMAGE_BASE}:${params.SHA_TAG}
                        kubectl apply -k .
                        kubectl rollout status deployment/messaging-api -n messaging-uat --timeout=120s
                    """
                }
            }
            post { failure { echo '❌ Deploy UAT başarısız.' } }
        }

        stage('Apinizer Sync UAT') {
            steps {
                script {
                    apinizerProxySync(
                        proxyName:   env.PROXY_NAME,
                        projectName: env.PROJECT_NAME_UAT,
                        openApiUrl:  env.OPENAPI_URL_UAT,
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

        // ── PROD ─────────────────────────────────────────────────────────────

        stage('Approve Prod') {
            steps {
                input message: 'PRODUCTION ortamına promote edilsin mi?', ok: 'Proceed'
            }
        }

        stage('Promote to Prod') {
            steps {
                script {
                    echo '🚀 PROD ortamına promote ediliyor...'

                    def payload = '''{
  "mappingNames": ["messagingapi"],
  "executionName": "Db2Map v2.1 - Production Deploy",
  "executionDescription": "API Proxy promotion from UAT to Production environment"
}'''
                    writeFile file: '/tmp/apinizer_promote_payload.json', text: payload

                    def promoteStatus = sh(
                        script: """
                            curl -s -o /tmp/apinizer_promote.json -w '%{http_code}' \\
                                -X POST \\
                                -H 'Authorization: Bearer ${env.APINIZER_TOKEN}' \\
                                -H 'Content-Type: application/json' \\
                                -d @/tmp/apinizer_promote_payload.json \\
                                '${env.APINIZER_URL}/apiops/promotion/executions'
                        """,
                        returnStdout: true
                    ).trim()

                    echo "Apinizer promote HTTP: ${promoteStatus}"
                    if (!promoteStatus.startsWith('2')) {
                        error("❌ Prod promote başarısız (HTTP ${promoteStatus}): ${readFile('/tmp/apinizer_promote.json')}")
                    }
                    echo '✅ PROD ortamına başarıyla promote edildi.'
                }
            }
            post { failure { echo '❌ Promote to Prod başarısız.' } }
        }
    }

    post {
        success { echo '✅ Pipeline başarıyla tamamlandı.' }
        failure { echo '💥 Pipeline başarısız oldu.' }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Apinizer: Proxy oluştur/güncelle → ortama deploy et
// ─────────────────────────────────────────────────────────────────────────────
def apinizerProxySync(Map args) {
    def proxyName   = args.proxyName
    def projectName = args.projectName
    def openApiUrl  = args.openApiUrl
    def environment = args.environment
    def baseUrl     = env.APINIZER_URL
    def token       = env.APINIZER_TOKEN
    def backendUrl  = openApiUrl.replace('/openapi.json', '')

    // 1 — Proxy var mı? (HTTP 200 → var; response body'yi de saklıyoruz)
    echo "Checking if API proxy exists: ${projectName}/${proxyName}"
    def proxyCheckCode = sh(
        script: """
            curl -s -o /tmp/apinizer_get.json -w '%{http_code}' \\
                -H 'Authorization: Bearer ${token}' \\
                '${baseUrl}/apiops/projects/${projectName}/apiProxies/${proxyName}/'
        """,
        returnStdout: true
    ).trim()
    echo "Proxy check returned: ${proxyCheckCode}"

    def proxyExists = (proxyCheckCode == '200')

    // 2a — Proxy varsa → rollback snapshot al, mevcut relativePathList'i al, spec güncelle
    if (proxyExists) {
        echo 'API proxy exists — taking rollback snapshot and updating spec...'

        sh """
            curl -s -o apinizer_backup_${environment}_${proxyName}.zip \\
                -H 'Authorization: Bearer ${token}' \\
                '${baseUrl}/apiops/projects/${projectName}/apiProxies/${proxyName}/export/'
            echo '✅ Rollback snapshot alındı.'
        """
        archiveArtifacts artifacts: "apinizer_backup_${environment}_${proxyName}.zip",
                         allowEmptyArchive: true

        // Mevcut relativePathList'i parse et
        def proxyJson       = readJSON file: '/tmp/apinizer_get.json'
        def relativePathList = proxyJson.resultList[0].clientRoute.relativePathList
        def relativePathJson = groovy.json.JsonOutput.toJson(relativePathList)
        echo "Mevcut relativePathList: ${relativePathJson}"

        def updateStatus = sh(
            script: """
                curl -s -o /tmp/apinizer_update.json -w '%{http_code}' \\
                    -X PUT \\
                    -H 'Authorization: Bearer ${token}' \\
                    -H 'Content-Type: application/json' \\
                    -d '{
                        "apiProxyName": "${proxyName}",
                        "apiProxyCreationType": "OPEN_API",
                        "specUrl": "${openApiUrl}",
                        "clientRoute": {
                            "relativePathList": ${relativePathJson},
                            "hostList": []
                        },
                        "reParse": true,
                        "deploy": false
                    }' \\
                    '${baseUrl}/apiops/projects/${projectName}/apiProxies/url/'
            """,
            returnStdout: true
        ).trim()

        echo "Apinizer update HTTP: ${updateStatus}"
        if (!updateStatus.startsWith('2')) {
            error("❌ Proxy güncelleme başarısız (HTTP ${updateStatus}): ${readFile('/tmp/apinizer_update.json')}")
        }

    // 2b — Proxy yoksa → oluştur
    } else {
        echo 'API proxy not found — creating...'

        def createStatus = sh(
            script: """
                curl -s -o /tmp/apinizer_create.json -w '%{http_code}' \\
                    -X POST \\
                    -H 'Authorization: Bearer ${token}' \\
                    -H 'Content-Type: application/json' \\
                    -d '{
                        "apiProxyName": "${proxyName}",
                        "apiProxyDescription": "Auto-generated proxy",
                        "apiProxyCreationType": "OPEN_API",
                        "specUrl": "${openApiUrl}",
                        "clientRoute": {
                            "relativePathList": ["/${proxyName}"],
                            "hostList": []
                        },
                        "routingInfo": {
                            "routingAddressList": [
                                {
                                    "address": "${backendUrl}",
                                    "weight": 100,
                                    "healthCheckEnabled": false
                                }
                            ],
                            "routingEnabled": true,
                            "mirrorEnabled": false
                        },
                        "reParse": false,
                        "deploy": false
                    }' \\
                    '${baseUrl}/apiops/projects/${projectName}/apiProxies/url/'
            """,
            returnStdout: true
        ).trim()

        echo "Apinizer create HTTP: ${createStatus}"
        if (!createStatus.startsWith('2')) {
            error("❌ Proxy oluşturma başarısız (HTTP ${createStatus}): ${readFile('/tmp/apinizer_create.json')}")
        }
    }

    // 3 — Ortama deploy et
    echo "🚀 Deploy ediliyor → ${projectName}/${proxyName} @ ${environment}"
    def deployStatus = sh(
        script: """
            curl -s -o /tmp/apinizer_deploy.json -w '%{http_code}' \\
                -X POST \\
                -H 'Authorization: Bearer ${token}' \\
                '${baseUrl}/apiops/projects/${projectName}/apiProxies/${proxyName}/environments/${environment}/'
        """,
        returnStdout: true
    ).trim()

    echo "Apinizer deploy HTTP: ${deployStatus}"
    if (!deployStatus.startsWith('2')) {
        error("❌ Apinizer deploy başarısız (HTTP ${deployStatus}): ${readFile('/tmp/apinizer_deploy.json')}")
    }
    echo "✅ Proxy '${proxyName}' → ${environment} ortamına başarıyla deploy edildi."
}

// ─────────────────────────────────────────────────────────────────────────────
// Kubernetes rollout status + /health smoke check
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
