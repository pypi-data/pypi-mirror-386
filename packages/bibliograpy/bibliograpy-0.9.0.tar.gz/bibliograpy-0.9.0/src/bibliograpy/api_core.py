"""Core management of reference decorators."""
import inspect
from dataclasses import dataclass
from enum import Enum
from typing import TextIO, Any


@dataclass(frozen=True)
class Format:
    """A format representation."""
    title: str | None
    command: str | None
    io_extension: list[str]

class Formats(Format, Enum):
    """Supported bibliography formats."""
    BIBTEX = ('Bibtex', 'bibtex', ['bib', 'bibtex'])
    RIS2001 = ('RIS (2001)', 'ris2001', ['ris'])
    RIS2011 = ('RIS (2011)', 'ris2011', ['ris'])
    REFER = ('refer', 'refer', ['refer'])
    ENDNOTE = ('Endnote', 'endnote', ['enw'])
    PUBMED = ('PubMed', 'pubmed', ['nbib', 'txt'])
    YML = (None, None, ['yml', 'yaml'])
    JSON = (None, None, ['json'])
    PYTHON = (None, None, ['py'])

    @staticmethod
    def as_command(format_id: str):
        """Gets a supported format enum instance from a supported process argument string."""
        for f in Formats:
            if format_id == f.command:
                return f
        raise ValueError(f'unexpected format {format_id}')

    def as_io_extension(self, format_id: str):
        """Gets a supported format enum instance from a supported process argument string."""
        for f in Formats:
            if f.command is None and format_id in f.io_extension:
                return f

        if format_id in self.io_extension:
            return self

        raise ValueError(f'unexpected format {format_id}')


class InputFormat:
    """InputFormat interface to deserialize a bibliography."""

    def __init__(self, source: Format, standard: Format):
        self._source = source
        self._standard = standard

    def from_yml(self, i: TextIO):
        """Reads from yml representation."""

    def from_json(self, i: TextIO):
        """Reads from json representation."""

    def from_standard(self, i: TextIO):
        """Reads from standard format."""

    def source(self) -> Format:
        """The source format."""
        return self._source

    def standard(self) -> Format:
        """The standard format."""
        return self._standard

    def read(self, i: TextIO):
        """Deserialization method."""
        if self.source() is Formats.YML:
            return self.from_yml(i)
        if self.source() is Formats.JSON:
            return self.from_json(i)
        if self.source() is self.standard():
            return self.from_standard(i)

        raise ValueError(f'unsupported configuration format {self.source()}')

class Symbolizer:
    """Builds a Python symbol for a given entry in a given format."""

    def to_symbol(self, fmt: Format, bib_entry) -> str:
        """Produces a python symbol from a bibliographical reference entry."""


@dataclass
class OutputParams:
    """Output stream params."""
    target: Formats
    symbolizer: Symbolizer

class OutputFormat:
    """Output format to serialize a bibliography."""

    def __init__(self, params: OutputParams, standard: Format):
        self._target = params.target
        self._symbolizer = params.symbolizer
        self._standard = standard

    def to_yml(self, o: TextIO):
        """Writes to yml representation."""

    def to_json(self, o: TextIO):
        """Writes to json representation."""

    def to_standard(self, o: TextIO):
        """Writes to standard format."""

    def to_py(self, o: TextIO):
        """Writes to python representation."""

    def target(self):
        """The file extension."""
        return self._target

    def standard(self) -> Format:
        """The standard format."""
        return self._standard

    def write(self, o: TextIO):
        """Serialization method."""
        if self.target() is Formats.YML:
            return self.to_yml(o)
        if self.target() is Formats.JSON:
            return self.to_json(o)
        if self.target() is Formats.PYTHON:
            return self.to_py(o)
        if self.target() is self.standard():
            return self.to_standard(o)

        raise ValueError(f'unsupported configuration format {self.target()}')


class CitationRenderer:
    """A builder of reference renderers:

    1. the function, class and symbol decorator
    2. the function to invoque at module loading
    """

    def format(self, refs: list) -> str:
        """Formats a citation list.

        Args:
            *refs: a list of bibliographical reference symbols

        Returns: a string rendering the list of the input reference symbols
        """

    def _doc_core(self, doc: str, *refs: Any | list) -> str:
        """Manages the documentation modification in various use cases:

        1. If the documentation is None, inits it to an empty string.
        2. Then, handles the cases the refs are a single instance, a list or a varargs of bibliographical symbols.

        Args:
            *refs (Any | list): a series of bibliographical reference symbols
        """
        if doc is None:
            doc = ''

        if len(refs) == 1:
            ref0 = refs[0]
            if isinstance(ref0, list):
                doc += self.format(ref0)
            else:
                doc += self.format([ref0])
        else:
            doc += self.format([*refs])

        return doc

    def cite_module(self, *refs: Any | list) -> None:
        """The bibliographical reference function to invoque at module loading to add a reference rendering to its
        documentation.

        Args:
            *refs (Any | list): a series of bibliographical reference symbols
        """
        frm = inspect.stack()[1]
        mod = inspect.getmodule(frm[0])
        mod.__doc__ = self._doc_core(mod.__doc__, *refs)

    def decorator(self, *refs: Any) -> "Returns a function to handle a function, a class or a method.":
        """The bibliographical reference decorator to use for functions, classes and methods.

        Args:
            *refs (Any | list[Any]): a series of bibliographical reference symbols

        Returns: a function to handle a function, a class or a method documentation which to render the bibliographical
        references into
        """

        def internal(obj):
            """
            Renders the bibliographical references given to the decorator into the parameter documentation.

            Args:
                obj: a function, a class or a method which documentation has to be added in

            Returns: the very input function, class or method
            """
            obj.__doc__ = self._doc_core(obj.__doc__, *refs)
            return obj

        return internal
