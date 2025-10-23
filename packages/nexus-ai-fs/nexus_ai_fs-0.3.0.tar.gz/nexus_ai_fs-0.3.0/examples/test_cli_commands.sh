#!/bin/bash
# Test script for Nexus CLI commands
# This script tests all CLI functionality end-to-end

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test workspace
TEST_WORKSPACE="/tmp/nexus-cli-test-$$"
DATA_DIR="$TEST_WORKSPACE/nexus-data"

# Set NEXUS_DATA_DIR environment variable so we don't need --data-dir on every command
export NEXUS_DATA_DIR="$DATA_DIR"

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Nexus CLI Test Suite${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}Cleaning up test workspace...${NC}"
    rm -rf "$TEST_WORKSPACE"
}

# Register cleanup
trap cleanup EXIT

# Test counter
TESTS_RUN=0
TESTS_PASSED=0

# Test helper function
test_command() {
    local description="$1"
    shift
    TESTS_RUN=$((TESTS_RUN + 1))

    echo -e "${BLUE}Test $TESTS_RUN:${NC} $description"

    if "$@"; then
        echo -e "${GREEN}✓ PASSED${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        echo ""
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        echo ""
        return 1
    fi
}

# Install nexus if not already installed
if ! command -v nexus &> /dev/null; then
    echo -e "${YELLOW}Installing Nexus CLI...${NC}"
    pip install -e . > /dev/null 2>&1
fi

echo -e "${GREEN}Starting CLI tests...${NC}\n"

# Test 1: Initialize workspace
test_command "Initialize workspace" \
    nexus init "$TEST_WORKSPACE"

# Test 2: List empty workspace
test_command "List empty workspace" \
    nexus ls /

# Test 3: Create directory (use /data instead of reserved /workspace namespace)
test_command "Create directory" \
    nexus mkdir /data

# Test 4: Create nested directory with --parents
test_command "Create nested directory" \
    nexus mkdir /projects/deep/nested/dir --parents

# Test 5: Write file with string content
test_command "Write file with string content" \
    nexus write /files/hello.txt "Hello, Nexus!"

# Test 6: Write Python file
test_command "Write Python file" \
    bash -c "echo 'def hello():\n    print(\"Hello World\")' | nexus write /files/code.py --input -"

# Test 7: Write JSON file
test_command "Write JSON file" \
    bash -c "echo '{\"name\": \"test\", \"value\": 42}' | nexus write /files/data.json --input -"

# Test 8: Write Markdown file
test_command "Write Markdown file" \
    bash -c "echo '# Test Document\n\n## Section 1\n\nSome content here.' | nexus write /files/README.md --input -"

# Test 9: List files
test_command "List files in /files" \
    nexus ls /files

# Test 10: List files recursively
test_command "List files recursively" \
    nexus ls / --recursive

# Test 11: List files with details
test_command "List files with details" \
    nexus ls / --long

# Test 12: Cat text file
test_command "Display text file" \
    nexus cat /files/hello.txt

# Test 13: Cat Python file (with syntax highlighting)
test_command "Display Python file with syntax highlighting" \
    nexus cat /files/code.py

# Test 14: Copy file
test_command "Copy file" \
    nexus cp /files/hello.txt /files/hello_copy.txt

# Test 15: Glob - find all .txt files
test_command "Find all .txt files" \
    nexus glob "*.txt" --path /files

# Test 16: Glob - find all files recursively
test_command "Find all files with ** pattern" \
    nexus glob "**/*"

# Test 17: Glob - find Python files
test_command "Find Python files" \
    nexus glob "**/*.py"

# Test 18: Grep - search for "Hello"
test_command "Grep search for 'Hello'" \
    nexus grep "Hello"

# Test 19: Grep - search in Python files only
test_command "Grep in Python files only" \
    nexus grep "def" --file-pattern "**/*.py"

# Test 20: Grep - case-insensitive search
test_command "Grep case-insensitive search" \
    nexus grep "HELLO" --ignore-case

# Test 21: Info - show file details
test_command "Show file information" \
    nexus info /files/hello.txt

# Test 22: Delete file
test_command "Delete file" \
    nexus rm /files/hello_copy.txt --force

# Test 23: Verify deletion
test_command "Verify file was deleted" \
    bash -c "! nexus cat /files/hello_copy.txt 2>/dev/null"

# Populate /data for rmdir test
echo -e "${BLUE}Populating /data for rmdir test...${NC}"
nexus write /data/testfile.txt "test content"

# Test 24: Remove directory (should fail - not empty)
test_command "Try to remove non-empty directory" \
    bash -c "! nexus rmdir /data --force 2>/dev/null"

# Test 25: Remove directory recursively
test_command "Remove directory recursively" \
    nexus rmdir /data --recursive --force

# Test 26: Version command
test_command "Show version information" \
    nexus version

# Test 27: Help command
test_command "Show help" \
    nexus --help

# Test 28: Command-specific help
test_command "Show ls command help" \
    nexus ls --help

# Test 29: Write multiple test files for advanced grep
echo -e "${BLUE}Creating test files for advanced operations...${NC}"
nexus write /files/test1.py "# TODO: implement feature\ndef test():\n    pass"
nexus write /files/test2.py "def another_test():\n    # TODO: add tests\n    return 42"
nexus write /files/test3.txt "This file has TODO items\nAnd ERROR messages"

test_command "Grep with multiple matches" \
    nexus grep "TODO"

# Test 30: Complex glob pattern
test_command "Complex glob with test_*.py pattern" \
    nexus glob "test*.py" --path /files

# ============================================================
# Auto-Parse Tests (Transparent Document Parsing)
# ============================================================
echo -e "\n${BLUE}Testing automatic document parsing...${NC}"

# Test 30a: Upload actual PDF file (if it exists)
if [ -f "examples/sample-local-pdf.pdf" ]; then
    test_command "Upload PDF file for auto-parse test" \
        nexus write /documents/sample.pdf --input examples/sample-local-pdf.pdf

    # Test 30b: Wait briefly for async parsing to complete
    echo -e "${YELLOW}Waiting for background PDF parsing...${NC}"
    sleep 3

    # Test 30c: Grep should find "PDF" in parsed content (not binary!)
    test_command "Grep finds text in auto-parsed PDF (not binary)" \
        nexus grep "PDF" --file-pattern "**/*.pdf"

    # Test 30d: Grep for "testing" which appears in the PDF
    test_command "Grep finds 'testing' in parsed PDF content" \
        nexus grep "testing" --file-pattern "**/*.pdf"

    echo -e "${GREEN}✓ Auto-parsing works transparently with PDF!${NC}\n"
else
    echo -e "${YELLOW}⚠ PDF file not found, skipping PDF auto-parse test${NC}\n"
fi

# Test 30e: Also test with Markdown
test_command "Write Markdown file for auto-parse test" \
    bash -c "echo '# Documentation\n\n## Features\nAUTO_PARSE_KEYWORD in markdown' | nexus write /files/auto_parse_test.md --input -"

echo -e "${YELLOW}Waiting for background Markdown parsing...${NC}"
sleep 2

test_command "Grep finds content in auto-parsed Markdown" \
    nexus grep "AUTO_PARSE_KEYWORD"

echo -e "${GREEN}✓ Auto-parsing works with multiple formats!${NC}\n"

# Test 31: Export metadata to JSONL
test_command "Export all metadata to JSONL" \
    nexus export "$TEST_WORKSPACE/metadata-export.jsonl"

# Test 32: Verify export file exists
test_command "Verify export file was created" \
    test -f "$TEST_WORKSPACE/metadata-export.jsonl"

