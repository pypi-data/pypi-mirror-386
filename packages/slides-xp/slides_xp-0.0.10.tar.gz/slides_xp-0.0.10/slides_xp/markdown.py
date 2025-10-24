"""
Render markdown as HTML
"""

from typing import cast

import mistune
import pygments.util
from pygments import highlight
from pygments.formatters import html
from pygments.lexers import get_lexer_by_name


# https://mistune.lepture.com/en/latest/guide.html#customize-renderer
class HighlightRenderer(mistune.HTMLRenderer):
    """
    Markdown render that adds code block highlights
    """

    def block_code(self, code, info=None):
        if info:
            try:
                lexer = get_lexer_by_name(info, stripall=True)
                formatter = html.HtmlFormatter()
                return highlight(code, lexer, formatter)
            except pygments.util.ClassNotFound:
                pass
        return "<pre><code>" + mistune.escape(code) + "</code></pre>"


markdown = mistune.create_markdown(renderer=HighlightRenderer())


def render_markdown(text: str) -> str:
    """
    Render markdown as HTML.
    """
    # We know it's a string, since we haven't set the renderer to None
    return cast(str, markdown(text))
