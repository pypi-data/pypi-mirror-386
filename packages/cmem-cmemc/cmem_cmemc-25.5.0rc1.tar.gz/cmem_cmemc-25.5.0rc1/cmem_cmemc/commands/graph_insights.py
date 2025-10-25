"""Graph Insights command group"""

from typing import TYPE_CHECKING

import click
from click import Argument, Context
from click.shell_completion import CompletionItem
from cmem.cmempy.api import get_json, request
from cmem.cmempy.config import get_dp_api_endpoint
from requests import HTTPError

from cmem_cmemc.command import CmemcCommand
from cmem_cmemc.command_group import CmemcGroup
from cmem_cmemc.completion import NOT_SORTED, finalize_completion, graph_uris
from cmem_cmemc.exceptions import CmemcError
from cmem_cmemc.object_list import (
    DirectListPropertyFilter,
    DirectValuePropertyFilter,
    ObjectList,
    transform_lower,
)
from cmem_cmemc.string_processor import GraphLink, TimeAgo
from cmem_cmemc.utils import get_graphs_as_dict, struct_to_table

if TYPE_CHECKING:
    from cmem_cmemc.context import ApplicationContext


API_BASE = get_dp_api_endpoint() + "/api/ext/semspect"


def is_available() -> bool:
    """Check availability of graph insights endpoints

    {
     "isActive": true,
     "isUserAllowed": true
    }
    """
    try:
        data: dict[str, bool] = get_json(API_BASE)
    except HTTPError:
        return False
    return bool(data["isActive"] is True and data["isUserAllowed"] is True)


def check_availability(ctx: click.Context) -> None:
    """Check availability of graph insights endpoints or raise an exception"""
    if is_available():
        return
    app: ApplicationContext = ctx.obj
    raise CmemcError(app, "Graph Insights is not available.")


def get_snapshots(ctx: click.Context) -> list[dict[str, str | bool | list[str]]]:
    """Get the snapshot list (all snapshots)"""
    check_availability(ctx)
    data: list[dict[str, str | bool | list[str]]] = get_json(
        API_BASE + "/snapshot/status", params={"includeManagementOnly": True}
    )
    return data


def complete_snapshot_ids(ctx: Context, param: Argument, incomplete: str) -> list[CompletionItem]:  # noqa: ARG001
    """Provide auto-completion for snapshot Ids"""
    snapshots = get_snapshots(ctx)
    snapshots = sorted(
        snapshots, key=lambda snapshot: snapshot["updateInfoTimestamp"], reverse=True
    )
    options = [
        (
            snapshot["databaseId"],
            f"{snapshot['mainGraphSynced']} ({snapshot['updateInfoTimestamp']})",
        )
        for snapshot in snapshots
    ]
    return finalize_completion(candidates=options, incomplete=incomplete, sort_by=NOT_SORTED)


snapshot_list = ObjectList(
    name="insight snapshots",
    get_objects=get_snapshots,
    filters=[
        DirectValuePropertyFilter(
            name="id",
            description="Snapshots with a specific id.",
            property_key="databaseId",
            transform=transform_lower,
        ),
        DirectValuePropertyFilter(
            name="main-graph",
            description="Snapshots with a specific main graph.",
            property_key="mainGraphSynced",
        ),
        DirectValuePropertyFilter(
            name="status",
            description="Snapshots with a specific status.",
            property_key="status",
        ),
        DirectListPropertyFilter(
            name="affected-graph",
            description="Snapshots with a specific affected graph (main or sub-graphs).",
            property_key="allGraphsSynced",
        ),
    ],
)


@click.command(cls=CmemcCommand, name="list")
@click.option(
    "--filter",
    "filter_",
    type=(str, str),
    help=snapshot_list.get_filter_help_text(),
    shell_complete=snapshot_list.complete_values,
    multiple=True,
)
@click.option("--raw", is_flag=True, help="Outputs raw JSON response.")
@click.option(
    "--id-only",
    is_flag=True,
    help="Return the snapshot IDs only. This is useful for piping the IDs into other commands.",
)
@click.pass_context
def list_command(ctx: Context, filter_: tuple[tuple[str, str]], id_only: bool, raw: bool) -> None:
    """List graph insight snapshots.

    Graph Insights Snapshots are identified by an ID.
    """
    check_availability(ctx)
    app: ApplicationContext = ctx.obj
    snapshots = snapshot_list.apply_filters(ctx=ctx, filter_=filter_)

    if id_only:
        for _ in snapshots:
            click.echo(_["databaseId"])
        return

    if raw:
        app.echo_info_json(snapshots)
        return

    graphs = get_graphs_as_dict()
    table = []
    for _ in snapshots:
        id_ = _["databaseId"]
        main_graph = _["mainGraphSynced"]
        updated = _["updateInfoTimestamp"]
        status = _["status"]
        if main_graph not in graphs:
            main_graph = rf"\[missing: {main_graph}]"
        table.append([id_, main_graph, updated, status])

    app.echo_info_table(
        table,
        headers=["ID", "Main Graph", "Updated", "Status"],
        sort_column=0,
        cell_processing={1: GraphLink(), 2: TimeAgo()},
        empty_table_message="No graph insight snapshots found.",
    )


