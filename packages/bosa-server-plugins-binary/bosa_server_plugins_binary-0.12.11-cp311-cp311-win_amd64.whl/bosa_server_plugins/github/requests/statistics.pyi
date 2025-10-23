from bosa_server_plugins.github.gql.contributions import FragmentTypes as FragmentTypes
from bosa_server_plugins.handler import BaseRequestModel as BaseRequestModel

class StatisticsRequest(BaseRequestModel):
    """GitHub Statistics Request Model."""
    organization: str | None
    username: str | list[str] | None
    since: str | None
    until: str | None
    statistics: list[FragmentTypes] | None
    exclude_breakdowns: bool | None
    exclude_detailed_breakdown: bool | None
