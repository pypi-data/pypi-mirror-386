#!/usr/bin/env python3
"""
Optimization Solver Tool
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..models.model_spec import ModelSpec
from ..models.mathopt_solver import MathOptSolver
from ..core.validators import Validator

logger = logging.getLogger(__name__)


class OptimizationSolver:
    """Optimization solver for mathematical models"""
    
    def __init__(self):
        self.validator = Validator()
        self.mathopt_solver = MathOptSolver()
    
    async def solve_optimization(
        self,
        problem_description: str,
        intent_data: Optional[Dict] = None,
        data_analysis: Optional[Dict] = None,
        model_building: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Solve optimization problem using real solver"""
        try:
            # REQUIRE a real model from build_model_tool - no fallbacks!
            if not model_building or 'result' not in model_building:
                logger.error("No model provided - solve_optimization requires a real model from build_model_tool")
                return {
                    "status": "error",
                    "step": "optimization_solution",
                    "error": "No model provided - solve_optimization requires a real model from build_model_tool",
                    "message": "Please run build_model_tool first to create a mathematical model"
                }
            
            # Validate that we have a proper model structure
            model_result = model_building['result']
            
            # Check if this is an enhanced model builder result (placeholder format)
            if 'execution_result' in model_result:
                execution_result = model_result['execution_result']
                # Enhanced model builder provides placeholder - need to solve
                if execution_result.get('status') == 'ready_for_solving':
                    logger.info("Enhanced model builder detected - proceeding with MathOpt solving")
                    # Continue to MathOpt solving below
                elif execution_result.get('status') == 'success' and execution_result.get('result', {}).get('status') == 'optimal':
                    logger.info("Model already solved by Python Model Builder - returning results")
                    return {
                        "status": "success",
                        "step": "optimization_solution",
                        "timestamp": datetime.now().isoformat(),
                        "result": {
                            "solver_used": model_result.get('solver_used', 'Unknown'),
                            "model_type": model_result.get('model_type', 'Unknown'),
                            "variables_count": model_result.get('variables_count', 0),
                            "objective_value": execution_result['result']['objective_value'],
                            "variables": execution_result['result']['variables'],
                            "solve_time": execution_result['result'].get('solve_time'),
                            "status": execution_result['result']['status']
                        },
                        "message": f"Model solved successfully using {model_result.get('solver_used', 'Unknown')} solver"
                    }
                else:
                    logger.error("Python Model Builder execution failed")
                    return {
                        "status": "error",
                        "step": "optimization_solution",
                        "error": "Python Model Builder execution failed",
                        "message": "Model building and solving failed"
                    }
            
            # Check old JSON model format
            elif not model_result.get('variables') or not model_result.get('constraints') or not model_result.get('objective'):
                logger.error("Invalid model structure - missing required components")
                return {
                    "status": "error",
                    "step": "optimization_solution",
                    "error": "Invalid model structure - missing variables, constraints, or objective",
                    "message": "Model must contain variables, constraints, and objective"
                }
            
            logger.info("Using real model from build_model_tool for optimization")
            logger.info(f"Model has {len(model_result.get('variables', []))} variables and {len(model_result.get('constraints', []))} constraints")
            
            # Use MathOpt solver for real OR-Tools solving with retry mechanism
            mathopt_solver = MathOptSolver()
            solver_result = await self._solve_with_retry(mathopt_solver, model_result, problem_description)
            
            # Validate the optimization results with reasonable criteria
            model_spec = ModelSpec.from_dict(model_result)
            validation = self.validator.validate(solver_result, model_spec)
            
            # Check if result is valid (including infeasible as valid)
            solver_status = solver_result.get('status', 'unknown')
            is_valid_result = solver_status in ['optimal', 'infeasible', 'unbounded', 'feasible']
            
            # Only fail if result is truly nonsensical
            is_nonsensical = (
                solver_status not in ['optimal', 'infeasible', 'unbounded', 'feasible', 'unknown'] or
                (solver_status == 'optimal' and not solver_result.get('optimal_values')) or
                (solver_status == 'optimal' and solver_result.get('objective_value') is None)
            )
            
            if not is_valid_result:
                logger.warning(f"Invalid solver status: {solver_status}")
            elif validation['errors'] and solver_status == 'optimal':
                logger.warning(f"Validation errors for optimal solution: {validation['errors']}")
            else:
                logger.info(f"✅ Valid optimization result: {solver_status}")
            
            solver_result['validation'] = validation
            solver_result['is_valid_result'] = is_valid_result
            solver_result['is_nonsensical'] = is_nonsensical
            
            # Return success for valid results (including infeasible)
            result = {
                "status": "success" if is_valid_result and not is_nonsensical else "error",
                "step": "optimization_solution",
                "timestamp": datetime.now().isoformat(),
                "result": solver_result,
                "message": f"Solved with real OR-Tools solver: {solver_status} (validation: {'passed' if validation['is_valid'] else 'warnings'})"
            }
            
            # Add validation feedback for low trust scores
            # Calculate trust score from validation results
            trust_score = 0.5  # Default trust score
            if validation.get('is_valid'):
                trust_score = 0.8
            elif validation.get('errors'):
                trust_score = 0.3
            elif validation.get('warnings'):
                trust_score = 0.6
            
            if trust_score < 0.6 and trust_score >= 0.25:  # Between threshold and 0.6
                result["validation_feedback"] = {
                    "trust_score": trust_score,
                    "score_category": self._categorize_trust_score(trust_score),
                    "issues": validation.get('errors', []),
                    "warnings": validation.get('warnings', []),
                    "recommendations": self._get_validation_recommendations(trust_score, validation)
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Solve error: {e}")
            return {"status": "error", "step": "optimization_solution", "error": str(e)}
    
    async def _solve_with_retry(self, mathopt_solver: MathOptSolver, model_result: Dict[str, Any], problem_description: str) -> Dict[str, Any]:
        """Solve with retry mechanism using different model types"""
        original_model_type = model_result.get('model_type', 'linear_programming')
        
        # Define retry strategies based on problem type
        retry_strategies = self._get_retry_strategies(original_model_type, problem_description)
        
        for attempt, (model_type, solver_type, description) in enumerate(retry_strategies):
            try:
                logger.info(f"🔄 Retry attempt {attempt + 1}: {description}")
                
                # Create modified model with new type
                modified_model = model_result.copy()
                modified_model['model_type'] = model_type
                
                # Solve with modified model
                solver_result = mathopt_solver.solve_model(modified_model)
                
                # Check if solve was successful
                solver_status = solver_result.get('status', 'unknown')
                if solver_status in ['optimal', 'infeasible', 'unbounded', 'feasible']:
                    logger.info(f"✅ Retry successful with {model_type} model using {solver_type} solver")
                    solver_result['retry_info'] = {
                        'attempt': attempt + 1,
                        'model_type_override': model_type,
                        'solver_used': solver_type,
                        'description': description,
                        'original_model_type': original_model_type
                    }
                    return solver_result
                else:
                    logger.warning(f"⚠️ Retry {attempt + 1} failed with status: {solver_status}")
                    
            except Exception as e:
                logger.warning(f"⚠️ Retry {attempt + 1} failed with exception: {e}")
                continue
        
        # If all retries failed, return the original result
        logger.error("❌ All retry attempts failed")
        return mathopt_solver.solve_model(model_result)
    
    def _get_retry_strategies(self, original_model_type: str, problem_description: str) -> List[tuple]:
        """Get retry strategies based on original model type and problem description"""
        strategies = []
        
        # Portfolio optimization specific strategies
        if 'portfolio' in problem_description.lower() or 'investment' in problem_description.lower():
            if 'quadratic' in original_model_type.lower():
                # Try linear programming for portfolio optimization
                strategies.append(('linear_programming', 'GLOP', 'Linear programming approach for portfolio optimization'))
                strategies.append(('mixed_integer_linear_programming', 'CP_SAT', 'Mixed integer linear programming for portfolio optimization'))
            elif 'linear' in original_model_type.lower():
                # Try mixed integer if linear fails
                strategies.append(('mixed_integer_linear_programming', 'CP_SAT', 'Mixed integer linear programming for portfolio optimization'))
                strategies.append(('quadratic_programming', 'GLOP', 'Quadratic programming with GLOP fallback'))
        
        # General optimization strategies
        elif 'quadratic' in original_model_type.lower():
            # Try linear programming if quadratic fails
            strategies.append(('linear_programming', 'GLOP', 'Linear programming fallback'))
            strategies.append(('mixed_integer_linear_programming', 'CP_SAT', 'Mixed integer linear programming fallback'))
        
        elif 'linear' in original_model_type.lower():
            # Try mixed integer if linear fails
            strategies.append(('mixed_integer_linear_programming', 'CP_SAT', 'Mixed integer linear programming fallback'))
            strategies.append(('quadratic_programming', 'GLOP', 'Quadratic programming with GLOP fallback'))
        
        elif 'mixed_integer' in original_model_type.lower():
            # Try linear if mixed integer fails
            strategies.append(('linear_programming', 'GLOP', 'Linear programming fallback'))
            strategies.append(('quadratic_programming', 'GLOP', 'Quadratic programming with GLOP fallback'))
        
        # Always try the original type as final fallback
        strategies.append((original_model_type, 'GLOP', f'Original {original_model_type} with GLOP fallback'))
        
        return strategies
    
    def _categorize_trust_score(self, trust_score: float) -> str:
        """Categorize trust score into user-friendly terms"""
        if trust_score >= 0.8:
            return "excellent"
        elif trust_score >= 0.6:
            return "good"
        elif trust_score >= 0.4:
            return "fair"
        elif trust_score >= 0.2:
            return "poor"
        else:
            return "critical"
    
    def _get_validation_recommendations(self, trust_score: float, validation: Dict[str, Any]) -> List[str]:
        """Get specific recommendations based on validation results"""
        recommendations = []
        
        # General recommendations based on trust score
        if trust_score < 0.4:
            recommendations.append("Consider reviewing the entire model formulation")
            recommendations.append("Verify all mathematical expressions are correct")
        elif trust_score < 0.5:
            recommendations.append("Check for numerical precision issues")
            recommendations.append("Verify constraint tolerances")
        
        # Specific recommendations based on validation errors
        errors = validation.get('errors', [])
        warnings = validation.get('warnings', [])
        
        if any('constraint' in str(error).lower() for error in errors):
            recommendations.append("Review constraint formulations for mathematical accuracy")
        
        if any('objective' in str(error).lower() for error in errors):
            recommendations.append("Verify objective function formulation and coefficients")
        
        if any('variable' in str(error).lower() for error in errors):
            recommendations.append("Check variable bounds and types")
        
        if warnings:
            recommendations.append("Review validation warnings for potential improvements")
        
        return recommendations


async def solve_optimization_tool(
    problem_description: str,
    intent_data: Optional[Dict] = None,
    data_analysis: Optional[Dict] = None,
    model_building: Optional[Dict] = None
) -> Dict[str, Any]:
    """Tool wrapper for optimization solving"""
    # This would be called from the main tools orchestrator
    # For now, return a placeholder
    return {"status": "error", "error": "Tool not initialized"}
