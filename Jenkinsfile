pipeline {
  agent any

  environment { PYTHONUNBUFFERED = '1' }

  options { timestamps() }

  stages {
    stage('Checkout') {
      steps { checkout scm }
    }

    stage('Detect Docker') {
      steps {
        script {
          def status = sh(returnStatus: true, script: 'command -v docker >/dev/null 2>&1')
          env.HAS_DOCKER = (status == 0) ? 'yes' : 'no'
          echo "HAS_DOCKER = ${env.HAS_DOCKER}"
        }
      }
    }

    stage('Tests') {
      when { expression { return env.HAS_DOCKER == 'no' } }
      steps {
        sh '''
          # локально без docker: ставим питон-зависимости в venv
          python3 -V  true
          pip3 -V  true
          python3 -m venv .venv
          . .venv/bin/activate || source .venv/Scripts/activate
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pytest -q --junitxml=pytest.xml --cov=src --cov-report=term-missing --cov-report=xml
        '''
      }
      post {
        always {
          junit 'pytest.xml'
          script {
            if (fileExists('coverage.xml')) {
              publishCoverage adapters: [coberturaAdapter('coverage.xml')], sourceFileResolver: sourceFiles('STORE_LAST_BUILD')
            } else {
              echo 'coverage.xml not found — skipping coverage publish'
            }
          }
        }
      }
    }

    stage('Tests (in Docker)') {
      when { expression { return env.HAS_DOCKER == 'yes' } }
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
          script {
            if (fileExists('coverage.xml')) {
              publishCoverage adapters: [coberturaAdapter('coverage.xml')], sourceFileResolver: sourceFiles('STORE_LAST_BUILD')
            } else {
              echo 'coverage.xml not found — skipping coverage publish'
            }
          }
        }
      }
    }

    stage('Build Docker image') {
      when { expression { return env.HAS_DOCKER == 'yes' } }
      steps {
        script {
          def img = "aspd-calendar-reminder:${env.BRANCH_NAME}-${env.BUILD_NUMBER}"
          sh "docker build -t ${img} ."
        }
      }
    }

    stage('Optional Push') {
      when { expression { return env.HAS_DOCKER == 'yes' && env.DOCKERHUB_PUSH?.trim() == 'true' } }
      steps {
        withCredentials([usernamePassword(credentialsId: 'dockerhub-creds',
                                          usernameVariable: 'DOCKER_USER',
                                          passwordVariable: 'DOCKER_PASS')]) {
          sh '''
            echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
            BRANCH=$(git rev-parse --abbrev-ref HEAD)
            docker tag aspd-calendar-reminder:${BRANCH}-${BUILD_NUMBER} $DOCKER_USER/aspd-calendar-reminder:${BUILD_NUMBER}
            docker push $DOCKER_USER/aspd-calendar-reminder:${BUILD_NUMBER}
          '''
        }
      }
    }
  }

  post {
    success { echo "✅ Build ${env.BUILD_TAG} succeeded" }
    failure { echo "❌ Build ${env.BUILD_TAG} failed" }
  }
}