from fastmcp import Context
from typing_extensions import Annotated
from pydantic import Field
from files_com_mcp.utils import object_list_to_markdown_table
import files_sdk
import files_sdk.error


async def list_for_folder(
    context: Context,
    path: Annotated[
        str | None, Field(description="Path to operate on.", default=None)
    ],
) -> str:
    """List Folders by Path

    Args:
        path: Path to operate on.
    """

    try:
        options = {
            "api_key": getattr(
                context.request_context.session, "_files_com_api_key", ""
            )
        }
        params = {}
        if path is None:
            return "Missing required parameter: path"
        params["path"] = path

        retval = files_sdk.folder.list_for(path, params, options)
        retval = [item for item in retval.auto_paging_iter()]
        if not retval:
            return "No folders found."

        markdown_list = object_list_to_markdown_table(retval, ["path"])
        return f"Folder Response:\n{markdown_list}"
    except files_sdk.error.NotAuthenticatedError as err:
        return f"Authentication Error: {err}"
    except files_sdk.error.Error as err:
        return f"Files.com Error: {err}"
    except Exception as ex:
        return f"General Exception: {ex}"


async def create_folder(
    context: Context,
    path: Annotated[
        str | None, Field(description="Path to operate on.", default=None)
    ],
) -> str:
    """Create Folder

    Args:
        path: Path to operate on.
    """

    try:
        options = {
            "api_key": getattr(
                context.request_context.session, "_files_com_api_key", ""
            )
        }
        params = {}
        if path is None:
            return "Missing required parameter: path"
        params["path"] = path

        # Smart Default(s)
        params["mkdir_parents"] = True

        retval = files_sdk.folder.create(path, params, options)
        retval = [retval]

        markdown_list = object_list_to_markdown_table(retval, ["path"])
        return f"Folder Response:\n{markdown_list}"
    except files_sdk.error.NotAuthenticatedError as err:
        return f"Authentication Error: {err}"
    except files_sdk.error.Error as err:
        return f"Files.com Error: {err}"
    except Exception as ex:
        return f"General Exception: {ex}"


def register_tools(mcp):
    @mcp.tool(name="List_For_Folder", description="List Folders by Path")
    async def list_for_folder_tool(
        context: Context,
        path: Annotated[
            str | None, Field(description="Path to operate on.", default=None)
        ],
    ) -> str:
        return await list_for_folder(context, path)

    @mcp.tool(name="Create_Folder", description="Create Folder")
    async def create_folder_tool(
        context: Context,
        path: Annotated[
            str | None, Field(description="Path to operate on.", default=None)
        ],
    ) -> str:
        return await create_folder(context, path)
