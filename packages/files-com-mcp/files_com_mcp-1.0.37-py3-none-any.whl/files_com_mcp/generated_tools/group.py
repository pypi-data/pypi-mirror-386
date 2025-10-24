from fastmcp import Context
from typing_extensions import Annotated
from pydantic import Field
from files_com_mcp.utils import object_list_to_markdown_table
import files_sdk
import files_sdk.error


async def list_group(context: Context) -> str:
    """List Groups"""

    try:
        options = {
            "api_key": getattr(
                context.request_context.session, "_files_com_api_key", ""
            )
        }
        params = {}

        retval = files_sdk.group.list(params, options)
        retval = [item for item in retval.auto_paging_iter()]
        if not retval:
            return "No groups found."

        markdown_list = object_list_to_markdown_table(
            retval, ["id", "name", "notes", "user_ids", "admin_ids"]
        )
        return f"Group Response:\n{markdown_list}"
    except files_sdk.error.NotAuthenticatedError as err:
        return f"Authentication Error: {err}"
    except files_sdk.error.Error as err:
        return f"Files.com Error: {err}"
    except Exception as ex:
        return f"General Exception: {ex}"


async def find_group(
    context: Context,
    id: Annotated[int | None, Field(description="Group ID.", default=None)],
) -> str:
    """Show Group

    Args:
        id: Group ID.
    """

    try:
        options = {
            "api_key": getattr(
                context.request_context.session, "_files_com_api_key", ""
            )
        }
        params = {}
        if id is None:
            return "Missing required parameter: id"
        params["id"] = id

        retval = files_sdk.group.find(id, params, options)
        retval = [retval]

        markdown_list = object_list_to_markdown_table(
            retval, ["id", "name", "notes", "user_ids", "admin_ids"]
        )
        return f"Group Response:\n{markdown_list}"
    except files_sdk.error.NotAuthenticatedError as err:
        return f"Authentication Error: {err}"
    except files_sdk.error.Error as err:
        return f"Files.com Error: {err}"
    except Exception as ex:
        return f"General Exception: {ex}"


async def create_group(
    context: Context,
    name: Annotated[
        str | None, Field(description="Group name.", default=None)
    ],
    notes: Annotated[
        str | None, Field(description="Group notes.", default=None)
    ],
    user_ids: Annotated[
        str | None,
        Field(
            description="A list of user ids. If sent as a string, should be comma-delimited.",
            default=None,
        ),
    ],
    admin_ids: Annotated[
        str | None,
        Field(
            description="A list of group admin user ids. If sent as a string, should be comma-delimited.",
            default=None,
        ),
    ],
) -> str:
    """Create Group

    Args:
        name: Group name.
        notes: Group notes.
        user_ids: A list of user ids. If sent as a string, should be comma-delimited.
        admin_ids: A list of group admin user ids. If sent as a string, should be comma-delimited.
    """

    try:
        options = {
            "api_key": getattr(
                context.request_context.session, "_files_com_api_key", ""
            )
        }
        params = {}
        if name is None:
            return "Missing required parameter: name"
        params["name"] = name
        if notes is not None:
            params["notes"] = notes
        if user_ids is not None:
            params["user_ids"] = user_ids
        if admin_ids is not None:
            params["admin_ids"] = admin_ids

        retval = files_sdk.group.create(params, options)
        retval = [retval]

        markdown_list = object_list_to_markdown_table(
            retval, ["id", "name", "notes", "user_ids", "admin_ids"]
        )
        return f"Group Response:\n{markdown_list}"
    except files_sdk.error.NotAuthenticatedError as err:
        return f"Authentication Error: {err}"
    except files_sdk.error.Error as err:
        return f"Files.com Error: {err}"
    except Exception as ex:
        return f"General Exception: {ex}"


