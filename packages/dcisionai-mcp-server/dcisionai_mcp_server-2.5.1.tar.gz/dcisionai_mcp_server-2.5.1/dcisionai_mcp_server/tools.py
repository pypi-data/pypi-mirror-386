#!/usr/bin/env python3
"""
DcisionAI MCP Tools Orchestrator - Refactored Version 2.1
========================================================
SECURITY: No eval(), uses AST parsing
VALIDATION: Comprehensive result validation  
RELIABILITY: Multi-region failover, rate limiting
ORGANIZATION: Modular architecture with clear separation of concerns
"""

import logging
import os
from typing import Any, Dict, Optional

from .core import BedrockClient, KnowledgeBase, Validator
from .tools_modules.intent_classifier import IntentClassifier
from .tools_modules.data_analyzer import DataAnalyzer
from .tools_modules.solver_selector import SolverSelectorTool
from .tools_modules.model_builder import ModelBuilder
from .tools_modules.optimization_solver import OptimizationSolver
from .tools_modules.explainability import ExplainabilityTool
from .tools_modules.simulation import SimulationTool
from .tools_modules.validation_tool import ValidationTool
from .tools_modules.workflow_validator import WorkflowValidator
from .workflows import WorkflowManager
from .config import Config

logger = logging.getLogger(__name__)


