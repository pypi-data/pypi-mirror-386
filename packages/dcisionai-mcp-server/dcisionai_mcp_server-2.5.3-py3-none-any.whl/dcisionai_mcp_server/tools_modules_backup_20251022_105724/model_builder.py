#!/usr/bin/env python3
"""
Model Building Tool
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from ..core.bedrock_client import BedrockClient
from ..core.knowledge_base import KnowledgeBase
from ..models.mathopt_builder import MathOptModelBuilder, HAS_MATHOPT
from ..utils.json_parser import parse_json
from ..utils.serialization import make_json_serializable

logger = logging.getLogger(__name__)


class ModelBuilder:
    """Model building for optimization problems"""
    
    def __init__(self, bedrock_client: BedrockClient, knowledge_base: KnowledgeBase):
        self.bedrock = bedrock_client
        self.kb = knowledge_base
    
    async def build_model(
        self,
        problem_description: str,
        intent_data: Optional[Dict] = None,
        data_analysis: Optional[Dict] = None,
        solver_selection: Optional[Dict] = None,
        max_retries: int = 2
    ) -> Dict[str, Any]:
        """Build optimization model with 7-step reasoning using Qwen 30B"""
        try:
            logger.info("Starting build_model function - using real Qwen 30B model building")
            
            # Use AI reasoning for ALL problem types - no hardcoded templates
            # Extract context from previous steps
            intent = intent_data.get('intent', 'unknown') if intent_data else 'unknown'
            industry = intent_data.get('industry', 'general') if intent_data else 'general'
            optimization_type = intent_data.get('optimization_type', 'linear') if intent_data else 'linear'
            variables = data_analysis.get('variables_identified', []) if data_analysis else []
            constraints = data_analysis.get('constraints_identified', []) if data_analysis else []
            
            # Extract solver information
            selected_solver = solver_selection.get('result', {}).get('selected_solver', 'GLOP') if solver_selection else 'GLOP'
            solver_capabilities = solver_selection.get('result', {}).get('capabilities', []) if solver_selection else []
            
            # Get knowledge base context and guidance
            kb_context = self.kb.search(problem_description) if self.kb else "No knowledge base available"
            kb_guidance = self.kb.get_problem_type_guidance(problem_description) if self.kb else ""
            
            # Get realistic mock data from data analysis
            mock_data_context = ""
            if data_analysis and data_analysis.get('result', {}).get('mock_data'):
                mock_data = data_analysis['result']['mock_data']
                mock_data_context = f"""
# REALISTIC MOCK DATA PROVIDED
Variables: {len(mock_data.get('variables', []))}
Constraints: {len(mock_data.get('constraints', []))}
Industry Benchmarks: {mock_data.get('benchmarks', {})}
Assumptions: {mock_data.get('assumptions', [])}

Use this realistic data to build your model with proper variable names, bounds, and constraints.
"""
            
            # Estimate problem size to detect combinatorial explosion
            estimated_vars = self._estimate_variable_count(problem_description)
            size_warning = ""
            if estimated_vars > 500:
                size_warning = f"""
# ⚠️ LARGE PROBLEM DETECTED
This problem requires approximately {estimated_vars} variables.
Use indexed notation (e.g., 'x[nurse][day][shift]') in your formulation.
Do not list all {estimated_vars} variables individually.
Focus on the mathematical structure rather than enumerating every variable.
"""
            
            validation_feedback = ""
            for attempt in range(max_retries):
                if attempt > 0:
                    retry_note = f"""RETRY {attempt + 1}: 
Previous attempt failed validation. Issues found:
{validation_feedback}
Please correct these issues in your response.

"""
                else:
                    retry_note = ""
                
                prompt = f"""{retry_note}You are a PhD-level optimization expert. Build a mathematical optimization model.

{mock_data_context}
{size_warning}
# CRITICAL RULES FOR MODEL BUILDING

## RULE 1: PROBLEM-SPECIFIC FORMULATION
- Read the problem description CAREFULLY
- Identify the SPECIFIC decisions to be made
- Formulate based on THESE specifics, not on general patterns

