pipeline {
    agent any

    parameters {
        string(name: 'SHA_TAG', defaultValue: 'latest', description: 'Docker image tag pushed by CI (e.g. sha-abc1234)')
    }

    environment {
        IMAGE_BASE     = 'apinizeren/messaging'
        NODE_IP        = '167.86.118.166'
        DEV_NODE_PORT  = '30211'
        TEST_NODE_PORT = '30212'
        UAT_NODE_PORT  = '30213'
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Deploy Dev') {
            steps {
                withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                    sh """
                        cd k8s/overlays/dev
                        kustomize edit set image ${IMAGE_BASE}=${IMAGE_BASE}:${params.SHA_TAG}
                        kubectl --kubeconfig=\$KUBECONFIG apply -k .
                    """
                }
            }
            post { failure { echo '❌ Deploy Dev başarısız.' } }
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

        stage('Deploy Test') {
            steps {
                withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                    sh """
                        cd k8s/overlays/test
                        kustomize edit set image ${IMAGE_BASE}=${IMAGE_BASE}:${params.SHA_TAG}
                        kubectl --kubeconfig=\$KUBECONFIG apply -k .
                    """
                }
            }
            post { failure { echo '❌ Deploy Test başarısız.' } }
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

        stage('Deploy UAT') {
            steps {
                withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                    sh """
                        cd k8s/overlays/uat
                        kustomize edit set image ${IMAGE_BASE}=${IMAGE_BASE}:${params.SHA_TAG}
                        kubectl --kubeconfig=\$KUBECONFIG apply -k .
                    """
                }
            }
            post { failure { echo '❌ Deploy UAT başarısız.' } }
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

def smokeTest(String namespace, String nodePort) {
    withEnv(["SMOKE_NAMESPACE=${namespace}", "SMOKE_PORT=${nodePort}"]) {
        sh '''
            echo "Smoke test: http://$NODE_IP:${SMOKE_PORT}/health"

            kubectl rollout status deployment/messaging-api \
                -n ${SMOKE_NAMESPACE} \
                --timeout=120s

            HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
                "http://$NODE_IP:${SMOKE_PORT}/health")

            if [ "$HTTP_STATUS" != "200" ]; then
                echo "❌ /health döndü: $HTTP_STATUS (beklenen: 200)"
                exit 1
            fi
            echo "✅ /health 200 OK — ${SMOKE_NAMESPACE}"
        '''
    }
}
