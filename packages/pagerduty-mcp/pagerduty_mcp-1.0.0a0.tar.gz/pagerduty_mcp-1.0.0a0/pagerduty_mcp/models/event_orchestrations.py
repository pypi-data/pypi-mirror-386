from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, computed_field

from pagerduty_mcp.models.base import DEFAULT_PAGINATION_LIMIT, MAXIMUM_PAGINATION_LIMIT
from pagerduty_mcp.models.references import TeamReference, UserReference


class EventOrchestrationIntegration(BaseModel):
    id: str = Field(description="ID of the Integration.", json_schema_extra={"readOnly": True})
    label: str = Field(description="Name of the Integration.")
    parameters: dict[str, Any] = Field(description="Integration parameters", json_schema_extra={"readOnly": True})


class EventOrchestration(BaseModel):
    id: str = Field(description="ID of the Orchestration.", json_schema_extra={"readOnly": True})
    self: str = Field(
        description="The API show URL at which the object is accessible", json_schema_extra={"readOnly": True}
    )
    name: str = Field(description="Name of the Orchestration.")
    description: str | None = Field(description="A description of this Orchestration's purpose.", default=None)
    team: TeamReference | None = Field(
        description="Reference to the team that owns the Orchestration. If none is specified, only admins have access.",
        default=None,
    )
    integrations: list[EventOrchestrationIntegration] | None = Field(
        description="List of integrations for the orchestration", default=None, json_schema_extra={"readOnly": True}
    )
    routes: int = Field(
        description="Number of different Service Orchestration being routed to", json_schema_extra={"readOnly": True}
    )
    created_at: datetime = Field(
        description="The date the Orchestration was created at.", json_schema_extra={"readOnly": True}
    )
    created_by: UserReference | None = Field(
        description="Reference to the user that has created the Orchestration.",
        json_schema_extra={"readOnly": True},
        default=None,
    )
    updated_at: datetime = Field(
        description="The date the Orchestration was last updated.", json_schema_extra={"readOnly": True}
    )
    updated_by: UserReference | None = Field(
        description="Reference to the user that has updated the Orchestration last.",
        json_schema_extra={"readOnly": True},
        default=None,
    )
    version: str | None = Field(
        description="Version of the Orchestration.", json_schema_extra={"readOnly": True}, default=None
    )

    @computed_field
    @property
    def type(self) -> Literal["event_orchestration"]:
        return "event_orchestration"


class EventOrchestrationQuery(BaseModel):
    limit: int | None = Field(
        ge=1,
        le=MAXIMUM_PAGINATION_LIMIT,
        default=DEFAULT_PAGINATION_LIMIT,
        description="The number of results per page.",
    )
    offset: int | None = Field(ge=0, default=None, description="Offset to start pagination search results.")
    sort_by: (
        Literal["name:asc", "name:desc", "routes:asc", "routes:desc", "created_at:asc", "created_at:desc"] | None
    ) = Field(default="name:asc", description="Used to specify the field you wish to sort the results on.")

    def to_params(self) -> dict[str, Any]:
        params = {}
        if self.limit:
            params["limit"] = self.limit
        if self.offset:
            params["offset"] = self.offset
        if self.sort_by:
            params["sort_by"] = self.sort_by
        return params


# Router-specific models
class EventOrchestrationRuleCondition(BaseModel):
    expression: str = Field(
        description="A PCL condition string",
        json_schema_extra={"example": "event.summary matches part 'my service error'"},
    )


class EventOrchestrationRuleActions(BaseModel):
    route_to: str | None = Field(
        description=(
            "The ID of the target Service for the resulting alert. "
            "You can find the service you want to route to by calling the services endpoint."
        ),
        default=None,
        json_schema_extra={"example": "PSI2I2O"},
    )
    dynamic_route_to: dict[str, Any] | None = Field(
        description=(
            "Use the contents of an event payload to dynamically route an event to the target service. "
            "Available to AIOps customers."
        ),
        default=None,
    )


class EventOrchestrationRule(BaseModel):
    id: str = Field(description="ID of the rule", json_schema_extra={"readOnly": True})
    label: str | None = Field(description="A description of this rule's purpose.", default=None)
    conditions: list[EventOrchestrationRuleCondition] = Field(
        description=(
            "Each of these conditions is evaluated to check if an event matches this rule. "
            "The rule is considered a match if **any** of these conditions match."
        )
    )
    actions: EventOrchestrationRuleActions = Field(
        description=(
            "When an event matches this rule, these are the actions that will be taken "
            "to change the resulting alert and incident."
        )
    )
    disabled: bool | None = Field(
        description="Indicates whether the rule is disabled and would therefore not be evaluated.", default=False
    )


class EventOrchestrationRuleSet(BaseModel):
    id: str = Field(
        description=(
            "The ID of this set of rules. Rules in other sets can route events into this set "
            "using the 'route_to' properties."
        ),
        default="start",
    )
    rules: list[EventOrchestrationRule] = Field(description="List of rules in this set")


