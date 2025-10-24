from __future__ import annotations

import io, json, sys
from collections.abc import Iterable, MutableSequence
from pathlib import Path
from subprocess import PIPE, run
from typing import TypeAlias, cast
from warnings import warn

import panflute as pf

from epijats import BiblioRefPool, dom, ref_list_from_csljson

from . import common
from .common import InlineContentConverter, MinitextElementConverter, Sink
from .metadata import convert_metadata


JsonData: TypeAlias = (
    None | str | int | float | list['JsonData'] | dict[str, 'JsonData']
)


class Converter(InlineContentConverter):
    def __init__(self, biblio: BiblioRefPool | None) -> None:
        self.biblio = biblio
        self._minitext = MinitextElementConverter(self)

    def link(self, link: pf.Link, dest: dom.MixedContent) -> None:
        sub: dom.MarkupElement
        if link.url.startswith("#"):
            sub = dom.CrossReference(link.url[1:])
        elif link.url.startswith("https:") or link.url.startswith("http:"):
            sub = dom.ExternalHyperlink(link.url)
        else:
            dest.append(dom.IssueElement(f"Invalid URL: {link.url}"))
        self.convert_content(link.content, sub.content)
        dest.append(sub)

    def cite(self, cite: pf.Cite, dest: dom.MixedContent) -> None:
        if not self.biblio:
            msg = "No bibliography provided for citations"
            dest.append(dom.IssueElement(msg))
        else:
            cite_tuple = dom.CitationTuple()
            for pd_cite in cite.citations:
                bp_cite = self.biblio.cite(pd_cite.id)
                if bp_cite:
                    cite_tuple.append(bp_cite)
                else:
                    msg = f"Reference '{pd_cite.id}' not found in bibliography"
                    dest.append(dom.IssueElement(msg))
            if len(cite_tuple):
                dest.append(cite_tuple)

    def inline(self, src: pf.Inline, dest: dom.MixedContent) -> None:
        if self._minitext.convert_element(src, dest):
            return
        elif isinstance(src, pf.Link):
            self.link(src, dest)
        elif isinstance(src, pf.Code):
            dest.append(dom.MarkupElement('tt', src.text))
        elif isinstance(src, pf.Cite):
            self.cite(src, dest)
        else:
            dest.append(dom.IssueElement(repr(src)))

    def convert_content(
        self, content: Iterable[pf.Inline], dest: dom.MixedContent
    ) -> None:
        todo = list(content)
        behind = todo.pop(0) if len(todo) else None
        for ahead in todo:
            if isinstance(behind, (pf.Space, pf.SoftBreak)):
                if isinstance(ahead, pf.Cite):
                    behind = None
            if behind is not None:
                self.inline(behind, dest)
            behind = ahead
        if behind is not None:
            self.inline(behind, dest)

    def block(self, block: pf.Block, sink: Sink[dom.Element]) -> bool:
        if isinstance(block, pf.Para):
            para = dom.Paragraph()
            self.convert_content(block.content, para.content)
            sink(para)
        elif isinstance(block, pf.Plain):
            tb = dom.MarkupBlock()
            self.convert_content(block.content, tb.content)
            sink(tb)
        elif isinstance(block, pf.BlockQuote):
            bq = dom.BlockQuote()
            self.nonsection_blocks(block.content, bq.content.append)
            sink(bq)
        elif isinstance(block, pf.CodeBlock):
            pre = dom.PreElement()
            pre.content.append_text(block.text)
            sink(pre)
        elif isinstance(block, pf.BulletList):
            ul = dom.ItemElement('ul')
            for item in block.content:
                li = dom.ItemElement('li')
                self.nonsection_blocks(item.content, li.content.append)
                ul.content.append(li)
            sink(ul)
        elif isinstance(block, pf.OrderedList):
            ul = dom.ItemElement('ol')
            for item in block.content:
                li = dom.ItemElement('li')
                self.nonsection_blocks(item.content, li.content.append)
                ul.content.append(li)
            sink(ul)
        elif isinstance(block, pf.RawBlock):
            pass
        else:
            return False
        return True

    def nonsection_blocks(
        self, content: Iterable[pf.Block], sink: Sink[dom.Element]
    ) -> None:
        for block in content:
            if self.block(block, sink):
                msg = None
            elif isinstance(block, pf.Header):
                msg = "Header in non-section content"
            else:
                msg = repr(block)
            if msg:
                sink(dom.IssueElement(msg))

    def presection_content(
        self, src: MutableSequence[pf.Block], sink: Sink[dom.Element]
    ) -> pf.Header | None:
        while src:
            block = src.pop(0)
            if isinstance(block, pf.Header):
                return block
            if not self.block(block, sink):
                sink(dom.IssueElement(repr(block)))
        return None

    def section_content(
        self, level: int, content: MutableSequence[pf.Block], dest: dom.ProtoSection
    ) -> pf.Header | None:
        header = self.presection_content(content, dest.presection.append)
        while header and header.level >= level:
            title = dom.MixedContent()
            self.convert_content(header.content, title)
            subsection = dom.Section(header.identifier or None, title)
            header = self.section_content(header.level + 1, content, subsection)
            dest.subsections.append(subsection)
        return header


