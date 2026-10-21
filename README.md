# SheetRunner

SheetRunner is a local web application for running Selenium browser tests described in Excel workbooks. It includes a Python/FastAPI service that validates workbooks and controls the browser, plus a React and Tailwind CSS interface for configuring and monitoring runs.

> **Status:** This is an early version. It supports common browser actions and creates HTML, JSON, and JUnit XML reports. Data-driven repetitions, file upload/download verification, and configurable output folders are not implemented yet.

## What it does

1. You choose a target URL, browser, suite workbook, and test-case workbook in the UI.
2. SheetRunner checks for the required workbook sheets and column headers, and verifies that enabled suite cases have test-case rows.
3. It starts Chrome, Firefox, or Edge, opens the target URL, and executes the `YES` cases and their steps in workbook order.
4. It records step results, captures screenshots for failed steps, and writes reports under `backend/artifacts/<run-id>/`.

The browser must be installed on the same computer as the Python backend. Selenium Manager locates or downloads a compatible driver when needed.

## Requirements

- Python 3.10 or newer
- Node.js 20 or newer and npm
- Chrome, Firefox, or Microsoft Edge
- Network access from the backend when testing a remote site or when Selenium Manager needs to download a driver

## Run locally

Open two terminals in the project directory.

### 1. Start the backend

**Windows PowerShell:**

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

If PowerShell blocks virtual-environment activation, run the commands from Command Prompt using `.venv\Scripts\activate.bat`, or invoke `.venv\Scripts\python.exe` and `.venv\Scripts\uvicorn.exe` directly.

**macOS/Linux:**

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API is available at <http://localhost:8000>. Interactive API documentation is at <http://localhost:8000/docs>.

### 2. Start the frontend

In a second terminal, from the project root:

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173>. The UI connects to the API at `http://localhost:8000` by default.

### 3. Run a test

1. Enter the URL of the site to test, including `http://` or `https://`. For a local site, use its actual address, for example `http://localhost:3000`.
2. Choose the browser.
3. Upload a suite workbook and a test-case workbook.
4. Select **Validate workbooks**, fix any reported issues, then select **Execute run**.
5. When execution completes, open the HTML, JSON, or XML report from the run panel.

The browser opened by Selenium runs on the backend computer. A website available only on another machine or network may not be reachable from it. If Chrome reports `ERR_NAME_NOT_RESOLVED`, check that the target hostname is spelled correctly and resolves from the backend computer.

## Prepare the workbooks

### Suite workbook

The active worksheet must contain these columns:

| Test Case | Execution |
| --- | --- |
| Sign in | YES |
| Password reset | NO |

Use `YES` to run a case and `NO` to skip it. Only enabled (`YES`) case names need matching rows in `TestCaseSheet`. A skipped case may be left out of that sheet. Case names should match between workbooks.

### Test-case workbook

This workbook must contain a `TestCaseSheet` worksheet and a `CapturedObjectProperties` worksheet.

`TestCaseSheet` uses one row per step and these columns:

| Column | Purpose |
| --- | --- |
| `Test Case` | Name from the suite workbook. Repeat it on each step, or leave blank on continuation rows. |
| `Step ID` | Step number or descriptive label. |
| `Page Name` | Logical page key used to find an element mapping. |
| `Locator Strategy` | Kept for documentation; runtime locators are resolved from `CapturedObjectProperties`. |
| `Element Name` | Logical element key on that page. Leave blank for actions that do not use an element. |
| `Action` | Action keyword, such as `click` or `verifyTitle`. |
| `Action Value` | Text to enter, expected text/title/URL, option value, navigation URL, or wait duration, depending on the action. |
| `On-Failure Behavior` | Use `CONTINUE`, `SKIP`, or `IGNORE` to continue after a failed step; other values stop the run on failure. |
| `Test-Data Reference` | Reserved for a future data-driven feature; use `SheetName.ColumnName` format when documenting it. |

