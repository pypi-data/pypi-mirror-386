"""Build dataset resource commands for cmemc."""

import re

import click
from click import ClickException, UsageError
from cmem.cmempy.workspace.projects.resources import get_all_resources
from cmem.cmempy.workspace.projects.resources.resource import (
    delete_resource,
    get_resource_metadata,
    get_resource_usage_data,
)

from cmem_cmemc import completion
from cmem_cmemc.command import CmemcCommand
from cmem_cmemc.command_group import CmemcGroup
from cmem_cmemc.context import ApplicationContext
from cmem_cmemc.utils import split_task_id, struct_to_table

RESOURCE_FILTER_TYPES = ["project", "regex"]
RESOURCE_FILTER_TYPES_HIDDEN = ["ids"]
RESOURCE_FILTER_TEXT = (
    "Filter file resources based on metadata. "
    f"First parameter CHOICE can be one of {RESOURCE_FILTER_TYPES!s}"
    ". The second parameter is based on CHOICE, e.g. a project "
    "ID or a regular expression string."
)


def _get_resources_filtered(
    resources: list[dict], filter_name: str, filter_value: str | tuple[str, ...]
) -> list[dict]:
    """Get file resources but filtered according to name and value."""
    # check for correct filter names (filter ids is used internally only)
    if filter_name not in RESOURCE_FILTER_TYPES + RESOURCE_FILTER_TYPES_HIDDEN:
        raise UsageError(
            f"{filter_name} is an unknown filter name. " f"Use one of {RESOURCE_FILTER_TYPES}."
        )
    # filter by ID list
    if filter_name == "ids":
        return [_ for _ in resources if _["id"] in filter_value]
    # filter by project
    if filter_name == "project":
        return [_ for _ in resources if _["project"] == str(filter_value)]
    # filter by regex
    if filter_name == "regex":
        return [_ for _ in resources if re.search(str(filter_value), _["name"])]
    # return unfiltered list
    return resources


@click.command(cls=CmemcCommand, name="list")
@click.option("--raw", is_flag=True, help="Outputs raw JSON.")
@click.option(
    "--id-only",
    is_flag=True,
    help="Lists only resource names and no other metadata. "
    "This is useful for piping the IDs into other commands.",
)
@click.option(
    "--filter",
    "filters_",
    multiple=True,
    type=(str, str),
    shell_complete=completion.resource_list_filter,
    help=RESOURCE_FILTER_TEXT,
)
@click.pass_obj
def list_command(
    app: ApplicationContext, raw: bool, id_only: bool, filters_: tuple[tuple[str, str], ...]
) -> None:
    """List available file resources.

    Outputs a table or a list of dataset resources (files).
    """
    resources = get_all_resources()
    for _ in filters_:
        filter_name, filter_value = _
        resources = _get_resources_filtered(resources, filter_name, filter_value)
    if raw:
        app.echo_info_json(resources)
        return
    if id_only:
        for _ in sorted(_["id"] for _ in resources):
            app.echo_result(_)
        return
    # output a user table
    table = []
    headers = ["ID", "Modified", "Size"]
    for _ in resources:
        row = [
            _["id"],
            _["modified"],
            _["size"],
        ]
        table.append(row)
    app.echo_info_table(
        table,
        headers=headers,
        sort_column=0,
        empty_table_message="No dataset resources found. "
        "Use the `dataset create` command to create a new file based dataset.",
    )


@click.command(cls=CmemcCommand, name="delete")
@click.argument("resource_ids", nargs=-1, type=click.STRING, shell_complete=completion.resource_ids)
@click.option("--force", is_flag=True, help="Delete resource even if in use by a task.")
@click.option(
    "-a",
    "--all",
    "all_",
    is_flag=True,
    help="Delete all resources. " "This is a dangerous option, so use it with care.",
)
@click.option(
    "--filter",
    "filters_",
    multiple=True,
    type=(str, str),
    shell_complete=completion.resource_list_filter,
    help=RESOURCE_FILTER_TEXT,
)
@click.pass_obj
def delete_command(
    app: ApplicationContext,
    resource_ids: tuple[str, ...],
    force: bool,
    all_: bool,
    filters_: tuple[tuple[str, str], ...],
) -> None:
    """Delete file resources.

    There are three selection mechanisms: with specific IDs, only those
    specified resources will be deleted; by using --filter, resources based
    on the filter type and value will be deleted; using --all will delete
    all resources.
    """
    if resource_ids == () and not all_ and filters_ == ():
        raise UsageError(
            "Either specify at least one resource ID or use the --all or "
            "--filter options to specify resources for deletion."
        )

    resources = get_all_resources()
    if len(resource_ids) > 0:
        for resource_id in resource_ids:
            if resource_id not in [_["id"] for _ in resources]:
                raise ClickException(f"Resource {resource_id} not available.")
        # "filter" by id
        resources = _get_resources_filtered(resources, "ids", resource_ids)
    for _ in filters_:
        resources = _get_resources_filtered(resources, _[0], _[1])

    # avoid double removal as well as sort IDs
    processed_ids = sorted({_["id"] for _ in resources}, key=lambda v: v.lower())
    count = len(processed_ids)
    for current, resource_id in enumerate(processed_ids, start=1):
        current_string = str(current).zfill(len(str(count)))
        app.echo_info(f"Delete resource {current_string}/{count}: {resource_id} ... ", nl=False)
        project_id, resource_local_id = split_task_id(resource_id)
        usage = get_resource_usage_data(project_id, resource_local_id)
        if len(usage) > 0:
            app.echo_error(f"in use by {len(usage)} task(s)", nl=False)
            if force:
                app.echo_info(" ... ", nl=False)
            else:
                app.echo_info("")
                continue
        delete_resource(project_name=project_id, resource_name=resource_local_id)
        app.echo_success("deleted")


@click.command(cls=CmemcCommand, name="inspect")
@click.argument("resource_id", type=click.STRING, shell_complete=completion.resource_ids)
@click.option("--raw", is_flag=True, help="Outputs raw JSON.")
@click.pass_obj
def inspect_command(app: ApplicationContext, resource_id: str, raw: bool) -> None:
    """Display all metadata of a file resource."""
    project_id, resource_id = split_task_id(resource_id)
    resource_data = get_resource_metadata(project_id, resource_id)
    if raw:
        app.echo_info_json(resource_data)
    else:
        table = struct_to_table(resource_data)
        app.echo_info_table(table, headers=["Key", "Value"], sort_column=0)


@click.command(cls=CmemcCommand, name="usage")
@click.argument("resource_id", type=click.STRING, shell_complete=completion.resource_ids)
@click.option("--raw", is_flag=True, help="Outputs raw JSON.")
@click.pass_obj
def usage_command(app: ApplicationContext, resource_id: str, raw: bool) -> None:
    """Display all usage data of a file resource."""
    project_id, resource_id = split_task_id(resource_id)
    usage = get_resource_usage_data(project_id, resource_id)
    if raw:
        app.echo_info_json(usage)
        return
    # output a user table
    table = []
    headers = ["Task ID", "Type", "Label"]
    for _ in usage:
        row = [project_id + ":" + _["id"], _["taskType"], _["label"]]
        table.append(row)
    app.echo_info_table(table, headers=headers, sort_column=2)


@click.group(cls=CmemcGroup)
def resource() -> CmemcGroup:  # type: ignore[empty-body]
    """List, inspect or delete dataset file resources.

    File resources are identified by their paths and project IDs.
    """


resource.add_command(list_command)
resource.add_command(delete_command)
resource.add_command(inspect_command)
resource.add_command(usage_command)