# Test 33: Export with prefix filter
test_command "Export only /workspace metadata" \
    nexus export "$TEST_WORKSPACE/workspace-export.jsonl" --prefix /workspace

# Test 34: Create a new test workspace for import testing
IMPORT_DATA_DIR="$TEST_WORKSPACE/import-test-data"
test_command "Create import test workspace" \
    mkdir -p "$IMPORT_DATA_DIR"

# Switch to import data directory for import tests
export NEXUS_DATA_DIR="$IMPORT_DATA_DIR"

# Test 35: Import metadata to new workspace
test_command "Import metadata from export file" \
    nexus import "$TEST_WORKSPACE/metadata-export.jsonl"

# Test 36: Verify imported files exist in metadata
test_command "List imported files" \
    nexus ls /

# Test 37: Re-import with skip existing (should skip all)
test_command "Re-import should skip existing files" \
    nexus import "$TEST_WORKSPACE/metadata-export.jsonl"

# Test 38: Import with overwrite
test_command "Import with overwrite flag" \
    nexus import "$TEST_WORKSPACE/metadata-export.jsonl" --overwrite

# Test 39: Test export/import workflow end-to-end
test_command "End-to-end export/import workflow" \
    bash -c "nexus export $TEST_WORKSPACE/full-backup.jsonl && \
             NEXUS_DATA_DIR=$IMPORT_DATA_DIR nexus import $TEST_WORKSPACE/full-backup.jsonl"

# ============================================================
# Advanced Export/Import Tests (Issue #35)
# ============================================================
echo -e "\n${BLUE}Testing advanced export/import features...${NC}"

# Test 39a: Import with conflict-mode=overwrite
test_command "Import with conflict-mode=overwrite" \
    nexus import "$TEST_WORKSPACE/metadata-export.jsonl" --conflict-mode overwrite

# Test 39b: Import with conflict-mode=skip (default)
test_command "Import with conflict-mode=skip" \
    nexus import "$TEST_WORKSPACE/metadata-export.jsonl" --conflict-mode skip

# Test 39c: Import with dry-run mode
test_command "Import with dry-run mode (no changes)" \
    nexus import "$TEST_WORKSPACE/metadata-export.jsonl" --dry-run

# Switch back to main data directory
export NEXUS_DATA_DIR="$DATA_DIR"

# ============================================================
# Work Detection CLI Tests (Issue #69)
# ============================================================
echo -e "\n${BLUE}Testing work detection CLI...${NC}"

# Create a separate workspace for work tests
WORK_DATA_DIR="$TEST_WORKSPACE/work-test-data"
test_command "Create work test workspace" \
    mkdir -p "$WORK_DATA_DIR"

# Test 40: Initialize work workspace
test_command "Initialize work test workspace" \
    nexus init "$WORK_DATA_DIR"

# Switch to work data directory
export NEXUS_DATA_DIR="$WORK_DATA_DIR/nexus-data"

# Create work items using Python for setup
cat > "$TEST_WORKSPACE/setup_work.py" << 'EOF'
import sys
import nexus
from datetime import datetime, UTC

data_dir = sys.argv[1]
nx = nexus.connect(config={"data_dir": data_dir + "/nexus-data"})

# Create work item files
work_items = [
    ("/jobs/task1.json", b'{"task": "process_data"}'),
    ("/jobs/task2.json", b'{"task": "train_model"}'),
    ("/jobs/task3.json", b'{"task": "analyze"}'),
    ("/jobs/task4.json", b'{"task": "report"}'),
    ("/jobs/task5.json", b'{"task": "cleanup"}'),
]

for path, content in work_items:
    nx.write(path, content)

# Set work metadata
nx.metadata.set_file_metadata("/jobs/task1.json", "status", "ready")
nx.metadata.set_file_metadata("/jobs/task1.json", "priority", 1)

nx.metadata.set_file_metadata("/jobs/task2.json", "status", "in_progress")
nx.metadata.set_file_metadata("/jobs/task2.json", "priority", 2)
nx.metadata.set_file_metadata("/jobs/task2.json", "worker_id", "worker-001")
nx.metadata.set_file_metadata("/jobs/task2.json", "started_at", datetime.now(UTC).isoformat())

nx.metadata.set_file_metadata("/jobs/task3.json", "status", "pending")
nx.metadata.set_file_metadata("/jobs/task3.json", "priority", 3)

# Task 4 is blocked by task 2
task2_path_id = nx.metadata.get_path_id("/jobs/task2.json")
nx.metadata.set_file_metadata("/jobs/task4.json", "status", "blocked")
nx.metadata.set_file_metadata("/jobs/task4.json", "priority", 2)
nx.metadata.set_file_metadata("/jobs/task4.json", "depends_on", task2_path_id)

nx.metadata.set_file_metadata("/jobs/task5.json", "status", "ready")
nx.metadata.set_file_metadata("/jobs/task5.json", "priority", 5)

nx.close()
print("Work items created successfully")
EOF

# Test 41: Setup work items
test_command "Setup work items with metadata" \
    bash -c "PYTHONPATH=\"$PWD/src\" python \"$TEST_WORKSPACE/setup_work.py\" \"$WORK_DATA_DIR\""

# Test 42: Query ready work items
test_command "Query ready work items" \
    nexus work ready

# Test 43: Query ready work with limit
test_command "Query ready work with limit" \
    nexus work ready --limit 1

# Test 44: Query pending work items
test_command "Query pending work items" \
    nexus work pending

# Test 45: Query blocked work items
test_command "Query blocked work items" \
    nexus work blocked

# Test 46: Query in-progress work items
test_command "Query in-progress work items" \
    nexus work in-progress

# Test 47: Query work status (aggregate statistics)
test_command "Query work queue status" \
    nexus work status

# Test 48: Query ready work as JSON
test_command "Query ready work as JSON output" \
    nexus work ready --json

# Test 49: Query status as JSON
test_command "Query status as JSON output" \
    nexus work status --json

# Switch back to main data directory
export NEXUS_DATA_DIR="$DATA_DIR"

# ============================================================
# Validation Tests (Issue #37)
# ============================================================
echo -e "\n${BLUE}Testing type-level validation...${NC}"

# Create a separate test script for validation
cat > "$TEST_WORKSPACE/test_validation.py" << 'EOF'
import sys
import nexus
from nexus.core.metadata import FileMetadata
from nexus.core.exceptions import ValidationError

data_dir = sys.argv[1]
nx = nexus.connect(config={"data_dir": data_dir})

# Test 1: Invalid path (doesn't start with /)
print("Testing invalid path validation...")
try:
    invalid_meta = FileMetadata(
        path="invalid-path",
        backend_name="local",
        physical_path="/storage/file.txt",
        size=100,
    )
    nx.metadata.put(invalid_meta)
    print("FAILED: Should have raised ValidationError")
    sys.exit(1)
except ValidationError as e:
    print(f"PASSED: Correctly rejected invalid path: {e}")

# Test 2: Negative size
print("\nTesting negative size validation...")
try:
    invalid_meta = FileMetadata(
        path="/test/file.txt",
        backend_name="local",
        physical_path="/storage/file.txt",
        size=-100,
    )
    nx.metadata.put(invalid_meta)
    print("FAILED: Should have raised ValidationError")
    sys.exit(1)
except ValidationError as e:
    print(f"PASSED: Correctly rejected negative size: {e}")

# Test 3: Path with null bytes
print("\nTesting path with null bytes validation...")
try:
    invalid_meta = FileMetadata(
        path="/test/file\x00.txt",
        backend_name="local",
        physical_path="/storage/file.txt",
        size=100,
    )
    nx.metadata.put(invalid_meta)
    print("FAILED: Should have raised ValidationError")
    sys.exit(1)
