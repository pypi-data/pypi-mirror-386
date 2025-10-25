from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, computed_field

from pagerduty_mcp.models.base import DEFAULT_PAGINATION_LIMIT, MAXIMUM_PAGINATION_LIMIT
from pagerduty_mcp.models.references import TeamReference, UserReference


class ScheduleLayerUser(BaseModel):
    user: UserReference = Field(description="The reference to the user in this layer")


class ScheduleLayer(BaseModel):
    id: str = Field(description="The ID of the schedule layer")
    start: datetime = Field(description="The start time of this layer")
    end: datetime | None = Field(
        default=None,
        description="The end time of this layer. If null, the layer does not end",
    )
    name: str = Field(description="The name of the schedule layer")
    rotation_virtual_start: datetime = Field(
        description="The effective start time of the layer. This can be before the start time of the schedule"
    )
    rotation_turn_length_seconds: int = Field(description="The duration of each on-call shift in seconds")
    users: list[ScheduleLayerUser] = Field(
        description="The ordered list of users on this layer. The position of the user on the list"
        " determines their order in the layer"
    )
    restrictions: list[dict[str, Any]] | None = Field(
        default=None,
        description="An array of restrictions for the layer. A restriction is a limit on which"
        " period of the day or week the schedule layer can accept assignments",
    )


class Schedule(BaseModel):
    id: str | None = Field(description="The ID of the schedule", default=None)
    summary: str = Field(
        description="A short-form, server-generated string that provides succinct information about the schedule"
    )
    name: str = Field(description="The name of the schedule")
    description: str | None = Field(default=None, description="The description of the schedule")
    time_zone: str = Field(description="The time zone of the schedule")
    self_url: str | None = Field(default=None, description="The API URL at which this schedule is accessible")
    html_url: str | None = Field(
        default=None,
        description="The URL at which this schedule is accessible in the PagerDuty UI",
    )
    created_at: datetime | None = Field(default=None, description="The date/time when this schedule was created")
    updated_at: datetime | None = Field(default=None, description="The date/time when this schedule was last updated")
    users: list[UserReference] | None = Field(default=None, description="The users associated with this schedule")
    teams: list[TeamReference] | None = Field(default=None, description="The teams associated with this schedule")
    schedule_layers: list[ScheduleLayer] | None = Field(
        default=None, description="A list of schedule layers for this schedule"
    )

    @computed_field
    @property
    def type(self) -> Literal["schedule"]:
        return "schedule"


class ScheduleQuery(BaseModel):
    query: str | None = Field(description="Filter schedules by name or description", default=None)
    team_ids: list[str] | None = Field(description="Filter schedules by team IDs", default=None)
    user_ids: list[str] | None = Field(description="Filter schedules by user IDs", default=None)
    include: list[str] | None = Field(
        description="Include additional details in response, such as 'schedule_layers'",
        default=None,
    )
    limit: int | None = Field(
        ge=1,
        le=MAXIMUM_PAGINATION_LIMIT,
        default=DEFAULT_PAGINATION_LIMIT,
        description="Pagination limit",
    )

    def to_params(self) -> dict[str, Any]:
        params = {}
        if self.query:
            params["query"] = self.query
        if self.team_ids:
            params["team_ids[]"] = self.team_ids
        if self.user_ids:
            params["user_ids[]"] = self.user_ids
        if self.include:
            params["include[]"] = self.include
        if self.limit:
            params["limit"] = self.limit
        return params


class Override(BaseModel):
    start: datetime = Field(description="The start time of the override")
    end: datetime = Field(description="The end time of the override")
    user: UserReference = Field(description="The user for the override")


class ScheduleOverrideCreate(BaseModel):
    overrides: list[Override] = Field(description="The list of overrides to create for the schedule")
