import collections
import logging
import time
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Union

import pydantic.error_wrappers
import redshift_connector
from pydantic.fields import Field
from pydantic.main import BaseModel

import datahub.emitter.mce_builder as builder
from datahub.configuration.time_window_config import get_time_bucket
from datahub.emitter.mcp import MetadataChangeProposalWrapper
from datahub.ingestion.api.workunit import MetadataWorkUnit
from datahub.ingestion.source.redshift.config import RedshiftConfig
from datahub.ingestion.source.redshift.redshift_schema import (
    RedshiftTable,
    RedshiftView,
)
from datahub.ingestion.source.redshift.report import RedshiftReport
from datahub.ingestion.source.usage.usage_common import GenericAggregatedDataset
from datahub.metadata.schema_classes import OperationClass, OperationTypeClass
from datahub.utilities.perf_timer import PerfTimer
from datahub.utilities.urns.dataset_urn import DatasetUrn

logger = logging.getLogger(__name__)

REDSHIFT_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


# Add this join to the sql query for more metrics on completed queries
# LEFT JOIN svl_query_metrics_summary sqms ON ss.query = sqms.query
# Reference: https://docs.aws.amazon.com/redshift/latest/dg/r_SVL_QUERY_METRICS_SUMMARY.html

# this sql query joins stl_scan over table info,
# querytext, and user info to get usage stats
# using non-LEFT joins here to limit the results to
# queries run by the user on user-defined tables.
REDSHIFT_USAGE_QUERY_TEMPLATE: str = """
SELECT DISTINCT ss.userid as userid,
       ss.query as query,
       sui.usename as username,
       ss.tbl as tbl,
       sq.querytxt as querytxt,
       sti.database as database,
       sti.schema as schema,
       sti.table as table,
       sq.starttime as starttime,
       sq.endtime as endtime
FROM stl_scan ss
  JOIN svv_table_info sti ON ss.tbl = sti.table_id
  JOIN stl_query sq ON ss.query = sq.query
  JOIN svl_user_info sui ON sq.userid = sui.usesysid
WHERE ss.starttime >= '{start_time}'
AND ss.starttime < '{end_time}'
AND sti.database = '{database}'
AND sq.aborted = 0
ORDER BY ss.endtime DESC;
""".strip()

REDSHIFT_OPERATION_ASPECT_QUERY_TEMPLATE: str = """
  (SELECT
      DISTINCT si.userid AS userid,
      si.query AS query,
      si.rows AS rows,
      sui.usename AS username,
      si.tbl AS tbl,
      sq.querytxt AS querytxt,
      sti.database AS database,
      sti.schema AS schema,
      sti.table AS table,
      sq.starttime AS starttime,
      sq.endtime AS endtime,
      'insert' AS operation_type
    FROM
      stl_insert si
      JOIN svv_table_info sti ON si.tbl = sti.table_id
      JOIN stl_query sq ON si.query = sq.query
      JOIN svl_user_info sui ON sq.userid = sui.usesysid
    WHERE
      si.starttime >= '{start_time}'
      AND si.starttime < '{end_time}'
      AND si.rows > 0
      AND sq.aborted = 0)
UNION
  (SELECT
      DISTINCT sd.userid AS userid,
      sd.query AS query,
      sd.rows AS ROWS,
      sui.usename AS username,
      sd.tbl AS tbl,
      sq.querytxt AS querytxt,
      sti.database AS database,
      sti.schema AS schema,
      sti.table AS table,
      sq.starttime AS starttime,
      sq.endtime AS endtime,
      'delete' AS operation_type
    FROM
      stl_delete sd
      JOIN svv_table_info sti ON sd.tbl = sti.table_id
      JOIN stl_query sq ON sd.query = sq.query
      JOIN svl_user_info sui ON sq.userid = sui.usesysid
    WHERE
      sd.starttime >= '{start_time}'
      AND sd.starttime < '{end_time}'
      AND sd.rows > 0
      AND sq.aborted = 0)
ORDER BY
  endtime DESC
""".strip()

RedshiftTableRef = str
AggregatedDataset = GenericAggregatedDataset[RedshiftTableRef]
AggregatedAccessEvents = Dict[datetime, Dict[RedshiftTableRef, AggregatedDataset]]


class RedshiftAccessEvent(BaseModel):
    userid: int
    username: str
    query: int
    tbl: int
    text: str = Field(alias="querytxt")
    database: str
    schema_: str = Field(alias="schema")
    table: str
    operation_type: Optional[str] = None
    starttime: datetime
    endtime: datetime


