from fastmcp import Context
from typing_extensions import Annotated
from pydantic import Field
from files_com_mcp.utils import object_list_to_markdown_table
import files_sdk
import files_sdk.error


async def list_bundle_notification(context: Context) -> str:
    """List Share Link Notifications"""

    try:
        options = {
            "api_key": getattr(
                context.request_context.session, "_files_com_api_key", ""
            )
        }
        params = {}

        retval = files_sdk.bundle_notification.list(params, options)
        retval = [item for item in retval.auto_paging_iter()]
        if not retval:
            return "No bundlenotifications found."

        markdown_list = object_list_to_markdown_table(
            retval,
            [
                "id",
                "bundle_id",
                "notify_user_id",
                "notify_on_registration",
                "notify_on_upload",
            ],
        )
        return f"BundleNotification Response:\n{markdown_list}"
    except files_sdk.error.NotAuthenticatedError as err:
        return f"Authentication Error: {err}"
    except files_sdk.error.Error as err:
        return f"Files.com Error: {err}"
    except Exception as ex:
        return f"General Exception: {ex}"


async def find_bundle_notification(
    context: Context,
    id: Annotated[
        int | None, Field(description="Bundle Notification ID.", default=None)
    ],
) -> str:
    """Show Share Link Notification

    Args:
        id: Bundle Notification ID.
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

        retval = files_sdk.bundle_notification.find(id, params, options)
        retval = [retval]

        markdown_list = object_list_to_markdown_table(
            retval,
            [
                "id",
                "bundle_id",
                "notify_user_id",
                "notify_on_registration",
                "notify_on_upload",
            ],
        )
        return f"BundleNotification Response:\n{markdown_list}"
    except files_sdk.error.NotAuthenticatedError as err:
        return f"Authentication Error: {err}"
    except files_sdk.error.Error as err:
        return f"Files.com Error: {err}"
    except Exception as ex:
        return f"General Exception: {ex}"


async def create_bundle_notification(
    context: Context,
    bundle_id: Annotated[
        int | None, Field(description="Bundle ID to notify on", default=None)
    ],
    notify_user_id: Annotated[
        int | None,
        Field(description="The id of the user to notify.", default=None),
    ],
) -> str:
    """Create Share Link Notification

    Args:
        bundle_id: Bundle ID to notify on
        notify_user_id: The id of the user to notify.
    """

    try:
        options = {
            "api_key": getattr(
                context.request_context.session, "_files_com_api_key", ""
            )
        }
        params = {}
        if bundle_id is None:
            return "Missing required parameter: bundle_id"
        params["bundle_id"] = bundle_id
        if notify_user_id is not None:
            params["notify_user_id"] = notify_user_id

        # Smart Default(s)
        params["notify_on_registration"] = True

        # Smart Default(s)
        params["notify_on_upload"] = True

        retval = files_sdk.bundle_notification.create(params, options)
        retval = [retval]

        markdown_list = object_list_to_markdown_table(
            retval,
            [
                "id",
                "bundle_id",
                "notify_user_id",
                "notify_on_registration",
                "notify_on_upload",
            ],
        )
        return f"BundleNotification Response:\n{markdown_list}"
    except files_sdk.error.NotAuthenticatedError as err:
        return f"Authentication Error: {err}"
    except files_sdk.error.Error as err:
        return f"Files.com Error: {err}"
    except Exception as ex:
        return f"General Exception: {ex}"


async def update_bundle_notification(
    context: Context,
    id: Annotated[
        int | None, Field(description="Bundle Notification ID.", default=None)
    ],
    notify_on_registration: Annotated[
        bool | None,
        Field(
            description="Triggers bundle notification when a registration action occurs for it.",
            default=None,
        ),
    ],
    notify_on_upload: Annotated[
        bool | None,
        Field(
            description="Triggers bundle notification when a upload action occurs for it.",
            default=None,
        ),
    ],
) -> str:
    """Update Share Link Notification

    Args:
        id: Bundle Notification ID.
        notify_on_registration: Triggers bundle notification when a registration action occurs for it.
        notify_on_upload: Triggers bundle notification when a upload action occurs for it.
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
        if notify_on_registration is not None:
            params["notify_on_registration"] = notify_on_registration
        if notify_on_upload is not None:
            params["notify_on_upload"] = notify_on_upload

        retval = files_sdk.bundle_notification.update(id, params, options)
        retval = [retval]

        markdown_list = object_list_to_markdown_table(
            retval,
            [
                "id",
                "bundle_id",
                "notify_user_id",
                "notify_on_registration",
                "notify_on_upload",
            ],
        )
        return f"BundleNotification Response:\n{markdown_list}"
    except files_sdk.error.NotAuthenticatedError as err:
        return f"Authentication Error: {err}"
    except files_sdk.error.Error as err:
        return f"Files.com Error: {err}"
    except Exception as ex:
        return f"General Exception: {ex}"


