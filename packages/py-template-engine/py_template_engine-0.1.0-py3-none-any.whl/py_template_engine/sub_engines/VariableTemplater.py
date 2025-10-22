import re
from functools import reduce

from py_template_engine.TemplaterInterface import TemplaterInterface


class VariableTemplater(TemplaterInterface):
    def render(self, template: str, **kwargs) -> str:
        return re.sub(
            r"{{(\w+(\.\w+)*)}}",
            lambda m: self.process(m.group(1).strip(), **kwargs),
            template,
        )

    def process(self, variable_name: str, **kwargs) -> str:
        return reduce(lambda acc, part: acc[part], variable_name.split("."), kwargs)