## RULE 2: VARIABLE DESIGN PRINCIPLES
- Define variables that represent the ACTUAL decisions
- For portfolio problems: If individual stocks are mentioned, create individual stock variables
- For production problems: If individual products are mentioned, create individual product variables
- NEVER oversimplify by grouping when individual items have different constraints

## RULE 2A: VARIABLE EXPANSION FOR COMPLEX PROBLEMS
- **Multi-dimensional problems**: If problem has multiple dimensions (e.g., sites × seasons × archaeologists), create variables for EACH combination
- **Time-based problems**: If problem spans multiple time periods, create variables for EACH time period
- **Resource allocation**: If problem involves multiple resources and multiple tasks, create variables for EACH resource-task combination
- **Scheduling problems**: If problem involves multiple entities (nurses, shifts, days), create variables for EACH entity-shift-day combination
- **Routing problems**: If problem involves multiple vehicles and multiple locations, create variables for EACH vehicle-location combination
- **Matrix problems**: If problem involves matrices (e.g., 5 vehicles × 20 customers), create variables for EACH matrix element
- **Example**: For "10 nurses × 7 days × 3 shifts", create 210 variables (x_nurse_day_shift), not 1 generic variable

## CRITICAL: NO MATHEMATICAL NOTATION IN VARIABLES
- **NEVER use Σ (summation) or mathematical notation in variable names**
- **NEVER use generic variables like x_n_d_s for multi-dimensional problems**
- **ALWAYS create individual variables for each combination**
- **Example**: For 3 nurses × 2 days × 2 shifts, create 12 variables:
  - x_nurse1_day1_shift1, x_nurse1_day1_shift2, x_nurse1_day2_shift1, x_nurse1_day2_shift2
  - x_nurse2_day1_shift1, x_nurse2_day1_shift2, x_nurse2_day2_shift1, x_nurse2_day2_shift2
  - x_nurse3_day1_shift1, x_nurse3_day1_shift2, x_nurse3_day2_shift1, x_nurse3_day2_shift2

## RULE 3: CONSTRAINT CAPTURE
- Capture ALL constraints mentioned in the problem
- If problem says "max 10% per stock", create individual stock variables
- If problem says "max 30% per sector", create sector-level constraints
- Ensure constraints can be mathematically enforced

## RULE 4: VALIDATION CHECK
Before finalizing your model, ask:
- Are ALL variables actually decision variables in this problem?
- Do ALL constraints reflect the actual limitations described?
- Does the objective match the actual goal stated?
- Can the model enforce ALL stated constraints?

# KNOWLEDGE BASE CONTEXT
{kb_context}

# PROBLEM-TYPE GUIDANCE
{kb_guidance}

PROBLEM DESCRIPTION:
{problem_description}

CONTEXT:
- Intent: {intent}
- Industry: {industry}
- Optimization Type: {optimization_type}
- Selected Solver: {selected_solver}
- Solver Capabilities: {', '.join(solver_capabilities)}

REQUIRED REASONING PROCESS:
You MUST show your work for each step. Do not skip any reasoning.

Step 1 - Decision Analysis:
What are the key decisions to be made in this problem? List each decision clearly.

Step 2 - Constraint Analysis:
What are the limitations and requirements? List each constraint clearly.

Step 3 - Objective Analysis:
What should be optimized? What is the goal?

Step 4 - Variable Design:
How do the decisions translate to mathematical variables? Define each variable with its meaning, type, and bounds.
**CRITICAL**: For multi-dimensional problems, create variables for EACH combination. Do not use generic variables.
**Example**: For "10 nurses × 7 days × 3 shifts", create 210 specific variables like x_nurse1_day1_shift1, x_nurse1_day1_shift2, etc.

**VARIABLE EXPANSION REQUIREMENTS**:
- Count the total number of combinations needed
- Create a separate variable for each combination
- Use descriptive names that include all dimensions
- List ALL variables explicitly in the variables array
- Do NOT use mathematical notation (Σ, etc.) in variable names
- Do NOT create generic variables like x_n_d_s

Step 5 - Constraint Formulation:
How do the limitations translate to mathematical constraints? Write each constraint as a mathematical expression.

