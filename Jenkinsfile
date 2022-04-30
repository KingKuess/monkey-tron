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
                sh 'sudo docker run --env-file /home/jenkins/.env --rm monkey-tron:py'
            }
        }
    }
}