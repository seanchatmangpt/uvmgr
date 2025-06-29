# 🚀 CI/CD Integration Guide - DoD Automation

## Table of Contents
- [Overview](#overview)
- [GitHub Actions](#github-actions)
- [GitLab CI/CD](#gitlab-cicd)
- [Azure DevOps](#azure-devops)
- [Jenkins](#jenkins)
- [AWS CodePipeline](#aws-codepipeline)
- [Google Cloud Build](#google-cloud-build)
- [CircleCI](#circleci)
- [Multi-Platform Strategies](#multi-platform-strategies)
- [Security Best Practices](#security-best-practices)

## Overview

The DoD Automation system provides seamless integration with all major CI/CD platforms. Each integration follows the **80/20 principle** to deliver maximum automation value with minimal configuration effort.

### Universal Integration Pattern
```yaml
# Universal CI/CD Integration Pattern
stages:
  - validate          # DoD criteria validation (quick feedback)
  - test             # Comprehensive testing (quality assurance)  
  - security         # Security scanning (safety validation)
  - deploy           # Deployment automation (delivery)
  - monitor          # Post-deployment monitoring (observability)

# 80/20 Optimization
critical_stages: [validate, test, security]    # 70% of value
important_stages: [deploy]                     # 25% of value  
optional_stages: [monitor]                     # 5% of value
```

### Key Benefits
- ✅ **Standardized Workflows**: Consistent automation across all platforms
- ✅ **80/20 Optimization**: Focus on high-impact CI/CD activities
- ✅ **Platform-Specific Features**: Leverage unique platform capabilities
- ✅ **Security Integration**: Built-in security scanning and compliance
- ✅ **Observability**: Complete telemetry and monitoring

## GitHub Actions

### Quick Setup

#### 1. Generate GitHub Actions Workflow
```bash
# Generate comprehensive GitHub Actions pipeline
uvmgr dod pipeline --provider=github --environments=dev,staging,prod

# Enterprise template with security features
uvmgr dod pipeline --provider=github --template=enterprise --features=security,testing,deployment
```

#### 2. Generated Workflow Example
```yaml
# .github/workflows/dod-automation.yml
name: 'DoD Automation Pipeline'

on:
  push:
    branches: [main, develop, 'feature/*']
  pull_request:
    branches: [main, develop]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

env:
  UVMGR_OTEL_ENDPOINT: ${{ secrets.OTEL_ENDPOINT }}
  UVMGR_AI_API_KEY: ${{ secrets.AI_API_KEY }}

jobs:
  # 80/20 Critical Stage (70% value)
  dod-critical:
    name: 'Critical DoD Validation'
    runs-on: ubuntu-latest
    timeout-minutes: 15
    
    strategy:
      matrix:
        python-version: ['3.11', '3.12']
    
    steps:
      - name: 'Checkout Code'
        uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for proper analysis
      
      - name: 'Set up Python'
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'
      
      - name: 'Install uvmgr'
        run: |
          python -m pip install --upgrade pip
          pip install uvmgr[all]
      
      - name: 'Initialize DoD Exoskeleton'
        run: uvmgr dod exoskeleton --template=standard --force
      
      - name: 'Execute Critical DoD Automation'
        run: |
          uvmgr dod complete \
            --env=development \
            --criteria=testing,security,devops \
            --parallel \
            --auto-fix
        env:
          UVMGR_CI: 'true'
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      
      - name: 'Upload DoD Report'
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: dod-report-${{ matrix.python-version }}
          path: |
            dod-automation-report.json
            .uvmgr/automation/reports/
            reports/
  
  # Important Stage (25% value)
  dod-comprehensive:
    name: 'Comprehensive DoD Validation'
    runs-on: ubuntu-latest
    needs: dod-critical
    if: github.ref == 'refs/heads/main'
    
    steps:
      - name: 'Checkout Code'
        uses: actions/checkout@v4
      
      - name: 'Set up Python'
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: 'Install uvmgr'
        run: pip install uvmgr[all]
      
      - name: 'Complete DoD Automation'
        run: |
          uvmgr dod complete \
            --env=staging \
            --comprehensive \
            --ai-assist \
            --parallel
      
      - name: 'Generate Deployment Pipeline'
        run: |
          uvmgr dod pipeline \
            --provider=github \
            --environments=staging,prod \
            --template=enterprise
  
  # Security-Focused Stage
  security-scan:
    name: 'Security Validation'
    runs-on: ubuntu-latest
    needs: dod-critical
    
    steps:
      - name: 'Checkout Code'
        uses: actions/checkout@v4
      
      - name: 'Run Security DoD'
        run: |
          pip install uvmgr[security]
          uvmgr dod complete \
            --criteria=security,compliance \
            --env=production \
            --detailed
      
      - name: 'Security Report'
        uses: github/codeql-action/upload-sarif@v2
        if: always()
        with:
          sarif_file: security-report.sarif

  # Deployment Stage (Production)
  deploy-production:
    name: 'Production Deployment'
    runs-on: ubuntu-latest
    needs: [dod-comprehensive, security-scan]
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    environment: production
    
    steps:
      - name: 'Checkout Code'
        uses: actions/checkout@v4
      
      - name: 'Production DoD Validation'
        run: |
          pip install uvmgr[all]
          uvmgr dod complete \
            --env=production \
            --criteria=security,devops,compliance \
            --ai-assist
      
      - name: 'Deploy Application'
        run: |
          # Your deployment commands here
          echo "Deploying with DoD validation complete"
```

#### 3. Advanced GitHub Features

##### Matrix Strategy for Multi-Environment Testing
```yaml
# Multi-environment matrix testing
strategy:
  matrix:
    environment: [development, staging, production]
    python-version: ['3.11', '3.12']
    include:
      - environment: development
        criteria: "testing,code_quality"
        timeout: 10
      - environment: staging  
        criteria: "testing,security,devops"
        timeout: 20
      - environment: production
        criteria: "security,devops,compliance"
        timeout: 30

steps:
  - name: 'Environment-Specific DoD'
    run: |
      uvmgr dod complete \
        --env=${{ matrix.environment }} \
        --criteria=${{ matrix.criteria }} \
        --timeout=${{ matrix.timeout }}
    timeout-minutes: ${{ matrix.timeout }}
```

##### Conditional Execution Based on Changes
```yaml
# Smart execution based on file changes
- name: 'Detect Changes'
  uses: dorny/paths-filter@v2
  id: changes
  with:
    filters: |
      python:
        - '**/*.py'
      security:
        - 'requirements*.txt'
        - 'pyproject.toml'
      docs:
        - '**/*.md'
        - 'docs/**'

- name: 'Run Python DoD'
  if: steps.changes.outputs.python == 'true'
  run: uvmgr dod complete --criteria=testing,code_quality

- name: 'Run Security DoD'  
  if: steps.changes.outputs.security == 'true'
  run: uvmgr dod complete --criteria=security --detailed
```

## GitLab CI/CD

### Quick Setup

#### 1. Generate GitLab CI Pipeline
```bash
# Generate GitLab CI/CD pipeline
uvmgr dod pipeline --provider=gitlab-ci --environments=dev,staging,prod

# Enterprise template with advanced features
uvmgr dod pipeline --provider=gitlab-ci --template=enterprise --features=security,testing,compliance
```

#### 2. Generated Pipeline Example
```yaml
# .gitlab-ci.yml
include:
  - template: Security/SAST.gitlab-ci.yml
  - template: Security/Dependency-Scanning.gitlab-ci.yml

variables:
  UVMGR_CI: "true"
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

cache:
  paths:
    - .cache/pip
    - .uvmgr_cache/

stages:
  - validate
  - test
  - security
  - deploy
  - monitor

# 80/20 Critical Validation (Development)
dod-critical:
  stage: validate
  image: python:3.11
  before_script:
    - pip install uvmgr[all]
    - uvmgr dod exoskeleton --template=enterprise --force
  script:
    - |
      uvmgr dod complete \
        --env=development \
        --criteria=testing,code_quality \
        --parallel \
        --auto-fix
  artifacts:
    reports:
      junit: reports/pytest.xml
      coverage_report:
        coverage_format: cobertura
        path: reports/coverage.xml
    paths:
      - dod-automation-report.json
      - .uvmgr/automation/reports/
    expire_in: 1 week
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

# Comprehensive Testing (Staging)  
dod-comprehensive:
  stage: test
  image: python:3.11
  needs: ["dod-critical"]
  script:
    - pip install uvmgr[all]
    - |
      uvmgr dod complete \
        --env=staging \
        --criteria=testing,security,devops \
        --comprehensive \
        --ai-assist
  artifacts:
    reports:
      junit: reports/pytest.xml
      coverage_report:
        coverage_format: cobertura
        path: reports/coverage.xml
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

# Security Validation
dod-security:
  stage: security  
  image: python:3.11
  needs: ["dod-critical"]
  script:
    - pip install uvmgr[security]
    - |
      uvmgr dod complete \
        --criteria=security,compliance \
        --env=production \
        --detailed \
        --fix-suggestions
  artifacts:
    reports:
      sast: security-report.json
      dependency_scanning: dependency-report.json
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

# Production Deployment
deploy-production:
  stage: deploy
  image: python:3.11
  needs: ["dod-comprehensive", "dod-security"]
  environment:
    name: production
    url: https://production.example.com
  script:
    - pip install uvmgr[all]
    - |
      uvmgr dod complete \
        --env=production \
        --criteria=security,devops,compliance \
        --ai-assist \
        --parallel
    - |
      # Your deployment script here
      echo "Deploying to production with DoD validation"
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
      when: manual
  
# Performance Monitoring
monitor-performance:
  stage: monitor
  image: python:3.11
  needs: ["deploy-production"]
  script:
    - pip install uvmgr[all]
    - |
      uvmgr dod testing \
        --strategy=performance \
        --environment=production \
        --record-video
  artifacts:
    paths:
      - performance-report.html
      - test-videos/
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
      when: delayed
      start_in: 5 minutes
```

#### 3. GitLab-Specific Features

##### Dynamic Child Pipelines
```yaml
# Generate dynamic pipelines based on project structure
generate-dynamic-pipeline:
  stage: validate
  image: python:3.11
  script:
    - pip install uvmgr[all]
    - uvmgr dod pipeline --provider=gitlab-ci --dynamic --output=generated-pipeline.yml
  artifacts:
    paths:
      - generated-pipeline.yml
    
trigger-dynamic:
  stage: test
  trigger:
    include:
      - artifact: generated-pipeline.yml
        job: generate-dynamic-pipeline
```

##### Multi-Project Pipeline Integration  
```yaml
# Trigger DoD validation in dependent projects
trigger-dependent-validation:
  stage: deploy
  trigger:
    project: group/dependent-project
    branch: main
    strategy: depend
  variables:
    UPSTREAM_DOD_SCORE: $DOD_OVERALL_SCORE
    TRIGGER_SOURCE: "upstream-validation"
```

## Azure DevOps

### Quick Setup

#### 1. Generate Azure DevOps Pipeline
```bash
# Generate Azure DevOps pipeline
uvmgr dod pipeline --provider=azure-devops --environments=dev,staging,prod

# Enterprise template with Microsoft integrations
uvmgr dod pipeline --provider=azure-devops --template=enterprise --features=security,testing,azure-integration
```

#### 2. Generated Pipeline Example
```yaml
# azure-pipelines.yml
trigger:
  branches:
    include:
      - main
      - develop
      - feature/*

pr:
  branches:
    include:
      - main
      - develop

variables:
  pythonVersion: '3.11'
  uvmgrVersion: 'latest'

pool:
  vmImage: 'ubuntu-latest'

stages:
  # 80/20 Critical Stage
  - stage: ValidateDoD
    displayName: 'DoD Critical Validation'
    jobs:
      - job: CriticalValidation
        displayName: 'Critical DoD Criteria'
        timeoutInMinutes: 15
        
        strategy:
          matrix:
            Python311:
              pythonVersion: '3.11'
            Python312:
              pythonVersion: '3.12'
        
        steps:
          - task: UsePythonVersion@0
            inputs:
              versionSpec: '$(pythonVersion)'
            displayName: 'Use Python $(pythonVersion)'
          
          - script: |
              python -m pip install --upgrade pip
              pip install uvmgr[all]
            displayName: 'Install uvmgr'
          
          - script: |
              uvmgr dod exoskeleton --template=enterprise --force
            displayName: 'Initialize DoD Exoskeleton'
          
          - script: |
              uvmgr dod complete \
                --env=development \
                --criteria=testing,security,devops \
                --parallel \
                --auto-fix
            displayName: 'Execute Critical DoD Automation'
            env:
              UVMGR_CI: 'true'
              SYSTEM_ACCESSTOKEN: $(System.AccessToken)
          
          - task: PublishTestResults@2
            inputs:
              testResultsFiles: 'reports/pytest.xml'
              testRunTitle: 'DoD Tests - Python $(pythonVersion)'
            condition: succeededOrFailed()
          
          - task: PublishCodeCoverageResults@1
            inputs:
              codeCoverageTool: 'cobertura'
              summaryFileLocation: 'reports/coverage.xml'
            condition: succeededOrFailed()
          
          - task: PublishBuildArtifacts@1
            inputs:
              pathToPublish: 'dod-automation-report.json'
              artifactName: 'dod-report-$(pythonVersion)'
            condition: succeededOrFailed()

  # Comprehensive Testing Stage
  - stage: ComprehensiveTest
    displayName: 'Comprehensive DoD Testing'
    dependsOn: ValidateDoD
    condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
    
    jobs:
      - job: ComprehensiveValidation
        displayName: 'Comprehensive DoD Validation'
        
        steps:
          - task: UsePythonVersion@0
            inputs:
              versionSpec: '$(pythonVersion)'
          
          - script: pip install uvmgr[all]
            displayName: 'Install uvmgr'
          
          - script: |
              uvmgr dod complete \
                --env=staging \
                --comprehensive \
                --ai-assist \
                --parallel
            displayName: 'Comprehensive DoD Automation'
          
          - task: AzureKeyVault@2
            inputs:
              azureSubscription: 'azure-service-connection'
              KeyVaultName: 'dod-automation-vault'
              SecretsFilter: 'ai-api-key,otel-endpoint'
            displayName: 'Get Secrets from Key Vault'

  # Security Validation
  - stage: SecurityValidation
    displayName: 'Security DoD Validation'
    dependsOn: ValidateDoD
    
    jobs:
      - job: SecurityScan
        displayName: 'Security DoD Scan'
        
        steps:
          - task: UsePythonVersion@0
            inputs:
              versionSpec: '$(pythonVersion)'
          
          - script: pip install uvmgr[security]
            displayName: 'Install uvmgr with security features'
          
          - script: |
              uvmgr dod complete \
                --criteria=security,compliance \
                --env=production \
                --detailed \
                --fix-suggestions
            displayName: 'Security DoD Validation'
          
          - task: PublishSecurityAnalysisLogs@3
            inputs:
              artifactName: 'CodeAnalysisLogs'
            condition: succeededOrFailed()

  # Production Deployment
  - stage: ProductionDeploy
    displayName: 'Production Deployment'
    dependsOn: 
      - ComprehensiveTest
      - SecurityValidation
    condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
    
    jobs:
      - deployment: DeployProduction
        displayName: 'Deploy to Production'
        environment: 'production'
        
        strategy:
          runOnce:
            deploy:
              steps:
                - task: UsePythonVersion@0
                  inputs:
                    versionSpec: '$(pythonVersion)'
                
                - script: pip install uvmgr[all]
                  displayName: 'Install uvmgr'
                
                - script: |
                    uvmgr dod complete \
                      --env=production \
                      --criteria=security,devops,compliance \
                      --ai-assist
                  displayName: 'Production DoD Validation'
                
                - script: |
                    # Your deployment commands here
                    echo "Deploying to production with DoD validation"
                  displayName: 'Deploy Application'
```

#### 3. Azure-Specific Integrations

##### Azure Key Vault Integration
```yaml
# Secure secret management
- task: AzureKeyVault@2
  inputs:
    azureSubscription: 'azure-service-connection'
    KeyVaultName: 'dod-automation-vault'
    SecretsFilter: |
      ai-api-key
      otel-endpoint
      security-scan-token
  displayName: 'Get DoD Automation Secrets'

- script: |
    uvmgr dod complete \
      --ai-assist \
      --env=production
  env:
    UVMGR_AI_API_KEY: $(ai-api-key)
    UVMGR_OTEL_ENDPOINT: $(otel-endpoint)
  displayName: 'DoD with Secure Configuration'
```

##### Azure Monitor Integration
```yaml
# Send DoD metrics to Azure Monitor
- script: |
    uvmgr dod complete \
      --env=production \
      --telemetry-endpoint=$(AZURE_MONITOR_ENDPOINT) \
      --telemetry-key=$(AZURE_MONITOR_KEY)
  displayName: 'DoD with Azure Monitor Telemetry'
```

## Jenkins

### Quick Setup

#### 1. Generate Jenkins Pipeline
```bash
# Generate Jenkinsfile
uvmgr dod pipeline --provider=jenkins --environments=dev,staging,prod

# Enterprise template with Jenkins plugins
uvmgr dod pipeline --provider=jenkins --template=enterprise --features=security,testing,jenkins-plugins
```

#### 2. Generated Jenkinsfile Example
```groovy
// Jenkinsfile
pipeline {
    agent any
    
    options {
        timeout(time: 1, unit: 'HOURS')
        retry(2)
        skipStagesAfterUnstable()
    }
    
    environment {
        UVMGR_CI = 'true'
        PYTHON_VERSION = '3.11'
        UVMGR_OTEL_ENDPOINT = credentials('otel-endpoint')
        UVMGR_AI_API_KEY = credentials('ai-api-key')
    }
    
    stages {
        stage('Setup') {
            steps {
                script {
                    // Setup Python environment
                    sh '''
                        python${PYTHON_VERSION} -m venv venv
                        . venv/bin/activate
                        pip install --upgrade pip
                        pip install uvmgr[all]
                    '''
                }
            }
        }
        
        stage('DoD Critical Validation') {
            parallel {
                stage('Development DoD') {
                    when {
                        anyOf {
                            branch 'develop'
                            branch 'feature/*'
                        }
                    }
                    steps {
                        script {
                            sh '''
                                . venv/bin/activate
                                uvmgr dod exoskeleton --template=standard --force
                                uvmgr dod complete \
                                    --env=development \
                                    --criteria=testing,code_quality \
                                    --parallel \
                                    --auto-fix
                            '''
                        }
                    }
                    post {
                        always {
                            publishTestResults testResultsPattern: 'reports/pytest.xml'
                            publishHTML([
                                allowMissing: false,
                                alwaysLinkToLastBuild: true,
                                keepAll: true,
                                reportDir: 'reports',
                                reportFiles: 'coverage.html',
                                reportName: 'Coverage Report'
                            ])
                        }
                    }
                }
                
                stage('Security DoD') {
                    steps {
                        script {
                            sh '''
                                . venv/bin/activate
                                uvmgr dod complete \
                                    --criteria=security,compliance \
                                    --env=staging \
                                    --detailed \
                                    --fix-suggestions
                            '''
                        }
                    }
                    post {
                        always {
                            publishHTML([
                                allowMissing: false,
                                alwaysLinkToLastBuild: true,
                                keepAll: true,
                                reportDir: 'reports',
                                reportFiles: 'security-report.html',
                                reportName: 'Security Report'
                            ])
                        }
                    }
                }
            }
        }
        
        stage('Comprehensive DoD') {
            when {
                branch 'main'
            }
            steps {
                script {
                    sh '''
                        . venv/bin/activate
                        uvmgr dod complete \
                            --env=staging \
                            --comprehensive \
                            --ai-assist \
                            --parallel
                    '''
                }
            }
            post {
                always {
                    archiveArtifacts artifacts: 'dod-automation-report.json', fingerprint: true
                    publishTestResults testResultsPattern: 'reports/**/*.xml'
                }
            }
        }
        
        stage('Production Deployment') {
            when {
                allOf {
                    branch 'main'
                    expression { return currentBuild.result == null || currentBuild.result == 'SUCCESS' }
                }
            }
            steps {
                script {
                    // Manual approval for production
                    input message: 'Deploy to production?', ok: 'Deploy'
                    
                    sh '''
                        . venv/bin/activate
                        uvmgr dod complete \
                            --env=production \
                            --criteria=security,devops,compliance \
                            --ai-assist
                        
                        # Your deployment commands here
                        echo "Deploying to production with DoD validation"
                    '''
                }
            }
            post {
                success {
                    emailext (
                        subject: "Production Deployment Successful - ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                        body: "DoD automation validation passed. Production deployment completed successfully.",
                        to: "${env.NOTIFICATION_EMAIL}"
                    )
                }
                failure {
                    emailext (
                        subject: "Production Deployment Failed - ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                        body: "DoD automation validation failed. Check the build logs for details.",
                        to: "${env.NOTIFICATION_EMAIL}"
                    )
                }
            }
        }
    }
    
    post {
        always {
            script {
                // Generate final DoD report
                sh '''
                    . venv/bin/activate
                    uvmgr dod status --detailed --format=json > final-dod-status.json
                '''
                archiveArtifacts artifacts: 'final-dod-status.json'
            }
        }
        cleanup {
            deleteDir()
        }
    }
}
```

#### 3. Jenkins-Specific Features

##### Blue Ocean Pipeline Visualization
```groovy
// Enhanced pipeline for Blue Ocean
pipeline {
    agent any
    
    stages {
        stage('DoD Automation') {
            parallel {
                stage('Testing') {
                    steps {
                        sh 'uvmgr dod complete --criteria=testing'
                    }
                }
                stage('Security') {
                    steps {
                        sh 'uvmgr dod complete --criteria=security'
                    }
                }
                stage('DevOps') {
                    steps {
                        sh 'uvmgr dod complete --criteria=devops'
                    }
                }
            }
        }
    }
}
```

##### Jenkins Plugin Integration
```groovy
// Integration with Jenkins plugins
stage('DoD with Plugins') {
    steps {
        // SonarQube integration
        withSonarQubeEnv('SonarQube') {
            sh 'uvmgr dod complete --criteria=code_quality --sonar-integration'
        }
        
        // Slack notification
        slackSend(
            channel: '#ci-cd',
            color: 'good',
            message: "DoD automation completed successfully for ${env.JOB_NAME}"
        )
        
        // Jira integration
        jiraAddComment(
            idOrKey: "${env.JIRA_ISSUE}",
            comment: "DoD automation validation passed. Ready for deployment."
        )
    }
}
```

## Multi-Platform Strategies

### Universal Configuration Management
```yaml
# .uvmgr/ci-config.yaml - Universal CI/CD configuration
ci_platforms:
  github:
    workflows_path: ".github/workflows"
    features: ["actions", "security", "packages"]
    secrets: ["GITHUB_TOKEN"]
    
  gitlab:
    workflows_path: ".gitlab-ci.yml"
    features: ["security", "registry", "pages"]
    variables: ["CI_REGISTRY_IMAGE"]
    
  azure:
    workflows_path: "azure-pipelines.yml"
    features: ["keyvault", "monitor", "artifacts"]
    connections: ["azure-service-connection"]
    
  jenkins:
    workflows_path: "Jenkinsfile"
    features: ["plugins", "distributed", "security"]
    credentials: ["ai-api-key", "otel-endpoint"]

# 80/20 Strategy per platform
optimization_strategy:
  development:
    critical: ["testing", "code_quality"]    # Fast feedback
    timeout: 10
    
  staging:
    critical: ["testing", "security", "devops"]  # Pre-production validation
    timeout: 20
    
  production:
    critical: ["security", "devops", "compliance"]  # Maximum validation
    timeout: 30
```

### Cross-Platform Pipeline Generation
```bash
# Generate pipelines for all platforms
uvmgr dod pipeline --provider=all --environments=dev,staging,prod

# Platform-specific optimizations
uvmgr dod pipeline --provider=github --optimize-for=speed
uvmgr dod pipeline --provider=gitlab --optimize-for=security  
uvmgr dod pipeline --provider=azure --optimize-for=integration
uvmgr dod pipeline --provider=jenkins --optimize-for=flexibility
```

## Security Best Practices

### Secret Management
```yaml
# Secure secret handling across platforms
secrets_management:
  github:
    - name: AI_API_KEY
      description: "AI service API key for DoD automation"
      required: true
    - name: OTEL_ENDPOINT
      description: "OpenTelemetry endpoint for monitoring"
      required: false
      
  gitlab:
    variables:
      AI_API_KEY:
        type: "variable"
        protected: true
        masked: true
      OTEL_ENDPOINT:
        type: "variable"
        protected: false
        
  azure:
    keyvault: "dod-automation-vault"
    secrets:
      - "ai-api-key"
      - "otel-endpoint"
      - "security-scan-token"
      
  jenkins:
    credentials:
      - id: "ai-api-key"
        type: "secret-text"
      - id: "otel-endpoint"
        type: "secret-text"
```

### Security Scanning Integration
```bash
# Platform-specific security integration
uvmgr dod pipeline --provider=github --features=security,codeql,dependabot
uvmgr dod pipeline --provider=gitlab --features=security,sast,dependency-scanning
uvmgr dod pipeline --provider=azure --features=security,defender,keyvault
uvmgr dod pipeline --provider=jenkins --features=security,owasp,snyk
```

### Compliance and Auditing
```yaml
# Compliance configuration
compliance:
  audit_trail: true
  data_retention: "1 year"
  encryption: "AES-256"
  access_control: "RBAC"
  
  regulations:
    - "SOC2"
    - "GDPR"
    - "HIPAA"
    - "PCI-DSS"
    
  reporting:
    format: ["json", "pdf", "csv"]
    schedule: "weekly"
    recipients: ["security@company.com", "compliance@company.com"]
```

---

**Generated by uvmgr CI/CD Integration Team**  
*Seamless DoD automation across all major CI/CD platforms*