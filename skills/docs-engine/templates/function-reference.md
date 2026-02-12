# Function Reference Template

> Copy this template for each function or command you're documenting.

---

## `function_name(param1, param2)`

**File:** `path/to/file.ext:line_number`

**Description:**
What this function does, in plain language. One or two sentences covering the main purpose and when you'd use it.

**Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `param1` | string | Yes | — | What this parameter controls |
| `param2` | number | No | `10` | Optional setting with sensible default |

**Returns:**
What the function gives back. Include the type and what it represents.

**Errors:**
- Throws `ValueError` if param1 is empty
- Returns `null` if the item isn't found

**Example:**
```
result = function_name("hello", 42)
# result: { status: "ok", value: "HELLO" }
```

**Notes:**
- Any gotchas, edge cases, or performance considerations
- Related functions: `other_function()`, `helper()`

---

## CLI Command Template

### `command-name`

**Synopsis:**
```
command-name [OPTIONS] <required-arg> [optional-arg]
```

**Description:**
What this command does.

**Options:**

| Flag | Description | Default |
|------|-------------|---------|
| `-h, --help` | Show help | — |
| `-v, --verbose` | Verbose output | off |
| `-o, --output FILE` | Output file | stdout |

**Examples:**
```bash
# Basic usage
command-name input.txt

# With options
command-name -v -o result.txt input.txt
```

**Exit Codes:**

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |
