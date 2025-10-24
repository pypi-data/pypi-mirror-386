# Files.com MCP Server

Files.com MCP allows your AI model, like ChatGPT or Claude, to use Files.com.

Files.com is the cloud-native, next-gen MFT, SFTP, and secure file-sharing platform that replaces brittle legacy servers with one always-on, secure fabric. Automate mission-critical file flows—across any cloud, protocol, or partner—while supporting human collaboration and eliminating manual work.

With universal SFTP, AS2, HTTPS, and 50+ native connectors backed by military-grade encryption, Files.com unifies governance, visibility, and compliance in a single pane of glass.

## Introduction

Modern AI models like ChatGPT and Claude are no longer just answering questions—they’re taking action. With Files.com MCP, you can securely give LLMs controlled access to real-world operations inside your Files.com environment.

Whether it's uploading, downloading, querying folders, or managing users, MCP enables your AI agent to interact with your Files.com infrastructure as if it were an extension of your team—without compromising on security, auditability, or control.

### What Is MCP?

Model Context Protocol (MCP) is a structured interface that lets Large Language Models call real APIs as part of their workflow. Think of it as a way to “hand tools” to the LLM—where the tools are real, authenticated functions from your Files.com environment.

When integrated via MCP, your LLM can:

 - Transfer files between cloud and on-prem systems

 - Query folders or file metadata

 - Create and manage users

 - Automate workflows like archival or sharing

 - And much more

MCP turns the LLM from a passive assistant into an active file operations agent.

### What is Files.com?

Files.com is the modern platform for secure file transfer, automation, and storage integration. Used by thousands of enterprises, Files.com connects cloud apps, on-prem systems, and human workflows—all through a single, powerful interface.

With robust APIs, native protocol support (SFTP, FTPS, AS2, and more), and enterprise-grade access controls, Files.com is built to move your files—reliably, securely, and at scale.

### Common Use Cases

*AI Assistants for Operations Teams:* Let your internal chatbot fetch or archive files on request.

*Automated LLM Workflows:* Build AI agents that react to incoming support requests, then retrieve or upload the necessary files from your environment.

*Developer Copilots:* Enable your dev-focused LLMs to create users, provision folders, or debug via real-time file access.

### Important Information

Large Language Models perform best when their toolset is focused. If you're integrating with Files.com MCP and noticing inconsistent tool usage, your LLM may be overloaded with too many available functions.

Most LLM clients allow you to selectively enable or disable tools exposed through MCP. For best results, only include the specific tools your agent needs for its task. This reduces ambiguity and improves the model’s ability to pick the right operation every time.

### Installation Into Your LLM

Each LLM client has its own method for installing an MCP, and they typically provide specific instructions. Many clients follow a pattern similar to Claude, so our Claude example is a great starting point if you’re working with one of those.

For LLMs that require a more detailed or technical setup, our MCP is implemented in Python and available on PyPI: https://pypi.org/project/files-com-mcp/

If your LLM client needs you to supply execution details for our MCP, we recommend using `uvx`, as demonstrated in the Claude example. This approach ensures a smooth, reproducible setup with minimal effort.

### Using with Claude

To install into Claude you have to add JSON to the `claude_desktop_config.json` file

An official tutorial can found here: https://modelcontextprotocol.io/quickstart/user#2-add-the-filesystem-mcp-server

To add the Files.com MCP, use the Claude Config JSON below (be sure to change the FILES_COM_API_KEY value)

#### uv Required

These examples require `uv` which is a popular modern environment manager for running isolated python tools. You will need to install it first. Using uvx is a huge improvement over older Python environment setup methods. It is simple, runs smoothly, and eliminates the need for manual configuration or unnecessary complexity.

#### Claude Config

```
{
  "mcpServers": {
    "Files.com": {
      "type": "stdio",
      "command": "uvx",
      "args": [
        "files-com-mcp"
      ],
      "env": {
        "FILES_COM_API_KEY": "CHangeME"
      }
    }
  }
}
```

## Authentication

There are two ways to authenticate: API Key authentication and Session-based authentication.

### Authenticate with an API Key

Authenticating with an API key is the recommended authentication method for most scenarios, and is
the method used in the examples on this site.

To use an API Key, first generate an API key from the [web
interface](https://www.files.com/docs/sdk-and-apis/api-keys) or [via the API or an
SDK](/python-mcp/resources/developers/api-keys).

Note that when using a user-specific API key, if the user is an administrator, you will have full
access to the entire API. If the user is not an administrator, you will only be able to access files
that user can access, and no access will be granted to site administration functions in the API.

Don't forget to replace the placeholder, `YOUR_API_KEY`, with your actual API key.

### Authenticate with a Session

You can also authenticate by creating a user session using the username and
password of an active user. If the user is an administrator, the session will have full access to
all capabilities of Files.com. Sessions created from regular user accounts will only be able to access files that
user can access, and no access will be granted to site administration functions.

Sessions use the exact same session timeout settings as web interface sessions. When a
session times out, simply create a new session and resume where you left off. This process is not
automatically handled by our SDKs because we do not want to store password information in memory without
your explicit consent.

#### Logging In

#### Using a Session

#### Logging Out

## Configuration

## Sort and Filter

Several of the Files.com API resources have list operations that return multiple instances of the
resource. The List operations can be sorted and filtered.

### Sorting

To sort the returned data, pass in the ```sort_by``` method argument.

Each resource supports a unique set of valid sort fields and can only be sorted by one field at a
time.

#### Special note about the List Folder Endpoint

For historical reasons, and to maintain compatibility
with a variety of other cloud-based MFT and EFSS services, Folders will always be listed before Files
when listing a Folder.  This applies regardless of the sorting parameters you provide.  These *will* be
used, after the initial sort application of Folders before Files.

