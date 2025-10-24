import subprocess

import typer
from rich import print

from sing_box_cli.api import api as api_app
from sing_box_cli.common import ClearCacheOption, UpdateConfigOption, ensure_root
from sing_box_cli.config import config as config_app
from sing_box_cli.config.config import get_config, run_cmd
from sing_box_cli.service import SharedContext, get_context_obj, service as service_app
from sing_box_cli.service.manager import create_service

app = typer.Typer(help="sing-box manager.")
app.add_typer(api_app)
app.add_typer(service_app, name="service")
app.add_typer(config_app, name="config")


@app.callback(invoke_without_command=False)
def callback(ctx: typer.Context) -> None:
    cfg = get_config()
    service = create_service(cfg)
    ctx.obj = SharedContext(config=cfg, service=service)


@app.command()
def run(
    ctx: typer.Context,
    update: UpdateConfigOption = False,
    purge: ClearCacheOption = False,
) -> None:
    """Run sing-box if host's service unavailable or debug mode."""
    ensure_root()
    cfg = get_context_obj(ctx).config

    if update:
        if cfg.update_config():
            pass
        else:
            print("❌ Failed to update configuration.")
    if purge:
        cfg.clear_cache()

    # stop if empty
    if cfg.config_file_content == "{}":
        print("❌ Configuration file is empty.")
        raise typer.Exit(1)

    # run
    cmd = run_cmd(cfg).split()
    subprocess.run(cmd)


@app.command()
def version(ctx: typer.Context) -> None:
    """Show version"""
    from sing_box_cli import __version__

    print(f"🔖 sing-box-cli {__version__}")
    print(f"📦 {get_context_obj(ctx).service.version()}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
