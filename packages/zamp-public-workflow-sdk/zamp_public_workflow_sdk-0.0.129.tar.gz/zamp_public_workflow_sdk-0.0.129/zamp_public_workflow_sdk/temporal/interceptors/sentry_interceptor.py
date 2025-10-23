"""
Configurable Sentry interceptor for Temporal workflows and activities.

This interceptor captures workflow and activity failures and reports them to Sentry.
"""

from typing import Any, Callable

from temporalio import workflow
from temporalio.worker import (
    ActivityInboundInterceptor,
    ActivityOutboundInterceptor,
    ExecuteActivityInput,
    ExecuteWorkflowInput,
    Interceptor,
    StartChildWorkflowInput,
    WorkflowInboundInterceptor,
    WorkflowInterceptorClassInput,
    WorkflowOutboundInterceptor,
)

with workflow.unsafe.imports_passed_through():
    from sentry_sdk import capture_exception, init, push_scope


def extract_context_from_contextvars(
    context_extraction_fn: Callable | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Extract relevant context information from contextvars.

    Args:
        context_extraction_fn: Optional function to extract context from contextvars.
                              If not provided, no context is extracted.

    Returns:
        Tuple of (tags_dict, context_dict) where:
        - tags_dict: Key identifiers for filtering/searching
        - context_dict: Detailed information for debugging
    """
    tags = {}
    context = {}

    # If no context extraction function is provided, return empty dicts
    if not context_extraction_fn:
        return tags, context

    try:
        # Use provided function to extract context
        context_vars = context_extraction_fn()

        # Extract specific fields
        user_id = context_vars.get("user_id")
        organization_id = context_vars.get("organization_id")
        process_id = context_vars.get("process_id")
        pantheon_trace_id = context_vars.get("pantheon_trace_id")

        # Add to tags and context if they exist
        if user_id:
            tags["user_id"] = user_id
            context["user_id"] = user_id

        if organization_id:
            tags["organization_id"] = organization_id
            context["organization_id"] = organization_id

        if process_id:
            tags["process_id"] = process_id
            context["process_id"] = process_id

        if pantheon_trace_id:
            tags["pantheon_trace_id"] = pantheon_trace_id
            context["pantheon_trace_id"] = pantheon_trace_id

    except Exception:
        # If contextvars access fails, return empty dicts
        pass

    return tags, context


class SentryActivityInboundInterceptor(ActivityInboundInterceptor):
    """Activity inbound interceptor that reports failures to Sentry."""

    def __init__(
        self,
        next_interceptor: ActivityInboundInterceptor,
        logger: Any,
        context_extraction_fn: Callable | None = None,
        additional_context_fn: Callable | None = None,
    ):
        self.next = next_interceptor
        self.logger = logger
        self.context_extraction_fn = context_extraction_fn
        self.additional_context_fn = additional_context_fn

    async def execute_activity(self, input: ExecuteActivityInput) -> Any:
        """Execute activity and report failures to Sentry."""
        try:
            return await self.next.execute_activity(input)
        except Exception as e:
            with push_scope() as scope:
                activity_name = input.fn.__name__
                # Set activity-specific tags
                scope.set_tag("activity.direction", "inbound")
                scope.set_tag("activity_type", activity_name)
                scope.set_tag("failure_level", "activity")

                # Set fingerprint for better Sentry grouping
                scope.fingerprint = [
                    f"activity_{activity_name}",
                    str(type(e).__name__),
                    str(e),
                    "activity_failure",
                ]

                # Extract context using provided function
                extracted_tags, extracted_context = extract_context_from_contextvars(self.context_extraction_fn)

                # Set tags for filtering/searching
                for key, value in extracted_tags.items():
                    scope.set_tag(key, value)

                # Add detailed context
                context = {
                    "name": activity_name,
                    "headers": dict(input.headers),
                    "type": "activity",
                    "args": str(input.args),
                    "direction": "inbound",
                }
                context.update(extracted_context)

                # Add any additional context if provided
                if self.additional_context_fn:
                    additional_context = self.additional_context_fn(input)
                    context.update(additional_context)

                scope.set_context("activity_details", context)
                try:
                    capture_exception(e)
                except Exception as e:
                    self.logger.error(
                        "Sentry captured failed",
                        activity_name=activity_name,
                        error=str(e),
                    )
            raise


class SentryActivityOutboundInterceptor(ActivityOutboundInterceptor):
    """Activity outbound interceptor that reports failures to Sentry."""

    def __init__(
        self,
        next_interceptor: ActivityOutboundInterceptor,
        logger: Any,
        context_extraction_fn: Callable | None = None,
        additional_context_fn: Callable | None = None,
    ):
        self.next = next_interceptor
        self.logger = logger
        self.context_extraction_fn = context_extraction_fn
        self.additional_context_fn = additional_context_fn

    async def execute_activity(self, input: ExecuteActivityInput) -> Any:
        """Execute activity and report failures to Sentry."""
        try:
            return await self.next.execute_activity(input)
        except Exception as e:
            with push_scope() as scope:
                activity_name = input.fn.__name__
                # Set activity-specific tags
                scope.set_tag("activity.direction", "outbound")
                scope.set_tag("activity_type", activity_name)
                scope.set_tag("failure_level", "activity")

                # Set fingerprint for better Sentry grouping
                scope.fingerprint = [
                    f"activity_{activity_name}",
                    str(type(e).__name__),
                    str(e),
                    "activity_failure",
                ]

                # Extract context using provided function
                extracted_tags, extracted_context = extract_context_from_contextvars(self.context_extraction_fn)

                # Set tags for filtering/searching
                for key, value in extracted_tags.items():
                    scope.set_tag(key, value)

                # Add detailed context
                context = {
                    "name": activity_name,
                    "headers": dict(input.headers),
                    "type": "activity",
                    "args": str(input.args),
                    "direction": "outbound",
                }
                context.update(extracted_context)

                # Add any additional context if provided
                if self.additional_context_fn:
                    additional_context = self.additional_context_fn(input)
                    context.update(additional_context)

                scope.set_context("activity_details", context)
                try:
                    capture_exception(e)
                except Exception as e:
                    self.logger.error(
                        "Sentry captured failed",
                        activity_name=activity_name,
                        error=str(e),
                    )
            raise


class SentryWorkflowInboundInterceptor(WorkflowInboundInterceptor):
    """Workflow inbound interceptor that reports failures to Sentry."""

    def __init__(
        self,
        next_interceptor: WorkflowInboundInterceptor,
        logger: Any,
        context_extraction_fn: Callable | None = None,
        additional_context_fn: Callable | None = None,
    ):
        self.next = next_interceptor
        self.logger = logger
        self.context_extraction_fn = context_extraction_fn
        self.additional_context_fn = additional_context_fn

    def init(self, outbound: WorkflowOutboundInterceptor) -> None:
        """Initialize with outbound interceptor."""
        self.next.init(
            SentryWorkflowOutboundInterceptor(
                outbound,
                self.logger,
                self.context_extraction_fn,
                self.additional_context_fn,
            )
        )

    async def execute_workflow(self, input: ExecuteWorkflowInput) -> Any:
        """Execute workflow and report failures to Sentry."""
        try:
            return await self.next.execute_workflow(input)
        except Exception as e:
            with push_scope() as scope:
                workflow_name = input.type.__name__
                # Set workflow-specific tags
                scope.set_tag("workflow.type", workflow_name)
                scope.set_tag("workflow.direction", "inbound")
                scope.set_tag("failure_level", "workflow")

                # Set fingerprint for better Sentry grouping
                scope.fingerprint = [
                    f"workflow_{workflow_name}",
                    str(type(e).__name__),
                    str(e),
                    "workflow_failure",
                ]

                # Extract context using provided function
                extracted_tags, extracted_context = extract_context_from_contextvars(self.context_extraction_fn)

                # Set tags for filtering/searching
                for key, value in extracted_tags.items():
                    scope.set_tag(key, value)

                # Add detailed context
                context = {
                    "type": workflow_name,
                    "headers": dict(input.headers),
                    "args": str(input.args),
                    "direction": "inbound",
                }
                context.update(extracted_context)

                # Add any additional context if provided
                if self.additional_context_fn:
                    additional_context = self.additional_context_fn(input)
                    context.update(additional_context)

                scope.set_context("workflow_details", context)
                try:
                    capture_exception(e)
                except Exception as e:
                    self.logger.error(
                        "Sentry captured failed",
                        workflow_name=workflow_name,
                        error=str(e),
                    )
            raise

    async def start_child_workflow(self, input: StartChildWorkflowInput) -> Any:
        """Execute child workflow and report failures to Sentry."""
        try:
            return await self.next.start_child_workflow(input)
        except Exception as e:
            with push_scope() as scope:
                # Set workflow-specific tags
                scope.set_tag("workflow.type", input.workflow)
                scope.set_tag("workflow.direction", "child_inbound")
                scope.set_tag("failure_level", "child_workflow")

                # Set fingerprint for better Sentry grouping
                scope.fingerprint = [
                    f"child_workflow_{input.workflow}",
                    str(type(e).__name__),
                    str(e),
                    "child_workflow_failure",
                ]

                # Extract context using provided function
                extracted_tags, extracted_context = extract_context_from_contextvars(self.context_extraction_fn)

                # Set tags for filtering/searching
                for key, value in extracted_tags.items():
                    scope.set_tag(key, value)

                # Add detailed context
                context = {
                    "type": input.workflow,
                    "workflow_id": input.id,
                    "task_queue": input.task_queue,
                    "headers": dict(input.headers),
                    "args": str(input.args),
                    "direction": "child_inbound",
                    "cron_schedule": input.cron_schedule,
                    "execution_timeout": str(input.execution_timeout) if input.execution_timeout else None,
                    "run_timeout": str(input.run_timeout) if input.run_timeout else None,
                }
                context.update(extracted_context)

                # Add any additional context if provided
                if self.additional_context_fn:
                    additional_context = self.additional_context_fn(input)
                    context.update(additional_context)

                scope.set_context("child_workflow_details", context)
                try:
                    capture_exception(e)
                except Exception as e:
                    self.logger.error(
                        "Sentry captured failed",
                        error=str(e),
                    )
            raise


class SentryWorkflowOutboundInterceptor(WorkflowOutboundInterceptor):
    """Workflow outbound interceptor that reports failures to Sentry."""

    def __init__(
        self,
        next_interceptor: WorkflowOutboundInterceptor,
        logger: Any,
        context_extraction_fn: Callable | None = None,
        additional_context_fn: Callable | None = None,
    ):
        self.next = next_interceptor
        self.logger = logger
        self.context_extraction_fn = context_extraction_fn
        self.additional_context_fn = additional_context_fn

    async def execute_workflow(self, input: ExecuteWorkflowInput) -> Any:
        """Execute workflow and report failures to Sentry."""
        try:
            return await self.next.execute_workflow(input)
        except Exception as e:
            with push_scope() as scope:
                workflow_name = input.type.__name__
                # Set workflow-specific tags
                scope.set_tag("workflow.type", workflow_name)
                scope.set_tag("workflow.direction", "outbound")
                scope.set_tag("failure_level", "workflow")

                # Set fingerprint for better Sentry grouping
                scope.fingerprint = [
                    f"workflow_{workflow_name}",
                    str(type(e).__name__),
                    str(e),
                    "workflow_failure",
                ]

                # Extract context using provided function
                extracted_tags, extracted_context = extract_context_from_contextvars(self.context_extraction_fn)

                # Set tags for filtering/searching
                for key, value in extracted_tags.items():
                    scope.set_tag(key, value)

                # Add detailed context
                context = {
                    "type": workflow_name,
                    "headers": dict(input.headers),
                    "args": str(input.args),
                    "direction": "outbound",
                }
                context.update(extracted_context)

                # Add any additional context if provided
                if self.additional_context_fn:
                    additional_context = self.additional_context_fn(input)
                    context.update(additional_context)

                scope.set_context("workflow_details", context)
                try:
                    capture_exception(e)
                except Exception as e:
                    self.logger.error(
                        "Sentry captured failed",
                        workflow_name=workflow_name,
                        error=str(e),
                    )
            raise

    async def start_child_workflow(self, input: StartChildWorkflowInput) -> Any:
        """Execute child workflow and report failures to Sentry."""
        try:
            return await self.next.start_child_workflow(input)
        except Exception as e:
            with push_scope() as scope:
                # Set workflow-specific tags
                scope.set_tag("workflow.type", input.workflow)
                scope.set_tag("workflow.direction", "child_outbound")
                scope.set_tag("failure_level", "child_workflow")

                # Set fingerprint for better Sentry grouping
                scope.fingerprint = [
                    f"child_workflow_{input.workflow}",
                    str(type(e).__name__),
                    str(e),
                    "child_workflow_failure",
                ]

                # Extract context using provided function
                extracted_tags, extracted_context = extract_context_from_contextvars(self.context_extraction_fn)

                # Set tags for filtering/searching
                for key, value in extracted_tags.items():
                    scope.set_tag(key, value)

                # Add detailed context
                context = {
                    "type": input.workflow,
                    "workflow_id": input.id,
                    "task_queue": input.task_queue,
                    "headers": dict(input.headers),
                    "args": str(input.args),
                    "direction": "child_outbound",
                    "cron_schedule": input.cron_schedule,
                    "execution_timeout": str(input.execution_timeout) if input.execution_timeout else None,
                    "run_timeout": str(input.run_timeout) if input.run_timeout else None,
                }
                context.update(extracted_context)

                # Add any additional context if provided
                if self.additional_context_fn:
                    additional_context = self.additional_context_fn(input)
                    context.update(additional_context)

                scope.set_context("child_workflow_details", context)
                try:
                    capture_exception(e)
                except Exception as e:
                    self.logger.error(
                        "Sentry captured failed",
                        error=str(e),
                    )
            raise


class SentryInterceptor(Interceptor):
    """
    Configurable Sentry interceptor that captures and reports workflow and activity failures.

    This interceptor can be configured with custom logging implementation and additional
    context functions, making it reusable across different codebases.
    """

    def __init__(
        self,
        logger_module: Any,
        context_extraction_fn: Callable | None = None,
        sentry_dsn: str | None = None,
        environment: str | None = None,
        additional_context_fn: Callable | None = None,
        **sentry_options: Any,
    ):
        """
        Initialize the Sentry interceptor with configurable parameters.

        Args:
            logger_module: Logger to use for logging (must support error method)
            context_extraction_fn: Optional function to extract context from contextvars
            sentry_dsn: Optional Sentry DSN. If not provided, assumes Sentry is already initialized
            environment: Optional environment name for Sentry
            additional_context_fn: Optional function to add custom context to Sentry events
            **sentry_options: Additional options to pass to sentry_sdk.init
        """
        self.logger = logger_module.get_logger(__name__)
        self.context_extraction_fn = context_extraction_fn
        self.additional_context_fn = additional_context_fn

        # Initialize Sentry if DSN is provided
        if sentry_dsn:
            init(
                dsn=sentry_dsn,
                environment=environment,
                **sentry_options,
            )

    def intercept_activity(self, next: ActivityInboundInterceptor) -> ActivityInboundInterceptor:
        """Create activity inbound interceptor."""
        return SentryActivityInboundInterceptor(
            next,
            self.logger,
            self.context_extraction_fn,
            self.additional_context_fn,
        )

    def workflow_interceptor_class(self, input: WorkflowInterceptorClassInput) -> type[WorkflowInboundInterceptor]:
        """Create workflow inbound interceptor class."""

        def interceptor_creator(next_interceptor):
            return SentryWorkflowInboundInterceptor(
                next_interceptor,
                self.logger,
                self.context_extraction_fn,
                self.additional_context_fn,
            )

        return interceptor_creator
