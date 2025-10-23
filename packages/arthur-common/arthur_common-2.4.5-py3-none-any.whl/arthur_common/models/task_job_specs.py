from typing import Literal, Optional, Self
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from arthur_common.models.enums import TaskType
from arthur_common.models.request_schemas import NewMetricRequest, NewRuleRequest

onboarding_id_desc = "An identifier to assign to the created model to make it easy to retrieve. Used by the UI during the GenAI model creation flow."


class CreateModelTaskJobSpec(BaseModel):
    job_type: Literal["create_model_task"] = "create_model_task"
    connector_id: UUID = Field(
        description="The id of the engine internal connector to use to create the task.",
    )
    task_name: str = Field(description="The name of the task.")
    onboarding_identifier: Optional[str] = Field(
        default=None,
        description=onboarding_id_desc,
    )
    initial_rules: list[NewRuleRequest] = Field(
        description="The initial rules to apply to the created model.",
    )
    task_type: TaskType = Field(
        default=TaskType.TRADITIONAL,
        description="The type of task to create.",
    )
    initial_metrics: list[NewMetricRequest] = Field(
        description="The initial metrics to apply to agentic tasks.",
    )

    @model_validator(mode="after")
    def initial_metric_required(self) -> Self:
        if self.task_type == TaskType.TRADITIONAL:
            if not len(self.initial_metrics) == 0:
                raise ValueError("No initial_metrics when task_type is TRADITIONAL")
        return self


class CreateModelLinkTaskJobSpec(BaseModel):
    job_type: Literal["link_model_task"] = "link_model_task"
    task_id: UUID = Field(
        description="The id of the Shield task to link when creating the new model.",
    )
    connector_id: UUID = Field(
        description="The id of the engine internal connector to use to link the task.",
    )
    onboarding_identifier: Optional[str] = Field(
        default=None,
        description=onboarding_id_desc,
    )


class UpdateModelTaskRulesJobSpec(BaseModel):
    job_type: Literal["update_model_task_rules"] = "update_model_task_rules"
    scope_model_id: UUID = Field(
        description="The id of the model to update the task rules.",
    )
    rules_to_enable: list[UUID] = Field(
        default_factory=list,
        description="The list of rule IDs to enable on the task.",
    )
    rules_to_disable: list[UUID] = Field(
        default_factory=list,
        description="The list of rule IDs to disable on the task.",
    )
    rules_to_archive: list[UUID] = Field(
        default_factory=list,
        description="The list of rule IDs to archive on the task.",
    )
    rules_to_add: list[NewRuleRequest] = Field(
        default_factory=list,
        description="The new rules to add to the task.",
    )


class DeleteModelTaskJobSpec(BaseModel):
    job_type: Literal["delete_model_task"] = "delete_model_task"
    scope_model_id: UUID = Field(description="The id of the model to delete.")


class FetchModelTaskJobSpec(BaseModel):
    job_type: Literal["fetch_model_task"] = "fetch_model_task"
    scope_model_id: UUID = Field(
        description="The id of the model to fetch its corresponding task.",
    )


class RegenerateTaskValidationKeyJobSpec(BaseModel):
    job_type: Literal["regenerate_validation_key"] = "regenerate_validation_key"
    scope_model_id: UUID = Field(
        description="The ID of the model to regenerate the validation key for.",
    )
