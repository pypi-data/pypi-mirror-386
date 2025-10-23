# WebSocket Communication Protocol

This document outlines the WebSocket communication protocol used in Portacode. The protocol involves three main participants: client sessions, the Portacode server, and devices.

## Architecture Overview

```
┌─────────────┐          ┌──────────────────┐          ┌─────────────────────────┐
│   Client    │          │   Portacode      │          │        Device           │
│   Session   │◄────────►│    Server        │◄────────►│ (Portacode CLI or       │
│             │          │                  │          │  Python package)        │
└─────────────┘          └──────────────────┘          └─────────────────────────┘
     │                           │                                  │
     │                           │                                  │
  Client-Side              Acts as middleman                  Device-Side
  Protocol                 - Routes messages                  Protocol
                          - Manages sessions
```

The Portacode server acts as a **routing middleman** between client sessions and devices. It manages routing fields that are included in messages to specify routing destinations but are removed or transformed before reaching the final recipient:

**Routing Fields Behavior:**

- **`device_id`** (Client → Server): Client includes this to specify which device to route to. Server uses it for routing, then **removes it** before forwarding to the device (the device knows the message is for them). Server **adds it** when routing device responses back to clients (so clients know which device the message came from).

- **`client_sessions`** (Device → Server): Device includes this to specify which client session(s) to route to. Server uses it for routing, then **removes it** before forwarding to clients (clients just receive the message without seeing routing metadata).

- **`source_client_session`** (Server → Device): Server **adds this** when forwarding client commands to devices (so device knows which client sent the command and can target responses back). Clients never include this field.

This document describes the complete protocol for communicating with devices through the server, guiding app developers on how to get their client sessions to communicate with devices.

## Table of Contents

