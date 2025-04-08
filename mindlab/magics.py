import sys
from argparse import Namespace
from functools import reduce
from typing import Any, no_type_check

import awswrangler
import ipywidgets
import pandas as pd
import redshift_connector
from boto3.session import Session
from botocore import exceptions as aws_exceptions
from google.auth.credentials import Credentials as GCPCredentials
from google.cloud import bigquery, exceptions as gcp_exceptions
from humanize.filesize import naturalsize
from IPython.core.magic import Magics, cell_magic, line_magic, magics_class
from IPython.core.magic_arguments import argument, magic_arguments, parse_argstring
from IPython.display import display
from stormware.amazon.auth import AWSAuth
from stormware.google.auth import GCPAuth

from mindlab.utils import Timer, get_config, mindlab_config


def compose_magic_decorators(*decorators: Any) -> Any:
    return reduce(lambda outer, inner: lambda magic_method: outer(inner(magic_method)), decorators)


common_arguments = compose_magic_decorators(
    magic_arguments(),
    argument('output', nargs='?', help='Name of the variable in which to store the output'),
    argument('-o', '--organization', help='The organization to use'),
    argument('-t', '--transpose', action='store_true', help='Display the data frame transposed'),
    argument('-i', '--info', action='store_true', help='Display additional query information'),
)
common_gcp_arguments = compose_magic_decorators(
    common_arguments,
    argument('-p', '--project', help='The project to use'),
)
common_aws_arguments = compose_magic_decorators(
    common_arguments,
    argument('-r', '--region', help='The region to use'),
)


