# Lab 2 — Group Signing Challenge

Lab 2 implements a three-member IPv8 client that registers a group with the grading server and completes multi-round ECDSA-style signing challenges. Each member runs their own node; signatures are exchanged peer-to-peer and aggregated before submission.

## Overview

The workflow is a state machine shared across three peers:

1. **Find peers** — Discover the grading server and the other two group members on the `HetCommunity` overlay.
2. **Register** — Submit the three members' public keys to the server and receive a `group_id`.
3. **Ready** — Exchange ready messages so all nodes start the challenge together.
4. **Challenge rounds** — The server sends a nonce per round; each member signs it with their Lab 1 private key.
5. **Aggregate** — Signatures are gossiped via `InternalSubmissionPayload` until all three slots are filled.
6. **Submit** — The combined submission is sent to the server; on success the client enters the `SUCCESS` state.

The `group_id` from registration is used again in Lab 3.

## Requirements

- Python 3.12–3.13
- Dependencies in `pyproject.toml` (`pyipv8>=3.2.0`, `cryptography<42`, `libnacl`, `python-dotenv`)
- Three team members, each with a Lab 1 private key
- Optional: [uv](https://docs.astral.sh/uv/)

## Installation

From the `lab2/` directory:

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

### 1. Private keys

Each member needs their Lab 1 key file in the `lab2/` directory:

| Member | Key file | `--node-id` |
|--------|----------|-------------|
| Member 0 | `lab1_key_0.pem` | `0` |
| Member 1 | `lab1_key_1.pem` | `1` |
| Member 2 | `lab1_key_2.pem` | `2` |

The `--node-id` must match the member's index in `PUBLIC_KEYS` and the corresponding signature slot (`sig1`, `sig2`, `sig3`).

### 2. Environment file

Create a `.env` file in `lab2/` with the hex-encoded public keys of all three members, in order:

```env
PUBLIC_KEYS=["<hex_pubkey_member_0>","<hex_pubkey_member_1>","<hex_pubkey_member_2>"]
```

All three nodes must use the **same** `PUBLIC_KEYS` value. The order must match each member's `--node-id`.

## Running

Each team member runs their own terminal from `lab2/`:

**Member 0:**

```bash
uv run python main.py --node-id 0
```

**Member 1:**

```bash
uv run python main.py --node-id 1
```

**Member 2:**

```bash
uv run python main.py --node-id 2
```

Start all three nodes around the same time so they can find each other and the server on the overlay.

## State machine

```
FIND_PEERS → REGISTER → READY → BEGIN_CHALLENGE ⇄ BEGIN_ROUND ⇄ ROUND → SUCCESS
```

| State | Behavior |
|-------|----------|
| `FIND_PEERS` | Locate server (`SERVER_PUBLIC_KEY`) and both teammates (`PUBLIC_KEYS`). |
| `REGISTER` | Send `RegisterPayload` with all three member keys; store returned `group_id`. |
| `READY` | Broadcast `ReadyPayload` to teammates; proceed when both have acknowledged. |
| `BEGIN_CHALLENGE` | Request the next challenge from the server. |
| `BEGIN_ROUND` | Sign the challenge nonce locally and forward partial submission to peers. |
| `ROUND` | Merge incoming signatures; rebroadcast or submit to server when complete. |
| `SUCCESS` | All required rounds completed successfully. |

## Expected output

While running you should see state transitions and submission logs, for example:

```
IPv8 started, searching for peer
Current state: State.FIND_PEERS
...
Current state: State.REGISTER
...
Sending to boss: SubmissionPayload(...)
Submission response: ...
Success state
```

Save the **`group_id`** from a successful run; Lab 3 requires it via the `GROUP_ID` environment variable.

## Troubleshooting

- **Stuck in `FIND_PEERS`** — Ensure all three nodes are running and connected to the IPv8 network; verify `PUBLIC_KEYS` matches the actual keys in the `.pem` files.
- **Registration fails** — Check that public keys are correct, in the right order, and that the server is reachable.
- **Signatures never complete** — Confirm each member uses a unique `--node-id` and the correct `lab1_key_{id}.pem`.
- **Wrong key file** — `KEY_FILE` is set automatically from `--node-id`; do not run two nodes with the same id.

## Relation to other labs

- **Lab 1** — Provides each member's identity key used for signing.
- **Lab 3** — Uses the same keys and the `group_id` from Lab 2 to run a proof-of-work blockchain across the group.
