<div id="toc" align="center" style="margin-bottom: 0;">
  <ul style="list-style: none; margin: 0; padding: 0;">
    <a href="https://stagehand.dev">
      <picture>
        <source media="(prefers-color-scheme: dark)" srcset="media/dark_logo.png" />
        <img alt="Stagehand" src="media/light_logo.png" width="200" style="margin-right: 30px;" />
      </picture>
    </a>
  </ul>
</div>
<p align="center">
  <strong>The AI Browser Automation Framework</strong><br>
  <a href="https://docs.stagehand.dev">Read the Docs</a>
</p>

<p align="center">
  <a href="https://pypi.org/project/stagehand">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/pypi/v/stagehand.svg?style=for-the-badge" />
      <img alt="PyPI version" src="https://img.shields.io/pypi/v/stagehand.svg?style=for-the-badge" />
    </picture>
  </a>
  <a href="https://github.com/browserbase/stagehand/tree/main?tab=MIT-1-ov-file#MIT-1-ov-file">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="media/dark_license.svg" />
      <img alt="MIT License" src="media/light_license.svg" />
    </picture>
  </a>
  <a href="https://stagehand.dev/slack">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="media/dark_slack.svg" />
      <img alt="Slack Community" src="media/light_slack.svg" />
    </picture>
  </a>
</p>

<p align="center">
If you're looking for the TypeScript implementation, you can find it 
<a href="https://github.com/browserbase/stagehand"> here</a>
</p>

<div align="center" style="display: flex; align-items: center; justify-content: center; gap: 4px; margin-bottom: 0;">
  <b>Vibe code</b>
  <span style="font-size: 1.05em;"> Stagehand with </span>
  <a href="https://director.ai" style="display: flex; align-items: center;">
    <span>Director</span>
  </a>
  <span> </span>
  <picture>
    <img alt="Director" src="media/director_icon.svg" width="25" />
  </picture>
</div>


## Why Stagehand?

Most existing browser automation tools either require you to write low-level code in a framework like Selenium, Playwright, or Puppeteer, or use high-level agents that can be unpredictable in production. By letting developers choose what to write in code vs. natural language, Stagehand is the natural choice for browser automations in production.

1. **Choose when to write code vs. natural language**: use AI when you want to navigate unfamiliar pages, and use code ([Playwright](https://playwright.dev/)) when you know exactly what you want to do.

2. **Preview and cache actions**: Stagehand lets you preview AI actions before running them, and also helps you easily cache repeatable actions to save time and tokens.

3. **Computer use models with one line of code**: Stagehand lets you integrate SOTA computer use models from OpenAI and Anthropic into the browser with one line of code.

-----

### TL;DR: Automate the web *reliably* with natural language:

- **act** — Instruct the AI to perform actions (e.g. click a button or scroll).
```python
await stagehand.page.act("click on the 'Quickstart' button")
```
- **extract** — Extract and validate data from a page using a Pydantic schema.
```python
await stagehand.page.extract("the summary of the first paragraph")
```
- **observe** — Get natural language interpretations to, for example, identify selectors or elements from the page.
```python
await stagehand.page.observe("find the search bar")
```
- **agent** — Execute autonomous multi-step tasks with provider-specific agents (OpenAI, Anthropic, etc.).
```python
await stagehand.agent.execute("book a reservation for 2 people for a trip to the Maldives")
```


## Installation:

To get started, simply:

```bash
pip install stagehand
```

> We recommend using [uv](https://docs.astral.sh/uv/) for your package/project manager. If you're using uv can follow these steps:

```bash
uv venv .venv
source .venv/bin/activate
uv pip install stagehand
```

## Quickstart

```python
import asyncio
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from stagehand import StagehandConfig, Stagehand

# Load environment variables
load_dotenv()

# Define Pydantic models for structured data extraction
class Company(BaseModel):
    name: str = Field(..., description="Company name")
    description: str = Field(..., description="Brief company description")

class Companies(BaseModel):
    companies: list[Company] = Field(..., description="List of companies")
    
async def main():
    # Create configuration
    config = StagehandConfig(
        env = "BROWSERBASE", # or LOCAL
        api_key=os.getenv("BROWSERBASE_API_KEY"),
        project_id=os.getenv("BROWSERBASE_PROJECT_ID"),
        model_name="google/gemini-2.5-flash-preview-05-20",
        model_api_key=os.getenv("MODEL_API_KEY"),
    )
    
    stagehand = Stagehand(config)
    
    try:
        print("\nInitializing 🤘 Stagehand...")
        # Initialize Stagehand
        await stagehand.init()

        if stagehand.env == "BROWSERBASE":    
            print(f"🌐 View your live browser: https://www.browserbase.com/sessions/{stagehand.session_id}")

        page = stagehand.page

        await page.goto("https://www.aigrant.com")
        
        # Extract companies using structured schema        
        companies_data = await page.extract(
          "Extract names and descriptions of 5 companies in batch 3",
          schema=Companies
        )
        
        # Display results
        print("\nExtracted Companies:")
        for idx, company in enumerate(companies_data.companies, 1):
            print(f"{idx}. {company.name}: {company.description}")

        observe = await page.observe("the link to the company Browserbase")
        print("\nObserve result:", observe)
        act = await page.act("click the link to the company Browserbase")
        print("\nAct result:", act)
            
    except Exception as e:
        print(f"Error: {str(e)}")
        raise
    finally:
        # Close the client
        print("\nClosing 🤘 Stagehand...")
        await stagehand.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## Documentation

See our full documentation [here](https://docs.stagehand.dev/).

## Cache Actions

You can cache actions in Stagehand to avoid redundant LLM calls. This is particularly useful for actions that are expensive to run or when the underlying DOM structure is not expected to change.

### Using `observe` to preview an action

`observe` lets you preview an action before taking it. If you are satisfied with the action preview, you can run it in `page.act` with no further LLM calls.

```python
# Get the action preview
action_preview = await page.observe("Click the quickstart link")

# action_preview is a JSON-ified version of a Playwright action:
# {
#     "description": "The quickstart link",
#     "method": "click",
#     "selector": "/html/body/div[1]/div[1]/a",
#     "arguments": []
# }

# NO LLM INFERENCE when calling act on the preview
await page.act(action_preview[0])
```

If the website happens to change, `self_heal` will run the loop again to save you from constantly updating your scripts.


## Contributing

At a high level, we're focused on improving reliability, speed, and cost in that order of priority. If you're interested in contributing, reach out on [Slack](https://stagehand.dev/slack), open an issue or start a discussion. 

For more info, check the [Contributing Guide](https://docs.stagehand.dev/examples/contributing).

**Local Development Installation:**

```bash
# Clone the repository
git clone https://github.com/browserbase/stagehand-python.git
cd stagehand-python

# Install in editable mode with development dependencies
pip install -r requirements.txt
```


## License

MIT License (c) 2025 Browserbase, Inc.
