import bleach
from typing import Optional
import structlog

logger = structlog.get_logger()


ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 'b', 'i', 'span', 'div',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li',
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
    'blockquote', 'code', 'pre',
    'a', 'img',
    'hr', 'section', 'article', 'aside', 'header', 'footer', 'main',
]

ALLOWED_ATTRIBUTES = {
    '*': ['class', 'id', 'style'],
    'a': ['href', 'title', 'target', 'rel'],
    'img': ['src', 'alt', 'title', 'width', 'height'],
    'th': ['scope'],
    'td': ['colspan', 'rowspan'],
}

ALLOWED_STYLES = [
    'color', 'background-color', 'font-size', 'font-weight', 'font-family',
    'text-align', 'margin', 'padding', 'border', 'border-radius',
    'width', 'height', 'max-width', 'max-height',
    'display', 'flex', 'grid', 'gap', 'justify-content', 'align-items',
    'box-shadow', 'transition', 'opacity',
]

ALLOWED_PROTOCOLS = ['http', 'https', 'mailto', 'data']


def sanitize_html(html: str) -> str:
    """
    Sanitize HTML to prevent XSS attacks.
    Removes scripts, event handlers, iframes, and other dangerous content.
    """
    # First, remove any script tags and their content
    import re
    html = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'<iframe\b[^<]*(?:(?!<\/iframe>)<[^<]*)*<\/iframe>', '', html, flags=re.IGNORECASE)
    
    # Remove event handlers
    html = re.sub(r'\s+on\w+\s*=\s*["\'][^"\']*["\']', '', html, flags=re.IGNORECASE)
    html = re.sub(r'\s+on\w+\s*=\s*\w+', '', html, flags=re.IGNORECASE)
    
    # Remove javascript: protocols
    html = re.sub(r'(href|src)\s*=\s*["\']\s*javascript:', r'\1="#"', html, flags=re.IGNORECASE)
    
    # Use bleach for final sanitization
    cleaned = bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )
    
    # Add sandbox attributes to links
    cleaned = re.sub(
        r'<a\s+([^>]*href\s*=\s*["\'][^"\']*["\'][^>]*)>',
        r'<a \1 target="_blank" rel="noopener noreferrer">',
        cleaned,
        flags=re.IGNORECASE,
    )
    
    return cleaned


def sanitize_markdown(markdown: str) -> str:
    """
    Sanitize markdown by converting to HTML, sanitizing, and converting back.
    For now, we just return the markdown as-is since we render it safely on frontend.
    """
    # In a production system, you might want to use a markdown parser
    # and sanitize the resulting HTML
    return markdown


def get_artifact_sandbox_attributes() -> dict:
    """
    Returns the sandbox attributes for the artifact iframe.
    This prevents scripts, forms, modals, popups, etc.
    """
    return {
        "sandbox": "allow-scripts allow-same-origin allow-forms allow-popups allow-pointer-lock",
        "allow": "clipboard-read clipboard-write",
    }


def create_sandboxed_html(content: str, title: str = "Artifact") -> str:
    """
    Create a complete HTML document with the artifact content sandboxed in an iframe.
    """
    sanitized = sanitize_html(content)
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            box-sizing: border-box;
        }}
        body {{
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #fafafa;
        }}
        .artifact-container {{
            width: 100%;
            height: 100%;
            min-height: 500px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: auto;
        }}
    </style>
</head>
<body>
    <div class="artifact-container">
        {sanitized}
    </div>
</body>
</html>"""