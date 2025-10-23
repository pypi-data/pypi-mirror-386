from wbcore.metadata.configs.display.instance_display.shortcuts import (
    Display,
    create_simple_display,
)
from wbcore.metadata.configs.preview import PreviewViewConfig


class ActivityPreviewConfig(PreviewViewConfig):
    def get_display(self) -> Display:
        return create_simple_display([["title", "type", "result"]])
