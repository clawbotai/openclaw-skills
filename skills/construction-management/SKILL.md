---
slug: "construction-management"
display_name: "Master Construction Management"
description: "Comprehensive construction project management: capacity planning, resource optimization, incident reporting, safety management, project controls, and lean construction practices."
---

# Master Construction Management

## Overview

End-to-end construction management system integrating capacity planning, safety/incident management, project controls, and modern best practices. Covers the full project lifecycle from pursuit through closeout with emphasis on safety culture, resource optimization, and data-driven decision making.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    MASTER CONSTRUCTION MANAGEMENT                       │
├──────────────────┬──────────────────┬───────────────────────────────────┤
│  CAPACITY &      │  SAFETY &        │  PROJECT CONTROLS &              │
│  RESOURCES       │  INCIDENTS       │  LEAN CONSTRUCTION               │
│  ─────────────   │  ──────────────  │  ────────────────────            │
│  • Demand        │  • Reporting     │  • Critical Path (CPM)           │
│    Forecasting   │  • Investigation │  • Earned Value (EVM)            │
│  • Gap Analysis  │  • Root Cause    │  • Last Planner System           │
│  • Go/No-Go      │  • 5 Whys        │  • Resource Leveling             │
│  • Staffing      │  • Fishbone      │  • Look-Ahead Planning           │
│    Ratios        │  • Near-Miss     │  • PPC Tracking                  │
│  • Pipeline Mgmt │  • OSHA Metrics  │  • Predictive Analytics          │
│  • Resource      │  • TRIR/DART     │  • Equipment Management          │
│    Leveling      │  • Toolbox Talks │  • Subcontractor Mgmt            │
│  • Smoothing     │  • JHA/JSA       │  • BIM/Digital Twin              │
│                  │  • Leading/      │                                   │
│                  │    Lagging KPIs  │                                   │
└──────────────────┴──────────────────┴───────────────────────────────────┘
```

## Incident Pyramid

```
                    △
                   /│\        Fatality (1)
                  / │ \
                 /  │  \      Serious Injury (10)
                /   │   \
               /    │    \    Minor Injury (30)
              /     │     \
             /      │      \  Near Miss (300)
            /       │       \
           /        │        \ Unsafe Acts (3000)
          ──────────┴──────────
```

> "Near-miss reporting prevents 90% of future serious incidents"

---

## Technical Implementation

```python
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import statistics
import json
import math

# ═══════════════════════════════════════════════════════════════════
# ENUMERATIONS
# ═══════════════════════════════════════════════════════════════════

class ResourceRole(Enum):
    PROJECT_MANAGER = "project_manager"
    SUPERINTENDENT = "superintendent"
    PROJECT_ENGINEER = "project_engineer"
    ESTIMATOR = "estimator"
    SCHEDULER = "scheduler"
    SAFETY_MANAGER = "safety_manager"
    QC_MANAGER = "qc_manager"
    ADMIN = "admin"
    BIM_MANAGER = "bim_manager"
    LEAN_COORDINATOR = "lean_coordinator"

class ProjectPhase(Enum):
    PURSUIT = "pursuit"
    PRECONSTRUCTION = "preconstruction"
    CONSTRUCTION = "construction"
    CLOSEOUT = "closeout"

class OpportunityStatus(Enum):
    IDENTIFIED = "identified"
    PURSUING = "pursuing"
    BID_SUBMITTED = "bid_submitted"
    NEGOTIATING = "negotiating"
    WON = "won"
    LOST = "lost"

class IncidentType(Enum):
    NEAR_MISS = "near_miss"
    FIRST_AID = "first_aid"
    MEDICAL_TREATMENT = "medical_treatment"
    LOST_TIME = "lost_time"
    FATALITY = "fatality"
    PROPERTY_DAMAGE = "property_damage"
    ENVIRONMENTAL = "environmental"

class IncidentCategory(Enum):
    FALL = "fall"
    STRUCK_BY = "struck_by"
    CAUGHT_IN = "caught_in"
    ELECTROCUTION = "electrocution"
    VEHICLE = "vehicle"
    MATERIAL_HANDLING = "material_handling"
    TOOL_EQUIPMENT = "tool_equipment"
    SLIP_TRIP = "slip_trip"
    FIRE = "fire"
    CHEMICAL = "chemical"
    OTHER = "other"

class InvestigationStatus(Enum):
    REPORTED = "reported"
    UNDER_INVESTIGATION = "under_investigation"
    ROOT_CAUSE_IDENTIFIED = "root_cause_identified"
    CORRECTIVE_ACTIONS_ASSIGNED = "corrective_actions_assigned"
    IN_REMEDIATION = "in_remediation"
    CLOSED = "closed"

class EquipmentStatus(Enum):
    AVAILABLE = "available"
    IN_USE = "in_use"
    MAINTENANCE = "maintenance"
    OUT_OF_SERVICE = "out_of_service"

# ═══════════════════════════════════════════════════════════════════
# DATA MODELS
# ═══════════════════════════════════════════════════════════════════

@dataclass
class StaffMember:
    id: str
    name: str
    role: ResourceRole
    capacity: float = 1.0  # FTE
    current_assignment: str = ""
    availability_date: datetime = None
    skills: List[str] = field(default_factory=list)
    max_project_value: float = 0
    certifications: List[str] = field(default_factory=list)

@dataclass
class ProjectDemand:
    project_id: str
    project_name: str
    value: float
    phase: ProjectPhase
    start_date: datetime
    end_date: datetime
    probability: float = 1.0
    resource_needs: Dict[ResourceRole, float] = field(default_factory=dict)

