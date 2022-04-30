pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                sh 'sudo docker build . -t monkey-tron:py'
            }
        }
        stage('Run') {
            steps {
                withCredentials([string(credentialsId: 'token', variable: 'token')]) {
                    sh 'sudo docker run --rm monkey-tron:py -e token=$token'
                }
            }
        }
    }
}