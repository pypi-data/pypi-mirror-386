# Copyright 2023 Iguazio
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import typing
from datetime import datetime, timezone
from typing import Any, Callable, NewType, Optional

import storey

import mlrun.common.model_monitoring
import mlrun.common.schemas
import mlrun.common.schemas.alert as alert_objects
import mlrun.model_monitoring
from mlrun.common.schemas.model_monitoring.constants import (
    HistogramDataDriftApplicationConstants,
    MetricData,
    ResultData,
    ResultKindApp,
    ResultStatusApp,
    StatsData,
    StatsKind,
    WriterEvent,
    WriterEventKind,
)
from mlrun.config import config
from mlrun.model_monitoring.db import TSDBConnector
from mlrun.model_monitoring.db._stats import (
    ModelMonitoringCurrentStatsFile,
    ModelMonitoringDriftMeasuresFile,
)
from mlrun.model_monitoring.helpers import get_result_instance_fqn
from mlrun.serving.utils import StepToDict
from mlrun.utils import logger

_RawEvent = dict[str, Any]
_AppResultEvent = NewType("_AppResultEvent", _RawEvent)


class _WriterEventError:
    pass


class _WriterEventValueError(_WriterEventError, ValueError):
    pass


class _WriterEventTypeError(_WriterEventError, TypeError):
    pass


class ModelMonitoringWriter(StepToDict):
    """
    Write monitoring application results to the target databases
    """

    kind = "monitoring_application_stream_pusher"

    def __init__(
        self,
        project: str,
        secret_provider: Optional[Callable] = None,
    ) -> None:
        self.project = project
        self.name = project  # required for the deployment process

        self._tsdb_connector = mlrun.model_monitoring.get_tsdb_connector(
            project=self.project, secret_provider=secret_provider
        )

    def _generate_event_on_drift(
        self,
        entity_id: str,
        result_status: int,
        event_value: dict,
        project_name: str,
        result_kind: int,
    ) -> None:
        entity = mlrun.common.schemas.alert.EventEntities(
            kind=alert_objects.EventEntityKind.MODEL_ENDPOINT_RESULT,
            project=project_name,
            ids=[entity_id],
        )

        event_kind = self._generate_alert_event_kind(
            result_status=result_status, result_kind=result_kind
        )

        event_data = mlrun.common.schemas.Event(
            kind=alert_objects.EventKind(value=event_kind),
            entity=entity,
            value_dict=event_value,
        )
        logger.info("Sending a drift event")
        mlrun.get_run_db().generate_event(event_kind, event_data)
        logger.info("Drift event sent successfully")

    @staticmethod
    def _generate_alert_event_kind(
        result_kind: int, result_status: int
    ) -> alert_objects.EventKind:
        """Generate the required Event Kind format for the alerting system"""
        event_kind = ResultKindApp(value=result_kind).name

        if result_status == ResultStatusApp.detected.value:
            event_kind = f"{event_kind}_detected"
        else:
            event_kind = f"{event_kind}_suspected"
        return alert_objects.EventKind(
            value=mlrun.utils.helpers.normalize_name(event_kind)
        )

    @staticmethod
    def _reconstruct_event(event: _RawEvent) -> tuple[_AppResultEvent, WriterEventKind]:
        """
        Modify the raw event into the expected monitoring application event
        schema as defined in `mlrun.common.schemas.model_monitoring.constants.WriterEvent`
        """
        if not isinstance(event, dict):
            raise _WriterEventTypeError(
                f"The event is of type: {type(event)}, expected a dictionary"
            )
        kind = event.pop(WriterEvent.EVENT_KIND, WriterEventKind.RESULT)
        result_event = _AppResultEvent(json.loads(event.pop(WriterEvent.DATA, "{}")))
        result_event.update(_AppResultEvent(event))

        expected_keys = list(
            set(WriterEvent.list()).difference(
                [WriterEvent.EVENT_KIND, WriterEvent.DATA]
            )
        )
        if kind == WriterEventKind.METRIC:
            expected_keys.extend(MetricData.list())
        elif kind == WriterEventKind.RESULT:
            expected_keys.extend(ResultData.list())
        elif kind == WriterEventKind.STATS:
            expected_keys.extend(StatsData.list())
        else:
            raise _WriterEventValueError(
                f"Unknown event kind: {kind}, expected one of: {WriterEventKind.list()}"
            )
        missing_keys = [key for key in expected_keys if key not in result_event]
        if missing_keys:
            raise _WriterEventValueError(
                f"The received event misses some keys compared to the expected "
                f"monitoring application event schema: {missing_keys} for event kind {kind}"
            )

        return result_event, kind

    def write_stats(self, event: _AppResultEvent) -> None:
        """
        Write to file the application stats event
        :param event: application stats event
        """
        endpoint_id = event[WriterEvent.ENDPOINT_ID]
        logger.debug(
            "Updating the model endpoint with stats",
            endpoint_id=endpoint_id,
        )
        stat_kind = event.get(StatsData.STATS_NAME)
        data, timestamp_str = event.get(StatsData.STATS), event.get(StatsData.TIMESTAMP)
        timestamp = datetime.fromisoformat(timestamp_str).astimezone(tz=timezone.utc)
        if stat_kind == StatsKind.CURRENT_STATS.value:
            ModelMonitoringCurrentStatsFile(self.project, endpoint_id).write(
                data, timestamp
            )
        elif stat_kind == StatsKind.DRIFT_MEASURES.value:
            ModelMonitoringDriftMeasuresFile(self.project, endpoint_id).write(
                data, timestamp
            )
        logger.info(
            "Updated the model endpoint statistics",
            endpoint_id=endpoint_id,
            stats_kind=stat_kind,
        )

    def do(self, event: _RawEvent) -> None:
        event, kind = self._reconstruct_event(event)
        logger.info("Starting to write event", event=event)
        if (
            kind == WriterEventKind.STATS
            and event[WriterEvent.APPLICATION_NAME]
            == HistogramDataDriftApplicationConstants.NAME
        ):
            self.write_stats(event)
            logger.info("Model monitoring writer finished handling event")
            return
        self._tsdb_connector.write_application_event(event=event.copy(), kind=kind)

        logger.info("Completed event DB writes")

        if (
            mlrun.mlconf.alerts.mode == mlrun.common.schemas.alert.AlertsModes.enabled
            and kind == WriterEventKind.RESULT
            and (
                event[ResultData.RESULT_STATUS] == ResultStatusApp.detected.value
                or event[ResultData.RESULT_STATUS]
                == ResultStatusApp.potential_detection.value
            )
        ):
            event_value = {
                "app_name": event[WriterEvent.APPLICATION_NAME],
                "model": event[WriterEvent.ENDPOINT_NAME],
                "model_endpoint_id": event[WriterEvent.ENDPOINT_ID],
                "result_name": event[ResultData.RESULT_NAME],
                "result_value": event[ResultData.RESULT_VALUE],
            }
            self._generate_event_on_drift(
                entity_id=get_result_instance_fqn(
                    event[WriterEvent.ENDPOINT_ID],
                    event[WriterEvent.APPLICATION_NAME],
                    event[ResultData.RESULT_NAME],
                ),
                result_status=event[ResultData.RESULT_STATUS],
                event_value=event_value,
                project_name=self.project,
                result_kind=event[ResultData.RESULT_KIND],
            )

        logger.info("Model monitoring writer finished handling event")


