# Lab 1 — Proof-of-Work Client

Lab 1 is a standalone IPv8 client that mines a nonce and submits your identity to the grading server over the `LabCommunity` overlay.

## Overview

The client:

1. Mines a nonce such that `SHA-256(email + "\n" + github_url + "\n" + nonce)` has **28 leading zero bits** (7 zero bytes with the high nibble of the 8th byte also zero).
2. Starts an IPv8 node and joins the lab overlay.
3. Discovers the grading server by its fixed public key.
4. Sends a `SubmissionPayload` containing your email, GitHub URL, and the mined nonce.

On success, the server responds with a `ResponsePayload` printed to the console.

## Requirements

- Python 3.10+
- Dependencies in `pyproject.toml` (`pyipv8`, `cryptography<46`)
- Optional: [uv](https://docs.astral.sh/uv/) for dependency management

## Installation

From the `lab1/` directory:

**Using uv:**

```bash
uv sync
```

**Using pip:**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Configuration

Before running, set your details in `main.py`:

- `EMAIL` — your student email
- `GITHUB_URL` — URL to this repository

The client uses a Curve25519 identity key stored in `ec_multichain.pem`. Generate one with IPv8's key tooling if you do not already have it, and place it in the `lab1/` directory (or update the path in `build_ipv8_config()`).

## Running

**Using uv:**

```bash
uv run python main.py
```

**Using Python directly:**

```bash
python main.py
```

The program first mines the nonce (this can take a while), then starts IPv8 and submits to the server. Mining progress is printed every 25 million attempts.

## How it works

| Step | Description |
|------|-------------|
| Mining | Concatenates your message with an 8-byte big-endian nonce and checks SHA-256 until the hash meets the difficulty target. |
| Networking | Joins `LabCommunity` via random walk and IPv8 bootstrap nodes. |
| Discovery | Waits until a peer matches the hard-coded server public key. |
| Submission | Sends `SubmissionPayload(email, github_url, nonce)` to the server. |

## Output

You should see logs similar to:

```
Start mining nonce...
Found nonce: <number>
Hash: <hex>
Community started
Server peer found: ('x.x.x.x', port)
Response from ...: True <message>
```

## Notes

- Keep `ec_multichain.pem` private; do not commit it.
- The private key from Lab 1 is reused in later labs (Lab 2 group signing, Lab 3 blockchain mining).
