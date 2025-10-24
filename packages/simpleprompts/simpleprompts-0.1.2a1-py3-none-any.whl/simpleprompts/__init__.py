from typing import Literal


class Prompt:
    def __init__(self, *sections):
        self.sections = sections

    def render(self, format: Literal["xml", "markdown"]):
        return "\n\n".join(
            str(s) if not isinstance(s, Section) else s.render_section(format=format)
            for s in self.sections
        )


class Section:
    def __init__(self, name):
        self.name = name
        self.indent_spaces = 0
        self._format = None
        self._content = []

    def __call__(self, *content):
        self._content = content
        return self

    @staticmethod
    def _indent(str: str, amount=0):
        split_str = str.split("\n")
        joined_str = "\n".join([" " * amount + s for s in split_str])
        return joined_str

    def indent(self, num_spaces: int):
        self.indent_spaces += num_spaces
        return self

    def format(self, format: Literal["xml", "markdown"] = "xml"):
        self._format = format
        return self

    def content(self, *content):
        self._content = content
        return self

    def render_section(
        self, depth: int = 0, format: Literal["xml", "markdown"] = "xml"
    ):
        format_to_use = self._format or format
        if not self._content:
            return ""
        if format_to_use == "xml":
            s = f"<{self.name}>\n"
        else:
            s = f"{'#' * (depth + 1)} {self.name}\n"
        for c in self._content:
            if isinstance(c, Section):
                s += c.render_section(depth=depth + 1, format=format) + "\n"
            elif c is None or c is False:
                pass
            else:
                s += str(c) + "\n"
        s = s.rstrip()
        if format_to_use == "xml":
            s += f"\n</{self.name}>\n"
        return self._indent(s.strip(), self.indent_spaces)


class SectionBuilder:
    def __getattr__(self, name):
        return Section(name)

    def __call__(self, name):
        return Section(name)


p = SectionBuilder()


__all__ = ["p", "Prompt"]
