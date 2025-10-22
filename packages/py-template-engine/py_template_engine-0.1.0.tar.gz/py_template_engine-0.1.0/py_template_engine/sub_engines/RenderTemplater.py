import re

from py_template_engine.TemplaterInterface import TemplaterInterface


class RenderTemplater(TemplaterInterface):
    def render(self, template: str, **kwargs) -> str:
        return re.sub(
            r"{{#RENDER (.*?)}}",
            lambda m: self.process(m.group(1).strip(), **kwargs),
            template,
        )

    def process(self, render_path: str, **kwargs) -> str:
        # Import here to avoid circular import
        from py_template_engine.TemplateEngine import TemplateEngine

        return TemplateEngine(template_path=render_path).render(**kwargs)
