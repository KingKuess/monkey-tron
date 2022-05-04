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
                if sudo docker ps | grep -q monkeytron-''' + env.BRANCH_NAME + '''; then
                    sudo docker rm -f monkeytron-''' + env.BRANCH_NAME + '''
                fi'''
            }
        }
        stage('Run') {
            steps {
                withCredentials([string(credentialsId: 'token', variable: 'token')]) {
                    sh 'sudo docker run --restart=always --name monkeytron-' + env.BRANCH_NAME + ' -e token=$token -d monkey-tron:py'
                }
            }
        }
    }
}