**CRITICAL CONSTRAINT FORMATTING RULES**:
- Use SIMPLE constraint expressions: "x1 + x2 <= 100"
- NO complex mathematical notation or symbols
- NO ellipsis (...) or summation notation like "chairs_day1 + ... + chairs_day30"
- NO "for all i" or indexed constraints like "chairs_day[i] <= 200 for all i"
- NO sum() functions like "sum(chairs_day[i])"
- For multi-day problems, use simple addition: "chairs_day1 + chairs_day2 + chairs_day3 <= 5000"
- Each constraint must be parseable by a simple parser
- If you need to sum over multiple variables, list them explicitly: "var1 + var2 + var3 <= limit"

Step 6 - Objective Formulation:
How does the goal translate to an objective function? Write the mathematical expression.

**CRITICAL OBJECTIVE FORMATTING RULES**:
- Use SIMPLE objective expressions: "25*x1 + 60*x2 + 120*x3"
- NO complex mathematical notation or symbols
- NO ellipsis (...) or summation notation like "25*(chairs_day1 + ... + chairs_day30)"
- NO sum() functions like "sum(25*chairs_day[i])"
- For multi-day problems, use simple addition: "25*chairs_day1 + 25*chairs_day2 + 25*chairs_day3"
- Each term must be parseable by a simple parser
- If you need to sum over multiple variables, list them explicitly: "coeff1*var1 + coeff2*var2 + coeff3*var3"

Step 7 - Validation:
Verify that every variable is used in at least one constraint or the objective function.

# OUTPUT FORMAT
Provide JSON with this EXACT structure:

{{
  "reasoning_steps": {{
    "step1_decision_analysis": "List of key decisions identified",
    "step2_constraint_analysis": "List of limitations and requirements", 
    "step3_objective_analysis": "Goal and optimization target",
    "step4_variable_design": "How decisions translate to variables",
    "step5_constraint_formulation": "How limitations translate to constraints",
    "step6_objective_formulation": "How goal translates to objective function",
    "step7_validation": "Verification that all variables are used"
  }},
  "model_type": "{optimization_type}",
                "variables": [
    {{
      "name": "x1",
      "type": "continuous", 
      "bounds": "0 to 1",
      "description": "Allocation to stock 1 (fraction)"
    }}
  ],
  "objective": {{
    "type": "maximize",
    "expression": "0.12*x1 + 0.08*x2 + 0.10*x3 + 0.06*x4",
    "description": "Expected portfolio return"
  }},
                "constraints": [
    {{
      "expression": "x1 + x2 + x3 + x4 = 1",
      "description": "Total allocation must equal 100%"
    }}
  ],
                "model_complexity": "medium",
                "estimated_solve_time": 0.1,
  "mathematical_formulation": "Complete mathematical description based on reasoning steps",
  "validation_summary": {{
    "variables_defined": 4,
    "constraints_defined": 5,
    "objective_matches_problem": true,
    "model_is_feasible": true,
    "all_variables_used": true,
    "reasoning_completed": true
  }}
}}