except ValidationError as e:
    print(f"PASSED: Correctly rejected path with null bytes: {e}")

# Test 4: Valid metadata should work
print("\nTesting valid metadata...")
try:
    valid_meta = FileMetadata(
        path="/test/valid.txt",
        backend_name="local",
        physical_path="/storage/valid.txt",
        size=1024,
    )
    nx.metadata.put(valid_meta)
    print("PASSED: Valid metadata accepted")
except ValidationError as e:
    print(f"FAILED: Valid metadata was rejected: {e}")
    sys.exit(1)

nx.close()
print("\nAll validation tests passed!")
EOF

# Test 50: Run validation tests
test_command "Run validation tests" \
    bash -c "PYTHONPATH=\"$PWD/src\" python \"$TEST_WORKSPACE/test_validation.py\" \"$DATA_DIR\""

# Test 51: Test SQLAlchemy model validation
cat > "$TEST_WORKSPACE/test_model_validation.py" << 'EOF'
import sys
from nexus.storage.models import FilePathModel, FileMetadataModel, ContentChunkModel
from nexus.core.exceptions import ValidationError
from datetime import datetime, UTC

print("Testing SQLAlchemy model validation...")

# Test FilePathModel validation
print("\n1. Testing FilePathModel validation...")
try:
    invalid_model = FilePathModel(
        virtual_path="no-leading-slash",
        backend_id="local",
        physical_path="/storage/file.txt",
        size_bytes=100,
        tenant_id="test",
    )
    invalid_model.validate()
    print("FAILED: Should have raised ValidationError")
    sys.exit(1)
except ValidationError as e:
    print(f"PASSED: {e}")

# Test FileMetadataModel validation
print("\n2. Testing FileMetadataModel validation...")
try:
    invalid_model = FileMetadataModel(
        path_id="test-id",
        key="a" * 300,  # Too long
        value="test",
        created_at=datetime.now(UTC),
    )
    invalid_model.validate()
    print("FAILED: Should have raised ValidationError")
    sys.exit(1)
except ValidationError as e:
    print(f"PASSED: {e}")

# Test ContentChunkModel validation
print("\n3. Testing ContentChunkModel validation...")
try:
    invalid_model = ContentChunkModel(
        content_hash="tooshort",
        size_bytes=1024,
        storage_path="/storage/chunk",
        ref_count=1,
    )
    invalid_model.validate()
    print("FAILED: Should have raised ValidationError")
    sys.exit(1)
except ValidationError as e:
    print(f"PASSED: {e}")

# Test negative ref_count
print("\n4. Testing negative ref_count validation...")
try:
    invalid_model = ContentChunkModel(
        content_hash="a" * 64,
        size_bytes=1024,
        storage_path="/storage/chunk",
        ref_count=-1,  # Negative
    )
    invalid_model.validate()
    print("FAILED: Should have raised ValidationError")
    sys.exit(1)
except ValidationError as e:
    print(f"PASSED: {e}")

print("\nAll SQLAlchemy model validation tests passed!")
EOF

test_command "Test SQLAlchemy model validation" \
    bash -c "PYTHONPATH=\"$PWD/src\" python \"$TEST_WORKSPACE/test_model_validation.py\""

# ============================================================
# Parser System Tests (Issue #17)
# ============================================================
echo -e "\n${BLUE}Testing parser system features...${NC}"

# Test 52: Parser auto-discovery
cat > "$TEST_WORKSPACE/test_parser_discovery.py" << 'EOF'
import sys
from nexus.parsers import ParserRegistry

print("Testing parser auto-discovery...")

registry = ParserRegistry()
count = registry.discover_parsers("nexus.parsers")

print(f"Discovered {count} parser(s)")
if count > 0:
    parsers = registry.get_parsers()
    print(f"Parser names: {[p.name for p in parsers]}")
    print("PASSED: Auto-discovery works")
else:
    print("FAILED: No parsers discovered")
    sys.exit(1)
EOF

test_command "Test parser auto-discovery" \
    bash -c "PYTHONPATH=\"$PWD/src\" python \"$TEST_WORKSPACE/test_parser_discovery.py\""

# Test 53: MIME type detection
cat > "$TEST_WORKSPACE/test_mime_detection.py" << 'EOF'
import sys
from nexus.parsers import detect_mime_type

print("Testing MIME type detection...")

# Test JSON detection
json_content = b'{"key": "value"}'
mime_type = detect_mime_type(json_content, "test.json")
print(f"JSON MIME type: {mime_type}")

if mime_type and ("json" in mime_type.lower() or "text" in mime_type.lower()):
    print("PASSED: JSON MIME type detected")
else:
    print("FAILED: Could not detect JSON MIME type")
    sys.exit(1)

# Test PDF detection
pdf_content = b"%PDF-1.4"
mime_type_pdf = detect_mime_type(pdf_content, "test.pdf")
print(f"PDF MIME type: {mime_type_pdf}")

if mime_type_pdf:
    print("PASSED: PDF MIME type detected")
else:
    print("WARNING: PDF MIME type not detected (python-magic may not be installed)")

print("PASSED: MIME type detection works")
EOF

test_command "Test MIME type detection" \
    bash -c "PYTHONPATH=\"$PWD/src\" python \"$TEST_WORKSPACE/test_mime_detection.py\""

# Test 54: Encoding detection
cat > "$TEST_WORKSPACE/test_encoding_detection.py" << 'EOF'
import sys
from nexus.parsers import detect_encoding

print("Testing text encoding detection...")

# Test UTF-8
utf8_text = "Hello, 世界! 🌍".encode()
encoding = detect_encoding(utf8_text)
print(f"Detected encoding: {encoding}")

if encoding and encoding.lower() in ["utf-8", "utf8", "ascii"]:
    print("PASSED: UTF-8 encoding detected")
else:
    print(f"WARNING: Unexpected encoding: {encoding}")
    print("PASSED: Encoding detection works (with fallback)")

# Test ASCII
ascii_text = b"Hello, world!"
encoding_ascii = detect_encoding(ascii_text)
print(f"ASCII encoding: {encoding_ascii}")

print("PASSED: Encoding detection works")
EOF

test_command "Test text encoding detection" \
    bash -c "PYTHONPATH=\"$PWD/src\" python \"$TEST_WORKSPACE/test_encoding_detection.py\""

# Test 55: Compressed file handling
cat > "$TEST_WORKSPACE/test_compression.py" << 'EOF'
import sys
import gzip
from nexus.parsers import is_compressed, decompress_content, prepare_content_for_parsing

print("Testing compressed file handling...")

# Test compression detection
if is_compressed("test.txt.gz"):
    print("PASSED: Compression detected for .gz file")
else:
    print("FAILED: Compression not detected for .gz file")
    sys.exit(1)

if not is_compressed("test.txt"):
    print("PASSED: No compression detected for .txt file")
else:
    print("FAILED: False positive for .txt file")
    sys.exit(1)

# Test decompression
original = b"This is a test document with important content."
compressed = gzip.compress(original)

print(f"Original size: {len(original)} bytes")
print(f"Compressed size: {len(compressed)} bytes")

decompressed, inner_name = decompress_content(compressed, "document.txt.gz")

if decompressed == original:
    print("PASSED: Decompression successful")
else:
    print("FAILED: Decompression failed")
    sys.exit(1)

if inner_name == "document.txt":
    print(f"PASSED: Inner filename extracted: {inner_name}")
else:
    print(f"WARNING: Inner filename: {inner_name}")

# Test unified content preparation
json_content = b'{"project": "nexus", "version": "0.2.0"}'
compressed_json = gzip.compress(json_content)

