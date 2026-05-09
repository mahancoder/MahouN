"""
Agent Orchestrator (HAJIX Refactored)
======================================

Central orchestrator for managing agent workflows and data flow.

Features:
    - Sequential workflow execution
    - Parallel agent execution
    - Task history tracking
    - Status monitoring

Usage:
    orchestrator = AgentOrchestrator()
    orchestrator.register_agent(agent)
    
    result = await orchestrator.execute_workflow(
        workflow=[{"agent": "doc_parser"}, {"agent": "dispute"}],
        initial_data={"text": "..."}
    )
"""

from typing import Any, Dict, List, Optional
import asyncio
import logging
from datetime import datetime

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Orchestrator for managing and coordinating agents.
    
    Provides workflow execution, parallel processing, and
    comprehensive task tracking.
    
    Attributes:
        agents: Dictionary of registered agents
        task_history: List of completed task records
    """
    
    def __init__(self):
        """Initialize orchestrator with empty agent registry."""
        self.agents: Dict[str, BaseAgent] = {}
        self.task_history: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(__name__)
    
    def register_agent(self, agent: BaseAgent) -> None:
        """
        Register an agent with the orchestrator.
        
        Args:
            agent: Agent instance to register
        """
        if agent.name in self.agents:
            self.logger.warning(f"Overwriting existing agent: {agent.name}")
        
        self.agents[agent.name] = agent
        self.logger.info(f"Registered agent: {agent.name}")
    
    def unregister_agent(self, agent_name: str) -> None:
        """
        Remove an agent from the orchestrator.
        
        Args:
            agent_name: Name of agent to remove
        """
        if agent_name in self.agents:
            del self.agents[agent_name]
            self.logger.info(f"Unregistered agent: {agent_name}")
        else:
            self.logger.warning(f"Agent not found: {agent_name}")
    
    async def execute_workflow(
        self,
        workflow: List[Dict[str, Any]],
        initial_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a sequential workflow of agents.
        
        Args:
            workflow: List of workflow steps, each with "agent" key
            initial_data: Starting data for the workflow
            
        Returns:
            Workflow result with status, steps, and final data
        """
        task_id = f"task_{datetime.now().isoformat()}"
        self.logger.info(f"Starting workflow: {task_id}")
        
        current_data = initial_data.copy()
        workflow_result = {
            "task_id": task_id,
            "status": "in_progress",
            "steps": [],
            "start_time": datetime.now().isoformat()
        }
        
        try:
            for step_idx, step in enumerate(workflow):
                agent_name = step.get("agent")
                
                if agent_name not in self.agents:
                    raise ValueError(f"Agent not found: {agent_name}")
                
                agent = self.agents[agent_name]
                step_config = step.get("config", {})
                step_input = {**current_data, **step_config}
                
                self.logger.info(f"Executing step {step_idx + 1}: {agent_name}")
                step_start = datetime.now()
                
                try:
                    step_result = await agent.process(step_input)
                    step_duration = (datetime.now() - step_start).total_seconds()
                    
                    workflow_result["steps"].append({
                        "step": step_idx + 1,
                        "agent": agent_name,
                        "status": "success",
                        "duration": step_duration,
                        "result": step_result
                    })
                    
                    current_data.update(step_result)
                    
                except Exception as e:
                    step_duration = (datetime.now() - step_start).total_seconds()
                    error_result = await agent.handle_error(e, step_input)
                    
                    workflow_result["steps"].append({
                        "step": step_idx + 1,
                        "agent": agent_name,
                        "status": "error",
                        "duration": step_duration,
                        "error": error_result
                    })
                    
                    if step.get("required", True):
                        raise
                    
                    self.logger.warning(
                        f"Step {step_idx + 1} failed but not required, continuing"
                    )
            
            workflow_result["status"] = "completed"
            workflow_result["end_time"] = datetime.now().isoformat()
            workflow_result["final_data"] = current_data
            
            self.logger.info(f"Workflow completed: {task_id}")
            
        except Exception as e:
            workflow_result["status"] = "failed"
            workflow_result["error"] = str(e)
            workflow_result["end_time"] = datetime.now().isoformat()
            self.logger.error(f"Workflow failed: {task_id}", exc_info=True)
        
        self.task_history.append(workflow_result)
        return workflow_result
    
    async def execute_parallel(
        self,
        agents: List[str],
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute multiple agents in parallel.
        
        Args:
            agents: List of agent names to execute
            input_data: Input data for all agents
            
        Returns:
            Dictionary mapping agent names to results
        """
        tasks: List[Any] = []
        valid_agents: List[Any] = []
        for agent_name in agents:
            if agent_name not in self.agents:
                self.logger.warning(f"Agent not found, skipping: {agent_name}")
                continue
            
            agent = self.agents[agent_name]
            tasks.append(agent.process(input_data))
            valid_agents.append(agent_name)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            agent_name: (
                result if not isinstance(result, Exception) 
                else {"error": str(result)}
            )
            for agent_name, result in zip(valid_agents, results)
        }
    
    def get_agent_status(
        self, 
        agent_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get status of agents.
        
        Args:
            agent_name: Specific agent name, or None for all agents
            
        Returns:
            Status dictionary for agent(s)
        """
        if agent_name:
            if agent_name in self.agents:
                return self.agents[agent_name].get_status()
            return {"error": f"Agent not found: {agent_name}"}
        
        return {
            name: agent.get_status() 
            for name, agent in self.agents.items()
        }
    
    def get_task_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent task history.
        
        Args:
            limit: Maximum number of tasks to return
            
        Returns:
            List of recent task records
        """
        return self.task_history[-limit:]
