import httpx
from arcade_tdk import ToolContext
from arcade_tdk.errors import ToolExecutionError

from arcade_linkedin.tools.constants import LINKEDIN_BASE_URL


async def _send_linkedin_request(
    context: ToolContext,
    method: str,
    endpoint: str,
    params: dict | None = None,
    json_data: dict | None = None,
) -> httpx.Response:
    """
    Send an asynchronous request to the LinkedIn API.

    Args:
        context: The tool context containing the authorization token.
        method: The HTTP method (GET, POST, PUT, DELETE, etc.).
        endpoint: The API endpoint path (e.g., "/ugcPosts").
        params: Query parameters to include in the request.
        json_data: JSON data to include in the request body.

    Returns:
        The response object from the API request.

    Raises:
        ToolExecutionError: If the request fails for any reason.
    """
    url = f"{LINKEDIN_BASE_URL}{endpoint}"
    token = (
        context.authorization.token if context.authorization and context.authorization.token else ""
    )
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method, url, headers=headers, params=params, json=json_data
            )
            response.raise_for_status()
        except httpx.RequestError as e:
            raise ToolExecutionError(f"Failed to send request to LinkedIn API: {e}")

    return response


def _handle_linkedin_api_error(response: httpx.Response) -> None:
    """
    Handle errors from the LinkedIn API by mapping common status codes to ToolExecutionErrors.

    Args:
        response: The response object from the API request.

    Raises:
        ToolExecutionError: If the response contains an error status code.
    """
    status_code_map = {
        401: ToolExecutionError("Unauthorized: Invalid or expired token"),
        403: ToolExecutionError("Forbidden: User does not have Spotify Premium"),
        429: ToolExecutionError("Too Many Requests: Rate limit exceeded"),
    }

    if response.status_code in status_code_map:
        raise status_code_map[response.status_code]
    elif response.status_code >= 400:
        raise ToolExecutionError(f"Error: {response.status_code} - {response.text}")
