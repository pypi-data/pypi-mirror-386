#!/usr/bin/env python3
"""
Comprehensive Test Suite for Diverse Industries
Tests all optimization tools across different industries and problem types
"""

import asyncio
import logging
import time
from typing import Dict, Any, List

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

class IndustryTestSuite:
    """Test suite for diverse industry optimization problems"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = time.time()
    
    async def run_all_tests(self):
        """Run all industry tests"""
        print("🚀 DcisionAI Comprehensive Industry Test Suite")
        print("=" * 80)
        
        # Test 1: Manufacturing Production Planning
        await self.test_manufacturing()
        
        # Test 2: Portfolio Optimization
        await self.test_portfolio()
        
        # Test 3: Nurse Scheduling
        await self.test_scheduling()
        
        # Test 4: Supply Chain Optimization
        await self.test_supply_chain()
        
        # Test 5: Resource Allocation
        await self.test_resource_allocation()
        
        # Test 6: Transportation/Logistics
        await self.test_transportation()
        
        # Test 7: Energy Grid Optimization
        await self.test_energy_grid()
        
        # Test 8: Healthcare Resource Planning
        await self.test_healthcare()
        
        # Print final summary
        self.print_final_summary()
    
    async def test_manufacturing(self):
        """Test manufacturing production planning optimization"""
        print("\n🏭 TEST 1: Manufacturing Production Planning")
        print("-" * 60)
        
        problem = """
        I need to optimize my furniture manufacturing production for the next month (30 days).
        I produce 3 types of furniture: chairs, tables, and cabinets.

        Daily production limits:
        - Chairs: max 200 units/day
        - Tables: max 100 units/day  
        - Cabinets: max 50 units/day

        Labor requirements per unit:
        - Chairs: 2 hours regular labor
        - Tables: 4 hours regular labor
        - Cabinets: 8 hours regular labor, 8 hours skilled labor

        Available daily labor:
        - Regular labor: 800 hours/day
        - Skilled labor: 40 hours/day

        Monthly demand (over 30 days):
        - Chairs: 3000 to 5000 units
        - Tables: 1500 to 2500 units
        - Cabinets: 800 to 1200 units

        Profit per unit:
        - Chairs: $25
        - Tables: $60
        - Cabinets: $120

        Objective: Maximize total profit for the month.
        """
        
        await self.run_complete_workflow("Manufacturing", problem)
    
    async def test_portfolio(self):
        """Test portfolio optimization"""
        print("\n💼 TEST 2: Portfolio Optimization")
        print("-" * 60)
        
        problem = """
        I need to optimize my investment portfolio with $1,000,000 to invest.
        
        Available stocks:
        - Tech stocks: AAPL, GOOGL, MSFT, AMZN, TSLA
        - Healthcare: JNJ, PFE, UNH, ABBV, MRK
        - Financial: JPM, BAC, WFC, GS, C
        - Energy: XOM, CVX, COP, EOG, SLB
        - Consumer: PG, KO, WMT, MCD, NKE
        
        Expected annual returns:
        - Tech: 12-18%
        - Healthcare: 8-12%
        - Financial: 6-10%
        - Energy: 4-8%
        - Consumer: 6-9%
        
        Risk constraints:
        - No single stock > 10% of portfolio
        - No sector > 30% of portfolio
        - Maximum portfolio volatility: 15%
        
        Objective: Maximize expected return while managing risk.
        """
        
        await self.run_complete_workflow("Portfolio", problem)
    
    async def test_scheduling(self):
        """Test nurse scheduling optimization"""
        print("\n👩‍⚕️ TEST 3: Nurse Scheduling")
        print("-" * 60)
        
        problem = """
        I need to optimize nurse scheduling for a hospital ward over the next 2 weeks (14 days).
        
        Staff:
        - 15 registered nurses (RNs)
        - 8 licensed practical nurses (LPNs)
        - 5 nursing assistants (NAs)
        
        Shifts:
        - Day shift: 7 AM - 7 PM (12 hours)
        - Night shift: 7 PM - 7 AM (12 hours)
        
        Requirements per shift:
        - Minimum 4 RNs, 2 LPNs, 1 NA
        - Maximum 6 RNs, 4 LPNs, 3 NAs
        
        Constraints:
        - No nurse works more than 5 consecutive days
        - Minimum 8 hours between shifts
        - Each nurse works 3-4 shifts per week
        - Weekend shifts get 1.5x pay
        
        Costs:
        - RN: $45/hour regular, $67.50/hour weekend
        - LPN: $30/hour regular, $45/hour weekend
        - NA: $20/hour regular, $30/hour weekend
        
        Objective: Minimize total labor costs while meeting coverage requirements.
        """
        
        await self.run_complete_workflow("Scheduling", problem)
    
    async def test_supply_chain(self):
        """Test supply chain optimization"""
        print("\n🚚 TEST 4: Supply Chain Optimization")
        print("-" * 60)
        
        problem = """
        I need to optimize my supply chain for a retail company with 50 stores.
        
        Suppliers:
        - Supplier A: Electronics, capacity 10,000 units/month, $50/unit
        - Supplier B: Electronics, capacity 8,000 units/month, $45/unit
        - Supplier C: Clothing, capacity 15,000 units/month, $25/unit
        - Supplier D: Clothing, capacity 12,000 units/month, $30/unit
        - Supplier E: Home goods, capacity 5,000 units/month, $80/unit
        
        Stores:
        - 20 stores in North region
        - 15 stores in South region
        - 15 stores in West region
        
        Demand (monthly):
        - Electronics: 15,000 units total
        - Clothing: 20,000 units total
        - Home goods: 4,000 units total
        
        Transportation costs:
        - North region: $2/unit
        - South region: $3/unit
        - West region: $4/unit
        
        Constraints:
        - Each store must receive at least 80% of demand
        - No supplier can provide more than 60% of any product category
        - Lead time: 2-5 days
        
        Objective: Minimize total cost (purchase + transportation) while meeting demand.
        """
        
        await self.run_complete_workflow("Supply Chain", problem)
    
    async def test_resource_allocation(self):
        """Test resource allocation optimization"""
        print("\n📊 TEST 5: Resource Allocation")
        print("-" * 60)
        
        problem = """
        I need to optimize resource allocation across 10 projects for the next quarter.
        
        Projects:
        - Project A: High priority, requires 5 developers, 2 designers, 1 PM
        - Project B: High priority, requires 3 developers, 1 designer, 1 PM
        - Project C: Medium priority, requires 4 developers, 2 designers, 1 PM
        - Project D: Medium priority, requires 2 developers, 1 designer, 0.5 PM
        - Project E: Low priority, requires 3 developers, 1 designer, 0.5 PM
        - Project F: Low priority, requires 2 developers, 1 designer, 0.5 PM
        - Project G: High priority, requires 6 developers, 3 designers, 1 PM
        - Project H: Medium priority, requires 3 developers, 2 designers, 1 PM
        - Project I: Low priority, requires 1 developer, 1 designer, 0.5 PM
        - Project J: High priority, requires 4 developers, 2 designers, 1 PM
        
        Available resources:
        - 25 developers
        - 15 designers
        - 8 project managers
        
        Project values:
        - High priority: $500K each
        - Medium priority: $300K each
        - Low priority: $150K each
        
        Constraints:
        - Each project must be fully staffed or not started
        - No resource can work on more than 2 projects
        - At least 80% of high priority projects must be completed
        
        Objective: Maximize total project value while respecting resource constraints.
        """
        
        await self.run_complete_workflow("Resource Allocation", problem)
    
    async def test_transportation(self):
        """Test transportation/logistics optimization"""
        print("\n🚛 TEST 6: Transportation/Logistics")
        print("-" * 60)
        
        problem = """
        I need to optimize delivery routes for a logistics company.
        
        Vehicles:
        - 5 small trucks: capacity 1000 lbs, cost $0.50/mile
        - 3 medium trucks: capacity 2000 lbs, cost $0.75/mile
        - 2 large trucks: capacity 4000 lbs, cost $1.00/mile
        
        Delivery locations:
        - 20 customer locations across the city
        - Each location has specific delivery requirements
        - Time windows: 8 AM - 6 PM
        
        Constraints:
        - Each vehicle can make maximum 8 deliveries per day
        - Maximum 10 hours driving time per vehicle
        - Each delivery must be completed within 2 hours of arrival
        - No vehicle can exceed weight capacity
        
        Distance matrix available for all location pairs.
        
        Objective: Minimize total transportation cost while meeting all delivery requirements.
        """
        
        await self.run_complete_workflow("Transportation", problem)
    
    async def test_energy_grid(self):
        """Test energy grid optimization"""
        print("\n⚡ TEST 7: Energy Grid Optimization")
        print("-" * 60)
        
        problem = """
        I need to optimize energy generation and distribution for a microgrid.
        
        Generation sources:
        - Solar panels: 500 kW capacity, $0.05/kWh, available 6 AM - 8 PM
        - Wind turbines: 300 kW capacity, $0.08/kWh, variable availability
        - Gas generator: 1000 kW capacity, $0.15/kWh, always available
        - Battery storage: 200 kWh capacity, 90% efficiency
        
        Load requirements (24-hour cycle):
        - Residential: 200-400 kW
        - Commercial: 300-600 kW
        - Industrial: 100-300 kW
        
        Constraints:
        - Must meet all demand at all times
        - Battery can only charge during excess generation
        - Gas generator has minimum 100 kW output when running
        - Grid connection available for import/export at $0.12/kWh
        
        Objective: Minimize total energy cost while ensuring reliable supply.
        """
        
        await self.run_complete_workflow("Energy Grid", problem)
    
    async def test_healthcare(self):
        """Test healthcare resource planning"""
        print("\n🏥 TEST 8: Healthcare Resource Planning")
        print("-" * 60)
        
        problem = """
        I need to optimize resource allocation for a hospital emergency department.
        
        Resources:
        - 8 emergency physicians
        - 12 nurses
        - 4 technicians
        - 15 beds
        - 3 operating rooms
        
        Patient types and requirements:
        - Critical: 2 physicians, 2 nurses, 1 bed, immediate care
        - Urgent: 1 physician, 1 nurse, 1 bed, within 1 hour
        - Non-urgent: 1 physician, 0.5 nurses, 1 bed, within 4 hours
        
        Expected arrivals (per 8-hour shift):
        - Critical: 2-4 patients
        - Urgent: 8-12 patients
        - Non-urgent: 15-25 patients
        
        Constraints:
        - Each physician can handle maximum 8 patients per shift
        - Each nurse can handle maximum 12 patients per shift
        - Operating rooms available 24/7 with 2-hour turnover
        - Bed occupancy must not exceed 90%
        
        Objective: Minimize patient wait times while maximizing resource utilization.
        """
        
        await self.run_complete_workflow("Healthcare", problem)
    
    async def run_complete_workflow(self, industry: str, problem: str):
        """Run complete optimization workflow for a problem"""
        print(f"\n📋 Running {industry} Optimization Workflow...")
        
        start_time = time.time()
        workflow_results = {}
        
        try:
            # Step 1: Intent Classification
            print("   🔍 Step 1: Intent Classification...")
            intent_result = await classify_intent(problem)
            workflow_results['intent'] = intent_result
            print(f"      ✅ Intent: {intent_result.get('result', {}).get('intent', 'N/A')}")
            print(f"      ✅ Industry: {intent_result.get('result', {}).get('industry', 'N/A')}")
            
            # Step 2: Data Analysis
            print("   📊 Step 2: Data Analysis...")
            data_analysis_result = await analyze_data(problem, intent_result.get('result'))
            workflow_results['data_analysis'] = data_analysis_result
            readiness_score = data_analysis_result.get('result', {}).get('readiness_score', 0)
            print(f"      ✅ Data Readiness: {readiness_score:.1%}")
            
            # Step 3: Solver Selection
            print("   ⚙️ Step 3: Solver Selection...")
            solver_selection_result = await select_solver(
                intent_result.get('result', {}).get('optimization_type', 'linear_programming'),
                problem_size={"num_variables": 50, "num_constraints": 20},
                performance_requirement="balanced"
            )
            workflow_results['solver_selection'] = solver_selection_result
            selected_solver = solver_selection_result.get('result', {}).get('selected_solver', 'N/A')
            print(f"      ✅ Selected Solver: {selected_solver}")
            
            # Step 4: Model Building
            print("   🧮 Step 4: Model Building...")
            model_building_result = await build_model(
                problem,
                intent_data=intent_result.get('result'),
                data_analysis=data_analysis_result.get('result'),
                solver_selection=solver_selection_result.get('result'),
                validate_output=False
            )
            workflow_results['model_building'] = model_building_result
            model_status = model_building_result.get('status')
            print(f"      ✅ Model Status: {model_status}")
            
            if model_status == 'success':
                model_details = model_building_result['result']
                num_vars = len(model_details.get('variables', []))
                num_constraints = len(model_details.get('constraints', []))
                model_type = model_details.get('model_type', 'N/A')
                print(f"         Variables: {num_vars}")
                print(f"         Constraints: {num_constraints}")
                print(f"         Model Type: {model_type}")
                
                # Step 5: Optimization Solving
                print("   ⚡ Step 5: Optimization Solving...")
                optimization_result = await solve_optimization(
                    problem,
                    intent_data=intent_result.get('result'),
                    data_analysis=data_analysis_result.get('result'),
                    model_building=model_building_result,
                    validate_output=False
                )
                workflow_results['optimization'] = optimization_result
                solve_status = optimization_result.get('status')
                print(f"      ✅ Solve Status: {solve_status}")
                
                if solve_status == 'success':
                    solve_details = optimization_result['result']
                    solver_status = solve_details.get('status', 'N/A')
                    objective_value = solve_details.get('objective_value', 0)
                    solve_time = solve_details.get('solve_time', 0)
                    print(f"         Solver Status: {solver_status}")
                    print(f"         Objective Value: ${objective_value:,.2f}")
                    print(f"         Solve Time: {solve_time:.3f}s")
                    
                    # Step 6: Business Explanation
                    print("   📈 Step 6: Business Explanation...")
                    explanation_result = await explain_optimization(
                        problem,
                        intent_data=intent_result.get('result'),
                        data_analysis=data_analysis_result.get('result'),
                        model_building=model_building_result,
                        optimization_solution=optimization_result
                    )
                    workflow_results['explanation'] = explanation_result
                    explanation_status = explanation_result.get('status')
                    print(f"      ✅ Explanation Status: {explanation_status}")
                    
                    # Step 7: Scenario Simulation
                    print("   🎯 Step 7: Scenario Simulation...")
                    simulation_result = await simulate_scenarios(
                        problem,
                        optimization_solution=optimization_result,
                        scenario_parameters={"demand_variation": 0.1, "cost_inflation": 0.05},
                        simulation_type="monte_carlo",
                        num_trials=1000
                    )
                    workflow_results['simulation'] = simulation_result
                    simulation_status = simulation_result.get('status')
                    print(f"      ✅ Simulation Status: {simulation_status}")
                    
                    # Step 8: Validation
                    print("   🛡️ Step 8: Validation...")
                    validation_result = await validate_tool_output(
                        problem,
                        tool_name="complete_workflow",
                        tool_output=workflow_results,
                        validation_type="comprehensive"
                    )
                    workflow_results['validation'] = validation_result
                    validation_status = validation_result.get('status')
                    trust_score = validation_result.get('result', {}).get('trust_score', 0)
                    print(f"      ✅ Validation Status: {validation_status}")
                    print(f"         Trust Score: {trust_score:.2f}")
                
            # Calculate timing
            end_time = time.time()
            total_time = end_time - start_time
            
            # Store results
            self.test_results[industry] = {
                'status': 'success' if model_status == 'success' else 'failed',
                'total_time': total_time,
                'workflow_results': workflow_results
            }
            
            print(f"   ✅ {industry} Test Completed in {total_time:.2f}s")
            
        except Exception as e:
            print(f"   ❌ {industry} Test Failed: {str(e)}")
            self.test_results[industry] = {
                'status': 'failed',
                'error': str(e),
                'total_time': time.time() - start_time
            }
    
    def print_final_summary(self):
        """Print final test summary"""
        print("\n" + "=" * 80)
        print("📊 FINAL TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results.values() if result['status'] == 'success')
        failed_tests = total_tests - successful_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        
        total_time = time.time() - self.start_time
        print(f"Total Execution Time: {total_time:.2f}s")
        
        print("\n📋 Detailed Results:")
        for industry, result in self.test_results.items():
            status_icon = "✅" if result['status'] == 'success' else "❌"
            print(f"  {status_icon} {industry}: {result['status']} ({result['total_time']:.2f}s)")
            if result['status'] == 'failed' and 'error' in result:
                print(f"     Error: {result['error']}")
        
        print("\n🎉 Test Suite Complete!")


async def main():
    """Main test execution"""
    test_suite = IndustryTestSuite()
    await test_suite.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
