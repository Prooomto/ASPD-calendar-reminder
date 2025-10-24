pipeline {
  agent any

  environment {
    PYTHONUNBUFFERED = '1'
    IMAGE_BASENAME   = 'aspd-calendar-reminder'
    SUBDIR           = ''   // код и requirements.txt в КОРНЕ
  }

  options {
    timestamps()
    // ansiColor('xterm') // включи при наличии AnsiColor
  }

  stages {

    stage('Checkout') {
      steps { checkout scm }
    }

    stage('Detect Docker') {
      steps {
        script {
          def s = sh(returnStatus: true, script: 'command -v docker >/dev/null 2>&1')
          env.HAS_DOCKER = (s == 0) ? 'yes' : 'no'
          echo "HAS_DOCKER = ${env.HAS_DOCKER}"
        }
      }
    }

    // ----- Tests (fallback: без docker) -----
    stage('Tests (fallback)') {
      when { expression { return env.HAS_DOCKER == 'no' } }
      steps {
        script {
          def runDir = (env.SUBDIR?.trim()) ? "${env.WORKSPACE}/${env.SUBDIR}" : "${env.WORKSPACE}"
          dir(runDir) {
            sh '''
              set -e
              if command -v python3 >/dev/null 2>&1; then PY=python3; PIP=pip3;
              elif command -v python >/dev/null 2>&1; then PY=python; PIP=pip;
              else
                echo "Python not installed on agent"; exit 2;
              fi

              $PY --version || true
              $PIP --version || true

              $PY -m venv .venv
              . .venv/bin/activate || source .venv/Scripts/activate

              python -m pip install --upgrade pip
              pip install -r requirements.txt
              pip install pytest pytest-cov

              pytest -q --junitxml=pytest.xml --cov=src --cov-report=term-missing --cov-report=xml
            '''
          }
        }
      }
      post {
        always {
          script {
            def runDir = (env.SUBDIR?.trim()) ? "${env.WORKSPACE}/${env.SUBDIR}" : "${env.WORKSPACE}"
            dir(runDir) {
              if (fileExists('pytest.xml')) junit 'pytest.xml' else echo 'pytest.xml not found'
              if (fileExists('coverage.xml')) {
                publishCoverage adapters: [coberturaAdapter('coverage.xml')],
                                sourceFileResolver: sourceFiles('STORE_LAST_BUILD')
              } else echo 'coverage.xml not found'
            }
          }
        }
      }
    }

    // ----- Tests (in Docker, без bind-mount) -----
    stage('Tests (in Docker)') {
      when { expression { return env.HAS_DOCKER == 'yes' } }
      steps {
        script {
          def runDir = (env.SUBDIR?.trim()) ? "${env.WORKSPACE}/${env.SUBDIR}" : "${env.WORKSPACE}"
          dir(runDir) {
            sh '''
              set -e
              echo "RunDir: $(pwd)"

              # 1) Создаём контейнер
              CID=$(docker create -w /workspace python:3.11 bash -lc "
                set -e
                python -m pip install --upgrade pip &&
                pip install -r requirements.txt &&
                pip install pytest pytest-cov &&
                pytest -q --junitxml=pytest.xml --cov=src --cov-report=term-missing --cov-report=xml
              ")

              # 2) Копируем исходники внутрь контейнера
              docker cp . "$CID:/workspace"

              # 3) Запускаем и ждём завершения
              set +e
              docker start -a "$CID"
              EXIT_CODE=$?
              set -e

              # 4) Забираем отчёты обратно (не падать, если файла нет)
              docker cp "$CID:/workspace/pytest.xml"   ./pytest.xml   2>/dev/null || true
              docker cp "$CID:/workspace/coverage.xml" ./coverage.xml 2>/dev/null || true

              # 5) Удаляем контейнер
              docker rm -f "$CID" >/dev/null 2>&1 || true
              exit $EXIT_CODE
            '''
          }
        }
      }
      post {
        always {
          script {
            def runDir = (env.SUBDIR?.trim()) ? "${env.WORKSPACE}/${env.SUBDIR}" : "${env.WORKSPACE}"
            dir(runDir) {
              if (fileExists('pytest.xml')) junit 'pytest.xml' else echo 'pytest.xml not found'
              if (fileExists('coverage.xml')) {
                publishCoverage adapters: [coberturaAdapter('coverage.xml')],
                                sourceFileResolver: sourceFiles('STORE_LAST_BUILD')
              } else echo 'coverage.xml not found'
            }
          }
        }
      }
    }

    // ----- Build Docker image -----
    stage('Build Docker image') {
      when { expression { return env.HAS_DOCKER == 'yes' } }
      steps {
        script {
          def branch = sh(returnStdout: true, script: 'git rev-parse --abbrev-ref HEAD').trim()
          env.IMAGE_TAG = "${env.IMAGE_BASENAME}:${branch}-${env.BUILD_NUMBER}"
          def buildCtx = (env.SUBDIR?.trim()) ? "${env.WORKSPACE}/${env.SUBDIR}" : "${env.WORKSPACE}"
          sh "docker build -t ${env.IMAGE_TAG} \"${buildCtx}\""
          echo "Built image: ${env.IMAGE_TAG}"
        }
      }
    }

    // ----- Optional Push -----
    stage('Optional Push') {
      when { expression { return env.HAS_DOCKER == 'yes' && env.DOCKERHUB_PUSH?.trim() == 'true' } }
      steps {
        script {
          withCredentials([usernamePassword(
            credentialsId: 'dockerhub-creds',
            usernameVariable: 'DOCKER_USER',
            passwordVariable: 'DOCKER_PASS'
          )]) {
            sh '''
              set -e
              echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin
            '''
            def pushTag = "${env.DOCKER_USER}/${env.IMAGE_BASENAME}:${env.BUILD_NUMBER}"
            sh """
              docker tag ${env.IMAGE_TAG} ${pushTag}
              docker push ${pushTag}
              echo "Pushed: ${pushTag}"
            """
          }
        }
      }
    }
  }

  post {
    success { echo "✅ Build ${env.BUILD_TAG} succeeded" }
    failure { echo "❌ Build ${env.BUILD_TAG} failed" }
  }
}