"""
Hierarchical Swarm Implementation

This module provides a hierarchical swarm architecture where a director agent coordinates
multiple worker agents to execute complex tasks through a structured workflow.

Flow:
1. User provides a task
2. Director creates a plan
3. Director distributes orders to agents individually or multiple tasks at once
4. Agents execute tasks and report back to the director
5. Director evaluates results and issues new orders if needed (up to max_loops)
6. All context and conversation history is preserved throughout the process

Todo

- Add layers of management -- a list of list of agents that act as departments
- Auto build agents from input prompt - and then add them to the swarm
- Create an interactive and dynamic UI like we did with heavy swarm
- Make it faster and more high performance
- Enable the director to choose a multi-agent approach to the task, it orchestrates how the agents talk and work together.
- Improve the director feedback, maybe add agent as a judge to the worker agent instead of the director.
- Use agent rearrange to orchestrate the agents

Classes:
    HierarchicalOrder: Represents a single task assignment to a specific agent
    SwarmSpec: Contains the overall plan and list of orders for the swarm
    HierarchicalSwarm: Main swarm orchestrator that manages director and worker agents
"""

import time
import traceback
from typing import Any, Callable, List, Optional, Union

from loguru import logger
from pydantic import BaseModel, Field
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from swarms.prompts.hiearchical_system_prompt import (
    HIEARCHICAL_SWARM_SYSTEM_PROMPT,
)
from swarms.prompts.multi_agent_collab_prompt import (
    MULTI_AGENT_COLLAB_PROMPT_TWO,
)
from swarms.prompts.reasoning_prompt import INTERNAL_MONOLGUE_PROMPT
from swarms.structs.agent import Agent
from swarms.structs.conversation import Conversation
from swarms.structs.ma_utils import list_all_agents
from swarms.structs.omni_agent_types import AgentListType
from swarms.tools.base_tool import BaseTool
from swarms.utils.history_output_formatter import (
    history_output_formatter,
)
from swarms.utils.output_types import OutputType


