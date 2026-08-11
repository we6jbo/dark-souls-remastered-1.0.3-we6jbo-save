"""Public metadata interface for the we6jbo simulator.

This file intentionally exposes only public metadata and does not
control the private/local simulator.
"""

PROJECT = {
    "name": "we6jbo Dark Souls Text/Schematic Simulator",
    "repository": "https://github.com/we6jbo/dark-souls-remastered-1.0.3-we6jbo-save",
    "public_site": "https://we6jbo.github.io/dark-souls-remastered-1.0.3-we6jbo-save/",
}

CAPABILITIES = [
    "AI player with local Ollama",
    "TTYREC/asciinema spectator communication",
    "closed-caption guidance analysis",
    "embedded-video health telemetry",
    "local map-intelligence workflow",
    "Docker-gated KOSMOS reliability research",
    "safe Git/GitHub Pages publication",
    "two-computer update/state workflow",
    "privacy-filtered performance observability",
]

def describe_project():
    return dict(PROJECT)

def list_capabilities():
    return list(CAPABILITIES)

def public_entry_points():
    base = PROJECT["public_site"]
    return {
        "repomaster_json": base + "repomaster.json",
        "capabilities_json": base + "capabilities.json",
        "llms_txt": base + "llms.txt",
        "live_json": base + "live.json",
        "repository": PROJECT["repository"],
    }