@dataclass
class CapacityGap:
    role: ResourceRole
    period_start: datetime
    period_end: datetime
    demand: float
    capacity: float
    gap: float
    severity: str

@dataclass
class CapacityForecast:
    forecast_date: datetime
    horizon_months: int
    total_demand_fte: float
    total_capacity_fte: float
    utilization_pct: float
    gaps: List[CapacityGap]
    recommendations: List[str]

@dataclass
class Person:
    name: str
    company: str
    role: str
    contact: str
    years_experience: int = 0

@dataclass
class CorrectiveAction:
    id: str
    description: str
    assigned_to: str
    due_date: datetime
    status: str = "open"
    completed_date: Optional[datetime] = None
    verification_notes: str = ""
    priority: str = "medium"

@dataclass
class Incident:
    id: str
    incident_type: IncidentType
    category: IncidentCategory
    date_time: datetime
    location: str
    project_id: str
    project_name: str
    description: str
    immediate_actions: str
    injured_person: Optional[Person] = None
    witnesses: List[Person] = field(default_factory=list)
    reported_by: str = ""
    status: InvestigationStatus = InvestigationStatus.REPORTED
    root_causes: List[str] = field(default_factory=list)
    contributing_factors: List[str] = field(default_factory=list)
    corrective_actions: List[CorrectiveAction] = field(default_factory=list)
    photos: List[str] = field(default_factory=list)
    weather_conditions: str = ""
    equipment_involved: List[str] = field(default_factory=list)
    days_lost: int = 0
    property_damage_cost: float = 0.0
    osha_recordable: bool = False

@dataclass
class ToolboxTalk:
    id: str
    date: datetime
    topic: str
    presenter: str
    project_id: str
    attendees: List[str] = field(default_factory=list)
    duration_minutes: int = 15
    notes: str = ""
    related_jha: str = ""

@dataclass
class JHA:
    """Job Hazard Analysis / Job Safety Analysis."""
    id: str
    job_description: str
    project_id: str
    created_date: datetime
    steps: List[Dict] = field(default_factory=list)
    approved_by: str = ""
    review_date: Optional[datetime] = None

@dataclass
class Equipment:
    id: str
    name: str
    type: str
    status: EquipmentStatus = EquipmentStatus.AVAILABLE
    assigned_project: str = ""
    last_inspection: Optional[datetime] = None
    next_maintenance: Optional[datetime] = None
    daily_rate: float = 0.0
    certifications_required: List[str] = field(default_factory=list)

@dataclass
class Subcontractor:
    id: str
    name: str
    trade: str
    prequalified: bool = False
    safety_rating: float = 0.0
    active_projects: List[str] = field(default_factory=list)
    contract_value: float = 0.0
    performance_score: float = 0.0

# ═══════════════════════════════════════════════════════════════════
# EVM — EARNED VALUE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════

@dataclass
class EVMSnapshot:
    date: datetime
    bac: float       # Budget at Completion
    pv: float        # Planned Value
    ev: float        # Earned Value
    ac: float        # Actual Cost

    @property
    def sv(self) -> float:
        return self.ev - self.pv

    @property
    def cv(self) -> float:
        return self.ev - self.ac

    @property
    def spi(self) -> float:
        return self.ev / self.pv if self.pv else 0

    @property
    def cpi(self) -> float:
        return self.ev / self.ac if self.ac else 0

    @property
    def eac(self) -> float:
        return self.bac / self.cpi if self.cpi else 0

    @property
    def etc(self) -> float:
        return self.eac - self.ac

    @property
    def vac(self) -> float:
        return self.bac - self.eac

    @property
    def tcpi(self) -> float:
        denom = self.bac - self.ac
        return (self.bac - self.ev) / denom if denom else 0

    def summary(self) -> Dict:
        return {
            "date": self.date.isoformat(),
            "SV": self.sv, "CV": self.cv,
            "SPI": round(self.spi, 3), "CPI": round(self.cpi, 3),
            "EAC": round(self.eac, 2), "ETC": round(self.etc, 2),
            "VAC": round(self.vac, 2), "TCPI": round(self.tcpi, 3),
            "status": "on_track" if self.spi >= 0.95 and self.cpi >= 0.95
                      else "at_risk" if self.spi >= 0.85 and self.cpi >= 0.85
                      else "critical"
        }

# ═══════════════════════════════════════════════════════════════════
# CPM — CRITICAL PATH METHOD
# ═══════════════════════════════════════════════════════════════════

@dataclass
class Activity:
    id: str
    name: str
    duration: int
    predecessors: List[str] = field(default_factory=list)
    resources: Dict[ResourceRole, float] = field(default_factory=dict)
    es: int = 0
    ef: int = 0
    ls: int = 0
    lf: int = 0

    @property
    def total_float(self) -> int:
        return self.ls - self.es

    @property
    def is_critical(self) -> bool:
        return self.total_float == 0


