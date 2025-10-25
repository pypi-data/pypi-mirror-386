from beekeeper.core.prompts.utils import SafeFormatter
from pydantic import BaseModel


class PromptTemplate(BaseModel):
    """
    Prompt Template.

    Attributes:
        template (str): Prompt template string.

    Example:
        ```python
        from beekeeper.core.prompts import PromptTemplate

        PromptTemplate("Summarize the following text: {input_text}")
        ```
    """

    template: str

    def __init__(self, template: str):
        super().__init__(template=template)

    def format(self, **kwargs):
        """
        Formats the template using the provided dynamic variables.
        Missing variables are left as placeholders.
        """
        return self.template.format_map(SafeFormatter(**kwargs))
