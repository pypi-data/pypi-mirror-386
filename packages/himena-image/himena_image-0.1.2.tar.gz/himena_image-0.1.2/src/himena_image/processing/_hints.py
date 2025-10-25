from himena import StandardType
from himena.plugins import when_command_executed, when_reader_used


(
    when_command_executed(StandardType.IMAGE, "himena-image:threshold")
    .add_command_suggestion("himena-image:label")
    .add_command_suggestion("himena-image:smooth-mask")
    .add_command_suggestion("himena-image:dilation")
    .add_command_suggestion("himena-image:erosion")
    .add_command_suggestion("himena-image:opening")
    .add_command_suggestion("himena-image:closing")
)
(
    when_command_executed(
        StandardType.IMAGE, "himena-image:gaussian-filter"
    ).add_command_suggestion("himena-image:threshold")
)
(
    when_command_executed(
        StandardType.IMAGE, "himena-image:label"
    ).add_command_suggestion(
        "himena-image:region-properties", defaults={"labels": lambda step: step.id}
    )
)
(
    when_command_executed(StandardType.IMAGE, "himena-image:dog-filter")
    .add_command_suggestion("himena-image:threshold")
    .add_command_suggestion("himena-image:peak-local-max")
)
(
    when_command_executed(StandardType.IMAGE, "himena-image:doh-filter")
    .add_command_suggestion("himena-image:threshold")
    .add_command_suggestion("himena-image:peak-local-max")
)
(
    when_command_executed(StandardType.IMAGE, "himena-image:log-filter")
    .add_command_suggestion("himena-image:threshold")
    .add_command_suggestion("himena-image:peak-local-max")
)
(
    when_reader_used(StandardType.IMAGE)
    .add_command_suggestion("builtins:image:set-colormaps")
    .add_command_suggestion("himena-image:projection")
)
(
    when_command_executed(StandardType.DATAFRAME, "himena-image:roi-measure")
    .add_command_suggestion("builtins:plot:scatter")
    .add_command_suggestion("builtins:plot:line")
    .add_command_suggestion("builtins:plot:histogram")
)
