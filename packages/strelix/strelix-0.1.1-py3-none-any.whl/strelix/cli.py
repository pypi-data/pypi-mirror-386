import click
import requests
import time
import json
import random
from pathlib import Path
from strelix.__version__ import __version__

CONFIG_FILE = Path.home() / ".strelix" / ".strelix.json"
DEFAULT_BASE_URL = "https://hook.strelix.dev"

RANDOM_WORD_LIST = [
    "apple", "banana", "cherry", "dog", "cat", "fish",
    "blue", "red", "green", "sun", "moon", "star", "cloud",
    "sky", "tree", "rock", "river", "bird", "silver", "purple"
]

def load_config():
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}

def save_config(cfg):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))

def generate_subdomain(num_words=3):
    return '-'.join(random.choices(RANDOM_WORD_LIST, k=num_words))

@click.group()
@click.version_option(__version__, prog_name="strelix")
def cli():
    """strelix CLI for webhook forwarding"""
    pass

@cli.command()
@click.option('--subdomain', help="Subdomain to listen on")
@click.option('--port', type=int, help="Local port to forward deliveries to")
@click.option('--base-url', help="Base URL of the webhook server (overrides config)")
@click.version_option(__version__, prog_name="strelix")
def listen(subdomain, port, base_url):
    """
    Listen for deliveries and forward to localhost:<port>
    """
    cfg = load_config()

    if base_url:
        cfg['base_url'] = base_url
    base_url = cfg.get('base_url', DEFAULT_BASE_URL)

    if subdomain:
        cfg['subdomain'] = subdomain
    elif 'subdomain' not in cfg:
        cfg['subdomain'] = generate_subdomain()
        click.echo(f"Auto-generated subdomain: {cfg['subdomain']}")
    subdomain = cfg['subdomain']

    if port:
        cfg['port'] = port
    elif 'port' not in cfg:
        click.echo("Port not set! Use --port to specify the local port to forward to.")
        raise SystemExit(1)
    port = cfg['port']

    save_config(cfg)

    click.echo(f"Listening on subdomain: {subdomain}.hook.strelix.dev -> localhost:{port}")
    click.echo(f"Webhook server: {base_url}\nPress Ctrl+C to stop.\n")

    last_id = None

    while True:
        try:
            params = {}
            if last_id:
                params['since'] = str(last_id)
            r = requests.get(f"{base_url}/api/hooks/{subdomain}/pull/", params=params, timeout=30)
            r.raise_for_status()

            try:
                data = r.json()
            except ValueError:
                data = {"deliveries": []}

            deliveries = data.get('deliveries', [])

            for d in deliveries:
                delivery_id = d['id']
                path = d.get('path', '')
                forward_url = f"http://localhost:{port}/{path}"
                click.echo(f"[{delivery_id}] Forwarding {d['method']} {path} -> {forward_url}")

                try:
                    resp = requests.request(
                        d['method'],
                        forward_url,
                        headers=d.get('headers', {}),
                        data=d.get('body', ''),
                        timeout=15
                    )
                    click.echo(f"  -> Delivered! Status: {resp.status_code}")

                    # mark delivered
                    requests.post(
                        f"{base_url}/api/hooks/{subdomain}/forwarded/",
                        json={"delivery_id": delivery_id}
                    )
                except Exception as e:
                    click.echo(f"  -> Failed to forward: {e}")

                last_id = delivery_id

        except Exception as exc:
            click.echo(f"Polling failed: {exc}")

        time.sleep(2)

def main():
    cli()