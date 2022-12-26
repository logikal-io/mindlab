import sys
from typing import Any, Optional, no_type_check

import ipywidgets
import pandas
from google.cloud import bigquery, exceptions
from humanize.filesize import naturalsize
from IPython.core.magic import Magics, cell_magic, magics_class
from IPython.core.magic_arguments import argument, magic_arguments, parse_argstring
from IPython.display import display

from mindlab.auth import GCPAuth


@magics_class
class MindLabMagics(Magics):  # type: ignore[misc]
    def __init__(self, shell: Any, **kwargs: Any):
        """
        Magics for data science work.
        """
        super().__init__(shell, **kwargs)
        pandas.set_option('display.max_columns', 50)
        pandas.set_option('display.max_rows', 500)
        self._gcp_auth = GCPAuth()

    @no_type_check
    @magic_arguments()
    @argument('output', nargs='?', help='Name of the variable in which to store the output')
    @argument('-o', '--organization', help='The organization to use')
    @argument('-p', '--project', help='The project to use')
    @argument('-t', '--transpose', action='store_true', help='Display the data frame transposed')
    @argument('-i', '--info', action='store_true', help='Display additional query information')
    @cell_magic
    def bigquery(self, line: str, cell: str) -> Optional[pandas.DataFrame]:
        """
        Cell magic to execute a Google BigQuery query.
        """
        args = parse_argstring(self.bigquery, line)
        credentials, project_id = self._gcp_auth.credentials(args.organization, args.project)
        with bigquery.Client(credentials=credentials, project=project_id) as client:
            query = client.query(cell)
            try:
                data = query.to_dataframe(progress_bar_type='tqdm_notebook' if args.info else None)
            except exceptions.BadRequest as error:
                print(f'Error: {error}', file=sys.stderr)
                return None
            if args.info:
                processed = naturalsize(query.total_bytes_processed)
                display(ipywidgets.HTML(value='Data processed: ' + (
                    f'<b>{processed}</b>' if not query.cache_hit
                    else 'none <b>(returned from cache)</b>'
                )))

        if args.output:
            self.shell.push({args.output: data})
            return None
        return data if not args.transpose else data.transpose()


def load_ipython_extension(ipython: Any) -> None:
    ipython.register_magics(MindLabMagics)
