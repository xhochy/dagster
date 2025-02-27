from dagster import check
from dagster.core.events import DagsterEventType
from dagster.core.events.log import EventRecord
from dagster.core.storage.pipeline_run import PipelineRunStatsSnapshot


def build_stats_from_events(run_id, records):
    check.list_param(records, 'records', of_type=EventRecord)

    steps_succeeded = 0
    steps_failed = 0
    materializations = 0
    expectations = 0
    start_time = None
    end_time = None

    for event in records:
        if not event.is_dagster_event:
            continue
        if event.dagster_event.event_type == DagsterEventType.PIPELINE_START:
            start_time = event.timestamp
        if event.dagster_event.event_type == DagsterEventType.STEP_FAILURE:
            steps_failed += 1
        if event.dagster_event.event_type == DagsterEventType.STEP_SUCCESS:
            steps_succeeded += 1
        if event.dagster_event.event_type == DagsterEventType.STEP_MATERIALIZATION:
            materializations += 1
        if event.dagster_event.event_type == DagsterEventType.STEP_EXPECTATION_RESULT:
            expectations += 1
        if (
            event.dagster_event.event_type == DagsterEventType.PIPELINE_SUCCESS
            or event.dagster_event.event_type == DagsterEventType.PIPELINE_FAILURE
        ):
            end_time = event.timestamp

    return PipelineRunStatsSnapshot(
        run_id, steps_succeeded, steps_failed, materializations, expectations, start_time, end_time
    )
