"""
Duplicant Observer Agent

Specialized agent for monitoring and analyzing duplicant-related game state data
from ONI save files (health, skills, morale, assignments, stress, etc.).
"""

from pathlib import Path
from typing import Any, Dict, Optional

from ..core.agent import Agent
from ..core.agent_types import AgentType
from ..services.save_file_parser import SaveFileParser


class DuplicantObserverAgent(Agent):
    """
    Observer agent specialized in duplicant monitoring and analysis.
    
    Responsibilities:
    - Monitor duplicant health and medical conditions
    - Track skill development and training progress
    - Analyze morale and stress levels
    - Monitor job assignments and productivity
    - Detect crew management issues
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
        self.section_name = "duplicants"
    
    async def process_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process duplicant data and generate analysis report.
        
        Args:
            input_data: Should contain either:
                - save_file_path: Path to ONI save file
                - duplicant_data: Pre-extracted duplicant data
                
        Returns:
            Dictionary containing duplicant analysis and recommendations
        """
        try:
            # Extract duplicant data
            if "save_file_path" in input_data:
                save_path = Path(input_data["save_file_path"])
                duplicant_data = self.save_parser.get_section_data(save_path, self.section_name)
            elif "duplicant_data" in input_data:
                duplicant_data = input_data["duplicant_data"]
            else:
                raise ValueError("Either 'save_file_path' or 'duplicant_data' must be provided")
            
            # Generate AI analysis if model is available
            if self.model:
                analysis_prompt = self._create_duplicant_analysis_prompt(duplicant_data)
                ai_analysis = await self.model.generate_response(analysis_prompt)
            else:
                ai_analysis = "No AI model available for analysis"
            
            # Perform basic analysis
            basic_analysis = self._perform_basic_analysis(duplicant_data)
            
            return {
                "agent_id": self.agent_id,
                "section": self.section_name,
                "timestamp": self._get_current_timestamp(),
                "duplicant_data": duplicant_data,
                "basic_analysis": basic_analysis,
                "ai_analysis": ai_analysis,
                "alerts": self._generate_alerts(duplicant_data),
                "recommendations": self._generate_recommendations(duplicant_data)
            }
            
        except Exception as e:
            self.logger.error(f"Error processing duplicant data: {e}")
            return {
                "agent_id": self.agent_id,
                "section": self.section_name,
                "error": str(e),
                "timestamp": self._get_current_timestamp()
            }
    
    def _create_duplicant_analysis_prompt(self, duplicant_data: Dict[str, Any]) -> str:
        """Create a detailed prompt for AI analysis of duplicant data."""
        return f"""
        Analyze the following ONI colony duplicant data and provide insights:
        
        Duplicant Data:
        {duplicant_data}
        
        Please provide:
        1. Overall crew health and wellbeing assessment
        2. Skill gaps and training priorities
        3. Morale and stress management evaluation
        4. Job assignment optimization suggestions
        5. Priority recommendations for crew management
        
        Focus on maintaining a happy, healthy, and productive crew.
        """
    
    def _perform_basic_analysis(self, duplicant_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform basic statistical analysis of duplicant data.

        This consumes the v0.1 duplicant contract with `count` and optional
        `list` entries including `identity`, `role`, and `vitals`.
        """
        entries = duplicant_data.get("list") or []
        total = int(duplicant_data.get("count", len(entries) or 0))
        health_vals = []
        stress_vals = []
        morale_vals = []  # Placeholder until morale available
        unassigned = []
        critical_health = []
        high_stress = []

        for e in entries:
            vit = (e.get("vitals") or {})
            h = vit.get("health")
            s = vit.get("stress")
            if isinstance(h, (int, float)):
                health_vals.append(float(h))
                if h <= 25:
                    critical_health.append(e.get("identity", {}).get("name"))
            if isinstance(s, (int, float)):
                stress_vals.append(float(s))
                if s >= 80:
                    high_stress.append(e.get("identity", {}).get("name"))
            role = e.get("role")
            if role in (None, "", "NoRole"):
                unassigned.append(e.get("identity", {}).get("name"))

        def avg(values):
            return (sum(values) / len(values)) if values else 0.0

        return {
            "total_duplicants": total,
            "average_health": avg(health_vals),
            "average_morale": avg(morale_vals),
            "average_stress": avg(stress_vals),
            "skill_distribution": {},
            "critical_health": [n for n in critical_health if n],
            "high_stress": [n for n in high_stress if n],
            "unassigned_duplicants": [n for n in unassigned if n],
        }
    
    def _generate_alerts(self, duplicant_data: Dict[str, Any]) -> list:
        """Generate alert messages for critical duplicant situations."""
        alerts = []
        
        # TODO: Implement actual alert logic based on health, stress, morale
        duplicant_count = duplicant_data.get("count", 0)
        if duplicant_count == 0:
            alerts.append({"type": "critical", "message": "No duplicants detected!"})
        elif duplicant_count < 3:
            alerts.append({"type": "warning", "message": f"Low crew count: {duplicant_count}"})
        
        # Check for health issues in health_status
        health_status = duplicant_data.get("health_status", {})
        for duplicant_id, health in health_status.items():
            if health == "critical":
                alerts.append({"type": "critical", "message": f"Duplicant {duplicant_id} in critical condition"})
        
        return alerts
    
    def _generate_recommendations(self, duplicant_data: Dict[str, Any]) -> list:
        """Generate actionable recommendations based on duplicant analysis."""
        recommendations = []
        
        # TODO: Implement actual recommendation logic
        # Examples:
        # - "Train more researchers for faster technology development"
        # - "Build recreational facilities to improve morale"
        # - "Reassign duplicants to better match skills"
        # - "Treat sick duplicants immediately"
        # - "Add more beds for growing crew"
        
        return recommendations
    
    async def _on_start(self):
        """Initialize the duplicant observer agent."""
        self.logger.info(f"Duplicant Observer Agent {self.agent_id} started")
        self.logger.info("Ready to monitor: health, skills, morale, assignments, stress")
    
    async def _on_stop(self):
        """Cleanup when the duplicant observer agent stops."""
        self.logger.info(f"Duplicant Observer Agent {self.agent_id} stopped")
    
    async def _process_message(self, message):
        """Process incoming messages for duplicant analysis requests."""
        if message.message_type == "analyze_duplicants":
            result = await self.process_input(message.content)
            await self.send_message(
                message.sender_id,
                "duplicant_analysis_result",
                result
            )
        elif message.message_type == "get_duplicant_status":
            # Quick status check without full analysis
            status = {"agent": self.agent_id, "status": "operational", "section": self.section_name}
            await self.send_message(
                message.sender_id,
                "duplicant_status_response",
                status
            )
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp as string."""
        from datetime import datetime
        return datetime.now().isoformat()
