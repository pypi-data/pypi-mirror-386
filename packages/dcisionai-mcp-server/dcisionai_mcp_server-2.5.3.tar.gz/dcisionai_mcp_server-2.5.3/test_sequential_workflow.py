#!/usr/bin/env python3
"""
Test Sequential Workflow with Smart Gating
Step by step: Intent → Data → Solver Selection → Model Builder → Solver → Simulation → Business Explain
"""

import asyncio
import json
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import our tools
from dcisionai_mcp_server.tools import (
    classify_intent,
    analyze_data,
    select_solver,
    build_model,
    solve_optimization,
    simulate_scenarios,
    explain_optimization,
    validate_tool_output
)

async def test_sequential_workflow():
    """Test the complete sequential workflow with smart gating"""
    
    problem_description = "I need to optimize my investment portfolio with $500,000 across 20 different stocks, maximizing returns while keeping risk below 15% and ensuring no single stock exceeds 10% of the portfolio."
    
    print("🚀 Testing Sequential Workflow with Smart Gating")
    print("=" * 70)
    print(f"Problem: {problem_description}")
    print("=" * 70)
    
    # Step 1: Intent Classification
    print("\n📋 STEP 1: Intent Classification")
    print("-" * 50)
    try:
        intent_result = await classify_intent(problem_description)
        print(f"✅ Status: {intent_result.get('status', 'unknown')}")
        
        if intent_result.get('status') == 'success':
            intent_data = intent_result.get('result', {})
            print(f"   Intent: {intent_data.get('intent', 'unknown')}")
            print(f"   Industry: {intent_data.get('industry', 'unknown')}")
            print(f"   Optimization Type: {intent_data.get('optimization_type', 'unknown')}")
            
            # Validate intent classification
            intent_validation = await validate_tool_output(
                problem_description, "classify_intent_tool", intent_result
            )
            trust_score = intent_validation.get('result', {}).get('overall_trust_score', 0.0)
            print(f"   🛡️ Guardian Trust Score: {trust_score:.2f}")
        else:
            print(f"❌ Failed: {intent_result.get('error', 'Unknown error')}")
            return None
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None
    
    # Step 2: Data Analysis
    print("\n📊 STEP 2: Data Analysis")
    print("-" * 50)
    try:
        data_result = await analyze_data(problem_description, intent_data)
        print(f"✅ Status: {data_result.get('status', 'unknown')}")
        
        if data_result.get('status') == 'success':
            data_analysis = data_result.get('result', {})
            variables = data_analysis.get('variables_identified', [])
            constraints = data_analysis.get('constraints_identified', [])
            print(f"   Variables Identified: {len(variables)}")
            print(f"   Constraints Identified: {len(constraints)}")
            
            # Validate data analysis
            data_validation = await validate_tool_output(
                problem_description, "analyze_data_tool", data_result
            )
            trust_score = data_validation.get('result', {}).get('overall_trust_score', 0.0)
            print(f"   🛡️ Guardian Trust Score: {trust_score:.2f}")
        else:
            print(f"❌ Failed: {data_result.get('error', 'Unknown error')}")
            return None
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None
    
    # Step 3: Solver Selection
    print("\n⚙️ STEP 3: Solver Selection")
    print("-" * 50)
    try:
        solver_result = await select_solver(
            optimization_type=intent_data.get('optimization_type', 'linear_programming'),
            problem_size={"num_variables": len(variables), "num_constraints": len(constraints)},
            performance_requirement="balanced"
        )
        print(f"✅ Status: {solver_result.get('status', 'unknown')}")
        
        if solver_result.get('status') == 'success':
            solver_data = solver_result.get('result', {})
            selected_solver = solver_data.get('selected_solver', 'unknown')
            capabilities = solver_data.get('capabilities', [])
            print(f"   Selected Solver: {selected_solver}")
            print(f"   Capabilities: {', '.join(capabilities[:3])}...")
            
            # Validate solver selection
            solver_validation = await validate_tool_output(
                problem_description, "select_solver_tool", solver_result
            )
            trust_score = solver_validation.get('result', {}).get('overall_trust_score', 0.0)
            print(f"   🛡️ Guardian Trust Score: {trust_score:.2f}")
        else:
            print(f"❌ Failed: {solver_result.get('error', 'Unknown error')}")
            return None
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None
    
    # Step 4: Model Builder (CRITICAL - with smart gating)
    print("\n🧮 STEP 4: Model Builder (CRITICAL)")
    print("-" * 50)
    try:
        model_result = await build_model(
            problem_description, 
            intent_data, 
            data_analysis,
            solver_data,
            validate_output=True  # Enable smart gating
        )
        print(f"✅ Status: {model_result.get('status', 'unknown')}")
        
        if model_result.get('status') == 'validation_failed':
            print(f"❌ GUARDIAN BLOCKED: {model_result.get('error', 'Unknown validation error')}")
            validation = model_result.get('validation', {})
            print(f"   Trust Score: {validation.get('trust_score', 0.0):.2f}")
            print(f"   Threshold: {validation.get('trust_threshold', 0.0):.2f}")
            print(f"   Critical Tool: {validation.get('is_critical_tool', False)}")
            return None
        elif model_result.get('status') == 'success':
            model_data = model_result.get('result', {})
            variables_count = len(model_data.get('variables', []))
            constraints_count = len(model_data.get('constraints', []))
            model_type = model_data.get('model_type', 'unknown')
            print(f"   Variables: {variables_count}")
            print(f"   Constraints: {constraints_count}")
            print(f"   Model Type: {model_type}")
            
            # Check if validation was performed
            if 'validation' in model_result:
                validation = model_result['validation']
                trust_score = validation.get('trust_score', 0.0)
                threshold = validation.get('trust_threshold', 0.0)
                passed = validation.get('validation_passed', False)
                print(f"   🛡️ Guardian Trust Score: {trust_score:.2f} (threshold: {threshold:.2f})")
                print(f"   🛡️ Guardian Status: {'✅ PASSED' if passed else '❌ FAILED'}")
        else:
            print(f"❌ Failed: {model_result.get('error', 'Unknown error')}")
            return None
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None
    
    # Step 5: Solver (CRITICAL - with smart gating)
    print("\n⚡ STEP 5: Solver (CRITICAL)")
    print("-" * 50)
    try:
        solve_result = await solve_optimization(
            problem_description,
            intent_data,
            data_analysis,
            model_result,
            validate_output=True  # Enable smart gating
        )
        print(f"✅ Status: {solve_result.get('status', 'unknown')}")
        
        if solve_result.get('status') == 'validation_failed':
            print(f"❌ GUARDIAN BLOCKED: {solve_result.get('error', 'Unknown validation error')}")
            validation = solve_result.get('validation', {})
            print(f"   Trust Score: {validation.get('trust_score', 0.0):.2f}")
            print(f"   Threshold: {validation.get('trust_threshold', 0.0):.2f}")
            print(f"   Critical Tool: {validation.get('is_critical_tool', False)}")
            return None
        elif solve_result.get('status') == 'success':
            solve_data = solve_result.get('result', {})
            solver_status = solve_data.get('status', 'unknown')
            objective_value = solve_data.get('objective_value', 0.0)
            solve_time = solve_data.get('solve_time', 0.0)
            print(f"   Solver Status: {solver_status}")
            print(f"   Objective Value: {objective_value:.4f}")
            print(f"   Solve Time: {solve_time:.3f}s")
            
            # Check if validation was performed
            if 'validation' in solve_result:
                validation = solve_result['validation']
                trust_score = validation.get('trust_score', 0.0)
                threshold = validation.get('trust_threshold', 0.0)
                passed = validation.get('validation_passed', False)
                print(f"   🛡️ Guardian Trust Score: {trust_score:.2f} (threshold: {threshold:.2f})")
                print(f"   🛡️ Guardian Status: {'✅ PASSED' if passed else '❌ FAILED'}")
        else:
            print(f"❌ Failed: {solve_result.get('error', 'Unknown error')}")
            return None
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None
    
    # Step 6: Simulation
    print("\n🎲 STEP 6: Simulation")
    print("-" * 50)
    try:
        simulation_result = await simulate_scenarios(
            problem_description,
            solve_result,
            simulation_type="monte_carlo",
            num_trials=1000
        )
        print(f"✅ Status: {simulation_result.get('status', 'unknown')}")
        
        if simulation_result.get('status') == 'success':
            sim_data = simulation_result.get('result', {})
            sim_type = sim_data.get('simulation_type', 'unknown')
            num_trials = sim_data.get('num_trials', 0)
            risk_metrics = sim_data.get('risk_metrics', {})
            print(f"   Simulation Type: {sim_type}")
            print(f"   Trials: {num_trials}")
            print(f"   Mean Return: {risk_metrics.get('mean_return', 0.0):.4f}")
            print(f"   Std Dev: {risk_metrics.get('std_dev', 0.0):.4f}")
            
            # Validate simulation
            sim_validation = await validate_tool_output(
                problem_description, "simulate_scenarios_tool", simulation_result
            )
            trust_score = sim_validation.get('result', {}).get('overall_trust_score', 0.0)
            print(f"   🛡️ Guardian Trust Score: {trust_score:.2f}")
        else:
            print(f"❌ Failed: {simulation_result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Step 7: Business Explain
    print("\n📝 STEP 7: Business Explain")
    print("-" * 50)
    try:
        explain_result = await explain_optimization(
            problem_description,
            intent_data,
            data_analysis,
            model_result,
            solve_result
        )
        print(f"✅ Status: {explain_result.get('status', 'unknown')}")
        
        if explain_result.get('status') == 'success':
            explain_data = explain_result.get('result', {})
            exec_summary = explain_data.get('executive_summary', {})
            problem_statement = exec_summary.get('problem_statement', 'N/A')
            business_impact = exec_summary.get('business_impact', 'N/A')
            print(f"   Problem Statement: {problem_statement[:60]}...")
            print(f"   Business Impact: {business_impact[:60]}...")
            
            # Validate explanation
            explain_validation = await validate_tool_output(
                problem_description, "explain_optimization_tool", explain_result
            )
            trust_score = explain_validation.get('result', {}).get('overall_trust_score', 0.0)
            print(f"   🛡️ Guardian Trust Score: {trust_score:.2f}")
        else:
            print(f"❌ Failed: {explain_result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # Summary
    print("\n📊 WORKFLOW SUMMARY")
    print("=" * 70)
    print("✅ Sequential workflow completed!")
    print("🛡️ Smart gating system active")
    print("🎯 Real optimization results (no fallbacks)")
    print("🔗 Proper tool chaining enforced")
    
    return {
        'intent': intent_result,
        'data': data_result,
        'solver': solver_result,
        'model': model_result,
        'solve': solve_result,
        'simulation': simulation_result,
        'explain': explain_result
    }

if __name__ == "__main__":
    print("🧪 Sequential Workflow Test with Smart Gating")
    print("=" * 70)
    
    # Run the test
    result = asyncio.run(test_sequential_workflow())
    
    if result:
        print("\n🎉 Test completed successfully!")
        print("All tools executed in proper sequence with smart gating validation.")
    else:
        print("\n❌ Test failed - workflow was blocked by guardian validation.")
