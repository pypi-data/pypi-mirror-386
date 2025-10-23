#!/usr/bin/env python3
"""
Individual Tool Testing Suite
Tests each optimization tool separately to validate functionality
"""

import asyncio
import logging
import time
from typing import Dict, Any

from dcisionai_mcp_server.tools import (
    classify_intent,
    analyze_data,
    select_solver,
    build_model,
    solve_optimization,
    explain_optimization,
    simulate_scenarios,
    validate_tool_output
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_individual_tools():
    """Test each tool individually with a simple manufacturing problem"""
    
    print("🔧 Individual Tool Testing Suite")
    print("=" * 60)
    
    # Simple manufacturing problem for testing
    problem = """
    I need to optimize production for 2 products over 3 days.
    
    Products:
    - Chairs: max 100 units/day, $20 profit/unit
    - Tables: max 50 units/day, $40 profit/unit
    
    Constraints:
    - Total labor: 200 hours/day
    - Chairs: 2 hours/unit
    - Tables: 4 hours/unit
    
    Objective: Maximize total profit over 3 days.
    """
    
    print(f"Problem: {problem.strip()}")
    print("=" * 60)
    
    # Test 1: Intent Classification
    print("\n🔍 TEST 1: Intent Classification")
    print("-" * 40)
    try:
        intent_result = await classify_intent(problem)
        print(f"✅ Status: {intent_result.get('status')}")
        if intent_result.get('status') == 'success':
            result = intent_result.get('result', {})
            print(f"   Intent: {result.get('intent', 'N/A')}")
            print(f"   Industry: {result.get('industry', 'N/A')}")
            print(f"   Optimization Type: {result.get('optimization_type', 'N/A')}")
        else:
            print(f"   Error: {intent_result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    
    # Test 2: Data Analysis
    print("\n📊 TEST 2: Data Analysis")
    print("-" * 40)
    try:
        data_result = await analyze_data(problem)
        print(f"✅ Status: {data_result.get('status')}")
        if data_result.get('status') == 'success':
            result = data_result.get('result', {})
            print(f"   Readiness Score: {result.get('readiness_score', 0):.1%}")
            print(f"   Data Quality: {result.get('data_quality', 'N/A')}")
            print(f"   Variables Identified: {len(result.get('variables_identified', []))}")
            print(f"   Constraints Identified: {len(result.get('constraints_identified', []))}")
            if result.get('mock_data'):
                mock_data = result['mock_data']
                print(f"   Mock Data Variables: {len(mock_data.get('variables', []))}")
                print(f"   Mock Data Constraints: {len(mock_data.get('constraints', []))}")
        else:
            print(f"   Error: {data_result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    
    # Test 3: Solver Selection
    print("\n⚙️ TEST 3: Solver Selection")
    print("-" * 40)
    try:
        solver_result = await select_solver(
            optimization_type="linear_programming",
            problem_size={"num_variables": 6, "num_constraints": 8},
            performance_requirement="balanced"
        )
        print(f"✅ Status: {solver_result.get('status')}")
        if solver_result.get('status') == 'success':
            result = solver_result.get('result', {})
            print(f"   Selected Solver: {result.get('selected_solver', 'N/A')}")
            print(f"   Capabilities: {result.get('capabilities', [])}")
            print(f"   Performance: {result.get('performance_metrics', {})}")
        else:
            print(f"   Error: {solver_result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    
    # Test 4: Model Building
    print("\n🧮 TEST 4: Model Building")
    print("-" * 40)
    try:
        model_result = await build_model(
            problem,
            intent_data={"intent": "production_planning", "industry": "manufacturing", "optimization_type": "linear_programming"},
            data_analysis={"readiness_score": 0.9, "mock_data": {"variables": [], "constraints": []}},
            solver_selection={"selected_solver": "GLOP", "capabilities": ["linear"]},
            validate_output=False
        )
        print(f"✅ Status: {model_result.get('status')}")
        if model_result.get('status') == 'success':
            result = model_result.get('result', {})
            print(f"   Model Type: {result.get('model_type', 'N/A')}")
            print(f"   Variables: {len(result.get('variables', []))}")
            print(f"   Constraints: {len(result.get('constraints', []))}")
            print(f"   Reasoning Steps: {len(result.get('reasoning_steps', {}))}")
            
            # Show first few variables and constraints
            variables = result.get('variables', [])
            if variables:
                print("   Sample Variables:")
                for i, var in enumerate(variables[:3]):
                    print(f"     {i+1}. {var.get('name', 'N/A')}: {var.get('type', 'N/A')} {var.get('bounds', 'N/A')}")
            
            constraints = result.get('constraints', [])
            if constraints:
                print("   Sample Constraints:")
                for i, const in enumerate(constraints[:3]):
                    print(f"     {i+1}. {const.get('expression', 'N/A')[:50]}...")
        else:
            print(f"   Error: {model_result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    
    # Test 5: Optimization Solving
    print("\n⚡ TEST 5: Optimization Solving")
    print("-" * 40)
    try:
        # Create a simple model for testing
        simple_model = {
            "variables": [
                {"name": "chairs_day1", "type": "continuous", "bounds": "0 to 100", "description": "Number of chairs produced on day 1"},
                {"name": "tables_day1", "type": "continuous", "bounds": "0 to 50", "description": "Number of tables produced on day 1"}
            ],
            "constraints": [
                {"expression": "chairs_day1 <= 100", "description": "Chair capacity"},
                {"expression": "tables_day1 <= 50", "description": "Table capacity"},
                {"expression": "2*chairs_day1 + 4*tables_day1 <= 200", "description": "Labor constraint"}
            ],
            "objective": {
                "type": "maximize",
                "expression": "20*chairs_day1 + 40*tables_day1",
                "description": "Total profit"
            }
        }
        
        solve_result = await solve_optimization(
            problem,
            intent_data={"intent": "production_planning"},
            data_analysis={"readiness_score": 0.9},
            model_building={"status": "success", "result": simple_model},
            validate_output=False
        )
        print(f"✅ Status: {solve_result.get('status')}")
        if solve_result.get('status') == 'success':
            result = solve_result.get('result', {})
            print(f"   Solver Status: {result.get('status', 'N/A')}")
            print(f"   Objective Value: ${result.get('objective_value', 0):.2f}")
            solve_time = result.get('solve_time', 0)
            try:
                if hasattr(solve_time, 'total_seconds'):
                    solve_time_sec = solve_time.total_seconds()
                else:
                    solve_time_sec = float(solve_time)
                print(f"   Solve Time: {solve_time_sec:.3f}s")
            except:
                print(f"   Solve Time: {solve_time}")
            print(f"   Solver Used: {result.get('solver', 'N/A')}")
            
            optimal_values = result.get('optimal_values', {})
            if optimal_values:
                print("   Optimal Values:")
                for var, value in optimal_values.items():
                    print(f"     {var}: {value:.2f}")
        else:
            print(f"   Error: {solve_result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    
    # Test 6: Business Explanation
    print("\n📈 TEST 6: Business Explanation")
    print("-" * 40)
    try:
        explanation_result = await explain_optimization(
            problem,
            intent_data={"intent": "production_planning"},
            data_analysis={"readiness_score": 0.9},
            model_building={"status": "success", "result": {"model_type": "linear_programming"}},
            optimization_solution={"status": "success", "result": {"objective_value": 2000, "status": "optimal"}}
        )
        print(f"✅ Status: {explanation_result.get('status')}")
        if explanation_result.get('status') == 'success':
            result = explanation_result.get('result', {})
            print(f"   Explanation Type: {result.get('explanation_type', 'N/A')}")
            print(f"   Key Insights: {len(result.get('key_insights', []))}")
            print(f"   Recommendations: {len(result.get('recommendations', []))}")
            
            insights = result.get('key_insights', [])
            if insights:
                print("   Sample Insights:")
                for i, insight in enumerate(insights[:2]):
                    print(f"     {i+1}. {insight[:60]}...")
        else:
            print(f"   Error: {explanation_result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    
    # Test 7: Scenario Simulation
    print("\n🎯 TEST 7: Scenario Simulation")
    print("-" * 40)
    try:
        simulation_result = await simulate_scenarios(
            problem,
            optimization_solution={"status": "success", "result": {"objective_value": 2000}},
            scenario_parameters={"demand_variation": 0.1, "cost_inflation": 0.05},
            simulation_type="monte_carlo",
            num_trials=100
        )
        print(f"✅ Status: {simulation_result.get('status')}")
        if simulation_result.get('status') == 'success':
            result = simulation_result.get('result', {})
            print(f"   Simulation Type: {result.get('simulation_type', 'N/A')}")
            print(f"   Number of Trials: {result.get('num_trials', 0)}")
            print(f"   Average Objective: ${result.get('average_objective', 0):.2f}")
            print(f"   Standard Deviation: ${result.get('std_deviation', 0):.2f}")
        else:
            print(f"   Error: {simulation_result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    
    # Test 8: Validation
    print("\n🛡️ TEST 8: Validation")
    print("-" * 40)
    try:
        validation_result = await validate_tool_output(
            problem,
            tool_name="test_tool",
            tool_output={"status": "success", "result": {"objective_value": 2000}},
            validation_type="comprehensive"
        )
        print(f"✅ Status: {validation_result.get('status')}")
        if validation_result.get('status') == 'success':
            result = validation_result.get('result', {})
            print(f"   Trust Score: {result.get('trust_score', 0):.2f}")
            print(f"   Should Block: {result.get('should_block_workflow', False)}")
            print(f"   Validation Type: {result.get('validation_type', 'N/A')}")
            
            issues = result.get('issues', [])
            if issues:
                print("   Issues Found:")
                for i, issue in enumerate(issues[:3]):
                    print(f"     {i+1}. {issue}")
        else:
            print(f"   Error: {validation_result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🎉 Individual Tool Testing Complete!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_individual_tools())
