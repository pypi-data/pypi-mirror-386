from bosa_server_plugins.github.constant import DEFAULT_ITEM_PER_PAGE as DEFAULT_ITEM_PER_PAGE, GITHUB_DATE_FORMAT as GITHUB_DATE_FORMAT, MAXIMUM_ITEM_PER_PAGE as MAXIMUM_ITEM_PER_PAGE, MINIMUM_ITEM_PER_PAGE as MINIMUM_ITEM_PER_PAGE
from bosa_server_plugins.github.gql.common import GQLDirection as GQLDirection
from bosa_server_plugins.github.gql.issue import GQLIssueOrderBy as GQLIssueOrderBy
from bosa_server_plugins.github.gql.pull_request import GQLPullRequestState as GQLPullRequestState
from bosa_server_plugins.github.helper.model.common import Direction as Direction
from bosa_server_plugins.github.requests.repositories import BasicRepositoryRequest as BasicRepositoryRequest
from bosa_server_plugins.github.tasks.search_pull_requests_task import PrOrderBy as PrOrderBy, PrState as PrState, PullRequestFields as PullRequestFields
from bosa_server_plugins.handler.model import BaseRequestModel as BaseRequestModel

class SearchPullRequestsRequest(BaseRequestModel):
    """Search Pull Requests Request."""
    repositories: list[str] | None
    merged: bool | None
    draft: bool | None
    author: str | None
    labels: list[str] | None
    state: PrState | None
    sort: PrOrderBy | None
    direction: Direction | None
    fields: list[PullRequestFields] | None
    summarize: bool | None
    since: str | None
    until: str | None
    callback_urls: list[str] | None
    def validate_dates(self):
        """Validate date format."""

class GetPullRequestRequest(BasicRepositoryRequest):
    """Request model for getting a single pull request."""
    pull_number: int

class GQLListPullRequestsRequest(BasicRepositoryRequest):
    """Request model for listing pull requests."""
    order_by: GQLIssueOrderBy | None
    direction: GQLDirection | None
    per_page: int | None
    states: list[GQLPullRequestState] | None
    labels: list[str] | None
    head: str | None
    base: str | None
    cursor: str | None
    from_last: bool | None