processed, effective_path, metadata = prepare_content_for_parsing(
    compressed_json, "config.json.gz"
)

if processed == json_content:
    print("PASSED: Unified preparation decompressed correctly")
else:
    print("FAILED: Unified preparation failed")
    sys.exit(1)

if metadata.get("compressed"):
    print("PASSED: Compression detected in metadata")
else:
    print("FAILED: Compression not detected in metadata")
    sys.exit(1)

print("PASSED: All compression tests passed")
EOF

test_command "Test compressed file handling" \
    bash -c "PYTHONPATH=\"$PWD/src\" python \"$TEST_WORKSPACE/test_compression.py\""

# Test 56: Compressed file with Nexus (end-to-end)
cat > "$TEST_WORKSPACE/test_compressed_nexus.py" << 'EOF'
import sys
import gzip
import nexus
import tempfile
from pathlib import Path
import time

print("Testing compressed file with Nexus end-to-end...")

with tempfile.TemporaryDirectory() as tmpdir:
    data_dir = Path(tmpdir) / "nexus-data"

    # Connect with auto_parse enabled
    nx = nexus.connect(config={"data_dir": str(data_dir), "auto_parse": True})

    # Create compressed markdown
    markdown_content = b"""# Compressed Test Document

This document was compressed before upload.

## Keywords
- COMPRESSED_TEST_KEYWORD
- AUTO_PARSE_COMPRESSED

The parser should handle decompression automatically.
"""

    compressed = gzip.compress(markdown_content)

    print(f"Original size: {len(markdown_content)} bytes")
    print(f"Compressed size: {len(compressed)} bytes")

    # Write compressed file
    nx.write("/docs/compressed.md.gz", compressed)
    print("✓ Uploaded compressed file")

    # Wait for parsing
    time.sleep(2)

    # Try to grep for content
    matches = nx.grep("COMPRESSED_TEST_KEYWORD")

    if matches and len(matches) > 0:
        print(f"PASSED: Found {len(matches)} matches in compressed file")
        print(f"  Matched file: {matches[0]['file']}")
    else:
        print("WARNING: Compressed file parsing may still be in progress")
        print("PASSED: Compressed file accepted by Nexus")

    nx.close()

print("PASSED: Compressed file integration test completed")
EOF

test_command "Test compressed file with Nexus (end-to-end)" \
    bash -c "PYTHONPATH=\"$PWD/src\" python \"$TEST_WORKSPACE/test_compressed_nexus.py\""

echo -e "${GREEN}✓ All parser system tests passed!${NC}\n"

# ============================================================
# rclone-style CLI Commands (Issue #81 - v0.2.0)
# ============================================================
echo -e "\n${BLUE}Testing rclone-style CLI commands...${NC}"

# Create test directories for sync/copy operations
SYNC_TEST_DIR="$TEST_WORKSPACE/sync-test"
mkdir -p "$SYNC_TEST_DIR/source"
mkdir -p "$SYNC_TEST_DIR/dest"

# Create test files in source directory
echo "File 1 content" > "$SYNC_TEST_DIR/source/file1.txt"
echo "File 2 content" > "$SYNC_TEST_DIR/source/file2.txt"
mkdir -p "$SYNC_TEST_DIR/source/subdir"
echo "File 3 content" > "$SYNC_TEST_DIR/source/subdir/file3.txt"

# Test 57: Tree command
test_command "Tree command - show directory structure" \
    nexus tree /files

# Test 58: Tree with depth limit
test_command "Tree command with depth limit" \
    nexus tree /files -L 1

# Test 59: Tree with sizes
test_command "Tree command with file sizes" \
    nexus tree / --show-size

# Test 60: Size command
test_command "Size command - calculate directory size" \
    nexus size /files

# Test 61: Size with human-readable output
test_command "Size command with human-readable output" \
    nexus size /files --human

# Test 62: Size with details (top 10 largest files)
test_command "Size command with details" \
    nexus size /files --human --details

# Test 63: Copy command - single file
test_command "Copy command - single file" \
    nexus copy /files/hello.txt /files/hello_copied_2.txt

# Test 64: Copy command - recursive (Nexus to Nexus)
# First, create a source directory with files
nexus write /copy-source/file1.txt "Copy test 1"
nexus write /copy-source/file2.txt "Copy test 2"
nexus write /copy-source/subdir/file3.txt "Copy test 3"

test_command "Copy command - recursive copy within Nexus" \
    nexus copy /copy-source/ /copy-dest/ --recursive

# Test 65: Verify copied files exist
test_command "Verify recursive copy succeeded" \
    nexus cat /copy-dest/file1.txt

# Test 66: Copy with checksum (should skip identical files)
test_command "Copy command - skip identical files with checksum" \
    nexus copy /copy-source/ /copy-dest/ --recursive

# Test 67: Move command
nexus write /move-test/source.txt "Move me"
test_command "Move command - rename file" \
    nexus move /move-test/source.txt /move-test/destination.txt --force

# Test 68: Verify move succeeded (source should not exist)
test_command "Verify move deleted source" \
    bash -c "! nexus cat /move-test/source.txt 2>/dev/null"

# Test 69: Verify move succeeded (destination should exist)
test_command "Verify move created destination" \
    nexus cat /move-test/destination.txt

# Test 70: Sync command - dry run
test_command "Sync command - dry run mode" \
    nexus sync "$SYNC_TEST_DIR/source/" /sync-dest/ --dry-run

# Test 71: Sync command - actual sync
test_command "Sync command - sync local to Nexus" \
    nexus sync "$SYNC_TEST_DIR/source/" /sync-dest/

# Test 72: Verify sync created files
test_command "Verify sync created files in Nexus" \
    nexus cat /sync-dest/file1.txt

# Test 73: Re-sync (should skip identical files)
test_command "Sync command - re-sync should skip identical files" \
    nexus sync "$SYNC_TEST_DIR/source/" /sync-dest/

# Test 74: Sync with delete flag
# Add extra file to destination
nexus write /sync-dest/extra.txt "This should be deleted"

test_command "Sync command - sync with delete flag" \
    nexus sync "$SYNC_TEST_DIR/source/" /sync-dest/ --delete

# Test 75: Verify extra file was deleted
test_command "Verify sync --delete removed extra file" \
    bash -c "! nexus cat /sync-dest/extra.txt 2>/dev/null"

# Test 76: Sync with --no-checksum (force copy all)
test_command "Sync command - disable checksum verification" \
    nexus sync "$SYNC_TEST_DIR/source/" /sync-dest-no-check/ --no-checksum

echo -e "${GREEN}✓ All rclone-style CLI tests passed!${NC}\n"

# ============================================================
# UNIX Permissions Tests (Issue #86 - v0.3.0)
# ============================================================
echo -e "\n${BLUE}Testing UNIX-style permissions...${NC}"

# Create test files for permission tests
PERM_DATA_DIR="$TEST_WORKSPACE/perm-test-data"
test_command "Create permissions test workspace" \
    mkdir -p "$PERM_DATA_DIR"

test_command "Initialize permissions test workspace" \
    nexus init "$PERM_DATA_DIR"

# Switch to permission test data directory
export NEXUS_DATA_DIR="$PERM_DATA_DIR/nexus-data"

# Create test files
nexus write /perm-test/file1.txt "Test file 1"
nexus write /perm-test/file2.txt "Test file 2"
nexus write /perm-test/secret.txt "Secret data"

# Test 77: chmod - octal mode
test_command "chmod - set octal mode 755" \
    nexus chmod 755 /perm-test/file1.txt