class HierarchicalSwarmDashboard:
    """
    Futuristic Arasaka Corporation-style dashboard for hierarchical swarm monitoring.

    This dashboard provides a professional, enterprise-grade interface with red and black
    color scheme, real-time monitoring of swarm operations, and cyberpunk aesthetics.

    Attributes:
        console (Console): Rich console instance for rendering
        live_display (Live): Live display for real-time updates
        swarm_name (str): Name of the swarm being monitored
        agent_statuses (dict): Current status of all agents
        director_status (str): Current status of the director
        current_loop (int): Current execution loop
        max_loops (int): Maximum number of loops
        is_active (bool): Whether the dashboard is currently active
    """

    def __init__(self, swarm_name: str = "Swarms Corporation"):
        """
        Initialize the Arasaka dashboard.

        Args:
            swarm_name (str): Name of the swarm to display in the dashboard
        """
        self.console = Console()
        self.live_display = None
        self.swarm_name = swarm_name
        self.agent_statuses = {}
        self.director_status = "INITIALIZING"
        self.current_loop = 0
        self.max_loops = 1
        self.is_active = False
        self.start_time = None
        self.spinner_frames = [
            "⠋",
            "⠙",
            "⠹",
            "⠸",
            "⠼",
            "⠴",
            "⠦",
            "⠧",
            "⠇",
            "⠏",
        ]
        self.spinner_idx = 0

        # Director information tracking
        self.director_plan = ""
        self.director_orders = []

        # Swarm information
        self.swarm_description = ""
        self.director_name = "Director"
        self.director_model_name = "gpt-4o-mini"

        # View mode for agents display
        self.detailed_view = False

        # Multi-loop agent tracking
        self.agent_history = {}  # Track agent outputs across loops
        self.current_loop = 0

    def _get_spinner(self) -> str:
        """Get current spinner frame for loading animations."""
        self.spinner_idx = (self.spinner_idx + 1) % len(
            self.spinner_frames
        )
        return self.spinner_frames[self.spinner_idx]

    def _create_header(self) -> Panel:
        """Create the dashboard header with Swarms Corporation branding."""
        header_text = Text()
        header_text.append(
            "╔══════════════════════════════════════════════════════════════════════════════╗\n",
            style="bold red",
        )
        header_text.append("║", style="bold red")
        header_text.append("                    ", style="bold red")
        header_text.append(
            "SWARMS CORPORATION", style="bold white on red"
        )
        header_text.append("                    ", style="bold red")
        header_text.append("║\n", style="bold red")
        header_text.append("║", style="bold red")
        header_text.append("                    ", style="bold red")
        header_text.append(
            "HIERARCHICAL SWARM OPERATIONS CENTER", style="bold red"
        )
        header_text.append("                    ", style="bold red")
        header_text.append("║\n", style="bold red")
        header_text.append(
            "╚══════════════════════════════════════════════════════════════════════════════╝",
            style="bold red",
        )

        return Panel(
            header_text,
            border_style="red",
            padding=(0, 1),
        )

    def _create_status_panel(self) -> Panel:
        """Create the operations status panel."""
        status_text = Text()

        # Corporation branding and operation type
        status_text.append(
            "By the Swarms Corporation", style="bold cyan"
        )
        status_text.append("\n", style="white")
        status_text.append(
            "Hierarchical Agent Operations", style="bold white"
        )

        status_text.append("\n\n", style="white")

        # Swarm information
        status_text.append("SWARM NAME: ", style="bold white")
        status_text.append(f"{self.swarm_name}", style="bold cyan")

        status_text.append("\n", style="white")
        status_text.append("DESCRIPTION: ", style="bold white")
        status_text.append(f"{self.swarm_description}", style="white")

        status_text.append("\n", style="white")
        status_text.append("DIRECTOR: ", style="bold white")
        status_text.append(
            f"{self.director_name} ({self.director_model_name})",
            style="cyan",
        )

        status_text.append("\n", style="white")
        status_text.append("TOTAL LOOPS: ", style="bold white")
        status_text.append(f"{self.max_loops}", style="bold cyan")

        status_text.append("  |  ", style="white")
        status_text.append("CURRENT LOOP: ", style="bold white")
        status_text.append(
            f"{self.current_loop}", style="bold yellow"
        )

        # Agent count metadata
        agent_count = len(getattr(self, "agent_history", {}))
        status_text.append("  |  ", style="white")
        status_text.append("AGENTS: ", style="bold white")
        status_text.append(f"{agent_count}", style="bold green")

        status_text.append("\n\n", style="white")

        # Director status
        status_text.append("DIRECTOR STATUS: ", style="bold white")
        if self.director_status == "INITIALIZING":
            status_text.append(
                f"{self._get_spinner()} {self.director_status}",
                style="bold yellow",
            )
        elif self.director_status == "ACTIVE":
            status_text.append(
                f"✓ {self.director_status}", style="bold green"
            )
        elif self.director_status == "PROCESSING":
            status_text.append(
                f"{self._get_spinner()} {self.director_status}",
                style="bold cyan",
            )
        else:
            status_text.append(
                f"✗ {self.director_status}", style="bold red"
            )

        status_text.append("\n\n", style="white")

        # Runtime and completion information
        if self.start_time:
            runtime = time.time() - self.start_time
            status_text.append("RUNTIME: ", style="bold white")
            status_text.append(f"{runtime:.2f}s", style="bold green")

            # Add completion percentage if loops are running
            if self.max_loops > 0:
                completion_percent = (
                    self.current_loop / self.max_loops
                ) * 100
                status_text.append("  |  ", style="white")
                status_text.append("PROGRESS: ", style="bold white")
                status_text.append(
                    f"{completion_percent:.1f}%", style="bold cyan"
                )

        return Panel(
            status_text,
            border_style="red",
            padding=(1, 2),
            title="[bold white]OPERATIONS STATUS[/bold white]",
        )

    def _create_agents_table(self) -> Table:
        """Create the agents monitoring table with full outputs and loop history."""
        table = Table(
            show_header=True,
            header_style="bold white on red",
            border_style="red",
            title="[bold white]AGENT MONITORING MATRIX[/bold white]",
            title_style="bold white",
            show_lines=True,
        )

        table.add_column("AGENT ID", style="bold cyan", width=25)
        table.add_column("LOOP", style="bold white", width=8)
        table.add_column("STATUS", style="bold white", width=15)
        table.add_column("TASK", style="white", width=40)
        table.add_column("OUTPUT", style="white", width=150)

        # Display agents with their history across loops
        for agent_name, history in self.agent_history.items():
            for loop_num in range(self.max_loops + 1):
                loop_key = f"Loop_{loop_num}"

                if loop_key in history:
                    loop_data = history[loop_key]
                    status = loop_data.get("status", "UNKNOWN")
                    task = loop_data.get("task", "N/A")
                    output = loop_data.get("output", "")

                    # Style status
                    if status == "RUNNING":
                        status_display = (
                            f"{self._get_spinner()} {status}"
                        )
                        status_style = "bold yellow"
                    elif status == "COMPLETED":
                        status_display = f"✓ {status}"
                        status_style = "bold green"
                    elif status == "PENDING":
                        status_display = f"○ {status}"
                        status_style = "bold red"
                    else:
                        status_display = f"✗ {status}"
                        status_style = "bold red"

                    # Show full output without truncation
                    output_display = output if output else "No output"

                    table.add_row(
                        Text(agent_name, style="bold cyan"),
                        Text(f"Loop {loop_num}", style="bold white"),
                        Text(status_display, style=status_style),
                        Text(task, style="white"),
                        Text(output_display, style="white"),
                    )

        return table

    def _create_detailed_agents_view(self) -> Panel:
        """Create a detailed view of agents with full outputs and loop history."""
        detailed_text = Text()

        for agent_name, history in self.agent_history.items():
            detailed_text.append(
                f"AGENT: {agent_name}\n", style="bold cyan"
            )
            detailed_text.append("=" * 80 + "\n", style="red")

            for loop_num in range(self.max_loops + 1):
                loop_key = f"Loop_{loop_num}"

                if loop_key in history:
                    loop_data = history[loop_key]
                    status = loop_data.get("status", "UNKNOWN")
                    task = loop_data.get("task", "N/A")
                    output = loop_data.get("output", "")

                    detailed_text.append(
                        f"LOOP {loop_num}:\n", style="bold white"
                    )
                    detailed_text.append(
                        f"STATUS: {status}\n", style="bold white"
                    )
                    detailed_text.append(
                        f"TASK: {task}\n", style="white"
                    )
                    detailed_text.append(
                        "OUTPUT:\n", style="bold white"
                    )
                    detailed_text.append(f"{output}\n", style="white")
                    detailed_text.append("─" * 80 + "\n", style="red")

        return Panel(
            detailed_text,
            border_style="red",
            padding=(1, 2),
            title="[bold white]DETAILED AGENT OUTPUTS (FULL HISTORY)[/bold white]",
        )

    def _create_director_panel(self) -> Panel:
        """Create the director information panel showing plan and orders."""
        director_text = Text()

        # Plan section
        director_text.append("DIRECTOR PLAN:\n", style="bold white")
        if self.director_plan:
            director_text.append(self.director_plan, style="white")
        else:
            director_text.append(
                "No plan available", style="dim white"
            )

        director_text.append("\n\n", style="white")

        # Orders section
        director_text.append("CURRENT ORDERS:\n", style="bold white")
        if self.director_orders:
            for i, order in enumerate(
                self.director_orders
            ):  # Show first 5 orders
                director_text.append(f"{i+1}. ", style="bold cyan")
                director_text.append(
                    f"{order.get('agent_name', 'Unknown')}: ",
                    style="bold white",
                )
                task = order.get("task", "No task")
                director_text.append(task, style="white")
                director_text.append("\n", style="white")

            if len(self.director_orders) > 5:
                director_text.append(
                    f"... and {len(self.director_orders) - 5} more orders",
                    style="dim white",
                )
        else:
            director_text.append(
                "No orders available", style="dim white"
            )

        return Panel(
            director_text,
            border_style="red",
            padding=(1, 2),
            title="[bold white]DIRECTOR OPERATIONS[/bold white]",
        )

    def _create_dashboard_layout(self) -> Layout:
        """Create the complete dashboard layout."""
        layout = Layout()

        # Split into operations status, director operations, and agents
        layout.split_column(
            Layout(name="operations_status", size=12),
            Layout(name="director_operations", size=12),
            Layout(name="agents", ratio=1),
        )

        # Add content to each section
        layout["operations_status"].update(
            self._create_status_panel()
        )
        layout["director_operations"].update(
            self._create_director_panel()
        )

        # Choose between table view and detailed view
        if self.detailed_view:
            layout["agents"].update(
                self._create_detailed_agents_view()
            )
        else:
            layout["agents"].update(
                Panel(
                    self._create_agents_table(),
                    border_style="red",
                    padding=(1, 1),
                )
            )

        return layout

    def start(self, max_loops: int = 1):
        """Start the dashboard display."""
        self.max_loops = max_loops
        self.start_time = time.time()
        self.is_active = True

        self.live_display = Live(
            self._create_dashboard_layout(),
            console=self.console,
            refresh_per_second=10,
            transient=False,
        )
        self.live_display.start()

    def update_agent_status(
        self,
        agent_name: str,
        status: str,
        task: str = "",
        output: str = "",
    ):
        """Update the status of a specific agent."""
        # Create loop key for tracking history
        loop_key = f"Loop_{self.current_loop}"

        # Initialize agent history if not exists
        if agent_name not in self.agent_history:
            self.agent_history[agent_name] = {}

        # Store current status and add to history
        self.agent_statuses[agent_name] = {
            "status": status,
            "task": task,
            "output": output,
        }

        # Add to history for this loop
        self.agent_history[agent_name][loop_key] = {
            "status": status,
            "task": task,
            "output": output,
        }

        if self.live_display and self.is_active:
            self.live_display.update(self._create_dashboard_layout())

    def update_director_status(self, status: str):
        """Update the director status."""
        self.director_status = status
        if self.live_display and self.is_active:
            self.live_display.update(self._create_dashboard_layout())

    def update_loop(self, current_loop: int):
        """Update the current execution loop."""
        self.current_loop = current_loop
        if self.live_display and self.is_active:
            self.live_display.update(self._create_dashboard_layout())

    def update_director_plan(self, plan: str):
        """Update the director's plan."""
        self.director_plan = plan
        if self.live_display and self.is_active:
            self.live_display.update(self._create_dashboard_layout())

    def update_director_orders(self, orders: list):
        """Update the director's orders."""
        self.director_orders = orders
        if self.live_display and self.is_active:
            self.live_display.update(self._create_dashboard_layout())

    def stop(self):
        """Stop the dashboard display."""
        self.is_active = False
        if self.live_display:
            self.live_display.stop()
            self.console.print()

    def update_swarm_info(
        self,
        name: str,
        description: str,
        max_loops: int,
        director_name: str,
        director_model_name: str,
    ):
        """Update the dashboard with swarm-specific information."""
        self.swarm_name = name
        self.swarm_description = description
        self.max_loops = max_loops
        self.director_name = director_name
        self.director_model_name = director_model_name
        if self.live_display and self.is_active:
            self.live_display.update(self._create_dashboard_layout())

    def force_refresh(self):
        """Force refresh the dashboard display."""
        if self.live_display and self.is_active:
            self.live_display.update(self._create_dashboard_layout())

    def show_full_output(self, agent_name: str, full_output: str):
        """Display full agent output in a separate panel."""
        if self.live_display and self.is_active:
            # Create a full output panel
            output_panel = Panel(
                Text(full_output, style="white"),
                title=f"[bold white]FULL OUTPUT - {agent_name}[/bold white]",
                border_style="red",
                padding=(1, 2),
                width=120,
            )

            # Temporarily show the full output
            self.console.print(output_panel)
            self.console.print()  # Add spacing

    def toggle_detailed_view(self):
        """Toggle between table view and detailed view."""
        self.detailed_view = not self.detailed_view
        if self.live_display and self.is_active:
            self.live_display.update(self._create_dashboard_layout())


