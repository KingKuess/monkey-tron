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
                sh 'sudo docker run --rm monkey-tron:py'
            }
        }
    }
}