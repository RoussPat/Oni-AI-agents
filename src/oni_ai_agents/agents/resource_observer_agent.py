"""
Resource Observer Agent

Specialized agent for monitoring and analyzing resource-related game state data
from ONI save files (food, oxygen, power, materials, storage, etc.).
"""

from typing import Dict, Any, Optional
from pathlib import Path

from ..core.agent import Agent
from ..core.agent_types import AgentType
from ..services.save_file_parser import SaveFileParser


class ResourceObserverAgent(Agent):
    """
    Observer agent specialized in resource monitoring and analysis.
    
    Responsibilities:
    - Monitor food levels and production
    - Track oxygen generation and consumption
    - Analyze power grid status and efficiency
    - Monitor material stocks and storage usage
    - Detect resource bottlenecks and shortages
    """
    
    def __init__(self, agent_id: str, model_provider: str = "openai", 
                 model_config: Optional[Dict[str, Any]] = None):
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentType.OBSERVING,
            model_provider=model_provider,
            model_config=model_config or {"model": "gpt-4"}
        )
        self.save_parser = SaveFileParser()
        self.section_name = "resources"
    
    async def process_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process resource data and generate analysis report.
        
        Args:
            input_data: Should contain either:
                - save_file_path: Path to ONI save file
                - resource_data: Pre-extracted resource data
                
        Returns:
            Dictionary containing resource analysis and recommendations
        """
        try:
            # Extract resource data
            if "save_file_path" in input_data:
                save_path = Path(input_data["save_file_path"])
                resource_data = self.save_parser.get_section_data(save_path, self.section_name)
            elif "resource_data" in input_data:
                resource_data = input_data["resource_data"]
            else:
                raise ValueError("Either 'save_file_path' or 'resource_data' must be provided")
            
            # Generate AI analysis if model is available
            if self.model:
                analysis_prompt = self._create_resource_analysis_prompt(resource_data)
                ai_analysis = await self.model.generate_response(analysis_prompt)
            else:
                ai_analysis = "No AI model available for analysis"
            
            # Perform basic analysis
            basic_analysis = self._perform_basic_analysis(resource_data)
            
            return {
                "agent_id": self.agent_id,
                "section": self.section_name,
                "timestamp": self._get_current_timestamp(),
                "resource_data": resource_data,
                "basic_analysis": basic_analysis,
                "ai_analysis": ai_analysis,
                "alerts": self._generate_alerts(resource_data),
                "recommendations": self._generate_recommendations(resource_data)
            }
            
        except Exception as e:
            self.logger.error(f"Error processing resource data: {e}")
            return {
                "agent_id": self.agent_id,
                "section": self.section_name,
                "error": str(e),
                "timestamp": self._get_current_timestamp()
            }
    
    def _create_resource_analysis_prompt(self, resource_data: Dict[str, Any]) -> str:
        """Create a detailed prompt for AI analysis of resource data."""
        return f"""
        Analyze the following ONI colony resource data and provide insights:
        
        Resource Data:
        {resource_data}
        
        Please provide:
        1. Overall resource status assessment
        2. Critical shortages or surpluses
        3. Production efficiency evaluation
        4. Storage optimization suggestions
        5. Priority recommendations for resource management
        
        Focus on actionable insights for colony survival and efficiency.
        """
    
    def _perform_basic_analysis(self, resource_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform basic statistical analysis of resource data."""
        # TODO: Implement actual analysis logic
        return {
            "total_food": resource_data.get("food", 0),
            "oxygen_level": resource_data.get("oxygen", 0),
            "power_status": resource_data.get("power", 0),
            "storage_efficiency": 0.0,  # Calculate from storage_usage
            "critical_resources": [],  # List of resources below threshold
            "surplus_resources": []    # List of resources above optimal
        }
    
    def _generate_alerts(self, resource_data: Dict[str, Any]) -> list:
        """Generate alert messages for critical resource situations."""
        alerts = []
        
        # TODO: Implement actual alert logic based on thresholds
        food_level = resource_data.get("food", 0)
        if food_level < 100:  # Example threshold
            alerts.append({"type": "critical", "message": f"Low food: {food_level}"})
        
        oxygen_level = resource_data.get("oxygen", 0)
        if oxygen_level < 50:  # Example threshold
            alerts.append({"type": "warning", "message": f"Low oxygen: {oxygen_level}"})
        
        return alerts
    
    def _generate_recommendations(self, resource_data: Dict[str, Any]) -> list:
        """Generate actionable recommendations based on resource analysis."""
        recommendations = []
        
        # TODO: Implement actual recommendation logic
        # Examples:
        # - "Increase food production capacity"
        # - "Build additional oxygen generators"
        # - "Optimize storage layout"
        # - "Research advanced materials"
        
        return recommendations
    
    async def _on_start(self):
        """Initialize the resource observer agent."""
        self.logger.info(f"Resource Observer Agent {self.agent_id} started")
        self.logger.info("Ready to monitor: food, oxygen, power, materials, storage")
    
    async def _on_stop(self):
        """Cleanup when the resource observer agent stops."""
        self.logger.info(f"Resource Observer Agent {self.agent_id} stopped")
    
    async def _process_message(self, message):
        """Process incoming messages for resource analysis requests."""
        if message.message_type == "analyze_resources":
            result = await self.process_input(message.content)
            await self.send_message(
                message.sender_id,
                "resource_analysis_result",
                result
            )
        elif message.message_type == "get_resource_status":
            # Quick status check without full analysis
            status = {"agent": self.agent_id, "status": "operational", "section": self.section_name}
            await self.send_message(
                message.sender_id,
                "resource_status_response",
                status
            )
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp as string."""
        from datetime import datetime
        return datetime.now().isoformat()
