from pathlib import PurePath
from typing import Annotated, Literal, Optional, Union

from pydantic import AnyUrl, BaseModel, Field, SecretStr


class BaseBackendOptions(BaseModel):
    """Common options for all declarative document backends."""

    enable_remote_fetch: bool = Field(
        False, description="Enable remote resource fetching."
    )
    enable_local_fetch: bool = Field(
        False, description="Enable local resource fetching."
    )


class DeclarativeBackendOptions(BaseBackendOptions):
    """Default backend options for a declarative document backend."""

    kind: Literal["declarative"] = Field("declarative", exclude=True, repr=False)


class HTMLBackendOptions(BaseBackendOptions):
    """Options specific to the HTML backend.

    This class can be extended to include options specific to HTML processing.
    """

    kind: Literal["html"] = Field("html", exclude=True, repr=False)
    fetch_images: bool = Field(
        False,
        description=(
            "Whether the backend should access remote or local resources to parse "
            "images in an HTML document."
        ),
    )
    source_uri: Optional[Union[AnyUrl, PurePath]] = Field(
        None,
        description=(
            "The URI that originates the HTML document. If provided, the backend "
            "will use it to resolve relative paths in the HTML document."
        ),
    )


class MarkdownBackendOptions(BaseBackendOptions):
    """Options specific to the Markdown backend."""

    kind: Literal["md"] = Field("md", exclude=True, repr=False)
    fetch_images: bool = Field(
        False,
        description=(
            "Whether the backend should access remote or local resources to parse "
            "images in the markdown document."
        ),
    )
    source_uri: Optional[Union[AnyUrl, PurePath]] = Field(
        None,
        description=(
            "The URI that originates the markdown document. If provided, the backend "
            "will use it to resolve relative paths in the markdown document."
        ),
    )


class PdfBackendOptions(BaseBackendOptions):
    """Backend options for pdf document backends."""

    kind: Literal["pdf"] = Field("pdf", exclude=True, repr=False)
    password: Optional[SecretStr] = None


BackendOptions = Annotated[
    Union[
        DeclarativeBackendOptions,
        HTMLBackendOptions,
        MarkdownBackendOptions,
        PdfBackendOptions,
    ],
    Field(discriminator="kind"),
]