- [Raw Message Format On Device Side](#raw-message-format-on-device-side)
- [Raw Message Format On Client Side](#raw-message-format-on-client-side)
- [Actions](#actions)
  - [Terminal Actions](#terminal-actions)
    - [`terminal_start`](#terminal_start)
    - [`terminal_send`](#terminal_send)
    - [`terminal_stop`](#terminal_stop)
    - [`terminal_list`](#terminal_list)
  - [System Actions](#system-actions)
    - [`system_info`](#system_info)
  - [File Actions](#file-actions)
    - [`file_read`](#file_read)
    - [`file_write`](#file_write)
    - [`directory_list`](#directory_list)
    - [`file_info`](#file_info)
    - [`file_delete`](#file_delete)
    - [`file_create`](#file_create)
    - [`folder_create`](#folder_create)
    - [`file_rename`](#file_rename)
    - [`content_request`](#content_request)
  - [Project State Actions](#project-state-actions)
    - [`project_state_folder_expand`](#project_state_folder_expand)
    - [`project_state_folder_collapse`](#project_state_folder_collapse)
    - [`project_state_file_open`](#project_state_file_open)
    - [`project_state_tab_close`](#project_state_tab_close)
    - [`project_state_set_active_tab`](#project_state_set_active_tab)
    - [`project_state_diff_open`](#project_state_diff_open)
    - [`project_state_diff_content_request`](#project_state_diff_content_request)
    - [`project_state_git_stage`](#project_state_git_stage)
    - [`project_state_git_unstage`](#project_state_git_unstage)
    - [`project_state_git_revert`](#project_state_git_revert)
    - [`project_state_git_commit`](#project_state_git_commit)
  - [Client Session Management](#client-session-management)
    - [`client_sessions_update`](#client_sessions_update)
- [Events](#events)
  - [Error Events](#error-events)
    - [`error`](#error)
  - [Terminal Events](#terminal-events)
    - [`terminal_started`](#terminal_started)
    - [`terminal_data`](#terminal_data)
    - [`terminal_exit`](#terminal_exit)
    - [`terminal_send_ack`](#terminal_send_ack)
    - [`terminal_stopped`](#terminal_stopped)
    - [`terminal_stop_completed`](#terminal_stop_completed)
    - [`terminal_list`](#terminal_list-event)
  - [System Events](#system-events)
    - [`system_info`](#system_info-event)
  - [File Events](#file-events)
    - [`file_read_response`](#file_read_response)
    - [`file_write_response`](#file_write_response)
    - [`directory_list_response`](#directory_list_response)
    - [`file_info_response`](#file_info_response)
    - [`file_delete_response`](#file_delete_response)
    - [`file_create_response`](#file_create_response)
    - [`folder_create_response`](#folder_create_response)
    - [`file_rename_response`](#file_rename_response)
    - [`content_response`](#content_response)
  - [Project State Events](#project-state-events)
    - [`project_state_initialized`](#project_state_initialized)
    - [`project_state_update`](#project_state_update)
    - [`project_state_folder_expand_response`](#project_state_folder_expand_response)
    - [`project_state_folder_collapse_response`](#project_state_folder_collapse_response)
    - [`project_state_file_open_response`](#project_state_file_open_response)
    - [`project_state_tab_close_response`](#project_state_tab_close_response)
    - [`project_state_set_active_tab_response`](#project_state_set_active_tab_response)
    - [`project_state_diff_open_response`](#project_state_diff_open_response)
    - [`project_state_diff_content_response`](#project_state_diff_content_response)
    - [`project_state_git_stage_response`](#project_state_git_stage_response)
    - [`project_state_git_unstage_response`](#project_state_git_unstage_response)
    - [`project_state_git_revert_response`](#project_state_git_revert_response)
    - [`project_state_git_commit_response`](#project_state_git_commit_response)
  - [Client Session Events](#client-session-events)
    - [`request_client_sessions`](#request_client_sessions)
  - [Terminal Data](#terminal-data)
    - [Terminal I/O Data](#terminal_data)
  - [Server-Side Events](#server-side-events)
    - [`device_status`](#device_status)
    - [`devices`](#devices)

## Raw Message Format On Device Side

Communication between the server and devices uses a [multiplexer](./multiplex.py) that wraps every message in a JSON object with a `channel` and a `payload`. This allows for multiple virtual communication channels over a single WebSocket connection.

**Device-Side Message Structure:**

```json
{
  "channel": "<channel_id>",
  "payload": {
    // This is where the Action or Event object goes
  }
}
```

**Field Descriptions:**

*   `channel` (string|integer, mandatory): Identifies the virtual channel the message is for. When sending control commands to the device, they should be sent to channel 0 and when the device responds to such control commands or sends system events, they will also be sent on the zero channel. When a terminal session is created in the device, it is assigned a uuid, the uuid becomes the channel for communicating to that specific terminal.
*   `payload` (object, mandatory): The content of the message, which will be either an [Action](#actions) or an [Event](#events) object.

**Channel Types:**
- **Channel 0** (control channel): Used for system commands, terminal management, file operations, and project state management
- **Channel UUID** (terminal channel): Used for terminal I/O to a specific terminal session

---

## Raw Message Format On Client Side

Client sessions communicate with the server using a unified message format with the same field names as the device protocol, plus routing information.

**Client-Side Message Structure (Client → Server):**

```json
{
  "device_id": <number>,
  "channel": <number|string>,
  "payload": {
    "cmd": "<command_name>",
    ...command-specific fields
  }
}
```

**Field Descriptions:**

*   `device_id` (number, mandatory): Routing field - specifies which device to send the message to. The server validates that the client has access to this device before forwarding.
*   `channel` (number|string, mandatory): Same as device protocol - the target channel (0 for control, UUID for terminal). Uses the same field name for consistency.
*   `payload` (object, mandatory): Same as device protocol - the command payload. Uses the same field name for consistency.

**Server Transformation (Client → Device):**

When the server receives a client message, it:
1. Validates client has access to the specified `device_id`
2. **Removes** `device_id` from the message (device doesn't need to be told "this is for you")
3. **Adds** `source_client_session` to the payload (so device knows which client to respond to)
4. Forwards to device: `{channel, payload: {...payload, source_client_session}}`

**Server Transformation (Device → Client):**

When the server receives a device response, it:
1. **Adds** `device_id` to the message (so client knows which device it came from, based on authenticated device connection)
2. **Removes** `client_sessions` routing metadata (clients don't need to see routing info)
3. Routes to appropriate client session(s)

**Server Response Format (Server → Client):**

```json
{
  "event": "<event_name>",
  "device_id": <number>,
  ...event-specific fields
}
```

**Field Descriptions:**

*   `event` (string, mandatory): The name of the event being sent.
*   `device_id` (number, mandatory): Authenticated field - identifies which device the event came from (added by server based on authenticated device connection).
*   Additional fields depend on the specific event type.

**Example Client Message:**
```json
{
  "device_id": 42,
  "channel": 0,
  "payload": {
    "cmd": "terminal_start",
    "shell": "bash",
    "cwd": "/home/user/project"
  }
}
```

**Example Server Response:**
```json
{
  "event": "terminal_started",
  "device_id": 42,
  "terminal_id": "uuid-1234-5678",
  "channel": "uuid-1234-5678",
  "pid": 12345
}
```

**Note:** The server acts as a translator between the client-side and device-side protocols:
- When a client sends a command, the server transforms it from the client format to the device format
- When a device sends an event, the server adds the `device_id` and routes it to the appropriate client sessions

---

## Actions

Actions are messages sent from the server to the device, placed within the `payload` of a raw message. They instruct the device to perform a specific operation and are handled by the [`BaseHandler`](./base.py) and its subclasses.

**Action Structure (inside the `payload`):**

```json
{
  "cmd": "<command_name>",
  "arg1": "value1",
  "arg2": "value2",
  "source_client_session": "channel.abc123"
}
```

**Field Descriptions:**

*   `cmd` (string, mandatory): The name of the action to be executed (e.g., `terminal_start`, `file_read`, `system_info`).
*   `source_client_session` (string, mandatory): The channel name of the client session that originated this command. This field is automatically added by the server and allows devices to identify which specific client sent the command.
*   Additional fields depend on the specific command (see individual command documentation below).

**Note**: Actions do not require targeting information - responses are automatically routed using the client session management system.

### `terminal_start`

Initiates a new terminal session on the device. Handled by [`terminal_start`](./terminal_handlers.py).

**Payload Fields:**

*   `shell` (string, optional): The shell to use (e.g., `/bin/bash`). Defaults to the system's default shell.
*   `cwd` (string, optional): The working directory to start the terminal in. Defaults to the user's home directory.
*   `project_id` (string, optional): The ID of the project this terminal is associated with.

**Responses:**

*   On success, the device will respond with a [`terminal_started`](#terminal_started) event.
*   On error, a generic [`error`](#error) event is sent.

### `terminal_send`

Sends input data to a running terminal session. Handled by [`terminal_send`](./terminal_handlers.py).

**Payload Fields:**

*   `terminal_id` (string, mandatory): The ID of the terminal session to send data to.
*   `data` (string, mandatory): The data to write to the terminal's standard input.

**Responses:**

*   On success, the device will respond with a [`terminal_send_ack`](#terminal_send_ack) event.
*   On error, a generic [`error`](#error) event is sent.

### `terminal_stop`

Terminates a running terminal session. Handled by [`terminal_stop`](./terminal_handlers.py).

**Payload Fields:**

*   `terminal_id` (string, mandatory): The ID of the terminal session to stop.

**Responses:**

*   The device immediately responds with a [`terminal_stopped`](#terminal_stopped) event to acknowledge the request.
*   Once the terminal is successfully stopped, a [`terminal_stop_completed`](#terminal_stop_completed) event is sent.
*   If the terminal is not found, a [`terminal_stop_completed`](#terminal_stop_completed) with a "not_found" status is sent.

### `terminal_list`

Requests a list of all active terminal sessions. Handled by [`terminal_list`](./terminal_handlers.py).

**Payload Fields:**

*   `project_id` (string, optional): If provided, filters terminals by this project ID. If "all", lists all terminals.

**Responses:**

*   On success, the device will respond with a [`terminal_list`](#terminal_list-event) event.

### `system_info`

Requests system information from the device. Handled by [`system_info`](./system_handlers.py).

**Payload Fields:**

This action does not require any payload fields.

**Responses:**

*   On success, the device will respond with a [`system_info`](#system_info-event) event.

### `file_read`

Reads the content of a file. Handled by [`file_read`](./file_handlers.py).

**Payload Fields:**

*   `path` (string, mandatory): The absolute path to the file to read.

**Responses:**

*   On success, the device will respond with a [`file_read_response`](#file_read_response) event.
*   On error, a generic [`error`](#error) event is sent.

### `file_write`

Writes content to a file. Handled by [`file_write`](./file_handlers.py).

**Payload Fields:**

*   `path` (string, mandatory): The absolute path to the file to write to.
*   `content` (string, mandatory): The content to write to the file.

**Responses:**

*   On success, the device will respond with a [`file_write_response`](#file_write_response) event.
*   On error, a generic [`error`](#error) event is sent.

### `directory_list`

Lists the contents of a directory. Handled by [`directory_list`](./file_handlers.py).

**Payload Fields:**

*   `path` (string, optional): The path to the directory to list. Defaults to the current directory.
*   `show_hidden` (boolean, optional): Whether to include hidden files in the listing. Defaults to `false`.

**Responses:**

*   On success, the device will respond with a [`directory_list_response`](#directory_list_response) event.
*   On error, a generic [`error`](#error) event is sent.

### `file_info`

Gets information about a file or directory. Handled by [`file_info`](./file_handlers.py).

**Payload Fields:**

*   `path` (string, mandatory): The path to the file or directory.

**Responses:**

*   On success, the device will respond with a [`file_info_response`](#file_info_response) event.

### `file_delete`

Deletes a file or directory. Handled by [`file_delete`](./file_handlers.py).

**Payload Fields:**

*   `path` (string, mandatory): The path to the file or directory to delete.
*   `recursive` (boolean, optional): If `true`, recursively deletes a directory and its contents. Defaults to `false`.

**Responses:**

*   On success, the device will respond with a [`file_delete_response`](#file_delete_response) event.
*   On error, a generic [`error`](#error) event is sent.

### `file_create`

Creates a new file. Handled by [`file_create`](./file_handlers.py).

**Payload Fields:**

*   `parent_path` (string, mandatory): The absolute path to the parent directory where the file should be created.
*   `file_name` (string, mandatory): The name of the file to create. Must not contain path separators or be special directories (`.`, `..`).
*   `content` (string, optional): The initial content for the file. Defaults to empty string.

**Responses:**

*   On success, the device will respond with a [`file_create_response`](#file_create_response) event.
*   On error, a generic [`error`](#error) event is sent.

### `folder_create`

Creates a new folder/directory. Handled by [`folder_create`](./file_handlers.py).

**Payload Fields:**

*   `parent_path` (string, mandatory): The absolute path to the parent directory where the folder should be created.
*   `folder_name` (string, mandatory): The name of the folder to create. Must not contain path separators or be special directories (`.`, `..`).

**Responses:**

*   On success, the device will respond with a [`folder_create_response`](#folder_create_response) event.
*   On error, a generic [`error`](#error) event is sent.

### `file_rename`

Renames a file or folder. Handled by [`file_rename`](./file_handlers.py).

**Payload Fields:**

*   `old_path` (string, mandatory): The absolute path to the file or folder to rename.
*   `new_name` (string, mandatory): The new name (not full path) for the item. Must not contain path separators or be special directories (`.`, `..`).

**Responses:**

*   On success, the device will respond with a [`file_rename_response`](#file_rename_response) event.
*   On error, a generic [`error`](#error) event is sent.

### `content_request`

Requests cached content by SHA-256 hash. This action is used to implement content caching for performance optimization, allowing clients to request large content (such as file content, HTML diffs, etc.) by hash instead of receiving it in every WebSocket message. For large content (>200KB), the response will be automatically chunked into multiple messages for reliable transmission. Handled by [`content_request`](./file_handlers.py).

**Payload Fields:**

*   `content_hash` (string, mandatory): The SHA-256 hash of the content to retrieve (with "sha256:" prefix).
*   `request_id` (string, mandatory): A unique identifier for this request, used to match with the response.

**Responses:**

*   On success, the device will respond with one or more [`content_response`](#content_response) events containing the cached content. Large content is automatically chunked.
*   On error (content not found), a [`content_response`](#content_response) event with `success: false` is sent.

## Project State Actions

Project state actions manage the state of project folders, including file structures, Git metadata, open files, and folder expansion states. These actions provide real-time synchronization between the client and server for project management functionality.

**Note:** Project state is automatically initialized when a client session connects with a `project_folder_path` property. No manual initialization command is required.

**Tab Management:** Open tabs are internally managed using a dictionary structure with unique keys to prevent duplicates and race conditions:
- File tabs use `file_path` as the unique key
- Diff tabs use a composite key: `diff:{file_path}:{from_ref}:{to_ref}:{from_hash}:{to_hash}`
- Untitled tabs use their `tab_id` as the unique key

This ensures that sending the same command multiple times (e.g., `project_state_diff_open` with identical parameters) will not create duplicate tabs but will instead activate the existing tab.

### `project_state_folder_expand`

Expands a folder in the project tree, loading its contents and enabling monitoring for that folder level. When a folder is expanded, the system proactively loads one level down for all subdirectories to enable immediate expansion in the UI. This action also scans items in the expanded folder and preloads content for any non-empty subdirectories.

**Payload Fields:**

*   `project_id` (string, mandatory): The project ID from the initialized project state.
*   `folder_path` (string, mandatory): The absolute path to the folder to expand.

**Responses:**

*   On success, the device will respond with a [`project_state_folder_expand_response`](#project_state_folder_expand_response) event, followed by a [`project_state_update`](#project_state_update) event containing the updated file structure with preloaded subdirectory contents.
*   On error, a generic [`error`](#error) event is sent.

### `project_state_folder_collapse`

Collapses a folder in the project tree, stopping monitoring for that folder level.

**Payload Fields:**

*   `project_id` (string, mandatory): The project ID from the initialized project state.
*   `folder_path` (string, mandatory): The absolute path to the folder to collapse.

**Responses:**

*   On success, the device will respond with a [`project_state_folder_collapse_response`](#project_state_folder_collapse_response) event, followed by a [`project_state_update`](#project_state_update) event.
*   On error, a generic [`error`](#error) event is sent.

### `project_state_file_open`

Marks a file as open in the project state, tracking it as part of the current editing session.

**Duplicate Prevention:** This action prevents creating duplicate file tabs by using the `file_path` as a unique key. If a file tab with the same path already exists, it will be activated instead of creating a new one.

**Payload Fields:**

*   `project_id` (string, mandatory): The project ID from the initialized project state.
*   `file_path` (string, mandatory): The absolute path to the file to open.
*   `set_active` (boolean, optional): Whether to set this file as the active file. Defaults to `true`.

**Responses:**

*   On success, the device will respond with a [`project_state_file_open_response`](#project_state_file_open_response) event, followed by a [`project_state_update`](#project_state_update) event.
*   On error, a generic [`error`](#error) event is sent.

### `project_state_tab_close`

Closes a tab in the project state, removing it from the current editing session.

**Payload Fields:**

*   `project_id` (string, mandatory): The project ID from the initialized project state.
*   `tab_id` (string, mandatory): The unique ID of the tab to close.

**Responses:**

*   On success, the device will respond with a [`project_state_tab_close_response`](#project_state_tab_close_response) event, followed by a [`project_state_update`](#project_state_update) event.
*   On error, a generic [`error`](#error) event is sent.

### `project_state_set_active_tab`

Sets the currently active tab in the project state. Only one tab can be active at a time.

**Payload Fields:**

*   `project_id` (string, mandatory): The project ID from the initialized project state.
*   `tab_id` (string, optional): The unique ID of the tab to set as active. If `null` or omitted, clears the active tab.

**Responses:**

*   On success, the device will respond with a [`project_state_set_active_tab_response`](#project_state_set_active_tab_response) event, followed by a [`project_state_update`](#project_state_update) event.
*   On error, a generic [`error`](#error) event is sent.

### `project_state_diff_open`

Opens a diff tab for comparing file versions at different points in the git timeline. This replaces the previous `project_state_create_diff_tab` action with a more efficient approach that doesn't require the client to provide file content, instead using git timeline references.

**Duplicate Prevention:** This action prevents creating duplicate diff tabs by using a unique key based on `file_path`, `from_ref`, `to_ref`, `from_hash`, and `to_hash`. If a diff tab with the same parameters already exists, it will be activated instead of creating a new one.

**Payload Fields:**

*   `project_id` (string, mandatory): The project ID from the initialized project state.
*   `file_path` (string, mandatory): The absolute path to the file to create a diff for.
*   `from_ref` (string, mandatory): The source reference point. Must be one of:
    - `"head"`: Content from the HEAD commit
    - `"staged"`: Content from the staging area
    - `"working"`: Current working directory content
    - `"commit"`: Content from a specific commit (requires `from_hash`)
*   `to_ref` (string, mandatory): The target reference point. Same options as `from_ref`.
*   `from_hash` (string, optional): Required when `from_ref` is `"commit"`. The commit hash to get content from.
*   `to_hash` (string, optional): Required when `to_ref` is `"commit"`. The commit hash to get content from.

**Responses:**

*   On success, the device will respond with a [`project_state_diff_open_response`](#project_state_diff_open_response) event, followed by a [`project_state_update`](#project_state_update) event.
*   On error, a generic [`error`](#error) event is sent.

### `project_state_diff_content_request`

Requests the content for a specific diff tab identified by its diff parameters. This action is used to load the actual file content (original and modified) as well as HTML diff data for diff tabs after they have been created by [`project_state_diff_open`](#project_state_diff_open). For large content (>200KB), the response will be automatically chunked into multiple messages for reliable transmission.

**Content Types:** This action can request content for a diff:
- `original`: The original (from) content of the diff
- `modified`: The modified (to) content of the diff  
- `html_diff`: The HTML diff versions for rich visual display
- `all`: All content types returned as a single JSON object (recommended for efficiency)

**Payload Fields:**

*   `project_id` (string, mandatory): The project ID from the initialized project state.
*   `file_path` (string, mandatory): The absolute path to the file the diff is for.
*   `from_ref` (string, mandatory): The source reference point used in the diff. Must match the diff tab parameters.
*   `to_ref` (string, mandatory): The target reference point used in the diff. Must match the diff tab parameters.
*   `from_hash` (string, optional): The commit hash for `from_ref` if it was `"commit"`. Must match the diff tab parameters.
*   `to_hash` (string, optional): The commit hash for `to_ref` if it was `"commit"`. Must match the diff tab parameters.
*   `content_type` (string, mandatory): The type of content to request. Must be one of:
    - `"original"`: Request the original (from) content
    - `"modified"`: Request the modified (to) content
    - `"html_diff"`: Request the HTML diff versions for visual display
    - `"all"`: Request all content types as a single JSON object
*   `request_id` (string, mandatory): Unique identifier for this request to match with the response.

**Responses:**

*   On success, the device will respond with one or more [`project_state_diff_content_response`](#project_state_diff_content_response) events. Large content is automatically chunked.
*   On error, a generic [`error`](#error) event is sent.

### `project_state_git_stage`

Stages file(s) for commit in the project's git repository. Supports both single file and bulk operations. Handled by [`project_state_git_stage`](./project_state_handlers.py).

**Payload Fields:**

*   `project_id` (string, mandatory): The project ID from the initialized project state.
*   `file_path` (string, optional): The absolute path to a single file to stage. Used for backward compatibility.
*   `file_paths` (array of strings, optional): Array of absolute paths to files to stage. Used for bulk operations.
*   `stage_all` (boolean, optional): If true, stages all unstaged changes in the repository. Takes precedence over file_path/file_paths.

**Operation Modes:**
- Single file: Provide `file_path`
- Bulk operation: Provide `file_paths` array  
- Stage all: Set `stage_all` to true

**Responses:**

*   On success, the device will respond with a [`project_state_git_stage_response`](#project_state_git_stage_response) event, followed by a [`project_state_update`](#project_state_update) event with updated git status.
*   On error, a generic [`error`](#error) event is sent.

### `project_state_git_unstage`

Unstages file(s) (removes from staging area) in the project's git repository. Supports both single file and bulk operations. Handled by [`project_state_git_unstage`](./project_state_handlers.py).

**Payload Fields:**

*   `project_id` (string, mandatory): The project ID from the initialized project state.
*   `file_path` (string, optional): The absolute path to a single file to unstage. Used for backward compatibility.
*   `file_paths` (array of strings, optional): Array of absolute paths to files to unstage. Used for bulk operations.
*   `unstage_all` (boolean, optional): If true, unstages all staged changes in the repository. Takes precedence over file_path/file_paths.

**Operation Modes:**
- Single file: Provide `file_path`
- Bulk operation: Provide `file_paths` array  
- Unstage all: Set `unstage_all` to true

**Responses:**

*   On success, the device will respond with a [`project_state_git_unstage_response`](#project_state_git_unstage_response) event, followed by a [`project_state_update`](#project_state_update) event with updated git status.
*   On error, a generic [`error`](#error) event is sent.

### `project_state_git_revert`

Reverts file(s) to their HEAD version, discarding local changes in the project's git repository. Supports both single file and bulk operations. Handled by [`project_state_git_revert`](./project_state_handlers.py).

**Payload Fields:**

*   `project_id` (string, mandatory): The project ID from the initialized project state.
*   `file_path` (string, optional): The absolute path to a single file to revert. Used for backward compatibility.
*   `file_paths` (array of strings, optional): Array of absolute paths to files to revert. Used for bulk operations.
*   `revert_all` (boolean, optional): If true, reverts all unstaged changes in the repository. Takes precedence over file_path/file_paths.

**Operation Modes:**
- Single file: Provide `file_path`
- Bulk operation: Provide `file_paths` array  
- Revert all: Set `revert_all` to true

**Responses:**

*   On success, the device will respond with a [`project_state_git_revert_response`](#project_state_git_revert_response) event, followed by a [`project_state_update`](#project_state_update) event with updated git status.
*   On error, a generic [`error`](#error) event is sent.

### `project_state_git_commit`

Commits staged changes with a commit message in the project's git repository. Handled by [`project_state_git_commit`](./project_state_handlers.py).

**Payload Fields:**

*   `project_id` (string, mandatory): The project ID from the initialized project state.
*   `commit_message` (string, mandatory): The commit message for the changes being committed.

**Responses:**

*   On success, the device will respond with a [`project_state_git_commit_response`](#project_state_git_commit_response) event, followed by a [`project_state_update`](#project_state_update) event with updated git status.
*   On error, a generic [`error`](#error) event is sent.

### Client Session Management

### `client_sessions_update`

Sends updated client session information to the device. This is a special internal action used by the server to inform devices about connected client sessions.

**Payload Fields:**

*   `sessions` (array, mandatory): Array of client session objects containing connection information.

**Responses:**

This action does not generate a response event.

---

## Events

Events are messages sent from the device to the server, placed within the `payload` of a raw message. They are sent in response to an action or to notify the server of a state change.

**Event Structure (inside the `payload`):**

```json
{
  "event": "<event_name>",
  // Event-specific fields...
  "device_id": 123,
  "project_id": "<project_uuid>",
  "client_sessions": ["channel.abc123", "channel.def456"]
}
```

**Standard Fields (automatically added by the system):**

*   `event` (string, mandatory): The name of the event being sent (e.g., `terminal_started`).
*   `device_id` (integer, mandatory): The ID of the authenticated device that generated this event. **Added by the server based on the authenticated connection for security** - devices cannot self-identify.
*   `project_id` (string, optional): The project UUID associated with this event, used for project-scoped filtering. Sent by the device.
*   `client_sessions` (array, optional): Array of client session channel names that should receive this event. **Added by the device's terminal manager** based on interested client sessions. When present, the event is sent only to these specific sessions. When absent, the event is broadcast to all sessions for the device owner.

**Event-Specific Fields:**

Each event type includes additional fields specific to its purpose, documented in the individual event sections below.

### <a name="error"></a>`error`

A generic event sent when an error occurs during the execution of an action.

**Event Fields:**

*   `message` (string, mandatory): A description of the error that occurred.

### <a name="terminal_started"></a>`terminal_started`

Confirms that a new terminal session has been successfully started. Triggered by a `terminal_start` action. Handled by [`terminal_start`](./terminal_handlers.py).

**Event Fields:**

*   `terminal_id` (string, mandatory): The unique ID of the newly created terminal session.
*   `channel` (string, mandatory): The channel name for terminal I/O.
*   `pid` (integer, mandatory): The process ID (PID) of the terminal process.
*   `shell` (string, optional): The shell that was used to start the terminal.
*   `cwd` (string, optional): The working directory where the terminal was started.
*   `project_id` (string, optional): The project ID associated with the terminal.

### <a name="terminal_data"></a>`terminal_data`

Streams real-time terminal output data from a running terminal session to connected clients. This event is automatically generated whenever the terminal process produces output (stdout/stderr). Generated by [`TerminalSession`](./session.py) through the terminal manager's session-aware messaging system.

**Event-Specific Fields:**

*   `channel` (string, mandatory): The terminal UUID identifying which terminal session produced this output. This matches the `terminal_id` from the corresponding `terminal_started` event.
*   `data` (string, mandatory): The raw terminal output data. **See detailed description below.**

**The `data` Field - Detailed Specification:**

The `data` field contains the exact bytes output by the terminal process, decoded as a UTF-8 string with error handling:

*   **Encoding**: UTF-8 with `errors="ignore"` - invalid UTF-8 sequences are silently dropped
*   **Content**: Raw terminal output including:
  - Regular command output (stdout)
  - Error messages (stderr) - combined with stdout in PTY mode  
  - ANSI escape sequences for colors, cursor positioning, screen clearing, etc.
  - Control characters (newlines, tabs, backspace, etc.)
  - Shell prompts and interactive application output
*   **Buffering**: Data is read in 1024-byte chunks from the terminal process and sent immediately (no line buffering)
*   **Binary Safety**: Binary data is handled via UTF-8 decoding with error tolerance
*   **Size**: Individual chunks are typically ≤1024 characters, but can be smaller for real-time responsiveness

**Examples of `data` content:**
```
"Hello, World!\n"                           // Simple command output
"\u001b[32mSuccess\u001b[0m\n"             // ANSI colored text  
"user@host:~/project$ "                     // Shell prompt
"\u001b[2J\u001b[H"                         // Clear screen escape sequence
"Progress: [████████████████████] 100%\r"   // Progress bar with carriage return
```

**Security Note**: The `device_id` field is automatically injected by the server based on the authenticated connection - the device cannot and should not specify its own ID. The `project_id` and `client_sessions` fields are added by the device's terminal manager for proper routing and filtering.

### <a name="terminal_exit"></a>`terminal_exit`

Notifies the server that a terminal session has terminated. This can be due to the process ending or the session being stopped. Handled by [`terminal_start`](./terminal_handlers.py).

**Event Fields:**

*   `terminal_id` (string, mandatory): The ID of the terminal session that has exited.
*   `returncode` (integer, mandatory): The exit code of the terminal process.
*   `project_id` (string, optional): The project ID associated with the terminal.

### <a name="terminal_send_ack"></a>`terminal_send_ack`

Acknowledges the receipt of a `terminal_send` action. Handled by [`terminal_send`](./terminal_handlers.py). This event carries no extra fields.

### <a name="terminal_stopped"></a>`terminal_stopped`

Acknowledges that a `terminal_stop` request has been received and is being processed. Handled by [`terminal_stop`](./terminal_handlers.py).

**Event Fields:**

*   `terminal_id` (string, mandatory): The ID of the terminal being stopped.
*   `status` (string, mandatory): The status of the stop operation (e.g., "stopping", "not_found").
*   `message` (string, mandatory): A descriptive message about the status.
*   `project_id` (string, optional): The project ID associated with the terminal.

### <a name="terminal_stop_completed"></a>`terminal_stop_completed`

Confirms that a terminal session has been successfully stopped. Handled by [`terminal_stop`](./terminal_handlers.py).

**Event Fields:**

*   `terminal_id` (string, mandatory): The ID of the stopped terminal.
*   `status` (string, mandatory): The final status ("success", "timeout", "error", "not_found").
*   `message` (string, mandatory): A descriptive message.
*   `project_id` (string, optional): The project ID associated with the terminal.

### <a name="terminal_list-event"></a>`terminal_list`

Provides the list of active terminal sessions in response to a `terminal_list` action. Handled by [`terminal_list`](./terminal_handlers.py).

**Event Fields:**

*   `sessions` (array, mandatory): A list of active terminal session objects.
*   `project_id` (string, optional): The project ID that was used to filter the list.

### <a name="system_info-event"></a>`system_info`

Provides system information in response to a `system_info` action. Handled by [`system_info`](./system_handlers.py).

**Event Fields:**

*   `info` (object, mandatory): An object containing system information, including:
    *   `cpu_percent` (float): CPU usage percentage.
    *   `memory` (object): Memory usage statistics.
    *   `disk` (object): Disk usage statistics.
    *   `os_info` (object): Operating system details, including `os_type`, `os_version`, `architecture`, `default_shell`, and `default_cwd`.

### <a name="file_read_response"></a>`file_read_response`

Returns the content of a file in response to a `file_read` action. Handled by [`file_read`](./file_handlers.py).

**Event Fields:**

*   `path` (string, mandatory): The path of the file that was read.
*   `content` (string, mandatory): The content of the file.
*   `size` (integer, mandatory): The size of the file in bytes.

### <a name="file_write_response"></a>`file_write_response`

Confirms that a file has been written successfully in response to a `file_write` action. Handled by [`file_write`](./file_handlers.py).

**Event Fields:**

*   `path` (string, mandatory): The path of the file that was written.
*   `bytes_written` (integer, mandatory): The number of bytes written to the file.
*   `success` (boolean, mandatory): Indicates whether the write operation was successful.

### <a name="directory_list_response"></a>`directory_list_response`

Returns the contents of a directory in response to a `directory_list` action. Handled by [`directory_list`](./file_handlers.py).

**Event Fields:**

*   `path` (string, mandatory): The path of the directory that was listed.
*   `items` (array, mandatory): A list of objects, each representing a file or directory in the listed directory.
*   `count` (integer, mandatory): The number of items in the `items` list.

### <a name="file_info_response"></a>`file_info_response`

Returns information about a file or directory in response to a `file_info` action. Handled by [`file_info`](./file_handlers.py).

**Event Fields:**

*   `path` (string, mandatory): The path of the file or directory.
*   `exists` (boolean, mandatory): Indicates whether the file or directory exists.
*   `is_file` (boolean, optional): Indicates if the path is a file.
*   `is_dir` (boolean, optional): Indicates if the path is a directory.
*   `is_symlink` (boolean, optional): Indicates if the path is a symbolic link.
*   `size` (integer, optional): The size of the file in bytes.
*   `modified` (float, optional): The last modification time (timestamp).
*   `accessed` (float, optional): The last access time (timestamp).
*   `created` (float, optional): The creation time (timestamp).
*   `permissions` (string, optional): The file permissions in octal format.
*   `owner_uid` (integer, optional): The user ID of the owner.
*   `group_gid` (integer, optional): The group ID of the owner.

### <a name="file_delete_response"></a>`file_delete_response`

Confirms that a file or directory has been deleted in response to a `file_delete` action. Handled by [`file_delete`](./file_handlers.py).

**Event Fields:**

*   `path` (string, mandatory): The path of the deleted file or directory.
*   `deleted_type` (string, mandatory): The type of the deleted item ("file" or "directory").
*   `success` (boolean, mandatory): Indicates whether the deletion was successful.

### <a name="file_create_response"></a>`file_create_response`

Confirms that a file has been created successfully in response to a `file_create` action. Handled by [`file_create`](./file_handlers.py).

**Event Fields:**

*   `parent_path` (string, mandatory): The path of the parent directory where the file was created.
*   `file_name` (string, mandatory): The name of the created file.
*   `file_path` (string, mandatory): The full absolute path to the created file.
*   `success` (boolean, mandatory): Indicates whether the creation was successful.

### <a name="folder_create_response"></a>`folder_create_response`

Confirms that a folder has been created successfully in response to a `folder_create` action. Handled by [`folder_create`](./file_handlers.py).

**Event Fields:**

*   `parent_path` (string, mandatory): The path of the parent directory where the folder was created.
*   `folder_name` (string, mandatory): The name of the created folder.
*   `folder_path` (string, mandatory): The full absolute path to the created folder.
*   `success` (boolean, mandatory): Indicates whether the creation was successful.

### <a name="file_rename_response"></a>`file_rename_response`

Confirms that a file or folder has been renamed successfully in response to a `file_rename` action. Handled by [`file_rename`](./file_handlers.py).

**Event Fields:**

*   `old_path` (string, mandatory): The original path of the renamed item.
*   `new_path` (string, mandatory): The new path of the renamed item.
*   `new_name` (string, mandatory): The new name of the item.
*   `is_directory` (boolean, mandatory): Indicates whether the renamed item is a directory.
*   `success` (boolean, mandatory): Indicates whether the rename was successful.

### <a name="content_response"></a>`content_response`

Returns cached content in response to a `content_request` action. This is part of the content caching system used for performance optimization. For large content (>200KB), the response is automatically chunked into multiple messages to ensure reliable transmission over WebSocket connections. Handled by [`content_request`](./file_handlers.py).

**Event Fields:**

*   `request_id` (string, mandatory): The unique identifier from the corresponding request, used to match request and response.
*   `content_hash` (string, mandatory): The SHA-256 hash that was requested.
*   `content` (string, optional): The cached content or chunk content if found and `success` is true. Null if content was not found.
*   `success` (boolean, mandatory): Indicates whether the content was found and returned successfully.
*   `error` (string, optional): Error message if `success` is false (e.g., "Content not found in cache").
*   `chunked` (boolean, mandatory): Indicates whether this response is part of a chunked transfer. False for single responses, true for chunked responses.

**Chunked Transfer Fields (when `chunked` is true):**

*   `transfer_id` (string, mandatory): Unique identifier for the chunked transfer session.
*   `chunk_index` (integer, mandatory): Zero-based index of this chunk in the sequence.
*   `chunk_count` (integer, mandatory): Total number of chunks in the transfer.
*   `chunk_size` (integer, mandatory): Size of this chunk in bytes.
*   `total_size` (integer, mandatory): Total size of the complete content in bytes.
*   `chunk_hash` (string, mandatory): SHA-256 hash of this chunk for verification.
*   `is_final_chunk` (boolean, mandatory): Indicates if this is the last chunk in the sequence.

**Chunked Transfer Process:**

1. **Size Check**: Content >200KB is automatically chunked into 64KB chunks
2. **Sequential Delivery**: Chunks are sent in order with increasing `chunk_index`
3. **Client Assembly**: Client collects all chunks and verifies integrity using hashes
4. **Hash Verification**: Both individual chunk hashes and final content hash are verified
5. **Error Handling**: Missing chunks or hash mismatches trigger request failure

**Example Non-Chunked Response:**
```json
{
  "event": "content_response",
  "request_id": "req_abc123",
  "content_hash": "sha256:...",
  "content": "Small content here",
  "success": true,
  "chunked": false
}
```

**Example Chunked Response (first chunk):**
```json
{
  "event": "content_response", 
  "request_id": "req_abc123",
  "content_hash": "sha256:...",
  "content": "First chunk content...",
  "success": true,
  "chunked": true,
  "transfer_id": "transfer_xyz789",
  "chunk_index": 0,
  "chunk_count": 5,
  "chunk_size": 65536,
  "total_size": 300000,
  "chunk_hash": "chunk_sha256:...",
  "is_final_chunk": false
}
```

### Project State Events

### <a name="project_state_initialized"></a>`project_state_initialized`

Confirms that project state has been successfully initialized for a client session. Contains the complete initial project state including file structure and Git metadata.

**Event Fields:**

*   `project_id` (string, mandatory): The project ID for the initialized project state.
*   `project_folder_path` (string, mandatory): The absolute path to the project folder.
*   `is_git_repo` (boolean, mandatory): Whether the project folder is a Git repository.
*   `git_branch` (string, optional): The current Git branch name if available.
*   `git_status_summary` (object, optional): Summary of Git status counts (modified, added, deleted, untracked files).
*   `git_detailed_status` (object, optional): Detailed Git status with comprehensive file change information and content hashes. Contains:
    *   `head_commit_hash` (string, optional): SHA hash of the HEAD commit.
    *   `staged_changes` (array, optional): Array of staged file changes. Each change contains:
        *   `file_repo_path` (string): Relative path from repository root.
        *   `file_name` (string): Just the filename (basename).
        *   `file_abs_path` (string): Absolute path to the file.
        *   `change_type` (string): Type of change following git's native types ('added', 'modified', 'deleted', 'untracked'). Note: renames appear as separate 'deleted' and 'added' entries unless git detects them as modifications.
        *   `content_hash` (string, optional): SHA256 hash of current file content. Null for deleted files.
        *   `is_staged` (boolean): Always true for staged changes.
        *   `diff_details` (object, optional): Per-character diff information computed using diff-match-patch algorithm. Contains:
            *   `diffs` (array): Array of diff operations, each containing:
                *   `operation` (integer): Diff operation type (-1 = delete, 0 = equal, 1 = insert).
                *   `text` (string): The text content for this operation.
            *   `stats` (object): Statistics about the diff:
                *   `char_additions` (integer): Number of characters added.
                *   `char_deletions` (integer): Number of characters deleted.
                *   `char_unchanged` (integer): Number of characters unchanged.
                *   `total_changes` (integer): Total number of character changes (additions + deletions).
            *   `algorithm` (string): Always "diff-match-patch" indicating the algorithm used.
    *   `unstaged_changes` (array, optional): Array of unstaged file changes with same structure as staged_changes but `is_staged` is always false.
    *   `untracked_files` (array, optional): Array of untracked files with same structure as staged_changes but `is_staged` is always false and `change_type` is always 'untracked'.
*   `open_tabs` (array, mandatory): Array of tab objects currently open. Internally stored as a dictionary with unique keys to prevent duplicates, but serialized as an array for API responses. Each tab object contains:
    *   `tab_id` (string, mandatory): Unique identifier for the tab.
    *   `tab_type` (string, mandatory): Type of tab ("file", "diff", "untitled", "image", "audio", "video").
    *   `title` (string, mandatory): Display title for the tab.
    *   `file_path` (string, optional): Path for file-based tabs.
    *   `content` (string, optional): Text content or base64 for media. When content caching is enabled, this field may be excluded from project state events if the content is available via `content_hash`.
    *   `original_content` (string, optional): For diff tabs - original content. When content caching is enabled, this field may be excluded from project state events if the content is available via `original_content_hash`.
    *   `modified_content` (string, optional): For diff tabs - modified content. When content caching is enabled, this field may be excluded from project state events if the content is available via `modified_content_hash`.
    *   `is_dirty` (boolean, mandatory): Whether the tab has unsaved changes.
    *   `mime_type` (string, optional): MIME type for media files.
    *   `encoding` (string, optional): Content encoding (base64, utf-8, etc.).
    *   `metadata` (object, optional): Additional metadata. When content caching is enabled, large metadata such as `html_diff_versions` may be excluded from project state events if available via `html_diff_hash`.
    *   `content_hash` (string, optional): SHA-256 hash of the tab content for content caching optimization. When present, the content can be retrieved via [`content_request`](#content_request) action.
    *   `original_content_hash` (string, optional): SHA-256 hash of the original content for diff tabs. When present, the original content can be retrieved via [`content_request`](#content_request) action.
    *   `modified_content_hash` (string, optional): SHA-256 hash of the modified content for diff tabs. When present, the modified content can be retrieved via [`content_request`](#content_request) action.
    *   `html_diff_hash` (string, optional): SHA-256 hash of the HTML diff versions JSON for diff tabs. When present, the HTML diff data can be retrieved via [`content_request`](#content_request) action as a JSON string.
*   `active_tab` (object, optional): The currently active tab object, or null if no tab is active.
*   `items` (array, mandatory): Flattened array of all visible file/folder items. Always includes root level items and one level down from the project root (since the project root is treated as expanded by default). Also includes items within explicitly expanded folders and one level down from each expanded folder. Each item object contains the following fields:
    *   `name` (string, mandatory): The file or directory name.
    *   `path` (string, mandatory): The absolute path to the file or directory.
    *   `is_directory` (boolean, mandatory): Whether this item is a directory.
    *   `parent_path` (string, mandatory): The absolute path to the parent directory.
    *   `size` (integer, optional): File size in bytes. Only present for files, not directories.
    *   `modified_time` (float, optional): Last modification time as Unix timestamp.
    *   `is_git_tracked` (boolean, optional): Whether the file is tracked by Git. Only present if project is a Git repository.
    *   `git_status` (string, optional): Git status of the file ("clean", "modified", "untracked", "ignored"). Only present if project is a Git repository.
    *   `is_hidden` (boolean, mandatory): Whether the file/directory name starts with a dot (hidden file).
    *   `is_ignored` (boolean, mandatory): Whether the file is ignored by Git. Only meaningful if project is a Git repository.
    *   `children` (array, optional): Array of child FileItem objects for directories. Usually null in flattened structure as children are included as separate items.
    *   `is_expanded` (boolean, mandatory): Whether this directory is expanded in the project tree. Only meaningful for directories.
    *   `is_loaded` (boolean, mandatory): Whether the directory contents have been loaded and are available. Always true for files. For directories, true indicates that the directory is being monitored (in monitored_folders) and its contents are loaded and available in the items list, enabling immediate expansion when requested.
*   `timestamp` (float, mandatory): Unix timestamp of when the state was generated.

### <a name="project_state_update"></a>`project_state_update`

Sent automatically when project state changes due to file system modifications, Git changes, or user actions. Contains the complete updated project state.

**Event Fields:**

*   `project_id` (string, mandatory): The project ID this update applies to.
*   `project_folder_path` (string, mandatory): The absolute path to the project folder.
*   `is_git_repo` (boolean, mandatory): Whether the project folder is a Git repository.
*   `git_branch` (string, optional): The current Git branch name if available.
*   `git_status_summary` (object, optional): Updated summary of Git status counts.
*   `git_detailed_status` (object, optional): Updated detailed Git status with comprehensive file change information, content hashes, and per-character diff details (same structure as in `project_state_initialized`).
*   `open_tabs` (array, mandatory): Updated array of tab objects currently open. Internally stored as a dictionary with unique keys to prevent duplicates, but serialized as an array for API responses.
*   `active_tab` (object, optional): Updated active tab object.
*   `items` (array, mandatory): Updated flattened array of all visible file/folder items. Always includes root level items and one level down from the project root (since the project root is treated as expanded by default). Also includes items within explicitly expanded folders and one level down from each expanded folder. Each item object contains the following fields:
    *   `name` (string, mandatory): The file or directory name.
    *   `path` (string, mandatory): The absolute path to the file or directory.
    *   `is_directory` (boolean, mandatory): Whether this item is a directory.
    *   `parent_path` (string, mandatory): The absolute path to the parent directory.
    *   `size` (integer, optional): File size in bytes. Only present for files, not directories.
    *   `modified_time` (float, optional): Last modification time as Unix timestamp.
    *   `is_git_tracked` (boolean, optional): Whether the file is tracked by Git. Only present if project is a Git repository.
    *   `git_status` (string, optional): Git status of the file ("clean", "modified", "untracked", "ignored"). Only present if project is a Git repository.
    *   `is_hidden` (boolean, mandatory): Whether the file/directory name starts with a dot (hidden file).
    *   `is_ignored` (boolean, mandatory): Whether the file is ignored by Git. Only meaningful if project is a Git repository.
    *   `children` (array, optional): Array of child FileItem objects for directories. Usually null in flattened structure as children are included as separate items.
    *   `is_expanded` (boolean, mandatory): Whether this directory is expanded in the project tree. Only meaningful for directories.
    *   `is_loaded` (boolean, mandatory): Whether the directory contents have been loaded and are available. Always true for files. For directories, true indicates that the directory is being monitored (in monitored_folders) and its contents are loaded and available in the items list, enabling immediate expansion when requested.
*   `timestamp` (float, mandatory): Unix timestamp of when the update was generated.

### <a name="project_state_folder_expand_response"></a>`project_state_folder_expand_response`

Confirms the result of a folder expand operation.

**Event Fields:**

*   `project_id` (string, mandatory): The project ID the operation was performed on.
*   `folder_path` (string, mandatory): The path to the folder that was expanded.
*   `success` (boolean, mandatory): Whether the expand operation was successful.

### <a name="project_state_folder_collapse_response"></a>`project_state_folder_collapse_response`

Confirms the result of a folder collapse operation.

**Event Fields:**

*   `project_id` (string, mandatory): The project ID the operation was performed on.
*   `folder_path` (string, mandatory): The path to the folder that was collapsed.
*   `success` (boolean, mandatory): Whether the collapse operation was successful.

### <a name="project_state_file_open_response"></a>`project_state_file_open_response`

Confirms the result of a file open operation.

**Event Fields:**

*   `project_id` (string, mandatory): The project ID the operation was performed on.
*   `file_path` (string, mandatory): The path to the file that was opened.
*   `success` (boolean, mandatory): Whether the file open operation was successful.
*   `set_active` (boolean, mandatory): Whether the file was also set as the active file.

### <a name="project_state_tab_close_response"></a>`project_state_tab_close_response`

Confirms the result of a tab close operation.

**Event Fields:**

*   `project_id` (string, mandatory): The project ID the operation was performed on.
*   `tab_id` (string, mandatory): The ID of the tab that was closed.
*   `success` (boolean, mandatory): Whether the tab close operation was successful.

### <a name="project_state_set_active_tab_response"></a>`project_state_set_active_tab_response`

Confirms the result of setting an active tab.

**Event Fields:**

*   `project_id` (string, mandatory): The project ID the operation was performed on.
*   `tab_id` (string, optional): The ID of the tab that was set as active (null if cleared).
*   `success` (boolean, mandatory): Whether the operation was successful.

### <a name="project_state_diff_open_response"></a>`project_state_diff_open_response`

Confirms the result of opening a diff tab with git timeline references.

**Event Fields:**

*   `project_id` (string, mandatory): The project ID the operation was performed on.
*   `file_path` (string, mandatory): The path to the file the diff tab was created for.
*   `from_ref` (string, mandatory): The source reference point that was used.
*   `to_ref` (string, mandatory): The target reference point that was used.
*   `from_hash` (string, optional): The commit hash used for `from_ref` if it was `"commit"`.
*   `to_hash` (string, optional): The commit hash used for `to_ref` if it was `"commit"`.
*   `success` (boolean, mandatory): Whether the diff tab creation was successful.
*   `error` (string, optional): Error message if the operation failed.

### <a name="project_state_diff_content_response"></a>`project_state_diff_content_response`

Returns the requested content for a specific diff tab, sent in response to a [`project_state_diff_content_request`](#project_state_diff_content_request) action. For large content (>200KB), the response is automatically chunked into multiple messages to ensure reliable transmission over WebSocket connections.

**Event Fields:**

*   `project_id` (string, mandatory): The project ID the operation was performed on.
*   `file_path` (string, mandatory): The path to the file the diff content is for.
*   `from_ref` (string, mandatory): The source reference point used in the diff.
*   `to_ref` (string, mandatory): The target reference point used in the diff.
*   `from_hash` (string, optional): The commit hash used for `from_ref` if it was `"commit"`.
*   `to_hash` (string, optional): The commit hash used for `to_ref` if it was `"commit"`.
*   `content_type` (string, mandatory): The type of content being returned (`"original"`, `"modified"`, `"html_diff"`, or `"all"`).
*   `request_id` (string, mandatory): The unique identifier from the request to match response with request.
*   `success` (boolean, mandatory): Whether the content retrieval was successful.
*   `content` (string, optional): The requested content or chunk content. For `html_diff` type, this is a JSON string containing the HTML diff versions object. For `all` type, this is a JSON string containing an object with `original_content`, `modified_content`, and `html_diff_versions` fields.
*   `error` (string, optional): Error message if the operation failed.
*   `chunked` (boolean, mandatory): Indicates whether this response is part of a chunked transfer. False for single responses, true for chunked responses.

**Chunked Transfer Fields (when `chunked` is true):**

*   `transfer_id` (string, mandatory): Unique identifier for the chunked transfer session.
*   `chunk_index` (integer, mandatory): Zero-based index of this chunk in the sequence.
*   `chunk_count` (integer, mandatory): Total number of chunks in the transfer.
*   `chunk_size` (integer, mandatory): Size of this chunk in bytes.
*   `total_size` (integer, mandatory): Total size of the complete content in bytes.
*   `chunk_hash` (string, mandatory): SHA-256 hash of this chunk for verification.
*   `is_final_chunk` (boolean, mandatory): Indicates if this is the last chunk in the sequence.

**Note:** The chunked transfer process follows the same pattern as described in [`content_response`](#content_response), with content >200KB automatically split into 64KB chunks for reliable transmission.

### <a name="project_state_git_stage_response"></a>`project_state_git_stage_response`

Confirms the result of a git stage operation. Supports responses for both single file and bulk operations.

**Event Fields:**

*   `project_id` (string, mandatory): The project ID the operation was performed on.
*   `file_path` (string, optional): The path to the file that was staged (for single file operations).
*   `file_paths` (array of strings, optional): Array of paths to files that were staged (for bulk operations).
*   `stage_all` (boolean, optional): Present if the operation was a "stage all" operation.
*   `success` (boolean, mandatory): Whether the stage operation was successful.
*   `error` (string, optional): Error message if the operation failed.

### <a name="project_state_git_unstage_response"></a>`project_state_git_unstage_response`

Confirms the result of a git unstage operation. Supports responses for both single file and bulk operations.

**Event Fields:**

*   `project_id` (string, mandatory): The project ID the operation was performed on.
*   `file_path` (string, optional): The path to the file that was unstaged (for single file operations).
*   `file_paths` (array of strings, optional): Array of paths to files that were unstaged (for bulk operations).
*   `unstage_all` (boolean, optional): Present if the operation was an "unstage all" operation.
*   `success` (boolean, mandatory): Whether the unstage operation was successful.
*   `error` (string, optional): Error message if the operation failed.

### <a name="project_state_git_revert_response"></a>`project_state_git_revert_response`

Confirms the result of a git revert operation. Supports responses for both single file and bulk operations.

**Event Fields:**

*   `project_id` (string, mandatory): The project ID the operation was performed on.
*   `file_path` (string, optional): The path to the file that was reverted (for single file operations).
*   `file_paths` (array of strings, optional): Array of paths to files that were reverted (for bulk operations).
*   `revert_all` (boolean, optional): Present if the operation was a "revert all" operation.
*   `success` (boolean, mandatory): Whether the revert operation was successful.
*   `error` (string, optional): Error message if the operation failed.

### <a name="project_state_git_commit_response"></a>`project_state_git_commit_response`

Confirms the result of a git commit operation.

**Event Fields:**

*   `project_id` (string, mandatory): The project ID the operation was performed on.
*   `commit_message` (string, mandatory): The commit message that was used.
*   `success` (boolean, mandatory): Whether the commit operation was successful.
*   `error` (string, optional): Error message if the operation failed.
*   `commit_hash` (string, optional): The SHA hash of the new commit if successful.

### Client Session Events

### <a name="request_client_sessions"></a>`request_client_sessions`

Sent by the device to request the current list of connected client sessions from the server. This is an internal event used during device initialization and reconnection.

**Event Fields:**

This event carries no additional fields.

### Terminal Data

### Terminal I/O Data Formats

Terminal I/O data can be sent in two formats depending on the implementation:

#### Modern Format (Recommended)

Terminal data is sent as a proper [`terminal_data`](#terminal_data) event on the control channel (channel 0) with client session targeting support:

```json
{
  "channel": 0,
  "payload": {
    "event": "terminal_data",
    "channel": "<terminal_uuid>",
    "data": "<terminal_output_string>",
    "device_id": 123,
    "project_id": "<project_uuid>",
    "client_sessions": ["channel.abc123", "channel.def456"]
  }
}
```

This format follows the standard event structure with automatic system field injection (device_id, project_id, client_sessions) for proper routing and security.

#### Legacy Format (Deprecated)

Terminal data sent directly on terminal channels (not on the control channel):

```json
{
  "channel": "<terminal_uuid>",
  "payload": "<terminal_output_string>"
}
```

*   Terminal output is sent as raw string data in the payload
*   Input to terminals is sent the same way but in the opposite direction  
*   No event wrapper or client targeting is used
*   This format broadcasts to all sessions for the device owner

### Server-Side Events

### <a name="device_status"></a>`device_status`

Sent by the server to clients to indicate device online/offline status changes.

**Event Fields:**

*   `device` (object, mandatory): Device status information
  *   `id` (integer, mandatory): Device ID
  *   `online` (boolean, mandatory): Whether the device is online

### <a name="devices"></a>`devices`

Sent by the server to clients to provide initial device list snapshot.

**Event Fields:**

*   `devices` (array, mandatory): Array of device objects with status information