import typer
import subprocess
from dbt_swap.core.smart_builder import DbtSmartBuilder
from dbt_swap.utils.logging import get_logger
from dbt_swap.cli.common import set_env

logger = get_logger(__name__)


app = typer.Typer(
    help="Build only modified models intelligently.",
)


@app.command("smart-build")
def smart_build(
    ctx: typer.Context,
    target: str = typer.Option("dev", "--target", "-t", help="DBT target name."),
    state: str = typer.Option("state", "--state", help="DBT state name."),
    dry_run: bool = typer.Option(False, help="Perform a dry run without making changes."),
    verbose: bool = typer.Option(False, help="Enable verbose output."),
    full: bool = typer.Option(True, help="Run with --full-refresh, --defer and --favor-state flags."),
    extra_args: list[str] = typer.Argument(
        None,
        help="Additional arguments to pass directly to `dbt build`.",
        allow_dash=True,
    ),
):
    """
    Run a smart build — builds only modified models based on dbt state and column level lineage.
    Additional arguments after `smart-build` are passed directly to `dbt build`.
    """
    set_env(target=target, state=state)

    dbt_smart_build = DbtSmartBuilder(verbose=verbose)
    modified_nodes = dbt_smart_build.find_modified_nodes()

    # Build the dbt command with modified nodes and extra arguments
    if extra_args is None:
        extra_args = []
    if full:
        extra_args = list(set(extra_args).union({"--full-refresh", "--defer", "--favor-state"}))
    base_command = ["dbt", "build", "-s"] + modified_nodes + extra_args
    command_str = " ".join(base_command)

    resource_types = {node["resource_type"] for node in dbt_smart_build.nodes.values()}
    resource_type_counts = {
        resource_type: {
            "smart_count": sum(
                1
                for node in dbt_smart_build.nodes.values()
                if node["resource_type"] == resource_type and node["name"] in modified_nodes
            ),
            "total_count": sum(
                1
                for node in dbt_smart_build.modified_and_downstream_node_ids
                if dbt_smart_build.nodes[node]["resource_type"] == resource_type
            ),
        }
        for resource_type in resource_types
    }
    for resource_type, counts in resource_type_counts.items():
        if counts["total_count"] > 0:
            logger.info(f"Building {counts['smart_count']}/{counts['total_count']} {resource_type}(s)")

    if dry_run:
        logger.info("[DRY RUN] Would build:")
        for modified_node in modified_nodes:
            logger.info(modified_node)
        return

    if len(modified_nodes) > 0:
        subprocess.run(command_str, shell=True, check=True)
