# DSPyTeach – DSPy File Teaching Analyzer

---

[![PyPI](https://img.shields.io/pypi/v/dspyteach.svg?include_prereleases&cacheSeconds=60&t=1)](https://pypi.org/project/dspyteach/)
[![Downloads](https://img.shields.io/pypi/dm/dspyteach.svg?cacheSeconds=300)](https://pypi.org/project/dspyteach/)
[![TestPyPI](https://img.shields.io/badge/TestPyPI-dspyteach-informational?cacheSeconds=300)](https://test.pypi.org/project/dspyteach/)
[![CI](https://github.com/AcidicSoil/dspy-file/actions/workflows/release.yml/badge.svg)](https://github.com/AcidicSoil/DSPyTeach/actions/workflows/release.yml)
[![Repo](https://img.shields.io/badge/GitHub-AcidicSoil%2FDSPyTeach-181717?logo=github)](https://github.com/AcidicSoil/DSPyTeach)

---

## DSPy-powered CLI that analyzes source files (one or many) and produces teaching briefs

**Each run captures:**

- an overview of the file and its major sections
- key teaching points, workflows, and pitfalls highlighted in the material
- a polished markdown brief suitable for sharing with learners

The implementation mirrors the multi-file tutorial (`tutorials/multi-llmtxt_generator`) but focuses on per-file inference. The program is split into:

- `dspy_file/signatures.py` – DSPy signatures that define inputs/outputs for each step
- `dspy_file/file_analyzer.py` – the main DSPy module that orchestrates overview, teaching extraction, and report composition. It now wraps the final report stage with `dspy.Refine`, pushing for 450–650+ word briefs.
- `dspy_file/file_helpers.py` – utilities for loading files and rendering the markdown brief
- `dspy_file/analyze_file_cli.py` – command line entry point that configures the local model and prints results. It can walk directories, apply glob filters, and batch-generate briefs.

---

## Quick start

1. Confirm Python 3.10–3.12 is available and pull at least one OpenAI-compatible model (Ollama, LM Studio, or a hosted provider).
2. From the repository root, create an isolated environment and install dependencies:

### Linux

  ```shell
  uv build
  uv sync
  source .venv/bin/activate
  ```

### Windows

  ```shell
  uv build
  uv sync
  .venv/scripts/activate
  ```

3. Run a smoke test to confirm the CLI is wired up:

  ```bash
  dspyteach --help
  ```

  Expected result: the help output lists available flags and displays the active version string.

4. Analyze a sample file to confirm end-to-end output:

   ```bash
   dspyteach path/to/example.py
   ```

   Expected result: the command prints a teaching brief to stdout and writes a `.teaching.md` file under `dspy_file/data/`.

---

## Requirements

- Python 3.10-3.12+
- DSPy installed in the environment
- A language-model backend. You can choose between:
  - **Ollama** (default): run it locally with the model `hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:Q6_K_XL` pulled.
  - **LM Studio** (OpenAI-compatible): start the LM Studio server (`lms server start`) and download a model such as `qwen3-4b-instruct-2507@q6_k_xl`.
  - **Any other OpenAI-compatible endpoint**: point the CLI at a hosted provider by supplying an API base URL and key (defaults to `gpt-5`).
- (Optional) `.env` file for DSPy configuration. `dotenv` loads variables such as `DSPYTEACH_PROVIDER`, `DSPYTEACH_MODEL`, `DSPYTEACH_API_BASE`, `DSPYTEACH_API_KEY`, and `OPENAI_API_KEY`.

---

## Example output

[example-data after running a few passes](https://github.com/AcidicSoil/DSPyTeach/tree/main/example-data)

---

## Installation

### Install with uv (recommended for local development)

<https://github.com/astral-sh/uv>

### Install from PyPI

```bash
uv pip install dspyteach
```

Expected result: running `dspyteach --help` prints the CLI usage banner from the installed package.

### Configure the language model

The CLI supports configurable OpenAI-compatible providers in addition to the default Ollama runtime. You can override the backend via CLI options or environment variables:

```bash
# Use LM Studio's OpenAI-compatible server with its default port
dspyteach path/to/project \
  --provider lmstudio \
  --model osmosis-mcp-4b@q8_0 \
  --api-base http://localhost:1234/v1
```

```bash
# Environment variable alternative (e.g. inside .env)
export DSPYTEACH_PROVIDER=lmstudio
export DSPYTEACH_MODEL=osmosis-mcp-4b@q8_0
export DSPYTEACH_API_BASE=http://localhost:1234/v1
dspyteach path/to/project
```

### LM-Studio Usage Notes

[LM Studio configuration guide](https://github.com/AcidicSoil/DSPyTeach/blob/main/docs/lm-studio-provider.md)

LM Studio must expose its local server before you run the CLI. Start it from the Developer tab inside the LM Studio app or via `lms server start` details in the [LM Studio configuration guide](https://github.com/AcidicSoil/DSPyTeach/blob/main/docs/lm-studio-provider.md); otherwise the CLI will exit early with a connection warning.

### OpenAI-compatible others usage

For hosted OpenAI-compatible services, set `--provider openai`, supply `--api-base` if needed, and pass an API key either through `--api-key`, `DSPYTEACH_API_KEY`, or the standard `OPENAI_API_KEY`. To keep a local Ollama model running after the CLI finishes, add `--keep-provider-alive`.

## Usage

Run the CLI to extract a teaching brief from a single file:

```bash
dspyteach path/to/your_file
```

Expected result: the CLI prints a markdown teaching brief to stdout and saves a copy under `dspy_file/data/`.

You can also point the CLI at a directory. The tool will recurse by default:

```bash
dspyteach path/to/project --glob "**/*.py" --glob "**/*.md"
```

Expected result: each matched file produces its own `.teaching.md` report in the output directory.

Use `--non-recursive` to stay in the top-level directory, add `--glob` repeatedly to narrow the target set, and pass `--raw` to print the raw DSPy prediction object instead of the formatted report.

### Command examples

- **Analyze a single markdown file**

  ```bash
  dspyteach docs/example.md
  ```

  Expected result: the CLI prints a teaching brief and stores `docs__example.teaching.md` in the output directory.

- **Process a repository while skipping generated assets**

  ```bash
  dspyteach ./repo \
    --glob "**/*.py" \
    --glob "**/*.md" \
    --exclude-dirs "build/,dist/,data/"
  ```

  Expected result: only `.py` and `.md` files outside the excluded directories are analyzed.

- **Generate refactor templates instead of teaching briefs**

  ```bash
  dspyteach --mode refactor ./repo
  ```

- **Refactoring prompts easily**

  ```bash
  dt -m refactor C:\Users\user\projects\WIP\.__pre-temp-prompts\temp-prompts-organized\ --provider lmstudio --api-base http://127.0.0.1:1234/v1 -ed prompt-front-matter/ -o ..\dspyteach\data -i
  ```

  Expected result: `.refactor.md` files appear alongside the teaching outputs with guidance tailored to the selected prompt.

Need to double-check files before the model runs? Add `--confirm-each` (alias `--interactive`) to prompt before every file, accepting with Enter or skipping with `n`.

To omit specific subdirectories entirely, pass one or more `--exclude-dirs` options. Each value can list comma-separated relative paths (for example `--exclude-dirs "build/,venv/" --exclude-dirs data/raw`). The analyzer ignores any files whose path begins with the provided prefixes.

Prefer short flags? The common options include `-r` (`--raw`), `-m` (`--mode`), `-nr` (`--non-recursive`), `-g` (`--glob`), `-i` (`--confirm-each`), `-ed` (`--exclude-dirs`), and `-o` (`--output-dir`). Mix and match them as needed.

## Adding Custom Prompts

The application can be extended with custom prompts for different analysis modes. When more than one prompt template (`.md` file) exists in the `dspy_file/prompts/` directory, the CLI will display a picker, allowing you to choose which prompt to use for the analysis.

To add a new prompt:

1. Create a new Markdown file (e.g., `my_custom_prompt.md`) inside the `dspy_file/prompts/` directory.
2. The name of the file (without the `.md` extension) will be used to identify the prompt in the picker.
3. Write your prompt content inside this new file.

For example, to add a prompt for summarizing code, you could create `dspy_file/prompts/summarize_code.md` with your desired instructions. The next time you run in a mode that uses prompts, `summarize_code` will appear as an option.

## Refactor files/dirs

Want to scaffold refactor prompt templates instead of teaching briefs? Switch the mode:

```bash
dspyteach --mode refactor path/to/project --glob "**/*.md"
```

---

---

## **clarity on what happens when in teaching mode**

### both of these commands shown below would create new directories in the path outside the cwd that you ran the commands from and the directories would be the following: so in this case it would be exactly ["C:\Users\user\projects\WIP\NAME-OF-CWD + (the new files it creates which will be...)dspyteach\teach\data\00-ideation\architecture\adr-new.architecture.md"]

#### "00-ideation\architecture\adr-new.architecture.md" are unique to my personal setup so your output would be a mirrored version of the target path recursively

directory analyzed --> "~\projects\WIP\ .__pre-temp-prompts\temp-prompts-organized" so all under temp-prompts-organized are analyzed unless flag is passed to do otherwise, ie., non-recursive or -i AKA --interactive (file by file of target path).

---

```bash
dt -m refactor C:\Users\user\projects\WIP\.__pre-temp-prompts\temp-prompts-organized\ --provider lmstudio --api-base <http://127.0.0.1:1234/v1> -ed prompt-front-matter/ -o ..\dspyteach\data -i
```

```bash
dt C:\Users\user\projects\WIP\.__pre-temp-prompts\temp-prompts-organized\ --provider lmstudio --api-base <http://127.0.0.1:1234/v1> -ed prompt-front-matter/ -o ..\dspyteach\teach\data -i
```

---

## Additional Information

The CLI reuses the same file resolution pipeline but feeds each document through the bundled `dspy-file_refactor-prompt_template.md` instructions (packaged under `dspy_file/prompts/`), saving `.refactor.md` files alongside the teaching reports. Teaching briefs remain the default (`--mode teach`), so existing workflows continue to work unchanged.

When multiple templates live in `dspy_file/prompts/`, the refactor mode surfaces a picker so you can choose which one to use. You can also point at a specific template explicitly with `-p/--prompt`, passing either a bundled name (`-p refactor_prompt_template`) or an absolute path to your own Markdown prompt.

Each run only executes the analyzer for the chosen mode. When you pass `--mode refactor` the teaching inference pipeline stays idle, and you can alias the command (for example `alias dspyrefactor='dspyteach --mode refactor'`) if you prefer refactor templates to be the default in your shell.

To change where reports land, supply `--output-dir /path/to/reports`. When omitted the CLI writes to `dspy_file/data/` next to the module. Every run prints the active model name and the resolved output directory before analysis begins so you can confirm the environment at a glance. For backwards compatibility the installer also registers `dspy-file-teaching` as an alias.

Each analyzed file is saved under the chosen directory with a slugged name (e.g. `src__main.teaching.md` or `src__main.refactor.md`). If a file already exists, the CLI appends a numeric suffix to avoid overwriting previous runs.

The generated brief is markdown that mirrors the source material:

- Overview paragraphs for quick orientation
- Section-by-section bullets capturing the narrative
- Key concepts, workflows, pitfalls, and references learners should review
- A `dspy.Refine` wrapper keeps retrying until the report clears a length reward (defaults scale to ~50% of the source word count, with min/max clamps), so the content tends to be substantially longer than a single LM call.
- If a model cannot honour DSPy's structured-output schema, the CLI prints a `Structured output fallback` notice and heuristically parses the textual response so you still get usable bullets.

Behind the scenes the CLI:

1. Loads environment variables via `python-dotenv`.
2. Configures DSPy with the provider selected via CLI or environment variables (Ollama by default).
3. Resolves all requested files, reads contents, runs the DSPy `FileTeachingAnalyzer` module, and prints a human-friendly report for each.
4. Persists each report to the configured output directory so results are easy to revisit.
5. Stops the Ollama model when appropriate so local resources are returned to the pool.

### Extending

- Adjust the `TeachingReport` signature or add new chains in `dspy_file/file_analyzer.py` to capture additional teaching metadata.
- Customize the render logic in `dspy_file.file_helpers.render_prediction` if you want richer CLI output or structured JSON.
- Tune `TeachingConfig` inside `file_analyzer.py` to raise `max_tokens`, adjust the `Refine` word-count reward, or add extra LM kwargs.
- Add more signatures and module stages to capture additional metadata (e.g., security checks) and wire them into `FileAnalyzer`.

---

## Releasing

Maintainer release steps live in [RELEASING.md](https://github.com/AcidicSoil/DSPyTeach/blob/main/docs/RELEASING.md).

## Troubleshooting

- If the program cannot connect to Ollama, verify that the server is running on `http://localhost:11434` and the requested model has been pulled.
- When you see `ollama command not found`, ensure the `ollama` binary is on your `PATH`.
- For encoding errors, the helper already falls back to `latin-1`, but you can add more fallbacks in `file_helpers.read_file_content` if needed.
