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

    // Fallback без Docker: ставим python в .venv и гоняем pytest
    stage('Tests (fallback)') {
      when { expression { return env.HAS_DOCKER == 'no' } }
      steps {
        dir('ASPD-calendar-reminder') {
        sh '''
          set -e
          if command -v python3 >/dev/null 2>&1; then PY=python3; PIP=pip3;
          elif command -v python >/dev/null 2>&1; then PY=python; PIP=pip;
          else
            echo "Python not installed on agent"; exit 2;
          fi

          $PY --version  true
          $PIP --version  true

          $PY -m venv .venv
          . .venv/bin/activate || source .venv/Scripts/activate

          python -m pip install --upgrade pip
          pip install -r requirements.txt

          pytest -q --junitxml=pytest.xml --cov=src --cov-report=term-missing --cov-report=xml
        '''
      }}
      post {
        always {
          junit 'pytest.xml'
          script {
            if (fileExists('coverage.xml')) {
              publishCoverage adapters: [coberturaAdapter('coverage.xml')],
                              sourceFileResolver: sourceFiles('STORE_LAST_BUILD')
            } else {
              echo 'coverage.xml not found — skipping coverage'
            }
          }
        }
      }
    }

    // Variant A: тесты в python:3.11 (docker run)
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
              publishCoverage adapters: [coberturaAdapter('coverage.xml')],
                              sourceFileResolver: sourceFiles('STORE_LAST_BUILD')
            } else {
              echo 'coverage.xml not found — skipping coverage'
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