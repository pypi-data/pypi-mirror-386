# File: src/noveler/presentation/cli/commands/bus_commands.py
# Purpose: Message Bus management CLI commands for operational maintenance
# Context: Provides manual commands for outbox flush, list, replay and health monitoring

"""Message Bus management CLI commands for production operations."""

import click
from pathlib import Path
import asyncio
import json
from datetime import datetime
from typing import Any

from noveler.presentation.shared.shared_utilities import _get_console as get_console
from noveler.infrastructure.logging.unified_logger import get_logger


@click.group(name="bus")
def bus_command_group() -> None:
    """Message Bus management commands for operational maintenance.

    Provides commands to manually manage outbox, DLQ, and monitor bus health.
    Useful for production troubleshooting and maintenance tasks.
    """
    pass


@bus_command_group.command("flush")
@click.option("--limit", default=100, help="Maximum number of events to flush")
@click.option("--dry-run", is_flag=True, help="Show what would be flushed without actual execution")
def flush_outbox(limit: int, dry_run: bool) -> None:
    """Manually flush pending events from the outbox.

    Args:
        limit: Maximum number of events to process
        dry_run: Preview mode without actual execution
    """
    console = get_console()
    logger = get_logger(__name__)

    try:
        # Message Bus setup
        from noveler.application.simple_message_bus import MessageBus, BusConfig
        from noveler.infrastructure.adapters.file_outbox_repository import FileOutboxRepository
        from noveler.application.idempotency import InMemoryIdempotencyStore

        outbox_repo = FileOutboxRepository()
        bus = MessageBus(
            config=BusConfig(),
            outbox_repo=outbox_repo,
            idempotency_store=InMemoryIdempotencyStore(),
            dispatch_inline=False  # Manual flush mode
        )

        if dry_run:
            pending = outbox_repo.load_pending(limit)
            console.print(f"[yellow]DRY RUN: Would flush {len(pending)} pending events[/]")
            for i, entry in enumerate(pending[:10], 1):  # Show first 10
                console.print(f"  {i}. {entry.name} (id: {entry.id[:8]}..., attempts: {entry.attempts})")
            if len(pending) > 10:
                console.print(f"  ... and {len(pending) - 10} more events")
            return

        # Actual flush
        async def do_flush():
            count = await bus.flush_outbox(limit)
            return count

        count = asyncio.run(do_flush())
        console.print(f"[green]Successfully flushed {count} events from outbox[/]")
        logger.info(f"Manual outbox flush completed: {count} events")

    except Exception as exc:
        console.print(f"[red]Error flushing outbox: {exc}[/]")
        logger.error(f"Manual outbox flush failed: {exc}")


@bus_command_group.command("list")
@click.option("--type", "entry_type", type=click.Choice(["pending", "dlq", "all"]), default="pending",
              help="Type of entries to list")
@click.option("--limit", default=50, help="Maximum number of entries to show")
@click.option("--format", "output_format", type=click.Choice(["table", "json"]), default="table",
              help="Output format")
