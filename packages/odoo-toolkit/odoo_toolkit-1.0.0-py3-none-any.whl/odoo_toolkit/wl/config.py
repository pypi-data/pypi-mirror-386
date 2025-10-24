from collections import defaultdict
from fnmatch import fnmatch
from pathlib import Path
from typing import Annotated

from typer import Argument, Option, Typer

from odoo_toolkit.common import (
    EMPTY_LIST,
    TransientProgress,
    get_valid_modules_to_path_mapping,
    normalize_list_option,
    print,
    print_command_title,
    print_error,
    print_header,
    print_success,
)

from .common import WeblateConfig, WeblateConfigError

app = Typer()


@app.command()
def config(
    modules: Annotated[
        list[str],
        Argument(help="Include these Odoo modules in `.weblate.json`, or either `all`, `community`, or `enterprise`."),
    ],
    project: Annotated[str, Option("--project", "-p", help="Specify the Weblate project slug.")],
    exclude: Annotated[
        list[str],
        Option("--exclude", "-x", help="Exclude these modules from being added or updated."),
    ] = EMPTY_LIST,
    languages: Annotated[
        list[str],
        Option(
            "--language",
            "-l",
            help="Define specific language codes for this component. Mostly used for localizations. "
            "If none are given, it follows the default languages on Weblate.",
        ),
    ] = EMPTY_LIST,
    reset: Annotated[
        bool, Option("--reset", "-r", help="Reset the config file for the given project and only add the given modules."),
    ] = False,
    com_path: Annotated[
        Path,
        Option(
            "--com-path",
            "-c",
            help="Specify the path to your Odoo Community repository.",
        ),
    ] = Path("odoo"),
    ent_path: Annotated[
        Path,
        Option(
            "--ent-path",
            "-e",
            help="Specify the path to your Odoo Enterprise repository.",
        ),
    ] = Path("enterprise"),
    extra_addons_paths: Annotated[
        list[Path],
        Option(
            "--addons-path",
            "-a",
            help="Specify extra addons paths if your modules are not in Community or Enterprise.",
        ),
    ] = EMPTY_LIST,
) -> None:
    """Update modules in the Weblate config file.

    This command will add, update, or remove module entries in `.weblate.json` files. The `.weblate.json` files need to
    be located at the provided addons paths' roots. If not, a new file will be created.

    For `odoo` and `enterprise`, the project slug follows the format `odoo-18` for major versions and `odoo-s18-1` for
    SaaS versions. Other repos have their own project slugs. Check the Weblate URLs to find the right project slug.
    """
    print_command_title(":memo: Odoo Weblate Config")

    module_to_path = get_valid_modules_to_path_mapping(
        modules=modules,
        com_path=com_path,
        ent_path=ent_path,
        extra_addons_paths=extra_addons_paths,
        filter_fn=lambda m: not any(fnmatch(m, p) for p in normalize_list_option(exclude)),
    )

    print(f"Modules to include: [b]{'[/b], [b]'.join(sorted(module_to_path.keys()))}[/b]\n")

    # Combine all paths into one list.
    all_addons_paths = [p.expanduser().resolve() for p in [com_path, ent_path, *extra_addons_paths]]

    # Create a mapping from each addons path to the relevant containing modules.
    addons_path_to_modules: dict[Path, list[str]] = defaultdict(list[str])
    for module, module_path in module_to_path.items():
        addons_path = next((ap for ap in all_addons_paths if module_path.is_relative_to(ap)), None)
        if addons_path:
            addons_path_to_modules[addons_path].append(module)
    addons_path_to_modules = dict(addons_path_to_modules)

    # For each addons path, add the given modules to the .weblate.json.
    for addons_path, local_modules in addons_path_to_modules.items():
        weblate_config_path = addons_path / ".weblate.json"

        print_header(f"Updating [u]{weblate_config_path}[/u]")

        weblate_config = WeblateConfig(weblate_config_path)
        if reset:
            weblate_config.clear(project)
        updated, skipped = 0, 0
        for m in TransientProgress().track(local_modules, description="Updating modules ..."):
            if weblate_config.update_module(module_to_path[m], project, normalize_list_option(languages)):
                updated += 1
            else:
                skipped += 1

        try:
            weblate_config.save()
            print(f"Modules added or updated: [b]{updated}[/b]")
            print(f"Modules skipped or removed: [b]{skipped}[/b]")
            print_success("Config file successfully updated.\n")
        except WeblateConfigError as e:
            print_error("Config file update failed.\n", str(e))
