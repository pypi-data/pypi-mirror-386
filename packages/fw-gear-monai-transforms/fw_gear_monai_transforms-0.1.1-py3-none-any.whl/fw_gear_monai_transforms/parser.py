"""Parser module to parse gear config.json."""

from typing import Tuple

from flywheel_gear_toolkit import GearToolkitContext


def parse_config(
    context: GearToolkitContext,
) -> Tuple[str, str, int]:
    """Returns input file and transforms module paths."""
    return (
        context.get_input_path("input-file"),
        context.get_input_path("transform-script"),
        context.config["number-of-iterations"],
    )