class DcisionAITools:
    """Main orchestrator for DcisionAI optimization tools"""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        
        # Initialize core components
        self.bedrock = BedrockClient()
        self.validator = Validator()
        self.workflow_manager = WorkflowManager()
        
        # Initialize knowledge base
        kb_path = os.path.join(os.path.dirname(__file__), '..', 'dcisionai_kb.json')
        self.kb = KnowledgeBase(kb_path)
        self.cache = {}
        
        # Initialize individual tools
        self.intent_classifier = IntentClassifier(self.bedrock, self.kb, self.cache)
        self.data_analyzer = DataAnalyzer(self.bedrock, self.kb)
        self.solver_selector = SolverSelectorTool()
        self.model_builder = ModelBuilder(self.bedrock, self.kb)
        self.optimization_solver = OptimizationSolver()
        self.explainability_tool = ExplainabilityTool(self.bedrock)
        self.simulation_tool = SimulationTool()
        self.validation_tool = ValidationTool(self.bedrock)
        self.workflow_validator = WorkflowValidator(self.validation_tool)
        
        logger.info("DcisionAI Tools v2.1 initialized with modular architecture")
    
    # ============================================================================
    # MAIN TOOL METHODS (Orchestrator Interface)
    # ============================================================================
    
    async def classify_intent(self, problem_description: str, context: Optional[str] = None) -> Dict[str, Any]:
        """Classify optimization problem intent"""
        return await self.intent_classifier.classify_intent(problem_description, context)
    
    async def analyze_data(self, problem_description: str, intent_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Analyze data readiness for optimization"""
        return await self.data_analyzer.analyze_data(problem_description, intent_data)
    
    async def select_solver(self, optimization_type: str, problem_size: Optional[Dict] = None, performance_requirement: str = "balanced") -> Dict[str, Any]:
        """Select appropriate solver for optimization problem"""
        return await self.solver_selector.select_solver(optimization_type, problem_size, performance_requirement)
    
    async def build_model(
        self,
        problem_description: str,
        intent_data: Optional[Dict] = None,
        data_analysis: Optional[Dict] = None,
        solver_selection: Optional[Dict] = None,
        max_retries: int = 2,
        validate_output: bool = True
    ) -> Dict[str, Any]:
        """Build optimization model with 7-step reasoning using Qwen 30B"""
        # Build the model
        model_result = await self.model_builder.build_model(
            problem_description, intent_data, data_analysis, solver_selection, max_retries
        )
        
        # Smart gating: Validate critical tool output
        if validate_output and model_result.get("status") == "success":
            validation = await self.workflow_validator.validate_workflow_step(
                problem_description, "build_model_tool", model_result
            )
            
            # Add validation results to output
            model_result["validation"] = validation
            
            # Block workflow if critical validation fails
            if validation.get("should_block_workflow", False):
                logger.error(f"Model building failed validation: {validation.get('error', 'Unknown validation error')}")
                return {
                    "status": "validation_failed",
                    "step": "model_building",
                    "error": f"Model validation failed: {validation.get('error', 'Trust score too low')}",
                    "validation": validation,
                    "original_result": model_result
                }
            else:
                logger.info(f"Model building passed validation (trust score: {validation.get('trust_score', 0.0):.2f})")
        
        return model_result
    
    async def solve_optimization(
        self,
        problem_description: str,
        intent_data: Optional[Dict] = None,
        data_analysis: Optional[Dict] = None,
        model_building: Optional[Dict] = None,
        validate_output: bool = True
    ) -> Dict[str, Any]:
        """Solve optimization problem using real solver"""
        # Solve the optimization
        solve_result = await self.optimization_solver.solve_optimization(
            problem_description, intent_data, data_analysis, model_building
        )
        
        # Smart gating: Validate critical tool output
        if validate_output and solve_result.get("status") == "success":
            # Extract model spec from model_building for validation
            model_spec = None
            if model_building and "result" in model_building:
                model_spec = model_building["result"]
            
            validation = await self.workflow_validator.validate_workflow_step(
                problem_description, "solve_optimization_tool", solve_result, model_spec
            )
            
            # Add validation results to output
            solve_result["validation"] = validation
            
            # Block workflow if critical validation fails
            if validation.get("should_block_workflow", False):
                logger.error(f"Optimization solving failed validation: {validation.get('error', 'Unknown validation error')}")
                return {
                    "status": "validation_failed",
                    "step": "optimization_solution",
                    "error": f"Optimization validation failed: {validation.get('error', 'Trust score too low')}",
                    "validation": validation,
                    "original_result": solve_result
                }
            else:
                logger.info(f"Optimization solving passed validation (trust score: {validation.get('trust_score', 0.0):.2f})")
        
        return solve_result
    
    async def explain_optimization(
        self,
        problem_description: str,
        intent_data: Optional[Dict] = None,
        data_analysis: Optional[Dict] = None,
        model_building: Optional[Dict] = None,
        optimization_solution: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Explain optimization results to business stakeholders"""
        return await self.explainability_tool.explain_optimization(
            problem_description, intent_data, data_analysis, model_building, optimization_solution
        )
    
    async def simulate_scenarios(
        self,
        problem_description: str,
        optimization_solution: Optional[Dict] = None,
        scenario_parameters: Optional[Dict] = None,
        simulation_type: str = "monte_carlo",
        num_trials: int = 10000
    ) -> Dict[str, Any]:
        """Simulate different scenarios for optimization analysis"""
        return await self.simulation_tool.simulate_scenarios(
            problem_description, optimization_solution, scenario_parameters, simulation_type, num_trials
        )

    async def validate_tool_output(
        self,
        problem_description: str,
        tool_name: str,
        tool_output: Dict[str, Any],
        model_spec: Optional[Dict] = None,
        validation_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """Validate any tool's output for correctness and business logic"""
        return await self.validation_tool.validate_tool_output(
            problem_description, tool_name, tool_output, model_spec, validation_type
        )

    async def validate_complete_workflow(
        self,
        problem_description: str,
        workflow_results: Dict[str, Any],
        model_spec: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Validate a complete optimization workflow"""
        return await self.workflow_validator.validate_complete_workflow(
            problem_description, workflow_results, model_spec
        )
    
    # ============================================================================
    # WORKFLOW METHODS
    # ============================================================================
    
    async def get_workflow_templates(self) -> Dict[str, Any]:
        """Get available workflow templates"""
        try:
            return {
                "status": "success",
                "workflow_templates": self.workflow_manager.get_all_workflows(),
                "total_workflows": 21
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def execute_workflow(self, industry: str, workflow_id: str, user_input: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute complete optimization workflow"""
        try:
            problem_desc = f"{workflow_id} for {industry}"
            
            intent_result = await self.classify_intent(problem_desc, industry)
            data_result = await self.analyze_data(problem_desc, intent_result.get('result'))
            model_result = await self.build_model(problem_desc, intent_result.get('result'), data_result.get('result'))
            solve_result = await self.solve_optimization(problem_desc, intent_result.get('result'), data_result.get('result'), model_result)
            explain_result = await self.explain_optimization(problem_desc, intent_result.get('result'), data_result.get('result'), model_result, solve_result.get('result'))
            
            return {
                "status": "success",
                "workflow_type": workflow_id,
                "industry": industry,
                "steps_completed": 5,
                "results": {
                    "intent_classification": intent_result,
                    "data_analysis": data_result,
                    "model_building": model_result,
                    "optimization_solution": solve_result,
                    "explainability": explain_result
                }
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}


# ============================================================================
# GLOBAL INSTANCE & WRAPPERS
# ============================================================================

_tools_instance = None

def get_tools() -> DcisionAITools:
    """Get global tools instance"""
    global _tools_instance
    if _tools_instance is None:
        _tools_instance = DcisionAITools()
    return _tools_instance

# Tool wrapper functions for backward compatibility
async def classify_intent(problem_description: str, context: Optional[str] = None) -> Dict[str, Any]:
    return await get_tools().classify_intent(problem_description, context)

async def analyze_data(problem_description: str, intent_data: Optional[Dict] = None) -> Dict[str, Any]:
    return await get_tools().analyze_data(problem_description, intent_data)

async def build_model(problem_description: str, intent_data: Optional[Dict] = None, data_analysis: Optional[Dict] = None, solver_selection: Optional[Dict] = None, validate_output: bool = True) -> Dict[str, Any]:
    return await get_tools().build_model(problem_description, intent_data, data_analysis, solver_selection, validate_output=validate_output)

async def solve_optimization(problem_description: str, intent_data: Optional[Dict] = None, data_analysis: Optional[Dict] = None, model_building: Optional[Dict] = None, validate_output: bool = True) -> Dict[str, Any]:
    return await get_tools().solve_optimization(problem_description, intent_data, data_analysis, model_building, validate_output=validate_output)

async def select_solver(optimization_type: str, problem_size: Optional[Dict] = None, performance_requirement: str = "balanced") -> Dict[str, Any]:
    return await get_tools().select_solver(optimization_type, problem_size, performance_requirement)

async def explain_optimization(problem_description: str, intent_data: Optional[Dict] = None, data_analysis: Optional[Dict] = None, model_building: Optional[Dict] = None, optimization_solution: Optional[Dict] = None) -> Dict[str, Any]:
    return await get_tools().explain_optimization(problem_description, intent_data, data_analysis, model_building, optimization_solution)

async def simulate_scenarios(problem_description: str, optimization_solution: Optional[Dict] = None, scenario_parameters: Optional[Dict] = None, simulation_type: str = "monte_carlo", num_trials: int = 10000) -> Dict[str, Any]:
    return await get_tools().simulate_scenarios(problem_description, optimization_solution, scenario_parameters, simulation_type, num_trials)

async def validate_tool_output(problem_description: str, tool_name: str, tool_output: Dict[str, Any], model_spec: Optional[Dict] = None, validation_type: str = "comprehensive") -> Dict[str, Any]:
    return await get_tools().validate_tool_output(problem_description, tool_name, tool_output, model_spec, validation_type)

async def validate_complete_workflow(problem_description: str, workflow_results: Dict[str, Any], model_spec: Optional[Dict] = None) -> Dict[str, Any]:
    return await get_tools().validate_complete_workflow(problem_description, workflow_results, model_spec)

async def get_workflow_templates() -> Dict[str, Any]:
    return await get_tools().get_workflow_templates()

async def execute_workflow(industry: str, workflow_id: str, user_input: Optional[Dict] = None) -> Dict[str, Any]:
    return await get_tools().execute_workflow(industry, workflow_id, user_input)
