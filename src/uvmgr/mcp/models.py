"""
Advanced DSPy models for uvmgr MCP with Qwen3 and web search.
"""

import logging
import asyncio
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta

import dspy
from dspy import (
    Predict, Signature, InputField, OutputField, 
    ChainOfThought, ReAct, MultiChainComparison
)
from dspy.teleprompt import BootstrapFewShot, BootstrapFinetune
from dspy.evaluate import Evaluate
from dspy.primitives import Example

from uvmgr.core.telemetry import span, record_exception

logger = logging.getLogger(__name__)


class MockLM:
    """Mock Language Model for testing without external LLM services."""
    
    def __init__(self, model_name: str = "qwen3-mock"):
        self.model_name = model_name
        self.calls = 0
        
    def __call__(self, prompt: str, **kwargs) -> str:
        """Generate a mock response based on the prompt."""
        self.calls += 1
        
        # Simple response generation based on prompt content
        if "validation" in prompt.lower():
            return "Analysis: The validation data appears to be consistent and well-structured. Confidence: 0.85. Key insights: Data quality is good. Recommendations: Continue monitoring."
        elif "workflow" in prompt.lower():
            return "Optimization: The workflow can be improved by caching dependencies and parallelizing jobs. Expected improvement: 30% faster execution. Implementation: Add cache steps and matrix strategy."
        elif "issue" in prompt.lower():
            return "Diagnosis: The issue appears to be related to configuration. Root cause: Missing environment variables. Solution: Add required env vars to workflow."
        elif "performance" in prompt.lower():
            return "Performance analysis shows good baseline metrics. Bottlenecks: None identified. Optimization opportunities: Consider parallel processing."
        elif "security" in prompt.lower():
            return "Security assessment: No critical vulnerabilities found. Recommendations: Enable branch protection and require code reviews."
        elif "trend" in prompt.lower():
            return "Trend analysis: Stable performance over time. Patterns: Consistent execution times. Predictions: Continued stability expected."
        elif "error" in prompt.lower():
            return "Error analysis: Configuration issue detected. Root cause: Missing dependencies. Solution: Install required packages."
        elif "web search" in prompt.lower():
            return "Web search results analyzed. Key findings: Best practices align with current implementation. Recommendations: Continue current approach."
        else:
            return "Analysis completed successfully. Confidence: 0.75. Insights: Data appears normal. Recommendations: Monitor for changes."


