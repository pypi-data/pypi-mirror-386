from pathlib import Path

from pyopenapi_gen import HTTPMethod, IROperation, IRResponse, IRSpec
from pyopenapi_gen.emitters.exceptions_emitter import ExceptionsEmitter


def test_exceptions_emitter__numeric_response_codes__generates_error_aliases(tmp_path: Path) -> None:
    """
    Scenario:
        ExceptionsEmitter processes an IRSpec containing operations with numeric
        response codes (404, 500).

    Expected Outcome:
        The emitter should generate exception_aliases.py with corresponding
        NotFoundError and InternalServerError classes (human-readable names)
        that inherit from appropriate base exceptions.
    """
    # Create IR operations with numeric response codes
    resp1 = IRResponse(status_code="404", description="Not found", content={})
    resp2 = IRResponse(status_code="500", description="Server err", content={})
    op1 = IROperation(
        operation_id="op1",
        method=HTTPMethod.GET,
        path="/x",
        summary="",
        description=None,
        parameters=[],
        request_body=None,
        responses=[resp1, resp2],
        tags=["t"],
    )
    spec = IRSpec(
        title="API",
        version="1.0",
        schemas={},
        operations=[op1],
        servers=["https://api.test"],
    )

    emitter = ExceptionsEmitter()
    out_dir = str(tmp_path / "out")
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    emitter.emit(spec, out_dir)

    alias_file = Path(out_dir) / "exception_aliases.py"
    assert alias_file.exists(), "exception_aliases.py not generated"
    content = alias_file.read_text()
    # Should have human-readable aliases for 404 and 500
    assert "class NotFoundError(ClientError)" in content
    assert "class InternalServerError(ServerError)" in content
    # Should import from the core package
    assert "from core.exceptions import" in content
    # Should NOT import HTTPError (it's not used in exception_aliases.py)
    assert "ClientError" in content
    assert "ServerError" in content
    # Should have human-readable docstrings
    assert "HTTP 404 Not Found" in content
    assert "HTTP 500 Internal Server Error" in content
