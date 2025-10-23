#!/usr/bin/env python3
"""
Test Updated Tools in Main MCP Server
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
    solve_optimization
)

async def test_updated_tools():
    """Test the updated tools in the main mcp-server directory"""
    
    print("🧪 Testing Updated Tools in Main MCP Server")
    print("=" * 60)
    
    # Test case
    problem_description = "I need to optimize my investment portfolio with $100,000 across 5 different stocks, maximizing returns while keeping risk below 10% and ensuring no single stock exceeds 20% of the portfolio."
    
    print(f"Problem: {problem_description}")
    print("=" * 60)
    
    try:
        # Step 1: Intent Classification
        print(f"\n🔍 Step 1: Intent Classification...")
        intent_result = await classify_intent(problem_description)
        intent_data = intent_result.get('result', {})
        print(f"✅ Intent: {intent_data.get('intent', 'unknown')}")
        print(f"✅ Industry: {intent_data.get('industry', 'unknown')}")
        print(f"✅ Use Case: {intent_data.get('matched_use_case', 'unknown')}")
        print(f"✅ Method: {intent_result.get('method', 'unknown')}")
        
        # Step 2: Data Analysis
        print(f"\n📊 Step 2: Data Analysis...")
        data_result = await analyze_data(problem_description, intent_data)
        data_analysis = data_result.get('result', {})
        print(f"✅ Data Readiness: {data_analysis.get('readiness_score', 0.0):.1%}")
        print(f"✅ Data Quality: {data_analysis.get('data_quality', 'unknown')}")
        print(f"✅ Simulated Data: {len(data_analysis.get('simulated_data', {}).get('variables', {}))} variables")
        
        # Step 3: Solver Selection
        print(f"\n⚙️ Step 3: Solver Selection...")
        solver_result = await select_solver(
            optimization_type=intent_data.get('optimization_type', 'linear_programming'),
            problem_size={"num_variables": 5, "num_constraints": 8},
            performance_requirement="balanced"
        )
        solver_data = solver_result.get('result', {})
        print(f"✅ Selected Solver: {solver_data.get('selected_solver', 'unknown')}")
        
        # Step 4: Enhanced Model Building
        print(f"\n🧮 Step 4: Enhanced Model Building...")
        model_result = await build_model(
            problem_description=problem_description,
            intent_data=intent_data,
            data_analysis=data_analysis,
            solver_selection=solver_data
        )
        
        if model_result.get('status') != 'success':
            print(f"❌ Model building failed: {model_result.get('error', 'unknown')}")
            return
        
        model_data = model_result.get('result', {})
        print(f"✅ Model Status: {model_result.get('status')}")
        print(f"✅ Model Type: {model_data.get('model_type', 'unknown')}")
        print(f"✅ Variables: {len(model_data.get('variables', []))}")
        print(f"✅ Constraints: {len(model_data.get('constraints', []))}")
        print(f"✅ Recommended Solver: {model_data.get('recommended_solver', 'unknown')}")
        
        # Step 5: Model Solving
        print(f"\n⚡ Step 5: Model Solving...")
        solve_result = await solve_optimization(
            problem_description=problem_description,
            intent_data=intent_data,
            data_analysis=data_analysis,
            model_building=model_result
        )
        
        if solve_result.get('status') == 'success':
            solve_data = solve_result.get('result', {})
            print(f"✅ Solve Status: {solve_result.get('status')}")
            print(f"✅ Solver Status: {solve_data.get('status', 'unknown')}")
            print(f"✅ Objective Value: {solve_data.get('objective_value', 'unknown')}")
            
            # Check for validation feedback
            validation_feedback = solve_result.get('validation_feedback')
            if validation_feedback:
                print(f"\n📊 VALIDATION FEEDBACK:")
                print(f"   Trust Score: {validation_feedback.get('trust_score', 0.0):.2f}")
                print(f"   Score Category: {validation_feedback.get('score_category', 'unknown')}")
                print(f"   Issues: {len(validation_feedback.get('issues', []))}")
                print(f"   Recommendations: {len(validation_feedback.get('recommendations', []))}")
            else:
                print(f"✅ No validation feedback needed - trust score is good")
        else:
            print(f"❌ Solving failed: {solve_result.get('error', 'unknown')}")
            print(f"   Error details: {solve_result.get('message', 'No details')}")
        
        # Summary
        print(f"\n{'='*60}")
        print("🎯 UPDATED TOOLS TEST SUMMARY")
        print(f"{'='*60}")
        
        intent_success = intent_result.get('status') == 'success'
        data_success = data_result.get('status') == 'success'
        model_success = model_result.get('status') == 'success'
        solve_success = solve_result.get('status') == 'success'
        
        print(f"Intent Classification: {'✅ SUCCESS' if intent_success else '❌ FAILURE'}")
        print(f"Data Analysis: {'✅ SUCCESS' if data_success else '❌ FAILURE'}")
        print(f"Model Building: {'✅ SUCCESS' if model_success else '❌ FAILURE'}")
        print(f"Model Solving: {'✅ SUCCESS' if solve_success else '❌ FAILURE'}")
        
        if intent_success and data_success and model_success and solve_success:
            print(f"\n🎉 All updated tools are working correctly!")
            print(f"✅ Enhanced Intent Classification with KB integration")
            print(f"✅ Enhanced Data Analysis with simulated data generation")
            print(f"✅ Enhanced Model Building with 7-step reasoning")
            print(f"✅ Enhanced Solving with validation feedback")
        else:
            print(f"\n⚠️ Some tools need attention:")
            if not intent_success:
                print(f"   - Intent Classification: {intent_result.get('error', 'unknown')}")
            if not data_success:
                print(f"   - Data Analysis: {data_result.get('error', 'unknown')}")
            if not model_success:
                print(f"   - Model Building: {model_result.get('error', 'unknown')}")
            if not solve_success:
                print(f"   - Model Solving: {solve_result.get('error', 'unknown')}")
        
        print(f"\n🎉 Test Complete!")
        print(f"Updated Tools: {'✅ Working' if all([intent_success, data_success, model_success, solve_success]) else '⚠️ Needs Attention'}")
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_updated_tools())