class HierarchicalOrder(BaseModel):
    """
    Represents a single task assignment within the hierarchical swarm.

    This class defines the structure for individual task orders that the director
    distributes to worker agents. Each order specifies which agent should execute
    what specific task.

    Attributes:
        agent_name (str): The name of the agent assigned to execute the task.
                         Must match an existing agent in the swarm.
        task (str): The specific task description to be executed by the assigned agent.
                   Should be clear and actionable.
    """

    agent_name: str = Field(
        ...,
        description="Specifies the name of the agent to which the task is assigned. This is a crucial element in the hierarchical structure of the swarm, as it determines the specific agent responsible for the task execution.",
    )
    task: str = Field(
        ...,
        description="Defines the specific task to be executed by the assigned agent. This task is a key component of the swarm's plan and is essential for achieving the swarm's goals.",
    )


class HierarchicalOrderRearrange(BaseModel):
    """
    Represents a single task assignment within the hierarchical swarm.

    This class defines the structure for individual task orders that the director
    distributes to worker agents. Each order specifies which agent should execute
    what specific task.
    """

    initial_task: str = Field(
        ...,
        description="The initial task that the director has to execute.",
    )
    flow_of_communication: str = Field(
        ...,
        description="How the agents will communicate with each other to accomplish the task. Like agent_one -> agent_two -> agent_three -> agent_four -> agent_one, can use comma signs to denote sequential communication and commas to denote parallel communication for example agent_one -> agent_two, agent_three -> agent_four",
    )


class SwarmSpec(BaseModel):
    """
    Defines the complete specification for a hierarchical swarm execution.

    This class contains the overall plan and all individual orders that the director
    creates to coordinate the swarm's activities. It serves as the structured output
    format for the director agent.

    Attributes:
        plan (str): A comprehensive plan outlining the sequence of actions and strategy
                   for the entire swarm to accomplish the given task.
        orders (List[HierarchicalOrder]): A list of specific task assignments to
                                         individual agents within the swarm.
    """

    # # thoughts: str = Field(
    # #     ...,
    # #     description="A plan generated by the director agent for the swarm to accomplish the given task, where the director autonomously reasons through the problem, devises its own strategy, and determines the sequence of actions. "
    # #     "This plan reflects the director's independent thought process, outlining the rationale, priorities, and steps it deems necessary for successful execution. "
    # #     "It serves as a blueprint for the swarm, enabling agents to follow the director's self-derived guidance and adapt as needed throughout the process.",
    # )

    plan: str = Field(
        ...,
        description="A plan generated by the director agent for the swarm to accomplish the given task, where the director autonomously reasons through the problem, devises its own strategy, and determines the sequence of actions. "
        "This plan reflects the director's independent thought process, outlining the rationale, priorities, and steps it deems necessary for successful execution. "
        "It serves as a blueprint for the swarm, enabling agents to follow the director's self-derived guidance and adapt as needed throughout the process.",
    )

    orders: List[HierarchicalOrder] = Field(
        ...,
        description="A collection of task assignments to specific agents within the swarm. These orders are the specific instructions that guide the agents in their task execution and are a key element in the swarm's plan.",
    )


