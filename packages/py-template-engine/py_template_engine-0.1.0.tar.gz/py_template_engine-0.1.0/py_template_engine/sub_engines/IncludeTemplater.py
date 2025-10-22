import re

from py_template_engine.TemplaterInterface import TemplaterInterface


class IncludeTemplater(TemplaterInterface):
    def render(self, template: str, **kwargs) -> str:
        return re.sub(
            r"{{#INCLUDE (.*?)}}",
            lambda m: self.process(m.group(1).strip(), **kwargs),
            template,
        )

    def process(self, include_path: str, **kwargs) -> str:
        with open(kwargs[include_path], "r") as file:
            return file.read()
