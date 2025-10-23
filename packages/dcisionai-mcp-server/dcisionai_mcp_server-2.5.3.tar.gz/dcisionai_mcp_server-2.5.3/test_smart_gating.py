#!/usr/bin/env python3
"""
Test Smart Gating System - Step by Step Validation
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
    build_model,
    solve_optimization,
    explain_optimization,
    validate_tool_output,
    validate_complete_workflow
)

async def test_step_by_step():
    """Test the complete optimization workflow with smart gating"""
    
    problem_description = "I need to optimize my investment portfolio with $500,000 across 20 different stocks, maximizing returns while keeping risk below 15% and ensuring no single stock exceeds 10% of the portfolio."
    
    print("🚀 Testing Smart Gating System - Step by Step")
    print("=" * 60)
    print(f"Problem: {problem_description}")
    print("=" * 60)
    
    workflow_results = {}
    
    # Step 1: Intent Classification
    print("\n📋 STEP 1: Intent Classification")
    print("-" * 40)
    try:
        intent_result = await classify_intent(problem_description)
        print(f"✅ Intent Classification: {intent_result.get('status', 'unknown')}")
        print(f"   Intent: {intent_result.get('result', {}).get('intent', 'unknown')}")
        print(f"   Industry: {intent_result.get('result', {}).get('industry', 'unknown')}")
        workflow_results['classify_intent_tool'] = intent_result
        
        # Validate intent classification
        intent_validation = await validate_tool_output(
            problem_description, "classify_intent_tool", intent_result
        )
        print(f"   Guardian Trust Score: {intent_validation.get('result', {}).get('overall_trust_score', 0.0):.2f}")
        
    except Exception as e:
        print(f"❌ Intent Classification Failed: {e}")
        return
    
    # Step 2: Data Analysis
    print("\n📊 STEP 2: Data Analysis")
    print("-" * 40)
    try:
        data_result = await analyze_data(problem_description, intent_result.get('result', {}))
        print(f"✅ Data Analysis: {data_result.get('status', 'unknown')}")
        print(f"   Variables Identified: {len(data_result.get('result', {}).get('variables_identified', []))}")
        print(f"   Constraints Identified: {len(data_result.get('result', {}).get('constraints_identified', []))}")
        workflow_results['analyze_data_tool'] = data_result
        
        # Validate data analysis
        data_validation = await validate_tool_output(
            problem_description, "analyze_data_tool", data_result
        )
        print(f"   Guardian Trust Score: {data_validation.get('result', {}).get('overall_trust_score', 0.0):.2f}")
        
    except Exception as e:
        print(f"❌ Data Analysis Failed: {e}")
        return
    
    # Step 3: Model Building (CRITICAL - with smart gating)
    print("\n🧮 STEP 3: Model Building (CRITICAL)")
    print("-" * 40)
    try:
        model_result = await build_model(
            problem_description, 
            intent_result.get('result', {}), 
            data_result.get('result', {}),
            validate_output=True  # Enable smart gating
        )
        print(f"✅ Model Building: {model_result.get('status', 'unknown')}")
        
        if model_result.get('status') == 'validation_failed':
            print(f"❌ GUARDIAN BLOCKED: {model_result.get('error', 'Unknown validation error')}")
            validation = model_result.get('validation', {})
            print(f"   Trust Score: {validation.get('trust_score', 0.0):.2f}")
            print(f"   Threshold: {validation.get('trust_threshold', 0.0):.2f}")
            return
        elif model_result.get('status') == 'success':
            model_data = model_result.get('result', {})
            print(f"   Variables: {len(model_data.get('variables', []))}")
            print(f"   Constraints: {len(model_data.get('constraints', []))}")
            print(f"   Model Type: {model_data.get('model_type', 'unknown')}")
            
            # Check if validation was performed
            if 'validation' in model_result:
                validation = model_result['validation']
                print(f"   Guardian Trust Score: {validation.get('trust_score', 0.0):.2f}")
                print(f"   Guardian Status: {'✅ PASSED' if validation.get('validation_passed', False) else '❌ FAILED'}")
            
            workflow_results['build_model_tool'] = model_result
        else:
            print(f"❌ Model Building Failed: {model_result.get('error', 'Unknown error')}")
            return
            
    except Exception as e:
        print(f"❌ Model Building Failed: {e}")
        return
    
    # Step 4: Optimization Solving (CRITICAL - with smart gating)
    print("\n⚡ STEP 4: Optimization Solving (CRITICAL)")
    print("-" * 40)
    try:
        solve_result = await solve_optimization(
            problem_description,
            intent_result.get('result', {}),
            data_result.get('result', {}),
            model_result,
            validate_output=True  # Enable smart gating
        )
        print(f"✅ Optimization Solving: {solve_result.get('status', 'unknown')}")
        
        if solve_result.get('status') == 'validation_failed':
            print(f"❌ GUARDIAN BLOCKED: {solve_result.get('error', 'Unknown validation error')}")
            validation = solve_result.get('validation', {})
            print(f"   Trust Score: {validation.get('trust_score', 0.0):.2f}")
            print(f"   Threshold: {validation.get('trust_threshold', 0.0):.2f}")
            return
        elif solve_result.get('status') == 'success':
            solve_data = solve_result.get('result', {})
            print(f"   Solver Status: {solve_data.get('status', 'unknown')}")
            print(f"   Objective Value: {solve_data.get('objective_value', 0.0):.4f}")
            print(f"   Solve Time: {solve_data.get('solve_time', 0.0):.3f}s")
            
            # Check if validation was performed
            if 'validation' in solve_result:
                validation = solve_result['validation']
                print(f"   Guardian Trust Score: {validation.get('trust_score', 0.0):.2f}")
                print(f"   Guardian Status: {'✅ PASSED' if validation.get('validation_passed', False) else '❌ FAILED'}")
            
            workflow_results['solve_optimization_tool'] = solve_result
        else:
            print(f"❌ Optimization Solving Failed: {solve_result.get('error', 'Unknown error')}")
            return
            
    except Exception as e:
        print(f"❌ Optimization Solving Failed: {e}")
        return
    
    # Step 5: Explanation (Non-critical)
    print("\n📝 STEP 5: Explanation (Non-Critical)")
    print("-" * 40)
    try:
        explain_result = await explain_optimization(
            problem_description,
            intent_result.get('result', {}),
            data_result.get('result', {}),
            model_result,
            solve_result
        )
        print(f"✅ Explanation: {explain_result.get('status', 'unknown')}")
        
        if explain_result.get('status') == 'success':
            explain_data = explain_result.get('result', {})
            print(f"   Executive Summary: {explain_data.get('executive_summary', {}).get('problem_statement', 'N/A')[:50]}...")
            workflow_results['explain_optimization_tool'] = explain_result
        else:
            print(f"❌ Explanation Failed: {explain_result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Explanation Failed: {e}")
    
    # Step 6: Complete Workflow Validation
    print("\n🛡️ STEP 6: Complete Workflow Validation")
    print("-" * 40)
    try:
        workflow_validation = await validate_complete_workflow(
            problem_description, workflow_results
        )
        print(f"✅ Workflow Validation: {workflow_validation.get('status', 'unknown')}")
        print(f"   Overall Trust Score: {workflow_validation.get('overall_trust_score', 0.0):.2f}")
        print(f"   Critical Failures: {len(workflow_validation.get('critical_failures', []))}")
        print(f"   Warnings: {len(workflow_validation.get('warnings', []))}")
        print(f"   Recommendation: {workflow_validation.get('workflow_recommendation', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Workflow Validation Failed: {e}")
    
    # Summary
    print("\n📊 SUMMARY")
    print("=" * 60)
    print(f"✅ Steps Completed: {len(workflow_results)}")
    print(f"🛡️ Guardian Validation: {'ACTIVE' if any('validation' in result for result in workflow_results.values()) else 'INACTIVE'}")
    print(f"🎯 Real Results: {'YES' if all(result.get('status') == 'success' for result in workflow_results.values()) else 'NO'}")
    
    # Show trust scores
    print("\n📈 Trust Scores:")
    for tool_name, result in workflow_results.items():
        if 'validation' in result:
            validation = result['validation']
            trust_score = validation.get('trust_score', 0.0)
            status = "✅ PASSED" if validation.get('validation_passed', False) else "❌ FAILED"
            print(f"   {tool_name}: {trust_score:.2f} {status}")

async def test_guardian_thresholds():
    """Test guardian threshold behavior"""
    print("\n🧪 TESTING GUARDIAN THRESHOLDS")
    print("=" * 60)
    
    # Test with a simple problem that should pass
    simple_problem = "Maximize x + y subject to x + y <= 1, x >= 0, y >= 0"
    
    try:
        # This should work and pass validation
        intent_result = await classify_intent(simple_problem)
        data_result = await analyze_data(simple_problem, intent_result.get('result', {}))
        model_result = await build_model(simple_problem, intent_result.get('result', {}), data_result.get('result', {}))
        
        print(f"Simple Problem Model Building: {model_result.get('status')}")
        if 'validation' in model_result:
            validation = model_result['validation']
            print(f"Trust Score: {validation.get('trust_score', 0.0):.2f}")
            print(f"Threshold: {validation.get('trust_threshold', 0.0):.2f}")
            print(f"Passed: {validation.get('validation_passed', False)}")
        
    except Exception as e:
        print(f"Simple problem test failed: {e}")

if __name__ == "__main__":
    print("🧪 Smart Gating System Test Suite")
    print("=" * 60)
    
    # Run the tests
    asyncio.run(test_step_by_step())
    asyncio.run(test_guardian_thresholds())
    
    print("\n🎉 Test Suite Complete!")