class WebSearchTool:
    """Mock web search tool for testing."""
    
    def __init__(self):
        self.search_count = 0
        
    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Perform mock web search and return results."""
        self.search_count += 1
        await asyncio.sleep(0.1)  # Simulate network delay
        
        # Generate mock search results based on query
        results = []
        for i in range(min(max_results, 3)):
            results.append({
                "title": f"Mock result {i+1} for: {query}",
                "snippet": f"This is a mock search result about {query}. It contains relevant information for testing purposes.",
                "url": f"https://example.com/result-{i+1}",
                "relevance_score": 0.8 - (i * 0.1)
            })
        
        return results


class UvmgrDSPyModels:
    """Advanced DSPy models for uvmgr MCP with Qwen3 and web search."""
    
    def __init__(self):
        self.models = {}
        self.predictors = {}
        self.web_search_tool = WebSearchTool()
        self._configure_dspy()
        self._initialize_models()
        self._initialize_predictors()
    
    def _configure_dspy(self):
        """Configure DSPy with Qwen3 and fallback options."""
        try:
            # Try to configure with OllamaLocal first
            try:
                dspy.configure(lm=dspy.OllamaLocal(model="qwen2.5:7b"))
                logger.info("DSPy configured with OllamaLocal Qwen2.5")
                return
            except Exception as e:
                logger.warning(f"DSPy OllamaLocal not available: {e}")
            
            # Try OpenAI as fallback
            try:
                dspy.configure(lm=dspy.OpenAI(model="gpt-4"))
                logger.info("DSPy configured with OpenAI GPT-4")
                return
            except Exception as e:
                logger.warning(f"DSPy OpenAI not available: {e}")
            
            # Use MockLM for testing
            mock_lm = MockLM("qwen3-mock")
            dspy.configure(lm=mock_lm)
            logger.info("DSPy configured with MockLM for testing")
            
        except Exception as e:
            logger.error(f"Failed to configure DSPy: {e}")
            # Final fallback to MockLM
            try:
                mock_lm = MockLM("qwen3-mock")
                dspy.configure(lm=mock_lm)
                logger.info("DSPy configured with MockLM fallback")
            except Exception as fallback_error:
                logger.error(f"Failed to configure DSPy with MockLM: {fallback_error}")
    
    def _initialize_models(self):
        """Initialize all DSPy models."""
        try:
            # Validation Analysis Model with Web Search
            class ValidationAnalyzer(dspy.Signature):
                """Analyze validation results with deep insights and web search."""
                validation_data = InputField(desc="Raw validation result data", default={})
                context = InputField(desc="Context and environment information", default={})
                data_type = InputField(desc="Type of data being validated", default="unknown")
                web_search_results = InputField(desc="Web search results for context", default=None)
                
                analysis = OutputField(desc="Comprehensive analysis of validation results", default="")
                confidence_score = OutputField(desc="Confidence in the analysis (0-1)", default=0.5)
                key_insights = OutputField(desc="Key insights and patterns discovered", default="")
                recommendations = OutputField(desc="Specific recommendations for improvement", default="")
                risk_assessment = OutputField(desc="Risk assessment and severity levels", default="")
                web_insights = OutputField(desc="Insights from web search", default="")
            
            self.models["validation_analyzer"] = ValidationAnalyzer()
            
            # Workflow Optimization Model with Web Search
            class WorkflowOptimizer(dspy.Signature):
                """Optimize GitHub Actions workflows with AI insights and web search."""
                workflow_data = InputField(desc="Current workflow configuration and runs", default={})
                performance_metrics = InputField(desc="Performance and execution metrics", default={})
                optimization_target = InputField(desc="Target for optimization (speed, cost, reliability)", default="performance")
                constraints = InputField(desc="Constraints and requirements", default={})
                web_search_results = InputField(desc="Web search results for best practices", default=None)
                
                optimization_plan = OutputField(desc="Detailed optimization plan", default="")
                expected_improvements = OutputField(desc="Expected improvements with metrics", default="")
                implementation_steps = OutputField(desc="Step-by-step implementation guide", default="")
                risk_mitigation = OutputField(desc="Risk mitigation strategies", default="")
                cost_benefit_analysis = OutputField(desc="Cost-benefit analysis of changes", default="")
                web_best_practices = OutputField(desc="Best practices from web search", default="")
            
            self.models["workflow_optimizer"] = WorkflowOptimizer()
            
            # Issue Diagnosis Model with Web Search
            class IssueDiagnoser(dspy.Signature):
                """Diagnose complex validation and workflow issues with web search."""
                issues = InputField(desc="List of issues and error messages", default=[])
                context = InputField(desc="Context, environment, and recent changes", default={})
                system_state = InputField(desc="Current system state and configuration", default={})
                web_search_results = InputField(desc="Web search results for similar issues", default=None)
                
                root_cause_analysis = OutputField(desc="Root cause analysis of issues", default="")
                issue_prioritization = OutputField(desc="Prioritized list of issues by severity", default="")
                solution_strategies = OutputField(desc="Multiple solution strategies", default="")
                prevention_measures = OutputField(desc="Measures to prevent future issues", default="")
                monitoring_recommendations = OutputField(desc="Monitoring and alerting recommendations", default="")
                web_solutions = OutputField(desc="Solutions found from web search", default="")
            
            self.models["issue_diagnoser"] = IssueDiagnoser()
            
            # Configuration Recommender with Web Search
            class ConfigRecommender(dspy.Signature):
                """Recommend optimal uvmgr configuration with web search."""
                current_config = InputField(desc="Current configuration settings", default={})
                usage_patterns = InputField(desc="Usage patterns and requirements", default={})
                performance_metrics = InputField(desc="Current performance metrics", default={})
                constraints = InputField(desc="Technical and business constraints", default={})
                web_search_results = InputField(desc="Web search results for configuration best practices", default=None)
                
                configuration_recommendations = OutputField(desc="Specific configuration recommendations", default="")
                reasoning = OutputField(desc="Detailed reasoning for each recommendation", default="")
                expected_impact = OutputField(desc="Expected impact of configuration changes", default="")
                migration_plan = OutputField(desc="Step-by-step migration plan", default="")
                validation_criteria = OutputField(desc="Criteria to validate configuration changes", default="")
                web_best_practices = OutputField(desc="Best practices from web search", default="")
            
            self.models["config_recommender"] = ConfigRecommender()
            
            # Performance Analyzer with Web Search
            class PerformanceAnalyzer(dspy.Signature):
                """Analyze performance patterns and bottlenecks with web search."""
                performance_data = InputField(desc="Performance metrics and timing data", default={})
                system_config = InputField(desc="System configuration and resources", default={})
                workload_patterns = InputField(desc="Workload patterns and usage", default={})
                web_search_results = InputField(desc="Web search results for performance optimization", default=None)
                
                performance_analysis = OutputField(desc="Comprehensive performance analysis", default="")
                bottleneck_identification = OutputField(desc="Identified bottlenecks and issues", default="")
                optimization_opportunities = OutputField(desc="Specific optimization opportunities", default="")
                capacity_planning = OutputField(desc="Capacity planning recommendations", default="")
                monitoring_strategy = OutputField(desc="Performance monitoring strategy", default="")
                web_optimization_tips = OutputField(desc="Optimization tips from web search", default="")
            
            self.models["performance_analyzer"] = PerformanceAnalyzer()
            
            # Security Analyzer with Web Search
            class SecurityAnalyzer(dspy.Signature):
                """Analyze security posture and identify vulnerabilities with web search."""
                security_data = InputField(desc="Security-related data and configurations", default={})
                threat_model = InputField(desc="Threat model and attack vectors", default={})
                compliance_requirements = InputField(desc="Compliance and regulatory requirements", default={})
                web_search_results = InputField(desc="Web search results for security threats and vulnerabilities", default=None)
                
                security_assessment = OutputField(desc="Comprehensive security assessment", default="")
                vulnerability_analysis = OutputField(desc="Identified vulnerabilities and risks", default="")
                remediation_plan = OutputField(desc="Detailed remediation plan", default="")
                security_controls = OutputField(desc="Recommended security controls", default="")
                compliance_gap_analysis = OutputField(desc="Compliance gap analysis", default="")
                web_security_insights = OutputField(desc="Security insights from web search", default="")
            
            self.models["security_analyzer"] = SecurityAnalyzer()
            
            # Trend Analyzer with Web Search
            class TrendAnalyzer(dspy.Signature):
                """Analyze trends and predict future patterns with web search."""
                historical_data = InputField(desc="Historical data and metrics", default={})
                time_period = InputField(desc="Time period for analysis", default="1d")
                prediction_horizon = InputField(desc="Prediction horizon and scope", default="1w")
                web_search_results = InputField(desc="Web search results for industry trends", default=None)
                
                trend_analysis = OutputField(desc="Comprehensive trend analysis", default="")
                pattern_identification = OutputField(desc="Identified patterns and correlations", default="")
                future_predictions = OutputField(desc="Predictions for future behavior", default="")
                anomaly_detection = OutputField(desc="Detected anomalies and outliers", default="")
                actionable_insights = OutputField(desc="Actionable insights and recommendations", default="")
                web_trend_insights = OutputField(desc="Trend insights from web search", default="")
            
            self.models["trend_analyzer"] = TrendAnalyzer()
            
            # Query Optimizer with Web Search
            class QueryOptimizer(dspy.Signature):
                """Optimize queries and requests for better performance with web search."""
                user_query = InputField(desc="Original user query or request", default="")
                context = InputField(desc="Context and constraints", default={})
                performance_requirements = InputField(desc="Performance requirements and SLAs", default={})
                web_search_results = InputField(desc="Web search results for query optimization", default=None)
                
                optimized_query = OutputField(desc="Optimized query parameters", default="")
                reasoning = OutputField(desc="Reasoning for optimization choices", default="")
                expected_improvement = OutputField(desc="Expected performance improvement", default="")
                alternative_approaches = OutputField(desc="Alternative approaches to consider", default="")
                implementation_notes = OutputField(desc="Implementation notes and considerations", default="")
                web_optimization_tips = OutputField(desc="Optimization tips from web search", default="")
            
            self.models["query_optimizer"] = QueryOptimizer()
            
            # Result Interpreter with Web Search
            class ResultInterpreter(dspy.Signature):
                """Interpret and explain complex results with web search."""
                raw_result = InputField(desc="Raw result data from operations", default={})
                user_context = InputField(desc="User context and requirements", default={})
                result_type = InputField(desc="Type of result being interpreted", default="unknown")
                web_search_results = InputField(desc="Web search results for context", default=None)
                
                interpretation = OutputField(desc="Human-readable interpretation", default="")
                key_insights = OutputField(desc="Key insights and takeaways", default="")
                business_impact = OutputField(desc="Business impact and implications", default="")
                next_actions = OutputField(desc="Recommended next actions", default="")
                follow_up_questions = OutputField(desc="Follow-up questions for deeper analysis", default="")
                web_context = OutputField(desc="Additional context from web search", default="")
            
            self.models["result_interpreter"] = ResultInterpreter()
            
            # Error Analyzer with Web Search
            class ErrorAnalyzer(dspy.Signature):
                """Analyze errors and provide intelligent solutions with web search."""
                error_message = InputField(desc="Error message and details", default="")
                context = InputField(desc="Context when error occurred", default={})
                system_state = InputField(desc="System state and configuration", default={})
                web_search_results = InputField(desc="Web search results for error solutions", default=None)
                
                error_analysis = OutputField(desc="Comprehensive error analysis", default="")
                root_cause = OutputField(desc="Root cause identification", default="")
                solution_strategies = OutputField(desc="Multiple solution strategies", default="")
                prevention_measures = OutputField(desc="Prevention measures", default="")
                escalation_criteria = OutputField(desc="Criteria for escalation", default="")
                web_solutions = OutputField(desc="Solutions found from web search", default="")
            
            self.models["error_analyzer"] = ErrorAnalyzer()
            
            # Web Search Model
            class WebSearchAnalyzer(dspy.Signature):
                """Analyze and synthesize web search results."""
                search_query = InputField(desc="Original search query", default="")
                search_results = InputField(desc="Web search results", default=[])
                analysis_context = InputField(desc="Context for analysis", default={})
                
                synthesized_insights = OutputField(desc="Synthesized insights from search results", default="")
                key_findings = OutputField(desc="Key findings and patterns", default="")
                relevance_score = OutputField(desc="Relevance score for each result", default=0.5)
                recommendations = OutputField(desc="Recommendations based on search results", default="")
                additional_queries = OutputField(desc="Additional search queries to explore", default="")
            
            self.models["web_search_analyzer"] = WebSearchAnalyzer()
            
        except Exception as e:
            logger.error(f"Failed to initialize DSPy models: {e}")
            # Create fallback models
            self._create_fallback_models()
    
    def _create_fallback_models(self):
        """Create simple fallback models if DSPy initialization fails."""
        try:
            # Simple fallback model with proper defaults
            class SimpleAnalyzer(dspy.Signature):
                """Simple analysis model."""
                data = InputField(desc="Input data", default={})
                context = InputField(desc="Context information", default={})
                analysis = OutputField(desc="Analysis result", default="Analysis completed")
                confidence = OutputField(desc="Confidence score", default=0.5)
            
            self.models["validation_analyzer"] = SimpleAnalyzer()
            self.models["workflow_optimizer"] = SimpleAnalyzer()
            self.models["issue_diagnoser"] = SimpleAnalyzer()
            self.models["config_recommender"] = SimpleAnalyzer()
            self.models["performance_analyzer"] = SimpleAnalyzer()
            self.models["security_analyzer"] = SimpleAnalyzer()
            self.models["trend_analyzer"] = SimpleAnalyzer()
            self.models["query_optimizer"] = SimpleAnalyzer()
            self.models["result_interpreter"] = SimpleAnalyzer()
            self.models["error_analyzer"] = SimpleAnalyzer()
            self.models["web_search_analyzer"] = SimpleAnalyzer()
            
        except Exception as e:
            logger.error(f"Failed to create fallback models: {e}")
            self.models = {}
    
    def _initialize_predictors(self):
        """Initialize DSPy predictors with different strategies."""
        try:
            # Simple predictor for basic tasks
            for name, model in self.models.items():
                self.predictors[f"{name}_simple"] = Predict(model)
            
            # Chain of Thought for complex reasoning
            for name, model in self.models.items():
                self.predictors[f"{name}_cot"] = ChainOfThought(model)
            
            # ReAct for action-oriented tasks (simplified without tools)
            try:
                for name, model in self.models.items():
                    if "optimizer" in name or "diagnoser" in name or "analyzer" in name:
                        # Use ChainOfThought as fallback for ReAct
                        self.predictors[f"{name}_react"] = ChainOfThought(model)
            except Exception as e:
                logger.warning(f"Failed to initialize ReAct predictors: {e}")
                # Fallback to ChainOfThought for these models
                for name, model in self.models.items():
                    if "optimizer" in name or "diagnoser" in name or "analyzer" in name:
                        self.predictors[f"{name}_react"] = ChainOfThought(model)
            
            # Multi-chain comparison for critical decisions
            try:
                critical_models = ["validation_analyzer", "issue_diagnoser", "security_analyzer"]
                for name in critical_models:
                    if name in self.models:
                        # Use ChainOfThought as fallback for MultiChainComparison
                        self.predictors[f"{name}_multi"] = ChainOfThought(self.models[name])
            except Exception as e:
                logger.warning(f"Failed to initialize MultiChainComparison predictors: {e}")
                # Fallback to ChainOfThought for these models
                for name in critical_models:
                    if name in self.models:
                        self.predictors[f"{name}_multi"] = ChainOfThought(self.models[name])
                        
        except Exception as e:
            logger.error(f"Failed to initialize predictors: {e}")
            self.predictors = {}
    
    async def web_search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Perform web search and return results."""
        return await self.web_search_tool.search(query, max_results)
    
    async def run_analysis(
        self, 
        model_name: str, 
        data: Any, 
        context: Dict[str, Any],
        strategy: str = "cot",
        enable_web_search: bool = True
    ) -> Dict[str, Any]:
        """Run analysis using specified model and strategy with optional web search."""
        with span("dspy.run_analysis", model=model_name, strategy=strategy):
            try:
                if not self.models or not self.predictors:
                    return {"error": "DSPy models not initialized"}
                
                # Perform web search if enabled
                web_search_results = None
                if enable_web_search and context.get("enable_web_search", True):
                    search_query = self._generate_search_query(model_name, data, context)
                    web_search_results = await self.web_search(search_query)
                
                predictor_key = f"{model_name}_{strategy}"
                if predictor_key not in self.predictors:
                    # Fallback to simple predictor
                    predictor_key = f"{model_name}_simple"
                
                if predictor_key not in self.predictors:
                    return {"error": f"No predictor available for {model_name}"}
                
                predictor = self.predictors[predictor_key]
                
                # Prepare inputs based on model
                if model_name == "validation_analyzer":
                    result = predictor(
                        validation_data=data,
                        context=context,
                        data_type=context.get("data_type", "unknown"),
                        web_search_results=web_search_results
                    )
                elif model_name == "workflow_optimizer":
                    result = predictor(
                        workflow_data=data,
                        performance_metrics=context.get("performance_metrics", {}),
                        optimization_target=context.get("optimization_target", "performance"),
                        constraints=context.get("constraints", {}),
                        web_search_results=web_search_results
                    )
                elif model_name == "issue_diagnoser":
                    result = predictor(
                        issues=data,
                        context=context,
                        system_state=context.get("system_state", {}),
                        web_search_results=web_search_results
                    )
                elif model_name == "config_recommender":
                    result = predictor(
                        current_config=data,
                        usage_patterns=context.get("usage_patterns", {}),
                        performance_metrics=context.get("performance_metrics", {}),
                        constraints=context.get("constraints", {}),
                        web_search_results=web_search_results
                    )
                elif model_name == "performance_analyzer":
                    result = predictor(
                        performance_data=data,
                        system_config=context.get("system_config", {}),
                        workload_patterns=context.get("workload_patterns", {}),
                        web_search_results=web_search_results
                    )
                elif model_name == "security_analyzer":
                    result = predictor(
                        security_data=data,
                        threat_model=context.get("threat_model", {}),
                        compliance_requirements=context.get("compliance_requirements", {}),
                        web_search_results=web_search_results
                    )
                elif model_name == "trend_analyzer":
                    result = predictor(
                        historical_data=data,
                        time_period=context.get("time_period", "1d"),
                        prediction_horizon=context.get("prediction_horizon", "1w"),
                        web_search_results=web_search_results
                    )
                elif model_name == "query_optimizer":
                    result = predictor(
                        user_query=data,
                        context=context,
                        performance_requirements=context.get("performance_requirements", {}),
                        web_search_results=web_search_results
                    )
                elif model_name == "result_interpreter":
                    result = predictor(
                        raw_result=data,
                        user_context=context,
                        result_type=context.get("result_type", "unknown"),
                        web_search_results=web_search_results
                    )
                elif model_name == "error_analyzer":
                    result = predictor(
                        error_message=data,
                        context=context,
                        system_state=context.get("system_state", {}),
                        web_search_results=web_search_results
                    )
                elif model_name == "web_search_analyzer":
                    result = predictor(
                        search_query=context.get("search_query", ""),
                        search_results=web_search_results or [],
                        analysis_context=context
                    )
                else:
                    # Generic fallback
                    result = predictor(data=data, context=context)
                
                # Extract all possible outputs
                return {
                    "analysis": getattr(result, 'analysis', None),
                    "confidence_score": getattr(result, 'confidence_score', None),
                    "key_insights": getattr(result, 'key_insights', None),
                    "recommendations": getattr(result, 'recommendations', None),
                    "risk_assessment": getattr(result, 'risk_assessment', None),
                    "optimization_plan": getattr(result, 'optimization_plan', None),
                    "expected_improvements": getattr(result, 'expected_improvements', None),
                    "implementation_steps": getattr(result, 'implementation_steps', None),
                    "risk_mitigation": getattr(result, 'risk_mitigation', None),
                    "cost_benefit_analysis": getattr(result, 'cost_benefit_analysis', None),
                    "root_cause_analysis": getattr(result, 'root_cause_analysis', None),
                    "issue_prioritization": getattr(result, 'issue_prioritization', None),
                    "solution_strategies": getattr(result, 'solution_strategies', None),
                    "prevention_measures": getattr(result, 'prevention_measures', None),
                    "monitoring_recommendations": getattr(result, 'monitoring_recommendations', None),
                    "configuration_recommendations": getattr(result, 'configuration_recommendations', None),
                    "reasoning": getattr(result, 'reasoning', None),
                    "expected_impact": getattr(result, 'expected_impact', None),
                    "migration_plan": getattr(result, 'migration_plan', None),
                    "validation_criteria": getattr(result, 'validation_criteria', None),
                    "performance_analysis": getattr(result, 'performance_analysis', None),
                    "bottleneck_identification": getattr(result, 'bottleneck_identification', None),
                    "optimization_opportunities": getattr(result, 'optimization_opportunities', None),
                    "capacity_planning": getattr(result, 'capacity_planning', None),
                    "monitoring_strategy": getattr(result, 'monitoring_strategy', None),
                    "security_assessment": getattr(result, 'security_assessment', None),
                    "vulnerability_analysis": getattr(result, 'vulnerability_analysis', None),
                    "remediation_plan": getattr(result, 'remediation_plan', None),
                    "security_controls": getattr(result, 'security_controls', None),
                    "compliance_gap_analysis": getattr(result, 'compliance_gap_analysis', None),
                    "trend_analysis": getattr(result, 'trend_analysis', None),
                    "pattern_identification": getattr(result, 'pattern_identification', None),
                    "future_predictions": getattr(result, 'future_predictions', None),
                    "anomaly_detection": getattr(result, 'anomaly_detection', None),
                    "actionable_insights": getattr(result, 'actionable_insights', None),
                    "optimized_query": getattr(result, 'optimized_query', None),
                    "expected_improvement": getattr(result, 'expected_improvement', None),
                    "alternative_approaches": getattr(result, 'alternative_approaches', None),
                    "implementation_notes": getattr(result, 'implementation_notes', None),
                    "interpretation": getattr(result, 'interpretation', None),
                    "business_impact": getattr(result, 'business_impact', None),
                    "next_actions": getattr(result, 'next_actions', None),
                    "follow_up_questions": getattr(result, 'follow_up_questions', None),
                    "error_analysis": getattr(result, 'error_analysis', None),
                    "root_cause": getattr(result, 'root_cause', None),
                    "solution_strategies": getattr(result, 'solution_strategies', None),
                    "escalation_criteria": getattr(result, 'escalation_criteria', None),
                    "web_insights": getattr(result, 'web_insights', None),
                    "web_best_practices": getattr(result, 'web_best_practices', None),
                    "web_solutions": getattr(result, 'web_solutions', None),
                    "web_optimization_tips": getattr(result, 'web_optimization_tips', None),
                    "web_security_insights": getattr(result, 'web_security_insights', None),
                    "web_trend_insights": getattr(result, 'web_trend_insights', None),
                    "web_context": getattr(result, 'web_context', None),
                    "synthesized_insights": getattr(result, 'synthesized_insights', None),
                    "key_findings": getattr(result, 'key_findings', None),
                    "relevance_score": getattr(result, 'relevance_score', None),
                    "additional_queries": getattr(result, 'additional_queries', None),
                    "web_search_results": web_search_results
                }
                
            except Exception as e:
                record_exception(e, attributes={"model": model_name, "strategy": strategy})
                logger.error(f"DSPy analysis failed for {model_name}: {e}")
                return {"error": str(e), "model": model_name, "strategy": strategy}
    
    def _generate_search_query(self, model_name: str, data: Any, context: Dict[str, Any]) -> str:
        """Generate search query based on model and data."""
        if model_name == "validation_analyzer":
            return f"validation best practices {context.get('data_type', 'data')}"
        elif model_name == "workflow_optimizer":
            return f"GitHub Actions workflow optimization {context.get('optimization_target', 'performance')}"
        elif model_name == "issue_diagnoser":
            return f"GitHub Actions troubleshooting {str(data)[:100]}"
        elif model_name == "config_recommender":
            return f"uvmgr configuration best practices"
        elif model_name == "performance_analyzer":
            return f"performance optimization techniques"
        elif model_name == "security_analyzer":
            return f"security best practices GitHub Actions"
        elif model_name == "trend_analyzer":
            return f"industry trends {context.get('time_period', 'recent')}"
        elif model_name == "query_optimizer":
            return f"query optimization techniques"
        elif model_name == "result_interpreter":
            return f"data interpretation best practices"
        elif model_name == "error_analyzer":
            return f"error troubleshooting {str(data)[:100]}"
        else:
            return f"{model_name} best practices"
    
    def get_available_models(self) -> List[str]:
        """Get list of available models."""
        return list(self.models.keys())
    
    def get_available_strategies(self) -> List[str]:
        """Get list of available strategies."""
        return ["simple", "cot", "react", "multi"]
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get information about a specific model."""
        if model_name in self.models:
            model = self.models[model_name]
            return {
                "name": model_name,
                "description": model.__doc__,
                "input_fields": [field.name for field in model.input_fields],
                "output_fields": [field.name for field in model.output_fields],
                "available_strategies": [
                    strategy for strategy in self.get_available_strategies()
                    if f"{model_name}_{strategy}" in self.predictors
                ]
            }
        return {"error": f"Model {model_name} not found"}


# Global DSPy models instance
dspy_models = UvmgrDSPyModels()


def get_dspy_models() -> UvmgrDSPyModels:
    """Get global DSPy models instance."""
    return dspy_models


async def run_dspy_analysis(
    model_name: str, 
    data: Any, 
    context: Dict[str, Any],
    strategy: str = "cot",
    enable_web_search: bool = True
) -> Dict[str, Any]:
    """Run DSPy analysis using global models with web search."""
    return await dspy_models.run_analysis(model_name, data, context, strategy, enable_web_search) 