class CPMScheduler:
    """Critical Path Method scheduler."""

    def __init__(self):
        self.activities: Dict[str, Activity] = {}

    def add_activity(self, id: str, name: str, duration: int,
                     predecessors: List[str] = None,
                     resources: Dict[ResourceRole, float] = None) -> Activity:
        act = Activity(id=id, name=name, duration=duration,
                       predecessors=predecessors or [],
                       resources=resources or {})
        self.activities[id] = act
        return act

    def calculate(self) -> List[Activity]:
        order = self._topo_sort()
        # Forward pass
        for act_id in order:
            act = self.activities[act_id]
            if not act.predecessors:
                act.es = 0
            else:
                act.es = max(self.activities[p].ef for p in act.predecessors)
            act.ef = act.es + act.duration
        project_end = max(a.ef for a in self.activities.values())
        # Backward pass
        for act_id in reversed(order):
            act = self.activities[act_id]
            successors = [a for a in self.activities.values() if act_id in a.predecessors]
            if not successors:
                act.lf = project_end
            else:
                act.lf = min(s.ls for s in successors)
            act.ls = act.lf - act.duration
        return [a for a in self.activities.values() if a.is_critical]

    def _topo_sort(self) -> List[str]:
        visited = set()
        order = []
        def visit(act_id):
            if act_id in visited:
                return
            visited.add(act_id)
            for pred in self.activities[act_id].predecessors:
                visit(pred)
            order.append(act_id)
        for act_id in self.activities:
            visit(act_id)
        return order

    def get_project_duration(self) -> int:
        self.calculate()
        return max(a.ef for a in self.activities.values())

    def resource_histogram(self) -> Dict[int, Dict[ResourceRole, float]]:
        self.calculate()
        histogram = {}
        for act in self.activities.values():
            for day in range(act.es, act.ef):
                if day not in histogram:
                    histogram[day] = {r: 0.0 for r in ResourceRole}
                for role, qty in act.resources.items():
                    histogram[day][role] += qty
        return histogram

    def resource_level(self) -> None:
        self.calculate()
        non_critical = sorted(
            [a for a in self.activities.values() if not a.is_critical],
            key=lambda a: a.total_float
        )
        for act in non_critical:
            act.es = act.ls
            act.ef = act.lf

# ═══════════════════════════════════════════════════════════════════
# LAST PLANNER SYSTEM (Lean Construction)
# ═══════════════════════════════════════════════════════════════════

@dataclass
class WeeklyPlan:
    week_start: datetime
    project_id: str
    planned_tasks: List[Dict] = field(default_factory=list)

    @property
    def ppc(self) -> float:
        if not self.planned_tasks:
            return 0.0
        completed = sum(1 for t in self.planned_tasks if t.get("completed", False))
        return (completed / len(self.planned_tasks)) * 100

    @property
    def variance_reasons(self) -> Dict[str, int]:
        reasons = {}
        for t in self.planned_tasks:
            if not t.get("completed") and t.get("reason_incomplete"):
                r = t["reason_incomplete"]
                reasons[r] = reasons.get(r, 0) + 1
        return reasons


class LastPlannerSystem:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.weekly_plans: List[WeeklyPlan] = []
        self.constraints_log: List[Dict] = []
        self.lookahead_weeks: int = 6

    def create_weekly_plan(self, week_start: datetime, tasks: List[Dict]) -> WeeklyPlan:
        plan = WeeklyPlan(week_start=week_start, project_id=self.project_id, planned_tasks=tasks)
        self.weekly_plans.append(plan)
        return plan

    def record_completion(self, week_start: datetime, results: List[Dict]) -> WeeklyPlan:
        plan = next((p for p in self.weekly_plans if p.week_start == week_start), None)
        if not plan:
            raise ValueError("Weekly plan not found")
        for result in results:
            for task in plan.planned_tasks:
                if task["task"] == result["task"]:
                    task["completed"] = result.get("completed", False)
                    task["reason_incomplete"] = result.get("reason_incomplete", "")
        return plan

    def log_constraint(self, task: str, constraint_type: str,
                       description: str, owner: str, needed_by: datetime) -> Dict:
        entry = {
            "task": task, "type": constraint_type,
            "description": description, "owner": owner,
            "needed_by": needed_by.isoformat(),
            "logged": datetime.now().isoformat(), "resolved": False
        }
        self.constraints_log.append(entry)
        return entry

    def ppc_trend(self) -> List[Dict]:
        return [{"week": p.week_start.isoformat(), "ppc": p.ppc}
                for p in sorted(self.weekly_plans, key=lambda p: p.week_start)]

    def top_variance_reasons(self, n: int = 5) -> Dict[str, int]:
        agg = {}
        for plan in self.weekly_plans:
            for reason, count in plan.variance_reasons.items():
                agg[reason] = agg.get(reason, 0) + count
        return dict(sorted(agg.items(), key=lambda x: -x[1])[:n])

# ═══════════════════════════════════════════════════════════════════
# CAPACITY PLANNER
# ═══════════════════════════════════════════════════════════════════