class WriterGraphFactory:
    def __init__(
        self,
        parquet_path: str,
    ):
        self.parquet_path = parquet_path
        self.parquet_batching_max_events = (
            config.model_endpoint_monitoring.writer_graph.max_events
        )
        self.parquet_batching_timeout_secs = (
            config.model_endpoint_monitoring.writer_graph.parquet_batching_timeout_secs
        )

    def apply_writer_graph(
        self,
        fn: mlrun.runtimes.ServingRuntime,
        tsdb_connector: TSDBConnector,
    ):
        graph = typing.cast(
            mlrun.serving.states.RootFlowStep,
            fn.set_topology(mlrun.serving.states.StepKinds.flow, engine="async"),
        )

        graph.to("ReconstructWriterEvent", "event_reconstructor")
        step = tsdb_connector.add_pre_writer_steps(
            graph=graph, after="event_reconstructor"
        )
        before_choice = step.name if step else "event_reconstructor"
        graph.add_step("KindChoice", "kind_choice_step", after=before_choice)
        tsdb_connector.apply_writer_steps(
            graph=graph,
            after="kind_choice_step",
        )
        graph.add_step(
            "AlertGenerator",
            "alert_generator",
            after="kind_choice_step",
            project=fn.metadata.project,
        )
        graph.add_step(
            "storey.Filter",
            name="filter_none",
            _fn="(event is not None)",
            after="alert_generator",
        )
        graph.add_step(
            "mlrun.serving.remote.MLRunAPIRemoteStep",
            name="alert_generator_api_call",
            after="filter_none",
            method="POST",
            path=f"projects/{fn.metadata.project}/events/{{kind}}",
            fill_placeholders=True,
        )

        graph.add_step(
            "mlrun.datastore.storeytargets.ParquetStoreyTarget",
            alternative_v3io_access_key=mlrun.common.schemas.model_monitoring.ProjectSecretKeys.ACCESS_KEY,
            name="stats_writer",
            after="kind_choice_step",
            graph_shape="cylinder",
            path=self.parquet_path
            if self.parquet_path.endswith("/")
            else self.parquet_path + "/",
            max_events=self.parquet_batching_max_events,
            flush_after_seconds=self.parquet_batching_timeout_secs,
            columns=[
                StatsData.TIMESTAMP,
                StatsData.STATS,
                WriterEvent.ENDPOINT_ID,
                StatsData.STATS_NAME,
            ],
            partition_cols=[WriterEvent.ENDPOINT_ID, StatsData.STATS_NAME],
            single_file=True,
        )