def convert_bibliography(metalist: pf.MetaValue | None) -> BiblioRefPool | None:
    if metalist is None:
        return None
    if not isinstance(metalist, pf.MetaList):
        warn("Expecting bibliography to be of pandoc MetaList type")
        return None
    sources = []
    for s in metalist.content:
        if isinstance(s, pf.MetaString):
            sources.append(Path(s.text))
        elif isinstance(s, pf.MetaInlines):
            sources.append(Path(common.convert_string(s.content)))
        else:
            warn(
                "Expecting bibliography entries to be of "
                "pandoc MetaString or MetaInlines types"
            )
    ref_list = ref_list_from_csljson(csljson_from_bibliography(sources))
    return BiblioRefPool(ref_list.references) if ref_list else None


def baseprint_from_pandoc_ast(doc: pf.Doc) -> dom.Article:
    ret = dom.Article()
    convert_metadata(doc.metadata, ret)
    biblio = convert_bibliography(doc.metadata.content.get('bibliography'))
    convert = Converter(biblio)
    abstract = doc.metadata.content.get('abstract')
    if isinstance(abstract, pf.MetaBlocks):
        ret.abstract = dom.Abstract()
        convert.nonsection_blocks(abstract.content, ret.abstract.blocks.append)
    convert.section_content(1, doc.content, ret.body)
    if biblio and len(biblio.used):
        ret.ref_list = dom.BiblioRefList(biblio.used)
    return ret


def csljson_from_bibliography(sources: Iterable[Path]) -> JsonData:
    args = [str(s) for s in sources]
    if not args:
        warn("Expecting pandoc to find bibliography files")
        return []
    cmd = ["pandoc", "--to", "csljson"] + args
    result = run(cmd, stdout=PIPE, stderr=sys.stderr, encoding="utf-8")
    if result.returncode:
        raise RuntimeError("Error with command: " + " ".join(cmd))
    try:
        return cast(JsonData, json.loads(result.stdout))
    except json.JSONDecodeError as ex:
        raise RuntimeError(f"Pandoc command returned invalid JSON: {ex}")


def baseprint_from_pandoc_inputs(
    sources: Iterable[Path], defaults: Iterable[Path]
) -> dom.Article:
    cmd = ["pandoc"]
    cmd += [str(s) for s in sources]
    for d in defaults:
        cmd += ["-d", str(d)]
    cmd += ["--to", "json"]
    result = run(cmd, stdout=PIPE, stderr=sys.stderr, encoding="utf-8")
    if result.returncode:
        raise RuntimeError("Error with command: " + " ".join(cmd))
    try:
        doc = pf.load(io.StringIO(result.stdout))
        return baseprint_from_pandoc_ast(doc)
    except json.JSONDecodeError as ex:
        raise RuntimeError(f"Pandoc command returned invalid JSON: {ex}")
