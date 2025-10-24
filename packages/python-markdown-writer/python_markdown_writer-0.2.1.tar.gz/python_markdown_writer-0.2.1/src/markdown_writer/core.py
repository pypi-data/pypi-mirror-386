"""A simple Markdown writer in Python."""

class MarkdownWriter:
    def __init__(self, document: str = ""):
        self.document = document

    def text(self, content: str):
        self.document += content + "\n\n"
    
    def h1(self, content: str):
        self.document += f"# {content}\n\n"

    def h2(self, content: str):
        self.document += f"## {content}\n\n"

    def h3(self, content: str):
        self.document += f"### {content}\n\n"

    def h4(self, content: str):
        self.document += f"#### {content}\n\n"

    def h5(self, content: str):
        self.document += f"##### {content}\n\n"

    def list(self, items: list):
        for item in items:
            self.document += f"- {str(item)}\n"
        self.document += "\n"

    def hyperlink(self, text: str, url: str):
        self.document += f"[{text}]({url})\n\n"

    def list(self, items: list, level: int = 1):
        for item in items:
            self.document += f"{'  ' * (level - 1)}- {str(item)}\n"
        self.document += "\n"

    def numbered_list(self, items: list):
        for index, item in enumerate(items, start=1):
            self.document += f"{index}. {str(item)}\n"
        self.document += "\n"
    
    def nested_list_from_dict(self, d: dict):
        def _add_items(d: dict, level: int):
            for key, value in d.items():
                self.document += f"{'  ' * (level - 1)}- {str(key)}\n"
                if isinstance(value, dict):
                    _add_items(value, level + 1)
                elif isinstance(value, list):
                    for item in value:
                        self.document += f"{'  ' * level}- {str(item)}\n"
                else:
                    self.document += f"{'  ' * level}- {str(value)}\n"

        _add_items(d, 1)
        self.document += "\n"
    
    def code_block(self, code: str, language: str = "", remove_indent: int = 0):
        if remove_indent:
            code = "\n".join(line[remove_indent:] for line in code.split("\n"))
        self.document += f"```{language}\n{code.strip()}\n```\n\n"

    def image(self, alt_text: str, url: str):
        self.document += f"![{alt_text}]({url})\n\n"

    def bold(self, content: str):
        return f"**{content}**"

    def italic(self, content: str):
        return f"*{content}*"

    def table_from_pandas(self, df, index=False):
        """Converts DataFrame to Markdown table"""
        self.document += df.to_markdown(index=index) + "\n\n"

    def to_html(self):
        raise NotImplementedError("HTML conversion is not implemented yet.")

    def save(self, filename: str):
        with open(filename, 'w') as file:
            file.write(self.document)
