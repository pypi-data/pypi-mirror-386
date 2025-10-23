"""
ClaudeCodeAgent Demo - Claude Code Autonomous Coding Pattern

Demonstrates Claude Code's proven autonomous architecture:
- 15-tool ecosystem (file, search, execution, web, workflow)
- Diff-first workflow for transparency
- System reminders to combat drift
- Context management with 92% compression trigger
- CLAUDE.md project memory

## Usage

```bash
python examples/autonomy/02_claude_code_agent_demo.py
```

## Based On

- Claude Code's production autonomous architecture
- Research: docs/research/CLAUDE_CODE_AUTONOMOUS_ARCHITECTURE.md
- Single-threaded master loop with tool-based convergence
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from kaizen.agents.autonomous import ClaudeCodeAgent, ClaudeCodeConfig
from kaizen.signatures import Signature, InputField, OutputField
from kaizen.tools import ToolRegistry
from kaizen.tools.builtin import register_builtin_tools


class CodingSignature(Signature):
    """Signature for autonomous coding tasks."""

    task: str = InputField(description="Coding task")
    context: str = InputField(description="Code context", default="")
    observation: str = InputField(description="Last observation", default="")

    code_changes: str = OutputField(description="Code modifications")
    next_action: str = OutputField(description="Next action")
    tool_calls: list = OutputField(description="Tool calls", default=[])


async def demo_claude_code_tools():
    """Demo 1: 15-tool ecosystem."""
    print("\n" + "=" * 80)
    print("DEMO 1: ClaudeCodeAgent - 15-Tool Ecosystem")
    print("=" * 80 + "\n")

    config = ClaudeCodeConfig(
        llm_provider="mock",
        model="mock-model",
        max_cycles=5,
        enable_diffs=True,
        enable_reminders=True,
    )

    registry = ToolRegistry()
    register_builtin_tools(registry)

    agent = ClaudeCodeAgent(
        config=config, signature=CodingSignature(), tool_registry=registry
    )

    print(f"✓ ClaudeCodeAgent created")
    print(f"  - Available tools: {len(list(registry.list_tools()))}")
    print(f"  - File operations: read_file, write_file, delete_file, etc.")
    print(f"  - Search: glob_search, grep_search")
    print(f"  - Execution: bash_command")
    print(f"  - Web: fetch_url, web_search")
    print(f"  - Workflow: todo_write")

    print(f"\n✅ Tool ecosystem ready for autonomous coding!")
    return agent


async def demo_diff_first_workflow():
    """Demo 2: Diff-first workflow."""
    print("\n" + "=" * 80)
    print("DEMO 2: Diff-First Workflow")
    print("=" * 80 + "\n")

    config = ClaudeCodeConfig(enable_diffs=True, max_cycles=3)

    agent = ClaudeCodeAgent(
        config=config,
        signature=CodingSignature(),
        tool_registry=ToolRegistry(),
    )

    print(f"✓ Diff-first workflow enabled")
    print(f"  - Shows minimal diffs before applying")
    print(f"  - Transparent change visibility")
    print(f"  - Easy review and revert")

    task = "Refactor authentication module"
    result = await agent.execute_autonomously(task)

    print(f"\n✅ Changes displayed as diffs!")
    print(f"  - Cycles: {result.get('cycles_used', 0)}")
    return result


async def demo_system_reminders():
    """Demo 3: System reminders for drift prevention."""
    print("\n" + "=" * 80)
    print("DEMO 3: System Reminders (Combat Drift)")
    print("=" * 80 + "\n")

    config = ClaudeCodeConfig(enable_reminders=True, max_cycles=15)

    agent = ClaudeCodeAgent(
        config=config,
        signature=CodingSignature(),
        tool_registry=ToolRegistry(),
    )

    print(f"✓ System reminders enabled")
    print(f"  - Inject every 10 cycles")
    print(f"  - Includes plan status")
    print(f"  - Includes context usage")
    print(f"  - Combat model drift")

    print(f"\n✅ Ready for long-running sessions!")
    return agent


async def demo_context_management():
    """Demo 4: Context management with 92% trigger."""
    print("\n" + "=" * 80)
    print("DEMO 4: Context Management (92% Trigger)")
    print("=" * 80 + "\n")

    config = ClaudeCodeConfig(
        context_threshold=0.92,  # 92% trigger
        max_cycles=100,  # Long sessions
    )

    agent = ClaudeCodeAgent(
        config=config,
        signature=CodingSignature(),
        tool_registry=ToolRegistry(),
    )

    print(f"✓ Context management configured")
    print(f"  - Compression trigger: {config.context_threshold * 100}%")
    print(f"  - Reduces to 50% after compression")
    print(f"  - Preserves important information")
    print(f"  - Max cycles: {config.max_cycles}")

    print(f"\n✅ Ready for 30+ hour sessions!")
    return agent


async def main():
    """Run all demonstrations."""
    print("\n" + "=" * 80)
    print("ClaudeCodeAgent Demonstrations")
    print("Claude Code Autonomous Architecture in Kaizen")
    print("=" * 80)

    try:
        await demo_claude_code_tools()
        await demo_diff_first_workflow()
        await demo_system_reminders()
        await demo_context_management()

        print("\n" + "=" * 80)
        print("✅ All Claude Code patterns demonstrated!")
        print("=" * 80 + "\n")

        print("📚 Learn More:")
        print("  - ClaudeCodeAgent: src/kaizen/agents/autonomous/claude_code.py")
        print("  - Research: docs/research/CLAUDE_CODE_AUTONOMOUS_ARCHITECTURE.md")
        print("  - Tests: tests/unit/agents/autonomous/test_claude_code.py")

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
