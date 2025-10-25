import re
from typing import Optional

import rich
from rich.console import Console
from rich.table import Table

from .colorizer import Colorizer as CL

console = Console()


def display_table(data, with_index: Optional[bool] = None, **kwargs):
    if isinstance(data, list):
        # list of dict
        if len(data) and isinstance(data[0], dict):
            # determine whether an index needs to be shown
            showindex = True
            if len(data) and "index" in data[0]:
                showindex = False
            if with_index is not None:
                showindex = with_index

            # Create rich table
            table = Table(show_header=True, header_style="bold", **kwargs)

            # Add columns
            headers = list(data[0].keys())
            if showindex:
                table.add_column("[dim white]#")
            for header in headers:
                table.add_column(f"[blue]{header}[/blue]")

            # Add rows
            for idx, dic in enumerate(data):
                # first column as index
                row = [str(idx)] if showindex else []

                for k in headers:
                    v = dic.get(k, "")

                    # Highlight of relative times
                    if k in ["relativeStartTime", "relativeEndTime"]:
                        v = CL.past(v) if "(-" in v else CL.future(v)

                    # highlight square bracketted content
                    def replace_brackets(match):
                        content = match.group(1)
                        if content.startswith("bic:"):
                            return f"[bold magenta]\[{content}][/]"
                        else:
                            return f"[bold yellow]\[{content}][/]"

                    if isinstance(v, rich.text.Text):
                        value = v
                    else:
                        value = re.sub(r"\[(.*?)\]", replace_brackets, str(v))

                        # highlight standard brackets
                        value = re.sub(r"\((.*?)\)", r"[green](\1)[/]", value)

                    row.append(value)
                table.add_row(*row)

            console.print(table)

        # list of scalars
        elif len(data):
            table = Table(show_header=False)

            if len(data) == 2:
                table.add_row(*[str(item) for item in data])
            else:
                for item in data:
                    table.add_row(str(item))

            console.print(table)

    if isinstance(data, dict):
        table = Table(show_header=True, header_style="bold", **kwargs)
        table.add_column("Key")
        table.add_column("Value")

        for k, v in data.items():
            table.add_row(f"[bold blue]{k}", str(v))

        console.print(table)