class HierarchicalSwarm:
    """
    A hierarchical swarm orchestrator that coordinates multiple agents through a director.

    This class implements a hierarchical architecture where a director agent creates
    plans and distributes tasks to worker agents. The director can provide feedback
    and iterate on results through multiple loops to achieve the desired outcome.

    The swarm maintains conversation history throughout the process, allowing for
    context-aware decision making and iterative refinement of results.

    Attributes:
        name (str): The name identifier for this swarm instance.
        description (str): A description of the swarm's purpose and capabilities.
        director (Optional[Union[Agent, Callable, Any]]): The director agent that
                                                         coordinates the swarm.
        agents (List[Union[Agent, Callable, Any]]): List of worker agents available
                                                   for task execution.
        max_loops (int): Maximum number of feedback loops the swarm can perform.
        output_type (OutputType): Format for the final output of the swarm.
        feedback_director_model_name (str): Model name for the feedback director.
        director_name (str): Name identifier for the director agent.
        director_model_name (str): Model name for the main director agent.
        verbose (bool): Whether to enable detailed logging and progress tracking.
        add_collaboration_prompt (bool): Whether to add collaboration prompts to agents.
        planning_director_agent (Optional[Union[Agent, Callable, Any]]): Optional
                                                                        planning agent.
        director_feedback_on (bool): Whether director feedback is enabled.
    """

    def __init__(
        self,
        name: str = "HierarchicalAgentSwarm",
        description: str = "Distributed task swarm",
        director: Optional[Union[Agent, Callable, Any]] = None,
        agents: AgentListType = None,
        max_loops: int = 1,
        output_type: OutputType = "dict-all-except-first",
        feedback_director_model_name: str = "gpt-4o-mini",
        director_name: str = "Director",
        director_model_name: str = "gpt-4o-mini",
        verbose: bool = False,
        add_collaboration_prompt: bool = True,
        planning_director_agent: Optional[
            Union[Agent, Callable, Any]
        ] = None,
        director_feedback_on: bool = True,
        interactive: bool = False,
        director_system_prompt: str = HIEARCHICAL_SWARM_SYSTEM_PROMPT,
        director_reasoning_model_name: str = "o3-mini",
        director_reasoning_enabled: bool = False,
        multi_agent_prompt_improvements: bool = False,
        *args,
        **kwargs,
    ):
        """
        Initialize a new HierarchicalSwarm instance.

        Args:
            name (str): The name identifier for this swarm instance.
            description (str): A description of the swarm's purpose.
            director (Optional[Union[Agent, Callable, Any]]): The director agent.
                                                             If None, a default director will be created.
            agents (List[Union[Agent, Callable, Any]]): List of worker agents.
                                                       Must not be empty.
            max_loops (int): Maximum number of feedback loops (must be > 0).
            output_type (OutputType): Format for the final output.
            feedback_director_model_name (str): Model name for feedback director.
            director_name (str): Name identifier for the director agent.
            director_model_name (str): Model name for the main director agent.
            verbose (bool): Whether to enable detailed logging.
            add_collaboration_prompt (bool): Whether to add collaboration prompts.
            planning_director_agent (Optional[Union[Agent, Callable, Any]]):
                Optional planning agent for enhanced planning capabilities.
            director_feedback_on (bool): Whether director feedback is enabled.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Raises:
            ValueError: If no agents are provided or max_loops is invalid.
        """
        self.name = name
        self.description = description
        self.director = director
        self.agents = agents
        self.max_loops = max_loops
        self.output_type = output_type
        self.feedback_director_model_name = (
            feedback_director_model_name
        )
        self.director_name = director_name
        self.verbose = verbose
        self.director_model_name = director_model_name
        self.add_collaboration_prompt = add_collaboration_prompt
        self.planning_director_agent = planning_director_agent
        self.director_feedback_on = director_feedback_on
        self.interactive = interactive
        self.director_system_prompt = director_system_prompt
        self.director_reasoning_model_name = (
            director_reasoning_model_name
        )
        self.director_reasoning_enabled = director_reasoning_enabled
        self.multi_agent_prompt_improvements = (
            multi_agent_prompt_improvements
        )

        self.initialize_swarm()

    def initialize_swarm(self):
        if self.interactive:
            self.agents_no_print()

        # Initialize dashboard if interactive mode is enabled
        self.dashboard = None
        if self.interactive:
            self.dashboard = HierarchicalSwarmDashboard(self.name)
            # Enable detailed view for better output visibility
            self.dashboard.detailed_view = True
            # Pass additional swarm information to dashboard
            self.dashboard.update_swarm_info(
                name=self.name,
                description=self.description,
                max_loops=self.max_loops,
                director_name=self.director_name,
                director_model_name=self.director_model_name,
            )

        self.init_swarm()

    def list_worker_agents(self) -> str:
        return list_all_agents(
            agents=self.agents,
            add_to_conversation=False,
        )

    def prepare_worker_agents(self):
        for agent in self.agents:
            prompt = (
                MULTI_AGENT_COLLAB_PROMPT_TWO
                + self.list_worker_agents()
            )
            if hasattr(agent, "system_prompt"):
                agent.system_prompt += prompt
            else:
                agent.system_prompt = prompt

    def reasoning_agent_run(
        self, task: str, img: Optional[str] = None
    ):
        """
        Run a reasoning agent to analyze the task before the main director processes it.

        Args:
            task (str): The task to reason about
            img (Optional[str]): Optional image input

        Returns:
            str: The reasoning output from the agent
        """

        agent = Agent(
            agent_name=self.director_name,
            agent_description=f"You're the {self.director_name} agent that is responsible for reasoning about the task and creating a plan for the swarm to accomplish the task.",
            model_name=self.director_reasoning_model_name,
            system_prompt=INTERNAL_MONOLGUE_PROMPT
            + self.director_system_prompt,
            max_loops=1,
        )

        prompt = f"Conversation History: {self.conversation.get_str()} \n\n Task: {task}"

        return agent.run(task=prompt, img=img)

    def init_swarm(self):
        """
        Initialize the swarm with proper configuration and validation.

        This method performs the following initialization steps:
        1. Sets up logging if verbose mode is enabled
        2. Creates a conversation instance for history tracking
        3. Performs reliability checks on the configuration
        4. Adds agent context to the director

        Raises:
            ValueError: If the swarm configuration is invalid.
        """
        # Initialize logger only if verbose is enabled
        if self.verbose:
            logger.info(
                f"[INIT] Initializing HierarchicalSwarm: {self.name}"
            )

        self.conversation = Conversation(time_enabled=False)

        # Reliability checks
        self.reliability_checks()

        self.add_context_to_director()

        # Initialize agent statuses in dashboard if interactive mode
        if self.interactive and self.dashboard:
            for agent in self.agents:
                if hasattr(agent, "agent_name"):
                    self.dashboard.update_agent_status(
                        agent.agent_name,
                        "PENDING",
                        "Awaiting task assignment",
                        "Ready for deployment",
                    )
            # Force refresh to ensure agents are displayed
            self.dashboard.force_refresh()

        if self.verbose:
            logger.success(
                f"[SUCCESS] HierarchicalSwarm: {self.name} initialized successfully."
            )

        if self.multi_agent_prompt_improvements:
            self.prepare_worker_agents()

    def add_context_to_director(self):
        """
        Add agent context and collaboration information to the director's conversation.

        This method ensures that the director has complete information about all
        available agents, their capabilities, and how they can collaborate. This
        context is essential for the director to make informed decisions about
        task distribution.

        Raises:
            Exception: If adding context fails due to agent configuration issues.
        """
        try:
            if self.verbose:
                logger.info("[INFO] Adding agent context to director")

            list_all_agents(
                agents=self.agents,
                conversation=self.conversation,
                add_to_conversation=True,
                add_collaboration_prompt=self.add_collaboration_prompt,
            )

            if self.verbose:
                logger.success(
                    "[SUCCESS] Agent context added to director successfully"
                )

        except Exception as e:
            error_msg = (
                f"[ERROR] Failed to add context to director: {str(e)}"
            )
            logger.error(
                f"{error_msg}\n[TRACE] Traceback: {traceback.format_exc()}"
            )

    def setup_director(self):
        """
        Set up the director agent with proper configuration and tools.

        Creates a new director agent with the SwarmSpec schema for structured
        output, enabling it to create plans and distribute orders effectively.

        Returns:
            Agent: A configured director agent ready to coordinate the swarm.

        Raises:
            Exception: If director setup fails due to configuration issues.
        """
        try:
            if self.verbose:
                logger.info("[SETUP] Setting up director agent")

            schema = BaseTool().base_model_to_dict(SwarmSpec)

            if self.verbose:
                logger.debug(f"[SCHEMA] Director schema: {schema}")

            return Agent(
                agent_name=self.director_name,
                agent_description="A director agent that can create a plan and distribute orders to agents",
                system_prompt=self.director_system_prompt,
                model_name=self.director_model_name,
                max_loops=1,
                base_model=SwarmSpec,
                tools_list_dictionary=[schema],
                output_type="dict-all-except-first",
            )

        except Exception as e:
            error_msg = f"[ERROR] Failed to setup director: {str(e)}\n[TRACE] Traceback: {traceback.format_exc()}\n[BUG] If this issue persists, please report it at: https://github.com/kyegomez/swarms/issues"
            logger.error(error_msg)

    def reliability_checks(self):
        """
        Perform validation checks to ensure the swarm is properly configured.

        This method validates:
        1. That at least one agent is provided
        2. That max_loops is greater than 0
        3. That a director is available (creates default if needed)

        Raises:
            ValueError: If the swarm configuration is invalid.
        """
        try:
            if self.verbose:
                logger.info(
                    f"Hiearchical Swarm: {self.name} Reliability checks in progress..."
                )

            if not self.agents or len(self.agents) == 0:
                raise ValueError(
                    "No agents found in the swarm. At least one agent must be provided to create a hierarchical swarm."
                )

            if self.max_loops <= 0:
                raise ValueError(
                    "Max loops must be greater than 0. Please set a valid number of loops."
                )

            if self.director is None:
                self.director = self.setup_director()

            if self.verbose:
                logger.success(
                    f"Hiearchical Swarm: {self.name} Reliability checks passed..."
                )

        except Exception as e:
            error_msg = f"[ERROR] Failed to setup director: {str(e)}\n[TRACE] Traceback: {traceback.format_exc()}\n[BUG] If this issue persists, please report it at: https://github.com/kyegomez/swarms/issues"
            logger.error(error_msg)

    def agents_no_print(self):
        for agent in self.agents:
            agent.print_on = False

    def run_director(
        self,
        task: str,
        img: str = None,
    ) -> SwarmSpec:
        """
        Execute the director agent with the given task and conversation context.

        This method runs the director agent to create a plan and distribute orders
        based on the current task and conversation history. If a planning director
        agent is configured, it will first create a detailed plan before the main
        director processes the task.

        Args:
            task (str): The task to be executed by the director.
            img (str, optional): Optional image input for the task.

        Returns:
            SwarmSpec: The director's output containing the plan and orders.

        Raises:
            Exception: If director execution fails.
        """
        try:
            if self.verbose:
                logger.info(
                    f"[RUN] Running director with task: {task}"
                )

            if self.planning_director_agent is not None:
                plan = self.planning_director_agent.run(
                    task=f"History: {self.conversation.get_str()} \n\n Create a detailed step by step comprehensive plan for the director to execute the task: {task}",
                    img=img,
                )

                task += plan

            if self.director_reasoning_enabled:
                reasoning_output = self.reasoning_agent_run(
                    task=task, img=img
                )
                task += f"\n\n Reasoning: {reasoning_output}"

            # Run the director with the context
            function_call = self.director.run(
                task=f"History: {self.conversation.get_str()} \n\n Task: {task}",
                img=img,
            )

            self.conversation.add(
                role="Director", content=function_call
            )

            if self.verbose:
                logger.success(
                    "[SUCCESS] Director execution completed"
                )
                logger.debug(
                    f"[OUTPUT] Director output type: {type(function_call)}"
                )

            return function_call

        except Exception as e:
            error_msg = f"[ERROR] Failed to setup director: {str(e)}\n[TRACE] Traceback: {traceback.format_exc()}\n[BUG] If this issue persists, please report it at: https://github.com/kyegomez/swarms/issues"
            logger.error(error_msg)
            raise e

    def step(
        self,
        task: str,
        img: str = None,
        streaming_callback: Optional[
            Callable[[str, str, bool], None]
        ] = None,
        *args,
        **kwargs,
    ):
        """
        Execute a single step of the hierarchical swarm workflow.

        This method performs one complete iteration of the swarm's workflow:
        1. Run the director to create a plan and orders
        2. Parse the director's output to extract plan and orders
        3. Execute all orders by calling the appropriate agents
        4. Optionally generate director feedback on the results

        Args:
            task (str): The task to be processed in this step.
            img (str, optional): Optional image input for the task.
            streaming_callback (Callable[[str, str, bool], None], optional):
                Callback function for streaming agent outputs. Parameters are
                (agent_name, chunk, is_final) where is_final indicates completion.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Any: The results from this step, either agent outputs or director feedback.

        Raises:
            Exception: If step execution fails.
        """
        try:
            if self.verbose:
                logger.info(
                    f"[STEP] Executing single step for task: {task}"
                )

            # Update dashboard for director execution
            if self.interactive and self.dashboard:
                self.dashboard.update_director_status("PLANNING")

            output = self.run_director(task=task, img=img)

            # Parse the orders
            plan, orders = self.parse_orders(output)

            if self.verbose:
                logger.info(
                    f"[PARSE] Parsed plan and {len(orders)} orders"
                )

            # Update dashboard with plan and orders information
            if self.interactive and self.dashboard:
                self.dashboard.update_director_plan(plan)
                # Convert orders to list of dicts for dashboard
                orders_list = [
                    {
                        "agent_name": order.agent_name,
                        "task": order.task,
                    }
                    for order in orders
                ]
                self.dashboard.update_director_orders(orders_list)
                self.dashboard.update_director_status("EXECUTING")

            # Execute the orders
            outputs = self.execute_orders(
                orders, streaming_callback=streaming_callback
            )

            if self.verbose:
                logger.info(f"[EXEC] Executed {len(outputs)} orders")

            if self.director_feedback_on is True:
                feedback = self.feedback_director(outputs)
            else:
                feedback = outputs

            if self.verbose:
                logger.success(
                    "[SUCCESS] Step completed successfully"
                )

            return feedback

        except Exception as e:
            error_msg = f"[ERROR] Failed to setup director: {str(e)}\n[TRACE] Traceback: {traceback.format_exc()}\n[BUG] If this issue persists, please report it at: https://github.com/kyegomez/swarms/issues"
            logger.error(error_msg)

    def run(
        self,
        task: Optional[str] = None,
        img: Optional[str] = None,
        streaming_callback: Optional[
            Callable[[str, str, bool], None]
        ] = None,
        *args,
        **kwargs,
    ):
        """
        Execute the hierarchical swarm for the specified number of feedback loops.

        This method orchestrates the complete swarm execution, performing multiple
        iterations based on the max_loops configuration. Each iteration builds upon
        the previous results, allowing for iterative refinement and improvement.

        The method maintains conversation history throughout all loops and provides
        context from previous iterations to subsequent ones.

        Args:
            task (str, optional): The initial task to be processed by the swarm.
                                 If None and interactive mode is enabled, will prompt for input.
            img (str, optional): Optional image input for the agents.
            streaming_callback (Callable[[str, str, bool], None], optional):
                Callback function for streaming agent outputs. Parameters are
                (agent_name, chunk, is_final) where is_final indicates completion.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Any: The formatted conversation history as output, formatted according
                 to the output_type configuration.

        Raises:
            Exception: If swarm execution fails.
        """
        try:
            # Handle interactive mode task input
            if task is None and self.interactive:
                task = self._get_interactive_task()

            current_loop = 0
            last_output = None

            # Start dashboard if in interactive mode
            if self.interactive and self.dashboard:
                self.dashboard.start(self.max_loops)
                self.dashboard.update_director_status("ACTIVE")

            if self.verbose:
                logger.info(
                    f"[START] Starting hierarchical swarm run: {self.name}"
                )
                logger.info(
                    f"[CONFIG] Configuration - Max loops: {self.max_loops}"
                )

            while current_loop < self.max_loops:
                if self.verbose:
                    logger.info(
                        f"[LOOP] Loop {current_loop + 1}/{self.max_loops} - Processing task"
                    )

                # Update dashboard loop counter
                if self.interactive and self.dashboard:
                    self.dashboard.update_loop(current_loop + 1)
                    self.dashboard.update_director_status(
                        "PROCESSING"
                    )

                # For the first loop, use the original task.
                # For subsequent loops, use the feedback from the previous loop as context.
                if current_loop == 0:
                    loop_task = task
                else:
                    loop_task = (
                        f"Previous loop results: {last_output}\n\n"
                        f"Original task: {task}\n\n"
                        "Based on the previous results and any feedback, continue with the next iteration of the task. "
                        "Refine, improve, or complete any remaining aspects of the analysis."
                    )

                # Execute one step of the swarm
                try:
                    last_output = self.step(
                        task=loop_task,
                        img=img,
                        streaming_callback=streaming_callback,
                        *args,
                        **kwargs,
                    )

                    if self.verbose:
                        logger.success(
                            f"[SUCCESS] Loop {current_loop + 1} completed successfully"
                        )

                except Exception as e:
                    error_msg = f"[ERROR] Failed to setup director: {str(e)}\n[TRACE] Traceback: {traceback.format_exc()}\n[BUG] If this issue persists, please report it at: https://github.com/kyegomez/swarms/issues"
                    logger.error(error_msg)

                current_loop += 1

                # Add loop completion marker to conversation
                self.conversation.add(
                    role="System",
                    content=f"--- Loop {current_loop}/{self.max_loops} completed ---",
                )

            # Stop dashboard if in interactive mode
            if self.interactive and self.dashboard:
                self.dashboard.update_director_status("COMPLETED")
                self.dashboard.stop()

            if self.verbose:
                logger.success(
                    f"[COMPLETE] Hierarchical swarm run completed: {self.name}"
                )
                logger.info(
                    f"[STATS] Total loops executed: {current_loop}"
                )

            return history_output_formatter(
                conversation=self.conversation, type=self.output_type
            )

        except Exception as e:
            # Stop dashboard on error
            if self.interactive and self.dashboard:
                self.dashboard.update_director_status("ERROR")
                self.dashboard.stop()

            error_msg = f"[ERROR] Failed to setup director: {str(e)}\n[TRACE] Traceback: {traceback.format_exc()}\n[BUG] If this issue persists, please report it at: https://github.com/kyegomez/swarms/issues"
            logger.error(error_msg)

    def _get_interactive_task(self) -> str:
        """
        Get task input from user in interactive mode.

        Returns:
            str: The task input from the user
        """
        if self.dashboard:
            self.dashboard.console.print(
                "\n[bold red]SWARMS CORPORATION[/bold red] - [bold white]TASK INPUT REQUIRED[/bold white]"
            )
            self.dashboard.console.print(
                "[bold cyan]Enter your task for the hierarchical swarm:[/bold cyan]"
            )

        task = input("> ")
        return task.strip()

    def feedback_director(self, outputs: list):
        """
        Generate feedback from the director based on agent outputs.

        This method creates a feedback director agent that analyzes the results
        from worker agents and provides specific, actionable feedback for improvement.
        The feedback is added to the conversation history and can be used in
        subsequent iterations.

        Args:
            outputs (list): List of outputs from worker agents that need feedback.

        Returns:
            str: The director's feedback on the agent outputs.

        Raises:
            Exception: If feedback generation fails.
        """
        try:
            if self.verbose:
                logger.info("[FEEDBACK] Generating director feedback")

            task = f"History: {self.conversation.get_str()} \n\n"

            feedback_director = Agent(
                agent_name="Director",
                agent_description="Director module that provides feedback to the worker agents",
                model_name=self.director_model_name,
                max_loops=1,
                system_prompt=HIEARCHICAL_SWARM_SYSTEM_PROMPT,
            )

            output = feedback_director.run(
                task=(
                    "You are the Director. Carefully review the outputs generated by all the worker agents in the previous step. "
                    "Provide specific, actionable feedback for each agent, highlighting strengths, weaknesses, and concrete suggestions for improvement. "
                    "If any outputs are unclear, incomplete, or could be enhanced, explain exactly how. "
                    f"Your feedback should help the agents refine their work in the next iteration. "
                    f"Worker Agent Responses: {task}"
                )
            )
            self.conversation.add(
                role=self.director.agent_name, content=output
            )

            if self.verbose:
                logger.success(
                    "[SUCCESS] Director feedback generated successfully"
                )

            return output

        except Exception as e:
            error_msg = f"[ERROR] Failed to setup director: {str(e)}\n[TRACE] Traceback: {traceback.format_exc()}\n[BUG] If this issue persists, please report it at: https://github.com/kyegomez/swarms/issues"
            logger.error(error_msg)

    def call_single_agent(
        self,
        agent_name: str,
        task: str,
        streaming_callback: Optional[
            Callable[[str, str, bool], None]
        ] = None,
        *args,
        **kwargs,
    ):
        """
        Call a single agent by name to execute a specific task.

        This method locates an agent by name and executes the given task with
        the current conversation context. The agent's output is added to the
        conversation history for future reference.

        Args:
            agent_name (str): The name of the agent to call.
            task (str): The task to be executed by the agent.
            streaming_callback (Callable[[str, str, bool], None], optional):
                Callback function for streaming agent outputs. Parameters are
                (agent_name, chunk, is_final) where is_final indicates completion.
            *args: Additional positional arguments for the agent.
            **kwargs: Additional keyword arguments for the agent.

        Returns:
            Any: The output from the agent's execution.

        Raises:
            ValueError: If the specified agent is not found in the swarm.
            Exception: If agent execution fails.
        """
        try:
            if self.verbose:
                logger.info(f"[CALL] Calling agent: {agent_name}")

            # Find agent by name
            agent = None
            for a in self.agents:
                if (
                    hasattr(a, "agent_name")
                    and a.agent_name == agent_name
                ):
                    agent = a
                    break

            if agent is None:
                available_agents = [
                    a.agent_name
                    for a in self.agents
                    if hasattr(a, "agent_name")
                ]
                raise ValueError(
                    f"Agent '{agent_name}' not found in swarm. Available agents: {available_agents}"
                )

            # Update dashboard for agent execution
            if self.interactive and self.dashboard:
                self.dashboard.update_agent_status(
                    agent_name, "RUNNING", task, "Executing task..."
                )

            # Handle streaming callback if provided
            if streaming_callback is not None:

                def agent_streaming_callback(chunk: str):
                    """Wrapper for agent streaming callback."""
                    try:
                        if chunk is not None and chunk.strip():
                            streaming_callback(
                                agent_name, chunk, False
                            )
                    except Exception as callback_error:
                        if self.verbose:
                            logger.warning(
                                f"[STREAMING] Callback failed for {agent_name}: {str(callback_error)}"
                            )

                output = agent.run(
                    task=f"History: {self.conversation.get_str()} \n\n Task: {task}",
                    streaming_callback=agent_streaming_callback,
                    *args,
                    **kwargs,
                )

                # Call completion callback
                try:
                    streaming_callback(agent_name, "", True)
                except Exception as callback_error:
                    if self.verbose:
                        logger.warning(
                            f"[STREAMING] Completion callback failed for {agent_name}: {str(callback_error)}"
                        )
            else:
                output = agent.run(
                    task=f"History: {self.conversation.get_str()} \n\n Task: {task}",
                    *args,
                    **kwargs,
                )
            self.conversation.add(role=agent_name, content=output)

            if self.verbose:
                logger.success(
                    f"[SUCCESS] Agent {agent_name} completed task successfully"
                )

            return output

        except Exception as e:
            # Update dashboard with error status
            if self.interactive and self.dashboard:
                self.dashboard.update_agent_status(
                    agent_name, "ERROR", task, f"Error: {str(e)}"
                )

            error_msg = f"[ERROR] Failed to setup director: {str(e)}\n[TRACE] Traceback: {traceback.format_exc()}\n[BUG] If this issue persists, please report it at: https://github.com/kyegomez/swarms/issues"
            logger.error(error_msg)

    def parse_orders(self, output):
        """
        Parse the director's output to extract plan and orders.

        This method handles various output formats from the director agent and
        extracts the plan and hierarchical orders. It supports both direct
        dictionary formats and function call formats with JSON arguments.

        Args:
            output: The raw output from the director agent.

        Returns:
            tuple: A tuple containing (plan, orders) where plan is a string
                   and orders is a list of HierarchicalOrder objects.

        Raises:
            ValueError: If the output format is unexpected or cannot be parsed.
            Exception: If parsing fails due to other errors.
        """
        try:
            if self.verbose:
                logger.info("[PARSE] Parsing director orders")
                logger.debug(f"[TYPE] Output type: {type(output)}")

            import json

            # Handle different output formats from the director
            if isinstance(output, list):
                # If output is a list, look for function call data
                for item in output:
                    if isinstance(item, dict):
                        # Check if it's a conversation format with role/content
                        if "content" in item and isinstance(
                            item["content"], list
                        ):
                            for content_item in item["content"]:
                                if (
                                    isinstance(content_item, dict)
                                    and "function" in content_item
                                ):
                                    function_data = content_item[
                                        "function"
                                    ]
                                    if "arguments" in function_data:
                                        try:
                                            args = json.loads(
                                                function_data[
                                                    "arguments"
                                                ]
                                            )
                                            if (
                                                "plan" in args
                                                and "orders" in args
                                            ):
                                                plan = args["plan"]
                                                orders = [
                                                    HierarchicalOrder(
                                                        **order
                                                    )
                                                    for order in args[
                                                        "orders"
                                                    ]
                                                ]

                                                if self.verbose:
                                                    logger.success(
                                                        f"[SUCCESS] Successfully parsed plan and {len(orders)} orders"
                                                    )

                                                return plan, orders
                                        except (
                                            json.JSONDecodeError
                                        ) as json_err:
                                            if self.verbose:
                                                logger.warning(
                                                    f"[WARN] JSON decode error: {json_err}"
                                                )
                                            pass
                        # Check if it's a direct function call format
                        elif "function" in item:
                            function_data = item["function"]
                            if "arguments" in function_data:
                                try:
                                    args = json.loads(
                                        function_data["arguments"]
                                    )
                                    if (
                                        "plan" in args
                                        and "orders" in args
                                    ):
                                        plan = args["plan"]
                                        orders = [
                                            HierarchicalOrder(**order)
                                            for order in args[
                                                "orders"
                                            ]
                                        ]

                                        if self.verbose:
                                            logger.success(
                                                f"[SUCCESS] Successfully parsed plan and {len(orders)} orders"
                                            )

                                        return plan, orders
                                except (
                                    json.JSONDecodeError
                                ) as json_err:
                                    if self.verbose:
                                        logger.warning(
                                            f"[WARN] JSON decode error: {json_err}"
                                        )
                                    pass
                # If no function call found, raise error
                raise ValueError(
                    f"Unable to parse orders from director output: {output}"
                )
            elif isinstance(output, dict):
                # Handle direct dictionary format
                if "plan" in output and "orders" in output:
                    plan = output["plan"]
                    orders = [
                        HierarchicalOrder(**order)
                        for order in output["orders"]
                    ]

                    if self.verbose:
                        logger.success(
                            f"[SUCCESS] Successfully parsed plan and {len(orders)} orders"
                        )

                    return plan, orders
                else:
                    raise ValueError(
                        f"Missing 'plan' or 'orders' in director output: {output}"
                    )
            else:
                raise ValueError(
                    f"Unexpected output format from director: {type(output)}"
                )

        except Exception as e:
            error_msg = f"[ERROR] Failed to parse orders: {str(e)}\n[TRACE] Traceback: {traceback.format_exc()}\n[BUG] If this issue persists, please report it at: https://github.com/kyegomez/swarms/issues"
            logger.error(error_msg)
            raise e

    def execute_orders(
        self,
        orders: list,
        streaming_callback: Optional[
            Callable[[str, str, bool], None]
        ] = None,
    ):
        """
        Execute all orders from the director's output.

        This method iterates through all hierarchical orders and calls the
        appropriate agents to execute their assigned tasks. Each agent's
        output is collected and returned as a list.

        Args:
            orders (list): List of HierarchicalOrder objects to execute.
            streaming_callback (Callable[[str, str, bool], None], optional):
                Callback function for streaming agent outputs. Parameters are
                (agent_name, chunk, is_final) where is_final indicates completion.

        Returns:
            list: List of outputs from all executed orders.

        Raises:
            Exception: If order execution fails.
        """
        try:
            if self.verbose:
                logger.info(f"[EXEC] Executing {len(orders)} orders")

            outputs = []
            for i, order in enumerate(orders):
                if self.verbose:
                    logger.info(
                        f"[ORDER] Executing order {i+1}/{len(orders)}: {order.agent_name}"
                    )

                # Update dashboard for agent execution
                if self.interactive and self.dashboard:
                    self.dashboard.update_agent_status(
                        order.agent_name,
                        "RUNNING",
                        order.task,
                        "Processing...",
                    )

                output = self.call_single_agent(
                    order.agent_name,
                    order.task,
                    streaming_callback=streaming_callback,
                )

                # Update dashboard with completed status
                if self.interactive and self.dashboard:
                    # Always show full output without truncation
                    output_display = str(output)

                    self.dashboard.update_agent_status(
                        order.agent_name,
                        "COMPLETED",
                        order.task,
                        output_display,
                    )

                outputs.append(output)

            if self.verbose:
                logger.success(
                    f"[SUCCESS] All {len(orders)} orders executed successfully"
                )

            return outputs

        except Exception as e:
            error_msg = f"[ERROR] Failed to setup director: {str(e)}\n[TRACE] Traceback: {traceback.format_exc()}\n[BUG] If this issue persists, please report it at: https://github.com/kyegomez/swarms/issues"
            logger.error(error_msg)

    def batched_run(
        self,
        tasks: List[str],
        img: str = None,
        streaming_callback: Optional[
            Callable[[str, str, bool], None]
        ] = None,
        *args,
        **kwargs,
    ):
        """
        Execute the hierarchical swarm for multiple tasks in sequence.

        This method processes a list of tasks sequentially, running the complete
        swarm workflow for each task. Each task is processed independently with
        its own conversation context and results.

        Args:
            tasks (List[str]): List of tasks to be processed by the swarm.
            img (str, optional): Optional image input for the tasks.
            streaming_callback (Callable[[str, str, bool], None], optional):
                Callback function for streaming agent outputs. Parameters are
                (agent_name, chunk, is_final) where is_final indicates completion.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            list: List of results for each processed task.

        Raises:
            Exception: If batched execution fails.
        """
        try:
            if self.verbose:
                logger.info(
                    f"[START] Starting batched hierarchical swarm run: {self.name}"
                )
                logger.info(
                    f"[CONFIG] Configuration - Max loops: {self.max_loops}"
                )

            # Initialize a list to store the results
            results = []

            # Process each task in parallel
            for task in tasks:
                result = self.run(
                    task,
                    img,
                    streaming_callback=streaming_callback,
                    *args,
                    **kwargs,
                )
                results.append(result)

            if self.verbose:
                logger.success(
                    f"[COMPLETE] Batched hierarchical swarm run completed: {self.name}"
                )
                logger.info(
                    f"[STATS] Total tasks processed: {len(tasks)}"
                )

            return results

        except Exception as e:
            error_msg = f"[ERROR] Batched hierarchical swarm run failed: {str(e)}"
            if self.verbose:
                logger.error(error_msg)
                logger.error(
                    f"[TRACE] Traceback: {traceback.format_exc()}"
                )
