#!/usr/bin/env python3
"""
Comprehensive Hybrid RAG Agent CLI Client

Interactive command-line interface for the hybrid agentic RAG system.
Connects to the FastAPI backend and provides real-time streaming responses
with detailed tool usage and system status visibility.

Features:
- 🔄 Real-time streaming responses from agent
- 🔍 Detailed tool usage logging
- 📊 System status monitoring
- 💬 Session management for conversation continuity
- 🎨 Rich terminal UI with colors and formatting
- ⚡ Fast WebSocket-style streaming
- 🛠️ Development-friendly debugging output

Usage:
    # Start the API server first:
    python comprehensive_agent_api.py

    # Then run this CLI:
    python comprehensive_agent_cli.py

    # Interactive commands:
    /help     - Show all available commands
    /health   - Check system health status
    /status   - Show current session and systems
    /clear    - Clear conversation history
    /quit     - Exit the CLI
"""

import sys
import json
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, Any
import os

# Rich terminal formatting
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.prompt import Prompt

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("⚠️ Rich not available. Install with: pip install rich")

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8058")
STREAMING_ENABLED = True
DEFAULT_SESSION_ID = f"cli_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


class ComprehensiveAgentCLI:
    """Interactive CLI for the Comprehensive Hybrid RAG Agent."""

    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        self.session_id = DEFAULT_SESSION_ID
        self.user_id = "cli_user"
        self.conversation_history = []
        self.system_status = {}
        self.api_session = None

        # CLI state
        self.running = True
        self.debug_mode = os.getenv("CLI_DEBUG", "false").lower() == "true"

        # Statistics
        self.stats = {
            "queries_sent": 0,
            "total_response_time": 0.0,
            "systems_used": set(),
            "tools_called": set(),
        }

    async def initialize(self):
        """Initialize the CLI client."""
        self.api_session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(
                total=300
            )  # 5 minute timeout for long responses
        )

        # Check API connection
        await self._check_api_health()

        # Display welcome message
        self._show_welcome()

    async def cleanup(self):
        """Clean up resources."""
        if self.api_session:
            await self.api_session.close()

    def _show_welcome(self):
        """Display welcome message and system status."""
        if RICH_AVAILABLE:
            welcome_panel = Panel(
                f"""[bold cyan]🤖 Comprehensive Hybrid RAG Agent CLI[/bold cyan]

[yellow]Session ID:[/yellow] {self.session_id}
[yellow]User ID:[/yellow] {self.user_id}
[yellow]API Endpoint:[/yellow] {API_BASE_URL}

[green]Available Commands:[/green]
• [cyan]/help[/cyan]     - Show all commands
• [cyan]/health[/cyan]   - Check system health  
• [cyan]/status[/cyan]   - Show session status
• [cyan]/clear[/cyan]    - Clear conversation
• [cyan]/debug[/cyan]    - Toggle debug mode
• [cyan]/stats[/cyan]    - Show usage statistics
• [cyan]/quit[/cyan]     - Exit CLI

[dim]Type your question or use commands starting with /[/dim]""",
                title="🚀 Welcome to Hybrid RAG Agent",
                border_style="cyan",
            )
            self.console.print(welcome_panel)
        else:
            print("🤖 Comprehensive Hybrid RAG Agent CLI")
            print(f"Session: {self.session_id} | User: {self.user_id}")
            print(f"API: {API_BASE_URL}")
            print("Type /help for commands or ask a question!")

    async def _check_api_health(self):
        """Check if the API server is healthy."""
        try:
            async with self.api_session.get(f"{API_BASE_URL}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    self.system_status = health_data

                    if RICH_AVAILABLE:
                        self._display_health_status(health_data)
                    else:
                        print(f"✅ API Health: {health_data.get('status', 'unknown')}")
                else:
                    raise aiohttp.ClientError(f"API returned status {response.status}")

        except Exception as e:
            error_msg = f"❌ Cannot connect to API server at {API_BASE_URL}"
            if RICH_AVAILABLE:
                self.console.print(f"[red]{error_msg}[/red]")
                self.console.print(f"[red]Error: {e}[/red]")
            else:
                print(error_msg)
                print(f"Error: {e}")

            print("\n🔧 To start the API server:")
            print("   python comprehensive_agent_api.py")
            sys.exit(1)

    def _display_health_status(self, health_data: Dict[str, Any]):
        """Display system health status using Rich formatting."""
        if not RICH_AVAILABLE:
            return

        status = health_data.get("status", "unknown")
        systems = health_data.get("systems", {})

        # Create health table
        health_table = Table(title="🏥 System Health Status")
        health_table.add_column("System", style="cyan")
        health_table.add_column("Status", style="bold")
        health_table.add_column("Details", style="dim")

        # Overall status
        status_color = (
            "green"
            if status == "healthy"
            else "red"
            if status == "unhealthy"
            else "yellow"
        )
        health_table.add_row(
            "Overall", f"[{status_color}]{status.upper()}[/{status_color}]", ""
        )

        # Individual systems
        for system_name, system_info in systems.items():
            sys_status = system_info.get("status", "unknown")
            sys_color = (
                "green"
                if sys_status == "healthy"
                else "red"
                if sys_status == "error"
                else "yellow"
            )
            details = system_info.get("details", "")
            health_table.add_row(
                system_name,
                f"[{sys_color}]{sys_status}[/{sys_color}]",
                str(details)[:50] + "..." if len(str(details)) > 50 else str(details),
            )

        self.console.print(health_table)

    async def run(self):
        """Main CLI loop."""
        try:
            while self.running:
                try:
                    # Get user input
                    if RICH_AVAILABLE:
                        prompt_text = f"[bold cyan]({self.session_id[-8:]})[/bold cyan] [yellow]❯[/yellow] "
                        user_input = Prompt.ask(prompt_text).strip()
                    else:
                        user_input = input(f"({self.session_id[-8:]}) ❯ ").strip()

                    if not user_input:
                        continue

                    # Handle commands
                    if user_input.startswith("/"):
                        await self._handle_command(user_input)
                    else:
                        # Send query to agent
                        await self._send_query(user_input)

                except KeyboardInterrupt:
                    if RICH_AVAILABLE:
                        self.console.print("\\n[yellow]Use /quit to exit[/yellow]")
                    else:
                        print("\\nUse /quit to exit")
                except EOFError:
                    break

        except Exception as e:
            if RICH_AVAILABLE:
                self.console.print(f"[red]CLI Error: {e}[/red]")
            else:
                print(f"CLI Error: {e}")
        finally:
            await self.cleanup()

    async def _handle_command(self, command: str):
        """Handle CLI commands."""
        cmd = command.lower().strip()

        if cmd == "/help":
            self._show_help()
        elif cmd == "/health":
            await self._check_api_health()
        elif cmd == "/status":
            self._show_status()
        elif cmd == "/clear":
            self._clear_conversation()
        elif cmd == "/debug":
            self._toggle_debug()
        elif cmd == "/stats":
            self._show_stats()
        elif cmd in ["/quit", "/exit", "/q"]:
            self.running = False
            if RICH_AVAILABLE:
                self.console.print("[yellow]👋 Goodbye![/yellow]")
            else:
                print("👋 Goodbye!")
        else:
            if RICH_AVAILABLE:
                self.console.print(f"[red]Unknown command: {command}[/red]")
                self.console.print("[dim]Type /help for available commands[/dim]")
            else:
                print(f"Unknown command: {command}")
                print("Type /help for available commands")

    def _show_help(self):
        """Show help information."""
        if RICH_AVAILABLE:
            help_table = Table(title="📚 Available Commands")
            help_table.add_column("Command", style="cyan")
            help_table.add_column("Description", style="white")

            commands = [
                ("/help", "Show this help message"),
                ("/health", "Check API server and system health"),
                ("/status", "Show current session and system status"),
                ("/clear", "Clear conversation history"),
                ("/debug", "Toggle debug mode for detailed logging"),
                ("/stats", "Show usage statistics"),
                ("/quit", "Exit the CLI client"),
            ]

            for cmd, desc in commands:
                help_table.add_row(cmd, desc)

            self.console.print(help_table)

            # Example queries
            examples_panel = Panel(
                """[bold cyan]Example Queries:[/bold cyan]

• "What is the architecture of our system?"
• "Search for information about user authentication"
• "Find relationships between microservices"
• "Tell me about the latest project updates"
• "How does the API documentation describe error handling?"

[dim]The agent will intelligently choose between Onyx Cloud, vector search, 
and knowledge graph based on your query complexity.[/dim]""",
                title="💡 Usage Examples",
                border_style="green",
            )
            self.console.print(examples_panel)
        else:
            print("📚 Available Commands:")
            print("  /help    - Show this help")
            print("  /health  - Check system health")
            print("  /status  - Show session status")
            print("  /clear   - Clear conversation")
            print("  /debug   - Toggle debug mode")
            print("  /stats   - Show statistics")
            print("  /quit    - Exit CLI")

    def _show_status(self):
        """Show current session status."""
        if RICH_AVAILABLE:
            status_info = f"""[yellow]Session ID:[/yellow] {self.session_id}
[yellow]User ID:[/yellow] {self.user_id}
[yellow]Debug Mode:[/yellow] {"Enabled" if self.debug_mode else "Disabled"}
[yellow]Queries Sent:[/yellow] {self.stats["queries_sent"]}
[yellow]Conversation Length:[/yellow] {len(self.conversation_history)} messages"""

            if self.stats["systems_used"]:
                status_info += f"\\n[yellow]Systems Used:[/yellow] {', '.join(self.stats['systems_used'])}"
            if self.stats["tools_called"]:
                status_info += f"\\n[yellow]Tools Called:[/yellow] {', '.join(self.stats['tools_called'])}"

            status_panel = Panel(
                status_info, title="📊 Session Status", border_style="blue"
            )
            self.console.print(status_panel)
        else:
            print("📊 Session Status:")
            print(f"  Session ID: {self.session_id}")
            print(f"  User ID: {self.user_id}")
            print(f"  Debug Mode: {'Enabled' if self.debug_mode else 'Disabled'}")
            print(f"  Queries: {self.stats['queries_sent']}")
            print(f"  Conversation: {len(self.conversation_history)} messages")

    def _clear_conversation(self):
        """Clear conversation history."""
        self.conversation_history.clear()
        if RICH_AVAILABLE:
            self.console.print("[green]✅ Conversation history cleared[/green]")
        else:
            print("✅ Conversation history cleared")

    def _toggle_debug(self):
        """Toggle debug mode."""
        self.debug_mode = not self.debug_mode
        status = "enabled" if self.debug_mode else "disabled"
        if RICH_AVAILABLE:
            self.console.print(f"[yellow]🔧 Debug mode {status}[/yellow]")
        else:
            print(f"🔧 Debug mode {status}")

    def _show_stats(self):
        """Show usage statistics."""
        avg_response_time = (
            self.stats["total_response_time"] / self.stats["queries_sent"]
            if self.stats["queries_sent"] > 0
            else 0
        )

        if RICH_AVAILABLE:
            stats_table = Table(title="📈 Usage Statistics")
            stats_table.add_column("Metric", style="cyan")
            stats_table.add_column("Value", style="white")

            stats_table.add_row("Queries Sent", str(self.stats["queries_sent"]))
            stats_table.add_row("Average Response Time", f"{avg_response_time:.2f}s")
            stats_table.add_row(
                "Systems Used", ", ".join(self.stats["systems_used"]) or "None"
            )
            stats_table.add_row(
                "Tools Called", ", ".join(self.stats["tools_called"]) or "None"
            )
            stats_table.add_row(
                "Conversation Length", str(len(self.conversation_history))
            )

            self.console.print(stats_table)
        else:
            print("📈 Usage Statistics:")
            print(f"  Queries: {self.stats['queries_sent']}")
            print(f"  Avg Response Time: {avg_response_time:.2f}s")
            print(f"  Systems Used: {', '.join(self.stats['systems_used']) or 'None'}")
            print(f"  Tools Called: {', '.join(self.stats['tools_called']) or 'None'}")

    async def _send_query(self, message: str):
        """Send query to the agent API."""
        start_time = datetime.now()

        # Prepare request
        request_data = {
            "message": message,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "search_type": "hybrid",
            "metadata": {"cli_version": "1.0.0", "debug_mode": self.debug_mode},
        }

        try:
            if STREAMING_ENABLED:
                await self._send_streaming_query(request_data, start_time)
            else:
                await self._send_regular_query(request_data, start_time)

        except Exception as e:
            if RICH_AVAILABLE:
                self.console.print(f"[red]❌ Query failed: {e}[/red]")
            else:
                print(f"❌ Query failed: {e}")

    async def _send_streaming_query(
        self, request_data: Dict[str, Any], start_time: datetime
    ):
        """Send streaming query to the agent."""
        if RICH_AVAILABLE:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                task = progress.add_task("🤖 Agent is thinking...", total=None)

                try:
                    async with self.api_session.post(
                        f"{API_BASE_URL}/chat/stream",
                        json=request_data,
                        headers={"Content-Type": "application/json"},
                    ) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            raise aiohttp.ClientError(
                                f"API returned {response.status}: {error_text}"
                            )

                        progress.remove_task(task)

                        # Stream response
                        self.console.print(
                            "\\n[bold green]🤖 Agent Response:[/bold green]"
                        )
                        response_text = ""

                        async for line in response.content:
                            if line:
                                line_text = line.decode("utf-8").strip()
                                if line_text.startswith("data: "):
                                    data_json = line_text[6:]  # Remove 'data: ' prefix
                                    if data_json == "[DONE]":
                                        break
                                    try:
                                        delta = json.loads(data_json)
                                        if delta.get("type") == "text":
                                            content = delta.get("content", "")
                                            response_text += content
                                            print(content, end="", flush=True)
                                        elif (
                                            delta.get("type") == "tool_call"
                                            and self.debug_mode
                                        ):
                                            tool_info = delta.get("metadata", {})
                                            self.console.print(
                                                f"\\n[dim]🔧 Tool: {tool_info.get('tool_name', 'unknown')}[/dim]"
                                            )
                                    except json.JSONDecodeError:
                                        continue

                        print("\\n")  # New line after response

                except Exception as e:
                    progress.remove_task(task)
                    raise e
        else:
            # Fallback without Rich
            print("🤖 Agent is thinking...")
            async with self.api_session.post(
                f"{API_BASE_URL}/chat/stream", json=request_data
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise aiohttp.ClientError(
                        f"API returned {response.status}: {error_text}"
                    )

                print("\\n🤖 Agent Response:")
                async for line in response.content:
                    if line:
                        line_text = line.decode("utf-8").strip()
                        if line_text.startswith("data: "):
                            data_json = line_text[6:]
                            if data_json == "[DONE]":
                                break
                            try:
                                delta = json.loads(data_json)
                                if delta.get("type") == "text":
                                    print(delta.get("content", ""), end="", flush=True)
                            except json.JSONDecodeError:
                                continue
                print("\\n")

        # Update statistics
        response_time = (datetime.now() - start_time).total_seconds()
        self.stats["queries_sent"] += 1
        self.stats["total_response_time"] += response_time

        # Add to conversation history
        self.conversation_history.append(
            {
                "timestamp": start_time.isoformat(),
                "message": request_data["message"],
                "response_time": response_time,
            }
        )

    async def _send_regular_query(
        self, request_data: Dict[str, Any], start_time: datetime
    ):
        """Send regular (non-streaming) query to the agent."""
        async with self.api_session.post(
            f"{API_BASE_URL}/chat", json=request_data
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise aiohttp.ClientError(
                    f"API returned {response.status}: {error_text}"
                )

            result = await response.json()

            # Display response
            if RICH_AVAILABLE:
                self._display_agent_response(result)
            else:
                print("\\n🤖 Agent Response:")
                print(result.get("response", "No response"))

            # Update statistics
            response_time = (datetime.now() - start_time).total_seconds()
            self.stats["queries_sent"] += 1
            self.stats["total_response_time"] += response_time

            # Track systems and tools used
            if result.get("systems_used"):
                self.stats["systems_used"].update(result["systems_used"])
            if result.get("tools_used"):
                for tool in result["tools_used"]:
                    self.stats["tools_called"].add(tool.get("name", "unknown"))

            # Add to conversation history
            self.conversation_history.append(
                {
                    "timestamp": start_time.isoformat(),
                    "message": request_data["message"],
                    "response": result.get("response", ""),
                    "response_time": response_time,
                    "tools_used": result.get("tools_used", []),
                    "systems_used": result.get("systems_used", []),
                }
            )

    def _display_agent_response(self, result: Dict[str, Any]):
        """Display agent response with Rich formatting."""
        if not RICH_AVAILABLE:
            return

        # Main response
        response_panel = Panel(
            result.get("response", "No response"),
            title="🤖 Agent Response",
            border_style="green",
        )
        self.console.print(response_panel)

        # Metadata table
        if self.debug_mode or result.get("tools_used") or result.get("systems_used"):
            meta_table = Table(title="📊 Response Metadata")
            meta_table.add_column("Property", style="cyan")
            meta_table.add_column("Value", style="white")

            meta_table.add_row(
                "Response Time", f"{result.get('response_time', 0):.2f}s"
            )
            meta_table.add_row("Confidence", result.get("confidence", "unknown"))
            meta_table.add_row("Total Sources", str(result.get("total_sources", 0)))

            if result.get("systems_used"):
                meta_table.add_row("Systems Used", ", ".join(result["systems_used"]))

            if result.get("tools_used") and self.debug_mode:
                tools_str = ", ".join(
                    [tool.get("name", "unknown") for tool in result["tools_used"]]
                )
                meta_table.add_row("Tools Called", tools_str)

            self.console.print(meta_table)


async def main():
    """Main entry point for the CLI."""
    # Set up signal handling for graceful shutdown
    import signal

    cli = ComprehensiveAgentCLI()

    def signal_handler(signum, frame):
        cli.running = False
        print("\\n👋 Shutting down CLI...")

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        await cli.initialize()
        await cli.run()
    except KeyboardInterrupt:
        print("\\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ CLI Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        sys.exit(1)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
