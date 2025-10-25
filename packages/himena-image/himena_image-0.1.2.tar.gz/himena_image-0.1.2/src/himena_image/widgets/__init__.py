from himena_image.widgets.viewer import NDImageViewer
from himena.plugins import register_widget_class
from himena.consts import StandardType

register_widget_class(StandardType.IMAGE, NDImageViewer, priority=1)