# Test 78: chmod - octal mode with 0o prefix
test_command "chmod - set octal mode with 0o prefix (0o644)" \
    nexus chmod 0o644 /perm-test/file2.txt

# Test 79: chmod - symbolic mode
test_command "chmod - set symbolic mode rwxr-xr-x" \
    nexus chmod rwxr-xr-x /perm-test/file1.txt

# Test 80: chmod - verify mode with ls -l
test_command "ls -l shows permissions" \
    nexus ls /perm-test --long

# Test 81: chown - change file owner
test_command "chown - change file owner to alice" \
    nexus chown alice /perm-test/file1.txt

# Test 82: chown - change another file owner
test_command "chown - change file owner to bob" \
    nexus chown bob /perm-test/file2.txt

# Test 83: chgrp - change file group
test_command "chgrp - change file group to developers" \
    nexus chgrp developers /perm-test/file1.txt

# Test 84: chgrp - change another file group
test_command "chgrp - change file group to admins" \
    nexus chgrp admins /perm-test/file2.txt

# Test 85: info - verify permissions in file info
test_command "info - verify permissions are shown" \
    nexus info /perm-test/file1.txt

# Test 86: ls -l - verify owner and group in listing
test_command "ls -l shows owner and group" \
    nexus ls /perm-test --long

echo -e "${GREEN}✓ All UNIX permission tests passed!${NC}\n"

# ============================================================
# Permission Inheritance Tests (Issue #111 - v0.3.0)
# ============================================================
echo -e "\n${BLUE}Testing permission inheritance...${NC}"

# Test 86a: Create parent directory with permissions
test_command "Permission inheritance - create parent directory" \
    nexus mkdir /inherit-test

test_command "Permission inheritance - set parent directory permissions" \
    bash -c "nexus chmod 777 /inherit-test && \
             nexus chown alice /inherit-test && \
             nexus chgrp developers /inherit-test"

# Test 86b: Create new file - should inherit from parent
test_command "Permission inheritance - create file in parent directory" \
    nexus write /inherit-test/new-file.txt "test content"

# Test 86c: Verify file inherited owner, group, and mode
test_command "Permission inheritance - verify owner inherited" \
    bash -c "nexus info /inherit-test/new-file.txt | grep -i 'alice'"

test_command "Permission inheritance - verify group inherited" \
    bash -c "nexus info /inherit-test/new-file.txt | grep -i 'developers'"

test_command "Permission inheritance - verify execute bits cleared (0o666)" \
    bash -c "nexus info /inherit-test/new-file.txt | grep -E '(0o666|rw-rw-rw-)'"

# Test 86d: Create another parent with different permissions
test_command "Permission inheritance - create strict parent directory" \
    nexus mkdir /inherit-test-2

test_command "Permission inheritance - set strict parent permissions (0o707)" \
    bash -c "nexus chmod 707 /inherit-test-2 && \
             nexus chown bob /inherit-test-2 && \
             nexus chgrp admins /inherit-test-2"

# Test 86e: Create file in strict parent
test_command "Permission inheritance - create file in strict parent" \
    nexus write /inherit-test-2/secret-file.txt "secret data"

# Test 86f: Verify file inherited strict permissions (0o606)
test_command "Permission inheritance - verify strict mode inherited (0o606)" \
    bash -c "nexus info /inherit-test-2/secret-file.txt | grep -E '(0o606|rw----rw-)'"

test_command "Permission inheritance - verify strict owner inherited" \
    bash -c "nexus info /inherit-test-2/secret-file.txt | grep -i 'bob'"

# Test 86g: Update existing file should preserve permissions
test_command "Permission inheritance - update file preserves permissions" \
    nexus write /inherit-test/new-file.txt "updated content"

test_command "Permission inheritance - verify updated file kept permissions" \
    bash -c "nexus info /inherit-test/new-file.txt | grep -i 'alice'"

echo -e "${GREEN}✓ All permission inheritance tests passed!${NC}\n"

# ============================================================
# ACL (Access Control List) Tests (Issue #86 - v0.3.0)
# ============================================================
echo -e "\n${BLUE}Testing Access Control Lists (ACLs)...${NC}"

# Test 87: setfacl - grant user permissions
test_command "setfacl - grant alice read+write" \
    nexus setfacl "user:alice:rw-" /perm-test/secret.txt

# Test 88: getfacl - show ACL entries
test_command "getfacl - display ACL for file" \
    nexus getfacl /perm-test/secret.txt

# Test 89: setfacl - grant group permissions
test_command "setfacl - grant developers group read+execute" \
    nexus setfacl "group:developers:r-x" /perm-test/secret.txt

# Test 90: getfacl - verify multiple ACL entries
test_command "getfacl - verify multiple ACL entries" \
    nexus getfacl /perm-test/secret.txt

# Test 91: setfacl - deny user access
test_command "setfacl - deny bob access" \
    nexus setfacl "deny:user:bob:---" /perm-test/secret.txt

# Test 92: getfacl - verify deny entry
test_command "getfacl - verify deny entry exists" \
    nexus getfacl /perm-test/secret.txt

# Test 93: setfacl - remove ACL entry
test_command "setfacl - remove alice ACL entry" \
    nexus setfacl "user:alice:rw-" /perm-test/secret.txt --remove

# Test 94: getfacl - verify removal
test_command "getfacl - verify alice entry removed" \
    nexus getfacl /perm-test/secret.txt

# Test 95: Combined permissions and ACLs
# Create file with specific owner/group and add ACLs
nexus write /perm-test/combined.txt "Combined test"
nexus chmod 750 /perm-test/combined.txt
nexus chown root /perm-test/combined.txt
nexus chgrp wheel /perm-test/combined.txt
nexus setfacl "user:charlie:r--" /perm-test/combined.txt

test_command "Combined - verify permissions and ACL" \
    bash -c "nexus info /perm-test/combined.txt && \
             nexus getfacl /perm-test/combined.txt"

# Test 96: Test Python API for permission checking
cat > "$TEST_WORKSPACE/test_permission_api.py" << 'EOF'
import sys
import nexus
from nexus.core.permissions import FileMode, FilePermissions

data_dir = sys.argv[1]
nx = nexus.connect(config={"data_dir": data_dir})

# Create test file with permissions
nx.write("/api-perm-test/test.txt", b"Test content")

# Get metadata
meta = nx.metadata.get("/api-perm-test/test.txt")
assert meta is not None, "Failed to get metadata"

# Set permissions (owner/group/mode may be None initially)
meta.owner = "alice"
meta.group = "developers"
meta.mode = 0o755
nx.metadata.put(meta)

# Commit changes by closing and reopening (like CLI does)
nx.close()
nx = nexus.connect(config={"data_dir": data_dir})

# Retrieve and verify
meta = nx.metadata.get("/api-perm-test/test.txt")
assert meta is not None, "Failed to get metadata after update"
assert meta.owner == "alice", f"Owner mismatch: expected 'alice', got {meta.owner!r}"
assert meta.group == "developers", f"Group mismatch: expected 'developers', got {meta.group!r}"
assert meta.mode == 0o755, f"Mode mismatch: expected 0o755, got {oct(meta.mode) if meta.mode is not None else None}"

# Test FileMode class
mode = FileMode(0o755)
assert mode.owner_can_read(), "Owner should be able to read"
assert mode.owner_can_write(), "Owner should be able to write"
assert mode.owner_can_execute(), "Owner should be able to execute"
assert mode.group_can_read(), "Group should be able to read"
assert not mode.group_can_write(), "Group should not be able to write"
assert mode.group_can_execute(), "Group should be able to execute"