@magics_class
class MindLabMagics(Magics):
    def __init__(self, shell: Any, **kwargs: Any):
        """
        Magics for data science work.
        """
        super().__init__(shell, **kwargs)  # type: ignore[no-untyped-call]
        pd.set_option('display.max_columns', 50)
        pd.set_option('display.max_rows', 500)
        self._aws_auth = AWSAuth()
        self._gcp_auth = GCPAuth()

    @no_type_check
    @magic_arguments()
    @argument('name', nargs='?', help='Name of the configuration value to get or set')
    @argument('value', nargs='?', help='New configuration value')
    @line_magic
    def mindlab_config(self, line: str) -> None:
        """
        Manage MindLab configuration.

        Setting a configuration value has the same effect as adding it to the ``tool.mindlab``
        section of the ``pyproject.toml`` file.
        """
        args = parse_argstring(self.mindlab_config, line)
        if not args.name:
            print(mindlab_config)
        elif not args.value:
            print(mindlab_config.get(args.name))
        else:
            mindlab_config[args.name] = args.value

    @no_type_check
    @common_gcp_arguments
    @cell_magic
    def bigquery(self, line: str, cell: str) -> pd.DataFrame | None:
        """
        Run a Google BigQuery query.
        """
        args = parse_argstring(self.bigquery, line)
        client_args = self._gcp_client_arguments(args, magic='bigquery')
        with bigquery.Client(**client_args) as client:
            query = client.query(cell)
            try:
                with Timer() as timer:
                    progress_bar = 'tqdm_notebook' if args.info else None
                    data = query.to_dataframe(progress_bar_type=progress_bar)
            except gcp_exceptions.BadRequest as error:
                print(f'Error: {error}', file=sys.stderr)
                return None

        if args.info:
            processed = (
                naturalsize(query.total_bytes_processed)
                if not query.cache_hit else 'none (returned from cache)'
            )
            self._display_query_details(
                total_time_ms=timer.time / 1e6,
                details=[f'Data processed: <b>{processed}</b>'],
            )

        return self._cell_magic_data(data=data, args=args)

    @no_type_check
    @common_aws_arguments
    @argument('-d', '--database', default='default', help='The database to use')
    @argument('-w', '--workgroup', default='primary', help='The workgroup to use')
    @cell_magic
    def athena(self, line: str, cell: str) -> pd.DataFrame | None:
        """
        Run an Amazon Athena query.
        """
        args = parse_argstring(self.athena, line)
        session = self._aws_session(args, magic='athena')
        try:
            data = awswrangler.athena.read_sql_query(
                sql=cell,
                database=self.get_config('athena_database', args.database),
                workgroup=self.get_config('athena_workgroup', args.workgroup),
                ctas_approach=False,
                encryption='SSE_S3', boto3_session=session,
            )
        except aws_exceptions.UnauthorizedSSOTokenError as error:
            print(f'Profile: {session.profile_name}', file=sys.stderr)
            print(f'Error: {error}', file=sys.stderr)
            return None
        except (
            aws_exceptions.BotoCoreError,
            aws_exceptions.ClientError,
            awswrangler.exceptions.QueryFailed,
            awswrangler.exceptions.QueryCancelled,
        ) as error:
            print(f'Error: {error}', file=sys.stderr)
            return None

        if args.info:
            stats = data.query_metadata['Statistics']
            planned = stats.get('QueryPlanningTimeInMillis', 0)
            timing = {
                'queued': stats.get('QueryQueueTimeInMillis', 0),
                'planned': planned,
                'executed': stats['EngineExecutionTimeInMillis'] - planned,
                'processed': stats.get('ServiceProcessingTimeInMillis', 0),
            }
            timing_info = ' » '.join(f'{name} {value:,.0f} ms' for name, value in timing.items())
            scanned = naturalsize(stats['DataScannedInBytes'])
            self._display_query_details(
                total_time_ms=stats["TotalExecutionTimeInMillis"],
                timing_info=timing_info,
                details=[
                    f'Data scanned: <b>{scanned}</b>',
                    f'Job ID: <em>{data.query_metadata["QueryExecutionId"]}</em>',
                ],
            )

        return self._cell_magic_data(data=data, args=args)

    @no_type_check
    @common_aws_arguments
    @argument('-c', '--connection', help='The Glue connection to use')
    @cell_magic
    def redshift(self, line: str, cell: str) -> pd.DataFrame | None:
        """
        Run an Amazon Redshift query.
        """
        args = parse_argstring(self.redshift, line)
        session = self._aws_session(args, magic='redshift')
        try:
            with Timer() as timer:
                connection = awswrangler.redshift.connect(
                    connection=self.get_config('redshift_connection', args.connection),
                    boto3_session=session, timeout=10,
                )
                data = awswrangler.redshift.read_sql_query(sql=cell, con=connection)
        except aws_exceptions.UnauthorizedSSOTokenError as error:
            print(f'Profile: {session.profile_name}', file=sys.stderr)
            print(f'Error: {error}', file=sys.stderr)
            return None
        except (
            awswrangler.exceptions.InvalidArgumentCombination,
            redshift_connector.error.Error,
        ) as error:
            print(f'Error: {error}', file=sys.stderr)
            return None

        if args.info:
            self._display_query_details(total_time_ms=timer.time / 1e6)

        return self._cell_magic_data(data=data, args=args)

    @staticmethod
    def get_config(
        name: str, value: str | None = None, magic: str | None = None, required: bool = True,
    ) -> str | None:
        if not value and magic:
            value = get_config(f'{magic}_{name}')
        return value or get_config(name, required=required)

    def _gcp_client_arguments(
        self, args: Namespace, magic: str,
    ) -> dict[str, GCPCredentials | str]:
        auth_args = {
            'organization': self.get_config(
                'organization', args.organization, magic=magic, required=False,
            ),
            'project': self.get_config('project', args.project, magic=magic, required=False),
        }
        return {
            'credentials': self._gcp_auth.credentials(**auth_args),
            'project': self._gcp_auth.project_id(**auth_args),
        }

    def _aws_session(self, args: Namespace, magic: str) -> Session:
        org = self.get_config('organization', args.organization, magic=magic, required=False)
        return self._aws_auth.session(
            organization=org,
            region=self.get_config('region', args.region, magic=magic, required=False),
        )

    @staticmethod
    def _display_query_details(
        total_time_ms: float,
        timing_info: str | None = None,
        details: list[str] | None = None,
    ) -> None:
        timing_info = f' ({timing_info})' if timing_info else ''
        display(ipywidgets.HTML(value='<br>'.join([
            '<b>Query Details</b>',
            *(details or []),
            f'Total time: <b>{total_time_ms:,.0f} ms{timing_info}</b>',
        ])))

    def _cell_magic_data(self, data: pd.DataFrame, args: Namespace) -> pd.DataFrame | None:
        if args.output:
            self.shell.push({args.output: data})  # type: ignore[union-attr]
            return None
        return data if not args.transpose else data.transpose()


def load_ipython_extension(ipython: Any) -> None:
    ipython.register_magics(MindLabMagics)