def list_entries(entry_type: str, limit: int, output_format: str) -> None:
    """List outbox entries by type.

    Args:
        entry_type: Type of entries to list (pending, dlq, all)
        limit: Maximum number of entries to show
        output_format: Output format (table or json)
    """
    console = get_console()

    try:
        from noveler.infrastructure.adapters.file_outbox_repository import FileOutboxRepository

        outbox_repo = FileOutboxRepository()

        if entry_type == "pending":
            entries = outbox_repo.load_pending(limit)
            title = "Pending Outbox Entries"
        elif entry_type == "dlq":
            entries = outbox_repo.load_dlq_entries(limit)
            title = "Dead Letter Queue Entries"
        else:  # all
            pending = outbox_repo.load_pending(limit // 2)
            dlq = outbox_repo.load_dlq_entries(limit // 2)
            entries = pending + dlq
            title = "All Outbox Entries"

        if output_format == "json":
            data = [
                {
                    "id": e.id,
                    "name": e.name,
                    "created_at": e.created_at.isoformat(),
                    "attempts": e.attempts,
                    "last_error": e.last_error,
                    "failed_at": e.failed_at.isoformat() if e.failed_at else None,
                    "payload_size": len(json.dumps(e.payload))
                }
                for e in entries
            ]
            console.print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            # Table format
            from rich.table import Table
            table = Table(title=title)
            table.add_column("ID", style="cyan", width=12)
            table.add_column("Name", style="green")
            table.add_column("Created", style="blue")
            table.add_column("Attempts", justify="right")
            table.add_column("Last Error", style="red", max_width=40)

            for entry in entries:
                error_preview = (entry.last_error[:37] + "..." if entry.last_error and len(entry.last_error) > 40
                               else entry.last_error or "")
                table.add_row(
                    entry.id[:8] + "...",
                    entry.name,
                    entry.created_at.strftime("%Y-%m-%d %H:%M"),
                    str(entry.attempts),
                    error_preview
                )

            console.print(table)
            console.print(f"\nTotal entries: {len(entries)}")

    except Exception as exc:
        console.print(f"[red]Error listing entries: {exc}[/]")


@bus_command_group.command("replay")
@click.argument("entry_id")
@click.option("--force", is_flag=True, help="Force replay even if entry is not in DLQ")
def replay_entry(entry_id: str, force: bool) -> None:
    """Replay a specific entry from DLQ back to pending.

    Args:
        entry_id: ID of the entry to replay
        force: Force replay even if not in DLQ
    """
    console = get_console()
    logger = get_logger(__name__)

    try:
        from noveler.infrastructure.adapters.file_outbox_repository import FileOutboxRepository

        outbox_repo = FileOutboxRepository()

        # Check if entry exists in DLQ
        dlq_entries = outbox_repo.load_dlq_entries(1000)
        target_entry = None
        for entry in dlq_entries:
            if entry.id.startswith(entry_id):
                target_entry = entry
                break

        if not target_entry and not force:
            console.print(f"[red]Entry {entry_id} not found in DLQ. Use --force to replay from any location.[/]")
            return

        if not target_entry:
            # Try to find in pending entries if force is used
            pending_entries = outbox_repo.load_pending(1000)
            for entry in pending_entries:
                if entry.id.startswith(entry_id):
                    target_entry = entry
                    break

        if not target_entry:
            console.print(f"[red]Entry {entry_id} not found anywhere.[/]")
            return

        # Manual replay implementation
        # Since FileOutboxRepository doesn't have a direct replay method,
        # we'll create a new entry with reset attempts
        from noveler.application.outbox import OutboxEntry

        replayed_entry = OutboxEntry(
            id=target_entry.id + "_replay_" + datetime.now().strftime("%Y%m%d_%H%M%S"),
            name=target_entry.name,
            payload=target_entry.payload,
            created_at=datetime.now(),
            attempts=0,  # Reset attempts
            dispatched_at=None,
            last_error=None,
            failed_at=None
        )

        outbox_repo.add(replayed_entry)

        console.print(f"[green]Entry {entry_id} replayed as {replayed_entry.id}[/]")
        logger.info(f"Manual entry replay: {entry_id} -> {replayed_entry.id}")

    except Exception as exc:
        console.print(f"[red]Error replaying entry: {exc}[/]")
        logger.error(f"Manual entry replay failed: {exc}")


@bus_command_group.command("health")
@click.option("--detailed", is_flag=True, help="Show detailed health information")
def show_health(detailed: bool) -> None:
    """Show Message Bus health status and metrics.

    Args:
        detailed: Show detailed health information including DLQ stats
    """
    console = get_console()

    try:
        from noveler.application.simple_message_bus import MessageBus, BusConfig
        from noveler.infrastructure.adapters.file_outbox_repository import FileOutboxRepository
        from noveler.application.idempotency import InMemoryIdempotencyStore

        outbox_repo = FileOutboxRepository()
        bus = MessageBus(
            config=BusConfig(),
            outbox_repo=outbox_repo,
            idempotency_store=InMemoryIdempotencyStore()
        )

        # Basic health info
        async def get_health():
            await bus.log_bus_health()
            if detailed:
                return await bus.get_dlq_stats()
            return {}

        dlq_stats = asyncio.run(get_health())

        # Metrics summary
        metrics = bus.get_metrics_summary()

        console.print("[bold green]Message Bus Health Status[/]")
        console.print(f"Processed Events: {metrics.get('processed_events_total', 0)}")

        cmd_stats = metrics.get('commands', {})
        console.print(f"Commands: {cmd_stats.get('count', 0)} total, " +
                     f"p95: {cmd_stats.get('p95_ms', 0):.1f}ms, " +
                     f"failure rate: {cmd_stats.get('failure_rate', 0):.2%}")

        event_stats = metrics.get('events', {})
        console.print(f"Events: {event_stats.get('count', 0)} total, " +
                     f"p95: {event_stats.get('p95_ms', 0):.1f}ms, " +
                     f"failure rate: {event_stats.get('failure_rate', 0):.2%}")

        if detailed and dlq_stats:
            console.print(f"\n[bold yellow]DLQ Status[/]")
            console.print(f"Failed Events: {dlq_stats.get('total_count', 0)}")
            console.print(f"Oldest Error: {dlq_stats.get('oldest_error', 'None')}")

            error_types = dlq_stats.get('error_types', {})
            if error_types:
                console.print("\nError Types:")
                for error, count in list(error_types.items())[:5]:  # Top 5 errors
                    console.print(f"  • {error}: {count} occurrences")

    except Exception as exc:
        console.print(f"[red]Error getting health status: {exc}[/]")


@bus_command_group.command("metrics")
@click.option("--reset", is_flag=True, help="Reset metrics after displaying")
def show_metrics(reset: bool) -> None:
    """Show detailed Message Bus performance metrics.

    Args:
        reset: Reset metrics after displaying them
    """
    console = get_console()

    try:
        from noveler.application.simple_message_bus import MessageBus, BusConfig
        from noveler.infrastructure.adapters.file_outbox_repository import FileOutboxRepository
        from noveler.application.idempotency import InMemoryIdempotencyStore

        outbox_repo = FileOutboxRepository()
        bus = MessageBus(
            config=BusConfig(),
            outbox_repo=outbox_repo,
            idempotency_store=InMemoryIdempotencyStore()
        )

        metrics = bus.get_metrics_summary()

        console.print("[bold blue]Message Bus Performance Metrics[/]")

        # Command metrics
        cmd_stats = metrics.get('commands', {})
        if cmd_stats.get('count', 0) > 0:
            console.print("\n[green]Command Performance:[/]")
            console.print(f"  Total: {cmd_stats['count']}")
            console.print(f"  Average: {cmd_stats['avg_ms']:.1f}ms")
            console.print(f"  P50: {cmd_stats['p50_ms']:.1f}ms")
            console.print(f"  P95: {cmd_stats['p95_ms']:.1f}ms")
            console.print(f"  Failure Rate: {cmd_stats['failure_rate']:.2%}")

        # Event metrics
        event_stats = metrics.get('events', {})
        if event_stats.get('count', 0) > 0:
            console.print("\n[yellow]Event Performance:[/]")
            console.print(f"  Total: {event_stats['count']}")
            console.print(f"  Average: {event_stats['avg_ms']:.1f}ms")
            console.print(f"  P50: {event_stats['p50_ms']:.1f}ms")
            console.print(f"  P95: {event_stats['p95_ms']:.1f}ms")
            console.print(f"  Failure Rate: {event_stats['failure_rate']:.2%}")

        console.print(f"\nTotal Processed Events: {metrics.get('processed_events_total', 0)}")

        if reset:
            bus.reset_metrics()
            console.print("\n[dim]Metrics have been reset.[/]")

    except Exception as exc:
        console.print(f"[red]Error showing metrics: {exc}[/]")


if __name__ == "__main__":
    bus_command_group()
