pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                sh 'docker build . -t monkey-tron:py'
            }
        }
        stage('Run') {
            steps {
                sh 'docker run --rm monkey-tron:py'
            }
        }
    }
}