class CapacityPlanner:
    STAFFING_RATIOS = {
        ResourceRole.PROJECT_MANAGER: 20_000_000,
        ResourceRole.SUPERINTENDENT: 10_000_000,
        ResourceRole.PROJECT_ENGINEER: 15_000_000,
        ResourceRole.ESTIMATOR: 50_000_000,
        ResourceRole.SCHEDULER: 30_000_000,
        ResourceRole.SAFETY_MANAGER: 25_000_000,
    }

    PHASE_FACTORS = {
        ProjectPhase.PURSUIT: {"est": 1.5, "pro": 0.3},
        ProjectPhase.PRECONSTRUCTION: {"pro": 0.7, "sch": 0.5},
        ProjectPhase.CONSTRUCTION: {"pro": 1.0, "sup": 1.0, "saf": 1.0},
        ProjectPhase.CLOSEOUT: {"pro": 0.5, "adm": 1.0},
    }

    def __init__(self, organization_name: str):
        self.organization_name = organization_name
        self.staff: Dict[str, StaffMember] = {}
        self.projects: Dict[str, ProjectDemand] = {}
        self.pipeline: Dict[str, ProjectDemand] = {}

    def add_staff(self, id, name, role, capacity=1.0, current_assignment="",
                  availability_date=None, max_project_value=0):
        member = StaffMember(id=id, name=name, role=role, capacity=capacity,
            current_assignment=current_assignment,
            availability_date=availability_date or datetime.now(),
            max_project_value=max_project_value)
        self.staff[id] = member
        return member

    def add_active_project(self, id, name, value, phase, start_date, end_date):
        needs = self._calculate_resource_needs(value, phase)
        project = ProjectDemand(project_id=id, project_name=name, value=value,
            phase=phase, start_date=start_date, end_date=end_date,
            probability=1.0, resource_needs=needs)
        self.projects[id] = project
        return project

    def add_pipeline_opportunity(self, id, name, value, win_probability,
                                 expected_start, duration_months):
        needs = self._calculate_resource_needs(value, ProjectPhase.CONSTRUCTION)
        opp = ProjectDemand(project_id=id, project_name=name, value=value,
            phase=ProjectPhase.PURSUIT, start_date=expected_start,
            end_date=expected_start + timedelta(days=duration_months * 30),
            probability=win_probability, resource_needs=needs)
        self.pipeline[id] = opp
        return opp

    def _calculate_resource_needs(self, value, phase):
        needs = {}
        for role, ratio in self.STAFFING_RATIOS.items():
            base_need = value / ratio
            phase_key = role.value[:3]
            factor = self.PHASE_FACTORS.get(phase, {}).get(phase_key, 1.0)
            needs[role] = base_need * factor
        return needs

    def get_current_capacity(self):
        capacity = {role: 0.0 for role in ResourceRole}
        for member in self.staff.values():
            if member.availability_date and member.availability_date <= datetime.now():
                capacity[member.role] += member.capacity
        return capacity

    def get_capacity_at_date(self, target_date):
        capacity = {role: 0.0 for role in ResourceRole}
        for member in self.staff.values():
            if member.availability_date and member.availability_date <= target_date:
                capacity[member.role] += member.capacity
        return capacity

    def calculate_demand(self, target_date, include_pipeline=True, pipeline_threshold=0.0):
        demand = {role: 0.0 for role in ResourceRole}
        for project in self.projects.values():
            if project.start_date <= target_date <= project.end_date:
                for role, need in project.resource_needs.items():
                    demand[role] += need * project.probability
        if include_pipeline:
            for opp in self.pipeline.values():
                if opp.probability >= pipeline_threshold:
                    if opp.start_date <= target_date <= opp.end_date:
                        for role, need in opp.resource_needs.items():
                            demand[role] += need * opp.probability
        return demand

    def identify_gaps(self, horizon_months=12):
        gaps = []
        for month in range(horizon_months):
            period_start = datetime.now() + timedelta(days=month * 30)
            period_end = period_start + timedelta(days=30)
            capacity = self.get_capacity_at_date(period_start)
            demand = self.calculate_demand(period_start)
            for role in ResourceRole:
                cap, dem = capacity.get(role, 0), demand.get(role, 0)
                gap = cap - dem
                if gap < 0:
                    gaps.append(CapacityGap(role=role, period_start=period_start,
                        period_end=period_end, demand=dem, capacity=cap,
                        gap=gap, severity="critical" if gap < -1 else "warning"))
        return gaps

    def can_pursue_project(self, value, start_date, duration_months):
        needs = self._calculate_resource_needs(value, ProjectPhase.CONSTRUCTION)
        end_date = start_date + timedelta(days=duration_months * 30)
        can_staff, bottlenecks = True, []
        current_date = start_date
        while current_date <= end_date:
            capacity = self.get_capacity_at_date(current_date)
            demand = self.calculate_demand(current_date)
            for role, need in needs.items():
                available = capacity.get(role, 0) - demand.get(role, 0)
                if need > available:
                    can_staff = False
                    bottlenecks.append({"date": current_date, "role": role.value,
                        "needed": need, "available": available, "gap": need - available})
            current_date += timedelta(days=30)
        if can_staff:
            rec = "GO - Sufficient capacity"
        elif len(bottlenecks) <= 2:
            rec = "CONDITIONAL - Minor gaps, consider hiring"
        else:
            rec = "CAUTION - Significant capacity constraints"
        return {"can_staff": can_staff, "recommendation": rec,
                "resource_needs": {r.value: v for r, v in needs.items()},
                "bottlenecks": bottlenecks[:10],
                "actions_required": self._suggest_hiring(bottlenecks)}

    def _suggest_hiring(self, bottlenecks):
        if not bottlenecks:
            return []
        role_gaps = {}
        for b in bottlenecks:
            role_gaps[b['role']] = max(role_gaps.get(b['role'], 0), b['gap'])
        return [f"Hire {int(gap)+1} {role}(s) - Gap: {gap:.1f} FTE"
                for role, gap in sorted(role_gaps.items(), key=lambda x: -x[1])]

    def generate_forecast(self, horizon_months=12):
        gaps = self.identify_gaps(horizon_months)
        capacity = self.get_current_capacity()
        demand = self.calculate_demand(datetime.now())
        total_cap = sum(capacity.values())
        total_dem = sum(demand.values())
        util = (total_dem / total_cap * 100) if total_cap > 0 else 0
        recs = []
        if util > 90:
            recs.append("High utilization (>90%) - consider hiring")
        elif util < 60:
            recs.append("Low utilization (<60%) - review project pipeline")
        for role in set(g.role.value for g in gaps if g.severity == "critical"):
            recs.append(f"Critical gap in {role} - immediate action needed")
        return CapacityForecast(forecast_date=datetime.now(), horizon_months=horizon_months,
            total_demand_fte=total_dem, total_capacity_fte=total_cap,
            utilization_pct=util, gaps=gaps, recommendations=recs)

    def generate_report(self):
        forecast = self.generate_forecast()
        lines = ["# Capacity Planning Report", "",
            f"**Organization:** {self.organization_name}",
            f"**Report Date:** {forecast.forecast_date.strftime('%Y-%m-%d')}", "",
            "## Executive Summary", "",
            "| Metric | Value |", "|--------|-------|",
            f"| Active Projects | {len(self.projects)} |",
            f"| Pipeline Opportunities | {len(self.pipeline)} |",
            f"| Total Staff | {len(self.staff)} |",
            f"| Capacity (FTE) | {forecast.total_capacity_fte:.1f} |",
            f"| Demand (FTE) | {forecast.total_demand_fte:.1f} |",
            f"| Utilization | {forecast.utilization_pct:.0f}% |", "",
            "## Capacity by Role", "",
            "| Role | Capacity | Demand | Gap |", "|------|----------|--------|-----|"]
        capacity = self.get_current_capacity()
        demand = self.calculate_demand(datetime.now())
        for role in ResourceRole:
            c, d = capacity.get(role, 0), demand.get(role, 0)
            g = c - d
            icon = "✅" if g >= 0 else "⚠️" if g > -1 else "🔴"
            lines.append(f"| {role.value} | {c:.1f} | {d:.1f} | {g:+.1f} {icon} |")
        lines.extend(["", "## Active Projects", "",
            "| Project | Value | Phase | End Date |", "|---------|-------|-------|----------|"])
        for p in sorted(self.projects.values(), key=lambda x: x.value, reverse=True):
            lines.append(f"| {p.project_name} | ${p.value:,.0f} | {p.phase.value} | {p.end_date.strftime('%Y-%m-%d')} |")
        if self.pipeline:
            lines.extend(["", "## Pipeline", "",
                "| Opportunity | Value | Probability | Expected Start |",
                "|-------------|-------|-------------|----------------|"])
            for p in sorted(self.pipeline.values(), key=lambda x: -x.probability):
                lines.append(f"| {p.project_name} | ${p.value:,.0f} | {p.probability:.0%} | {p.start_date.strftime('%Y-%m-%d')} |")
        critical_gaps = [g for g in forecast.gaps if g.severity == "critical"]
        if critical_gaps:
            lines.extend(["", f"## Critical Capacity Gaps ({len(critical_gaps)})", "",
                "| Role | Period | Gap |", "|------|--------|-----|"])
            for gap in critical_gaps[:10]:
                lines.append(f"| {gap.role.value} | {gap.period_start.strftime('%Y-%m')} | {gap.gap:.1f} FTE |")
        if forecast.recommendations:
            lines.extend(["", "## Recommendations", ""])
            for rec in forecast.recommendations:
                lines.append(f"- {rec}")
        return "\n".join(lines)

