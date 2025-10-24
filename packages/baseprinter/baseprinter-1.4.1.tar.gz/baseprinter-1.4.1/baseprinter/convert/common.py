from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Protocol, TypeAlias, TypeVar
from warnings import warn

import panflute as pf

from epijats import dom
from epijats.dom import MixedContent


SinkableT = TypeVar('SinkableT')
Sink: TypeAlias = Callable[[SinkableT], None]


def convert_string(content: Iterable[pf.Inline]) -> str:
    strs = []
    for inline in content:
        if isinstance(inline, (pf.Space, pf.SoftBreak)):
            strs.append(" ")
        elif isinstance(inline, pf.Str):
            strs.append(inline.text)
    return "".join(strs)


def get_meta_map_str(meta: pf.MetaMap, key: str) -> str | None:
    value = meta.get(key)
    if value is None:
        return None
    if isinstance(value, pf.MetaString):
        return value.text
    elif isinstance(value, pf.MetaInlines):
        return convert_string(value.content)
    else:
        warn(f"Expecting {key}: to have string value")
        return None


class InlineElementConverter(Protocol):
    def convert_element(self, src: pf.Inline, dest: MixedContent, /) -> bool: ...


class InlineContentConverter(Protocol):
    def convert_content(
        self, src: Iterable[pf.Inline], dest: MixedContent, /
    ) -> None: ...


def convert_markup(
    tag: str,
    content: Iterable[pf.Inline],
    converter: InlineContentConverter,
    dest: MixedContent,
) -> None:
    sub = dom.MarkupElement(tag)
    converter.convert_content(content, sub.content)
    dest.append(sub)


class MinitextElementConverter(InlineElementConverter):
    def __init__(self, content: InlineContentConverter):
        self.content = content

    def convert_element(self, src: pf.Inline, dest: MixedContent) -> bool:
        if isinstance(src, pf.Space):
            dest.append_text(" ")
        elif isinstance(src, pf.SoftBreak):
            dest.append_text("\n")
        elif isinstance(src, pf.Str):
            dest.append_text(src.text)
        elif isinstance(src, pf.Quoted):
            dest.append_text('“' if src.quote_type == 'DoubleQuote' else "‘")
            self.content.convert_content(src.content, dest)
            dest.append_text('”' if src.quote_type == 'DoubleQuote' else "’")
        elif isinstance(src, pf.Strong):
            convert_markup('b', src.content, self.content, dest)
        elif isinstance(src, pf.Emph):
            convert_markup('i', src.content, self.content, dest)
        elif isinstance(src, pf.Subscript):
            convert_markup('sub', src.content, self.content, dest)
        elif isinstance(src, pf.Superscript):
            convert_markup('sup', src.content, self.content, dest)
        elif isinstance(src, pf.RawInline):
            pass
        else:
            return False
        return True


class MinitextConverter(MinitextElementConverter, InlineContentConverter):
    def __init__(self) -> None:
        super().__init__(self)

    def convert_content(self, src: Iterable[pf.Inline], dest: MixedContent, /) -> None:
        for inline in src:
            if not self.convert_element(inline, dest):
                msg = f"This markup context does not permit: {inline}"
                dest.append(dom.IssueElement(msg))
        return None


def convert_minitext(meta: pf.MetaValue | None, dest: MixedContent) -> None:
    if isinstance(meta, pf.MetaString):
        dest.append_text(meta.text)
    elif isinstance(meta, pf.MetaInlines):
        MinitextConverter().convert_content(meta.content, dest)
