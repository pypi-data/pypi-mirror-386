import os
import sys
import shutil
import logging
from pathlib import Path

# --- Setup ---
# Add src to python path to allow imports for standalone execution
# This makes the script runnable from anywhere.
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "src"))

# Now we can import the project modules
from glocaltext.config import load_config
from glocaltext.workflow import capture_text_matches, precise_write_back

# Configure basic logging for the test
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Test Configuration ---
TEST_DIR = project_root / "tests"
TEMP_DATA_DIR = TEST_DIR / "temp_test_data"
INPUT_FILE = TEMP_DATA_DIR / "test_input.md"
OUTPUT_DIR = TEMP_DATA_DIR / "output"
CONFIG_FILE = TEMP_DATA_DIR / "config.yaml"
EXPECTED_OUTPUT_FILE = OUTPUT_DIR / "test_input.md"

INPUT_MD_CONTENT = """
# Test Document

This is the first sentence.

This is the second sentence, which is a bit longer.

> This is a blockquote, it should be translated.

And this is a third sentence after a newline.
"""

# This config will point to the files we are about to create.
# It uses a simple regex to extract full sentences.
# Using as_posix() for cross-platform path compatibility in YAML.
CONFIG_YAML_CONTENT = f"""
providers:
  # Dummy provider, not used in this test since we mock the translation
  dummy:
    model: "dummy-model"

tasks:
  - name: "markdown_test"
    source_lang: "en"
    target_lang: "zh-TW" # Target language is just for metadata in this test
    targets:
      - "{INPUT_FILE.relative_to(project_root).as_posix()}" # Use relative path from project root
    extraction_rules:
      - '^(?!#)([^\\n]+)$' # Extracts non-empty lines that don't start with '#'
    output:
      in_place: false
      path: "{OUTPUT_DIR.relative_to(project_root).as_posix()}" # Use relative path for output
"""


def setup_test_environment():
    """Creates temporary directories and files needed for the test."""
    logging.info(f"Setting up test environment in: {TEMP_DATA_DIR}")
    # Clean up previous runs if any
    if TEMP_DATA_DIR.exists():
        shutil.rmtree(TEMP_DATA_DIR)

    # Create directories
    TEMP_DATA_DIR.mkdir(parents=True)
    OUTPUT_DIR.mkdir()

    # Create test files
    INPUT_FILE.write_text(INPUT_MD_CONTENT, "utf-8")
    CONFIG_FILE.write_text(CONFIG_YAML_CONTENT, "utf-8")
    logging.info("Test files created.")


def cleanup_test_environment():
    """Removes temporary directories and files."""
    if TEMP_DATA_DIR.exists():
        logging.info(f"Cleaning up test environment: {TEMP_DATA_DIR}")
        shutil.rmtree(TEMP_DATA_DIR)


def run_test_workflow():
    """Executes the main E2E test workflow."""
    try:
        # 1. Load configuration
        # The workflow's file finding logic is relative to CWD, so we must run from the project root.
        os.chdir(project_root)
        logging.info(f"Changed directory to {project_root} for config loading.")

        config = load_config(CONFIG_FILE)
        markdown_task = next(
            (t for t in config.tasks if t.name == "markdown_test"), None
        )
        if not markdown_task:
            raise RuntimeError("Test task 'markdown_test' not found in config.")

        # 2. Capture text matches from the input file
        logging.info("Phase 1: Capturing text matches...")
        matches = capture_text_matches(task=markdown_task, debug=True)

        if not matches:
            raise AssertionError("Assertion Failed: No text matches were captured.")

        logging.info(f"Captured {len(matches)} matches.")

        # 3. Mock the translation step (Phases 2-4)
        logging.info("Phase 2-4: Mocking translation...")
        for match in matches:
            match.translated_text = f"{match.original_text} [Translated]"

        # 4. Write the translated content back to the output directory (Phase 5)
        logging.info("Phase 5: Writing back translations...")
        precise_write_back(matches, task_output=markdown_task.output)

        # 5. Verify the output
        logging.info("Phase 6: Verifying output...")
        if not EXPECTED_OUTPUT_FILE.exists():
            raise FileNotFoundError(
                f"Assertion Failed: Expected output file was not created at {EXPECTED_OUTPUT_FILE}"
            )

        output_content = EXPECTED_OUTPUT_FILE.read_text("utf-8")

        if "[Translated]" not in output_content:
            raise AssertionError(
                "Assertion Failed: '[Translated]' tag not found in the output file."
            )

        logging.info(
            "Verification successful: Output file contains translated content."
        )

        return True

    except (Exception, AssertionError) as e:
        logging.error(f"TEST FAILED: {e}", exc_info=True)
        return False


def main():
    """Main function to set up, run, and tear down the test."""
    setup_test_environment()
    success = False
    try:
        success = run_test_workflow()
    finally:
        cleanup_test_environment()

    if success:
        print("\\n✅ End-to-end workflow test PASSED!")
    else:
        print("\\n❌ End-to-end workflow test FAILED.")
        sys.exit(1)


if __name__ == "__main__":
    main()