`CapturedObjectProperties` maps logical elements to actual locators:

| Page Name | Element Name | Locator Strategy | Locator Value |
| --- | --- | --- | --- |
| Login | Username | ID | username |
| Login | Submit | CSS | button[type="submit"] |

Supported locator strategies are `ID`, `NAME`, `XPATH`, `CSS`, `CLASS NAME`, and `LINK TEXT`. For a step with an element, the page and element names must match a mapping.

## Supported actions

Action names are case-insensitive and may include spaces or underscores. The current runner supports:

- **Element interaction:** `click`, `submit`, `enterText` (also `type`, `sendKeys`, `input`), `clear`
- **Checks and reads:** `verifyText` (also `getText`, `readText`), `verifyValue`, `verifyTitle`, `verifyURL`, `verifyVisible`, `verifyEnabled`, `verifyChecked`
- **Alerts:** `verifyAlertText`, `acceptAlert`, `dismissAlert`
- **Dropdowns:** `selectByText`, `selectByValue`, `selectByIndex`
- **Navigation and browser:** `navigate`, `back`, `forward`, `refresh`, `maximize`, `close`
- **Page interaction:** `wait` (seconds), `scrollToElement` (also `scroll`), `hover`, `doubleClick`, `rightClick`
- **Frames and windows:** `switchToFrame`, `switchToParentFrame`, `switchToDefaultContent`, `switchToWindow`

Verification actions fail the step when the expected value is not found. If an action requiring an element is used, provide its page/element mapping. Alerts, frames, and windows require the page to be in the correct state when their step runs. `switchToWindow` switches to the most recently opened window.

## Example workbooks

Ready-made examples are in [`sample_workbooks/`](sample_workbooks/):

- `suite.xlsx` and `test-cases.xlsx`: small starter pair.
- `action-examples-suite.xlsx` and `action-examples-cases.xlsx`: two sample cases for each of the 35 action keywords listed in the UI guide.

The action examples are marked `NO` so they do not run before you configure selectors and page state for your application. Replace `[replace-with-locator]` in `CapturedObjectProperties`, adjust action values, then mark the cases you want to run as `YES`.

To regenerate the basic starter pair:

```bash
cd backend
python -m app.make_samples
```

## Reports and files

For each run, the backend writes:

```text
backend/artifacts/<run-id>/<run-id>.html
backend/artifacts/<run-id>/<run-id>.json
backend/artifacts/<run-id>/<run-id>.xml
backend/artifacts/<run-id>/screenshots/   # screenshots from failed steps
```

The HTML report includes step status, errors, skipped cases, and a run summary. JSON contains structured run data. XML is a JUnit-style report suitable for CI tools. Uploaded workbooks are stored under `backend/uploads/`.

## API endpoints

- `GET /api/health` — service health
- `POST /api/validate` — validate two uploaded workbooks
- `POST /api/runs` — create a run
- `GET /api/runs/{run_id}` — retrieve in-memory run status and result
- `GET /docs` — interactive FastAPI documentation

Run status is held in backend memory, so restarting the API clears the run list. Report files already written to disk remain available.

## Known limitations

- Test-data references are accepted as workbook fields but do not yet create repeated data-driven runs.
- The suite/case workbooks are uploaded through the web UI; there is no separate command-line runner yet.
- The UI does not yet configure screenshot and report directories; outputs use `backend/artifacts/`.
- File upload/download verification and file hashes are not implemented.
- Window switching selects the last window handle; it does not select by a configured window name.
- Workbook validation checks required sheets/headers and enabled case names, but it does not validate every action or every referenced value before starting the browser.

## Project layout

```text
backend/
  app/          FastAPI endpoints, workbook parsing, Selenium runner
  artifacts/    Generated reports and screenshots (created at runtime)
  uploads/      Uploaded workbooks (created at runtime)
frontend/
  src/          React interface and Tailwind styles
sample_workbooks/
                Example suite and test-case workbooks
```
