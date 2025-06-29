# 🔧 DoD Automation Troubleshooting & Advanced Configuration

## Table of Contents
- [Common Issues](#common-issues)
- [Advanced Configuration](#advanced-configuration)
- [Performance Optimization](#performance-optimization)
- [Security Configuration](#security-configuration)
- [AI Integration Issues](#ai-integration-issues)
- [CI/CD Platform Issues](#cicd-platform-issues)
- [Debugging Tools](#debugging-tools)
- [Expert-Level Configuration](#expert-level-configuration)

## Common Issues

### Issue 1: Exoskeleton Initialization Fails

#### Symptoms
```bash
$ uvmgr dod exoskeleton --template=standard
Error: Exoskeleton already exists. Use --force to overwrite.
```

#### Solutions

**Solution A: Force Overwrite**
```bash
# Force clean initialization
uvmgr dod exoskeleton --template=standard --force

# Verify initialization
uvmgr dod status --detailed
```

**Solution B: Clean Manual Reset**
```bash
# Remove existing exoskeleton
rm -rf .uvmgr/exoskeleton

# Reinitialize fresh
uvmgr dod exoskeleton --template=enterprise

# Verify structure
ls -la .uvmgr/exoskeleton/
```

**Solution C: Debug Mode Investigation**
```bash
# Enable debug logging
export UVMGR_DEBUG=1
export UVMGR_OTEL_DEBUG=1

# Run with verbose output
uvmgr dod exoskeleton --template=standard --verbose

# Check logs
cat .uvmgr/telemetry/logs/dod-automation.log
```

#### Prevention
```yaml
# .uvmgr/exoskeleton/config.yaml - Robust configuration
exoskeleton:
  version: "1.0.0"
  auto_cleanup: true          # Automatic cleanup on errors
  backup_on_overwrite: true   # Backup existing config
  validation_strict: false    # Allow flexible validation
```

### Issue 2: DoD Validation Criteria Not Found

#### Symptoms
```bash
$ uvmgr dod validate --criteria=custom_testing
Error: Unknown criteria: custom_testing
Available criteria: testing, security, devops, code_quality, documentation, performance, compliance
```

#### Solutions

**Solution A: Use Standard Criteria**
```bash
# List available criteria
uvmgr dod validate --list-criteria

# Use standard criteria
uvmgr dod validate --criteria=testing,security,devops
```

**Solution B: Register Custom Criteria**
```python
# .uvmgr/extensions/custom_criteria.py
from uvmgr.extensions.criteria import CriteriaExtension, CriteriaValidator

class CustomTestingValidator(CriteriaValidator):
    def validate(self, project_path: Path) -> CriteriaResult:
        # Your custom validation logic
        score = self.run_custom_tests(project_path)
        return CriteriaResult(
            criterion="custom_testing",
            passed=score >= 80,
            score=score,
            weight=0.15,
            execution_time=time.time() - start_time
        )

# Register the custom criterion
CriteriaExtension.register(
    name="custom_testing",
    validator=CustomTestingValidator(),
    weight=0.15,
    priority="important"
)
```

**Solution C: Configuration-Based Criteria**
```yaml
# .uvmgr/exoskeleton/config.yaml
automation:
  custom_criteria:
    custom_testing:
      weight: 0.15
      priority: "important"
      validator: "path.to.custom.validator"
      config:
        test_command: "pytest tests/custom/"
        coverage_threshold: 85
        timeout: 300
```

### Issue 3: Automation Pipeline Timeout

#### Symptoms
```bash
$ uvmgr dod complete --env=production
Timeout: Automation execution exceeded 1800 seconds
```

#### Solutions

**Solution A: Increase Timeout**
```bash
# Increase global timeout
uvmgr dod complete --env=production --timeout=3600

# Environment-specific timeout
export UVMGR_AUTOMATION_TIMEOUT=3600
uvmgr dod complete --env=production
```

**Solution B: Optimize Execution Strategy**
```bash
# Use parallel execution
uvmgr dod complete --env=production --parallel

# Focus on critical criteria only
uvmgr dod complete --criteria=testing,security --parallel

# Skip optional criteria for speed
uvmgr dod complete --env=production --skip-optional
```

**Solution C: Advanced Timeout Configuration**
```yaml
# .uvmgr/exoskeleton/config.yaml
automation:
  timeouts:
    global: 3600              # 1 hour global timeout
    per_criterion:
      testing: 900            # 15 minutes for testing
      security: 1200          # 20 minutes for security
      devops: 600             # 10 minutes for devops
      code_quality: 300       # 5 minutes for code quality
    
  optimization:
    parallel_limit: 4         # Max parallel processes
    early_termination: true   # Stop on sufficient value
    cache_enabled: true       # Use result caching
```

### Issue 4: AI Integration Failures

#### Symptoms
```bash
$ uvmgr dod complete --ai-assist
Error: AI service unavailable. API key validation failed.
```

#### Solutions

**Solution A: Verify API Configuration**
```bash
# Check API key configuration
echo $UVMGR_AI_API_KEY

# Test AI connectivity
uvmgr ai test-connection

# Use fallback provider
uvmgr dod complete --ai-provider=anthropic --ai-assist
```

**Solution B: Configure Multiple AI Providers**
```yaml
# .uvmgr/ai/config.yaml
ai_providers:
  primary:
    provider: "openai"
    api_key: "${OPENAI_API_KEY}"
    model: "gpt-4-turbo"
    timeout: 30
    
  fallback:
    provider: "anthropic"
    api_key: "${ANTHROPIC_API_KEY}"
    model: "claude-3-sonnet"
    timeout: 30
    
  local:
    provider: "ollama"
    endpoint: "http://localhost:11434"
    model: "llama2"
    timeout: 60

failure_handling:
  retry_attempts: 3
  fallback_enabled: true
  graceful_degradation: true  # Continue without AI if all fail
```

**Solution C: AI-Free Operation**
```bash
# Disable AI assistance entirely
uvmgr dod complete --no-ai

# Use cached AI results only
uvmgr dod complete --ai-cache-only

# Manual mode with user prompts
uvmgr dod complete --manual-decisions
```

### Issue 5: Permission and Access Issues

#### Symptoms
```bash
$ uvmgr dod pipeline --provider=github
Error: Permission denied. Cannot write to .github/workflows/
```

#### Solutions

**Solution A: Fix File Permissions**
```bash
# Fix directory permissions
chmod -R 755 .github/workflows/

# Fix ownership if needed
sudo chown -R $USER:$USER .github/

# Retry operation
uvmgr dod pipeline --provider=github
```

**Solution B: Alternative Output Location**
```bash
# Use custom output directory
uvmgr dod pipeline --provider=github --output-path=./pipelines/

# Generate without writing
uvmgr dod pipeline --provider=github --dry-run --output=stdout
```

**Solution C: Container/Sandbox Mode**
```bash
# Run in Docker container
docker run -v $(pwd):/workspace uvmgr/dod:latest \
  uvmgr dod complete --env=development

# Use temporary directory
export UVMGR_TEMP_DIR=/tmp/uvmgr-workspace
uvmgr dod complete --workspace=$UVMGR_TEMP_DIR
```

## Advanced Configuration

### Multi-Project Configuration

```yaml
# .uvmgr/workspace.yaml - Multi-project workspace configuration
workspace:
  projects:
    - name: "backend-api"
      path: "./services/api"
      template: "enterprise"
      criteria_weights:
        security: 0.35      # Higher security for API
        testing: 0.25
        devops: 0.20
        
    - name: "frontend-app"
      path: "./apps/web"
      template: "standard"
      criteria_weights:
        testing: 0.30       # Higher testing for frontend
        code_quality: 0.25
        performance: 0.20
        
    - name: "ml-models"
      path: "./ml/"
      template: "ai-native"
      criteria_weights:
        testing: 0.40       # Critical for ML reliability
        security: 0.25
        performance: 0.20

  coordination:
    execution_order: ["backend-api", "frontend-app", "ml-models"]
    parallel_execution: false
    shared_cache: true
    cross_project_dependencies: true
```

### Environment-Specific Configuration

```yaml
# .uvmgr/environments/production.yaml
environment:
  name: "production"
  type: "production"
  
  automation:
    criteria_weights:
      security: 0.40        # Maximum security for production
      devops: 0.25          # Critical deployment automation
      compliance: 0.20      # Regulatory requirements
      testing: 0.15         # Final validation
    
    execution_strategy:
      parallel: false       # Sequential for production safety
      timeout: 7200         # 2 hours for production validation
      retry_attempts: 2
      manual_approval: true # Require manual approval
    
    integrations:
      monitoring:
        provider: "datadog"
        api_key: "${DATADOG_API_KEY}"
        alerts: true
        
      security:
        provider: "snyk"
        api_token: "${SNYK_TOKEN}"
        severity_threshold: "high"
        
      compliance:
        frameworks: ["SOC2", "GDPR", "HIPAA"]
        audit_trail: true
        retention_days: 2555  # 7 years
```

### Custom Weaver Forge Templates

```yaml
# .uvmgr/templates/fintech-template.yaml
template:
  name: "fintech-enterprise"
  description: "Financial services enterprise template"
  version: "2.0.0"
  
  automation:
    criteria_weights:
      security: 0.45        # Highest priority for fintech
      compliance: 0.25      # Regulatory requirements
      testing: 0.20         # Quality assurance
      devops: 0.10          # Controlled deployment
    
    security_requirements:
      encryption: "AES-256"
      authentication: "multi-factor"
      audit_logging: "comprehensive"
      vulnerability_scanning: "continuous"
      penetration_testing: "quarterly"
    
    compliance_frameworks:
      - "PCI-DSS"
      - "SOC2"
      - "GDPR"
      - "SOX"
      - "BASEL-III"
    
    testing_strategy:
      unit_coverage: 95
      integration_coverage: 90
      e2e_coverage: 85
      performance_benchmarks: true
      chaos_engineering: true
```

## Performance Optimization

### Caching Strategy

```yaml
# .uvmgr/performance/caching.yaml
caching:
  enabled: true
  provider: "redis"      # redis, file, memory
  
  redis_config:
    host: "localhost"
    port: 6379
    db: 0
    password: "${REDIS_PASSWORD}"
    ssl: true
    
  cache_policies:
    criteria_results:
      ttl: 3600          # 1 hour
      invalidation: "content-based"
      compression: true
      
    ai_responses:
      ttl: 86400         # 24 hours
      invalidation: "manual"
      encryption: true
      
    dependency_analysis:
      ttl: 7200          # 2 hours
      invalidation: "file-based"
      
  optimization:
    prefetch_enabled: true
    background_refresh: true
    cache_warming: true
    hit_rate_target: 0.85
```

### Parallel Execution Optimization

```python
# .uvmgr/performance/parallel_config.py
from uvmgr.core.parallel import ParallelExecutionEngine

class OptimizedParallelConfig:
    """Advanced parallel execution configuration."""
    
    def __init__(self):
        self.cpu_cores = os.cpu_count()
        self.memory_gb = psutil.virtual_memory().total // (1024**3)
        
    def get_optimal_config(self, criteria: List[str]) -> ParallelConfig:
        """Calculate optimal parallel execution configuration."""
        
        # Resource-aware optimization
        if self.memory_gb >= 16 and self.cpu_cores >= 8:
            # High-resource environment
            return ParallelConfig(
                max_workers=min(self.cpu_cores, len(criteria)),
                memory_per_worker=2048,  # 2GB per worker
                io_intensive_limit=4,
                cpu_intensive_limit=self.cpu_cores - 2
            )
        elif self.memory_gb >= 8 and self.cpu_cores >= 4:
            # Medium-resource environment
            return ParallelConfig(
                max_workers=min(4, len(criteria)),
                memory_per_worker=1024,  # 1GB per worker
                io_intensive_limit=2,
                cpu_intensive_limit=2
            )
        else:
            # Low-resource environment - prefer sequential
            return ParallelConfig(
                max_workers=1,
                memory_per_worker=512,   # 512MB
                io_intensive_limit=1,
                cpu_intensive_limit=1
            )
```

### Resource Monitoring

```yaml
# .uvmgr/monitoring/resources.yaml
monitoring:
  enabled: true
  interval: 30  # seconds
  
  thresholds:
    cpu_usage: 80     # percent
    memory_usage: 85  # percent
    disk_usage: 90    # percent
    
  actions:
    high_cpu:
      - "reduce_parallel_workers"
      - "enable_caching"
      
    high_memory:
      - "trigger_garbage_collection"
      - "reduce_batch_size"
      
    high_disk:
      - "cleanup_temp_files" 
      - "compress_logs"
      
  alerting:
    webhook: "${MONITORING_WEBHOOK}"
    channels: ["slack", "email"]
    severity_levels: ["warning", "critical"]
```

## Security Configuration

### Advanced Security Settings

```yaml
# .uvmgr/security/advanced.yaml
security:
  encryption:
    at_rest:
      algorithm: "AES-256-GCM"
      key_rotation: 90  # days
      key_source: "aws-kms"  # aws-kms, azure-keyvault, hashicorp-vault
      
    in_transit:
      tls_version: "1.3"
      cipher_suites: ["TLS_AES_256_GCM_SHA384"]
      certificate_validation: true
      
  authentication:
    methods: ["api-key", "oauth2", "mutual-tls"]
    session_timeout: 3600  # seconds
    max_failed_attempts: 3
    lockout_duration: 1800  # seconds
    
  authorization:
    model: "rbac"  # rbac, abac, acl
    roles:
      - name: "dod-admin"
        permissions: ["read", "write", "execute", "configure"]
      - name: "dod-operator"
        permissions: ["read", "execute"]
      - name: "dod-viewer"
        permissions: ["read"]
        
  auditing:
    enabled: true
    log_level: "detailed"
    retention_days: 2555  # 7 years
    tamper_protection: true
    real_time_monitoring: true
    
  vulnerability_management:
    scanning:
      frequency: "continuous"
      tools: ["snyk", "bandit", "safety", "semgrep"]
      severity_threshold: "medium"
      
    patching:
      auto_update: false
      approval_required: true
      testing_required: true
      rollback_enabled: true
```

### Zero-Trust Configuration

```yaml
# .uvmgr/security/zero-trust.yaml
zero_trust:
  principles:
    verify_explicitly: true
    least_privilege: true
    assume_breach: true
    
  network:
    micro_segmentation: true
    traffic_encryption: true
    network_monitoring: true
    
  identity:
    continuous_verification: true
    context_aware_access: true
    privileged_access_management: true
    
  devices:
    device_compliance: true
    certificate_based_auth: true
    health_attestation: true
    
  data:
    classification: "automatic"
    loss_prevention: true
    rights_management: true
    
  applications:
    secure_development: true
    runtime_protection: true
    api_security: true
    
  analytics:
    user_behavior: true
    threat_detection: true
    risk_scoring: true
    automated_response: true
```

## Expert-Level Configuration

### Custom DSPy Model Integration

```python
# .uvmgr/ai/custom_models.py
import dspy
from uvmgr.extensions.ai import AIModelExtension

class ExpertDoDAnalysisModel(dspy.Module):
    """Expert-level DoD analysis with specialized reasoning."""
    
    def __init__(self):
        super().__init__()
        
        # Multi-step reasoning chain
        self.project_analyzer = dspy.ChainOfThought(
            "project_context: str, criteria: List[str] -> "
            "risk_assessment: Dict[str, float], optimization_strategy: str, "
            "execution_plan: List[str], confidence: float"
        )
        
        self.failure_predictor = dspy.Predict(
            "historical_data: str, current_metrics: Dict -> "
            "failure_probability: float, risk_factors: List[str], "
            "prevention_actions: List[str]"
        )
        
        self.optimization_engine = dspy.ChainOfThought(
            "current_performance: Dict, constraints: Dict -> "
            "optimized_config: Dict, expected_improvement: float, "
            "implementation_steps: List[str]"
        )
    
    def forward(self, project_context: str, criteria: List[str], 
                historical_data: str = None):
        """Advanced DoD analysis with expert reasoning."""
        
        # Step 1: Comprehensive project analysis
        analysis = self.project_analyzer(
            project_context=project_context,
            criteria=criteria
        )
        
        # Step 2: Failure prediction if historical data available
        prediction = None
        if historical_data:
            prediction = self.failure_predictor(
                historical_data=historical_data,
                current_metrics=analysis.risk_assessment
            )
        
        # Step 3: Optimization recommendations
        optimization = self.optimization_engine(
            current_performance=analysis.risk_assessment,
            constraints={"time_limit": 1800, "resource_limit": 0.8}
        )
        
        return dspy.Prediction(
            analysis=analysis,
            prediction=prediction,
            optimization=optimization,
            overall_confidence=min(analysis.confidence, 
                                 optimization.expected_improvement)
        )

# Register the expert model
AIModelExtension.register(
    name="expert_dod_analyzer",
    model=ExpertDoDAnalysisModel(),
    use_cases=["advanced_analysis", "failure_prediction", "optimization"]
)
```

### Custom Telemetry Processors

```python
# .uvmgr/telemetry/processors.py
from uvmgr.core.telemetry import TelemetryProcessor
from opentelemetry import trace, metrics

class CustomDoDTelemetryProcessor(TelemetryProcessor):
    """Custom telemetry processing for DoD automation."""
    
    def __init__(self):
        super().__init__()
        self.tracer = trace.get_tracer("dod.custom")
        self.meter = metrics.get_meter("dod.custom")
        
        # Custom metrics
        self.efficiency_gauge = self.meter.create_gauge(
            "dod.efficiency_ratio",
            description="80/20 efficiency ratio"
        )
        
        self.value_counter = self.meter.create_counter(
            "dod.value_delivered",
            description="Total value delivered"
        )
        
    def process_automation_result(self, result: AutomationResult):
        """Process automation results with custom logic."""
        
        with self.tracer.start_as_current_span("custom.result_processing") as span:
            # Calculate 80/20 efficiency
            critical_score = result.get_critical_score()
            total_time = result.execution_time
            efficiency_ratio = critical_score / (total_time / 3600)  # per hour
            
            # Record custom metrics
            self.efficiency_gauge.set(efficiency_ratio)
            self.value_counter.add(critical_score)
            
            # Add custom span attributes
            span.set_attributes({
                "dod.efficiency_ratio": efficiency_ratio,
                "dod.critical_score": critical_score,
                "dod.meets_8020_target": efficiency_ratio >= 3.5
            })
            
            # Custom business logic
            if efficiency_ratio < 2.0:
                self.trigger_optimization_alert(result)
            elif efficiency_ratio > 5.0:
                self.record_best_practice(result)
    
    def trigger_optimization_alert(self, result: AutomationResult):
        """Trigger alert for low efficiency."""
        # Custom alerting logic
        pass
        
    def record_best_practice(self, result: AutomationResult):
        """Record high-efficiency configuration as best practice."""
        # Learning system integration
        pass
```

### Advanced Workflow Orchestration

```yaml
# .uvmgr/workflows/expert-orchestration.yaml
orchestration:
  engine: "spiffworkflow"  # spiffworkflow, temporal, airflow
  
  workflows:
    expert_dod_pipeline:
      description: "Expert-level DoD automation with adaptive execution"
      
      tasks:
        - id: "context_analysis"
          type: "ai_analysis"
          model: "expert_dod_analyzer"
          inputs: ["project_context", "historical_data"]
          outputs: ["risk_assessment", "execution_strategy"]
          
        - id: "adaptive_planning"
          type: "decision_tree"
          depends_on: ["context_analysis"]
          rules:
            - condition: "risk_assessment.complexity > 0.8"
              action: "enable_comprehensive_validation"
            - condition: "risk_assessment.security_risk > 0.7"
              action: "prioritize_security_criteria"
            - condition: "execution_strategy.parallel_recommended"
              action: "enable_parallel_execution"
              
        - id: "dynamic_execution"
          type: "conditional_parallel"
          depends_on: ["adaptive_planning"]
          branches:
            high_risk:
              condition: "risk_assessment.overall > 0.8"
              tasks: ["security_deep_scan", "compliance_audit", "penetration_test"]
            medium_risk:
              condition: "risk_assessment.overall > 0.5"
              tasks: ["standard_validation", "security_scan"]
            low_risk:
              condition: "risk_assessment.overall <= 0.5"
              tasks: ["minimal_validation"]
              
        - id: "continuous_optimization"
          type: "feedback_loop"
          depends_on: ["dynamic_execution"]
          actions:
            - "update_execution_strategy"
            - "refine_risk_model"
            - "optimize_resource_allocation"
            
  monitoring:
    real_time: true
    alerting: true
    auto_scaling: true
    failure_recovery: true
```

---

**Generated by uvmgr DoD Troubleshooting & Configuration Team**  
*Expert-level support for DoD automation mastery*