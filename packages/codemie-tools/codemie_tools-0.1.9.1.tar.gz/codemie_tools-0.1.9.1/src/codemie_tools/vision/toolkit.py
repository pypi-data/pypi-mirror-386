from typing import Any, Optional, List

from pydantic import Field

from codemie_tools.base.base_toolkit import BaseToolkit
from codemie_tools.base.file_object import FileObject
from codemie_tools.base.models import ToolKit, ToolSet, Tool
from codemie_tools.vision.image_tool import ImageTool
from codemie_tools.vision.tool_vars import IMAGE_TOOL


class VisionToolkit(BaseToolkit):
    chat_model: Optional[Any] = None
    files: list[FileObject] = Field(default_factory=list, exclude=True)

    @classmethod
    def get_tools_ui_info(cls, *args, **kwargs):
        return ToolKit(
            toolkit=ToolSet.VISION.value,
            tools=[
                Tool.from_metadata(IMAGE_TOOL),
            ]
        ).model_dump()

    def get_tools(self):
        """Get tools for processing images.
    
        Returns:
            List of tools for image processing
        """
        tools = []

        # Process files if available
        if not self.files:
            return tools

        tools.append(ImageTool(files=self.files, chat_model=self.chat_model))

        return tools

    @classmethod
    def get_toolkit(
            cls,
            files: List[FileObject],
            chat_model: Optional[Any] = None
    ):
        # Filter for image files
        image_files = []
        for file_obj in files:
            if file_obj.is_image():
                image_files.append(file_obj)
        return VisionToolkit(files=image_files, chat_model=chat_model)