Respond with valid JSON only:"""
                
                try:
                    resp = await self.bedrock.invoke("anthropic.claude-3-5-sonnet-20240620-v1:0", prompt, 8000)
                    result = parse_json(resp)
                except Exception as bedrock_error:
                    logger.error(f"Bedrock invoke error: {bedrock_error}")
                    # No fallback model - let validation handle the failure
                    result = {
                        "status": "error",
                        "error": f"AI model generation failed: {str(bedrock_error)}",
                        "should_retry": True
                    }
                
                # Debug output
                logger.info(f"Model building attempt {attempt+1}:")
                logger.info(f"Raw response length: {len(resp) if resp else 0}")
                logger.info(f"Raw response preview: {resp[:200] if resp else 'None'}...")
                logger.info(f"Generated result keys: {list(result.keys()) if result else 'None'}")
                if result and 'raw_response' in result:
                    logger.info(f"Raw response in result: {result['raw_response'][:200]}...")
                if result and 'reasoning_steps' in result:
                    logger.info(f"Reasoning steps keys: {list(result['reasoning_steps'].keys()) if result['reasoning_steps'] else 'None'}")
                
                if self._validate_model_v2(result):
                    # Auto-correct model type based on variable types
                    has_integer_vars = any(var.get('type') == 'integer' for var in result.get('variables', []))
                    has_binary_vars = any(var.get('type') == 'binary' for var in result.get('variables', []))
                    
                    if has_integer_vars or has_binary_vars:
                        if optimization_type == 'linear_programming':
                            result['model_type'] = 'mixed_integer_linear_programming'
                            logger.info("Auto-corrected model type: linear_programming -> mixed_integer_linear_programming (integer variables detected)")
                        elif optimization_type == 'quadratic_programming':
                            result['model_type'] = 'mixed_integer_quadratic_programming'
                            logger.info("Auto-corrected model type: quadratic_programming -> mixed_integer_quadratic_programming (integer variables detected)")
                    else:
                        result.setdefault('model_type', optimization_type)
                    
                    # Try to build MathOpt model if available
                    mathopt_result = None
                    if HAS_MATHOPT:
                        try:
                            mathopt_builder = MathOptModelBuilder()
                            mathopt_result = mathopt_builder.build_model_from_reasoning(result)
                            if mathopt_result.get('status') == 'success':
                                result['mathopt_model'] = mathopt_result
                                logger.info("MathOpt model built successfully")
                        except Exception as e:
                            logger.warning(f"MathOpt model building failed: {e}")
                    
                    # Clean result to ensure JSON serializability
                    cleaned_result = make_json_serializable(result)
                    
                    return {
                        "status": "success",
                        "step": "model_building",
                        "timestamp": datetime.now().isoformat(),
                        "result": cleaned_result,
                        "message": f"Model built with 7-step reasoning{' + MathOpt' if mathopt_result and mathopt_result.get('status') == 'success' else ''} (attempt {attempt+1})"
                    }
                else:
                    logger.warning(f"Model validation failed on attempt {attempt+1}")
                    # Generate validation feedback for retry
                    validation_feedback = self._get_validation_feedback(result)
                    logger.warning(f"Validation issues: {validation_feedback}")
                    
                    if result:
                        logger.warning(f"Missing keys: {[k for k in ['variables', 'constraints', 'objective', 'reasoning_steps'] if k not in result]}")
                        if 'reasoning_steps' in result:
                            required_steps = ['step1_decision_analysis', 'step2_constraint_analysis', 'step3_objective_analysis', 'step4_variable_design', 'step5_constraint_formulation', 'step6_objective_formulation', 'step7_validation']
                            missing_steps = [s for s in required_steps if s not in result['reasoning_steps']]
                            if missing_steps:
                                logger.warning(f"Missing reasoning steps: {missing_steps}")
            
            return {"status": "error", "step": "model_building", "error": "Validation failed after retries"}
            
        except Exception as e:
            logger.error(f"Model error: {e}")
            return {"status": "error", "step": "model_building", "error": str(e)}
    
    def _validate_model_v2(self, data: Dict) -> bool:
        """Enhanced validation for v2.0 models with 7-step reasoning."""
        # Basic structure validation
        if not data.get('variables') or not data.get('constraints') or not data.get('objective'):
            return False
        
        # Check for reasoning steps
        if not data.get('reasoning_steps'):
            return False
        
        # Check that all 7 steps are present
        required_steps = [
            'step1_decision_analysis', 'step2_constraint_analysis', 'step3_objective_analysis',
            'step4_variable_design', 'step5_constraint_formulation', 'step6_objective_formulation',
            'step7_validation'
        ]
        reasoning_steps = data.get('reasoning_steps', {})
        if not all(step in reasoning_steps for step in required_steps):
            return False
        
        # Variable usage validation
        var_names = {v['name'] for v in data['variables'] if isinstance(v, dict)}
        all_text = ' '.join(c.get('expression', '') for c in data['constraints'] if isinstance(c, dict))
        all_text += ' ' + data['objective'].get('expression', '') if isinstance(data.get('objective'), dict) else ''
        
        # All variables must be used
        if not all(name in all_text for name in var_names):
            return False
        
        # Check validation summary
        validation_summary = data.get('validation_summary', {})
        if not validation_summary.get('all_variables_used', False):
            return False
        
        return True

    def _get_validation_feedback(self, result: Dict) -> str:
        """Generate feedback for failed validation"""
        issues = []
        
        if not result.get('variables'):
            issues.append("- Missing 'variables' array")
        if not result.get('constraints'):
            issues.append("- Missing 'constraints' array")
        if not result.get('objective'):
            issues.append("- Missing 'objective' object")
        
        reasoning_steps = result.get('reasoning_steps', {})
        required_steps = ['step1_decision_analysis', 'step2_constraint_analysis', 
                          'step3_objective_analysis', 'step4_variable_design',
                          'step5_constraint_formulation', 'step6_objective_formulation',
                          'step7_validation']
        missing_steps = [s for s in required_steps if s not in reasoning_steps]
        if missing_steps:
            issues.append(f"- Missing reasoning steps: {', '.join(missing_steps)}")
        
        validation_summary = result.get('validation_summary', {})
        if not validation_summary.get('all_variables_used'):
            issues.append("- Not all variables are used in constraints or objective")
        
        # Check for unused variables
        if result.get('variables') and result.get('constraints') and result.get('objective'):
            var_names = {v['name'] for v in result['variables'] if isinstance(v, dict)}
            all_text = ' '.join(c.get('expression', '') for c in result['constraints'] if isinstance(c, dict))
            all_text += ' ' + result['objective'].get('expression', '') if isinstance(result.get('objective'), dict) else ''
            unused_vars = [name for name in var_names if name not in all_text]
            if unused_vars:
                issues.append(f"- Unused variables: {', '.join(unused_vars[:5])}{'...' if len(unused_vars) > 5 else ''}")
        
        return '\n'.join(issues) if issues else "Unknown validation issue"

    def _estimate_variable_count(self, problem_description: str) -> int:
        """Estimate number of variables needed to detect combinatorial explosion"""
        import re
        
        # Look for patterns like "10 nurses × 7 days × 3 shifts"
        multiplication_pattern = r'(\d+)\s*[×x*]\s*(\d+)\s*[×x*]\s*(\d+)'
        match = re.search(multiplication_pattern, problem_description, re.IGNORECASE)
        if match:
            return int(match.group(1)) * int(match.group(2)) * int(match.group(3))
        
        # Look for patterns like "100 nurses, 30 days, 3 shifts"
        numbers = re.findall(r'\b(\d+)\b', problem_description)
        if len(numbers) >= 3:
            # Take the largest 3 numbers and multiply them
            numbers = [int(n) for n in numbers if int(n) > 1]
            if len(numbers) >= 3:
                numbers.sort(reverse=True)
                return numbers[0] * numbers[1] * numbers[2]
        
        # Look for explicit variable counts
        var_count_pattern = r'(\d+)\s*(?:variables?|stocks?|items?|products?|nurses?|employees?|vehicles?|customers?)'
        matches = re.findall(var_count_pattern, problem_description, re.IGNORECASE)
        if matches:
            return max(int(m) for m in matches)
        
        # Default estimate based on problem complexity
        if any(word in problem_description.lower() for word in ['portfolio', 'investment', 'stocks']):
            return 20  # Typical portfolio size
        elif any(word in problem_description.lower() for word in ['schedule', 'nurse', 'employee', 'shift']):
            return 50  # Typical scheduling problem
        elif any(word in problem_description.lower() for word in ['production', 'manufacturing', 'factory']):
            return 30  # Typical production problem
        else:
            return 10  # Conservative default


async def build_model_tool(
    problem_description: str,
    intent_data: Optional[Dict] = None,
    data_analysis: Optional[Dict] = None,
    solver_selection: Optional[Dict] = None
) -> Dict[str, Any]:
    """Tool wrapper for model building"""
    # This would be called from the main tools orchestrator
    # For now, return a placeholder
    return {"status": "error", "error": "Tool not initialized"}