@click.command(cls=CmemcCommand, name="delete")
@click.argument("SNAPSHOT_ID", type=str, shell_complete=complete_snapshot_ids, required=False)
@click.option(
    "--filter",
    "filter_",
    type=(str, str),
    help=snapshot_list.get_filter_help_text(),
    shell_complete=snapshot_list.complete_values,
    multiple=True,
)
@click.option("-a", "--all", "all_", is_flag=True, help="Delete all snapshots.")
@click.pass_context
def delete_command(
    ctx: Context, snapshot_id: str | None, filter_: tuple[tuple[str, str]], all_: bool
) -> None:
    """Delete a graph insight snapshot.

    Graph Insight Snapshots are identified by an ID.
    To get a list of existing snapshots,
    execute the `graph insights list` command or use tab-completion.
    """
    check_availability(ctx)
    app: ApplicationContext = ctx.obj
    if snapshot_id is None and not filter_ and not all_:
        raise click.UsageError("Either provide a snapshot ID or a filter, or use the --all flag.")

    if all_:
        app.echo_info("Deleting all snapshots ... ", nl=False)
        request(method="DELETE", uri=f"{API_BASE}/snapshot")
        app.echo_success("done")
        return

    all_snapshots = get_snapshots(ctx)
    all_snapshot_ids = [_["databaseId"] for _ in all_snapshots]
    filter_to_apply = list(filter_) if filter_ else []
    if snapshot_id:
        filter_to_apply.append(("id", snapshot_id))
    snapshots_to_delete = snapshot_list.apply_filters(ctx=ctx, filter_=filter_to_apply)
    if not snapshots_to_delete:
        raise click.UsageError("No snapshots found to delete.")

    for _ in snapshots_to_delete:
        id_to_delete = _["databaseId"]
        if id_to_delete not in all_snapshot_ids:
            raise click.UsageError(f"Snapshot ID '{id_to_delete}' does not exist.")
    for _ in snapshots_to_delete:
        id_to_delete = _["databaseId"]
        app.echo_info(f"Deleting snapshot {id_to_delete} ... ", nl=False)
        request(method="DELETE", uri=f"{API_BASE}/snapshot/{id_to_delete}")
        app.echo_success("done")


@click.command(cls=CmemcCommand, name="create")
@click.argument("iri", type=click.STRING, shell_complete=graph_uris)
@click.pass_context
def create_command(ctx: Context, iri: str) -> None:
    """Create or update a graph insight snapshot.

    Create a graph insight snapshot for a given graph.
    If the snapshot already exists, it is hot-swapped after re-creation.
    The snapshot contains only the (imported) graphs the requesting user can read.
    """
    check_availability(ctx)
    app: ApplicationContext = ctx.obj
    app.echo_info(f"Create / Update graph snapshot for graph {iri} ... ", nl=False)
    request(method="POST", uri=f"{API_BASE}/snapshot", params={"contextGraph": iri})
    app.echo_success("started")


@click.command(cls=CmemcCommand, name="update")
@click.argument("SNAPSHOT_ID", type=str, shell_complete=complete_snapshot_ids, required=False)
@click.option(
    "--filter",
    "filter_",
    type=(str, str),
    help=snapshot_list.get_filter_help_text(),
    shell_complete=snapshot_list.complete_values,
    multiple=True,
)
@click.option("-a", "--all", "all_", is_flag=True, help="Delete all snapshots.")
@click.pass_context
def update_command(
    ctx: Context, snapshot_id: str | None, filter_: tuple[tuple[str, str]], all_: bool
) -> None:
    """Update a graph insight snapshot.

    Update a graph insight snapshot.
    After the update, the snapshot is hot-swapped.
    """
    check_availability(ctx)
    app: ApplicationContext = ctx.obj
    if snapshot_id is None and not filter_ and not all_:
        raise click.UsageError("Either provide a snapshot ID or a filter, or use the --all flag.")

    filter_to_apply = list(filter_) if filter_ else []
    if snapshot_id:
        filter_to_apply.append(("id", snapshot_id))
    snapshots_to_update = snapshot_list.apply_filters(ctx=ctx, filter_=filter_to_apply)

    all_snapshots = get_snapshots(ctx)
    all_snapshot_ids = [_["databaseId"] for _ in all_snapshots]

    if all_:
        snapshots_to_update = get_snapshots(ctx)

    if not snapshots_to_update:
        raise click.UsageError("No snapshots found to delete.")

    for _ in snapshots_to_update:
        id_to_update = _["databaseId"]
        if id_to_update not in all_snapshot_ids:
            raise click.UsageError(f"Snapshot ID '{id_to_update}' does not exist.")
    for _ in snapshots_to_update:
        id_to_update = _["databaseId"]
        app.echo_info(f"Update snapshot {id_to_update} ... ", nl=False)
        request(method="PUT", uri=f"{API_BASE}/snapshot/{snapshot_id}")
        app.echo_success("started")


@click.command(cls=CmemcCommand, name="inspect")
@click.argument("SNAPSHOT_ID", type=str, shell_complete=complete_snapshot_ids)
@click.option("--raw", is_flag=True, help="Outputs raw JSON.")
@click.pass_context
def inspect_command(ctx: Context, snapshot_id: str, raw: bool) -> None:
    """Inspect the metadata of a graph insight snapshot."""
    check_availability(ctx)
    app: ApplicationContext = ctx.obj
    snapshot: dict[str, str | bool | list[str]] = get_json(
        f"{API_BASE}/snapshot/status/{snapshot_id}"
    )
    if raw:
        app.echo_info_json(snapshot)
    else:
        table = struct_to_table(snapshot)
        app.echo_info_table(table, headers=["Key", "Value"], sort_column=0)


@click.group(cls=CmemcGroup, name="insights")
def insights_group() -> CmemcGroup:  # type: ignore[empty-body]
    """List, create, delete and inspect graph insight snapshots.

    Graph Insight Snapshots are identified by an ID.
    To get a list of existing snapshots,
    execute the `graph insights list` command or use tab-completion.
    """


insights_group.add_command(list_command)
insights_group.add_command(delete_command)
insights_group.add_command(create_command)
insights_group.add_command(update_command)
insights_group.add_command(inspect_command)