async def update_group(
    context: Context,
    id: Annotated[int | None, Field(description="Group ID.", default=None)],
    notes: Annotated[
        str | None, Field(description="Group notes.", default=None)
    ],
    user_ids: Annotated[
        str | None,
        Field(
            description="A list of user ids. If sent as a string, should be comma-delimited.",
            default=None,
        ),
    ],
    admin_ids: Annotated[
        str | None,
        Field(
            description="A list of group admin user ids. If sent as a string, should be comma-delimited.",
            default=None,
        ),
    ],
    name: Annotated[
        str | None, Field(description="Group name.", default=None)
    ],
) -> str:
    """Update Group

    Args:
        id: Group ID.
        notes: Group notes.
        user_ids: A list of user ids. If sent as a string, should be comma-delimited.
        admin_ids: A list of group admin user ids. If sent as a string, should be comma-delimited.
        name: Group name.
    """

    try:
        options = {
            "api_key": getattr(
                context.request_context.session, "_files_com_api_key", ""
            )
        }
        params = {}
        if id is None:
            return "Missing required parameter: id"
        params["id"] = id
        if notes is not None:
            params["notes"] = notes
        if user_ids is not None:
            params["user_ids"] = user_ids
        if admin_ids is not None:
            params["admin_ids"] = admin_ids
        if name is not None:
            params["name"] = name

        retval = files_sdk.group.update(id, params, options)
        retval = [retval]

        markdown_list = object_list_to_markdown_table(
            retval, ["id", "name", "notes", "user_ids", "admin_ids"]
        )
        return f"Group Response:\n{markdown_list}"
    except files_sdk.error.NotAuthenticatedError as err:
        return f"Authentication Error: {err}"
    except files_sdk.error.Error as err:
        return f"Files.com Error: {err}"
    except Exception as ex:
        return f"General Exception: {ex}"


async def delete_group(
    context: Context,
    id: Annotated[int | None, Field(description="Group ID.", default=None)],
) -> str:
    """Delete Group

    Args:
        id: Group ID.
    """

    try:
        options = {
            "api_key": getattr(
                context.request_context.session, "_files_com_api_key", ""
            )
        }
        params = {}
        if id is None:
            return "Missing required parameter: id"
        params["id"] = id

        retval = files_sdk.group.delete(id, params, options)
        retval = [retval]

        markdown_list = object_list_to_markdown_table(
            retval, ["id", "name", "notes", "user_ids", "admin_ids"]
        )
        return f"Group Response:\n{markdown_list}"
    except files_sdk.error.NotAuthenticatedError as err:
        return f"Authentication Error: {err}"
    except files_sdk.error.Error as err:
        return f"Files.com Error: {err}"
    except Exception as ex:
        return f"General Exception: {ex}"


def register_tools(mcp):
    @mcp.tool(name="List_Group", description="List Groups")
    async def list_group_tool(context: Context) -> str:
        return await list_group(context)

    @mcp.tool(name="Find_Group", description="Show Group")
    async def find_group_tool(
        context: Context,
        id: Annotated[
            int | None, Field(description="Group ID.", default=None)
        ],
    ) -> str:
        return await find_group(context, id)

    @mcp.tool(name="Create_Group", description="Create Group")
    async def create_group_tool(
        context: Context,
        name: Annotated[
            str | None, Field(description="Group name.", default=None)
        ],
        notes: Annotated[
            str | None, Field(description="Group notes.", default=None)
        ],
        user_ids: Annotated[
            str | None,
            Field(
                description="A list of user ids. If sent as a string, should be comma-delimited.",
                default=None,
            ),
        ],
        admin_ids: Annotated[
            str | None,
            Field(
                description="A list of group admin user ids. If sent as a string, should be comma-delimited.",
                default=None,
            ),
        ],
    ) -> str:
        return await create_group(context, name, notes, user_ids, admin_ids)

    @mcp.tool(name="Update_Group", description="Update Group")
    async def update_group_tool(
        context: Context,
        id: Annotated[
            int | None, Field(description="Group ID.", default=None)
        ],
        notes: Annotated[
            str | None, Field(description="Group notes.", default=None)
        ],
        user_ids: Annotated[
            str | None,
            Field(
                description="A list of user ids. If sent as a string, should be comma-delimited.",
                default=None,
            ),
        ],
        admin_ids: Annotated[
            str | None,
            Field(
                description="A list of group admin user ids. If sent as a string, should be comma-delimited.",
                default=None,
            ),
        ],
        name: Annotated[
            str | None, Field(description="Group name.", default=None)
        ],
    ) -> str:
        return await update_group(
            context, id, notes, user_ids, admin_ids, name
        )

    @mcp.tool(name="Delete_Group", description="Delete Group")
    async def delete_group_tool(
        context: Context,
        id: Annotated[
            int | None, Field(description="Group ID.", default=None)
        ],
    ) -> str:
        return await delete_group(context, id)
