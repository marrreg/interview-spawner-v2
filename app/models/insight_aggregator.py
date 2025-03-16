import os
import json
import logging
from typing import List, Dict, Any
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('insight_aggregator')

class InsightAggregator:
    """Aggregates insights from multiple conversations"""
    
    def __init__(self, api_key=None, model="gpt-4o-mini"):
        """Initialize the insight aggregator
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: OpenAI model to use for aggregation
        """
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
        self.model = model
        self.client = OpenAI(api_key=self.api_key)
        logger.info(f"Initialized InsightAggregator with model: {self.model}")
    
    def aggregate_insights(self, insights: List[Dict[str, Any]], context: str) -> List[Dict[str, Any]]:
        """Aggregate insights from multiple conversations
        
        Args:
            insights: List of insights from conversations
            context: High-level context for the simulation
            
        Returns:
            List[Dict[str, Any]]: Aggregated insights
        """
        if not insights:
            logger.info("No insights provided for aggregation, returning empty list")
            return []
        
        # Format insights for analysis
        insights_text = ""
        for i, insight in enumerate(insights):
            insights_text += f"Insight {i+1} (from {insight['persona_name']}): {insight['insight']}\n"
        
        logger.info(f"Aggregating {len(insights)} insights for context: {context}")
        
        system_prompt = f"""
        You are an expert at analyzing customer research insights and identifying patterns and themes.
        
        Your task is to analyze insights from multiple customer interviews about {context} and:
        1. Identify common themes and patterns
        2. Cluster similar insights together
        3. Rank insights by importance/impact
        4. Identify unique or surprising insights
        5. Formulate actionable recommendations based on these insights
        
        For each key insight or theme you identify, provide:
        - A concise name for the theme/insight
        - A clear description of the insight
        - The support/evidence from the interviews
        - The potential impact on product decisions
        - A confidence score (1-5) based on how many personas shared similar insights
        
        Avoid generic insights and focus on specific, actionable findings that would impact product decisions.
        """
        
        user_prompt = f"""
        Here are the insights from the customer interviews:
        
        {insights_text}
        
        Please analyze these insights and identify the key themes, patterns, and actionable findings.
        
        Your response must be a valid JSON array with the following structure:
        [
          {{
            "theme": "Name of theme/insight",
            "description": "Clear description of the insight",
            "evidence": "Support from interviews",
            "impact": "Potential impact on product decisions",
            "confidence": confidence_score_1_to_5
          }},
          ...
        ]
        
        Ensure your response is a complete, valid JSON array and doesn't use any wrapper object.
        Keep descriptions and impacts concise to avoid truncation.
        """
        
        try:
            logger.info("Calling OpenAI API for insight aggregation")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"},
                max_tokens=2000  # Increased from 1000 to 2000
            )
            
            result = response.choices[0].message.content
            logger.info(f"Received response of length: {len(result)}")
            
            # Parse the JSON response
            try:
                # Try to fix common JSON issues
                result = self._ensure_valid_json(result)
                logger.info("Attempting to parse JSON response")
                
                aggregated_insights = json.loads(result)
                logger.info(f"Successfully parsed JSON response: {type(aggregated_insights)}")
                
                # If the response is not a list but has an insights key, extract it
                if isinstance(aggregated_insights, dict) and "insights" in aggregated_insights:
                    logger.info("Found 'insights' key in response, extracting it")
                    aggregated_insights = aggregated_insights["insights"]
                
                # Ensure we have a list
                if not isinstance(aggregated_insights, list):
                    logger.warning(f"Response is not a list: {type(aggregated_insights)}")
                    aggregated_insights = []
                else:
                    logger.info(f"Got {len(aggregated_insights)} aggregated insights")
                
                # Validate each insight has required fields
                validated_insights = []
                for insight in aggregated_insights:
                    if self._validate_insight(insight):
                        validated_insights.append(insight)
                    else:
                        logger.warning(f"Skipping invalid insight: {insight}")
                
                if len(validated_insights) == 0 and len(aggregated_insights) > 0:
                    logger.warning("No valid insights found after validation, using fallback")
                    return self._fallback_aggregation(insights)
                
                return validated_insights
                
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON response: {str(e)}")
                logger.error(f"Problematic JSON: {result[:200]}...") # Log first 200 chars
                return self._fallback_aggregation(insights)
            
        except Exception as e:
            logger.error(f"Error aggregating insights: {str(e)}", exc_info=True)
            return self._fallback_aggregation(insights)
    
    def _ensure_valid_json(self, json_str: str) -> str:
        """Attempt to fix common JSON issues to ensure valid parsing
        
        Args:
            json_str: JSON string to fix
            
        Returns:
            str: Fixed JSON string
        """
        # Remove any leading/trailing non-JSON text
        json_start = json_str.find('[')
        json_end = json_str.rfind(']') + 1
        
        # If we found valid array markers, extract just that part
        if json_start >= 0 and json_end > json_start:
            logger.info(f"Extracting JSON array from positions {json_start} to {json_end}")
            return json_str[json_start:json_end]
        
        # Try to find a JSON object instead
        json_start = json_str.find('{')
        json_end = json_str.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            logger.info(f"Extracting JSON object from positions {json_start} to {json_end}")
            return json_str[json_start:json_end]
        
        # If we couldn't find valid JSON markers, return the original string
        logger.warning("Could not find valid JSON markers in the response")
        return json_str
    
    def _validate_insight(self, insight: Dict[str, Any]) -> bool:
        """Validate that an insight has all required fields
        
        Args:
            insight: Insight to validate
            
        Returns:
            bool: Whether the insight is valid
        """
        required_fields = ["theme", "description", "evidence", "impact", "confidence"]
        
        # Check all required fields are present
        for field in required_fields:
            if field not in insight:
                logger.warning(f"Insight missing required field: {field}")
                return False
        
        # Check confidence is a number between 1-5
        try:
            confidence = int(insight["confidence"])
            if confidence < 1 or confidence > 5:
                logger.warning(f"Insight has invalid confidence score: {confidence}")
                return False
        except (ValueError, TypeError):
            logger.warning(f"Insight has non-integer confidence: {insight.get('confidence')}")
            return False
        
        return True
    
    def _fallback_aggregation(self, insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fallback method for insight aggregation if the API call fails
        
        Args:
            insights: List of insights from conversations
            
        Returns:
            List[Dict[str, Any]]: Simple aggregated insights
        """
        logger.info("Using fallback insight aggregation method")
        # Group insights by content similarity (very basic approach)
        grouped_insights = {}
        
        for insight in insights:
            insight_text = insight["insight"].lower()
            found_group = False
            
            for group_key in grouped_insights:
                if any(word in insight_text for word in group_key.split()):
                    grouped_insights[group_key].append(insight)
                    found_group = True
                    break
            
            if not found_group:
                # Create a new group with the first few words as the key
                key_words = " ".join(insight_text.split()[:3])
                grouped_insights[key_words] = [insight]
        
        # Convert groups to aggregated insights
        aggregated = []
        
        for group_key, group_insights in grouped_insights.items():
            aggregated.append({
                "theme": group_key.capitalize(),
                "description": group_insights[0]["insight"],
                "evidence": f"Mentioned by {len(group_insights)} personas",
                "impact": "Requires further analysis",
                "confidence": min(len(group_insights), 5)
            })
        
        logger.info(f"Fallback aggregation produced {len(aggregated)} insights")
        return aggregated 