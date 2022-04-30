pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                sh 'sudo docker build . -t monkey-tron:py'
            }
        }
        stage('Remove Previous Container') {
            steps {
                sh '''
                if docker ps | grep -q monkeytron-''' + env.BRANCH_NAME + '''; then
                    docker rm monkeytron-''' + env.BRANCH_NAME + '''
                fi'''
            }
        }
        stage('Run') {
            steps {
                withCredentials([string(credentialsId: 'token', variable: 'token')]) {
                    sh 'sudo docker run --name monkeytron-' + env.BRANCH_NAME + ' -e token=$token -d monkey-tron:py'
                }
            }
        }
    }
}