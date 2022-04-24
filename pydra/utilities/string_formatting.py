from pydra.core.messages.serializers import deserialize_string


__all__ = ["format_zmq_connections"]


def format_zmq_connections(connections):
    header = "\n".join(["=" * len("connections"), "connections".upper(), "=" * len("connections"), ""])
    parts = [header]
    for key, vals in connections.items():
        parts.append(key)
        parts.append("-" * len(key))
        parts.append(f"Publisher: {vals.get('publisher')}")
        parts.append(f"Sender: {vals.get('sender')}")
        parts.append(f"Receiver: {vals.get('receiver')}")
        if "subscriptions" in vals.keys():
            parts.append("Subscriptions:")
            for (name, port, subs) in vals["subscriptions"]:
                parts.append(f"\t{name} - {port} - {tuple([deserialize_string(sub.flag) for sub in subs])}")
        parts.append("")
    return "\n".join(parts)
