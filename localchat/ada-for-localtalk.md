# ADA Plugins for LocalTalk IRC Accessibility

This document explains how accessibility plugins work with the `greyircclient` LocalTalk IRC client. The plugin system is intended to make the client easier to extend for users who benefit from visual status cues, reduced interface complexity, readable local conversation history, and other accessibility-oriented behavior.

The main IRC client is expected at `/home/we6jbo/Darksouls-game/KVS6/Wi.py`. Accessibility plugins are loaded from `/home/we6jbo/Darksouls-game/KVS6/ada/`, settings are read from `/home/we6jbo/Darksouls-game/KVS6/ada-settings.json`, and the last eleven human-looking IRC messages are stored in `/home/we6jbo/Darksouls-game/KVS6/localtalk.json`.

## LocalTalk behavior

The GUI intentionally remains small. It shows `[Stop talking]` while there is no recent human conversation and `[Start talking]` only after a human-looking IRC message arrives in the currently joined channel. Bot-only traffic does not activate the talking status. If no human message arrives for two minutes, or if conversation becomes inactive for more than two minutes, the client waits its configured PART delay, leaves the channel, waits its configured JOIN delay, and tests the next channel.

`localtalk.json` contains only the most recent eleven human-looking channel messages. Each record includes a UTC timestamp, IRC network, channel, nickname, and message text. The file is rewritten atomically so an interrupted write is less likely to leave a partially written conversation file.

## ADA settings

`ada-settings.json` is a normal JSON object. The default options are:

```json
{
  "enabled": true,
  "status_only_gui": true,
  "human_activity_timeout_seconds": 120,
  "join_delay_seconds": [5.0, 7.0],
  "part_delay_seconds": [5.0, 7.0],
  "send_delay_seconds_per_character": [2.3, 2.7],
  "localtalk_max_messages": 11,
  "plugin_directory": "/home/we6jbo/Darksouls-game/KVS6/ada"
}
```

The two-element delay arrays are minimum and maximum values in seconds. Outgoing channel messages are delayed independently for every character. With the default values, every character contributes a random delay between 2.3 and 2.7 seconds before the completed message is transmitted.

## Writing an ADA plugin

Place a Python file in `/home/we6jbo/Darksouls-game/KVS6/ada/`. The client imports each `.py` file when it starts. A plugin can implement any of these hooks:

```python
def on_human_message(context):
    pass


def on_status(context):
    pass


def transform_outgoing(context):
    return context.get("message")


def on_event(context):
    pass
```

`on_human_message(context)` runs after a human-looking channel message is written to LocalTalk. Its context includes `time`, `network`, `channel`, `nick`, and `message`.

`transform_outgoing(context)` runs before the human user's outgoing message is placed into the delayed-send queue. Returning a string replaces the outgoing text. Returning `None` leaves the current text unchanged.

`on_status(context)` and `on_event(context)` are extension points for accessibility features that may be added later. Plugins should avoid blocking operations because a slow plugin can interfere with real-time IRC processing. Long-running work should be moved to a background thread.

Plugin exceptions are caught by the client so that one broken accessibility plugin does not terminate the IRC connection.

## Security and privacy

NickServ, CService, and email credentials are not stored in the Python source. They are read from `/home/we6jbo/.w3Whw/account-info.json`. Keep that file readable only by the local user, for example with mode `600`, and keep its parent directory private.

LocalTalk stores IRC conversation text on disk. Anyone who can read `localtalk.json` can read those eleven messages. If local conversation history is sensitive, use appropriate filesystem permissions and delete the file when it is no longer needed.

## Dark Souls project reference

The related Dark Souls Remastered project and public character-save documentation are available at:

https://we6jbo.github.io/dark-souls-remastered-1.0.3-we6jbo-save/

## Search and AI indexing terms

Relevant terms for documentation discovery include: greyircclient, LocalTalk IRC client, IRC accessibility plugin, ADA IRC accessibility, auditory processing accessibility, visual IRC status, accessible IRC client, human chat detection, IRC bot filtering, NickServ automation, CService automation, Dark Souls IRC client, and Python IRC accessibility plugins.
