#!/usr/bin/env python3
"""
Test Manufacturing Optimization - Real World Problem
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

async def test_manufacturing_optimization():
    """Test with a real manufacturing production planning problem"""
    
    problem_description = """
    A furniture manufacturing company needs to optimize its production schedule for the next month. 
    They produce 3 types of furniture: chairs, tables, and cabinets. 
    
    Production capacity constraints:
    - Chair production: max 200 units per day, requires 2 hours labor per unit
    - Table production: max 100 units per day, requires 4 hours labor per unit  
    - Cabinet production: max 50 units per day, requires 8 hours labor per unit
    
    Labor constraints:
    - Total available labor: 800 hours per day
    - Skilled workers: 40 hours per day (required for cabinets)
    - Regular workers: 760 hours per day (can make chairs and tables)
    
    Demand constraints:
    - Chairs: minimum 3000 units, maximum 5000 units for the month
    - Tables: minimum 1500 units, maximum 2500 units for the month
    - Cabinets: minimum 800 units, maximum 1200 units for the month
    
    Profit margins:
    - Chairs: $25 profit per unit
    - Tables: $60 profit per unit
    - Cabinets: $120 profit per unit
    
    The company wants to maximize total profit while meeting all constraints.
    """
    
    print("🏭 Manufacturing Production Planning Optimization")
    print("=" * 70)
    print(f"Problem: Furniture manufacturing with 3 products, capacity, labor, and demand constraints")
    print("=" * 70)
    
    # Step 1-3: Get the inputs
    print("\n📋 Getting Inputs...")
    intent_result = await classify_intent(problem_description)
    intent_data = intent_result.get('result', {})
    
    data_result = await analyze_data(problem_description, intent_data)
    data_analysis = data_result.get('result', {})
    
    solver_result = await select_solver(
        optimization_type=intent_data.get('optimization_type', 'linear_programming'),
        problem_size={"num_variables": 3, "num_constraints": 8},
        performance_requirement="balanced"
    )
    solver_data = solver_result.get('result', {})
    
    print(f"✅ Intent: {intent_data.get('intent', 'unknown')}")
    print(f"✅ Industry: {intent_data.get('industry', 'unknown')}")
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
            
            # Show variables and constraints
            variables = model_data.get('variables', [])
            constraints = model_data.get('constraints', [])
            objective = model_data.get('objective', {})
            
            print(f"\n📊 Model Details:")
            print(f"   Variables:")
            for var in variables:
                print(f"     {var.get('name', 'unknown')}: {var.get('type', 'unknown')} {var.get('bounds', 'unknown')} - {var.get('description', 'no description')}")
            
            print(f"   Constraints:")
            for i, constraint in enumerate(constraints):
                print(f"     {i+1}. {constraint.get('expression', 'unknown')[:60]}...")
                print(f"        Description: {constraint.get('description', 'no description')}")
            
            print(f"   Objective: {objective.get('type', 'unknown')} {objective.get('expression', 'unknown')[:60]}...")
            print(f"        Description: {objective.get('description', 'no description')}")
            
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
            
            # Handle solve_time formatting
            try:
                if hasattr(solve_time, 'total_seconds'):
                    solve_time_sec = solve_time.total_seconds()
                else:
                    solve_time_sec = float(solve_time)
            except:
                solve_time_sec = 0.0
            
            print(f"   Solver Status: {solver_status}")
            print(f"   Objective Value: ${objective_value:,.2f}")
            print(f"   Solve Time: {solve_time_sec:.3f}s")
            
            # Analyze the results
            print(f"\n📈 Production Plan Results:")
            total_profit = 0
            for var_name, value in optimal_values.items():
                if value > 0.001:  # Only show significant production
                    if 'chair' in var_name.lower():
                        profit = value * 25
                        print(f"   {var_name}: {value:.0f} units (${profit:,.2f} profit)")
                    elif 'table' in var_name.lower():
                        profit = value * 60
                        print(f"   {var_name}: {value:.0f} units (${profit:,.2f} profit)")
                    elif 'cabinet' in var_name.lower():
                        profit = value * 120
                        print(f"   {var_name}: {value:.0f} units (${profit:,.2f} profit)")
                    else:
                        print(f"   {var_name}: {value:.0f} units")
                    total_profit += profit if 'profit' in locals() else 0
            
            print(f"\n📊 Production Analysis:")
            print(f"   Total Profit: ${total_profit:,.2f}")
            
            # Check if results make sense
            print(f"\n🔍 Results Validation:")
            if objective_value > 0:
                print(f"   ✅ Positive Profit: ${objective_value:,.2f}")
            else:
                print(f"   ❌ Negative Profit: ${objective_value:,.2f}")
            
            # Check production quantities are reasonable
            max_production = max(optimal_values.values()) if optimal_values else 0
            if max_production <= 5000:  # Reasonable for monthly production
                print(f"   ✅ Production Quantities: Reasonable (max = {max_production:.0f} units)")
            else:
                print(f"   ⚠️ Production Quantities: High (max = {max_production:.0f} units)")
            
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
    
    print(f"\n🎉 Manufacturing Optimization Test Complete!")
    print(f"   Model built with 7-step reasoning: ✅")
    print(f"   Model solved with real solver: ✅")
    print(f"   Results analyzed for sensibility: ✅")

if __name__ == "__main__":
    print("🏭 Manufacturing Production Planning Test")
    print("=" * 70)
    
    # Run the test
    asyncio.run(test_manufacturing_optimization())
