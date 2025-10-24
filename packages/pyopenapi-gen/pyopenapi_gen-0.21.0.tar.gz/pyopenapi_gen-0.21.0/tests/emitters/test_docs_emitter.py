from pathlib import Path

from pyopenapi_gen import (
    HTTPMethod,
    IROperation,
    IRParameter,
    IRResponse,
    IRSchema,
    IRSpec,
)
from pyopenapi_gen.core.utils import NameSanitizer
from pyopenapi_gen.emitters.docs_emitter import DocsEmitter


def create_simple_response_schema() -> IRSchema:
    # Create a basic IRSchema for response bodies
    return IRSchema(name=None, type="object", format=None)


def create_simple_param_schema() -> IRSchema:
    # Create a basic IRSchema for path parameters
    return IRSchema(name=None, type="string", format=None)


def test_docs_emitter__emit_index_and_tag_files(tmp_path: Path) -> None:
    """
    Scenario:
        Render documentation for a spec with two tags, one with special characters.
    Expected Outcome:
        - index.md lists each tag with sanitized links.
        - Each tag's .md file is created with the operation section.
    """
    # Arrange
    tag1 = "items"
    tag2 = "My-Tag!"
    op1 = IROperation(
        operation_id="list_items",
        method=HTTPMethod.GET,
        path="/items",
        summary="List items",
        description="",
        parameters=[
            IRParameter(
                name="common_param",
                param_in="query",
                required=False,
                schema=create_simple_param_schema(),
            )
        ],
        request_body=None,
        responses=[
            IRResponse(
                status_code="200",
                description="OK",
                content={"application/json": create_simple_response_schema()},
                stream=False,
            )
        ],
        tags=[tag1],
    )
    op2 = IROperation(
        operation_id="get_special",
        method=HTTPMethod.GET,
        path="/special/{id}",
        summary="Get special item",
        description="",
        parameters=[
            IRParameter(
                name="id",
                param_in="path",
                required=True,
                schema=create_simple_param_schema(),
            )
        ],
        request_body=None,
        responses=[
            IRResponse(
                status_code="200",
                description="OK",
                content={"application/json": create_simple_response_schema()},
                stream=False,
            )
        ],
        tags=[tag2],
    )
    spec = IRSpec(title="API", version="1.0.0", schemas={}, operations=[op1, op2])
    docs_out = tmp_path / "docs"

    # Act
    DocsEmitter().emit(spec, str(docs_out))

    # Assert index.md
    index_file = docs_out / "index.md"
    assert index_file.exists(), "index.md not generated"
    index_text = index_file.read_text()
    san1 = NameSanitizer.sanitize_module_name(tag1)
    san2 = NameSanitizer.sanitize_module_name(tag2)
    assert f"- [{tag1}]({san1}.md)" in index_text
    assert f"- [{tag2}]({san2}.md)" in index_text

    # Assert per-tag files
    for tag, op in [(tag1, op1), (tag2, op2)]:
        san = NameSanitizer.sanitize_module_name(tag)
        tag_file = docs_out / f"{san}.md"
        assert tag_file.exists(), f"Expected {san}.md to exist"
        text = tag_file.read_text()
        # Should contain the operation heading and method/path lines
        assert f"### {op.operation_id}" in text
        assert f"**Method:** `{op.method.value}`" in text
        assert f"**Path:** `{op.path}`" in text