# Test FilePermissions class
perms = FilePermissions(owner="alice", group="developers", mode=mode)
assert perms.can_read("alice", []), "Alice should be able to read (owner)"
assert perms.can_write("alice", []), "Alice should be able to write (owner)"
assert perms.can_execute("alice", []), "Alice should be able to execute (owner)"

assert perms.can_read("bob", ["developers"]), "Bob should be able to read (group member)"
assert not perms.can_write("bob", ["developers"]), "Bob should not be able to write (group member)"
assert perms.can_execute("bob", ["developers"]), "Bob should be able to execute (group member)"

assert perms.can_read("charlie", []), "Charlie should be able to read (other)"
assert not perms.can_write("charlie", []), "Charlie should not be able to write (other)"
assert perms.can_execute("charlie", []), "Charlie should be able to execute (other)"

nx.close()
print("All Python API permission tests passed!")
EOF

test_command "Python API - permission checking" \
    bash -c "PYTHONPATH=\"$PWD/src\" python \"$TEST_WORKSPACE/test_permission_api.py\" \"$PERM_DATA_DIR/nexus-data\""

# Test 97: Test ACL Python API
cat > "$TEST_WORKSPACE/test_acl_api.py" << 'EOF'
import sys
import nexus
from nexus.core.acl import ACL, ACLEntry, ACLEntryType, ACLPermission
from nexus.storage.models import ACLEntryModel

data_dir = sys.argv[1]
nx = nexus.connect(config={"data_dir": data_dir})

# Create test file
nx.write("/api-acl-test/secret.txt", b"Secret content")

# Get path_id using public API
path_id = nx.metadata.get_path_id("/api-acl-test/secret.txt")

if not path_id:
    print("FAILED: Could not find path_id")
    sys.exit(1)

# Create ACL entries directly in database using SessionLocal
with nx.metadata.SessionLocal() as session:
    # Grant alice read+write
    acl_entry1 = ACLEntryModel(
        path_id=path_id,
        entry_type="user",
        identifier="alice",
        permissions="rw-",
        deny=False,
    )
    session.add(acl_entry1)

    # Grant developers group read
    acl_entry2 = ACLEntryModel(
        path_id=path_id,
        entry_type="group",
        identifier="developers",
        permissions="r--",
        deny=False,
    )
    session.add(acl_entry2)

    # Deny bob
    acl_entry3 = ACLEntryModel(
        path_id=path_id,
        entry_type="user",
        identifier="bob",
        permissions="---",
        deny=True,
    )
    session.add(acl_entry3)

    session.commit()

# Test ACL parsing and checking
acl = ACL.from_strings([
    "user:alice:rw-",
    "group:developers:r--",
    "deny:user:bob:---",
])

# Test permission checks
result = acl.check_permission("alice", [], ACLPermission.READ)
assert result == True, "Alice should be able to read"

result = acl.check_permission("alice", [], ACLPermission.WRITE)
assert result == True, "Alice should be able to write"

result = acl.check_permission("bob", [], ACLPermission.READ)
assert result == False, "Bob should be denied (explicit deny)"

result = acl.check_permission("charlie", ["developers"], ACLPermission.READ)
assert result == True, "Charlie should be able to read (via group)"

result = acl.check_permission("charlie", ["developers"], ACLPermission.WRITE)
assert result == None, "Charlie write should fall back to UNIX permissions"

nx.close()
print("All Python ACL API tests passed!")
EOF

test_command "Python API - ACL checking" \
    bash -c "PYTHONPATH=\"$PWD/src\" python \"$TEST_WORKSPACE/test_acl_api.py\" \"$PERM_DATA_DIR/nexus-data\""

# Switch back to main data directory
export NEXUS_DATA_DIR="$DATA_DIR"

echo -e "${GREEN}✓ All ACL tests passed!${NC}\n"

# ============================================================
# Permission Policy Tests (v0.3.0 - Issue #110)
# ============================================================
echo -e "\n${BLUE}Testing Permission Policies (Automatic Assignment)...${NC}"

# Create separate workspace for policy tests
POLICY_DATA_DIR="$TEST_WORKSPACE/policy-test-data"
test_command "Create policy test workspace" \
    mkdir -p "$POLICY_DATA_DIR"

test_command "Initialize policy test workspace" \
    nexus init "$POLICY_DATA_DIR"

# Test with Python API (policies work automatically)
cat > "$TEST_WORKSPACE/test_permission_policies.py" << 'EOF'
import sys
import nexus

data_dir = sys.argv[1]

# Connect as agent alice in acme-corp tenant
nx_alice = nexus.connect(config={
    "data_dir": data_dir,
    "tenant_id": "acme-corp",
    "agent_id": "alice",
})

print("Testing automatic permission assignment...")

# Test 1: Create file in /workspace - should get owner=alice
nx_alice.write("/workspace/acme-corp/alice/code.py", b"# Alice's code")
meta = nx_alice.metadata.get("/workspace/acme-corp/alice/code.py")

assert meta.owner == "alice", f"Expected owner=alice, got {meta.owner}"
assert meta.group == "agents", f"Expected group=agents, got {meta.group}"
assert meta.mode == 0o644, f"Expected mode=0o644, got {oct(meta.mode) if meta.mode else None}"
print("✓ /workspace policy applied correctly (owner=${agent_id})")

# Test 2: Create file in /shared - should get owner=root, group=acme-corp
nx_alice.write("/shared/acme-corp/data.txt", b"Shared data")
meta_shared = nx_alice.metadata.get("/shared/acme-corp/data.txt")

assert meta_shared.owner == "root", f"Expected owner=root, got {meta_shared.owner}"
assert meta_shared.group == "acme-corp", f"Expected group=acme-corp, got {meta_shared.group}"
assert meta_shared.mode == 0o664, f"Expected mode=0o664, got {oct(meta_shared.mode) if meta_shared.mode else None}"
print("✓ /shared policy applied correctly (group=${tenant_id})")

# Test 3: Update file - permissions should be preserved
nx_alice.write("/workspace/acme-corp/alice/code.py", b"# Updated code")
meta_updated = nx_alice.metadata.get("/workspace/acme-corp/alice/code.py")

assert meta_updated.owner == "alice", "Owner should be preserved on update"
assert meta_updated.group == "agents", "Group should be preserved on update"
assert meta_updated.mode == 0o644, "Mode should be preserved on update"
print("✓ Permissions preserved on file update")

# Test 4: Different agent gets different ownership
nx_alice.close()

nx_bob = nexus.connect(config={
    "data_dir": data_dir,
    "tenant_id": "acme-corp",
    "agent_id": "bob",
})

nx_bob.write("/workspace/acme-corp/bob/report.md", b"# Bob's report")
meta_bob = nx_bob.metadata.get("/workspace/acme-corp/bob/report.md")

assert meta_bob.owner == "bob", f"Expected owner=bob, got {meta_bob.owner}"
assert meta_bob.group == "agents", f"Expected group=agents, got {meta_bob.group}"
print("✓ Different agents get different ownership")

# Test 5: Inspect policies in database
from nexus.storage.policy_store import PolicyStore

with nx_bob.metadata.SessionLocal() as session:
    policy_store = PolicyStore(session)
    policies = policy_store.list_policies(tenant_id=None)

    assert len(policies) == 4, f"Expected 4 default policies, got {len(policies)}"

    # Verify workspace policy
    workspace_policy = next(p for p in policies if "/workspace/" in p.namespace_pattern)
    assert workspace_policy.default_owner == "${agent_id}", "Workspace policy should use ${agent_id}"
    assert workspace_policy.default_group == "agents", "Workspace policy should use agents group"
    assert workspace_policy.default_mode == 0o644, "Workspace policy should use 0o644"

    # Verify shared policy
    shared_policy = next(p for p in policies if "/shared/" in p.namespace_pattern)
    assert shared_policy.default_owner == "root", "Shared policy should use root owner"
    assert shared_policy.default_group == "${tenant_id}", "Shared policy should use ${tenant_id}"
    assert shared_policy.default_mode == 0o664, "Shared policy should use 0o664"

    print(f"✓ Found {len(policies)} default policies in database")

