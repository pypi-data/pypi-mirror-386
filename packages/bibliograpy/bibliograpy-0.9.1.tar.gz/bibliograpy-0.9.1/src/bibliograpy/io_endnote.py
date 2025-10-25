"""endnote I/O module."""

import json

from typing import TextIO

import yaml

from bibliograpy.api_core import InputFormat, OutputFormat, Format, Formats, OutputParams
from bibliograpy.api_endnote import Tags


class EndnoteInputFormat(InputFormat):
    """endnote input format implementation."""

    def __init__(self, source: Format):
        super().__init__(source=source, standard=Formats.ENDNOTE)

    def from_yml(self, i: TextIO):
        """Reads from yml representation."""
        return [{Tags.parse(str(k)): e[k] for k in e} for e in yaml.safe_load(i)]

    def from_json(self, i: TextIO):
        """Reads from json representation."""
        return [{Tags.parse(k): e[k] for k in e} for e in json.load(i)]

    def from_standard(self, i: TextIO) -> list[dict[Tags, str | list[str]]]:
        """Reads from standard format."""

        results: list[dict[Tags, str | list[str]]] = []

        result: dict[Tags, str | list[str]] = {}
        while line := i.readline():
            if line.strip() == '':
                if result:
                    results.append(result)
                    result = {}
                continue

            tag = Tags.parse(line[:2])

            if tag.repeating:
                if tag in result:
                    result[tag].append(line[3:].rstrip('\n\r'))
                else:
                    result[tag] = [line[3:].rstrip('\n\r')]
            else:
                result[tag] = line[3:].rstrip('\n\r')

        if result:
            results.append(result)
        return results


class EndnoteOutputFormat(OutputFormat):
    """endnote format implementation."""

    def __init__(self,
                 content: list[dict[Tags, str | list[str]]],
                 params: OutputParams):
        super().__init__(params=params, standard=Formats.ENDNOTE)
        self._content = content

    def to_yml(self, o: TextIO):
        """Writes to yml representation."""
        yaml.dump([{k.endnote_name(): e[k] for k in e} for e in self._content],
                  o,
                  sort_keys=False,
                  encoding='utf-8')

    def to_json(self, o: TextIO):
        """Writes to json representation."""
        json.dump([{k.endnote_name(): e[k] for k in e} for e in self._content],
                  fp=o,
                  sort_keys=False)

    def to_standard(self, o: TextIO):
        """Writes to standard format."""

        for bib_entry in self._content:

            for tag in bib_entry:

                if tag.repeating:
                    for l in bib_entry[tag]:
                        o.write(f'%{tag.endnote_name()} {l}\n')
                else:
                    o.write(f'%{tag.endnote_name()} {bib_entry[tag]}\n')

            o.write('\n')


    def to_py(self, o: TextIO):
        """Writes to python representation."""

        o.write('from bibliograpy.api_endnote import *\n\n')

        for bib_entry in self._content:

            o.write(f'{self._symbolizer.to_symbol(fmt=self.standard(), bib_entry=bib_entry)} = ')
            o.write('{\n')
            for e in bib_entry:
                if e.repeating:
                    o.write(f"  Tags.{e.name}: {bib_entry[e]},\n")
                else:
                    o.write(f"  Tags.{e.name}: '{bib_entry[e]}',\n")
            o.write('}\n')
