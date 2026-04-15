pipeline {
    agent any

    parameters {
        string(
            name: 'VERSION_TAG',
            defaultValue: 'latest',
            description: 'Semantic version tag pushed by CI (e.g. v1.2.3)'
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

        // Retry configuration
        RETRY_COUNT     = '3'
        RETRY_DELAY_SEC = '15'
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm: [
                    $class: 'GitSCM',
                    branches: scm.branches,
                    userRemoteConfigs: scm.userRemoteConfigs,
                    extensions: [[$class: 'CleanBeforeCheckout']]
                ]
            }
        }

        // ── DEV ──────────────────────────────────────────────────────────────

        stage('Deploy Dev') {
            steps {
                withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                    sh """
                        export KUBECONFIG=\$KUBECONFIG
                        cd k8s/overlays/dev
                        kustomize edit set image ${IMAGE_BASE}=${IMAGE_BASE}:${params.VERSION_TAG}
                        kubectl apply -k .
                        kubectl rollout status deployment/messaging-api -n messaging-dev --timeout=120s
                    """
                }
            }
            post { failure { echo '❌ Deploy Dev failed.' } }
        }

        stage('Apinizer Sync Dev') {
            steps {
                script {
                    retryWithDelay(env.RETRY_COUNT.toInteger(), env.RETRY_DELAY_SEC.toInteger(), 'Apinizer Sync Dev') {
                        apinizerProxySync(
                            proxyName:      env.PROXY_NAME,
                            projectName:    env.PROJECT_NAME_DEV,
                            openApiUrl:     env.OPENAPI_URL_DEV,
                            environment:    'dev',
                            versionTag:     params.VERSION_TAG
                        )
                    }
                }
            }
            post { failure { echo '❌ Apinizer Sync Dev failed.' } }
        }

        stage('Smoke Test Dev') {
            steps {
                withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                    script {
                        retryWithDelay(env.RETRY_COUNT.toInteger(), env.RETRY_DELAY_SEC.toInteger(), 'Smoke Test Dev') {
                            smokeTest('messaging-dev', env.DEV_NODE_PORT)
                        }
                    }
                }
            }
            post { failure { echo '❌ Smoke Test Dev failed — pipeline stopping.' } }
        }

        stage('Approve Test') {
            steps {
                input message: "Deploy to TEST environment?\n\n🏷️ Version: ${params.VERSION_TAG}", ok: 'Proceed'
            }
        }

        // ── TEST ─────────────────────────────────────────────────────────────

        stage('Deploy Test') {
            steps {
                withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                    sh """
                        export KUBECONFIG=\$KUBECONFIG
                        cd k8s/overlays/test
                        kustomize edit set image ${IMAGE_BASE}=${IMAGE_BASE}:${params.VERSION_TAG}
                        kubectl apply -k .
                        kubectl rollout status deployment/messaging-api -n messaging-test --timeout=120s
                    """
                }
            }
            post { failure { echo '❌ Deploy Test failed.' } }
        }

        stage('Apinizer Sync Test') {
            steps {
                script {
                    retryWithDelay(env.RETRY_COUNT.toInteger(), env.RETRY_DELAY_SEC.toInteger(), 'Apinizer Sync Test') {
                        apinizerProxySync(
                            proxyName:      env.PROXY_NAME,
                            projectName:    env.PROJECT_NAME_TEST,
                            openApiUrl:     env.OPENAPI_URL_TEST,
                            environment:    'test',
                            versionTag:     params.VERSION_TAG
                        )
                    }
                }
            }
            post { failure { echo '❌ Apinizer Sync Test failed.' } }
        }

        stage('Smoke Test Test') {
            steps {
                withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                    script {
                        retryWithDelay(env.RETRY_COUNT.toInteger(), env.RETRY_DELAY_SEC.toInteger(), 'Smoke Test (test)') {
                            smokeTest('messaging-test', env.TEST_NODE_PORT)
                        }
                    }
                }
            }
            post { failure { echo '❌ Smoke Test (test) failed — pipeline stopping.' } }
        }

        stage('Approve UAT') {
            steps {
                input message: "Deploy to UAT environment?\n\n🏷️ Version: ${params.VERSION_TAG}", ok: 'Proceed'
            }
        }

        // ── UAT ──────────────────────────────────────────────────────────────

        stage('Deploy UAT') {
            steps {
                withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                    sh """
                        export KUBECONFIG=\$KUBECONFIG
                        cd k8s/overlays/uat
                        kustomize edit set image ${IMAGE_BASE}=${IMAGE_BASE}:${params.VERSION_TAG}
                        kubectl apply -k .
                        kubectl rollout status deployment/messaging-api -n messaging-uat --timeout=120s
                    """
                }
            }
            post { failure { echo '❌ Deploy UAT failed.' } }
        }

        stage('Apinizer Sync UAT') {
            steps {
                script {
                    retryWithDelay(env.RETRY_COUNT.toInteger(), env.RETRY_DELAY_SEC.toInteger(), 'Apinizer Sync UAT') {
                        apinizerProxySync(
                            proxyName:      env.PROXY_NAME,
                            projectName:    env.PROJECT_NAME_UAT,
                            openApiUrl:     env.OPENAPI_URL_UAT,
                            environment:    'uat',
                            versionTag:     params.VERSION_TAG
                        )
                    }
                }
            }
            post { failure { echo '❌ Apinizer Sync UAT failed.' } }
        }

        stage('Smoke Test UAT') {
            steps {
                withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                    script {
                        retryWithDelay(env.RETRY_COUNT.toInteger(), env.RETRY_DELAY_SEC.toInteger(), 'Smoke Test UAT') {
                            smokeTest('messaging-uat', env.UAT_NODE_PORT)
                        }
                    }
                }
            }
            post { failure { echo '❌ Smoke Test UAT failed.' } }
        }

        // ── PROD ─────────────────────────────────────────────────────────────

        stage('Approve Prod') {
            steps {
                input message: "Promote to PRODUCTION environment?\n\n🏷️ Version: ${params.VERSION_TAG}\n\n⚠️ This action will affect live traffic.", ok: 'Proceed'
            }
        }

        stage('Promote to Prod') {
            steps {
                script {
                    echo '🚀 Promoting to PROD...'

                    def payload = """{
  "mappingNames": ["messagingapi"],
  "executionName": "Db2Map v2.1 - Production Deploy",
  "executionDescription": "API Proxy promotion from UAT to Production environment - ${params.VERSION_TAG}"
}"""
                    writeFile file: '/tmp/apinizer_promote_payload.json', text: payload

                    retryWithDelay(env.RETRY_COUNT.toInteger(), env.RETRY_DELAY_SEC.toInteger(), 'Promote to Prod') {
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
                            error("❌ Prod promote failed (HTTP ${promoteStatus}): ${readFile('/tmp/apinizer_promote.json')}")
                        }
                    }
                    echo '✅ Successfully promoted to PROD.'
                }
            }
            post { failure { echo '❌ Promote to Prod failed.' } }
        }
    }

    post {
        success { echo '✅ Pipeline completed successfully.' }
        failure { echo '💥 Pipeline failed.' }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Retry wrapper
// ─────────────────────────────────────────────────────────────────────────────
def retryWithDelay(int maxAttempts, int delaySeconds, String stageName, Closure body) {
    int attempt = 0
    while (true) {
        attempt++
        try {
            echo "🔄 [${stageName}] Attempt ${attempt} of ${maxAttempts}..."
            body()
            echo "✅ [${stageName}] Succeeded on attempt ${attempt}."
            return
        } catch (Exception e) {
            if (attempt >= maxAttempts) {
                echo "❌ [${stageName}] All ${maxAttempts} attempts failed. Last error: ${e.message}"
                throw e
            }
            echo "⚠️ [${stageName}] Attempt ${attempt} failed: ${e.message}"
            echo "⏳ [${stageName}] Retrying in ${delaySeconds}s... (${attempt}/${maxAttempts})"
            sleep(delaySeconds)
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Apinizer: Create/update proxy → deploy to environment
// ─────────────────────────────────────────────────────────────────────────────
def apinizerProxySync(Map args) {
    def proxyName   = args.proxyName
    def projectName = args.projectName
    def openApiUrl  = args.openApiUrl
    def environment = args.environment
    def versionTag  = args.versionTag
    def baseUrl     = env.APINIZER_URL
    def token       = env.APINIZER_TOKEN
    def backendUrl  = openApiUrl.replace('/openapi.json', '')

    // 1 — Check if proxy exists (HTTP 200 → exists)
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

    // 2a — Proxy exists → take rollback snapshot, update spec
    if (proxyExists) {
        echo 'API proxy exists — taking rollback snapshot and updating spec...'

        sh """
            curl -s -o apinizer_backup_${environment}_${proxyName}.zip \\
                -H 'Authorization: Bearer ${token}' \\
                '${baseUrl}/apiops/projects/${projectName}/apiProxies/${proxyName}/export/'
            echo '✅ Rollback snapshot taken.'
        """
        archiveArtifacts artifacts: "apinizer_backup_${environment}_${proxyName}.zip",
                         allowEmptyArchive: true

        def proxyJson        = readJSON file: '/tmp/apinizer_get.json'
        def relativePathList = proxyJson.resultList[0].clientRoute.relativePathList
        def relativePathJson = '[' + relativePathList.collect { '"' + it + '"' }.join(',') + ']'
        echo "Existing relativePathList: ${relativePathJson}"

        def updateStatus = sh(
            script: """
                curl -s -o /tmp/apinizer_update.json -w '%{http_code}' \\
                    -X PUT \\
                    -H 'Authorization: Bearer ${token}' \\
                    -H 'Content-Type: application/json' \\
                    -d '{
                        "apiProxyName": "${proxyName}",
                        "backendApiVersion": "${versionTag}",
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
            error("❌ Proxy update failed (HTTP ${updateStatus}): ${readFile('/tmp/apinizer_update.json')}")
        }

    // 2b — Proxy does not exist → create it
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
                        "backendApiVersion": "${versionTag}",
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
            error("❌ Proxy creation failed (HTTP ${createStatus}): ${readFile('/tmp/apinizer_create.json')}")
        }
    }

    // 3 — Deploy to environment
    echo "🚀 Deploying → ${projectName}/${proxyName} @ ${environment}"
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
        error("❌ Apinizer deploy failed (HTTP ${deployStatus}): ${readFile('/tmp/apinizer_deploy.json')}")
    }
    echo "✅ Proxy '${proxyName}' successfully deployed to ${environment}."
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

            echo "Waiting 5 seconds..."
            sleep 5

            for i in 1 2 3; do
                HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
                    --connect-timeout 10 \
                    "http://$NODE_IP:${SMOKE_PORT}/health")
                echo "Attempt $i: $HTTP_STATUS"
                if [ "$HTTP_STATUS" = "200" ]; then
                    echo "✅ /health 200 OK — ${SMOKE_NAMESPACE}"
                    exit 0
                fi
                sleep 5
            done

            echo "❌ /health failed: $HTTP_STATUS (expected: 200)"
            exit 1
        '''
    }
}
