"""Flask application for offline file integrity checking."""

from __future__ import annotations

import os
import time
from pathlib import Path

from flask import (
    Flask,
    after_this_request,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename

from utils.hashing import (
    ALGORITHMS,
    HashingError,
    calculate_hashes,
    compare_hash,
    format_file_size,
)


BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
MAX_FILE_SIZE = 100 * 1024 * 1024


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-file-integrity-key")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE

UPLOAD_FOLDER.mkdir(exist_ok=True)


def is_valid_upload(file_storage) -> tuple[bool, str]:
    """Validate that a submitted file exists and has a usable filename."""
    if not file_storage:
        return False, "Please choose a file to upload."

    if not file_storage.filename:
        return False, "The selected upload does not include a file name."

    safe_name = secure_filename(file_storage.filename)
    if not safe_name:
        return False, "This file name is not supported. Please rename the file."

    return True, ""


def save_upload(file_storage) -> Path:
    """Save an uploaded file with a secure filename inside the upload folder."""
    safe_name = secure_filename(file_storage.filename)
    file_path = app.config["UPLOAD_FOLDER"] / f"{time.time_ns()}_{safe_name}"
    file_storage.save(file_path)
    return file_path


def delete_file(file_path: Path) -> None:
    """Remove a temporary uploaded file without raising user-facing errors."""
    try:
        if file_path.exists():
            file_path.unlink()
    except OSError:
        app.logger.warning("Could not delete temporary upload: %s", file_path)


@app.errorhandler(RequestEntityTooLarge)
def handle_large_file(_error):
    """Show a friendly message when an upload exceeds 100 MB."""
    flash("File is too large. Please upload a file no bigger than 100 MB.", "error")
    return redirect(url_for("index"))


@app.errorhandler(500)
def handle_server_error(_error):
    """Handle unexpected errors with a friendly response."""
    return (
        render_template(
            "result.html",
            error="Something went wrong while processing the file. Please try again.",
            algorithms=ALGORITHMS,
        ),
        500,
    )


@app.route("/", methods=["GET"])
def index():
    """Render the home page with generation and verification forms."""
    return render_template("index.html", algorithms=ALGORITHMS)


@app.route("/generate", methods=["POST"])
def generate():
    """Generate all supported hashes for an uploaded file."""
    uploaded_file = request.files.get("file")
    valid, message = is_valid_upload(uploaded_file)
    if not valid:
        flash(message, "error")
        return redirect(url_for("index"))

    file_path = save_upload(uploaded_file)

    try:
        file_size = file_path.stat().st_size
        start_time = time.perf_counter()
        hashes = calculate_hashes(file_path)
        elapsed = time.perf_counter() - start_time
        safe_name = secure_filename(uploaded_file.filename)

        report = render_hash_report(
            filename=safe_name,
            file_size=format_file_size(file_size),
            elapsed=elapsed,
            hashes=hashes,
        )

        return render_template(
            "result.html",
            mode="generate",
            filename=safe_name,
            file_size=format_file_size(file_size),
            elapsed=f"{elapsed:.4f}",
            hashes=hashes,
            report=report,
            algorithms=ALGORITHMS,
        )
    except HashingError as error:
        return render_template(
            "result.html",
            error=str(error),
            algorithms=ALGORITHMS,
        )
    finally:
        delete_file(file_path)


@app.route("/verify", methods=["POST"])
def verify():
    """Compare a generated hash against a user-provided known hash."""
    uploaded_file = request.files.get("verify_file")
    valid, message = is_valid_upload(uploaded_file)
    if not valid:
        flash(message, "error")
        return redirect(url_for("index"))

    algorithm = request.form.get("algorithm", "").lower().strip()
    expected_hash = request.form.get("expected_hash", "").strip()

    if algorithm not in ALGORITHMS:
        flash("Please select a supported hash algorithm.", "error")
        return redirect(url_for("index"))

    if not expected_hash:
        flash("Please paste the hash value you want to verify.", "error")
        return redirect(url_for("index"))

    file_path = save_upload(uploaded_file)

    try:
        file_size = file_path.stat().st_size
        start_time = time.perf_counter()
        hashes = calculate_hashes(file_path, [algorithm])
        elapsed = time.perf_counter() - start_time
        generated_hash = hashes[algorithm]
        is_match = compare_hash(generated_hash, expected_hash)
        safe_name = secure_filename(uploaded_file.filename)

        report = render_verification_report(
            filename=safe_name,
            file_size=format_file_size(file_size),
            elapsed=elapsed,
            algorithm=algorithm,
            generated_hash=generated_hash,
            expected_hash=expected_hash,
            is_match=is_match,
        )

        return render_template(
            "result.html",
            mode="verify",
            filename=safe_name,
            file_size=format_file_size(file_size),
            elapsed=f"{elapsed:.4f}",
            algorithm=algorithm,
            generated_hash=generated_hash,
            expected_hash=expected_hash,
            is_match=is_match,
            report=report,
            algorithms=ALGORITHMS,
        )
    except HashingError as error:
        return render_template(
            "result.html",
            error=str(error),
            algorithms=ALGORITHMS,
        )
    finally:
        delete_file(file_path)


@app.route("/download-report", methods=["POST"])
def download_report():
    """Download the rendered hash report as a plain text file."""
    report = request.form.get("report", "").strip()
    if not report:
        flash("No report is available to download.", "error")
        return redirect(url_for("index"))

    report_path = BASE_DIR / "uploads" / f"hash_report_{time.time_ns()}.txt"
    report_path.write_text(report, encoding="utf-8")

    @after_this_request
    def cleanup(response):
        delete_file(report_path)
        return response

    return send_file(
        report_path,
        as_attachment=True,
        download_name="file_integrity_report.txt",
        mimetype="text/plain",
    )


def render_hash_report(filename: str, file_size: str, elapsed: float, hashes: dict) -> str:
    """Create a plain text report for generated hashes."""
    lines = [
        "File Integrity Hash Report",
        "=" * 30,
        f"File Name: {filename}",
        f"File Size: {file_size}",
        f"Hash Generation Time: {elapsed:.4f} seconds",
        "",
        "Hashes:",
    ]
    for algorithm, digest in hashes.items():
        lines.append(f"{algorithm.upper()}: {digest}")
    return "\n".join(lines)


def render_verification_report(
    filename: str,
    file_size: str,
    elapsed: float,
    algorithm: str,
    generated_hash: str,
    expected_hash: str,
    is_match: bool,
) -> str:
    """Create a plain text report for hash verification."""
    status = "Integrity Verified" if is_match else "File Modified"
    return "\n".join(
        [
            "File Integrity Verification Report",
            "=" * 37,
            f"File Name: {filename}",
            f"File Size: {file_size}",
            f"Hash Generation Time: {elapsed:.4f} seconds",
            f"Algorithm: {algorithm.upper()}",
            f"Generated Hash: {generated_hash}",
            f"Expected Hash: {expected_hash}",
            f"Result: {status}",
        ]
    )


if __name__ == "__main__":
    app.run(debug=True)