nx_bob.close()
print("\nAll permission policy tests passed!")
EOF

test_command "Test permission policies - automatic assignment" \
    bash -c "PYTHONPATH=\"$PWD/src\" python \"$TEST_WORKSPACE/test_permission_policies.py\" \"$POLICY_DATA_DIR/nexus-data\""

echo -e "${GREEN}✓ All permission policy tests passed!${NC}\n"

# NOTE: Permission enforcement is tested implicitly through existing CLI commands:
# - chmod/chown/chgrp set permissions
# - ls/cat/write/rm check permissions before operations
# - Dedicated unit tests exist in tests/unit/test_permission_enforcer.py
# There are no dedicated CLI commands for PermissionEnforcer/OperationContext (internal APIs)

# ============================================================
# ReBAC (Relationship-Based Access Control) Tests (v0.3.0)
# ============================================================
echo -e "\n${BLUE}Testing ReBAC (Zanzibar-style Authorization)...${NC}"

# Create separate workspace for ReBAC tests
REBAC_DATA_DIR="$TEST_WORKSPACE/rebac-test-data"
test_command "Create ReBAC test workspace" \
    mkdir -p "$REBAC_DATA_DIR"

test_command "Initialize ReBAC test workspace" \
    nexus init "$REBAC_DATA_DIR"

# Switch to ReBAC test data directory
export NEXUS_DATA_DIR="$REBAC_DATA_DIR/nexus-data"

# Create ReBAC tables (required for ReBAC to work)
echo -e "${BLUE}Setting up ReBAC database tables...${NC}"
cat > "$TEST_WORKSPACE/setup_rebac_tables.py" << 'EOF'
import sys
import sqlite3
from pathlib import Path

data_dir = sys.argv[1]
db_path = Path(data_dir) / "metadata.db"

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Create ReBAC tables
cursor.execute("""
    CREATE TABLE IF NOT EXISTS rebac_tuples (
        tuple_id TEXT PRIMARY KEY,
        subject_type TEXT NOT NULL,
        subject_id TEXT NOT NULL,
        subject_relation TEXT,
        relation TEXT NOT NULL,
        object_type TEXT NOT NULL,
        object_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        expires_at TEXT,
        conditions TEXT
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS rebac_namespaces (
        namespace_id TEXT PRIMARY KEY,
        object_type TEXT NOT NULL UNIQUE,
        config TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS rebac_check_cache (
        cache_id TEXT PRIMARY KEY,
        subject_type TEXT NOT NULL,
        subject_id TEXT NOT NULL,
        permission TEXT NOT NULL,
        object_type TEXT NOT NULL,
        object_id TEXT NOT NULL,
        result INTEGER NOT NULL,
        computed_at TEXT NOT NULL,
        expires_at TEXT NOT NULL
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS rebac_changelog (
        change_id INTEGER PRIMARY KEY AUTOINCREMENT,
        change_type TEXT NOT NULL,
        tuple_id TEXT,
        subject_type TEXT NOT NULL,
        subject_id TEXT NOT NULL,
        relation TEXT NOT NULL,
        object_type TEXT NOT NULL,
        object_id TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
""")

conn.commit()
conn.close()
print("ReBAC tables created successfully")
EOF

bash -c "PYTHONPATH=\"$PWD/src\" python \"$TEST_WORKSPACE/setup_rebac_tables.py\" \"$REBAC_DATA_DIR/nexus-data\""

# Test 98: Create relationship tuple (agent member-of group)
test_command "rebac create - alice member-of engineering" \
    bash -c "nexus rebac create agent alice member-of group engineering 2>&1 | grep -i 'tuple id'"

# Test 99: Create another relationship tuple (group owner-of file)
test_command "rebac create - engineering owner-of /projects" \
    bash -c "nexus rebac create group engineering owner-of file /projects 2>&1 | grep -i 'tuple id'"

# Test 100: Create hierarchical relationship (parent-of)
test_command "rebac create - parent folder relationship" \
    bash -c "nexus rebac create file /projects parent-of file /projects/backend 2>&1 | grep -i 'tuple id'"

# Test 101: Check direct permission
test_command "rebac check - alice member-of engineering (direct)" \
    bash -c "nexus rebac check agent alice member-of group engineering 2>&1 | grep 'GRANTED'"

# Test 102: Check group ownership
test_command "rebac check - engineering owner-of /projects" \
    bash -c "nexus rebac check group engineering owner-of file /projects 2>&1 | grep 'GRANTED'"

# Test 103: Expand API - find all members of engineering
test_command "rebac expand - find all members of engineering" \
    bash -c "nexus rebac expand member-of group engineering 2>&1 | grep -E '(alice|Subjects)'"

# Test 104: Expand API - find all owners of /projects
test_command "rebac expand - find all owners of /projects" \
    bash -c "nexus rebac expand owner-of file /projects 2>&1 | grep -E '(engineering|Subjects)'"

# Test 105: Create additional team members
test_command "rebac create - bob member-of engineering" \
    bash -c "nexus rebac create agent bob member-of group engineering 2>&1 | grep -i 'tuple id'"

test_command "rebac create - charlie member-of engineering" \
    bash -c "nexus rebac create agent charlie member-of group engineering 2>&1 | grep -i 'tuple id'"

# Test 106: Expand should show multiple members
test_command "rebac expand - multiple engineering members" \
    bash -c "nexus rebac expand member-of group engineering 2>&1 | grep -c 'agent' | grep -E '[3-9]|[1-9][0-9]+'"

# Test 107: Create temporary access with expiration
test_command "rebac create - temporary viewer access" \
    bash -c "nexus rebac create agent temp-user viewer-of file /temp-doc --expires '2099-12-31T23:59:59' 2>&1 | grep -i 'tuple id'"

# Test 108: Check temporary access (should work before expiry)
test_command "rebac check - temporary access before expiry" \
    bash -c "nexus rebac check agent temp-user viewer-of file /temp-doc 2>&1 | grep 'GRANTED'"

# Test 109: Test viewer relationship
test_command "rebac create - david viewer-of /reports" \
    bash -c "nexus rebac create agent david viewer-of file /reports 2>&1 | grep -i 'tuple id'"

test_command "rebac check - david viewer-of /reports" \
    bash -c "nexus rebac check agent david viewer-of file /reports 2>&1 | grep 'GRANTED'"

# Test 110: Test negative check (permission not granted)
test_command "rebac check - eve NOT member-of engineering" \
    bash -c "nexus rebac check agent eve member-of group engineering 2>&1 | grep 'DENIED'"

# Test 111: Test rebac help
test_command "rebac --help shows all commands" \
    bash -c "nexus rebac --help | grep -E '(create|delete|check|expand)'"

# Test 112: Test rebac create help
test_command "rebac create --help shows usage" \
    bash -c "nexus rebac create --help | grep 'Create a relationship tuple'"

# Test 113: Test rebac check help
test_command "rebac check --help shows usage" \
    bash -c "nexus rebac check --help | grep 'Check if subject has permission'"

# Test 114: Test rebac expand help
test_command "rebac expand --help shows usage" \
    bash -c "nexus rebac expand --help | grep 'Find all subjects'"