# ═══════════════════════════════════════════════════════════════════
# INCIDENT MANAGER
# ═══════════════════════════════════════════════════════════════════

class IncidentManager:
    ROOT_CAUSE_CATEGORIES = [
        "Training/Competency", "Procedures/Work Instructions",
        "Equipment/Tools", "Supervision", "Communication",
        "Housekeeping", "PPE", "Work Environment",
        "Physical/Mental State", "Management System"
    ]

    def __init__(self):
        self.incidents: Dict[str, Incident] = {}
        self.corrective_actions: Dict[str, CorrectiveAction] = {}
        self.toolbox_talks: List[ToolboxTalk] = []
        self.jhas: Dict[str, JHA] = {}

    def report_incident(self, incident_type, category, date_time, location,
                        project_id, project_name, description, immediate_actions,
                        reported_by, injured_person=None):
        incident_id = f"INC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        injured = Person(**injured_person) if injured_person else None
        incident = Incident(id=incident_id, incident_type=incident_type,
            category=category, date_time=date_time, location=location,
            project_id=project_id, project_name=project_name,
            description=description, immediate_actions=immediate_actions,
            reported_by=reported_by, injured_person=injured)
        if incident_type in [IncidentType.MEDICAL_TREATMENT,
                             IncidentType.LOST_TIME, IncidentType.FATALITY]:
            incident.osha_recordable = True
        self.incidents[incident_id] = incident
        return incident

    def add_witness(self, incident_id, witness):
        self.incidents[incident_id].witnesses.append(Person(**witness))
        return self.incidents[incident_id]

    def conduct_investigation(self, incident_id, root_causes, contributing_factors):
        inc = self.incidents[incident_id]
        inc.root_causes = root_causes
        inc.contributing_factors = contributing_factors
        inc.status = InvestigationStatus.ROOT_CAUSE_IDENTIFIED
        return inc

    def five_whys_analysis(self, incident_id, whys):
        analysis = {"incident_id": incident_id,
            "analysis_date": datetime.now().isoformat(),
            "whys": [{"level": i+1, "question": f"Why #{i+1}?", "answer": w}
                     for i, w in enumerate(whys)]}
        if whys:
            self.incidents[incident_id].root_causes.append(whys[-1])
        return analysis

    def fishbone_analysis(self, incident_id, categories):
        """Ishikawa/fishbone analysis.
        categories: {"People": [...], "Process": [...], "Equipment": [...],
                     "Environment": [...], "Materials": [...], "Management": [...]}"""
        analysis = {"incident_id": incident_id,
            "analysis_date": datetime.now().isoformat(), "type": "fishbone",
            "categories": categories,
            "all_causes": [c for causes in categories.values() for c in causes]}
        inc = self.incidents[incident_id]
        for causes in categories.values():
            inc.contributing_factors.extend(causes)
        return analysis

    def assign_corrective_action(self, incident_id, description, assigned_to,
                                 due_days=7, priority="medium"):
        action_id = f"CA-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        action = CorrectiveAction(id=action_id, description=description,
            assigned_to=assigned_to,
            due_date=datetime.now() + timedelta(days=due_days), priority=priority)
        self.incidents[incident_id].corrective_actions.append(action)
        self.incidents[incident_id].status = InvestigationStatus.CORRECTIVE_ACTIONS_ASSIGNED
        self.corrective_actions[action_id] = action
        return action

    def complete_corrective_action(self, action_id, verification_notes):
        action = self.corrective_actions[action_id]
        action.status = "completed"
        action.completed_date = datetime.now()
        action.verification_notes = verification_notes
        return action

    def overdue_actions(self):
        now = datetime.now()
        return [a for a in self.corrective_actions.values()
                if a.status == "open" and a.due_date < now]

    def record_toolbox_talk(self, topic, presenter, project_id, attendees,
                            duration_minutes=15, notes="", related_jha=""):
        talk = ToolboxTalk(id=f"TBT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            date=datetime.now(), topic=topic, presenter=presenter,
            project_id=project_id, attendees=attendees,
            duration_minutes=duration_minutes, notes=notes, related_jha=related_jha)
        self.toolbox_talks.append(talk)
        return talk

    def create_jha(self, job_description, project_id, steps, approved_by=""):
        """steps: [{"step": str, "hazards": [str], "controls": [str]}]"""
        jha = JHA(id=f"JHA-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            job_description=job_description, project_id=project_id,
            created_date=datetime.now(), steps=steps, approved_by=approved_by,
            review_date=datetime.now() + timedelta(days=90))
        self.jhas[jha.id] = jha
        return jha

    def calculate_trir(self, hours_worked, project_id=None):
        incidents = list(self.incidents.values())
        if project_id:
            incidents = [i for i in incidents if i.project_id == project_id]
        recordables = len([i for i in incidents if i.osha_recordable])
        return (recordables * 200_000) / hours_worked if hours_worked else 0

    def calculate_dart(self, hours_worked, project_id=None):
        incidents = list(self.incidents.values())
        if project_id:
            incidents = [i for i in incidents if i.project_id == project_id]
        dart_cases = len([i for i in incidents if i.incident_type == IncidentType.LOST_TIME])
        return (dart_cases * 200_000) / hours_worked if hours_worked else 0

    def get_incident_metrics(self, project_id=None, start_date=None, end_date=None):
        incidents = list(self.incidents.values())
        if project_id:
            incidents = [i for i in incidents if i.project_id == project_id]
        if start_date:
            incidents = [i for i in incidents if i.date_time >= start_date]
        if end_date:
            incidents = [i for i in incidents if i.date_time <= end_date]
        total = len(incidents)
        near_misses = len([i for i in incidents if i.incident_type == IncidentType.NEAR_MISS])
        recordables = len([i for i in incidents if i.osha_recordable])
        by_category = {}
        for cat in IncidentCategory:
            count = len([i for i in incidents if i.category == cat])
            if count > 0:
                by_category[cat.value] = count
        return {
            "total_incidents": total, "near_misses": near_misses,
            "first_aid_cases": len([i for i in incidents if i.incident_type == IncidentType.FIRST_AID]),
            "osha_recordables": recordables,
            "lost_time_incidents": len([i for i in incidents if i.incident_type == IncidentType.LOST_TIME]),
            "total_days_lost": sum(i.days_lost for i in incidents),
            "by_category": by_category,
            "near_miss_ratio": near_misses / recordables if recordables else 0,
            "toolbox_talks_conducted": len(self.toolbox_talks),
            "open_corrective_actions": len([a for a in self.corrective_actions.values() if a.status == "open"]),
            "overdue_actions": len(self.overdue_actions()),
        }

    def safety_scorecard(self, hours_worked, project_id=None):
        metrics = self.get_incident_metrics(project_id=project_id)
        return {
            "lagging_indicators": {
                "trir": self.calculate_trir(hours_worked, project_id),
                "dart": self.calculate_dart(hours_worked, project_id),
                "recordables": metrics["osha_recordables"],
                "days_lost": metrics["total_days_lost"],
                "property_damage": sum(i.property_damage_cost for i in self.incidents.values()
                    if not project_id or i.project_id == project_id),
            },
            "leading_indicators": {
                "near_miss_reports": metrics["near_misses"],
                "toolbox_talks": len([t for t in self.toolbox_talks
                    if not project_id or t.project_id == project_id]),
                "jhas_completed": len([j for j in self.jhas.values()
                    if not project_id or j.project_id == project_id]),
                "open_corrective_actions": metrics["open_corrective_actions"],
                "overdue_corrective_actions": metrics["overdue_actions"],
                "near_miss_ratio": metrics["near_miss_ratio"],
            }
        }

    def predict_incident_risk(self, project_id=None):
        metrics = self.get_incident_metrics(project_id=project_id)
        scorecard = self.safety_scorecard(200_000, project_id)
        risk_score, factors = 0, []
        trir = scorecard["lagging_indicators"]["trir"]
        if trir > 3.0:
            risk_score += 30; factors.append(f"High TRIR ({trir:.1f})")
        elif trir > 1.5:
            risk_score += 15; factors.append(f"Elevated TRIR ({trir:.1f})")
        if metrics["near_miss_ratio"] < 5:
            risk_score += 20; factors.append("Low near-miss ratio (possible underreporting)")
        overdue = metrics["overdue_actions"]
        if overdue > 5:
            risk_score += 25; factors.append(f"{overdue} overdue corrective actions")
        elif overdue > 0:
            risk_score += 10
        if metrics["by_category"]:
            if max(metrics["by_category"].values()) > 5:
                risk_score += 15; factors.append("Concentrated incident pattern")
        level = "LOW" if risk_score < 25 else "MEDIUM" if risk_score < 50 else "HIGH"
        return {"risk_score": min(risk_score, 100), "level": level, "factors": factors}

    def get_trend_analysis(self, months=6):
        trends = []
        now = datetime.now()
        for i in range(months):
            m, y = now.month - i, now.year
            while m <= 0:
                m += 12; y -= 1
            month_start = datetime(y, m, 1)
            nm, ny = m + 1, y
            if nm > 12:
                nm, ny = 1, y + 1
            month_end = datetime(ny, nm, 1) - timedelta(days=1)
            mi = [inc for inc in self.incidents.values() if month_start <= inc.date_time <= month_end]
            trends.append({"month": month_start.strftime("%Y-%m"), "total": len(mi),
                "near_misses": len([i for i in mi if i.incident_type == IncidentType.NEAR_MISS]),
                "recordables": len([i for i in mi if i.osha_recordable])})
        return list(reversed(trends))

    def generate_incident_report(self, incident_id):
        inc = self.incidents[incident_id]
        lines = ["# Incident Report", "",
            f"**Incident ID:** {inc.id}", f"**Type:** {inc.incident_type.value}",
            f"**Category:** {inc.category.value}",
            f"**Date/Time:** {inc.date_time.strftime('%Y-%m-%d %H:%M')}",
            f"**Location:** {inc.location}", f"**Project:** {inc.project_name}",
            f"**Status:** {inc.status.value}",
            f"**OSHA Recordable:** {'Yes' if inc.osha_recordable else 'No'}", "",
            "## Description", inc.description, "",
            "## Immediate Actions Taken", inc.immediate_actions, ""]
        if inc.injured_person:
            ip = inc.injured_person
            lines.extend(["## Injured Person", f"- Name: {ip.name}",
                f"- Company: {ip.company}", f"- Role: {ip.role}",
                f"- Experience: {ip.years_experience} years", ""])
        if inc.root_causes:
            lines.extend(["## Root Causes", *[f"- {rc}" for rc in inc.root_causes], ""])
        if inc.corrective_actions:
            lines.extend(["## Corrective Actions",
                "| Action | Assigned To | Due | Priority | Status |",
                "|--------|-------------|-----|----------|--------|"])
            for ca in inc.corrective_actions:
                lines.append(f"| {ca.description} | {ca.assigned_to} | {ca.due_date.strftime('%Y-%m-%d')} | {ca.priority} | {ca.status} |")
        return "\n".join(lines)

