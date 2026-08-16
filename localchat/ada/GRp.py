"""Example ADA plugin for greyircclient localtalk automation."""

def on_human_message(context):
    """Called after a human-looking IRC message is saved to localtalk.json."""
    return None


def on_status(context):
    """Optional hook for accessibility status changes."""
    return None


def transform_outgoing(context):
    """Return a replacement outgoing message, or None to leave it unchanged."""
    return context.get("message")


def on_event(context):
    """Optional generic event hook reserved for future extensions."""
    return None
