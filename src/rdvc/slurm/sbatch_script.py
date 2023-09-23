from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader


def render_template(template_name: str, trim_blocks: bool = True, trim_lspace: bool = True, **kwargs: Any) -> str:
    environment = Environment(loader=FileSystemLoader(Path(__file__).parent.parent / "templates"))
    template = environment.get_template(template_name)

    return template.render(trim_blocks=trim_blocks, trim_lspace=trim_lspace, **kwargs)