# ═══════════════════════════════════════════════════════════════════
# EQUIPMENT MANAGER
# ═══════════════════════════════════════════════════════════════════

class EquipmentManager:
    def __init__(self):
        self.equipment: Dict[str, Equipment] = {}

    def add_equipment(self, id, name, type, daily_rate=0.0, certifications_required=None):
        eq = Equipment(id=id, name=name, type=type, daily_rate=daily_rate,
            certifications_required=certifications_required or [])
        self.equipment[id] = eq
        return eq

    def assign_to_project(self, equipment_id, project_id):
        eq = self.equipment[equipment_id]
        eq.status = EquipmentStatus.IN_USE
        eq.assigned_project = project_id
        return eq

    def record_inspection(self, equipment_id):
        eq = self.equipment[equipment_id]
        eq.last_inspection = datetime.now()
        return eq

    def schedule_maintenance(self, equipment_id, date):
        self.equipment[equipment_id].next_maintenance = date
        return self.equipment[equipment_id]

    def overdue_inspections(self, interval_days=30):
        cutoff = datetime.now() - timedelta(days=interval_days)
        return [eq for eq in self.equipment.values()
                if not eq.last_inspection or eq.last_inspection < cutoff]

    def utilization_report(self):
        total = len(self.equipment)
        in_use = len([e for e in self.equipment.values() if e.status == EquipmentStatus.IN_USE])
        return {"total": total, "in_use": in_use,
            "available": len([e for e in self.equipment.values() if e.status == EquipmentStatus.AVAILABLE]),
            "maintenance": len([e for e in self.equipment.values() if e.status == EquipmentStatus.MAINTENANCE]),
            "utilization_pct": (in_use / total * 100) if total else 0}