### Filtering

Filters apply selection criteria to the underlying query that returns the results. They can be
applied individually or combined with other filters, and the resulting data can be sorted by a
single field.

Each resource supports a unique set of valid filter fields, filter combinations, and combinations of
filters and sort fields.

#### Filter Types

| Filter | Type | Description |
| --------- | --------- | --------- |
| `filter` | Exact | Find resources that have an exact field value match to a passed in value. (i.e., FIELD_VALUE = PASS_IN_VALUE). |
| `filter_prefix` | Pattern | Find resources where the specified field is prefixed by the supplied value. This is applicable to values that are strings. |
| `filter_gt` | Range | Find resources that have a field value that is greater than the passed in value.  (i.e., FIELD_VALUE > PASS_IN_VALUE). |
| `filter_gteq` | Range | Find resources that have a field value that is greater than or equal to the passed in value.  (i.e., FIELD_VALUE >=  PASS_IN_VALUE). |
| `filter_lt` | Range | Find resources that have a field value that is less than the passed in value.  (i.e., FIELD_VALUE < PASS_IN_VALUE). |
| `filter_lteq` | Range | Find resources that have a field value that is less than or equal to the passed in value.  (i.e., FIELD_VALUE \<= PASS_IN_VALUE). |

## Paths

Working with paths in Files.com involves several important considerations. Understanding how path comparisons are applied helps developers ensure consistency and accuracy across all interactions with the platform.
<div></div>

### Capitalization

Files.com compares paths in a **case-insensitive** manner. This means path segments are treated as equivalent regardless of letter casing.

For example, all of the following resolve to the same internal path:

| Path Variant                          | Interpreted As              |
|---------------------------------------|------------------------------|
| `Documents/Reports/Q1.pdf`            | `documents/reports/q1.pdf`  |
| `documents/reports/q1.PDF`            | `documents/reports/q1.pdf`  |
| `DOCUMENTS/REPORTS/Q1.PDF`            | `documents/reports/q1.pdf`  |

This behavior applies across:
- API requests
- Folder and file lookup operations
- Automations and workflows

See also: [Case Sensitivity Documentation](https://www.files.com/docs/files-and-folders/case-sensitivity/)

### Slashes

All path parameters in Files.com (API, SDKs, CLI, automations, integrations) must **omit leading and trailing slashes**. Paths are always treated as **absolute and slash-delimited**, so only internal `/` separators are used and never at the start or end of the string.

####  Path Slash Examples
| Path                              | Valid? | Notes                         |
|-----------------------------------|--------|-------------------------------|
| `folder/subfolder/file.txt`       |   ✅   | Correct, internal separators only |
| `/folder/subfolder/file.txt`      |   ❌   | Leading slash not allowed     |
| `folder/subfolder/file.txt/`      |   ❌   | Trailing slash not allowed    |
| `//folder//file.txt`              |   ❌   | Duplicate separators not allowed |

<div></div>

### Unicode Normalization

Files.com normalizes all paths using [Unicode NFC (Normalization Form C)](https://www.unicode.org/reports/tr15/#Norm_Forms) before comparison. This ensures consistency across different representations of the same characters.

For example, the following two paths are treated as equivalent after NFC normalization:

| Input                                  | Normalized Form       |
|----------------------------------------|------------------------|
| `uploads/\u0065\u0301.txt`             | `uploads/é.txt`        |
| `docs/Café/Report.txt`                 | `docs/Café/Report.txt` |

- All input must be UTF‑8 encoded.
- Precomposed and decomposed characters are unified.
- This affects search, deduplication, and comparisons across SDKs.

<div></div>

## Foreign Language Support

The Files.com MCP will soon be updated to support localized responses by using a configuration
method. When available, it can be used to guide the API in selecting a preferred language for applicable response content.

Language support currently applies to select human-facing fields only, such as notification messages
and error descriptions.

If the specified language is not supported or the value is omitted, the API defaults to English.

## Errors

## Mock Server

Files.com publishes a Files.com API server, which is useful for testing your use of the Files.com
SDKs and other direct integrations against the Files.com API in an integration test environment.

It is a Ruby app that operates as a minimal server for the purpose of testing basic network
operations and JSON encoding for your SDK or API client. It does not maintain state and it does not
deeply inspect your submissions for correctness.

Eventually we will add more features intended for integration testing, such as the ability to
intentionally provoke errors.

Download the server as a Docker image via [Docker Hub](https://hub.docker.com/r/filescom/files-mock-server).

The Source Code is also available on [GitHub](https://github.com/Files-com/files-mock-server).

A README is available on the GitHub link.

## Development

While our MCP works well out-of-the-box, some power users find value in modifying MCP code to suit their unique needs. For those power users, it is recommended to use STDIO mode. Upload and Download tools rely on the file system where the MCP is running.

To test LLM tools we recommend a popular command-line program called `inspector`. This will start a WebUI on a local port, the output of the command will give you the link to the inspector GUI.
Ex: http://127.0.0.1:6274


### Development - STDIO

```
FILES_COM_API_KEY="dummyKey" npx @modelcontextprotocol/inspector uv run -m files_com_mcp
```


### Development - SSE

```
FILES_COM_API_KEY="dummyKey" uv run -m files_com_mcp --mode server --port 12345
```

Launch the inspector

```
npx @modelcontextprotocol/inspector
```

### Development Claude Config

```
{
  "mcpServers": {
    "Files.com": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/folder-containing-files_com_mcp",
        "run",
        "-m",
        "files_com_mcp"
      ],
      "env": {
        "FILES_COM_API_KEY": "CHangeME"
      }
    }
  }
}
```

## MCP Registry Metadata

```
mcp-name: com.files/python-mcp
```
