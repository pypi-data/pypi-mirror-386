"""
Typst translator for docutils nodes.

This module implements the TypstTranslator class, which translates docutils
nodes to Typst markup.
"""

import re
from typing import Any, Optional

from docutils import nodes
from sphinx import addnodes
from sphinx.util import logging
from sphinx.util.docutils import SphinxTranslator

logger = logging.getLogger(__name__)


class TypstTranslator(SphinxTranslator):
    """
    Translator class that converts docutils nodes to Typst markup.

    This translator visits nodes in the document tree and generates
    corresponding Typst markup.
    """

    def __init__(self, document: nodes.document, builder: Any) -> None:
        """
        Initialize the translator.

        Args:
            document: The docutils document to translate
            builder: The Sphinx builder instance
        """
        super().__init__(document, builder)
        self.builder = builder
        self.body = []

        # State management variables
        self.section_level = 0
        self.in_figure = False
        self.in_table = False
        self.in_caption = False
        self.list_stack = []  # Track list nesting: 'bullet' or 'enumerated'

        # Figure-specific state
        self.figure_content = []
        self.figure_caption = ""

        # Code block container state (Issue #20)
        self.in_captioned_code_block = False
        self.code_block_caption = ""
        self.code_block_label = ""

    def astext(self) -> str:
        """
        Return the translated text as a string.

        Returns:
            The translated Typst markup
        """
        return "".join(self.body)

    def add_text(self, text: str) -> None:
        """
        Add text to the output body or table cell content.

        Args:
            text: The text to add
        """
        if (
            hasattr(self, "in_table")
            and self.in_table
            and hasattr(self, "table_cell_content")
        ):
            self.table_cell_content.append(text)
        else:
            self.body.append(text)

    def visit_document(self, node: nodes.document) -> None:
        """
        Visit a document node.

        Args:
            node: The document node
        """
        # Document root doesn't need special markup
        pass

    def depart_document(self, node: nodes.document) -> None:
        """
        Depart a document node.

        Args:
            node: The document node
        """
        # Document root doesn't need closing
        pass

    def visit_section(self, node: nodes.section) -> None:
        """
        Visit a section node.

        Args:
            node: The section node
        """
        # Increment section level
        self.section_level += 1

    def depart_section(self, node: nodes.section) -> None:
        """
        Depart a section node.

        Args:
            node: The section node
        """
        # Decrement section level
        self.section_level -= 1
        # Add a newline after sections
        self.add_text("\n")

    def visit_title(self, node: nodes.title) -> None:
        """
        Visit a title node.

        Args:
            node: The title node
        """
        # Typst heading syntax: = Title, == Title, === Title, etc.
        # Use section_level to determine heading level
        heading_prefix = "=" * self.section_level
        self.add_text(f"{heading_prefix} ")

    def depart_title(self, node: nodes.title) -> None:
        """
        Depart a title node.

        Args:
            node: The title node
        """
        self.add_text("\n\n")

    def visit_subtitle(self, node: nodes.subtitle) -> None:
        """
        Visit a subtitle node.

        Args:
            node: The subtitle node
        """
        # Typst subtitle syntax: use emphasized text for subtitle
        self.add_text("_")

    def depart_subtitle(self, node: nodes.subtitle) -> None:
        """
        Depart a subtitle node.

        Args:
            node: The subtitle node
        """
        self.add_text("_\n\n")

    def visit_compound(self, node: nodes.compound) -> None:
        """
        Visit a compound node.

        Compound nodes are containers that group related content.
        They are often used to wrap toctree directives.

        Args:
            node: The compound node
        """
        # Compound nodes are just containers, process their children
        pass

    def depart_compound(self, node: nodes.compound) -> None:
        """
        Depart a compound node.

        Args:
            node: The compound node
        """
        pass

    def visit_container(self, node: nodes.container) -> None:
        """
        Visit a container node.

        Handle Sphinx-generated containers, particularly literal-block-wrapper
        for captioned code blocks (Issue #20).

        Args:
            node: The container node
        """
        # Check if this is a literal-block-wrapper (captioned code block)
        if "literal-block-wrapper" in node.get("classes", []):
            self.in_captioned_code_block = True
            # Caption and literal_block children will be processed separately
            # We need to extract caption text first
            for child in node.children:
                if isinstance(child, nodes.caption):
                    self.code_block_caption = child.astext()
                elif isinstance(child, nodes.literal_block):
                    # Extract label from :name: option
                    if child.get("names"):
                        self.code_block_label = child.get("names")[0]
        # Other container types: just process children
        pass

    def depart_container(self, node: nodes.container) -> None:
        """
        Depart a container node.

        Args:
            node: The container node
        """
        # Reset state after literal-block-wrapper
        if "literal-block-wrapper" in node.get("classes", []):
            self.in_captioned_code_block = False
            self.code_block_caption = ""
            self.code_block_label = ""

    def visit_paragraph(self, node: nodes.paragraph) -> None:
        """
        Visit a paragraph node.

        Args:
            node: The paragraph node
        """
        # Paragraphs don't need special markup in Typst
        pass

    def depart_paragraph(self, node: nodes.paragraph) -> None:
        """
        Depart a paragraph node.

        Args:
            node: The paragraph node
        """
        # Add double newline after paragraphs
        self.add_text("\n\n")

    def visit_comment(self, node: nodes.comment) -> None:
        """
        Visit a comment node.

        Comments are skipped entirely in Typst output as they are meant
        for source-level documentation only.

        Args:
            node: The comment node

        Raises:
            nodes.SkipNode: Always raised to skip the comment
        """
        raise nodes.SkipNode

    def depart_comment(self, node: nodes.comment) -> None:
        """
        Depart a comment node.

        Args:
            node: The comment node

        Note:
            This method is not called when SkipNode is raised in visit_comment.
        """
        pass

    def visit_raw(self, node: nodes.raw) -> None:
        """
        Visit a raw node.

        Pass through content if format is 'typst', otherwise skip.

        Args:
            node: The raw node

        Raises:
            nodes.SkipNode: When format is not 'typst'
        """
        format_name = node.get("format", "").lower()

        if format_name == "typst":
            # Output the raw Typst content directly
            content = node.astext()
            if content:  # Only add non-empty content
                self.add_text(content)
                self.add_text("\n\n")
            raise nodes.SkipNode
        else:
            # Skip content for other formats
            logger.debug(f"Skipping raw node with format: {format_name}")
            raise nodes.SkipNode

    def depart_raw(self, node: nodes.raw) -> None:
        """
        Depart a raw node.

        Args:
            node: The raw node

        Note:
            This method is not called when SkipNode is raised in visit_raw.
        """
        pass

    def visit_Text(self, node: nodes.Text) -> None:
        """
        Visit a text node.

        Args:
            node: The text node
        """
        # Add the text content
        self.add_text(node.astext())

    def depart_Text(self, node: nodes.Text) -> None:
        """
        Depart a text node.

        Args:
            node: The text node
        """
        # Text nodes don't need closing
        pass

    def visit_emphasis(self, node: nodes.emphasis) -> None:
        """
        Visit an emphasis (italic) node.

        Args:
            node: The emphasis node
        """
        # Typst italic syntax: _text_
        self.add_text("_")

    def depart_emphasis(self, node: nodes.emphasis) -> None:
        """
        Depart an emphasis (italic) node.

        Args:
            node: The emphasis node
        """
        self.add_text("_")

    def visit_strong(self, node: nodes.strong) -> None:
        """
        Visit a strong (bold) node.

        Args:
            node: The strong node
        """
        # Typst bold syntax: *text*
        self.add_text("*")

    def depart_strong(self, node: nodes.strong) -> None:
        """
        Depart a strong (bold) node.

        Args:
            node: The strong node
        """
        self.add_text("*")

    def visit_literal(self, node: nodes.literal) -> None:
        """
        Visit a literal (inline code) node.

        Args:
            node: The literal node
        """
        # Typst inline code syntax: `code`
        self.add_text("`")

    def depart_literal(self, node: nodes.literal) -> None:
        """
        Depart a literal (inline code) node.

        Args:
            node: The literal node
        """
        self.add_text("`")

    def visit_subscript(self, node: nodes.subscript) -> None:
        """
        Visit a subscript node.

        Args:
            node: The subscript node
        """
        # Typst subscript syntax: #sub[text]
        self.add_text("#sub[")

    def depart_subscript(self, node: nodes.subscript) -> None:
        """
        Depart a subscript node.

        Args:
            node: The subscript node
        """
        self.add_text("]")

    def visit_superscript(self, node: nodes.superscript) -> None:
        """
        Visit a superscript node.

        Args:
            node: The superscript node
        """
        # Typst superscript syntax: #super[text]
        self.add_text("#super[")

    def depart_superscript(self, node: nodes.superscript) -> None:
        """
        Depart a superscript node.

        Args:
            node: The superscript node
        """
        self.add_text("]")

    def visit_bullet_list(self, node: nodes.bullet_list) -> None:
        """
        Visit a bullet list node.

        Args:
            node: The bullet list node
        """
        self.list_stack.append("bullet")

    def depart_bullet_list(self, node: nodes.bullet_list) -> None:
        """
        Depart a bullet list node.

        Args:
            node: The bullet list node
        """
        self.list_stack.pop()
        self.add_text("\n")

    def visit_enumerated_list(self, node: nodes.enumerated_list) -> None:
        """
        Visit an enumerated (numbered) list node.

        Args:
            node: The enumerated list node
        """
        self.list_stack.append("enumerated")

    def depart_enumerated_list(self, node: nodes.enumerated_list) -> None:
        """
        Depart an enumerated (numbered) list node.

        Args:
            node: The enumerated list node
        """
        self.list_stack.pop()
        self.add_text("\n")

    def visit_list_item(self, node: nodes.list_item) -> None:
        """
        Visit a list item node.

        Args:
            node: The list item node
        """
        # Calculate indentation based on nesting level
        indent = "  " * (len(self.list_stack) - 1)

        # Determine list marker based on list type
        if self.list_stack and self.list_stack[-1] == "bullet":
            self.add_text(f"{indent}- ")
        elif self.list_stack and self.list_stack[-1] == "enumerated":
            self.add_text(f"{indent}+ ")

    def depart_list_item(self, node: nodes.list_item) -> None:
        """
        Depart a list item node.

        Args:
            node: The list item node
        """
        self.add_text("\n")

    def visit_literal_block(self, node: nodes.literal_block) -> None:
        """
        Visit a literal block (code block) node.

        Implements Task 4.2.2: codly forced usage with #codly-range() for highlighted lines
        Design 3.5: All code blocks use codly, with #codly-range() for highlights
        Requirements 7.3, 7.4: Support line numbers and highlighted lines
        Issue #20: Support :linenos:, :caption:, and :name: options
        Issue #31: Support :lineno-start: and :dedent: options

        Args:
            node: The literal block node
        """
        # Issue #20: Handle captioned code blocks
        # If we're in a captioned code block (literal-block-wrapper container),
        # wrap the code block in a #figure()
        if self.in_captioned_code_block and self.code_block_caption:
            # Escape special characters in caption
            escaped_caption = self.code_block_caption
            # Start figure with caption (will add closing bracket in depart)
            self.add_text(f"#figure(caption: [{escaped_caption}])[\n")

        # Check for :linenos: option (Issue #20)
        # If linenos is not set or False, disable line numbers in codly
        linenos = node.get("linenos", False)
        if not linenos:
            self.add_text("#codly(number-format: none)\n")

        # Extract highlight_args if present (Task 4.2.2)
        highlight_args = node.get("highlight_args", {})
        hl_lines = highlight_args.get("hl_lines", [])

        # Issue #31: Support :lineno-start: option
        # Sphinx stores lineno-start in highlight_args['linenostart']
        lineno_start = highlight_args.get("linenostart")
        if linenos and lineno_start is not None:
            self.add_text(f"#codly(start: {lineno_start})\n")

        # Generate #codly-range() if highlight lines are specified
        if hl_lines:
            # Convert list of line numbers to Typst array format
            # Example: [2, 3] -> #codly-range(highlight: (2, 3))
            # Example: [2, 4, 5, 6] -> #codly-range(highlight: (2, 4, 5, 6))
            highlight_str = ", ".join(str(line) for line in hl_lines)
            self.add_text(f"#codly-range(highlight: ({highlight_str}))\n")

        # Typst code block syntax: ```language\ncode\n```
        # Extract language if specified
        language = node.get("language", "")
        if language:
            self.add_text(f"```{language}\n")
        else:
            self.add_text("```\n")

    def depart_literal_block(self, node: nodes.literal_block) -> None:
        """
        Depart a literal block (code block) node.

        Issue #20: Handle closing figure bracket and labels.

        Args:
            node: The literal block node
        """
        # Close code block
        self.add_text("\n```\n")

        # Issue #20: Close figure wrapper if we're in a captioned code block
        if self.in_captioned_code_block and self.code_block_caption:
            # Close the figure's trailing content block with ]
            self.add_text("]")
            # Add label if present
            if self.code_block_label:
                self.add_text(f" <{self.code_block_label}>")
            self.add_text("\n\n")
        elif node.get("names"):
            # Handle :name: option without :caption: - just add label after code block
            label = node.get("names")[0]
            self.add_text(f" <{label}>\n\n")
        else:
            # Normal code block - just add spacing
            self.add_text("\n")

    def visit_definition_list(self, node: nodes.definition_list) -> None:
        """
        Visit a definition list node.

        Args:
            node: The definition list node
        """
        # Definition lists don't need special opening markup in Typst
        pass

    def depart_definition_list(self, node: nodes.definition_list) -> None:
        """
        Depart a definition list node.

        Args:
            node: The definition list node
        """
        # Add newline after definition list
        self.add_text("\n")

    def visit_definition_list_item(self, node: nodes.definition_list_item) -> None:
        """
        Visit a definition list item node.

        Args:
            node: The definition list item node
        """
        # Definition list items don't need special markup
        pass

    def depart_definition_list_item(self, node: nodes.definition_list_item) -> None:
        """
        Depart a definition list item node.

        Args:
            node: The definition list item node
        """
        # Definition list items don't need closing
        pass

    def visit_term(self, node: nodes.term) -> None:
        """
        Visit a term (definition list term) node.

        Args:
            node: The term node
        """
        # Typst definition list syntax: / term: definition
        self.add_text("/ ")

    def depart_term(self, node: nodes.term) -> None:
        """
        Depart a term (definition list term) node.

        Args:
            node: The term node
        """
        # Add colon after term
        self.add_text(": ")

    def visit_definition(self, node: nodes.definition) -> None:
        """
        Visit a definition (definition list definition) node.

        Args:
            node: The definition node
        """
        # Definitions don't need special opening markup
        pass

    def depart_definition(self, node: nodes.definition) -> None:
        """
        Depart a definition (definition list definition) node.

        Args:
            node: The definition node
        """
        # Add newline after definition
        self.add_text("\n")

    def visit_figure(self, node: nodes.figure) -> None:
        """
        Visit a figure node.

        Args:
            node: The figure node
        """
        self.in_figure = True
        self.figure_content = []  # Store figure content (image)
        self.figure_caption = ""  # Store caption text

        # Start figure with potential label
        self.add_text("#figure(\n")

    def depart_figure(self, node: nodes.figure) -> None:
        """
        Depart a figure node.

        Args:
            node: The figure node
        """
        # Close the figure
        if self.figure_caption:
            self.add_text(f",\n  caption: [{self.figure_caption}]")

        # Add label if figure has ids
        if node.get("ids"):
            label = node["ids"][0]
            self.add_text(f"\n) <{label}>\n\n")
        else:
            self.add_text("\n)\n\n")

        self.in_figure = False
        self.figure_content = []
        self.figure_caption = ""

    def visit_caption(self, node: nodes.caption) -> None:
        """
        Visit a caption node.

        Handles captions for both figures and code blocks (Issue #20).

        Args:
            node: The caption node
        """
        # For captioned code blocks, caption is already extracted in visit_container
        # We should skip output to avoid duplicate caption text
        if self.in_captioned_code_block:
            raise nodes.SkipNode
        # For figures, start collecting caption text
        self.in_caption = True

    def depart_caption(self, node: nodes.caption) -> None:
        """
        Depart a caption node.

        Args:
            node: The caption node
        """
        # Store caption text for figures
        if self.in_figure:
            self.figure_caption = node.astext()
        self.in_caption = False

    def visit_table(self, node: nodes.table) -> None:
        """
        Visit a table node.

        Args:
            node: The table node
        """
        self.in_table = True
        self.table_cells = []  # Store cells for table generation
        self.table_colcount = 0  # Track number of columns

    def depart_table(self, node: nodes.table) -> None:
        """
        Depart a table node.

        Args:
            node: The table node
        """
        # Generate Typst #table() syntax
        if self.table_colcount > 0:
            # Use self.body.append directly to avoid routing to table_cell_content
            self.body.append(f"#table(\n  columns: {self.table_colcount},\n")

            # Add all cells
            for cell in self.table_cells:
                self.body.append(f"  [{cell}],\n")

            self.body.append(")\n\n")

        self.in_table = False
        self.table_cells = []
        self.table_colcount = 0

    def visit_tgroup(self, node: nodes.tgroup) -> None:
        """
        Visit a tgroup (table group) node.

        Args:
            node: The tgroup node
        """
        # Get column count from tgroup
        self.table_colcount = node.get("cols", 0)

    def depart_tgroup(self, node: nodes.tgroup) -> None:
        """
        Depart a tgroup (table group) node.

        Args:
            node: The tgroup node
        """
        pass

    def visit_colspec(self, node: nodes.colspec) -> None:
        """
        Visit a colspec (column specification) node.

        Args:
            node: The colspec node
        """
        # Column specifications are handled by tgroup
        raise nodes.SkipNode

    def depart_colspec(self, node: nodes.colspec) -> None:
        """
        Depart a colspec (column specification) node.

        Args:
            node: The colspec node
        """
        pass

    def visit_thead(self, node: nodes.thead) -> None:
        """
        Visit a thead (table header) node.

        Args:
            node: The thead node
        """
        # Header rows are handled the same as body rows in Typst
        pass

    def depart_thead(self, node: nodes.thead) -> None:
        """
        Depart a thead (table header) node.

        Args:
            node: The thead node
        """
        pass

    def visit_tbody(self, node: nodes.tbody) -> None:
        """
        Visit a tbody (table body) node.

        Args:
            node: The tbody node
        """
        pass

    def depart_tbody(self, node: nodes.tbody) -> None:
        """
        Depart a tbody (table body) node.

        Args:
            node: The tbody node
        """
        pass

    def visit_row(self, node: nodes.row) -> None:
        """
        Visit a row (table row) node.

        Args:
            node: The row node
        """
        # Rows are processed by collecting entries
        pass

    def depart_row(self, node: nodes.row) -> None:
        """
        Depart a row (table row) node.

        Args:
            node: The row node
        """
        pass

    def visit_entry(self, node: nodes.entry) -> None:
        """
        Visit an entry (table cell) node.

        Args:
            node: The entry node
        """
        # Start collecting cell content
        self.table_cell_content = []

    def depart_entry(self, node: nodes.entry) -> None:
        """
        Depart an entry (table cell) node.

        Args:
            node: The entry node
        """
        # Get cell content and add to table cells
        # Extract text from the accumulated body content since visit_entry
        cell_text = ""
        if hasattr(self, "table_cell_content") and self.table_cell_content:
            cell_text = "".join(self.table_cell_content).strip()

        if not cell_text:
            # If no content was captured, try to get text from the node
            cell_text = node.astext().strip()

        self.table_cells.append(cell_text)
        self.table_cell_content = []

    def visit_block_quote(self, node: nodes.block_quote) -> None:
        """
        Visit a block quote node.

        Args:
            node: The block quote node
        """
        # Typst block quote syntax: #quote[...]
        # Check if there's an attribution child node
        has_attribution = any(isinstance(child, nodes.attribution) for child in node)

        if has_attribution:
            # Will add attribution parameter when we encounter the attribution node
            self.add_text("#quote(")
        else:
            self.add_text("#quote[")

    def depart_block_quote(self, node: nodes.block_quote) -> None:
        """
        Depart a block quote node.

        Args:
            node: The block quote node
        """
        # Check if there's an attribution child node
        has_attribution = any(isinstance(child, nodes.attribution) for child in node)

        if has_attribution:
            self.add_text(")\n\n")
        else:
            self.add_text("]\n\n")

    def visit_attribution(self, node: nodes.attribution) -> None:
        """
        Visit an attribution node (quote attribution).

        Args:
            node: The attribution node
        """
        # Close the quote content and add attribution parameter
        self.add_text("], attribution: [")

    def depart_attribution(self, node: nodes.attribution) -> None:
        """
        Depart an attribution node.

        Args:
            node: The attribution node
        """
        # Close attribution parameter
        self.add_text("]")

    def visit_image(self, node: nodes.image) -> None:
        """
        Visit an image node.

        Args:
            node: The image node
        """
        # Typst image syntax: #image("path", width: value)
        uri = node.get("uri", "")

        # If inside a figure, don't add # prefix (figure will handle it)
        if self.in_figure:
            self.add_text(f'  image("{uri}"')
        else:
            self.add_text(f'#image("{uri}"')

        # Add optional attributes
        if "width" in node:
            width = node["width"]
            self.add_text(f", width: {width}")

        if "height" in node:
            height = node["height"]
            self.add_text(f", height: {height}")

        self.add_text(")")

    def depart_image(self, node: nodes.image) -> None:
        """
        Depart an image node.

        Args:
            node: The image node
        """
        # If inside a figure, don't add extra newlines (figure will handle spacing)
        if not self.in_figure:
            self.add_text("\n\n")

    def visit_target(self, node: nodes.target) -> None:
        """
        Visit a target node (label definition).

        Args:
            node: The target node
        """
        # Generate Typst label if target has ids
        if node.get("ids"):
            label = node["ids"][0]
            self.add_text(f"<{label}> ")
        # Skip processing children as target is typically empty
        raise nodes.SkipNode

    def depart_target(self, node: nodes.target) -> None:
        """
        Depart a target node.

        Args:
            node: The target node
        """
        # Target is handled in visit
        pass

    def visit_pending_xref(self, node: nodes.Node) -> None:
        """
        Visit a pending_xref node (Sphinx cross-reference).

        Args:
            node: The pending_xref node
        """
        # pending_xref nodes are typically resolved by Sphinx before reaching the writer
        # If we encounter one, it means resolution failed or we're in a special case
        # We handle it by generating a link to the target

        reftarget = node.get("reftarget", "")
        reftype = node.get("reftype", "")

        if reftarget:
            # Generate a link to the target
            # Sanitize the target for Typst label format
            label = reftarget.replace(".", "-").replace("_", "-")
            self.add_text(f"#link(<{label}>)[")
        # Continue processing children to get the link text

    def depart_pending_xref(self, node: nodes.Node) -> None:
        """
        Depart a pending_xref node.

        Args:
            node: The pending_xref node
        """
        reftarget = node.get("reftarget", "")
        if reftarget:
            self.add_text("]")

    def _compute_relative_include_path(
        self, target_docname: str, current_docname: Optional[str]
    ) -> str:
        """
        Compute relative path for toctree #include() directive.

        This method calculates the relative path from the current document
        to the target document for use in Typst #include() directives.
        Uses PurePosixPath for OS-independent POSIX path handling.

        Args:
            target_docname: Target document name (e.g., "chapter1/section1")
            current_docname: Current document name (e.g., "chapter1/index"), or None

        Returns:
            Relative path string for #include() (e.g., "section1" or "../chapter2/doc")

        Examples:
            >>> _compute_relative_include_path("chapter1/section1", "chapter1/index")
            "section1"
            >>> _compute_relative_include_path("chapter2/doc", "chapter1/index")
            "../chapter2/doc"
            >>> _compute_relative_include_path("chapter1/doc", None)
            "chapter1/doc"

        Notes:
            This method implements Issue #5 fix for nested toctree relative paths.
            It handles three cases:
            1. current_docname is None: return absolute path
            2. Same directory: use relative_to() directly
            3. Cross-directory: calculate via common parent

        Requirements: 1.1, 1.2, 1.3, 1.4, 1.5
        """
        from pathlib import PurePosixPath

        logger.debug(
            f"Computing relative include path: target={target_docname}, "
            f"current={current_docname}"
        )

        # Fallback to absolute path if current_docname is None
        if not current_docname:
            logger.debug(f"No current document, using absolute path: {target_docname}")
            return target_docname

        current_path = PurePosixPath(current_docname)
        target_path = PurePosixPath(target_docname)
        current_dir = current_path.parent

        logger.debug(
            f"Path components: current_dir={current_dir}, " f"target_path={target_path}"
        )

        # Root directory case: use absolute path (backward compatibility)
        if current_dir == PurePosixPath("."):
            logger.debug(
                f"Current document is in root directory, "
                f"using absolute path: {target_docname}"
            )
            return target_docname

        # Try to compute relative path
        try:
            rel_path = target_path.relative_to(current_dir)
            result = str(rel_path)
            logger.debug(
                f"Same directory reference: {current_dir} -> {target_path}, "
                f"result: {result}"
            )
            return result
        except ValueError:
            # Different directory trees - build path via common parent
            logger.debug(
                "Cross-directory reference detected, calculating via common parent"
            )

            current_parts = current_dir.parts
            target_parts = target_path.parts

            # Find common parent by comparing path components
            common_length = 0
            for i, (c, t) in enumerate(zip(current_parts, target_parts)):
                if c == t:
                    common_length = i + 1
                else:
                    break

            logger.debug(
                f"Common parent depth: {common_length}, "
                f"current_parts={current_parts}, target_parts={target_parts}"
            )

            # Build path: "../" from current to common parent
            up_count = len(current_parts) - common_length
            up_path = "../" * up_count if up_count > 0 else ""

            # Build path: from common parent to target
            down_parts = target_parts[common_length:]
            down_path = "/".join(down_parts) if down_parts else ""

            relative_path: str = up_path + down_path

            logger.debug(
                f"Cross-directory path calculation: up_count={up_count}, "
                f"up_path='{up_path}', down_path='{down_path}', "
                f"result: {relative_path}"
            )

            return relative_path

    def visit_toctree(self, node: nodes.Node) -> None:
        """
        Visit a toctree node (Sphinx table of contents tree).

        Requirement 13: Multi-document integration and toctree processing
        - Generate #include() for each entry
        - Apply #set heading(offset: 1) to lower heading levels
        - Issue #5: Fix relative paths for nested toctrees
          - Calculate relative paths from current document
        - Issue #7: Simplify toctree output with single content block
          - Generate single #[...] block containing all includes
          - Apply #set heading(offset: 1) once per toctree

        Args:
            node: The toctree node

        Notes:
            This method generates Typst #include() directives for each toctree entry
            within a single content block #[...] to apply heading offset without
            displaying the block delimiters in the output. This simplifies the
            generated Typst code and improves readability.
        """
        # Get entries from the toctree node
        entries = node.get("entries", [])

        logger.debug(f"Processing toctree with {len(entries)} entries")

        # If no entries, don't generate anything
        if not entries:
            logger.debug("Toctree has no entries, skipping")
            raise nodes.SkipNode

        # Get current document name for relative path calculation
        current_docname = getattr(self.builder, "current_docname", None)

        logger.debug(
            f"Current document for toctree: {current_docname}, "
            f"entries: {[docname for _, docname in entries]}"
        )

        # Issue #7: Generate single content block for all includes
        # Start single content block
        self.add_text("#[\n")
        self.add_text("  #set heading(offset: 1)\n")

        # Generate #include() for each entry within the single block
        # Each included file has its own imports, so block scope is safe
        for _title, docname in entries:
            # Compute relative path for #include() (Issue #5 fix)
            relative_path = self._compute_relative_include_path(
                docname, current_docname
            )

            logger.debug(
                f"Generated #include() for toctree: {docname} -> {relative_path}.typ"
            )

            # Issue #7: Generate only #include() within the block
            self.add_text(f'  #include("{relative_path}.typ")\n')

        # End single content block
        self.add_text("]\n\n")

        # Skip processing children as we've handled the toctree entries
        raise nodes.SkipNode

    def depart_toctree(self, node: nodes.Node) -> None:
        """
        Depart a toctree node.

        Args:
            node: The toctree node
        """
        # Toctree is handled in visit
        pass

    def visit_reference(self, node: nodes.reference) -> None:
        """
        Visit a reference node (link).

        Args:
            node: The reference node
        """
        # Get the reference URI
        refuri = node.get("refuri", "")

        # Check if it's an internal reference (starts with #)
        if refuri.startswith("#"):
            # Internal reference to a label
            label = refuri[1:]  # Remove the #
            self.add_text(f"#link(<{label}>)[")
        else:
            # External reference (HTTP/HTTPS URL or relative path)
            self.add_text(f'#link("{refuri}")[')

    def depart_reference(self, node: nodes.reference) -> None:
        """
        Depart a reference node.

        Args:
            node: The reference node
        """
        # Close the link
        self.add_text("]")

    def unknown_visit(self, node: nodes.Node) -> None:
        """
        Handle unknown nodes during visit.

        Args:
            node: The unknown node
        """
        # Log a warning for unknown nodes but don't raise an exception
        from sphinx.util import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"unknown node type: {node}")

    def unknown_departure(self, node: nodes.Node) -> None:
        """
        Handle unknown nodes during departure.

        Args:
            node: The unknown node
        """
        # Silently ignore unknown departures
        pass

    def _convert_latex_to_typst(self, latex_content: str) -> str:
        """
        Convert LaTeX math syntax to Typst native syntax.

        Implements Task 6.5: Basic LaTeX to Typst conversion
        Requirement 4.9: Fallback when typst_use_mitex=False

        Args:
            latex_content: LaTeX math content

        Returns:
            Typst native math content
        """
        # Basic conversion rules for common LaTeX commands
        result = latex_content

        # Greek letters: \alpha -> alpha, \beta -> beta, etc.
        greek_letters = [
            "alpha",
            "beta",
            "gamma",
            "delta",
            "epsilon",
            "zeta",
            "eta",
            "theta",
            "iota",
            "kappa",
            "lambda",
            "mu",
            "nu",
            "xi",
            "omicron",
            "pi",
            "rho",
            "sigma",
            "tau",
            "upsilon",
            "phi",
            "chi",
            "psi",
            "omega",
            "Alpha",
            "Beta",
            "Gamma",
            "Delta",
            "Epsilon",
            "Zeta",
            "Eta",
            "Theta",
            "Iota",
            "Kappa",
            "Lambda",
            "Mu",
            "Nu",
            "Xi",
            "Omicron",
            "Pi",
            "Rho",
            "Sigma",
            "Tau",
            "Upsilon",
            "Phi",
            "Chi",
            "Psi",
            "Omega",
        ]
        for letter in greek_letters:
            result = result.replace(f"\\{letter}", letter)

        # Fractions: \frac{a}{b} -> frac(a, b)
        result = re.sub(r"\\frac\{([^}]+)\}\{([^}]+)\}", r"frac(\1, \2)", result)

        # Sum: \sum_{lower}^{upper} -> sum_(lower)^upper
        result = re.sub(r"\\sum_\{([^}]+)\}\^\{([^}]+)\}", r"sum_(\1)^(\2)", result)
        result = re.sub(r"\\sum_\{([^}]+)\}", r"sum_(\1)", result)
        result = result.replace(r"\sum", "sum")

        # Integral: \int_{lower}^{upper} -> integral_(lower)^upper
        result = re.sub(
            r"\\int_\{([^}]+)\}\^\{([^}]+)\}", r"integral_(\1)^(\2)", result
        )
        result = re.sub(r"\\int_\{([^}]+)\}", r"integral_(\1)", result)
        result = result.replace(r"\int", "integral")

        # Product: \prod -> product
        result = result.replace(r"\prod", "product")

        # Square root: \sqrt{x} -> sqrt(x)
        result = re.sub(r"\\sqrt\{([^}]+)\}", r"sqrt(\1)", result)

        # Infinity: \infty -> infinity
        result = result.replace(r"\infty", "infinity")

        # Partial derivative: \partial -> diff (Typst uses diff or ∂)
        result = result.replace(r"\partial", "diff")

        # Common functions
        result = result.replace(r"\sin", "sin")
        result = result.replace(r"\cos", "cos")
        result = result.replace(r"\tan", "tan")
        result = result.replace(r"\log", "log")
        result = result.replace(r"\ln", "ln")
        result = result.replace(r"\exp", "exp")

        # If there are still backslashes, warn about unconverted syntax
        if "\\" in result:
            logger.warning(
                f"LaTeX math contains commands that may not convert well to Typst: {latex_content}"
            )

        return result

    def visit_math(self, node: nodes.math) -> None:
        """
        Visit an inline math node.

        Implements Task 6.2: LaTeX math conversion (mitex)
        Implements Task 6.3: Labeled equations
        Implements Task 6.4: Typst native math support
        Implements Task 6.5: Math fallback functionality
        Requirement 4.3: Inline math should use #mi(`...`) format (LaTeX)
        Requirement 4.9: Fallback when typst_use_mitex=False
        Requirement 5.2: Inline math should use $...$ format (Typst native)
        Requirement 4.7: Labeled equations should generate <eq:label> format
        Design 3.3: Support both mitex and Typst native math

        Args:
            node: The inline math node
        """
        # Extract math content
        math_content = node.astext()

        # Task 6.4: Check if this is explicitly marked as Typst native
        is_typst_native = "typst-native" in node.get("classes", [])

        # Task 6.5: Check typst_use_mitex config (default to True)
        use_mitex = getattr(self.builder.config, "typst_use_mitex", True)

        if is_typst_native or not use_mitex:
            # Requirement 5.2: Typst native inline math syntax
            # Task 6.5: Convert LaTeX to Typst if use_mitex=False
            if not is_typst_native and not use_mitex:
                # Convert LaTeX syntax to Typst native
                math_content = self._convert_latex_to_typst(math_content)
            self.add_text(f"${math_content}$")
        else:
            # Requirement 4.3: LaTeX math via mitex
            self.add_text(f"#mi(`{math_content}`)")

        # Task 6.3: Add label if present
        if "ids" in node and node["ids"]:
            label = node["ids"][0]
            self.add_text(f" <{label}>")

        # Skip children to prevent duplicate output of math content
        raise nodes.SkipNode

    def depart_math(self, node: nodes.math) -> None:
        """
        Depart an inline math node.

        Args:
            node: The inline math node
        """
        # No additional output needed
        pass

    def visit_math_block(self, node: nodes.math_block) -> None:
        """
        Visit a block math node.

        Implements Task 6.2: LaTeX math conversion (mitex)
        Implements Task 6.3: Labeled equations
        Implements Task 6.4: Typst native math support
        Implements Task 6.5: Math fallback functionality
        Requirement 4.2: Block math should use #mitex(`...`) format (LaTeX)
        Requirement 4.9: Fallback when typst_use_mitex=False
        Requirement 5.2: Block math should use $ ... $ format (Typst native)
        Requirement 4.7: Labeled equations should generate <eq:label> format
        Design 3.3: Support both mitex and Typst native math

        Args:
            node: The block math node
        """
        # Extract math content
        math_content = node.astext()

        # Task 6.4: Check if this is explicitly marked as Typst native
        is_typst_native = "typst-native" in node.get("classes", [])

        # Task 6.5: Check typst_use_mitex config (default to True)
        use_mitex = getattr(self.builder.config, "typst_use_mitex", True)

        if is_typst_native or not use_mitex:
            # Requirement 5.2: Typst native block math syntax
            # Task 6.5: Convert LaTeX to Typst if use_mitex=False
            if not is_typst_native and not use_mitex:
                # Convert LaTeX syntax to Typst native
                math_content = self._convert_latex_to_typst(math_content)
            self.add_text(f"$ {math_content} $")
        else:
            # Requirement 4.2: LaTeX math via mitex
            self.add_text(f"#mitex(`{math_content}`)")

        # Task 6.3: Add label if present
        if "ids" in node and node["ids"]:
            label = node["ids"][0]
            self.add_text(f" <{label}>")

        self.add_text("\n\n")

        # Skip children to prevent duplicate output of math content
        raise nodes.SkipNode

    def depart_math_block(self, node: nodes.math_block) -> None:
        """
        Depart a block math node.

        Args:
            node: The block math node
        """
        # No additional output needed
        pass

    # Admonition nodes (Task 3.4)
    # Requirement 2.8-2.10: Convert Sphinx admonitions to gentle-clues

    def _visit_admonition(
        self, node: nodes.Node, clue_type: str, custom_title: str = None
    ) -> None:
        """
        Helper method to visit any admonition node.

        Args:
            node: The admonition node
            clue_type: The gentle-clues function name (e.g., 'info', 'warning', 'tip')
            custom_title: Optional custom title for the admonition
        """
        # Check if there's a title element in the node
        title = None
        for child in node.children:
            if isinstance(child, nodes.title):
                title = child.astext()
                break

        # Use custom title if provided, otherwise check for title element
        if title:
            self.add_text(f'#{clue_type}(title: "{title}")[')
        elif custom_title:
            self.add_text(f'#{clue_type}(title: "{custom_title}")[')
        else:
            self.add_text(f"#{clue_type}[")

    def _depart_admonition(self) -> None:
        """
        Helper method to depart any admonition node.
        """
        self.add_text("]\n\n")

    def visit_note(self, node: nodes.note) -> None:
        """Visit a note admonition (converts to #info[])."""
        self._visit_admonition(node, "info")

    def depart_note(self, node: nodes.note) -> None:
        """Depart a note admonition."""
        self._depart_admonition()

    def visit_warning(self, node: nodes.warning) -> None:
        """Visit a warning admonition (converts to #warning[])."""
        self._visit_admonition(node, "warning")

    def depart_warning(self, node: nodes.warning) -> None:
        """Depart a warning admonition."""
        self._depart_admonition()

    def visit_tip(self, node: nodes.tip) -> None:
        """Visit a tip admonition (converts to #tip[])."""
        self._visit_admonition(node, "tip")

    def depart_tip(self, node: nodes.tip) -> None:
        """Depart a tip admonition."""
        self._depart_admonition()

    def visit_important(self, node: nodes.important) -> None:
        """Visit an important admonition (converts to #warning(title: "Important")[])."""
        self._visit_admonition(node, "warning", custom_title="Important")

    def depart_important(self, node: nodes.important) -> None:
        """Depart an important admonition."""
        self._depart_admonition()

    def visit_caution(self, node: nodes.caution) -> None:
        """Visit a caution admonition (converts to #warning[])."""
        self._visit_admonition(node, "warning")

    def depart_caution(self, node: nodes.caution) -> None:
        """Depart a caution admonition."""
        self._depart_admonition()

    def visit_seealso(self, node: addnodes.seealso) -> None:
        """Visit a seealso admonition (converts to #info(title: "See Also")[])."""
        self._visit_admonition(node, "info", custom_title="See Also")

    def depart_seealso(self, node: addnodes.seealso) -> None:
        """Depart a seealso admonition."""
        self._depart_admonition()

    # Inline nodes (Task 7.4)
    # Requirement 3.1: Inline cross-references and links

    def visit_inline(self, node: nodes.inline) -> None:
        """
        Visit an inline node.

        Inline nodes are generic containers for inline content.
        They are often used for cross-references with specific CSS classes.

        Task 7.4: Handle inline nodes, especially those with 'xref' class
        Requirement 3.1: Cross-references and links
        """
        # Inline nodes are transparent containers - we just process their children
        # The CSS classes (like 'xref', 'doc', 'std-ref') are mainly for HTML/CSS styling
        # For Typst output, we simply render the text content
        pass

    def depart_inline(self, node: nodes.inline) -> None:
        """
        Depart an inline node.
        """
        pass