class RedshiftUsageExtractor:
    """
    This plugin extracts usage statistics for datasets in Amazon Redshift.

    Note: Usage information is computed by querying the following system tables -
    1. stl_scan
    2. svv_table_info
    3. stl_query
    4. svl_user_info

    To grant access this plugin for all system tables, please alter your datahub Redshift user the following way:
    ```sql
    ALTER USER datahub_user WITH SYSLOG ACCESS UNRESTRICTED;
    ```
    This plugin has the below functionalities -
    1. For a specific dataset this plugin ingests the following statistics -
       1. top n queries.
       2. top users.
    2. Aggregation of these statistics into buckets, by day or hour granularity.

    :::note

    This source only does usage statistics. To get the tables, views, and schemas in your Redshift warehouse, ingest using the `redshift` source described above.

    :::

    :::note

    Redshift system tables have some latency in getting data from queries. In addition, these tables only maintain logs for 2-5 days. You can find more information from the official documentation [here](https://aws.amazon.com/premiumsupport/knowledge-center/logs-redshift-database-cluster/).

    :::

    """

    def __init__(
        self,
        config: RedshiftConfig,
        connection: redshift_connector.Connection,
        report: RedshiftReport,
    ):
        self.config = config
        self.report = report
        self.connection = connection

    def generate_usage(
        self, all_tables: Dict[str, Dict[str, List[Union[RedshiftView, RedshiftTable]]]]
    ) -> Iterable[MetadataWorkUnit]:
        self.report.num_usage_workunits_emitted = 0
        self.report.num_usage_stat_skipped = 0
        self.report.num_operational_stats_skipped = 0

        """Gets Redshift usage stats as work units"""
        if self.config.include_operational_stats:
            with PerfTimer() as timer:
                # Generate operation aspect workunits
                yield from self._gen_operation_aspect_workunits(
                    self.connection, all_tables
                )
                self.report.operational_metadata_extraction_sec[
                    self.config.database
                ] = round(timer.elapsed_seconds(), 2)

        # Generate aggregate events
        query: str = REDSHIFT_USAGE_QUERY_TEMPLATE.format(
            start_time=self.config.start_time.strftime(REDSHIFT_DATETIME_FORMAT),
            end_time=self.config.end_time.strftime(REDSHIFT_DATETIME_FORMAT),
            database=self.config.database,
        )
        access_events_iterable: Iterable[
            RedshiftAccessEvent
        ] = self._gen_access_events_from_history_query(
            query, connection=self.connection, all_tables=all_tables
        )

        aggregated_events: AggregatedAccessEvents = self._aggregate_access_events(
            access_events_iterable
        )
        # Generate usage workunits from aggregated events.
        for time_bucket in aggregated_events.values():
            for aggregate in time_bucket.values():
                wu: MetadataWorkUnit = self._make_usage_stat(aggregate)
                self.report.num_usage_workunits_emitted += 1
                yield wu

    def _gen_operation_aspect_workunits(
        self,
        connection: redshift_connector.Connection,
        all_tables: Dict[str, Dict[str, List[Union[RedshiftView, RedshiftTable]]]],
    ) -> Iterable[MetadataWorkUnit]:
        # Generate access events
        query: str = REDSHIFT_OPERATION_ASPECT_QUERY_TEMPLATE.format(
            start_time=self.config.start_time.strftime(REDSHIFT_DATETIME_FORMAT),
            end_time=self.config.end_time.strftime(REDSHIFT_DATETIME_FORMAT),
        )
        access_events_iterable: Iterable[
            RedshiftAccessEvent
        ] = self._gen_access_events_from_history_query(
            query, connection, all_tables=all_tables
        )

        # Generate operation aspect work units from the access events
        yield from self._gen_operation_aspect_workunits_from_access_events(
            access_events_iterable, all_tables=all_tables
        )

    def _should_process_event(
        self,
        event: RedshiftAccessEvent,
        all_tables: Dict[str, Dict[str, List[Union[RedshiftView, RedshiftTable]]]],
    ) -> bool:
        # Check schema/table allow/deny patterns
        return not (
            event.database not in all_tables
            or event.schema_ not in all_tables[event.database]
            or not any(
                event.table == t.name for t in all_tables[event.database][event.schema_]
            )
        )

    def _gen_access_events_from_history_query(
        self,
        query: str,
        connection: redshift_connector.Connection,
        all_tables: Dict[str, Dict[str, List[Union[RedshiftView, RedshiftTable]]]],
    ) -> Iterable[RedshiftAccessEvent]:
        cursor = connection.cursor()
        cursor.execute(query)
        results = cursor.fetchmany()
        field_names = [i[0] for i in cursor.description]
        while results:
            for row in results:
                try:
                    access_event = RedshiftAccessEvent(
                        userid=row[field_names.index("userid")],
                        username=row[field_names.index("username")],
                        query=row[field_names.index("query")],
                        querytxt=row[field_names.index("querytxt")].strip()
                        if row[field_names.index("querytxt")]
                        else None,
                        tbl=row[field_names.index("tbl")],
                        database=row[field_names.index("database")],
                        schema=row[field_names.index("schema")],
                        table=row[field_names.index("table")],
                        starttime=row[field_names.index("starttime")],
                        endtime=row[field_names.index("endtime")],
                        operation_type=row[field_names.index("operation_type")]
                        if "operation_type" in field_names
                        else None,
                    )
                except pydantic.error_wrappers.ValidationError as e:
                    logging.warning(
                        f"Validation error on access event creation from row {row}. The error was: {e} Skipping ...."
                    )
                    self.report.num_usage_stat_skipped += 1
                    continue

                # Replace database name with the alias name if one is provided in the config.
                if self.config.database_alias:
                    access_event.database = self.config.database_alias

                if not self._should_process_event(access_event, all_tables=all_tables):
                    self.report.num_usage_stat_skipped += 1
                    continue

                yield access_event
            results = cursor.fetchmany()

    def _gen_operation_aspect_workunits_from_access_events(
        self,
        events_iterable: Iterable[RedshiftAccessEvent],
        all_tables: Dict[str, Dict[str, List[Union[RedshiftView, RedshiftTable]]]],
    ) -> Iterable[MetadataWorkUnit]:
        self.report.num_operational_stats_workunits_emitted = 0
        for event in events_iterable:
            if not (
                event.database
                and event.username
                and event.schema_
                and event.table
                and event.endtime
                and event.operation_type
            ):
                continue

            if not self._should_process_event(event, all_tables=all_tables):
                self.report.num_operational_stats_skipped += 1
                continue

            assert event.operation_type in ["insert", "delete"]

            resource: str = f"{event.database}.{event.schema_}.{event.table}"
            reported_time: int = int(time.time() * 1000)
            last_updated_timestamp: int = int(event.endtime.timestamp() * 1000)
            user_email: str = event.username
            operation_aspect = OperationClass(
                timestampMillis=reported_time,
                lastUpdatedTimestamp=last_updated_timestamp,
                actor=builder.make_user_urn(user_email.split("@")[0]),
                operationType=(
                    OperationTypeClass.INSERT
                    if event.operation_type == "insert"
                    else OperationTypeClass.DELETE
                ),
            )
            dataset_urn = DatasetUrn.create_from_ids(
                platform_id="redshift",
                table_name=resource.lower(),
                platform_instance=self.config.platform_instance,
                env=self.config.env,
            )

            yield MetadataChangeProposalWrapper(
                entityUrn=str(dataset_urn), aspect=operation_aspect
            ).as_workunit()
            self.report.num_operational_stats_workunits_emitted += 1

    def _aggregate_access_events(
        self, events_iterable: Iterable[RedshiftAccessEvent]
    ) -> AggregatedAccessEvents:
        datasets: AggregatedAccessEvents = collections.defaultdict(dict)
        for event in events_iterable:
            floored_ts: datetime = get_time_bucket(
                event.starttime, self.config.bucket_duration
            )
            resource: str = f"{event.database}.{event.schema_}.{event.table}"
            # Get a reference to the bucket value(or initialize not yet in dict) and update it.
            agg_bucket: AggregatedDataset = datasets[floored_ts].setdefault(
                resource,
                AggregatedDataset(
                    bucket_start_time=floored_ts,
                    resource=resource,
                ),
            )
            # current limitation in user stats UI, we need to provide email to show users
            user_email: str = f"{event.username if event.username else 'unknown'}"
            if "@" not in user_email:
                user_email += f"@{self.config.email_domain}"
            agg_bucket.add_read_entry(
                user_email,
                event.text,
                [],  # TODO: not currently supported by redshift; find column level changes
                user_email_pattern=self.config.user_email_pattern,
            )
        return datasets

    def _make_usage_stat(self, agg: AggregatedDataset) -> MetadataWorkUnit:
        return agg.make_usage_workunit(
            self.config.bucket_duration,
            lambda resource: builder.make_dataset_urn_with_platform_instance(
                "redshift",
                resource.lower(),
                self.config.platform_instance,
                self.config.env,
            ),
            self.config.top_n_queries,
            self.config.format_sql_queries,
            self.config.include_top_n_queries,
        )
