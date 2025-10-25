#!/usr/bin/env python
""" Get completed tasks from taskwarrior and output a simple report """
import subprocess
import json
import itertools
import operator
from datetime import date
from dateutil.relativedelta import relativedelta, MO
import click

__version__ = "0.3.1"

def validate_tasks(tasks):
    """ Validate tasks have a proejct, inject "None" if they don't """
    try:
        for task in tasks:
            test = task["project"]
    except KeyError:
        task["project"] = "None"
    return tasks

@click.command()
@click.option("--bullet", default="*", help="Character to use for bullets in list")
@click.option("--header", is_flag=True, help="Display date header")
@click.option(
    "--ignore", multiple=True, help="Project(s) to ignore in the report (can be used multiple times)"
)
@click.option(
    "--sort", is_flag=True, default=True, help="Alphabetically sort by project"
)
@click.option("--uuid", is_flag=True, help="Display the task UUID")
@click.version_option(__version__, prog_name="task-status")
def main(uuid, header, bullet, sort, ignore):
    """Main function that does all the work for task_status"""
    today = date.today()
    last_monday = today + relativedelta(weekday=MO(-2))

    task_command = [
        "task",
        f"end.after:{last_monday}",
        "status_report:display",
        "-home",
        "-DELETED",
        "-delegated",
        "export",
    ]
    tasks = subprocess.run(
        task_command,
        capture_output=True,
        check=True,
    )
    entries = validate_tasks(json.loads(tasks.stdout.decode()))

    # Convert ignore tuple to set for faster lookup
    ignored_projects = set(ignore)

    output_list = []
    project_list = []
    if header:
        print(f"Reporting from: {last_monday}")
    for status_projects, status_entries in itertools.groupby(
        entries, key=operator.itemgetter("project")
    ):
        # Skip ignored projects
        if status_projects not in ignored_projects and status_projects not in project_list:
            project_list.append(status_projects)
            output_list.append(list(status_entries))
    if sort:
        project_list.sort()
    for project in project_list:
        print(f"{bullet} {project}")
        for entry in entries:
            if entry["project"] == project and uuid:
                print(f'\t{bullet} {entry["description"]} ({entry["uuid"]})')
            elif entry["project"] == project:
                print(f'\t{bullet} {entry["description"]}')


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter # pragma: no cover
