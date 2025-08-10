"""
Hybrid Workflow Service

Manages the pause-save-analyze-act workflow for ONI AI system.
Coordinates between save file analysis and game interaction.
"""

import logging
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core.agent import Agent
from ..core.agent_types import AgentType
from ..services.save_file_parser import SaveFileParser


class WorkflowStage(Enum):
    """Stages in the hybrid workflow process."""
    WAITING = auto()         # Waiting for user to pause and save
    PARSING = auto()         # Parsing save file data
    ANALYZING = auto()       # AI agents analyzing data
    DECIDING = auto()        # Core agent making decisions
    PRESENTING = auto()      # Presenting recommendations to user
    EXECUTING = auto()       # User executing commands (manual or automated)
    COMPLETED = auto()       # Cycle completed


class WorkflowSession:
    """Represents a single analysis session from save file to recommendations."""
    
    def __init__(self, session_id: str, save_file_path: Path):
        self.session_id = session_id
        self.save_file_path = save_file_path
        self.stage = WorkflowStage.WAITING
        self.started_at = datetime.now()
        self.results: Dict[str, Any] = {}
        self.recommendations: List[Dict[str, Any]] = []
        self.errors: List[str] = []


class HybridWorkflowManager:
    """
    Manages the hybrid pause-analyze-act workflow.
    
    Workflow Steps:
    1. User pauses game and saves
    2. System parses save file
    3. Observer agents analyze their sections
    4. Core agent synthesizes analysis and makes decisions
    5. System presents recommendations to user
    6. User executes recommendations (manual or automated)
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.save_parser = SaveFileParser()
        self.active_sessions: Dict[str, WorkflowSession] = {}
        self.observer_agents: Dict[str, Agent] = {}
        self.core_agent: Optional[Agent] = None
        
    def register_observer_agent(self, section_name: str, agent: Agent):
        """Register an observer agent for a specific save file section."""
        if agent.agent_type != AgentType.OBSERVING:
            raise ValueError(f"Agent must be of type OBSERVING, got {agent.agent_type}")
        
        self.observer_agents[section_name] = agent
        self.logger.info(f"Registered observer agent for section: {section_name}")
    
    def register_core_agent(self, agent: Agent):
        """Register the core decision-making agent."""
        if agent.agent_type != AgentType.CORE:
            raise ValueError(f"Agent must be of type CORE, got {agent.agent_type}")
        
        self.core_agent = agent
        self.logger.info("Registered core agent")
    
    async def start_analysis_session(self, save_file_path: Path, session_id: Optional[str] = None) -> str:
        """
        Start a new analysis session for a save file.
        
        Args:
            save_file_path: Path to the ONI save file
            session_id: Optional custom session ID
            
        Returns:
            Session ID for tracking progress
        """
        if session_id is None:
            session_id = f"session_{int(datetime.now().timestamp())}"
        
        if not save_file_path.exists():
            raise FileNotFoundError(f"Save file not found: {save_file_path}")
        
        session = WorkflowSession(session_id, save_file_path)
        self.active_sessions[session_id] = session
        
        self.logger.info(f"Started analysis session {session_id} for {save_file_path}")
        
        # Begin the analysis workflow
        await self._execute_workflow(session)
        
        return session_id
    
    async def _execute_workflow(self, session: WorkflowSession):
        """Execute the complete workflow for a session."""
        try:
            # Stage 1: Parse save file
            session.stage = WorkflowStage.PARSING
            await self._parse_save_file(session)
            
            # Stage 2: Analyze with observer agents
            session.stage = WorkflowStage.ANALYZING
            await self._run_observer_analysis(session)
            
            # Stage 3: Core agent decision making
            session.stage = WorkflowStage.DECIDING
            await self._run_core_analysis(session)
            
            # Stage 4: Present recommendations
            session.stage = WorkflowStage.PRESENTING
            await self._prepare_recommendations(session)
            
            session.stage = WorkflowStage.COMPLETED
            self.logger.info(f"Workflow completed for session {session.session_id}")
            
        except Exception as e:
            self.logger.error(f"Workflow error in session {session.session_id}: {e}")
            session.errors.append(str(e))
    
    async def _parse_save_file(self, session: WorkflowSession):
        """Parse the save file and extract section data."""
        self.logger.info(f"Parsing save file for session {session.session_id}")
        
        # Parse all sections
        parsed_data = self.save_parser.parse_save_file(session.save_file_path)
        session.results["save_data"] = parsed_data
        
        self.logger.debug(f"Parsed {len(parsed_data)} sections from save file")
    
    async def _run_observer_analysis(self, session: WorkflowSession):
        """Run analysis on all registered observer agents."""
        self.logger.info(f"Running observer analysis for session {session.session_id}")
        
        observer_results = {}
        save_data = session.results["save_data"]
        
        for section_name, agent in self.observer_agents.items():
            try:
                section_data = save_data.get(section_name, {})
                input_data = {
                    "save_file_path": str(session.save_file_path),
                    f"{section_name}_data": section_data
                }
                
                result = await agent.process_input(input_data)
                observer_results[section_name] = result
                
                self.logger.debug(f"Completed analysis for section: {section_name}")
                
            except Exception as e:
                self.logger.error(f"Error in {section_name} observer: {e}")
                session.errors.append(f"Observer {section_name}: {str(e)}")
        
        session.results["observer_analysis"] = observer_results
        self.logger.info(f"Completed analysis from {len(observer_results)} observers")
    
    async def _run_core_analysis(self, session: WorkflowSession):
        """Run core agent analysis and decision making."""
        if not self.core_agent:
            self.logger.warning("No core agent registered, skipping core analysis")
            return
        
        self.logger.info(f"Running core analysis for session {session.session_id}")
        
        # Prepare comprehensive input for core agent
        core_input = {
            "session_id": session.session_id,
            "save_file_path": str(session.save_file_path),
            "observer_results": session.results.get("observer_analysis", {}),
            "raw_save_data": session.results.get("save_data", {})
        }
        
        try:
            core_result = await self.core_agent.process_input(core_input)
            session.results["core_analysis"] = core_result
            
            self.logger.info("Core analysis completed")
            
        except Exception as e:
            self.logger.error(f"Error in core analysis: {e}")
            session.errors.append(f"Core agent: {str(e)}")
    
    async def _prepare_recommendations(self, session: WorkflowSession):
        """Prepare final recommendations for the user."""
        self.logger.info(f"Preparing recommendations for session {session.session_id}")
        
        recommendations = []
        
        # Collect recommendations from observer agents
        observer_analysis = session.results.get("observer_analysis", {})
        for section_name, analysis in observer_analysis.items():
            if "recommendations" in analysis:
                for rec in analysis["recommendations"]:
                    recommendations.append({
                        "source": f"{section_name}_observer",
                        "type": "section_specific",
                        "recommendation": rec,
                        "priority": "medium"  # Default priority
                    })
        
        # Add core agent recommendations
        core_analysis = session.results.get("core_analysis", {})
        if "recommendations" in core_analysis:
            for rec in core_analysis["recommendations"]:
                recommendations.append({
                    "source": "core_agent",
                    "type": "strategic",
                    "recommendation": rec,
                    "priority": "high"  # Core recommendations are high priority
                })
        
        session.recommendations = recommendations
        self.logger.info(f"Prepared {len(recommendations)} recommendations")
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get current status of an analysis session."""
        if session_id not in self.active_sessions:
            return {"error": f"Session {session_id} not found"}
        
        session = self.active_sessions[session_id]
        
        return {
            "session_id": session_id,
            "stage": session.stage.name,
            "started_at": session.started_at.isoformat(),
            "save_file": str(session.save_file_path),
            "recommendations_count": len(session.recommendations),
            "errors": session.errors,
            "completed": session.stage == WorkflowStage.COMPLETED
        }
    
    def get_session_recommendations(self, session_id: str) -> List[Dict[str, Any]]:
        """Get recommendations for a completed session."""
        if session_id not in self.active_sessions:
            return []
        
        session = self.active_sessions[session_id]
        return session.recommendations
    
    def get_session_results(self, session_id: str) -> Dict[str, Any]:
        """Get full results for a session."""
        if session_id not in self.active_sessions:
            return {}
        
        session = self.active_sessions[session_id]
        return session.results
    
    def cleanup_session(self, session_id: str):
        """Remove a session from active sessions."""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            self.logger.info(f"Cleaned up session {session_id}")
    
    def get_registered_agents(self) -> Dict[str, str]:
        """Get information about registered agents."""
        agents_info = {}
        
        for section, agent in self.observer_agents.items():
            agents_info[f"observer_{section}"] = agent.agent_id
        
        if self.core_agent:
            agents_info["core"] = self.core_agent.agent_id
        
        return agents_info