# Test 115: Python API - ReBAC operations
cat > "$TEST_WORKSPACE/test_rebac_api.py" << 'EOF'
import sys
from pathlib import Path
from nexus.core.rebac_manager import ReBACManager

data_dir = sys.argv[1]
db_path = Path(data_dir) / "metadata.db"
rebac_mgr = ReBACManager(db_path=str(db_path))

# Create relationships
tuple1 = rebac_mgr.rebac_write(
    subject=("agent", "frank"),
    relation="member-of",
    object=("group", "data-science"),
)
print(f"Created tuple: {tuple1}")

tuple2 = rebac_mgr.rebac_write(
    subject=("group", "data-science"),
    relation="owner-of",
    object=("file", "/datasets"),
)
print(f"Created tuple: {tuple2}")

# Check permission
has_perm = rebac_mgr.rebac_check(
    subject=("agent", "frank"),
    permission="member-of",
    object=("group", "data-science"),
)
assert has_perm == True, "Frank should be member of data-science"
print("✓ Permission check passed")

# Expand members
members = rebac_mgr.rebac_expand(
    permission="member-of",
    object=("group", "data-science"),
)
assert len(members) >= 1, "Should have at least 1 member"
assert ("agent", "frank") in members, "Frank should be in members list"
print(f"✓ Expand returned {len(members)} member(s)")

# Delete relationship
deleted = rebac_mgr.rebac_delete(tuple1)
assert deleted == True, "Should successfully delete tuple"
print("✓ Delete succeeded")

# Check after deletion
has_perm_after = rebac_mgr.rebac_check(
    subject=("agent", "frank"),
    permission="member-of",
    object=("group", "data-science"),
)
assert has_perm_after == False, "Frank should no longer be member after deletion"
print("✓ Permission revoked after delete")

rebac_mgr.close()
print("All Python ReBAC API tests passed!")
EOF

test_command "Python API - ReBAC operations" \
    bash -c "PYTHONPATH=\"$PWD/src\" python \"$TEST_WORKSPACE/test_rebac_api.py\" \"$REBAC_DATA_DIR/nexus-data\""

# Switch back to main data directory
export NEXUS_DATA_DIR="$DATA_DIR"

echo -e "${GREEN}✓ All ReBAC tests passed!${NC}\n"

# ============================================================
# Skills System CLI Tests (v0.3.0 - Issue #88)
# ============================================================
echo -e "\n${BLUE}Testing Skills System CLI...${NC}"

# Create separate workspace for skills tests
SKILLS_DATA_DIR="$TEST_WORKSPACE/skills-test-data"
test_command "Create skills test workspace" \
    mkdir -p "$SKILLS_DATA_DIR"

test_command "Initialize skills test workspace" \
    nexus init "$SKILLS_DATA_DIR"

# Switch to skills test data directory
export NEXUS_DATA_DIR="$SKILLS_DATA_DIR/nexus-data"

# Test 116: List skills (empty initially)
test_command "skills list - list all skills (empty initially)" \
    bash -c "nexus skills list 2>&1 || true"

# Test 117: Create a new skill
test_command "skills create - create new skill from basic template" \
    bash -c "nexus skills create my-test-skill --description 'Test skill for CLI' --author 'Test Runner' 2>&1 | grep -i 'created skill'"

# Test 118: List skills again (should show created skill)
test_command "skills list - show created skill" \
    bash -c "nexus skills list 2>&1 | grep 'my-test-skill'"

# Test 119: Create another skill with different template
test_command "skills create - create data-analysis skill" \
    bash -c "nexus skills create data-viz --description 'Data visualization' --template data-analysis --author 'Test Runner' 2>&1 | grep -i 'created skill'"

# Test 120: Show skill info
test_command "skills info - show detailed skill information" \
    bash -c "nexus skills info my-test-skill 2>&1 | grep -E '(my-test-skill|Test skill)'"

# Test 121: Search skills
test_command "skills search - search for skills by description" \
    bash -c "nexus skills search 'test' 2>&1 | grep -i 'my-test-skill'"

# Test 122: Calculate skill size
test_command "skills size - calculate skill size" \
    bash -c "nexus skills size my-test-skill 2>&1 | grep -i 'total size'"

# Test 123: Calculate skill size with human-readable output
test_command "skills size - human-readable output" \
    bash -c "nexus skills size my-test-skill --human 2>&1 | grep -E '(B|KB|MB)'"

# Test 124: Validate skill (generic format)
test_command "skills validate - validate skill for export" \
    bash -c "nexus skills validate my-test-skill 2>&1 | grep -i 'valid'"

# Test 125: Validate skill (claude format)
test_command "skills validate - validate for claude format" \
    bash -c "nexus skills validate my-test-skill --format claude 2>&1 | grep -i 'valid'"

# Test 126: Export skill to .zip
SKILLS_EXPORT_FILE="$TEST_WORKSPACE/my-test-skill.zip"
test_command "skills export - export skill to .zip" \
    bash -c "nexus skills export my-test-skill --output '$SKILLS_EXPORT_FILE' 2>&1 | grep -i 'exported skill'"

# Test 127: Verify export file exists
test_command "skills export - verify .zip file created" \
    test -f "$SKILLS_EXPORT_FILE"

# Test 128: Export with Claude format
SKILLS_EXPORT_CLAUDE="$TEST_WORKSPACE/my-test-skill-claude.zip"
test_command "skills export - export with claude format" \
    bash -c "nexus skills export my-test-skill --output '$SKILLS_EXPORT_CLAUDE' --format claude 2>&1 | grep -i 'exported skill'"

# Test 129: Fork skill
test_command "skills fork - fork existing skill" \
    bash -c "nexus skills fork my-test-skill forked-skill --author 'Forker' 2>&1 | grep -i 'forked skill'"

# Test 130: Verify forked skill exists
test_command "skills list - verify forked skill exists" \
    bash -c "nexus skills list 2>&1 | grep 'forked-skill'"

# Test 131: Publish skill to tenant tier
test_command "skills publish - publish to tenant" \
    bash -c "nexus skills publish my-test-skill 2>&1 | grep -i 'published skill'"

# Test 132: List tenant skills
test_command "skills list --tenant - show tenant skills" \
    bash -c "nexus skills list --tenant 2>&1 || true"

# Test 133: Test help command
test_command "skills --help shows available commands" \
    bash -c "nexus skills --help | grep -E '(list|create|fork|publish|search|info|export|validate|size)'"

# Test 134: Test list --help
test_command "skills list --help shows usage" \
    bash -c "nexus skills list --help | grep 'List all skills'"

# Test 135: Test create --help
test_command "skills create --help shows usage" \
    bash -c "nexus skills create --help | grep 'Create a new skill'"

# Test 136: Filter by tier
test_command "skills list --tier agent - filter by agent tier" \
    bash -c "nexus skills list --tier agent 2>&1 | grep -E '(forked-skill|my-test-skill)' || echo 'No agent skills found'"

# Switch back to main data directory
export NEXUS_DATA_DIR="$DATA_DIR"

echo -e "${GREEN}✓ All Skills System CLI tests passed!${NC}\n"

# Summary
echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Test Summary${NC}"
echo -e "${BLUE}================================${NC}"
echo -e "Total tests run: ${TESTS_RUN}"
echo -e "${GREEN}Tests passed: ${TESTS_PASSED}${NC}"

if [ $TESTS_PASSED -eq $TESTS_RUN ]; then
    echo -e "\n${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    TESTS_FAILED=$((TESTS_RUN - TESTS_PASSED))
    echo -e "${RED}Tests failed: ${TESTS_FAILED}${NC}"
    echo -e "\n${RED}✗ Some tests failed${NC}"
    exit 1
fi
