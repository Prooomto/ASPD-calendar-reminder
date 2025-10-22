pipeline {
  agent any

  // Если твой код лежит в подпапке, задай SUBDIR='имя_папки'.
  // Если в корне — оставь пустым.
  environment {
    PYTHONUNBUFFERED = '1'
    SUBDIR = ''        // например: 'ASPD-calendar-reminder'
    IMAGE_BASENAME = 'aspd-calendar-reminder'
  }

  options {
    timestamps()
    // ansiColor('xterm')  // включи, если установлен плагин AnsiColor
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

    // --- Tests (fallback, без docker) ---
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

              $PY --version  true
              $PIP --version  true

              $PY -m venv .venv
              . .venv/bin/activate || source .venv/Scripts/activate

              python -m pip install --upgrade pip
              pip install -r requirements.txt

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
              junit 'pytest.xml'
              if (fileExists('coverage.xml')) {
                publishCoverage adapters: [coberturaAdapter('coverage.xml')],
                                sourceFileResolver: sourceFiles('STORE_LAST_BUILD')
              } else {
                echo 'coverage.xml not found — skipping coverage publish'
              }
            }
          }
        }
      }
    }

    // --- Tests (in Docker, Variant A) ---
    stage('Tests (in Docker)') {
      when { expression { return env.HAS_DOCKER == 'yes' } }
      steps {
        script {
          def mountDir = (env.SUBDIR?.trim()) ? "${env.WORKSPACE}/${env.SUBDIR}" : "${env.WORKSPACE}"
          sh """
            echo "WORKSPACE MOUNT = ${mountDir}"
            docker run --rm \
              -v "${mountDir}:/workspace" -w /workspace \
              python:3.11 bash -lc '
                set -e
                ls -la
                python -m pip install --upgrade pip &&
                pip install -r requirements.txt &&
                pytest -q --junitxml=pytest.xml --cov=src --cov-report=term-missing --cov-report=xml
              '
          """
        }
      }
      post {
        always {
          script {
            def runDir = (env.SUBDIR?.trim()) ? "${env.WORKSPACE}/${env.SUBDIR}" : "${env.WORKSPACE}"
            dir(runDir) {
              junit 'pytest.xml'
              if (fileExists('coverage.xml')) {
                publishCoverage adapters: [coberturaAdapter('coverage.xml')],
                                sourceFileResolver: sourceFiles('STORE_LAST_BUILD')
              } else {
                echo 'coverage.xml not found — skipping coverage publish'
              }
            }
          }
        }
      }
    }

    // --- Build image ---
    stage('Build Docker image') {
      when { expression { return env.HAS_DOCKER == 'yes' } }
      steps {
        script {
          // тег вида: basename:branch-build
          def branch = sh(returnStdout: true, script: 'git rev-parse --abbrev-ref HEAD').trim()
          env.IMAGE_TAG = "${env.IMAGE_BASENAME}:${branch}-${env.BUILD_NUMBER}"
          def buildCtx = (env.SUBDIR?.trim()) ? "${env.WORKSPACE}/${env.SUBDIR}" : "${env.WORKSPACE}"
          sh "docker build -t ${env.IMAGE_TAG} \"${buildCtx}\""
          echo "Built image: ${env.IMAGE_TAG}"
        }
      }
    }

    // --- Optional push ---
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
            // пуш в свой namespace: $DOCKER_USER/<name>:buildNumber
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