"""
Cost Analysis Operations
========================

This module provides intelligent cost analysis and optimization for development
workflows with AGI-driven insights and comprehensive resource tracking.

The system can:
- Analyze development resource consumption and costs
- Track CI/CD pipeline costs and optimization opportunities
- Provide intelligent cost forecasting and budgeting
- Optimize resource allocation based on usage patterns
- Generate cost reports and recommendations

Key Features:
- Multi-dimensional cost analysis (time, compute, storage, services)
- AGI-driven cost optimization recommendations
- Real-time cost tracking and alerting
- Integration with cloud providers and CI/CD systems
- Comprehensive cost reporting and visualization
"""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from uvmgr.core.agi_reasoning import observe_with_agi_reasoning
from uvmgr.core.agi_memory import get_persistent_memory
from uvmgr.core.semconv import CliAttributes
from uvmgr.core.telemetry import span, metric_counter, metric_histogram


class CostCategory(Enum):
    """Categories of costs to track."""
    COMPUTE = "compute"
    STORAGE = "storage"
    NETWORK = "network"
    CI_CD = "ci_cd"
    CLOUD_SERVICES = "cloud_services"
    DEVELOPER_TIME = "developer_time"
    TOOLING = "tooling"
    INFRASTRUCTURE = "infrastructure"
    TESTING = "testing"
    DEPLOYMENT = "deployment"


class CostUnit(Enum):
    """Units for cost measurement."""
    USD = "usd"
    CREDITS = "credits"
    CPU_HOURS = "cpu_hours"
    GB_HOURS = "gb_hours"
    REQUESTS = "requests"
    MINUTES = "minutes"
    EXECUTIONS = "executions"


class OptimizationPriority(Enum):
    """Priority levels for cost optimizations."""
    CRITICAL = "critical"  # High impact, easy to implement
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MONITORING = "monitoring"  # Just monitor for now


@dataclass
class CostEntry:
    """Individual cost entry."""
    id: str
    category: CostCategory
    description: str
    amount: float
    unit: CostUnit
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: str = "manual"
    project: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class CostBudget:
    """Budget definition for cost tracking."""
    id: str
    name: str
    category: Optional[CostCategory]
    period: str  # "monthly", "weekly", "daily"
    limit: float
    unit: CostUnit
    current_spend: float = 0.0
    alert_threshold: float = 0.8  # Alert at 80% of budget
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OptimizationRecommendation:
    """Cost optimization recommendation."""
    id: str
    title: str
    description: str
    category: CostCategory
    priority: OptimizationPriority
    potential_savings: float
    unit: CostUnit
    implementation_effort: str  # "low", "medium", "high"
    impact_description: str
    action_items: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CostReport:
    """Comprehensive cost report."""
    period_start: datetime
    period_end: datetime
    total_cost: float
    unit: CostUnit
    category_breakdown: Dict[CostCategory, float]
    trend_analysis: Dict[str, Any]
    budget_status: List[Dict[str, Any]]
    optimization_opportunities: List[OptimizationRecommendation]
    insights: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


