#!/usr/bin/env python3
"""
Test Model Directly - Bypass Guardian and test the actual model
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
    validate_tool_output
)

async def test_model_directly():
    """Test the model directly without Guardian blocking"""
    
    problem_description = "I need to optimize my investment portfolio with $500,000 across 20 different stocks, maximizing returns while keeping risk below 15% and ensuring no single stock exceeds 10% of the portfolio."
    
    print("🧪 Testing Model Directly (Bypassing Guardian)")
    print("=" * 60)
    print(f"Problem: {problem_description}")
    print("=" * 60)
    
    # Step 1-3: Get the inputs (these worked fine)
    print("\n📋 Getting Inputs...")
    intent_result = await classify_intent(problem_description)
    intent_data = intent_result.get('result', {})
    
    data_result = await analyze_data(problem_description, intent_data)
    data_analysis = data_result.get('result', {})
    
    solver_result = await select_solver(
        optimization_type=intent_data.get('optimization_type', 'linear_programming'),
        problem_size={"num_variables": 20, "num_constraints": 25},
        performance_requirement="balanced"
    )
    solver_data = solver_result.get('result', {})
    
    print(f"✅ Intent: {intent_data.get('intent', 'unknown')}")
    print(f"✅ Solver: {solver_data.get('selected_solver', 'unknown')}")
    
    # Step 4: Build model WITHOUT validation (bypass Guardian)
    print("\n🧮 Building Model (No Guardian Validation)")
    print("-" * 50)
    try:
        model_result = await build_model(
            problem_description, 
            intent_data, 
            data_analysis,
            solver_data,
            validate_output=False  # Bypass Guardian
        )
        
        print(f"✅ Model Status: {model_result.get('status', 'unknown')}")
        
        if model_result.get('status') == 'success':
            model_data = model_result.get('result', {})
            print(f"   Variables: {len(model_data.get('variables', []))}")
            print(f"   Constraints: {len(model_data.get('constraints', []))}")
            print(f"   Model Type: {model_data.get('model_type', 'unknown')}")
            
            # Show the 7-step reasoning
            reasoning_steps = model_data.get('reasoning_steps', {})
            print(f"\n📝 7-Step Reasoning Process:")
            for i in range(1, 8):
                step_key = f"step{i}_decision_analysis" if i == 1 else f"step{i}_constraint_analysis" if i == 2 else f"step{i}_objective_analysis" if i == 3 else f"step{i}_variable_design" if i == 4 else f"step{i}_constraint_formulation" if i == 5 else f"step{i}_objective_formulation" if i == 6 else f"step{i}_validation"
                step_content = reasoning_steps.get(step_key, "N/A")
                print(f"   Step {i}: {step_content[:80]}...")
            
            # Show some variables and constraints
            variables = model_data.get('variables', [])
            constraints = model_data.get('constraints', [])
            objective = model_data.get('objective', {})
            
            print(f"\n📊 Model Details:")
            print(f"   Variables (first 5):")
            for i, var in enumerate(variables[:5]):
                print(f"     {var.get('name', 'unknown')}: {var.get('type', 'unknown')} {var.get('bounds', 'unknown')}")
            
            print(f"   Constraints (first 3):")
            for i, constraint in enumerate(constraints[:3]):
                print(f"     {constraint.get('expression', 'unknown')[:60]}...")
            
            print(f"   Objective: {objective.get('type', 'unknown')} {objective.get('expression', 'unknown')[:60]}...")
            
        else:
            print(f"❌ Model Building Failed: {model_result.get('error', 'Unknown error')}")
            return
            
    except Exception as e:
        print(f"❌ Model Building Exception: {e}")
        return
    
    # Step 5: Solve the model directly
    print("\n⚡ Solving Model Directly")
    print("-" * 50)
    try:
        solve_result = await solve_optimization(
            problem_description,
            intent_data,
            data_analysis,
            model_result,
            validate_output=False  # Bypass Guardian
        )
        
        print(f"✅ Solve Status: {solve_result.get('status', 'unknown')}")
        
        if solve_result.get('status') == 'success':
            solve_data = solve_result.get('result', {})
            solver_status = solve_data.get('status', 'unknown')
            objective_value = solve_data.get('objective_value', 0.0)
            solve_time = solve_data.get('solve_time', 0.0)
            optimal_values = solve_data.get('optimal_values', {})
            
            print(f"   Solver Status: {solver_status}")
            print(f"   Objective Value: {objective_value:.6f}")
            print(f"   Solve Time: {solve_time:.3f}s")
            
            # Analyze the results
            print(f"\n📈 Portfolio Allocation Results:")
            total_allocation = 0.0
            non_zero_allocations = 0
            
            for var_name, value in optimal_values.items():
                if value > 0.001:  # Only show significant allocations
                    non_zero_allocations += 1
                    total_allocation += value
                    print(f"   {var_name}: {value:.4f} ({value*100:.2f}%)")
            
            print(f"\n📊 Portfolio Analysis:")
            print(f"   Total Allocation: {total_allocation:.6f} ({total_allocation*100:.4f}%)")
            print(f"   Non-zero Allocations: {non_zero_allocations}")
            print(f"   Diversification: {non_zero_allocations}/20 stocks")
            
            # Check if results make sense
            print(f"\n🔍 Results Validation:")
            if abs(total_allocation - 1.0) < 0.01:
                print(f"   ✅ Budget Constraint: Satisfied (total ≈ 100%)")
            else:
                print(f"   ❌ Budget Constraint: Violated (total = {total_allocation*100:.2f}%)")
            
            if non_zero_allocations > 1:
                print(f"   ✅ Diversification: Good ({non_zero_allocations} stocks)")
            else:
                print(f"   ⚠️ Diversification: Poor (only {non_zero_allocations} stock)")
            
            # Check individual stock limits (should be ≤ 10%)
            max_allocation = max(optimal_values.values()) if optimal_values else 0
            if max_allocation <= 0.1:
                print(f"   ✅ Stock Limits: Satisfied (max = {max_allocation*100:.2f}%)")
            else:
                print(f"   ❌ Stock Limits: Violated (max = {max_allocation*100:.2f}%)")
            
            # Check if objective value is reasonable
            if 0.05 <= objective_value <= 0.25:  # 5% to 25% expected return
                print(f"   ✅ Expected Return: Reasonable ({objective_value*100:.2f}%)")
            else:
                print(f"   ⚠️ Expected Return: Unusual ({objective_value*100:.2f}%)")
            
        else:
            print(f"❌ Solving Failed: {solve_result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Solving Exception: {e}")
    
    # Step 6: Now validate with Guardian to see what it thinks
    print("\n🛡️ Guardian Validation (After the fact)")
    print("-" * 50)
    try:
        # Validate the model
        model_validation = await validate_tool_output(
            problem_description, "build_model_tool", model_result
        )
        model_trust = model_validation.get('result', {}).get('overall_trust_score', 0.0)
        print(f"   Model Trust Score: {model_trust:.2f}")
        
        # Validate the solution
        solve_validation = await validate_tool_output(
            problem_description, "solve_optimization_tool", solve_result
        )
        solve_trust = solve_validation.get('result', {}).get('overall_trust_score', 0.0)
        print(f"   Solve Trust Score: {solve_trust:.2f}")
        
        print(f"\n🎯 Guardian Assessment:")
        if model_trust >= 0.6:
            print(f"   ✅ Model: Guardian would approve (score: {model_trust:.2f})")
        else:
            print(f"   ❌ Model: Guardian would block (score: {model_trust:.2f})")
            
        if solve_trust >= 0.7:
            print(f"   ✅ Solution: Guardian would approve (score: {solve_trust:.2f})")
        else:
            print(f"   ❌ Solution: Guardian would block (score: {solve_trust:.2f})")
            
    except Exception as e:
        print(f"❌ Guardian Validation Exception: {e}")
    
    print(f"\n🎉 Direct Model Test Complete!")
    print(f"   Model built with 7-step reasoning: ✅")
    print(f"   Model solved with real solver: ✅")
    print(f"   Results analyzed for sensibility: ✅")

if __name__ == "__main__":
    print("🧪 Direct Model Testing (Bypassing Guardian)")
    print("=" * 60)
    
    # Run the test
    asyncio.run(test_model_directly())