# ═══════════════════════════════════════════════════════════════════
# SUBCONTRACTOR MANAGER
# ═══════════════════════════════════════════════════════════════════

class SubcontractorManager:
    def __init__(self):
        self.subcontractors: Dict[str, Subcontractor] = {}

    def add_subcontractor(self, id, name, trade, safety_rating=1.0):
        sub = Subcontractor(id=id, name=name, trade=trade, safety_rating=safety_rating)
        self.subcontractors[id] = sub
        return sub

    def prequalify(self, sub_id, emr, trir, insurance_verified):
        sub = self.subcontractors[sub_id]
        sub.safety_rating = emr
        passed = emr <= 1.0 and trir <= 3.0 and insurance_verified
        sub.prequalified = passed
        return {"id": sub_id, "prequalified": passed, "emr": emr, "trir": trir}

    def rate_performance(self, sub_id, quality, schedule, safety, communication):
        score = quality * 0.3 + schedule * 0.25 + safety * 0.3 + communication * 0.15
        self.subcontractors[sub_id].performance_score = score
        return score

    def ranked_by_trade(self, trade):
        return sorted([s for s in self.subcontractors.values()
            if s.trade == trade and s.prequalified], key=lambda s: -s.performance_score)
```

## Quick Start — Capacity Planning

```python
from datetime import datetime, timedelta