class IntelligentCostAnalyzer:
    """
    Intelligent cost analysis and optimization system.
    
    Provides advanced cost management capabilities:
    - Multi-dimensional cost tracking and analysis
    - AGI-driven optimization recommendations
    - Predictive cost modeling and forecasting
    - Budget management and alerting
    - Integration with development workflows
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.cost_entries: List[CostEntry] = []
        self.budgets: Dict[str, CostBudget] = {}
        self.optimization_history: List[OptimizationRecommendation] = []
        
        # Cost tracking configuration
        self.default_currency = CostUnit.USD
        self.developer_hourly_rate = 75.0  # Default developer cost per hour
        self.enable_agi_optimization = True
        self.cost_storage_file = self.project_root / ".uvmgr" / "cost_data.json"
        
        # Cost calculation baselines
        self.cost_baselines = {
            CostCategory.CI_CD: {"github_actions_minute": 0.008},  # $0.008 per minute
            CostCategory.COMPUTE: {"aws_t3_micro_hour": 0.0104},  # $0.0104 per hour
            CostCategory.STORAGE: {"aws_s3_gb_month": 0.023},     # $0.023 per GB/month
            CostCategory.CLOUD_SERVICES: {"aws_lambda_request": 0.0000002},  # $0.0000002 per request
        }
        
        # Load existing data
        asyncio.create_task(self._load_cost_data())
    
    async def _load_cost_data(self):
        """Load existing cost data from storage."""
        try:
            if self.cost_storage_file.exists():
                with open(self.cost_storage_file) as f:
                    data = json.load(f)
                
                # Load cost entries
                for entry_data in data.get("cost_entries", []):
                    entry = CostEntry(
                        id=entry_data["id"],
                        category=CostCategory(entry_data["category"]),
                        description=entry_data["description"],
                        amount=entry_data["amount"],
                        unit=CostUnit(entry_data["unit"]),
                        timestamp=entry_data["timestamp"],
                        metadata=entry_data.get("metadata", {}),
                        source=entry_data.get("source", "manual"),
                        project=entry_data.get("project"),
                        tags=entry_data.get("tags", [])
                    )
                    self.cost_entries.append(entry)
                
                # Load budgets
                for budget_data in data.get("budgets", []):
                    budget = CostBudget(
                        id=budget_data["id"],
                        name=budget_data["name"],
                        category=CostCategory(budget_data["category"]) if budget_data.get("category") else None,
                        period=budget_data["period"],
                        limit=budget_data["limit"],
                        unit=CostUnit(budget_data["unit"]),
                        current_spend=budget_data.get("current_spend", 0.0),
                        alert_threshold=budget_data.get("alert_threshold", 0.8),
                        metadata=budget_data.get("metadata", {})
                    )
                    self.budgets[budget.id] = budget
                    
        except Exception as e:
            print(f"⚠️  Error loading cost data: {e}")
    
    async def _save_cost_data(self):
        """Save cost data to storage."""
        try:
            self.cost_storage_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "cost_entries": [
                    {
                        "id": entry.id,
                        "category": entry.category.value,
                        "description": entry.description,
                        "amount": entry.amount,
                        "unit": entry.unit.value,
                        "timestamp": entry.timestamp,
                        "metadata": entry.metadata,
                        "source": entry.source,
                        "project": entry.project,
                        "tags": entry.tags
                    }
                    for entry in self.cost_entries
                ],
                "budgets": [
                    {
                        "id": budget.id,
                        "name": budget.name,
                        "category": budget.category.value if budget.category else None,
                        "period": budget.period,
                        "limit": budget.limit,
                        "unit": budget.unit.value,
                        "current_spend": budget.current_spend,
                        "alert_threshold": budget.alert_threshold,
                        "metadata": budget.metadata
                    }
                    for budget in self.budgets.values()
                ]
            }
            
            with open(self.cost_storage_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"⚠️  Error saving cost data: {e}")
    
    async def track_cost(self, 
                        category: CostCategory,
                        description: str,
                        amount: float,
                        unit: CostUnit = None,
                        metadata: Dict[str, Any] = None,
                        source: str = "manual",
                        project: str = None,
                        tags: List[str] = None) -> str:
        """Track a cost entry."""
        
        with span("cost.track_cost", category=category.value, amount=amount):
            
            entry_id = f"cost_{int(time.time())}_{len(self.cost_entries)}"
            
            entry = CostEntry(
                id=entry_id,
                category=category,
                description=description,
                amount=amount,
                unit=unit or self.default_currency,
                timestamp=time.time(),
                metadata=metadata or {},
                source=source,
                project=project,
                tags=tags or []
            )
            
            self.cost_entries.append(entry)
            
            # Update budgets
            await self._update_budget_spend(entry)
            
            # Save data
            await self._save_cost_data()
            
            # Observe cost tracking
            observe_with_agi_reasoning(
                attributes={
                    CliAttributes.COMMAND: "cost_track",
                    "category": category.value,
                    "amount": str(amount),
                    "unit": entry.unit.value
                },
                context={"cost_analysis": True, "tracking": True}
            )
            
            metric_counter("cost.entries_tracked")(1)
            metric_histogram(f"cost.amount.{category.value}")(amount)
            
            return entry_id
    
    async def track_ci_cd_cost(self, 
                              pipeline_name: str,
                              duration_minutes: float,
                              platform: str = "github_actions") -> str:
        """Track CI/CD pipeline cost."""
        
        # Calculate cost based on platform
        cost_per_minute = self.cost_baselines[CostCategory.CI_CD].get(
            f"{platform}_minute", 0.008
        )
        
        total_cost = duration_minutes * cost_per_minute
        
        return await self.track_cost(
            category=CostCategory.CI_CD,
            description=f"CI/CD pipeline: {pipeline_name}",
            amount=total_cost,
            unit=CostUnit.USD,
            metadata={
                "pipeline_name": pipeline_name,
                "duration_minutes": duration_minutes,
                "platform": platform,
                "cost_per_minute": cost_per_minute
            },
            source="automated",
            tags=["ci_cd", platform]
        )
    
    async def track_developer_time(self,
                                  activity: str,
                                  duration_hours: float,
                                  hourly_rate: float = None) -> str:
        """Track developer time as cost."""
        
        rate = hourly_rate or self.developer_hourly_rate
        total_cost = duration_hours * rate
        
        return await self.track_cost(
            category=CostCategory.DEVELOPER_TIME,
            description=f"Developer time: {activity}",
            amount=total_cost,
            unit=CostUnit.USD,
            metadata={
                "activity": activity,
                "duration_hours": duration_hours,
                "hourly_rate": rate
            },
            source="automated",
            tags=["developer_time"]
        )
    
    async def track_cloud_service_cost(self,
                                     service_name: str,
                                     usage_amount: float,
                                     usage_unit: str,
                                     cost_per_unit: float) -> str:
        """Track cloud service cost."""
        
        total_cost = usage_amount * cost_per_unit
        
        return await self.track_cost(
            category=CostCategory.CLOUD_SERVICES,
            description=f"Cloud service: {service_name}",
            amount=total_cost,
            unit=CostUnit.USD,
            metadata={
                "service_name": service_name,
                "usage_amount": usage_amount,
                "usage_unit": usage_unit,
                "cost_per_unit": cost_per_unit
            },
            source="automated",
            tags=["cloud", service_name]
        )
    
    async def create_budget(self,
                           name: str,
                           category: Optional[CostCategory],
                           period: str,
                           limit: float,
                           unit: CostUnit = None,
                           alert_threshold: float = 0.8) -> str:
        """Create a cost budget."""
        
        budget_id = f"budget_{int(time.time())}"
        
        budget = CostBudget(
            id=budget_id,
            name=name,
            category=category,
            period=period,
            limit=limit,
            unit=unit or self.default_currency,
            alert_threshold=alert_threshold
        )
        
        self.budgets[budget_id] = budget
        await self._save_cost_data()
        
        # Observe budget creation
        observe_with_agi_reasoning(
            attributes={
                CliAttributes.COMMAND: "cost_create_budget",
                "budget_name": name,
                "category": category.value if category else "all",
                "limit": str(limit)
            },
            context={"cost_analysis": True, "budget_management": True}
        )
        
        metric_counter("cost.budgets_created")(1)
        
        return budget_id
    
    async def _update_budget_spend(self, cost_entry: CostEntry):
        """Update budget spend with new cost entry."""
        
        current_time = time.time()
        
        for budget in self.budgets.values():
            # Check if entry applies to this budget
            if budget.category and budget.category != cost_entry.category:
                continue
            
            # Check if entry is within budget period
            period_start = self._get_period_start(budget.period, current_time)
            if cost_entry.timestamp < period_start:
                continue
            
            # Convert cost to budget unit if needed
            converted_amount = await self._convert_cost_units(
                cost_entry.amount, cost_entry.unit, budget.unit
            )
            
            budget.current_spend += converted_amount
            
            # Check for budget alerts
            if budget.current_spend >= budget.limit * budget.alert_threshold:
                await self._send_budget_alert(budget, cost_entry)
    
    async def _send_budget_alert(self, budget: CostBudget, triggering_entry: CostEntry):
        """Send budget alert."""
        
        alert_data = {
            "budget_name": budget.name,
            "current_spend": budget.current_spend,
            "limit": budget.limit,
            "percentage": (budget.current_spend / budget.limit) * 100,
            "triggering_entry": triggering_entry.description
        }
        
        # Store alert in memory for AGI learning
        memory = get_persistent_memory()
        memory.store_knowledge(
            content=f"Budget alert: {budget.name} at {alert_data['percentage']:.1f}% of limit",
            knowledge_type="budget_alert",
            metadata=alert_data
        )
        
        # Observe alert
        observe_with_agi_reasoning(
            attributes={
                CliAttributes.COMMAND: "cost_budget_alert",
                "budget_name": budget.name,
                "percentage": str(alert_data['percentage'])
            },
            context={"cost_analysis": True, "budget_alert": True}
        )
        
        metric_counter("cost.budget_alerts")(1)
        
        print(f"🚨 Budget Alert: {budget.name} is at {alert_data['percentage']:.1f}% of limit")
    
    def _get_period_start(self, period: str, current_time: float) -> float:
        """Get the start time for a budget period."""
        current_dt = datetime.fromtimestamp(current_time)
        
        if period == "daily":
            start_dt = current_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "weekly":
            days_since_monday = current_dt.weekday()
            start_dt = current_dt - timedelta(days=days_since_monday)
            start_dt = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "monthly":
            start_dt = current_dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            # Default to daily
            start_dt = current_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        
        return start_dt.timestamp()
    
    async def _convert_cost_units(self, amount: float, from_unit: CostUnit, to_unit: CostUnit) -> float:
        """Convert between cost units."""
        
        if from_unit == to_unit:
            return amount
        
        # Simple conversion - in practice you'd have more sophisticated conversion rates
        conversion_rates = {
            (CostUnit.CPU_HOURS, CostUnit.USD): 0.10,  # $0.10 per CPU hour
            (CostUnit.GB_HOURS, CostUnit.USD): 0.01,   # $0.01 per GB hour
            (CostUnit.REQUESTS, CostUnit.USD): 0.0001, # $0.0001 per request
            (CostUnit.MINUTES, CostUnit.USD): 0.008,   # $0.008 per minute
        }
        
        rate = conversion_rates.get((from_unit, to_unit))
        if rate:
            return amount * rate
        
        # If no conversion available, return original amount
        return amount
    
    async def generate_cost_report(self, 
                                  period_days: int = 30,
                                  include_optimization: bool = True) -> CostReport:
        """Generate comprehensive cost report."""
        
        with span("cost.generate_report", period_days=period_days):
            
            end_time = time.time()
            start_time = end_time - (period_days * 86400)
            
            # Filter entries for period
            period_entries = [
                entry for entry in self.cost_entries
                if start_time <= entry.timestamp <= end_time
            ]
            
            # Calculate totals
            total_cost = sum(entry.amount for entry in period_entries)
            
            # Category breakdown
            category_breakdown = {}
            for category in CostCategory:
                category_cost = sum(
                    entry.amount for entry in period_entries
                    if entry.category == category
                )
                if category_cost > 0:
                    category_breakdown[category] = category_cost
            
            # Trend analysis
            trend_analysis = await self._analyze_cost_trends(period_entries)
            
            # Budget status
            budget_status = []
            for budget in self.budgets.values():
                status = {
                    "budget_name": budget.name,
                    "current_spend": budget.current_spend,
                    "limit": budget.limit,
                    "percentage": (budget.current_spend / budget.limit) * 100,
                    "status": "ok" if budget.current_spend < budget.limit * budget.alert_threshold else "warning"
                }
                budget_status.append(status)
            
            # Generate optimization recommendations
            optimization_opportunities = []
            if include_optimization:
                optimization_opportunities = await self._generate_optimization_recommendations(period_entries)
            
            # Generate insights
            insights = await self._generate_cost_insights(period_entries, category_breakdown)
            
            report = CostReport(
                period_start=datetime.fromtimestamp(start_time),
                period_end=datetime.fromtimestamp(end_time),
                total_cost=total_cost,
                unit=self.default_currency,
                category_breakdown=category_breakdown,
                trend_analysis=trend_analysis,
                budget_status=budget_status,
                optimization_opportunities=optimization_opportunities,
                insights=insights,
                metadata={
                    "period_days": period_days,
                    "entries_analyzed": len(period_entries),
                    "generation_time": time.time()
                }
            )
            
            # Observe report generation
            observe_with_agi_reasoning(
                attributes={
                    CliAttributes.COMMAND: "cost_generate_report",
                    "period_days": str(period_days),
                    "total_cost": str(total_cost),
                    "entries_analyzed": str(len(period_entries))
                },
                context={"cost_analysis": True, "reporting": True}
            )
            
            metric_counter("cost.reports_generated")(1)
            metric_histogram("cost.report_generation_time")(time.time() - end_time)
            
            return report
    
    async def _analyze_cost_trends(self, entries: List[CostEntry]) -> Dict[str, Any]:
        """Analyze cost trends."""
        
        if len(entries) < 2:
            return {"trend": "insufficient_data"}
        
        # Sort by timestamp
        sorted_entries = sorted(entries, key=lambda e: e.timestamp)
        
        # Split into first and second half for comparison
        mid_point = len(sorted_entries) // 2
        first_half = sorted_entries[:mid_point]
        second_half = sorted_entries[mid_point:]
        
        first_half_cost = sum(e.amount for e in first_half)
        second_half_cost = sum(e.amount for e in second_half)
        
        if first_half_cost == 0:
            trend_percentage = 0
        else:
            trend_percentage = ((second_half_cost - first_half_cost) / first_half_cost) * 100
        
        trend_direction = "increasing" if trend_percentage > 5 else "decreasing" if trend_percentage < -5 else "stable"
        
        return {
            "trend": trend_direction,
            "trend_percentage": trend_percentage,
            "first_half_cost": first_half_cost,
            "second_half_cost": second_half_cost
        }
    
    async def _generate_optimization_recommendations(self, entries: List[CostEntry]) -> List[OptimizationRecommendation]:
        """Generate AGI-driven optimization recommendations."""
        
        recommendations = []
        
        # Analyze by category
        category_costs = {}
        for entry in entries:
            category = entry.category
            if category not in category_costs:
                category_costs[category] = []
            category_costs[category].append(entry)
        
        # Check for high CI/CD costs
        if CostCategory.CI_CD in category_costs:
            ci_cd_cost = sum(e.amount for e in category_costs[CostCategory.CI_CD])
            total_cost = sum(e.amount for e in entries)
            
            if ci_cd_cost > total_cost * 0.3:  # More than 30% of total cost
                recommendations.append(OptimizationRecommendation(
                    id="optimize_ci_cd",
                    title="Optimize CI/CD Pipeline Costs",
                    description="CI/CD costs represent a significant portion of total expenses",
                    category=CostCategory.CI_CD,
                    priority=OptimizationPriority.HIGH,
                    potential_savings=ci_cd_cost * 0.3,  # Estimate 30% savings
                    unit=self.default_currency,
                    implementation_effort="medium",
                    impact_description="Reduce CI/CD runtime through optimization",
                    action_items=[
                        "Analyze slow CI/CD steps",
                        "Implement parallel job execution",
                        "Cache dependencies and build artifacts",
                        "Use matrix builds efficiently"
                    ]
                ))
        
        # Check for high developer time costs
        if CostCategory.DEVELOPER_TIME in category_costs:
            dev_entries = category_costs[CostCategory.DEVELOPER_TIME]
            manual_tasks = [e for e in dev_entries if "manual" in e.description.lower()]
            
            if len(manual_tasks) > len(dev_entries) * 0.4:  # More than 40% manual tasks
                manual_cost = sum(e.amount for e in manual_tasks)
                
                recommendations.append(OptimizationRecommendation(
                    id="automate_manual_tasks",
                    title="Automate Manual Development Tasks",
                    description="High proportion of manual tasks detected",
                    category=CostCategory.DEVELOPER_TIME,
                    priority=OptimizationPriority.CRITICAL,
                    potential_savings=manual_cost * 0.6,  # Estimate 60% savings
                    unit=self.default_currency,
                    implementation_effort="medium",
                    impact_description="Reduce manual effort through automation",
                    action_items=[
                        "Identify repetitive manual tasks",
                        "Implement automated scripts",
                        "Use development task automation tools",
                        "Create workflow templates"
                    ]
                ))
        
        return recommendations
    
    async def _generate_cost_insights(self, 
                                    entries: List[CostEntry], 
                                    category_breakdown: Dict[CostCategory, float]) -> List[str]:
        """Generate insights about costs."""
        
        insights = []
        
        if not entries:
            insights.append("No cost data available for analysis")
            return insights
        
        total_cost = sum(entry.amount for entry in entries)
        
        # Most expensive category
        if category_breakdown:
            top_category = max(category_breakdown.items(), key=lambda x: x[1])
            percentage = (top_category[1] / total_cost) * 100
            insights.append(f"Highest cost category: {top_category[0].value} ({percentage:.1f}% of total)")
        
        # Cost frequency analysis
        daily_avg = total_cost / max(1, len(set(int(e.timestamp / 86400) for e in entries)))
        insights.append(f"Average daily cost: ${daily_avg:.2f}")
        
        # Source analysis
        sources = {}
        for entry in entries:
            sources[entry.source] = sources.get(entry.source, 0) + entry.amount
        
        if "automated" in sources and "manual" in sources:
            auto_percentage = (sources["automated"] / total_cost) * 100
            insights.append(f"Automated cost tracking: {auto_percentage:.1f}% of total costs")
        
        # AGI-driven insights using memory
        memory = get_persistent_memory()
        similar_patterns = memory.retrieve_similar("cost optimization", n_results=3)
        
        if similar_patterns:
            insights.append("Historical patterns suggest potential optimization opportunities")
        
        return insights
    
    def get_cost_stats(self) -> Dict[str, Any]:
        """Get comprehensive cost statistics."""
        
        total_entries = len(self.cost_entries)
        total_cost = sum(entry.amount for entry in self.cost_entries)
        
        if total_entries == 0:
            return {
                "total_entries": 0,
                "total_cost": 0.0,
                "categories": {},
                "budgets": len(self.budgets),
                "cost_currency": self.default_currency.value
            }
        
        # Category distribution
        categories = {}
        for entry in self.cost_entries:
            category = entry.category.value
            categories[category] = categories.get(category, 0) + entry.amount
        
        # Recent activity (last 7 days)
        recent_cutoff = time.time() - (7 * 86400)
        recent_entries = [e for e in self.cost_entries if e.timestamp > recent_cutoff]
        recent_cost = sum(e.amount for e in recent_entries)
        
        return {
            "total_entries": total_entries,
            "total_cost": total_cost,
            "cost_currency": self.default_currency.value,
            "categories": categories,
            "budgets": len(self.budgets),
            "recent_entries_7d": len(recent_entries),
            "recent_cost_7d": recent_cost,
            "agi_optimization_enabled": self.enable_agi_optimization,
            "developer_hourly_rate": self.developer_hourly_rate
        }


# Global cost analyzer instance
_cost_analyzer = None

def get_cost_analyzer(project_root: Optional[Path] = None) -> IntelligentCostAnalyzer:
    """Get the global cost analyzer."""
    global _cost_analyzer
    if _cost_analyzer is None:
        _cost_analyzer = IntelligentCostAnalyzer(project_root)
    return _cost_analyzer

async def track_cost_entry(category: CostCategory, 
                          description: str,
                          amount: float,
                          **kwargs) -> str:
    """Track a cost entry."""
    analyzer = get_cost_analyzer()
    return await analyzer.track_cost(category, description, amount, **kwargs)

async def generate_cost_report(period_days: int = 30) -> CostReport:
    """Generate a cost report."""
    analyzer = get_cost_analyzer()
    return await analyzer.generate_cost_report(period_days)

def get_cost_status() -> Dict[str, Any]:
    """Get cost analysis system status."""
    analyzer = get_cost_analyzer()
    return analyzer.get_cost_stats()