pipeline {
  agent any

  environment {
    PYTHONUNBUFFERED = '1'
  }

  options {
    timestamps()
  }

  stages {
    stage('Checkout') {
      steps { checkout scm }
    }

    stage('Tests (in Docker)') {
      steps {
        sh """
          docker run --rm \
            -v "$PWD":/workspace -w /workspace \
            python:3.11 bash -lc '
              python -m pip install --upgrade pip &&
              pip install -r requirements.txt &&
              pytest -q --junitxml=pytest.xml --cov=src --cov-report=term-missing --cov-report=xml
            '
        """
      }
      post {
        always {
          junit 'pytest.xml'
          publishCoverage adapters: [coberturaAdapter('coverage.xml')], sourceFileResolver: sourceFiles('STORE_LAST_BUILD')
        }
      }
    }

    stage('Build Docker image') {
      steps {
        script {
          def img = "aspd-calendar-reminder:${env.BRANCH_NAME}-${env.BUILD_NUMBER}"
          sh "docker build -t ${img} ."
        }
      }
    }

    stage('Optional Push') {
      when { expression { return env.DOCKERHUB_PUSH?.trim() == 'true' } }
      steps {
        withCredentials([usernamePassword(credentialsId: 'dockerhub-creds', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
          sh 'echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin'
          sh 'docker tag aspd-calendar-reminder:$(git rev-parse --abbrev-ref HEAD)-${BUILD_NUMBER} $DOCKER_USER/aspd-calendar-reminder:${BUILD_NUMBER}'
          sh 'docker push $DOCKER_USER/aspd-calendar-reminder:${BUILD_NUMBER}'
        }
      }
    }
  }

  post {
    success { echo "✅ Build ${env.BUILD_TAG} succeeded" }
    failure { echo "❌ Build ${env.BUILD_TAG} failed" }
  }
}