class EventOrchestrationCatchAll(BaseModel):
    actions: EventOrchestrationRuleActions = Field(
        description="These are the actions that will be taken to change the resulting alert and incident."
    )


class EventOrchestrationParent(BaseModel):
    id: str = Field(description="ID of the Global Event Orchestration this Router belongs to.")
    type: Literal["event_orchestration_reference"] = Field(
        description="A string that determines the schema of the parent object", json_schema_extra={"readOnly": True}
    )
    self: str = Field(
        description="The API show URL at which the parent object is accessible", json_schema_extra={"readOnly": True}
    )


class EventOrchestrationPath(BaseModel):
    type: Literal["router"] = Field(
        description="Indicates that these are a 'router' type set of rules.", default="router"
    )
    parent: EventOrchestrationParent = Field(json_schema_extra={"readOnly": True})
    self: str | None = Field(
        description="The API show URL at which the object is accessible",
        json_schema_extra={"readOnly": True},
        default=None,
    )
    sets: list[EventOrchestrationRuleSet] = Field(
        description=(
            "The Router contains a single set of rules (the 'start' set). "
            "The Router evaluates Events against these Rules, one at a time, "
            "and routes each Event to a specific Service based on the first rule that matches."
        ),
        max_length=1,
    )
    catch_all: EventOrchestrationCatchAll = Field(
        description=(
            "When none of the rules match an event, the event will be routed according to the catch_all settings."
        )
    )
    created_at: datetime = Field(
        description="The date/time the object was created.", json_schema_extra={"readOnly": True}
    )
    created_by: UserReference | None = Field(
        description="Reference to the user that created the object.", json_schema_extra={"readOnly": True}, default=None
    )
    updated_at: datetime = Field(
        description="The date/time the object was last updated.", json_schema_extra={"readOnly": True}
    )
    updated_by: UserReference | None = Field(
        description="Reference to the user that last updated the object.",
        json_schema_extra={"readOnly": True},
        default=None,
    )
    version: str = Field(description="Version of these Orchestration Rules", json_schema_extra={"readOnly": True})


class EventOrchestrationRouter(BaseModel):
    orchestration_path: EventOrchestrationPath | None = Field(
        description="The orchestration router path configuration", default=None
    )

    @classmethod
    def from_api_response(cls, response_data: dict[str, Any]) -> "EventOrchestrationRouter":
        """Create EventOrchestrationRouter from PagerDuty API response.

        Handles both wrapped and direct response formats:
        - Wrapped: {"orchestration_path": {...}}
        - Direct: {...} (router data directly)
        """
        if "orchestration_path" in response_data:
            # Response is already wrapped
            return cls.model_validate(response_data)

        # Response is direct router data, wrap it
        return cls(orchestration_path=EventOrchestrationPath.model_validate(response_data))


class EventOrchestrationPathUpdateRequest(BaseModel):
    """Orchestration path model for update requests, excluding readonly fields."""

    type: Literal["router"] = Field(
        description="Indicates that these are a 'router' type set of rules.", default="router"
    )
    sets: list[EventOrchestrationRuleSet] = Field(
        description=(
            "The Router contains a single set of rules (the 'start' set). "
            "The Router evaluates Events against these Rules, one at a time, "
            "and routes each Event to a specific Service based on the first rule that matches."
        ),
        max_length=1,
    )
    catch_all: EventOrchestrationCatchAll = Field(
        description=(
            "When none of the rules match an event, the event will be routed according to the catch_all settings."
        )
    )
    # Note: Explicitly exclude readonly fields like created_at, updated_at, version, etc.
    # that cause JSON serialization errors and shouldn't be sent in update requests


class EventOrchestrationRouterUpdateRequest(BaseModel):
    """Request model for updating an event orchestration router configuration."""

    orchestration_path: EventOrchestrationPathUpdateRequest = Field(
        description="The orchestration router path configuration to update"
    )

    @classmethod
    def from_path(cls, path: EventOrchestrationPath) -> "EventOrchestrationRouterUpdateRequest":
        """Create update request from an EventOrchestrationPath, excluding readonly fields."""
        update_path = EventOrchestrationPathUpdateRequest(type=path.type, sets=path.sets, catch_all=path.catch_all)
        return cls(orchestration_path=update_path)


class EventOrchestrationRuleCreateRequest(BaseModel):
    """Request model for creating a new event orchestration rule."""

    label: str | None = Field(description="A description of this rule's purpose.", default=None)
    conditions: list[EventOrchestrationRuleCondition] = Field(
        description=(
            "Each of these conditions is evaluated to check if an event matches this rule. "
            "The rule is considered a match if **any** of these conditions match."
        )
    )
    actions: EventOrchestrationRuleActions = Field(
        description=(
            "When an event matches this rule, these are the actions that will be taken "
            "to change the resulting alert and incident."
        )
    )
    disabled: bool | None = Field(
        description="Indicates whether the rule is disabled and would therefore not be evaluated.", default=False
    )
