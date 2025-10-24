from typing import List, Optional

from byteplussdkarkruntime._models import BaseModel

__all__ = ["SequentialImageGenerationOptions", "ImagesResponse"]


class SequentialImageGenerationOptions(BaseModel):
    max_images: Optional[int] = None
    """ Maximum number of images to generate in this request; effective only when the multi-image feature is enabled """


class Usage(BaseModel):
    generated_images: int
    """The number of images generated."""


class Image(BaseModel):
    url: str
    """The URL of the generated image, if any."""

    b64_json: str
    """The Base 64 encoded string of the generated image, if any."""

    size: str
    """The size of the generated image, if any."""


class Error(BaseModel):
    message: str
    """The reason for failed image generation"""

    code: str
    """The error code for failed image generation"""


class ImagesResponse(BaseModel):
    model: str
    """The model used to generated the images."""

    data: List[Image]
    """The generated images."""

    error: Error
    """The error body, if applicable."""

    usage: Usage
    """The usage information for the generation of images."""

    created_at: int
    """The Unix timestamp when the image was generated."""
