from bosa_server_plugins.github.constant import DEFAULT_ITEM_PER_PAGE as DEFAULT_ITEM_PER_PAGE, DEFAULT_OWNER as DEFAULT_OWNER, DEFAULT_PAGE as DEFAULT_PAGE, MAXIMUM_ITEM_PER_PAGE as MAXIMUM_ITEM_PER_PAGE, MINIMUM_ITEM_PER_PAGE as MINIMUM_ITEM_PER_PAGE
from datetime import datetime
from github import Github as Github
from github.Repository import Repository as Repository
from typing import Any

def count_items(items: list[dict[str, Any]], key: str = 'author') -> dict[str, dict[str, Any]]:
    """Generic method to count items per user.

    Args:
        items (List[Dict[str, Any]]): List of items to count
        key (str, optional): Key to use for identification. Can be a single value or a list.

    Returns:
        Dict[str, Dict[str, Any]]: Dictionary of counts and details
    """
def resolve_repositories(repositories: list[str] | None = None) -> list[str]:
    """Resolve repository names to their full GitHub repository names.

    Args:
        repositories (Optional[List[str]]): List of repository names or aliases to resolve.
            If None, all valid repositories in GDP-ADMIN organization will be used.

    Returns:
        List[str]: List of fully qualified repository names.
    """
def get_repository_objects(client: Github, repository_names: list[str] | None = None) -> list[Repository]:
    """Get repository objects from names.

    Args:
        client: GitHub client object
        repository_names: List of repository names to get. If None, uses all repositories
            in GDP-ADMIN organization.

    Returns:
        List of Repository objects.
    """
def convert_to_datetime(date_str: str | None) -> datetime | None:
    """Convert ISO 8601 date string to datetime object.

    Args:
        date_str: ISO 8601 date string

    Returns:
        datetime object or None
    """
def parse_date(date_value, default_value=None):
    """Parse a date string into a datetime object with flexible format handling.

    This function handles multiple date formats:
    - ISO format with Z timezone: 2024-11-04T00:00:00Z
    - ISO format without explicit timezone: 2024-11-04T00:00:00
    - Space-separated format: 2024-11-04 00:00:00
    - Date-only format: 2024-11-04

    Args:
        date_value: The date string or datetime object to parse
        default_value: Default value to return if parsing fails (default: None)

    Returns:
        datetime object or default_value if parsing fails
    """
def get_sanitized_per_page(per_page: int | None = None) -> int:
    """Get the sanitized number of items per page.

    If per_page is not provided or 0, return the default value.
    If per_page is greater than the maximum value, return the maximum value.
    If per_page is less than the minimum value, return the minimum value.

    Args:
        per_page: The number of items per page.

    Returns:
        int: The default number of items per page.
    """
def get_sanitized_page(page: int | None = None) -> int:
    """Get the sanitized page number.

    If page is not provided, return the default value.
    If page is less than 1, return 1.
    """
