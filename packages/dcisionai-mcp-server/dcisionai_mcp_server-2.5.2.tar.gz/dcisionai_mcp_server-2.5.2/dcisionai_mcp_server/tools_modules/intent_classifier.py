#!/usr/bin/env python3
"""
Intent Classification Tool
"""

import hashlib
import logging
import boto3
import json
from datetime import datetime
from typing import Any, Dict, Optional
from botocore.exceptions import ClientError

from ..core.bedrock_client import BedrockClient
from ..core.knowledge_base import KnowledgeBase
from ..utils.json_parser import parse_json

logger = logging.getLogger(__name__)


class IntentClassifier:
    """Intent classification for optimization problems"""
    
    def __init__(self, bedrock_client: BedrockClient, knowledge_base: KnowledgeBase, cache: Dict[str, Any]):
        self.bedrock = bedrock_client
        self.kb = knowledge_base
        self.cache = cache
        
        # Initialize Bedrock Knowledge Base client
        self.knowledge_base_id = "0WHL51KZTW"
        self.region = "us-east-1"
        try:
            self.bedrock_agent_runtime = boto3.client(
                'bedrock-agent-runtime',
                region_name=self.region
            )
            logger.info("✅ Bedrock Agent Runtime client initialized for intent classification")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Bedrock Agent Runtime client: {e}")
            self.bedrock_agent_runtime = None
    
    async def classify_intent(self, problem_description: str, context: Optional[str] = None) -> Dict[str, Any]:
        """Classify optimization problem intent using KB -> Truth -> LLM fallback approach"""
        try:
            # Pre-filter: Check if problem is clearly outside our 3-industry wedge
            non_wedge_keywords = [
                'social media', 'dating app', 'streaming', 'video', 'database', 'query', 'support ticket',
                'hospital', 'healthcare', 'medical', 'school', 'education', 'bus route', 'transportation',
                'machine learning', 'ml', 'ai', 'algorithm', 'model training', 'neural network',
                'website', 'app', 'software', 'code', 'programming', 'development', 'engineering',
                'customer service', 'ticket', 'chat', 'email', 'communication'
            ]
            
            problem_lower = problem_description.lower()
            context_lower = (context or '').lower()
            combined_text = f"{problem_lower} {context_lower}"
            
            for keyword in non_wedge_keywords:
                if keyword in combined_text:
                    logger.info(f"⚠️ Problem contains non-wedge keyword '{keyword}' - providing roadmap response")
                    return {
                        "status": "roadmap",
                        "step": "intent_classification",
                        "method": "pre_filter_roadmap",
                        "timestamp": datetime.now().isoformat(),
                        "result": {
                            "intent": "roadmap",
                            "industry": "other",
                            "matched_use_case": "roadmap",
                            "confidence": 0.0,
                            "reasoning": f"Problem contains '{keyword}' which is outside our 3-industry wedge"
                        },
                        "message": f"DcisionAI currently focuses on Manufacturing, Retail, and Finance optimization. {keyword.title()} optimization is planned for our roadmap. Please check back later or contact us for custom solutions."
                    }
            
            # Step 1: Try Knowledge Base first
            logger.info("🔍 Step 1: Querying Bedrock Knowledge Base...")
            kb_result = await self._classify_with_knowledge_base(problem_description, context)
            
            if kb_result and kb_result.get('confidence', 0) > 0.8:
                # Check if the industry is within our 3-industry wedge
                industry = kb_result.get('industry', 'unknown').lower()
                if industry not in ['manufacturing', 'retail', 'finance']:
                    logger.info(f"⚠️ KB returned industry '{industry}' not in our 3-industry wedge - providing roadmap response")
                    return {
                        "status": "roadmap",
                        "step": "intent_classification",
                        "method": "industry_roadmap",
                        "timestamp": datetime.now().isoformat(),
                        "result": {
                            "intent": "roadmap",
                            "industry": industry,
                            "matched_use_case": "roadmap",
                            "confidence": 0.0,
                            "reasoning": f"Industry '{industry}' is not yet supported in our current platform"
                        },
                        "message": f"DcisionAI currently focuses on Manufacturing, Retail, and Finance optimization. {industry.title()} industry support is planned for our roadmap. Please check back later or contact us for custom solutions."
                    }
                
                logger.info(f"✅ KB Classification successful: {kb_result.get('intent')} (confidence: {kb_result.get('confidence')})")
                return {
                    "status": "success",
                    "step": "intent_classification",
                    "method": "knowledge_base",
                    "timestamp": datetime.now().isoformat(),
                    "result": kb_result,
                    "message": f"Intent: {kb_result['intent']} (Use Case: {kb_result.get('matched_use_case', 'unknown')})"
                }
            
            # Step 2: Try Truth tool validation
            logger.info("🔍 Step 2: Using Truth tool for validation...")
            truth_result = await self._classify_with_truth_tool(problem_description, context, kb_result)
            
            if truth_result and truth_result.get('confidence', 0) > 0.7:
                # Check if the industry is within our 3-industry wedge
                industry = truth_result.get('industry', 'unknown').lower()
                if industry not in ['manufacturing', 'retail', 'finance']:
                    logger.info(f"⚠️ Truth tool returned industry '{industry}' not in our 3-industry wedge - providing roadmap response")
                    return {
                        "status": "roadmap",
                        "step": "intent_classification",
                        "method": "industry_roadmap",
                        "timestamp": datetime.now().isoformat(),
                        "result": {
                            "intent": "roadmap",
                            "industry": industry,
                            "matched_use_case": "roadmap",
                            "confidence": 0.0,
                            "reasoning": f"Industry '{industry}' is not yet supported in our current platform"
                        },
                        "message": f"DcisionAI currently focuses on Manufacturing, Retail, and Finance optimization. {industry.title()} industry support is planned for our roadmap. Please check back later or contact us for custom solutions."
                    }
                
                logger.info(f"✅ Truth tool validation successful: {truth_result.get('intent')} (confidence: {truth_result.get('confidence')})")
                return {
                    "status": "success",
                    "step": "intent_classification",
                    "method": "truth_tool",
                    "timestamp": datetime.now().isoformat(),
                    "result": truth_result,
                    "message": f"Intent: {truth_result['intent']} (Use Case: {truth_result.get('matched_use_case', 'unknown')})"
                }
            
            # Step 3: Fallback to LLM
            logger.info("🔍 Step 3: Using LLM fallback...")
            llm_result = await self._classify_with_llm(problem_description, context, kb_result, truth_result)
            
            # Step 4: Validate LLM result with Truth tool
            logger.info("🔍 Step 4: Validating LLM result with Truth tool...")
            final_truth_result = await self._classify_with_truth_tool(problem_description, context, llm_result)
            
            # Use the validated result
            final_result = final_truth_result if final_truth_result else llm_result
            
            # Check if we have a confident match to a known use case
            if final_result.get('confidence', 0) < 0.6 or final_result.get('matched_use_case', 'unknown') == 'unknown':
                logger.info("⚠️ Low confidence or unknown use case - providing graceful fallback")
                return {
                    "status": "unmatched",
                    "step": "intent_classification",
                    "method": "graceful_fallback",
                    "timestamp": datetime.now().isoformat(),
                    "result": {
                        "intent": "unmatched",
                        "industry": "unknown",
                        "matched_use_case": "unknown",
                        "confidence": 0.0,
                        "reasoning": "Problem does not match any known optimization use cases in our current knowledge base"
                    },
                    "message": "DcisionAI is building more vast use cases - please revisit later. Your problem may require a custom optimization approach not yet covered in our knowledge base."
                }
            
            # Check if the industry is within our 3-industry wedge
            industry = final_result.get('industry', 'unknown').lower()
            if industry not in ['manufacturing', 'retail', 'finance']:
                logger.info(f"⚠️ Industry '{industry}' not in our 3-industry wedge - providing roadmap response")
                return {
                    "status": "roadmap",
                    "step": "intent_classification",
                    "method": "industry_roadmap",
                    "timestamp": datetime.now().isoformat(),
                    "result": {
                        "intent": "roadmap",
                        "industry": industry,
                        "matched_use_case": "roadmap",
                        "confidence": 0.0,
                        "reasoning": f"Industry '{industry}' is not yet supported in our current platform"
                    },
                    "message": f"DcisionAI currently focuses on Manufacturing, Retail, and Finance optimization. {industry.title()} industry support is planned for our roadmap. Please check back later or contact us for custom solutions."
                }
            
            logger.info(f"✅ Final classification completed: {final_result.get('intent')} (confidence: {final_result.get('confidence')})")
            return {
                "status": "success",
                "step": "intent_classification",
                "method": "llm_with_truth_validation",
                "timestamp": datetime.now().isoformat(),
                "result": final_result,
                "message": f"Intent: {final_result['intent']} (Use Case: {final_result.get('matched_use_case', 'unknown')})"
            }
            
        except Exception as e:
            logger.error(f"Intent classification error: {e}")
            return {"status": "error", "step": "intent_classification", "error": str(e)}
    
    async def _query_knowledge_base(self, problem_description: str) -> str:
        """Query Bedrock Knowledge Base for relevant use cases"""
        try:
            if not self.bedrock_agent_runtime:
                logger.warning("Bedrock Agent Runtime not available, using fallback")
                return "Knowledge base not available"
            
            # Query the knowledge base
            response = self.bedrock_agent_runtime.retrieve_and_generate(
                input={
                    "text": f"Optimization problem: {problem_description}"
                },
                retrieveAndGenerateConfiguration={
                    "type": "KNOWLEDGE_BASE",
                    "knowledgeBaseConfiguration": {
                        "knowledgeBaseId": self.knowledge_base_id,
                        "modelArn": f"arn:aws:bedrock:{self.region}::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
                    }
                }
            )
            
            # Extract the answer and citations
            answer = response.get('output', {}).get('text', '')
            citations = response.get('citations', [])
            
            # Build context string
            context_parts = [f"Knowledge Base Answer: {answer}"]
            
            if citations:
                context_parts.append("Relevant Use Cases:")
                for i, citation in enumerate(citations[:3], 1):
                    if 'retrievedReferences' in citation:
                        for ref in citation['retrievedReferences'][:1]:
                            content = ref.get('content', {}).get('text', '')
                            location = ref.get('location', {}).get('s3Location', {}).get('uri', '')
                            context_parts.append(f"  {i}. {content[:200]}... (Source: {location})")
            
            return "\n".join(context_parts)
            
        except ClientError as e:
            logger.error(f"Bedrock Knowledge Base query failed: {e}")
            return f"Knowledge base query failed: {e.response['Error']['Message']}"
        except Exception as e:
            logger.error(f"Knowledge base query error: {e}")
            return f"Knowledge base query error: {str(e)}"
    
    async def _classify_with_knowledge_base(self, problem_description: str, context: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Classify intent using Bedrock Knowledge Base"""
        try:
            if not self.bedrock_agent_runtime:
                logger.warning("Bedrock Agent Runtime not available for KB classification")
                return None
            
            # Query the knowledge base
            response = self.bedrock_agent_runtime.retrieve_and_generate(
                input={
                    "text": f"Optimization problem: {problem_description}"
                },
                retrieveAndGenerateConfiguration={
                    "type": "KNOWLEDGE_BASE",
                    "knowledgeBaseConfiguration": {
                        "knowledgeBaseId": self.knowledge_base_id,
                        "modelArn": f"arn:aws:bedrock:{self.region}::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
                    }
                }
            )
            
            # Extract answer and analyze for intent
            answer = response.get('output', {}).get('text', '')
            citations = response.get('citations', [])
            
            # Analyze the KB response to extract intent
            intent_analysis = await self._analyze_kb_response(answer, citations, problem_description)
            
            if intent_analysis:
                logger.info(f"✅ KB classification successful: {intent_analysis.get('intent')}")
                return intent_analysis
            
            return None
            
        except Exception as e:
            logger.error(f"KB classification failed: {e}")
            return None
    
    async def _analyze_kb_response(self, answer: str, citations: list, problem_description: str) -> Optional[Dict[str, Any]]:
        """Analyze KB response to extract intent classification"""
        try:
            # Build prompt to analyze KB response
            prompt = f"""Analyze this Knowledge Base response and extract the optimization intent.

PROBLEM: {problem_description}
KB ANSWER: {answer}

CITATIONS: {len(citations)} relevant sources found

Extract the most appropriate intent from the KB response. Use specific intent names:

MANUFACTURING: resource_allocation, production_planning, scheduling, inventory_management, supply_chain_optimization, energy_optimization
FINANCE: portfolio_optimization, risk_management, asset_allocation, capital_allocation, trading_optimization
RETAIL: inventory_management, pricing_optimization, demand_forecasting, assortment_planning, markdown_optimization
LOGISTICS: routing, inventory_management, delivery_optimization, warehouse_optimization, resource_allocation
ENERGY: grid_optimization, load_balancing, generation_dispatch, energy_optimization

JSON format:
{{
  "intent": "production_planning|scheduling",
  "industry": "manufacturing",
  "optimization_type": "linear_programming|integer_programming|mixed_integer_programming",
  "complexity": "low|medium|high",
  "confidence": 0.0-1.0,
  "matched_use_case": "01_Production_Scheduling",
  "reasoning": "explanation based on KB content"
}}"""
            
            resp = await self.bedrock.invoke("anthropic.claude-3-haiku-20240307-v1:0", prompt, 1000)
            result = parse_json(resp)
            
            # Set defaults
            result.setdefault('intent', 'unknown')
            result.setdefault('industry', 'unknown')
            result.setdefault('optimization_type', 'linear_programming')
            result.setdefault('complexity', 'medium')
            result.setdefault('confidence', 0.8)  # High confidence for KB results
            result.setdefault('matched_use_case', 'unknown')
            result.setdefault('reasoning', 'Based on Knowledge Base analysis')
            
            # Fix use case ID mapping to match our expected format
            matched_use_case = result.get('matched_use_case', 'unknown')
            if matched_use_case != 'unknown':
                result['matched_use_case'] = self._map_kb_use_case_to_expected(matched_use_case, result.get('intent', ''), result.get('industry', ''))
                
            return result
            
        except Exception as e:
            logger.error(f"KB response analysis failed: {e}")
            return None
    
    async def _classify_with_truth_tool(self, problem_description: str, context: Optional[str] = None, previous_result: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """Classify intent using Truth tool validation"""
        try:
            # Build truth validation prompt
            prompt = f"""Validate and classify this optimization problem using truth validation.

PROBLEM: {problem_description}
CONTEXT: {context or "No additional context"}
PREVIOUS_ANALYSIS: {previous_result or "No previous analysis"}

Validate the problem classification and provide the most accurate intent. Use specific intent names:

MANUFACTURING: resource_allocation, production_planning, scheduling, inventory_management, supply_chain_optimization, energy_optimization
FINANCE: portfolio_optimization, risk_management, asset_allocation, capital_allocation, trading_optimization
RETAIL: inventory_management, pricing_optimization, demand_forecasting, assortment_planning, markdown_optimization
LOGISTICS: routing, inventory_management, delivery_optimization, warehouse_optimization, resource_allocation
ENERGY: grid_optimization, load_balancing, generation_dispatch, energy_optimization

JSON format:
{{
  "intent": "production_planning|scheduling",
  "industry": "manufacturing",
  "optimization_type": "linear_programming|integer_programming|mixed_integer_programming",
  "complexity": "low|medium|high",
  "confidence": 0.0-1.0,
  "matched_use_case": "01_Production_Scheduling",
  "reasoning": "truth validation explanation",
  "validation_score": 0.0-1.0
}}"""
            
            resp = await self.bedrock.invoke("anthropic.claude-3-haiku-20240307-v1:0", prompt, 1000)
            result = parse_json(resp)
            
            # Set defaults
            result.setdefault('intent', 'unknown')
            result.setdefault('industry', 'unknown')
            result.setdefault('optimization_type', 'linear_programming')
            result.setdefault('complexity', 'medium')
            result.setdefault('confidence', 0.7)  # Medium confidence for truth validation
            result.setdefault('matched_use_case', 'unknown')
            result.setdefault('reasoning', 'Truth tool validation')
            result.setdefault('validation_score', 0.8)
            
            return result
            
        except Exception as e:
            logger.error(f"Truth tool classification failed: {e}")
            return None
    
    async def _classify_with_llm(self, problem_description: str, context: Optional[str] = None, kb_result: Optional[Dict] = None, truth_result: Optional[Dict] = None) -> Dict[str, Any]:
        """Classify intent using LLM fallback"""
        try:
            # Build comprehensive LLM prompt with all previous results
            prompt = f"""Classify this optimization problem using comprehensive analysis.

PROBLEM: {problem_description}
CONTEXT: {context or "No additional context"}

PREVIOUS_ANALYSES:
KB_RESULT: {kb_result or "No KB result"}
TRUTH_RESULT: {truth_result or "No truth result"}

Provide the most accurate classification. Use specific intent names:

MANUFACTURING: resource_allocation, production_planning, scheduling, inventory_management, supply_chain_optimization, energy_optimization
FINANCE: portfolio_optimization, risk_management, asset_allocation, capital_allocation, trading_optimization
RETAIL: inventory_management, pricing_optimization, demand_forecasting, assortment_planning, markdown_optimization
LOGISTICS: routing, inventory_management, delivery_optimization, warehouse_optimization, resource_allocation
ENERGY: grid_optimization, load_balancing, generation_dispatch, energy_optimization

JSON format:
{{
  "intent": "production_planning|scheduling",
  "industry": "manufacturing",
  "optimization_type": "linear_programming|integer_programming|mixed_integer_programming",
  "complexity": "low|medium|high",
  "confidence": 0.0-1.0,
  "matched_use_case": "01_Production_Scheduling",
  "reasoning": "comprehensive LLM analysis"
}}"""
            
            resp = await self.bedrock.invoke("anthropic.claude-3-haiku-20240307-v1:0", prompt, 1000)
            result = parse_json(resp)
            
            # Set defaults
            result.setdefault('intent', 'unknown')
            result.setdefault('industry', 'unknown')
            result.setdefault('optimization_type', 'linear_programming')
            result.setdefault('complexity', 'medium')
            result.setdefault('confidence', 0.6)  # Lower confidence for LLM fallback
            result.setdefault('matched_use_case', 'unknown')
            result.setdefault('reasoning', 'LLM fallback analysis')
            
            return result
            
        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
            return {
                'intent': 'unknown',
                'industry': 'unknown',
                'optimization_type': 'linear_programming',
                'complexity': 'medium',
                'confidence': 0.3,
                'matched_use_case': 'unknown',
                'reasoning': 'LLM classification failed'
            }
    
    def _map_kb_use_case_to_expected(self, kb_use_case: str, intent: str, industry: str) -> str:
        """Map KB use case IDs to our expected format"""
        # Common mappings from KB responses to our expected format
        use_case_mappings = {
            # Portfolio optimization mappings
            '01_Asset_Allocation': '01_Portfolio_Optimization',
            '01_Portfolio_Optimization': '01_Portfolio_Optimization',
            'Portfolio_Optimization': '01_Portfolio_Optimization',
            'Asset_Allocation': '01_Portfolio_Optimization',
            
            # Inventory optimization mappings
            '02_Inventory_Allocation_Optimization': '01_Inventory_Optimization',
            '01_Inventory_Optimization': '01_Inventory_Optimization',
            'Inventory_Optimization': '01_Inventory_Optimization',
            'Inventory_Allocation': '01_Inventory_Optimization',
            
            # Production scheduling mappings
            '01_Production_Scheduling': '01_Production_Scheduling',
            'Production_Scheduling': '01_Production_Scheduling',
            
            # Pricing optimization mappings
            '03_Pricing_Optimization': '02_Pricing_Optimization',
            '02_Pricing_Optimization': '02_Pricing_Optimization',
            'Pricing_Optimization': '02_Pricing_Optimization',
            
            # Markdown optimization mappings
            '04_Markdown_Optimization': '01_Markdown_Optimization',
            '01_Markdown_Optimization': '01_Markdown_Optimization',
            'Markdown_Optimization': '01_Markdown_Optimization',
            
            # Vehicle routing mappings
            '01_Vehicle_Routing_Optimization': '01_Vehicle_Routing',
            '01_Vehicle_Routing_Problem': '01_Vehicle_Routing',
            'Vehicle_Routing': '01_Vehicle_Routing',
            
            # Grid optimization mappings
            '01_Grid_Optimization': '01_Grid_Optimization',
            'Grid_Optimization': '01_Grid_Optimization',
            
            # Risk management mappings
            '02_Risk_Management': '02_Risk_Management',
            'Risk_Management': '02_Risk_Management',
        }
        
        # Direct mapping if available
        if kb_use_case in use_case_mappings:
            return use_case_mappings[kb_use_case]
        
        # Fallback: try to construct expected format based on intent and industry
        if 'portfolio' in intent.lower() and 'finance' in industry.lower():
            return '01_Portfolio_Optimization'
        elif 'inventory' in intent.lower():
            if 'retail' in industry.lower():
                return '01_Inventory_Optimization'
            elif 'manufacturing' in industry.lower():
                return '02_Inventory_Optimization'
        elif 'production' in intent.lower() or 'scheduling' in intent.lower():
            return '01_Production_Scheduling'
        elif 'pricing' in intent.lower():
            return '02_Pricing_Optimization'
        elif 'markdown' in intent.lower():
            return '01_Markdown_Optimization'
        elif 'routing' in intent.lower() or 'delivery' in intent.lower():
            return '01_Vehicle_Routing'
        elif 'grid' in intent.lower() or 'energy' in intent.lower():
            return '01_Grid_Optimization'
        elif 'risk' in intent.lower():
            return '02_Risk_Management'
        
        # Default fallback
        return kb_use_case


async def classify_intent_tool(problem_description: str, context: Optional[str] = None) -> Dict[str, Any]:
    """Tool wrapper for intent classification"""
    # This would be called from the main tools orchestrator
    # For now, return a placeholder
    return {"status": "error", "error": "Tool not initialized"}
