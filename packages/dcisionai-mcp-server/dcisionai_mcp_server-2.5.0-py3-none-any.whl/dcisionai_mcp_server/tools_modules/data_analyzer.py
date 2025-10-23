#!/usr/bin/env python3
"""
Data Analysis Tool with Realistic Mock Data Generation
"""

import logging
import random
import boto3
import json
from datetime import datetime
from typing import Any, Dict, Optional, List
from botocore.exceptions import ClientError

from ..core.bedrock_client import BedrockClient
from ..core.knowledge_base import KnowledgeBase
from ..utils.json_parser import parse_json

logger = logging.getLogger(__name__)


class DataAnalyzer:
    """Enhanced data analysis with KB integration and user data comparison"""
    
    def __init__(self, bedrock_client: BedrockClient, knowledge_base: KnowledgeBase):
        self.bedrock = bedrock_client
        self.kb = knowledge_base
        
        # Initialize Bedrock Knowledge Base client
        self.knowledge_base_id = "0WHL51KZTW"
        self.region = "us-east-1"
        try:
            self.bedrock_agent_runtime = boto3.client(
                'bedrock-agent-runtime',
                region_name=self.region
            )
            logger.info("✅ Bedrock Agent Runtime client initialized for data analysis")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Bedrock Agent Runtime client: {e}")
            self.bedrock_agent_runtime = None
    
    async def analyze_data(self, problem_description: str, intent_data: Optional[Dict] = None, user_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Enhanced data analysis using intent response and KB requirements"""
        try:
            # Extract intent information
            intent = intent_data.get('intent', 'unknown') if intent_data else 'unknown'
            industry = intent_data.get('industry', 'unknown') if intent_data else 'unknown'
            matched_use_case = intent_data.get('matched_use_case', 'unknown') if intent_data else 'unknown'
            
            logger.info(f"🔍 Analyzing data for intent: {intent}, industry: {industry}, use case: {matched_use_case}")
            
            # Step 1: Query KB for data requirements for this use case
            kb_data_requirements = await self._get_kb_data_requirements(intent, industry, matched_use_case)
            
            # Step 2: Analyze user-provided data
            user_data_analysis = self._analyze_user_data(user_data or {})
            
            # Step 3: Compare user data vs KB requirements
            data_gap_analysis = self._analyze_data_gaps(user_data_analysis, kb_data_requirements)
            
            # Step 4: Generate missing data using KB templates
            simulated_data = await self._generate_missing_data(data_gap_analysis, kb_data_requirements, problem_description)
            
            # Step 5: Create comprehensive data summary
            data_summary = self._create_data_summary(user_data_analysis, simulated_data, data_gap_analysis, kb_data_requirements)
            
            result = {
                "intent_used": intent,
                "industry": industry,
                "use_case": matched_use_case,
                "kb_requirements": kb_data_requirements,
                "user_data_analysis": user_data_analysis,
                "data_gap_analysis": data_gap_analysis,
                "simulated_data": simulated_data,
                "data_summary": data_summary,
                "readiness_score": data_summary.get('overall_readiness', 0.8),
                "data_quality": data_summary.get('data_quality', 'high'),
                "completeness": data_summary.get('completeness', 'complete')
            }
            
            return {
                "status": "success",
                "step": "data_analysis",
                "timestamp": datetime.now().isoformat(),
                "result": result,
                "message": f"Data analysis completed: {data_summary.get('overall_readiness', 0.8):.1%} readiness with KB integration"
            }
            
        except Exception as e:
            logger.error(f"Enhanced data analysis error: {e}")
            return {"status": "error", "step": "data_analysis", "error": str(e)}
    
    def _generate_mock_data(self, problem_description: str, intent: str, industry: str, optimization_type: str) -> Dict[str, Any]:
        """Generate realistic mock data based on problem characteristics"""
        problem_lower = problem_description.lower()
        
        # Manufacturing/Production Planning
        if any(word in problem_lower for word in ['manufacturing', 'production', 'factory', 'plant', 'furniture', 'chairs', 'tables', 'cabinets']):
            return self._generate_manufacturing_data(problem_description)
        
        # Portfolio Optimization
        elif any(word in problem_lower for word in ['portfolio', 'investment', 'stocks', 'assets', 'returns', 'risk']):
            return self._generate_portfolio_data(problem_description)
        
        # Scheduling Problems
        elif any(word in problem_lower for word in ['schedule', 'nurse', 'employee', 'shift', 'staffing', 'roster']):
            return self._generate_scheduling_data(problem_description)
        
        # Supply Chain/Logistics
        elif any(word in problem_lower for word in ['supply', 'logistics', 'transportation', 'warehouse', 'inventory']):
            return self._generate_supply_chain_data(problem_description)
        
        # Resource Allocation
        elif any(word in problem_lower for word in ['resource', 'allocation', 'budget', 'capacity', 'assignment']):
            return self._generate_resource_allocation_data(problem_description)
        
        # Default generic optimization
        else:
            return self._generate_generic_data(problem_description)
    
    def _generate_manufacturing_data(self, problem_description: str) -> Dict[str, Any]:
        """Generate realistic manufacturing data"""
        # Extract product types from problem description
        products = []
        if 'chair' in problem_description.lower():
            products.append('chairs')
        if 'table' in problem_description.lower():
            products.append('tables')
        if 'cabinet' in problem_description.lower():
            products.append('cabinets')
        
        if not products:
            products = ['product_a', 'product_b', 'product_c']
        
        # Realistic manufacturing parameters
        variables = []
        constraints = []
        assumptions = []
        
        for i, product in enumerate(products):
            # Realistic production capacity (units per day)
            daily_capacity = random.randint(50, 300)
            
            # Realistic labor hours per unit (based on complexity)
            labor_hours = random.uniform(1.5, 8.0)
            
            # Realistic profit margins ($10-150 per unit)
            profit_per_unit = random.uniform(10, 150)
            
            # Realistic demand (monthly)
            monthly_demand_min = random.randint(500, 2000)
            monthly_demand_max = monthly_demand_min + random.randint(500, 1500)
            
            variables.append({
                "name": f"{product}_daily_production",
                "type": "continuous",
                "bounds": f"0 to {daily_capacity}",
                "description": f"Daily production quantity of {product}",
                "realistic_value": daily_capacity * 0.7  # 70% utilization
            })
            
            constraints.append({
                "type": "capacity",
                "expression": f"{product}_daily_production <= {daily_capacity}",
                "description": f"Daily production capacity limit for {product}",
                "realistic_bound": daily_capacity
            })
            
            constraints.append({
                "type": "demand",
                "expression": f"{monthly_demand_min} <= {product}_daily_production * 30 <= {monthly_demand_max}",
                "description": f"Monthly demand range for {product}",
                "realistic_range": [monthly_demand_min, monthly_demand_max]
            })
            
            assumptions.append(f"{product.title()}: {labor_hours:.1f} labor hours/unit, ${profit_per_unit:.2f} profit/unit")
        
        # Labor constraints
        total_labor_hours = random.randint(800, 2000)
        constraints.append({
            "type": "labor",
            "expression": f"sum(labor_hours * production) <= {total_labor_hours}",
            "description": "Daily labor hour availability",
            "realistic_bound": total_labor_hours
        })
        
        return {
            "variables": variables,
            "constraints": constraints,
            "objective": {
                "type": "maximize",
                "expression": "sum(profit_per_unit * production)",
                "description": "Maximize total profit"
            },
            "assumptions": assumptions,
            "benchmarks": {
                "typical_utilization": "70-85%",
                "profit_margin_range": "15-35%",
                "labor_efficiency": "80-95%"
            },
            "industry_standards": {
                "setup_time": "5-15% of production time",
                "quality_rate": "95-99%",
                "maintenance_downtime": "2-5%"
            }
        }
    
    def _generate_portfolio_data(self, problem_description: str) -> Dict[str, Any]:
        """Generate realistic portfolio optimization data"""
        variables = []
        constraints = []
        assumptions = []
        
        # Extract specific asset names from problem description
        asset_names = self._extract_asset_names(problem_description)
        
        # If no specific assets found, use default
        if not asset_names:
            num_assets = 5  # Default smaller number
            asset_names = [f"Asset_{i+1}" for i in range(num_assets)]
        
        for i, asset in enumerate(asset_names):
            # Realistic expected returns (annual, 5-15%)
            expected_return = random.uniform(0.05, 0.15)
            
            # Realistic volatility (15-35%)
            volatility = random.uniform(0.15, 0.35)
            
            # Realistic correlation with market
            beta = random.uniform(0.7, 1.4)
            
            variables.append({
                "name": f"weight_{asset}",
                "type": "continuous",
                "bounds": "0 to 1",
                "description": f"Portfolio weight for {asset}",
                "expected_return": expected_return,
                "volatility": volatility,
                "beta": beta
            })
            
            assumptions.append(f"{asset}: {expected_return:.1%} expected return, {volatility:.1%} volatility")
        
        # Portfolio constraints
        constraints.append({
            "type": "budget",
            "expression": "sum(weights) = 1",
            "description": "Portfolio weights must sum to 100%"
        })
        
        constraints.append({
            "type": "risk",
            "expression": "portfolio_variance <= max_variance",
            "description": "Portfolio risk constraint",
            "max_variance": 0.04  # 20% volatility limit
        })
        
        return {
            "variables": variables,
            "constraints": constraints,
            "objective": {
                "type": "maximize",
                "expression": "sum(expected_return * weight)",
                "description": "Maximize expected portfolio return"
            },
            "assumptions": assumptions,
            "benchmarks": {
                "market_return": "8-12% annually",
                "risk_free_rate": "2-4%",
                "typical_sharpe_ratio": "0.5-1.2"
            },
            "market_data": {
                "correlation_matrix": "Generated based on realistic correlations",
                "risk_free_rate": 0.03,
                "market_volatility": 0.20
            }
        }
    
    def _extract_asset_names(self, problem_description: str) -> List[str]:
        """Extract specific asset names from problem description"""
        import re
        
        # Look for patterns like "Tech Corp", "Energy Ltd", etc.
        # Pattern: Capitalized words followed by Corp/Ltd/Inc/Co/Bank
        asset_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Corp|Ltd|Inc|Co|Bank|Group|Holdings|Partners))\b'
        matches = re.findall(asset_pattern, problem_description)
        
        if matches:
            return [match.strip() for match in matches]
        
        # Look for quoted asset names
        quoted_pattern = r'"([^"]+)"'
        quoted_matches = re.findall(quoted_pattern, problem_description)
        
        if quoted_matches:
            return quoted_matches
        
        # Look for simple stock names (single capitalized words)
        simple_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
        simple_matches = re.findall(simple_pattern, problem_description)
        
        # Filter out common words that aren't asset names
        exclude_words = {'An', 'The', 'A', 'Investment', 'Manager', 'Has', 'To', 'Allocate', 'Across', 'Stocks', 'Expected', 'Return', 'Risk', 'Portfolio', 'Must', 'Not', 'Exceed', 'Single', 'Can', 'What', 'Is', 'Optimal', 'Maximize', 'While', 'Staying', 'Within', 'Constraints', 'How', 'Should', 'Be', 'Scheduled', 'Minimize', 'Labor', 'Costs', 'Meeting', 'All', 'Requirements'}
        asset_names = [match for match in simple_matches if match not in exclude_words and len(match) > 2]
        
        return asset_names[:10]  # Limit to 10 assets
    
    def _extract_number_from_text(self, text: str, keywords: List[str]) -> Optional[int]:
        """Extract a number that appears near specific keywords in text"""
        import re
        
        text_lower = text.lower()
        
        for keyword in keywords:
            # Look for patterns like "25 nurses", "across 3 shifts", "for the next 7 days"
            patterns = [
                rf'(\d+)\s+{keyword}',  # "25 nurses"
                rf'{keyword}.*?(\d+)',  # "nurses across 25"
                rf'(\d+).*?{keyword}',  # "25 across nurses"
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text_lower)
                if matches:
                    try:
                        return int(matches[0])
                    except (ValueError, IndexError):
                        continue
        
        return None
    
    def _generate_scheduling_data(self, problem_description: str) -> Dict[str, Any]:
        """Generate realistic scheduling data"""
        # Extract scheduling parameters from problem description
        num_employees = self._extract_number_from_text(problem_description, ['nurses', 'employees', 'staff'])
        if num_employees is None:
            num_employees = 25  # Default for healthcare
        
        num_shifts = self._extract_number_from_text(problem_description, ['shifts'])
        if num_shifts is None:
            num_shifts = 3  # Day, Evening, Night
        
        num_days = self._extract_number_from_text(problem_description, ['days'])
        if num_days is None:
            num_days = 7   # Weekly schedule
        
        variables = []
        constraints = []
        assumptions = []
        
        for emp in range(num_employees):
            for day in range(num_days):
                for shift in range(num_shifts):
                    variables.append({
                        "name": f"emp_{emp}_day_{day}_shift_{shift}",
                        "type": "binary",
                        "bounds": "binary",
                        "description": f"Employee {emp} assigned to shift {shift} on day {day}"
                    })
        
        # Coverage constraints
        for day in range(num_days):
            for shift in range(num_shifts):
                min_coverage = random.randint(3, 8)
                constraints.append({
                    "type": "coverage",
                    "expression": f"sum(emp_*_day_{day}_shift_{shift}) >= {min_coverage}",
                    "description": f"Minimum coverage for day {day}, shift {shift}",
                    "min_coverage": min_coverage
                })
        
        # Employee constraints
        for emp in range(num_employees):
            max_shifts_per_week = random.randint(4, 6)
            constraints.append({
                "type": "employee_limit",
                "expression": f"sum(emp_{emp}_day_*_shift_*) <= {max_shifts_per_week}",
                "description": f"Employee {emp} maximum shifts per week",
                "max_shifts": max_shifts_per_week
            })
        
        assumptions.append(f"{num_employees} employees, {num_shifts} shifts/day, {num_days} days/week")
        assumptions.append("Minimum 8 hours between shifts")
        assumptions.append("Maximum 5 consecutive days")
        
        return {
            "variables": variables,
            "constraints": constraints,
            "objective": {
                "type": "minimize",
                "expression": "sum(assignment_costs)",
                "description": "Minimize total scheduling costs"
            },
            "assumptions": assumptions,
            "benchmarks": {
                "typical_utilization": "75-90%",
                "overtime_threshold": "40 hours/week",
                "shift_premium": "10-25%"
            }
        }
    
    def _generate_supply_chain_data(self, problem_description: str) -> Dict[str, Any]:
        """Generate realistic supply chain data"""
        num_suppliers = random.randint(3, 8)
        num_products = random.randint(5, 15)
        num_customers = random.randint(10, 30)
        
        variables = []
        constraints = []
        assumptions = []
        
        # Supplier capacity variables
        for supplier in range(num_suppliers):
            capacity = random.randint(1000, 10000)
            variables.append({
                "name": f"supplier_{supplier}_capacity",
                "type": "continuous",
                "bounds": f"0 to {capacity}",
                "description": f"Production capacity at supplier {supplier}",
                "realistic_capacity": capacity
            })
        
        # Demand variables
        for customer in range(num_customers):
            for product in range(num_products):
                demand = random.randint(50, 500)
                variables.append({
                    "name": f"demand_customer_{customer}_product_{product}",
                    "type": "continuous",
                    "bounds": f"0 to {demand}",
                    "description": f"Demand for product {product} from customer {customer}",
                    "realistic_demand": demand
                })
        
        assumptions.append(f"{num_suppliers} suppliers, {num_products} products, {num_customers} customers")
        assumptions.append("Lead times: 1-5 days")
        assumptions.append("Transportation costs: $0.50-$2.00 per unit")
        
        return {
            "variables": variables,
            "constraints": constraints,
            "objective": {
                "type": "minimize",
                "expression": "sum(production_costs + transportation_costs)",
                "description": "Minimize total supply chain costs"
            },
            "assumptions": assumptions,
            "benchmarks": {
                "typical_fill_rate": "95-98%",
                "inventory_turnover": "6-12 times/year",
                "on_time_delivery": "90-95%"
            }
        }
    
    def _generate_resource_allocation_data(self, problem_description: str) -> Dict[str, Any]:
        """Generate realistic resource allocation data"""
        num_projects = random.randint(5, 20)
        num_resources = random.randint(3, 10)
        
        variables = []
        constraints = []
        assumptions = []
        
        for project in range(num_projects):
            for resource in range(num_resources):
                variables.append({
                    "name": f"project_{project}_resource_{resource}",
                    "type": "continuous",
                    "bounds": "0 to 1",
                    "description": f"Allocation of resource {resource} to project {project}",
                    "realistic_allocation": random.uniform(0.1, 0.8)
                })
        
        # Resource capacity constraints
        for resource in range(num_resources):
            capacity = random.uniform(0.8, 1.2)
            constraints.append({
                "type": "resource_capacity",
                "expression": f"sum(project_*_resource_{resource}) <= {capacity}",
                "description": f"Resource {resource} capacity constraint",
                "realistic_capacity": capacity
            })
        
        assumptions.append(f"{num_projects} projects, {num_resources} resource types")
        assumptions.append("Project priorities: High, Medium, Low")
        assumptions.append("Resource costs: $50-$200 per unit")
        
        return {
            "variables": variables,
            "constraints": constraints,
            "objective": {
                "type": "maximize",
                "expression": "sum(project_value * allocation)",
                "description": "Maximize total project value"
            },
            "assumptions": assumptions,
            "benchmarks": {
                "typical_utilization": "80-95%",
                "project_success_rate": "70-85%",
                "resource_efficiency": "75-90%"
            }
        }
    
    def _generate_generic_data(self, problem_description: str) -> Dict[str, Any]:
        """Generate generic optimization data"""
        num_variables = random.randint(5, 15)
        
        variables = []
        constraints = []
        
        for i in range(num_variables):
            variables.append({
                "name": f"x_{i+1}",
                "type": "continuous",
                "bounds": "0 to 100",
                "description": f"Decision variable {i+1}",
                "realistic_value": random.uniform(10, 80)
            })
        
        # Generic constraints
        constraints.append({
            "type": "budget",
            "expression": "sum(x_*) <= 1000",
            "description": "Budget constraint"
        })
        
        return {
            "variables": variables,
            "constraints": constraints,
            "objective": {
                "type": "maximize",
                "expression": "sum(coefficient * x_*)",
                "description": "Maximize objective function"
            },
            "assumptions": ["Generic optimization problem"],
            "benchmarks": {"typical_solution_time": "1-10 seconds"}
        }
    
    def _calculate_readiness_score(self, mock_data: Dict[str, Any]) -> float:
        """Calculate data readiness score"""
        score = 0.9  # Mock data is always high quality
        
        # Adjust based on data completeness
        if mock_data.get('variables'):
            score += 0.05
        if mock_data.get('constraints'):
            score += 0.03
        if mock_data.get('assumptions'):
            score += 0.02
        
        return min(score, 1.0)
    
    async def _get_kb_data_requirements(self, intent: str, industry: str, use_case: str) -> Dict[str, Any]:
        """Query KB for data requirements for the specific use case"""
        try:
            if not self.bedrock_agent_runtime:
                logger.warning("Bedrock Agent Runtime not available, using fallback")
                return self._get_fallback_data_requirements(intent, industry, use_case)
            
            # Query KB for data requirements
            query = f"Data requirements for {use_case} in {industry} industry for {intent} optimization"
            
            response = self.bedrock_agent_runtime.retrieve_and_generate(
                input={
                    "text": query
                },
                retrieveAndGenerateConfiguration={
                    "type": "KNOWLEDGE_BASE",
                    "knowledgeBaseConfiguration": {
                        "knowledgeBaseId": self.knowledge_base_id,
                        "modelArn": f"arn:aws:bedrock:{self.region}::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
                    }
                }
            )
            
            # Extract and analyze KB response
            answer = response.get('output', {}).get('text', '')
            citations = response.get('citations', [])
            
            # Parse KB response to extract data requirements
            kb_requirements = await self._parse_kb_data_requirements(answer, citations, intent, industry, use_case)
            
            logger.info(f"✅ KB data requirements retrieved for {use_case}")
            return kb_requirements
            
        except Exception as e:
            logger.error(f"KB data requirements query failed: {e}")
            return self._get_fallback_data_requirements(intent, industry, use_case)
    
    async def _parse_kb_data_requirements(self, answer: str, citations: list, intent: str, industry: str, use_case: str) -> Dict[str, Any]:
        """Parse KB response to extract data requirements"""
        try:
            prompt = f"""Extract data requirements from this Knowledge Base response.

KB ANSWER: {answer}
INTENT: {intent}
INDUSTRY: {industry}
USE_CASE: {use_case}

Extract the required data elements and format them as JSON:

{{
  "required_variables": [
    {{"name": "variable_name", "type": "continuous|binary|integer", "description": "description", "required": true}},
    {{"name": "capacity", "type": "continuous", "description": "Resource capacity", "required": true}}
  ],
  "required_constraints": [
    {{"type": "capacity", "description": "Capacity constraint", "required": true}},
    {{"type": "demand", "description": "Demand constraint", "required": true}}
  ],
  "required_parameters": [
    {{"name": "cost_per_unit", "type": "float", "description": "Cost per unit", "required": true}},
    {{"name": "time_horizon", "type": "integer", "description": "Planning horizon", "required": true}}
  ],
  "data_sources": ["internal_systems", "external_apis", "manual_input"],
  "data_quality_requirements": {{
    "completeness": "95%",
    "accuracy": "99%",
    "timeliness": "real_time"
  }}
}}"""
            
            resp = await self.bedrock.invoke("anthropic.claude-3-haiku-20240307-v1:0", prompt, 1000)
            result = parse_json(resp)
            
            # Set defaults
            result.setdefault('required_variables', [])
            result.setdefault('required_constraints', [])
            result.setdefault('required_parameters', [])
            result.setdefault('data_sources', ['manual_input'])
            result.setdefault('data_quality_requirements', {
                'completeness': '90%',
                'accuracy': '95%',
                'timeliness': 'daily'
            })
            
            return result
            
        except Exception as e:
            logger.error(f"KB data requirements parsing failed: {e}")
            return self._get_fallback_data_requirements(intent, industry, use_case)
    
    def _get_fallback_data_requirements(self, intent: str, industry: str, use_case: str) -> Dict[str, Any]:
        """Fallback data requirements when KB is not available"""
        # Generate basic requirements based on intent and industry
        requirements = {
            "required_variables": [],
            "required_constraints": [],
            "required_parameters": [],
            "data_sources": ["manual_input"],
            "data_quality_requirements": {
                "completeness": "90%",
                "accuracy": "95%",
                "timeliness": "daily"
            }
        }
        
        # Add requirements based on intent
        if "production_planning" in intent or "scheduling" in intent:
            requirements["required_variables"].extend([
                {"name": "production_quantity", "type": "continuous", "description": "Production quantity", "required": True},
                {"name": "capacity", "type": "continuous", "description": "Production capacity", "required": True}
            ])
            requirements["required_constraints"].extend([
                {"type": "capacity", "description": "Capacity constraint", "required": True},
                {"type": "demand", "description": "Demand constraint", "required": True}
            ])
        
        elif "portfolio" in intent:
            requirements["required_variables"].extend([
                {"name": "asset_weights", "type": "continuous", "description": "Portfolio weights", "required": True},
                {"name": "expected_returns", "type": "continuous", "description": "Expected returns", "required": True}
            ])
            requirements["required_constraints"].extend([
                {"type": "budget", "description": "Budget constraint", "required": True},
                {"type": "risk", "description": "Risk constraint", "required": True}
            ])
        
        return requirements
    
    def _analyze_user_data(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze user-provided data"""
        analysis = {
            "data_provided": len(user_data) > 0,
            "data_types": list(user_data.keys()) if user_data else [],
            "data_quality": "unknown",
            "completeness": 0.0,
            "variables_found": [],
            "constraints_found": [],
            "parameters_found": [],
            "data_sources": ["user_input"] if user_data else []
        }
        
        if user_data:
            # Analyze data quality
            analysis["data_quality"] = "high" if len(user_data) > 5 else "medium" if len(user_data) > 2 else "low"
            analysis["completeness"] = min(len(user_data) / 10, 1.0)  # Assume 10 is complete
            
            # Look for variables, constraints, parameters
            for key, value in user_data.items():
                if "variable" in key.lower() or "quantity" in key.lower():
                    analysis["variables_found"].append(key)
                elif "constraint" in key.lower() or "limit" in key.lower():
                    analysis["constraints_found"].append(key)
                elif "param" in key.lower() or "cost" in key.lower():
                    analysis["parameters_found"].append(key)
        
        return analysis
    
    def _analyze_data_gaps(self, user_analysis: Dict[str, Any], kb_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze gaps between user data and KB requirements"""
        gaps = {
            "missing_variables": [],
            "missing_constraints": [],
            "missing_parameters": [],
            "gap_score": 0.0,
            "critical_gaps": [],
            "optional_gaps": []
        }
        
        # Check for missing variables
        required_vars = [var["name"] for var in kb_requirements.get("required_variables", [])]
        user_vars = user_analysis.get("variables_found", [])
        
        for var in required_vars:
            if var not in user_vars:
                gaps["missing_variables"].append(var)
                gaps["critical_gaps"].append(f"Missing variable: {var}")
        
        # Check for missing constraints
        required_constraints = [const["type"] for const in kb_requirements.get("required_constraints", [])]
        user_constraints = user_analysis.get("constraints_found", [])
        
        for const in required_constraints:
            if const not in user_constraints:
                gaps["missing_constraints"].append(const)
                gaps["critical_gaps"].append(f"Missing constraint: {const}")
        
        # Check for missing parameters
        required_params = [param["name"] for param in kb_requirements.get("required_parameters", [])]
        user_params = user_analysis.get("parameters_found", [])
        
        for param in required_params:
            if param not in user_params:
                gaps["missing_parameters"].append(param)
                gaps["critical_gaps"].append(f"Missing parameter: {param}")
        
        # Calculate gap score
        total_required = len(required_vars) + len(required_constraints) + len(required_params)
        total_missing = len(gaps["missing_variables"]) + len(gaps["missing_constraints"]) + len(gaps["missing_parameters"])
        gaps["gap_score"] = total_missing / total_required if total_required > 0 else 0.0
        
        return gaps
    
    async def _generate_missing_data(self, gap_analysis: Dict[str, Any], kb_requirements: Dict[str, Any], problem_description: str) -> Dict[str, Any]:
        """Generate missing data using KB templates"""
        try:
            simulated_data = {
                "variables": {},
                "constraints": {},
                "parameters": {},
                "data_sources": ["simulated", "kb_template"],
                "generation_method": "kb_template"
            }
            
            # Generate missing variables
            for var_name in gap_analysis.get("missing_variables", []):
                var_data = self._generate_variable_data(var_name, problem_description)
                simulated_data["variables"][var_name] = var_data
            
            # Generate missing constraints
            for const_type in gap_analysis.get("missing_constraints", []):
                const_data = self._generate_constraint_data(const_type, problem_description)
                simulated_data["constraints"][const_type] = const_data
            
            # Generate missing parameters
            for param_name in gap_analysis.get("missing_parameters", []):
                param_data = self._generate_parameter_data(param_name, problem_description)
                simulated_data["parameters"][param_name] = param_data
            
            logger.info(f"✅ Generated simulated data for {len(simulated_data['variables'])} variables, {len(simulated_data['constraints'])} constraints, {len(simulated_data['parameters'])} parameters")
            
            return simulated_data
            
        except Exception as e:
            logger.error(f"Missing data generation failed: {e}")
            return {"variables": {}, "constraints": {}, "parameters": {}, "data_sources": ["fallback"], "generation_method": "fallback"}
    
    def _generate_variable_data(self, var_name: str, problem_description: str) -> Dict[str, Any]:
        """Generate data for a specific variable"""
        # Generate realistic data based on variable name
        if "production" in var_name.lower() or "quantity" in var_name.lower():
            return {
                "type": "continuous",
                "value": random.randint(50, 500),
                "bounds": [0, 1000],
                "description": f"Production quantity for {var_name}",
                "unit": "units"
            }
        elif "capacity" in var_name.lower():
            return {
                "type": "continuous",
                "value": random.randint(100, 1000),
                "bounds": [0, 2000],
                "description": f"Capacity for {var_name}",
                "unit": "units"
            }
        elif "weight" in var_name.lower() or "allocation" in var_name.lower():
            return {
                "type": "continuous",
                "value": random.uniform(0.1, 0.5),
                "bounds": [0, 1],
                "description": f"Allocation weight for {var_name}",
                "unit": "fraction"
            }
        else:
            return {
                "type": "continuous",
                "value": random.randint(10, 100),
                "bounds": [0, 200],
                "description": f"Value for {var_name}",
                "unit": "units"
            }
    
    def _generate_constraint_data(self, const_type: str, problem_description: str) -> Dict[str, Any]:
        """Generate data for a specific constraint type"""
        if const_type == "capacity":
            return {
                "type": "inequality",
                "expression": "sum(production) <= capacity_limit",
                "limit": random.randint(500, 2000),
                "description": "Production capacity constraint"
            }
        elif const_type == "demand":
            return {
                "type": "equality",
                "expression": "sum(production) >= demand_requirement",
                "requirement": random.randint(200, 800),
                "description": "Demand satisfaction constraint"
            }
        elif const_type == "budget":
            return {
                "type": "inequality",
                "expression": "sum(cost * quantity) <= budget_limit",
                "limit": random.randint(10000, 100000),
                "description": "Budget constraint"
            }
        else:
            return {
                "type": "inequality",
                "expression": f"sum({const_type}_var) <= {const_type}_limit",
                "limit": random.randint(100, 1000),
                "description": f"{const_type.title()} constraint"
            }
    
    def _generate_parameter_data(self, param_name: str, problem_description: str) -> Dict[str, Any]:
        """Generate data for a specific parameter"""
        if "cost" in param_name.lower():
            return {
                "value": random.uniform(10, 100),
                "unit": "dollars",
                "description": f"Cost parameter for {param_name}"
            }
        elif "time" in param_name.lower() or "horizon" in param_name.lower():
            return {
                "value": random.randint(7, 30),
                "unit": "days",
                "description": f"Time parameter for {param_name}"
            }
        elif "rate" in param_name.lower():
            return {
                "value": random.uniform(0.01, 0.1),
                "unit": "percentage",
                "description": f"Rate parameter for {param_name}"
            }
        else:
            return {
                "value": random.uniform(1, 10),
                "unit": "units",
                "description": f"Parameter for {param_name}"
            }
    
    def _create_data_summary(self, user_analysis: Dict[str, Any], simulated_data: Dict[str, Any], gap_analysis: Dict[str, Any], kb_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive data summary"""
        summary = {
            "user_data_provided": user_analysis.get("data_provided", False),
            "user_data_quality": user_analysis.get("data_quality", "unknown"),
            "user_data_completeness": user_analysis.get("completeness", 0.0),
            "simulated_data_generated": len(simulated_data.get("variables", {})) > 0,
            "simulated_variables": len(simulated_data.get("variables", {})),
            "simulated_constraints": len(simulated_data.get("constraints", {})),
            "simulated_parameters": len(simulated_data.get("parameters", {})),
            "critical_gaps": gap_analysis.get("critical_gaps", []),
            "gap_score": gap_analysis.get("gap_score", 0.0),
            "overall_readiness": 0.0,
            "data_quality": "high",
            "completeness": "complete"
        }
        
        # Calculate overall readiness - consider both user data and simulated data
        user_completeness = user_analysis.get("completeness", 0.0)
        
        # Calculate simulated data coverage
        total_required = len(kb_requirements.get("required_variables", [])) + len(kb_requirements.get("required_constraints", [])) + len(kb_requirements.get("required_parameters", []))
        total_simulated = len(simulated_data.get("variables", {})) + len(simulated_data.get("constraints", {})) + len(simulated_data.get("parameters", {}))
        simulated_coverage = total_simulated / total_required if total_required > 0 else 1.0
        
        # Overall readiness = weighted average of user data + simulated data
        # If user provided data, weight it more heavily; if not, rely on simulation
        if user_analysis.get("data_provided", False):
            summary["overall_readiness"] = (user_completeness * 0.3 + simulated_coverage * 0.7)
        else:
            summary["overall_readiness"] = simulated_coverage
        
        # Determine data quality
        if summary["overall_readiness"] > 0.9:
            summary["data_quality"] = "excellent"
        elif summary["overall_readiness"] > 0.7:
            summary["data_quality"] = "high"
        elif summary["overall_readiness"] > 0.5:
            summary["data_quality"] = "medium"
        else:
            summary["data_quality"] = "low"
        
        # Determine completeness
        if gap_analysis.get("critical_gaps", []):
            summary["completeness"] = "partial"
        else:
            summary["completeness"] = "complete"
        
        return summary


async def analyze_data_tool(problem_description: str, intent_data: Optional[Dict] = None) -> Dict[str, Any]:
    """Tool wrapper for data analysis"""
    # This would be called from the main tools orchestrator
    # For now, return a placeholder
    return {"status": "error", "error": "Tool not initialized"}
