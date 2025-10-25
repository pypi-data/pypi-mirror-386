"""
bibliograpy process module
"""
import importlib
import logging
from argparse import Namespace
from dataclasses import dataclass
from pathlib import Path

from bibliograpy.api_core import Formats, OutputParams
from bibliograpy.io_bibtex import BibtexInputFormat, BibtexOutputFormat
from bibliograpy.io_pubmed import PubmedInputFormat, PubmedOutputFormat
from bibliograpy.io_refer import ReferInputFormat, ReferOutputFormat
from bibliograpy.io_ris2001 import Ris2001InputFormat, Ris2001OutputFormat
from bibliograpy.io_ris2011 import Ris2011InputFormat, Ris2011OutputFormat
from bibliograpy.io_endnote import EndnoteInputFormat, EndnoteOutputFormat
from bibliograpy.api_core import Symbolizer
from bibliograpy.default_symbolizer import DefaultSymbolizer

LOG = logging.getLogger(__name__)


@dataclass(frozen=True)
class _Params:
    ns: Namespace

    def source(self) -> Formats:
        """Gets the input data format."""
        return self.format().as_io_extension(self.ns.file.split('.')[-1])

    def output(self) -> Path:
        """Gets the output file path."""
        return Path(Path.cwd()) / self.ns.output_dir / self.ns.output_file

    def target(self) -> Formats:
        """Gets the output data format."""
        return self.format().as_io_extension(self.ns.output_file.split('.')[-1])

    def scope_symbol(self) -> str | None:
        """Gets the bibtex scope symbol."""
        if 'shared_scope' in self.ns and self.ns.shared_scope:
            return 'SHARED_SCOPE'
        return self.ns.scope if 'scope' in self.ns else None

    def init_scope(self) -> str:
        """Get the bibtex scope initialisation expression value."""
        return self.ns.init_scope

    def file(self) -> str:
        """Gets the input file path string."""
        return self.ns.file

    def encoding(self) -> str:
        """Gets the I/O encoding."""
        return self.ns.encoding

    def format(self) -> Formats:
        """Gets the processing format."""
        return Formats.as_command(self.ns.CMD)

    def symbolizer(self) -> Symbolizer:
        """Computes and gets the python helper for python symbol definition."""
        if 'symbolizer' in self.ns and self.ns.symbolizer:
            p = self.ns.symbolizer.split(':')
            module_name = p[0]
            class_name = p[1] if len(p) > 1 else 'Symbolizer'
            return vars(importlib.import_module(module_name))[class_name]()

        return DefaultSymbolizer.default()

    def to_output_params(self) -> OutputParams:
        """Builds output parameters."""
        return OutputParams(target=self.target(), symbolizer=self.symbolizer())

def _process(ns: Namespace):
    """config
    """
    LOG.info("dependencies")

    params = _Params(ns=ns)

    LOG.info('open configuration file %s', ns.file)

    if params.format() is Formats.BIBTEX:
        _process_bibtex(params=params)

    elif params.format() is Formats.RIS2001:
        _process_ris2001(params=params)

    elif params.format() is Formats.RIS2011:
        _process_ris2011(params=params)

    elif params.format() is Formats.REFER:
        _process_refer(params=params)

    elif params.format() is Formats.ENDNOTE:
        _process_endnote(params=params)

    elif params.format() is Formats.PUBMED:
        _process_pubmed(params=params)
    else:
        raise ValueError(f'unsupported format {format}')


def _process_bibtex(params: _Params) -> None:
    """Bibtex processing."""
    iformat = BibtexInputFormat(source=params.source())
    with open(params.file(), encoding=params.encoding()) as i:
        content = iformat.read(i)
        oformat = BibtexOutputFormat(content=content,
                                     params=params.to_output_params(),
                                     scope_symbol=params.scope_symbol(),
                                     init_scope=params.init_scope())
        with open(params.output(), 'w', encoding=params.encoding()) as o:
            oformat.write(o)

def _process_ris2001(params: _Params) -> None:
    """RIS 2001 processing."""
    iformat = Ris2001InputFormat(source=params.source())
    with open(params.file(), encoding=params.encoding()) as i:
        content = iformat.read(i)
        oformat = Ris2001OutputFormat(content=content, params=params.to_output_params())
        with open(params.output(), 'w', encoding=params.encoding()) as o:
            oformat.write(o)

def _process_ris2011(params: _Params) -> None:
    """RIS 2011 processing."""
    iformat = Ris2011InputFormat(source=params.source())
    with open(params.file(), encoding=params.encoding()) as i:
        content = iformat.read(i)
        oformat = Ris2011OutputFormat(content=content, params=params.to_output_params())
        with open(params.output(), 'w', encoding=params.encoding()) as o:
            oformat.write(o)

def _process_refer(params: _Params) -> None:
    """Refer processing."""
    iformat = ReferInputFormat(source=params.source())
    with open(params.file(), encoding=params.encoding()) as i:
        content = iformat.read(i)
        oformat = ReferOutputFormat(content=content, params=params.to_output_params())
        with open(params.output(), 'w', encoding=params.encoding()) as o:
            oformat.write(o)

def _process_endnote(params: _Params) -> None:
    """Endnote processing."""
    iformat = EndnoteInputFormat(source=params.source())
    with open(params.file(), encoding=params.encoding()) as i:
        content = iformat.read(i)
        oformat = EndnoteOutputFormat(content=content, params=params.to_output_params())
        with open(params.output(), 'w', encoding=params.encoding()) as o:
            oformat.write(o)

def _process_pubmed(params: _Params) -> None:
    """PubMed processing."""
    iformat = PubmedInputFormat(source=params.source())
    with open(params.file(), encoding=params.encoding()) as i:
        content = iformat.read(i)
        oformat = PubmedOutputFormat(content=content, params=params.to_output_params())
        with open(params.output(), 'w', encoding=params.encoding()) as o:
            oformat.write(o)
