#!/usr/bin/env python3
"""Namecheap CLI - A comprehensive command-line interface for Namecheap."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import click
import yaml
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.table import Table

from namecheap import Namecheap, NamecheapError
from namecheap.models import DNSRecord

from .completion import get_completion_script

console = Console()


# Configuration
def get_config_dir() -> Path:
    """Get config directory, using XDG on Unix-like systems."""
    import os
    import sys

    if sys.platform == "win32":
        # Windows: use platformdirs for proper Windows paths
        from platformdirs import user_config_dir

        return Path(user_config_dir("namecheap"))
    # Linux/macOS: use XDG
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        return Path(xdg_config) / "namecheap"
    return Path.home() / ".config" / "namecheap"


CONFIG_DIR = get_config_dir()
CONFIG_FILE = CONFIG_DIR / "config.yaml"


class Config:
    """CLI configuration."""

    def __init__(self) -> None:
        self.client: Namecheap | None = None
        self.output_format: str = "table"
        self.no_color: bool = False
        self.quiet: bool = False
        self.verbose: bool = False
        self.profile: str = "default"
        self.sandbox: bool | None = None

    def load_config(self, config_path: Path | None = None) -> dict:
        """Load configuration from file."""
        path = config_path or CONFIG_FILE
        if not path.exists():
            return {}

        with open(path) as f:
            return yaml.safe_load(f) or {}

    def init_client(self) -> Namecheap:
        """Initialize Namecheap client."""
        if self.client:
            return self.client

        # Check if config file exists
        if not CONFIG_FILE.exists():
            console.print("[red]❌ Configuration not found![/red]")
            console.print(
                "\nPlease run [bold cyan]namecheap-cli config init[/bold cyan] to set up your configuration."
            )
            console.print(
                f"\nThis will create a config file at: [dim]{CONFIG_FILE}[/dim]"
            )
            sys.exit(1)

        config = self.load_config()
        profile_config = config.get("profiles", {}).get(self.profile, {})

        # Check if profile exists
        if not profile_config:
            console.print(
                f"[red]❌ Profile '{self.profile}' not found in configuration![/red]"
            )
            console.print(
                f"\nAvailable profiles: {', '.join(config.get('profiles', {}).keys()) or 'none'}"
            )
            console.print(
                "\nRun [bold cyan]namecheap-cli config init[/bold cyan] to create a new profile."
            )
            sys.exit(1)

        # Override sandbox if specified
        if self.sandbox is not None:
            profile_config["sandbox"] = self.sandbox

        try:
            self.client = Namecheap(**profile_config)
            return self.client
        except Exception as e:
            # Check for common configuration errors
            error_msg = str(e)
            if (
                "Parameter APIUser is missing" in error_msg
                or "Parameter APIKey is missing" in error_msg
            ):
                console.print("[red]❌ Invalid or incomplete configuration![/red]")
                console.print(
                    "\nYour configuration appears to be missing required fields."
                )
                console.print(
                    "Please run [bold cyan]namecheap-cli config init[/bold cyan] to reconfigure."
                )
            else:
                console.print(f"[red]❌ Error initializing client: {e}[/red]")
            sys.exit(1)


pass_config = click.make_pass_decorator(Config, ensure=True)


def output_formatter(data: Any, format: str, headers: list[str] | None = None) -> None:
    """Format output based on specified format."""
    if format == "json":
        click.echo(json.dumps(data, indent=2, default=str))
    elif format == "yaml":
        click.echo(yaml.dump(data, default_flow_style=False, default=str))
    elif format == "csv":
        if isinstance(data, list) and data:
            if headers:
                click.echo(",".join(headers))
            for item in data:
                if isinstance(item, dict):
                    click.echo(",".join(str(item.get(h, "")) for h in headers))
                else:
                    click.echo(",".join(str(getattr(item, h, "")) for h in headers))
    else:
        # Default table format - handled by specific commands
        pass


@click.group()
@click.option(
    "--config", "config_path", type=click.Path(exists=True), help="Config file path"
)
@click.option("--profile", default="default", help="Config profile to use")
@click.option("--sandbox", is_flag=True, help="Use sandbox API")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["table", "json", "yaml", "csv"]),
    default="table",
    help="Output format",
)
@click.option("--no-color", is_flag=True, help="Disable colored output")
@click.option("--quiet", "-q", is_flag=True, help="Minimal output")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.version_option()
@pass_config
def cli(
    config: Config, config_path, profile, sandbox, output, no_color, quiet, verbose
) -> None:
    """Namecheap CLI - Manage domains and DNS records."""
    config.output_format = output
    config.no_color = no_color
    config.quiet = quiet
    config.verbose = verbose
    config.profile = profile
    config.sandbox = sandbox

    if no_color:
        console._color_system = None


@cli.group("domain")
def domain_group() -> None:
    """Domain management commands."""
    pass


@domain_group.command("list")
@click.option("--status", type=click.Choice(["active", "expired", "locked"]))
@click.option(
    "--sort", type=click.Choice(["name", "expires", "created"]), default="name"
)
@click.option("--expiring-in", type=int, help="Show domains expiring within N days")
@pass_config
def domain_list(
    config: Config, status: str | None, sort: str, expiring_in: int | None
) -> None:
    """List all domains."""
    nc = config.init_client()

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task("Loading domains...", total=None)
            domains = nc.domains.list()

        # Filter by status
        if status:
            if status == "active":
                domains = [d for d in domains if not d.is_expired]
            elif status == "expired":
                domains = [d for d in domains if d.is_expired]
            elif status == "locked":
                domains = [d for d in domains if d.is_locked]

        # Filter by expiration
        if expiring_in:
            cutoff = datetime.now() + timedelta(days=expiring_in)
            domains = [d for d in domains if d.expires <= cutoff]

        # Sort
        if sort == "name":
            domains.sort(key=lambda d: d.name)
        elif sort == "expires":
            domains.sort(key=lambda d: d.expires)
        elif sort == "created":
            domains.sort(key=lambda d: d.created)

        # Output
        if config.output_format == "table":
            table = Table(title=f"Domains ({len(domains)} total)")
            table.add_column("Domain", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Expires", style="yellow")
            table.add_column("Auto-Renew")
            table.add_column("Locked")

            for d in domains:
                status_text = "Active" if not d.is_expired else "Expired"
                status_style = "green" if not d.is_expired else "red"
                table.add_row(
                    d.name,
                    f"[{status_style}]{status_text}[/{status_style}]",
                    d.expires.strftime("%Y-%m-%d"),
                    "✓" if d.auto_renew else "✗",
                    "🔒" if d.is_locked else "",
                )

            console.print(table)
        else:
            data = [
                {
                    "domain": d.name,
                    "status": "active" if not d.is_expired else "expired",
                    "expires": d.expires.isoformat(),
                    "auto_renew": d.auto_renew,
                    "locked": d.is_locked,
                }
                for d in domains
            ]
            output_formatter(
                data,
                config.output_format,
                ["domain", "status", "expires", "auto_renew", "locked"],
            )

    except NamecheapError as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)


@domain_group.command("check")
@click.argument("domains", nargs=-1, required=False)
@click.option("--file", "-f", type=click.File("r"), help="File with domains to check")
@pass_config
def domain_check(config: Config, domains: tuple[str, ...], file) -> None:
    """Check domain availability."""
    nc = config.init_client()

    # Collect domains
    domain_list = list(domains)
    if file:
        domain_list.extend(line.strip() for line in file if line.strip())

    if not domain_list:
        console.print("[red]❌ No domains specified[/red]")
        sys.exit(1)

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(f"Checking {len(domain_list)} domains...", total=None)
            results = nc.domains.check(*domain_list, include_pricing=True)

        # Output
        if config.output_format == "table":
            table = Table(title="Domain Availability")
            table.add_column("Domain", style="cyan")
            table.add_column("Available", style="green")
            table.add_column("Price (USD/year)", style="yellow")

            for result in results:
                available_text = "✅ Available" if result.available else "❌ Taken"
                available_style = "green" if result.available else "red"

                if result.available and result.price:
                    price_text = f"${result.price:.2f}"
                else:
                    price_text = "-"

                row = [
                    result.domain,
                    f"[{available_style}]{available_text}[/{available_style}]",
                    price_text,
                ]

                table.add_row(*row)

            console.print(table)

            # Show suggestions for taken domains
            taken = [r for r in results if not r.available]
            if taken and not config.quiet:
                console.print("\n💡 [yellow]Suggestions for taken domains:[/yellow]")
                for r in taken[:3]:  # Show up to 3 suggestions
                    base = r.domain.split(".")[0]
                    suggestions = [
                        f"{base}.net",
                        f"{base}.io",
                        f"get{base}.com",
                        f"{base}app.com",
                    ]
                    console.print(f"  • {r.domain} → {', '.join(suggestions[:3])}")

        else:
            data = []
            for result in results:
                item = {
                    "domain": result.domain,
                    "available": result.available,
                }
                if result.available and result.price:
                    item["price"] = float(result.price)
                data.append(item)

            headers = ["domain", "available", "price"]
            output_formatter(data, config.output_format, headers)

    except NamecheapError as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)


@domain_group.command("info")
@click.argument("domain")
@pass_config
def domain_info(config: Config, domain: str) -> None:
    """Get detailed domain information."""
    nc = config.init_client()

    try:
        domains = nc.domains.list()
        domain_obj = next((d for d in domains if d.name == domain), None)

        if not domain_obj:
            console.print(f"[red]❌ Domain {domain} not found in your account[/red]")
            sys.exit(1)

        if config.output_format == "table":
            console.print(f"\n[bold cyan]Domain Information: {domain}[/bold cyan]\n")
            console.print(
                f"[bold]Status:[/bold] "
                f"{'Active' if not domain_obj.is_expired else '[red]Expired[/red]'}"
            )
            console.print(
                f"[bold]Created:[/bold] {domain_obj.created.strftime('%Y-%m-%d')}"
            )
            console.print(
                f"[bold]Expires:[/bold] {domain_obj.expires.strftime('%Y-%m-%d')}"
            )
            console.print(
                f"[bold]Auto-Renew:[/bold] {'✓ Enabled' if domain_obj.auto_renew else '✗ Disabled'}"
            )
            console.print(
                f"[bold]Locked:[/bold] {'🔒 Yes' if domain_obj.is_locked else '🔓 No'}"
            )
            console.print(
                f"[bold]WHOIS Guard:[/bold] "
                f"{'✓ Enabled' if domain_obj.whois_guard else '✗ Disabled'}"
            )

            # Calculate days until expiration
            days_left = (domain_obj.expires - datetime.now()).days
            if days_left < 30:
                console.print(
                    f"\n⚠️  [yellow]Domain expires in {days_left} days![/yellow]"
                )
            elif days_left < 60:
                console.print(f"\n📅 Domain expires in {days_left} days")

        else:
            data = {
                "domain": domain_obj.name,
                "status": "active" if not domain_obj.is_expired else "expired",
                "created": domain_obj.created.isoformat(),
                "expires": domain_obj.expires.isoformat(),
                "auto_renew": domain_obj.auto_renew,
                "locked": domain_obj.is_locked,
                "whois_guard": domain_obj.whois_guard,
                "days_until_expiration": (domain_obj.expires - datetime.now()).days,
            }
            output_formatter(data, config.output_format)

    except NamecheapError as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)


@cli.group("dns")
def dns_group() -> None:
    """DNS record management commands."""
    pass


@dns_group.command("list")
@click.argument("domain")
@click.option("--type", "-t", help="Filter by record type")
@click.option("--name", "-n", help="Filter by record name")
@pass_config
def dns_list(config: Config, domain: str, type: str | None, name: str | None) -> None:
    """List DNS records for a domain."""
    nc = config.init_client()

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(f"Loading DNS records for {domain}...", total=None)
            records = nc.dns.get(domain)

        # Filter records
        if type:
            records = [r for r in records if r.type == type.upper()]
        if name:
            records = [r for r in records if r.name == name]

        # Sort by type then name
        records.sort(key=lambda r: (r.type, r.name))

        # Output
        if config.output_format == "table":
            table = Table(title=f"DNS Records for {domain} ({len(records)} total)")
            table.add_column("Type", style="cyan", width=8)
            table.add_column("Name", style="green", width=20)
            table.add_column("Value", style="yellow", no_wrap=False)
            table.add_column("TTL", style="magenta", width=8)
            table.add_column("Priority", width=8)

            for r in records:
                # Truncate long values for display
                value = r.value
                if len(value) > 50 and not config.verbose:
                    value = value[:47] + "..."

                table.add_row(
                    r.type,
                    r.name,
                    value,
                    str(r.ttl),
                    str(r.priority) if r.priority else "-",
                )

            console.print(table)
        else:
            data = [
                {
                    "type": r.type,
                    "name": r.name,
                    "value": r.value,
                    "ttl": r.ttl,
                    "priority": r.priority,
                }
                for r in records
            ]
            output_formatter(
                data, config.output_format, ["type", "name", "value", "ttl", "priority"]
            )

    except NamecheapError as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)


@dns_group.command("add")
@click.argument("domain")
@click.argument(
    "record_type",
    type=click.Choice(
        ["A", "AAAA", "CNAME", "MX", "TXT", "NS", "URL", "URL301", "FRAME"],
        case_sensitive=False,
    ),
)
@click.argument("name")
@click.argument("value")
@click.option(
    "--ttl",
    type=int,
    default=1799,
    help="TTL in seconds (60-86400, default: 1799 = Automatic)",
)
@click.option("--priority", type=int, help="Priority (required for MX records)")
@pass_config
def dns_add(
    config: Config,
    domain: str,
    record_type: str,
    name: str,
    value: str,
    ttl: int,
    priority: int | None,
) -> None:
    """Add a DNS record."""
    nc = config.init_client()
    record_type = record_type.upper()

    # Validate MX priority
    if record_type == "MX" and priority is None:
        console.print("[red]❌ Priority is required for MX records[/red]")
        sys.exit(1)

    try:
        # Create the new record
        new_record = DNSRecord(
            name=name, type=record_type, value=value, ttl=ttl, priority=priority
        )

        # Get existing records
        if not config.quiet:
            console.print(f"Adding {record_type} record to {domain}...")

        existing = nc.dns.get(domain)

        # Check for duplicates
        for r in existing:
            if r.name == name and r.type == record_type and r.value == value:
                console.print("[yellow]⚠️  Record already exists[/yellow]")
                return

        # Add the new record
        existing.append(new_record)

        # Build and set records
        builder = nc.dns.builder()
        for r in existing:
            if r.type == "A":
                builder.a(r.name, r.value, ttl=r.ttl)
            elif r.type == "AAAA":
                builder.aaaa(r.name, r.value, ttl=r.ttl)
            elif r.type == "CNAME":
                builder.cname(r.name, r.value, ttl=r.ttl)
            elif r.type == "MX":
                builder.mx(r.name, r.value, priority=r.priority or 10, ttl=r.ttl)
            elif r.type == "TXT":
                builder.txt(r.name, r.value, ttl=r.ttl)
            elif r.type == "NS":
                builder.ns(r.name, r.value, ttl=r.ttl)
            elif r.type == "URL":
                builder.url(r.name, r.value, redirect_type="301", ttl=r.ttl)
                builder._records[-1].type = "URL"
            elif r.type == "URL301":
                builder.url(r.name, r.value, redirect_type="301", ttl=r.ttl)
            elif r.type == "FRAME":
                builder.url(r.name, r.value, redirect_type="frame", ttl=r.ttl)

        nc.dns.set(domain, builder)

        if not config.quiet:
            console.print(f"[green]✅ Added {record_type} record successfully![/green]")

    except NamecheapError as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)


@dns_group.command("delete")
@click.argument("domain")
@click.option("--type", "-t", help="Record type to delete")
@click.option("--name", "-n", help="Record name to delete")
@click.option("--value", "-v", help="Record value to delete")
@click.option("--all", is_flag=True, help="Delete all records (dangerous!)")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@pass_config
def dns_delete(
    config: Config,
    domain: str,
    type: str | None,
    name: str | None,
    value: str | None,
    all: bool,
    yes: bool,
) -> None:
    """Delete DNS records."""
    nc = config.init_client()

    if all and not (type or name or value) and not yes:
        console.print(
            f"[red]⚠️  Warning: This will delete ALL DNS records for {domain}[/red]"
        )
        if not Confirm.ask("Are you sure?", default=False):
            console.print("[yellow]Cancelled[/yellow]")
            return

    try:
        # Get existing records
        records = nc.dns.get(domain)
        original_count = len(records)

        # Filter records to keep
        if all and not (type or name or value):
            records_to_keep = []
        else:
            records_to_keep = []
            records_to_delete = []

            for r in records:
                should_delete = True
                if type and r.type != type.upper():
                    should_delete = False
                if name and r.name != name:
                    should_delete = False
                if value and r.value != value:
                    should_delete = False

                if should_delete and (type or name or value):
                    records_to_delete.append(r)
                else:
                    records_to_keep.append(r)

            if not records_to_delete:
                console.print("[yellow]No matching records found[/yellow]")
                return

            # Show what will be deleted
            if not yes and not config.quiet:
                console.print(
                    f"[yellow]Will delete {len(records_to_delete)} record(s):[/yellow]"
                )
                for r in records_to_delete:
                    console.print(f"  • {r.type} {r.name} → {r.value}")

                if not Confirm.ask("Continue?", default=True):
                    console.print("[yellow]Cancelled[/yellow]")
                    return

        # Build remaining records
        if records_to_keep:
            builder = nc.dns.builder()
            for r in records_to_keep:
                if r.type == "A":
                    builder.a(r.name, r.value, ttl=r.ttl)
                elif r.type == "AAAA":
                    builder.aaaa(r.name, r.value, ttl=r.ttl)
                elif r.type == "CNAME":
                    builder.cname(r.name, r.value, ttl=r.ttl)
                elif r.type == "MX":
                    builder.mx(r.name, r.value, priority=r.priority or 10, ttl=r.ttl)
                elif r.type == "TXT":
                    builder.txt(r.name, r.value, ttl=r.ttl)
                elif r.type == "NS":
                    builder.ns(r.name, r.value, ttl=r.ttl)
                elif r.type == "URL":
                    builder.url(r.name, r.value, redirect_type="301", ttl=r.ttl)
                    builder._records[-1].type = "URL"
                elif r.type == "URL301":
                    builder.url(r.name, r.value, redirect_type="301", ttl=r.ttl)
                elif r.type == "FRAME":
                    builder.url(r.name, r.value, redirect_type="frame", ttl=r.ttl)

            nc.dns.set(domain, builder)
        else:
            # Delete all records by setting empty builder
            nc.dns.set(domain, nc.dns.builder())

        deleted_count = original_count - len(records_to_keep)
        if not config.quiet:
            console.print(f"[green]✅ Deleted {deleted_count} record(s)[/green]")

    except NamecheapError as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)


@dns_group.command("export")
@click.argument("domain")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["bind", "yaml", "json"]),
    default="yaml",
    help="Export format",
)
@click.option(
    "--output", "-o", type=click.File("w"), help="Output file (default: stdout)"
)
@pass_config
def dns_export(config: Config, domain: str, format: str, output) -> None:
    """Export DNS records."""
    nc = config.init_client()

    try:
        records = nc.dns.get(domain)

        if format == "bind":
            # BIND zone file format
            lines = [f"; Zone file for {domain}", f"; Exported at {datetime.now()}", ""]

            for r in sorted(records, key=lambda x: (x.type, x.name)):
                if r.type == "MX":
                    lines.append(
                        f"{r.name}\t{r.ttl}\tIN\t{r.type}\t{r.priority}\t{r.value}"
                    )
                else:
                    lines.append(f"{r.name}\t{r.ttl}\tIN\t{r.type}\t{r.value}")

            content = "\n".join(lines)

        elif format == "yaml":
            # YAML format
            data = {
                "domain": domain,
                "records": [
                    {
                        "type": r.type,
                        "name": r.name,
                        "value": r.value,
                        "ttl": r.ttl,
                        **({"priority": r.priority} if r.priority else {}),
                    }
                    for r in records
                ],
            }
            content = yaml.dump(data, default_flow_style=False)

        else:  # json
            data = {
                "domain": domain,
                "records": [
                    {
                        "type": r.type,
                        "name": r.name,
                        "value": r.value,
                        "ttl": r.ttl,
                        **({"priority": r.priority} if r.priority else {}),
                    }
                    for r in records
                ],
            }
            content = json.dumps(data, indent=2)

        if output:
            output.write(content)
            if not config.quiet:
                console.print(
                    f"[green]✅ Exported {len(records)} records to {output.name}[/green]"
                )
        else:
            click.echo(content)

    except NamecheapError as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)


@cli.group("account")
def account_group() -> None:
    """Account management commands."""
    pass


@account_group.command("balance")
@pass_config
def account_balance(config: Config) -> None:
    """Check account balance."""
    config.init_client()

    try:
        # This would need to be implemented in the SDK
        console.print(
            "[yellow]Account balance check not yet implemented in SDK[/yellow]"
        )
        console.print("This feature requires the users.getBalances API method")

    except NamecheapError as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)


@cli.group("config")
def config_group() -> None:
    """Configuration management commands."""
    pass


@config_group.command("init")
def config_init() -> None:
    """Initialize configuration file."""
    CONFIG_DIR.mkdir(exist_ok=True)

    if CONFIG_FILE.exists() and not Confirm.ask(
        f"{CONFIG_FILE} already exists. Overwrite?", default=False
    ):
        console.print("[yellow]Cancelled[/yellow]")
        return

    console.print("\n[bold cyan]Namecheap CLI Configuration Wizard[/bold cyan]\n")

    console.print("[dim]To get your API key:[/dim]")
    console.print(
        "1. Go to [link=https://ap.www.namecheap.com/settings/tools/apiaccess/]https://ap.www.namecheap.com/settings/tools/apiaccess/[/link]"
    )
    console.print("2. Enable API access")
    console.print("3. Whitelist your IP address")
    console.print("4. Generate your API key\n")

    # Get configuration values
    api_key = Prompt.ask("API Key", password=True)
    username = Prompt.ask("Username")
    api_user = Prompt.ask("API User", default=username)
    sandbox = Confirm.ask("Use sandbox API?", default=True)

    # Create config
    config = {
        "default_profile": "default",
        "profiles": {
            "default": {
                "api_key": api_key,
                "username": username,
                "api_user": api_user,
                "sandbox": sandbox,
            }
        },
        "defaults": {
            "output": "table",
            "color": True,
            "auto_renew": True,
            "whois_privacy": True,
            "dns_ttl": 1799,
        },
    }

    # Save config
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(config, f, default_flow_style=False)

    # Set permissions to 600 (read/write for owner only)
    CONFIG_FILE.chmod(0o600)

    console.print(f"\n[green]✅ Configuration saved to {CONFIG_FILE}[/green]")
    console.print("\n💡 Tips:")
    console.print(
        "  • You can also use environment variables (NAMECHEAP_API_KEY, etc.)"
    )
    console.print("  • Add more profiles with: nc config add-profile <name>")
    console.print("  • Use a profile with: nc --profile <name> <command>")


@cli.command("completion")
@click.argument("shell", type=click.Choice(["bash", "zsh", "fish"]))
def completion(shell: str) -> None:
    """Generate shell completion script."""
    script = get_completion_script(shell)
    click.echo(script)

    if not console.is_terminal:
        # Script is being redirected, just output it
        return

    # Show instructions
    console.print(f"\n[dim]# To install {shell} completion:[/dim]")

    if shell == "bash":
        console.print("[dim]# Add to ~/.bashrc or ~/.bash_profile:[/dim]")
        console.print("[dim]nc completion bash >> ~/.bashrc[/dim]")
    elif shell == "zsh":
        console.print("[dim]# Add to ~/.zshrc:[/dim]")
        console.print("[dim]nc completion zsh >> ~/.zshrc[/dim]")
    elif shell == "fish":
        console.print("[dim]# Add to fish config:[/dim]")
        console.print(
            "[dim]nc completion fish > ~/.config/fish/completions/nc.fish[/dim]"
        )


def main() -> None:
    """Main entry point."""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        if "--debug" in sys.argv:
            console.print_exception()
        else:
            console.print(f"[red]❌ Unexpected error: {e}[/red]")
            console.print("[dim]Run with --debug for full traceback[/dim]")
        sys.exit(1)


if __name__ == "__main__":
    main()
