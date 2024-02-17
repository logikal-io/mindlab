import re
import sys
from importlib.metadata import version as pkg_version
from typing import Any, List, Tuple, cast

from IPython.core.magic import Magics
from sphinx import addnodes, domains
from sphinx.application import Sphinx
from sphinx.environment import BuildEnvironment
from sphinx.ext.autodoc import Documenter, ObjectMembers
from sphinx.ext.autodoc.importer import get_class_members
from sphinx.roles import XRefRole

extensions = [
    'sphinx.ext.autosectionlabel',
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
]
intersphinx_mapping = {
    'python': (f'https://docs.python.org/{sys.version_info[0]}.{sys.version_info[1]}', None),
    'pandas': (f'https://pandas.pydata.org/pandas-docs/version/{pkg_version("pandas")}', None),
    'matplotlib': (f'https://matplotlib.org/{pkg_version("matplotlib")}/', None),
    'pyspark': (f'https://spark.apache.org/docs/{pkg_version("pyspark")}/api/python/', None),
    'stormware': (f'https://docs.logikal.io/stormware/{pkg_version("stormware")}/', None),
}
nitpick_ignore = [
    ('py:class', 'pandas.core.groupby.generic.DataFrameGroupBy'),
    ('py:class', 'pyspark.sql.session.SparkSession'),
]


class MagicsDocumenter(Documenter):
    """
    Documenter subclass for magics classes.
    """
    objtype = 'magics'
    titles_allowed = True

    @classmethod
    def can_document_member(cls, member: Any, membername: str, isattr: bool, parent: Any) -> bool:
        return issubclass(parent.object, Magics) and (
            membername in parent.object.magics['line']
            or membername in parent.object.magics['cell']
        )

    def resolve_name(
        self, modname: str, parents: Any, path: str, base: Any,
    ) -> Tuple[str, List[str]]:
        return modname or path.rstrip('.'), parents + [base]

    def get_object_members(self, want_all: bool) -> Tuple[bool, ObjectMembers]:
        return False, list(get_class_members(
            subject=self.object, objpath=self.objpath, attrgetter=self.get_attr,
            inherit_docstrings=False,
        ).values())

    def _document_magic(self, magic: Any, magic_type: str) -> None:
        lines: List[str] = []

        # Usage
        usage = magic.parser.format_usage().lstrip('::').strip()
        usage = ' '.join(line.strip() for line in usage.splitlines())
        lines.extend([f'.. {magic_type}magic:: {usage}', ''])

        # Description
        for line in magic.parser.description.strip().splitlines():
            clean_line = line.strip()
            lines.append((2 * ' ' if clean_line else '') + clean_line)

        # Arguments
        if actions := magic.parser._get_positional_actions():  # pylint: disable=protected-access
            lines.extend(['', 2 * ' ' + '.. describe:: Positional arguments:', ''])
            for action in actions:
                lines.extend([4 * ' ' + action.dest, 6 * ' ' + action.help])

        if actions := magic.parser._get_optional_actions():  # pylint: disable=protected-access
            lines.extend(['', 2 * ' ' + '.. describe:: Named arguments:', ''])
            for action in actions:
                lines.extend([4 * ' ' + ', '.join(action.option_strings), 6 * ' ' + action.help])

        # Add lines
        source = self.get_sourcename()
        for line in lines:
            self.add_line(line, source)

    def generate(self, *_args: Any, **_kwargs: Any) -> None:
        self.parse_name()
        self.import_object()

        members = self.get_object_members(want_all=True)[1]
        for magic_type in ['line', 'cell']:
            for member_name, member in members:
                if member_name in self.object.magics[magic_type]:
                    self._document_magic(magic=member, magic_type=magic_type)


def setup(app: Sphinx) -> None:
    app.add_autodocumenter(MagicsDocumenter)

    # Directives for magics
    class LineMagicDirective(domains.std.GenericObject):
        magic_prefix = '%'
        indextemplate = 'pair: %s; linemagic'

        def _object_hierarchy_parts(self, sig_node: addnodes.desc_signature) -> Tuple[str, ...]:
            name_index = sig_node.first_child_matching_class(addnodes.desc_name)
            name = cast(str, sig_node[name_index].rawsource)
            return (name, ) if name_index is not None else ()

        def _toc_entry_name(self, sig_node: addnodes.desc_signature) -> Any:
            if parts := sig_node.get('_toc_parts'):
                return cast(str, parts[-1])
            return ''

        @classmethod
        def parse_node(  # type: ignore[override]
            cls,
            env: BuildEnvironment,  # pylint: disable=unused-argument
            sig: str, signode: addnodes.desc_signature,
        ) -> str:
            if not (magic := re.search(r'%([\w_]+)(.*)', sig)):
                raise RuntimeError(f'Invalid magic command "{sig}"')
            name = magic.group(1)
            signode += addnodes.desc_sig_operator(cls.magic_prefix, cls.magic_prefix)
            signode += addnodes.desc_name(name, name)
            if arguments := magic.group(2).strip():
                signode += addnodes.desc_sig_space(' ', ' ')
                signode += addnodes.desc_sig_keyword(arguments, arguments)
            return name

    class CellMagicDirective(LineMagicDirective):
        magic_prefix = '%%'
        indextemplate = 'pair: %s; cellmagic'

    # Add magic directives and roles to the standard domain
    for magic_type, directive in {'line': LineMagicDirective, 'cell': CellMagicDirective}.items():
        role = f'{magic_type}magic'

        app.add_directive_to_domain(domain='std', name=role, cls=directive)
        app.add_role_to_domain(domain='std', name=role, role=XRefRole())

        object_types = app.registry.domain_object_types.setdefault('std', {})
        object_types[role] = domains.ObjType(role, role)
