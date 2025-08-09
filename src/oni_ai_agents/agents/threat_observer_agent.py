"""
Threat Observer Agent

Specialized agent for monitoring and analyzing threat and environmental data
from ONI save files (diseases, temperature, pressure, contamination, etc.).
"""

from typing import Dict, Any, Optional
from pathlib import Path

from ..core.agent import Agent
from ..core.agent_types import AgentType
from ..services.save_file_parser import SaveFileParser


class ThreatObserverAgent(Agent):
    """
    Observer agent specialized in threat detection and environmental monitoring.
    
    Responsibilities:
    - Monitor disease outbreaks and contamination
    - Track temperature zones and heat management
    - Analyze pressure and atmospheric issues
    - Detect hostile creatures and external threats
    - Monitor environmental hazards
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
        self.section_name = "threats"
    
    async def process_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process threat data and generate analysis report.
        
        Args:
            input_data: Should contain either:
                - save_file_path: Path to ONI save file
                - threat_data: Pre-extracted threat data
                
        Returns:
            Dictionary containing threat analysis and emergency recommendations
        """
        try:
            # Extract threat data
            if "save_file_path" in input_data:
                save_path = Path(input_data["save_file_path"])
                threat_data = self.save_parser.get_section_data(save_path, self.section_name)
            elif "threat_data" in input_data:
                threat_data = input_data["threat_data"]
            else:
                raise ValueError("Either 'save_file_path' or 'threat_data' must be provided")
            
            # Generate AI analysis if model is available
            if self.model:
                analysis_prompt = self._create_threat_analysis_prompt(threat_data)
                ai_analysis = await self.model.generate_response(analysis_prompt)
            else:
                ai_analysis = "No AI model available for analysis"
            
            # Perform basic analysis
            basic_analysis = self._perform_basic_analysis(threat_data)
            
            return {
                "agent_id": self.agent_id,
                "section": self.section_name,
                "timestamp": self._get_current_timestamp(),
                "threat_data": threat_data,
                "basic_analysis": basic_analysis,
                "ai_analysis": ai_analysis,
                "alerts": self._generate_alerts(threat_data),
                "emergency_actions": self._generate_emergency_actions(threat_data),
                "threat_level": self._assess_overall_threat_level(threat_data)
            }
            
        except Exception as e:
            self.logger.error(f"Error processing threat data: {e}")
            return {
                "agent_id": self.agent_id,
                "section": self.section_name,
                "error": str(e),
                "timestamp": self._get_current_timestamp()
            }
    
    def _create_threat_analysis_prompt(self, threat_data: Dict[str, Any]) -> str:
        """Create a detailed prompt for AI analysis of threat data."""
        return f"""
        Analyze the following ONI colony threat and environmental data:
        
        Threat Data:
        {threat_data}
        
        Please provide:
        1. Immediate threat assessment and priority ranking
        2. Environmental stability evaluation
        3. Disease containment strategies
        4. Temperature and pressure management recommendations
        5. Emergency response priorities
        
        Focus on colony survival and threat mitigation strategies.
        """
    
    def _perform_basic_analysis(self, threat_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform basic analysis of threat data."""
        # TODO: Implement actual analysis logic
        return {
            "active_diseases": [],      # List from diseases dict
            "hot_zones": [],           # List from temperature_zones
            "pressure_problems": [],   # List from pressure_issues
            "contaminated_areas": [],  # List from contamination
            "hostile_count": 0,        # Count from hostile_creatures
            "critical_threats": [],    # Highest priority threats
            "environmental_stability": "unknown"  # Overall stability rating
        }
    
    def _generate_alerts(self, threat_data: Dict[str, Any]) -> list:
        """Generate alert messages for critical threat situations."""
        alerts = []
        
        # TODO: Implement actual alert logic
        diseases = threat_data.get("diseases", {})
        for disease_name, disease_info in diseases.items():
            if disease_info.get("severity") == "high":
                alerts.append({
                    "type": "critical", 
                    "message": f"Disease outbreak: {disease_name}",
                    "location": disease_info.get("location", "unknown")
                })
        
        # Temperature alerts
        temp_zones = threat_data.get("temperature_zones", {})
        for zone, temp_info in temp_zones.items():
            if temp_info.get("temperature", 0) > 75:  # Example threshold
                alerts.append({
                    "type": "warning",
                    "message": f"Overheating in {zone}: {temp_info.get('temperature')}°C"
                })
        
        return alerts
    
    def _generate_emergency_actions(self, threat_data: Dict[str, Any]) -> list:
        """Generate immediate emergency actions for critical threats."""
        actions = []
        
        # TODO: Implement actual emergency action logic
        # Examples:
        # - "Quarantine diseased area immediately"
        # - "Build cooling system in overheated zone"
        # - "Evacuate high-pressure area"
        # - "Deploy medical treatment for sick duplicants"
        
        return actions
    
    def _assess_overall_threat_level(self, threat_data: Dict[str, Any]) -> str:
        """Assess overall threat level for the colony."""
        # TODO: Implement actual threat level assessment
        # Consider: number of active threats, severity, spread rate
        
        threat_count = len(threat_data.get("diseases", {}))
        threat_count += len(threat_data.get("pressure_issues", {}))
        threat_count += len(threat_data.get("contamination", {}))
        
        if threat_count == 0:
            return "low"
        elif threat_count <= 2:
            return "moderate"
        else:
            return "high"
    
    async def _on_start(self):
        """Initialize the threat observer agent."""
        self.logger.info(f"Threat Observer Agent {self.agent_id} started")
        self.logger.info("Ready to monitor: diseases, temperature, pressure, contamination, hostiles")
    
    async def _on_stop(self):
        """Cleanup when the threat observer agent stops."""
        self.logger.info(f"Threat Observer Agent {self.agent_id} stopped")
    
    async def _process_message(self, message):
        """Process incoming messages for threat analysis requests."""
        if message.message_type == "analyze_threats":
            result = await self.process_input(message.content)
            await self.send_message(
                message.sender_id,
                "threat_analysis_result",
                result
            )
        elif message.message_type == "emergency_check":
            # Quick emergency status check
            threat_data = message.content.get("threat_data", {})
            threat_level = self._assess_overall_threat_level(threat_data)
            status = {
                "agent": self.agent_id, 
                "threat_level": threat_level,
                "requires_immediate_action": threat_level == "high"
            }
            await self.send_message(
                message.sender_id,
                "emergency_status_response",
                status
            )
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp as string."""
        from datetime import datetime
        return datetime.now().isoformat()