async def delete_bundle_notification(
    context: Context,
    id: Annotated[
        int | None, Field(description="Bundle Notification ID.", default=None)
    ],
) -> str:
    """Delete Share Link Notification

    Args:
        id: Bundle Notification ID.
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

        retval = files_sdk.bundle_notification.delete(id, params, options)
        retval = [retval]

        markdown_list = object_list_to_markdown_table(
            retval,
            [
                "id",
                "bundle_id",
                "notify_user_id",
                "notify_on_registration",
                "notify_on_upload",
            ],
        )
        return f"BundleNotification Response:\n{markdown_list}"
    except files_sdk.error.NotAuthenticatedError as err:
        return f"Authentication Error: {err}"
    except files_sdk.error.Error as err:
        return f"Files.com Error: {err}"
    except Exception as ex:
        return f"General Exception: {ex}"


def register_tools(mcp):
    @mcp.tool(
        name="List_Bundle_Notification",
        description="List Share Link Notifications",
    )
    async def list_bundle_notification_tool(context: Context) -> str:
        return await list_bundle_notification(context)

    @mcp.tool(
        name="Find_Bundle_Notification",
        description="Show Share Link Notification",
    )
    async def find_bundle_notification_tool(
        context: Context,
        id: Annotated[
            int | None,
            Field(description="Bundle Notification ID.", default=None),
        ],
    ) -> str:
        return await find_bundle_notification(context, id)

    @mcp.tool(
        name="Create_Bundle_Notification",
        description="Create Share Link Notification",
    )
    async def create_bundle_notification_tool(
        context: Context,
        bundle_id: Annotated[
            int | None,
            Field(description="Bundle ID to notify on", default=None),
        ],
        notify_user_id: Annotated[
            int | None,
            Field(description="The id of the user to notify.", default=None),
        ],
    ) -> str:
        return await create_bundle_notification(
            context, bundle_id, notify_user_id
        )

    @mcp.tool(
        name="Update_Bundle_Notification",
        description="Update Share Link Notification",
    )
    async def update_bundle_notification_tool(
        context: Context,
        id: Annotated[
            int | None,
            Field(description="Bundle Notification ID.", default=None),
        ],
        notify_on_registration: Annotated[
            bool | None,
            Field(
                description="Triggers bundle notification when a registration action occurs for it.",
                default=None,
            ),
        ],
        notify_on_upload: Annotated[
            bool | None,
            Field(
                description="Triggers bundle notification when a upload action occurs for it.",
                default=None,
            ),
        ],
    ) -> str:
        return await update_bundle_notification(
            context, id, notify_on_registration, notify_on_upload
        )

    @mcp.tool(
        name="Delete_Bundle_Notification",
        description="Delete Share Link Notification",
    )
    async def delete_bundle_notification_tool(
        context: Context,
        id: Annotated[
            int | None,
            Field(description="Bundle Notification ID.", default=None),
        ],
    ) -> str:
        return await delete_bundle_notification(context, id)