class ReconstructWriterEvent(storey.MapClass):
    def __init__(self):
        super().__init__()

    def do(self, event: dict) -> dict[str, Any]:
        logger.info("Reconstructing the event", event=event)
        kind = event.pop(WriterEvent.EVENT_KIND, WriterEventKind.RESULT)
        result_event = _AppResultEvent(json.loads(event.pop(WriterEvent.DATA, "{}")))
        result_event.update(_AppResultEvent(event))

        expected_keys = list(
            set(WriterEvent.list()).difference(
                [WriterEvent.EVENT_KIND, WriterEvent.DATA]
            )
        )
        if kind == WriterEventKind.METRIC:
            expected_keys.extend(MetricData.list())
        elif kind == WriterEventKind.RESULT:
            expected_keys.extend(ResultData.list())
        elif kind == WriterEventKind.STATS:
            expected_keys.extend(StatsData.list())
        else:
            raise _WriterEventValueError(
                f"Unknown event kind: {kind}, expected one of: {WriterEventKind.list()}"
            )
        missing_keys = [key for key in expected_keys if key not in result_event]
        if missing_keys:
            raise _WriterEventValueError(
                f"The received event misses some keys compared to the expected "
                f"monitoring application event schema: {missing_keys} for event kind {kind}"
            )
        result_event["kind"] = kind
        if kind in WriterEventKind.user_app_outputs():
            result_event[WriterEvent.END_INFER_TIME] = datetime.fromisoformat(
                event[WriterEvent.END_INFER_TIME]
            )
        if kind == WriterEventKind.STATS:
            result_event[StatsData.STATS] = json.dumps(result_event[StatsData.STATS])
        return result_event


class KindChoice(storey.Choice):
    def select_outlets(self, event):
        kind = event.get("kind")
        logger.info("Selecting the outlet for the event", kind=kind)
        if kind == WriterEventKind.METRIC:
            outlets = ["tsdb_metrics"]
        elif kind == WriterEventKind.RESULT:
            outlets = ["tsdb_app_results", "alert_generator"]
        elif kind == WriterEventKind.STATS:
            outlets = ["stats_writer"]
        else:
            raise _WriterEventValueError(
                f"Unknown event kind: {kind}, expected one of: {WriterEventKind.list()}"
            )
        return outlets


class AlertGenerator(storey.MapClass):
    def __init__(self, project: str, **kwargs):
        self.project = project
        super().__init__(**kwargs)

    def do(self, event: dict) -> Optional[dict[str, Any]]:
        kind = event.pop(WriterEvent.EVENT_KIND, WriterEventKind.RESULT)
        if (
            mlrun.mlconf.alerts.mode == mlrun.common.schemas.alert.AlertsModes.enabled
            and kind == WriterEventKind.RESULT
            and (
                event[ResultData.RESULT_STATUS] == ResultStatusApp.detected.value
                or event[ResultData.RESULT_STATUS]
                == ResultStatusApp.potential_detection.value
            )
        ):
            event_value = {
                "app_name": event[WriterEvent.APPLICATION_NAME],
                "model": event[WriterEvent.ENDPOINT_NAME],
                "model_endpoint_id": event[WriterEvent.ENDPOINT_ID],
                "result_name": event[ResultData.RESULT_NAME],
                "result_value": event[ResultData.RESULT_VALUE],
            }
            data = self._generate_event_data(
                entity_id=get_result_instance_fqn(
                    event[WriterEvent.ENDPOINT_ID],
                    event[WriterEvent.APPLICATION_NAME],
                    event[ResultData.RESULT_NAME],
                ),
                result_status=event[ResultData.RESULT_STATUS],
                event_value=event_value,
                project_name=self.project,
                result_kind=event[ResultData.RESULT_KIND],
            )
            event = data.dict()
            logger.info("Generated alert event", event=event)
            return event
        return None

    @staticmethod
    def _generate_alert_event_kind(
        result_kind: int, result_status: int
    ) -> alert_objects.EventKind:
        """Generate the required Event Kind format for the alerting system"""
        event_kind = ResultKindApp(value=result_kind).name

        if result_status == ResultStatusApp.detected.value:
            event_kind = f"{event_kind}_detected"
        else:
            event_kind = f"{event_kind}_suspected"
        return alert_objects.EventKind(
            value=mlrun.utils.helpers.normalize_name(event_kind)
        )

    def _generate_event_data(
        self,
        entity_id: str,
        result_status: int,
        event_value: dict,
        project_name: str,
        result_kind: int,
    ) -> mlrun.common.schemas.Event:
        entity = mlrun.common.schemas.alert.EventEntities(
            kind=alert_objects.EventEntityKind.MODEL_ENDPOINT_RESULT,
            project=project_name,
            ids=[entity_id],
        )

        event_kind = self._generate_alert_event_kind(
            result_status=result_status, result_kind=result_kind
        )

        event_data = mlrun.common.schemas.Event(
            kind=alert_objects.EventKind(value=event_kind),
            entity=entity,
            value_dict=event_value,
        )

        return event_data
