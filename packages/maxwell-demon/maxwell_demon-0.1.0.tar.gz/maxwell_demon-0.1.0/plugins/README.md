# Maxwell Plugins

Maxwell supports external plugins to extend its functionality without modifying core code.

## Plugin Types

### 1. Python Plugins

Python plugins are `.py` files containing BaseWorkflow subclasses:

```python
# ~/.maxwell/plugins/my_plugin.py
from pathlib import Path
from typing import Any, Dict, List
from dataclasses import dataclass

from maxwell.workflows.base import (
    BaseWorkflow,
    WorkflowInputs,
    WorkflowOutputs,
    WorkflowConfig,
    WorkflowPriority,
    WorkflowResult,
)
from maxwell.registry import register_workflow

@dataclass(frozen=True)
class MyPluginInputs(WorkflowInputs):
    message: str = "Hello, World!"

@dataclass(frozen=True)
class MyPluginOutputs(WorkflowOutputs):
    result: str

@register_workflow
class MyPluginWorkflow(BaseWorkflow):
    workflow_id = "my-plugin"
    name = "My Custom Plugin"
    description = "Example plugin workflow"
    version = "1.0"
    category = "custom"
    tags = {"plugin", "example"}

    InputSchema = MyPluginInputs
    OutputSchema = MyPluginOutputs

    def get_cli_parameters(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "message",
                "type": str,
                "required": False,
                "default": "Hello, World!",
                "help": "Message to process",
            }
        ]

    def get_required_inputs(self) -> List[str]:
        return []

    def get_produced_outputs(self) -> List[str]:
        return ["result"]

    def get_config(self, root_dir: Path) -> WorkflowConfig:
        return WorkflowConfig(
            enabled=True,
            priority=WorkflowPriority.MEDIUM,
            timeout_seconds=60,
            parameters={"root_dir": str(root_dir)},
        )

    def execute(self, project_root: Path, context: Dict[str, Any]) -> WorkflowResult:
        inputs: MyPluginInputs = self.parse_inputs(context)

        # Your plugin logic here
        result = f"Processed: {inputs.message}"

        outputs = MyPluginOutputs(result=result)
        return self.create_result(outputs)
```

### 2. Script Plugins

Script plugins are executable scripts with JSON metadata files:

**Example: hello-plugin**

```bash
#!/usr/bin/env bash
# ~/.maxwell/plugins/hello

name=${1:-World}
echo "Hello, $name from Maxwell plugin!"
```

```json
{
  "workflow_id": "hello",
  "name": "Hello Plugin",
  "description": "Simple hello world plugin",
  "version": "1.0",
  "category": "utility",
  "tags": ["example", "greeting"],
  "parameters": [
    {
      "name": "name",
      "type": "str",
      "required": false,
      "default": "World",
      "help": "Name to greet"
    }
  ]
}
```

Make the script executable:
```bash
chmod +x ~/.maxwell/plugins/hello
```

## Plugin Locations

Maxwell searches for plugins in:

1. **Global plugins**: `~/.maxwell/plugins/`
2. **Project plugins**: `<project>/.maxwell/plugins/`

Project plugins are loaded after global plugins, so they can override global ones.

## Using Plugins

Once installed, plugins appear in the workflow list:

```bash
maxwell list-workflows
# Will show your custom plugins alongside built-in workflows

maxwell my-plugin --message "Hello from plugin!"
# Execute your Python plugin

maxwell hello --name "Maxwell"
# Execute your script plugin
```

## Example Plugins

### Git Stats Plugin (Script)

```bash
#!/usr/bin/env bash
# ~/.maxwell/plugins/git-stats

days=${1:-7}

echo "Git activity for last $days days:"
git log --since="$days days ago" --pretty=format:"%h - %an: %s" --abbrev-commit
```

```json
{
  "workflow_id": "git-stats",
  "name": "Git Statistics",
  "description": "Show git commit statistics",
  "version": "1.0",
  "category": "git",
  "tags": ["git", "statistics"],
  "parameters": [
    {
      "name": "days",
      "type": "int",
      "required": false,
      "default": 7,
      "help": "Number of days to look back"
    }
  ]
}
```

### File Counter Plugin (Python)

```python
# ~/.maxwell/plugins/count_files.py
from pathlib import Path
from typing import Any, Dict, List
from dataclasses import dataclass
from collections import Counter

from maxwell.workflows.base import (
    BaseWorkflow,
    WorkflowInputs,
    WorkflowOutputs,
    WorkflowResult,
)
from maxwell.registry import register_workflow

@dataclass(frozen=True)
class CounterInputs(WorkflowInputs):
    pass

@dataclass(frozen=True)
class CounterOutputs(WorkflowOutputs):
    counts: Dict[str, int]

@register_workflow
class FileCounterWorkflow(BaseWorkflow):
    workflow_id = "count-files"
    name = "File Counter"
    description = "Count files by extension"

    InputSchema = CounterInputs
    OutputSchema = CounterOutputs

    def execute(self, project_root: Path, context: Dict[str, Any]) -> WorkflowResult:
        counter = Counter()
        for file in project_root.rglob("*"):
            if file.is_file():
                counter[file.suffix or "no_extension"] += 1

        outputs = CounterOutputs(counts=dict(counter))
        return self.create_result(outputs)
```

## Best Practices

1. **Naming**: Use lowercase with hyphens for workflow_id (e.g., `my-plugin`)
2. **Categories**: Choose appropriate category (utility, analysis, documentation, etc.)
3. **Documentation**: Always include description and help text
4. **Error Handling**: Handle errors gracefully and return meaningful messages
5. **Testing**: Test plugins before deploying to production
6. **Versioning**: Use semantic versioning for your plugins

## Troubleshooting

Enable debug logging to see plugin loading:

```bash
export MAXWELL_LOG_LEVEL=DEBUG
maxwell list-workflows
```

Check plugin discovery:
```python
from maxwell.registry import get_workflow_registry

registry = get_workflow_registry()
registry.load_plugins()  # Manually trigger plugin loading
print(registry.list_workflow_ids())
```