planner = CapacityPlanner("ABC Construction")
planner.add_staff("PM-001", "John Smith", ResourceRole.PROJECT_MANAGER)
planner.add_staff("PM-002", "Jane Doe", ResourceRole.PROJECT_MANAGER)
planner.add_staff("SUP-001", "Mike Johnson", ResourceRole.SUPERINTENDENT)
planner.add_staff("SUP-002", "Bob Williams", ResourceRole.SUPERINTENDENT)
planner.add_staff("PE-001", "Sarah Davis", ResourceRole.PROJECT_ENGINEER)

planner.add_active_project("PRJ-001", "Downtown Tower", 25_000_000,
    ProjectPhase.CONSTRUCTION, datetime(2024,6,1), datetime(2025,12,31))
planner.add_active_project("PRJ-002", "Hospital Wing", 40_000_000,
    ProjectPhase.CONSTRUCTION, datetime(2024,9,1), datetime(2026,6,30))
planner.add_pipeline_opportunity("OPP-001", "Office Complex", 30_000_000,
    0.6, datetime(2025,3,1), 18)

eval = planner.can_pursue_project(20_000_000, datetime(2025,6,1), 12)
print(eval["recommendation"])
print(planner.generate_report())
```

## Quick Start — Incident & Safety

```python
manager = IncidentManager()

incident = manager.report_incident(
    IncidentType.NEAR_MISS, IncidentCategory.STRUCK_BY,
    datetime.now(), "Level 5, Grid C-4", "PRJ-001", "Office Tower",
    "Unsecured tool fell from scaffold, landed 2 feet from worker",
    "Area cordoned off, toolbox talk conducted", "Site Foreman")

manager.five_whys_analysis(incident.id, [
    "Tool fell from scaffold", "Tool was not secured",
    "No tool lanyard was used", "Worker not trained on tool tethering",
    "Tool tethering training not in orientation"])

manager.fishbone_analysis(incident.id, {
    "People": ["Insufficient training"], "Process": ["No SOP for tethering"],
    "Equipment": ["Lanyards not provided"], "Environment": ["Wind gusts"],
    "Management": ["Orientation gap"]})

manager.assign_corrective_action(incident.id,
    "Update orientation for tool tethering", "Safety Manager", 14, "high")

manager.create_jha("Steel erection at Level 5", "PRJ-001", [
    {"step": "Set up scaffold", "hazards": ["Fall", "Struck by tools"],
     "controls": ["Harness", "Tool lanyards", "Barricade below"]}])

manager.record_toolbox_talk("Tool Tethering", "Safety Manager",
    "PRJ-001", ["Worker A", "Worker B"])

print(manager.safety_scorecard(500_000, "PRJ-001"))
print(manager.predict_incident_risk("PRJ-001"))
```

## Quick Start — CPM & Last Planner

```python
scheduler = CPMScheduler()
scheduler.add_activity("A", "Excavation", 10)
scheduler.add_activity("B", "Foundation", 15, ["A"],
    {ResourceRole.SUPERINTENDENT: 1, ResourceRole.PROJECT_ENGINEER: 1})
scheduler.add_activity("C", "Underground Utilities", 8, ["A"])
scheduler.add_activity("D", "Structural Steel", 20, ["B", "C"],
    {ResourceRole.SUPERINTENDENT: 2})
scheduler.add_activity("E", "Roofing", 10, ["D"])

critical = scheduler.calculate()
print(f"Critical path: {[a.id for a in critical]}")
print(f"Duration: {scheduler.get_project_duration()} days")

lps = LastPlannerSystem("PRJ-001")
plan = lps.create_weekly_plan(datetime(2025, 2, 10), [
    {"task": "Pour slab A", "responsible": "Concrete Sub", "constraint_free": True},
    {"task": "Install rebar B", "responsible": "Rebar Sub", "constraint_free": True},
    {"task": "Backfill east", "responsible": "Earthwork Sub", "constraint_free": False}])

lps.record_completion(datetime(2025, 2, 10), [
    {"task": "Pour slab A", "completed": True},
    {"task": "Install rebar B", "completed": True},
    {"task": "Backfill east", "completed": False, "reason_incomplete": "prerequisite_work"}])
print(f"PPC: {plan.ppc:.0f}%")
```

## Quick Start — EVM

```python
evm = EVMSnapshot(date=datetime.now(), bac=10_000_000,
    pv=4_000_000, ev=3_500_000, ac=3_800_000)
print(evm.summary())
# SPI=0.875, CPI=0.921, EAC=$10.86M
```

## Key Concepts

| Concept | Description |
|---------|-------------|
| **TRIR** | (Recordables × 200,000) / Hours Worked |
| **DART** | (Lost Time Cases × 200,000) / Hours Worked |
| **EMR** | Experience Modification Rate (insurance) |
| **SPI** | Schedule Performance Index (EV/PV, ≥1.0) |
| **CPI** | Cost Performance Index (EV/AC, ≥1.0) |
| **PPC** | Percent Plan Complete (Last Planner) |
| **CPM** | Critical Path Method |
| **Resource Leveling** | Delay non-critical tasks to reduce peaks |
| **Resource Smoothing** | Adjust within float, no extension |
| **5 Whys** | Iterative root cause analysis |
| **Fishbone** | Ishikawa: People, Process, Equipment, Environment, Materials, Management |
| **JHA/JSA** | Job Hazard/Safety Analysis |
| **Toolbox Talk** | Short safety briefing |
| **Leading Indicators** | Near-misses, JHAs, talks, observations |
| **Lagging Indicators** | TRIR, DART, days lost, fatalities |
| **BIM** | 3D/4D/5D models for coordination |
| **Digital Twin** | Real-time virtual project replica |
| **Lean Construction** | Eliminate waste, pull planning |
| **Last Planner** | Collaborative weekly planning + PPC |

## Requirements

```bash
pip install (no external dependencies — pure Python)
```
