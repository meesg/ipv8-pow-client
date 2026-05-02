import asyncio
from dataclasses import dataclass

from ipv8.community import Community, CommunitySettings
from ipv8.configuration import ConfigBuilder, Strategy, WalkerDefinition, default_bootstrap_defs
from ipv8.lazy_community import lazy_wrapper
from ipv8.messaging.payload_dataclass import DataClassPayload
from ipv8.util import run_forever
from ipv8.peer import Peer
from ipv8_service import IPv8
from hashlib import sha256

LAB_COMMUNITY_ID = bytes.fromhex("2c1cc6e35ff484f99ebdfb6108477783c0102881")
LAB_COMMUNITY_NAME = "LabCommunity"
SERVER_PUBLIC_KEY_BIN = bytes.fromhex(
    "4c69624e61434c504b3a86b23934a28d669c390e2d1fc0b0870706c4591cc0cb"
    "178bc5a811da6d87d27ef319b2638ef60cc8d119724f4c53a1ebfad919c3ac4136c501ce5c09364e0ebb"
)

EMAIL = "m.gribnau@student.tudelft.nl"
GITHUB_URL = "https://github.com/meesg/ipv8-pow-client"
MESSAGE = f"{EMAIL}\n{GITHUB_URL}\n"

@dataclass
class SubmissionPayload(DataClassPayload[1]):
    email: str
    github_url: str
    nonce: int

@dataclass
class ResponsePayload(DataClassPayload[2]):
    success: bool
    message: str

# DataClassPayload fills format_list on first __new__; inbound unpack runs before any client
# instantiates ResponsePayload, so register wire formats eagerly.
_ = ResponsePayload(False, "")

class LabCommunity(Community):
    community_id = LAB_COMMUNITY_ID

    def __init__(self, settings: CommunitySettings) -> None:
        super().__init__(settings)
        self.add_message_handler(ResponsePayload, self.on_response)

    @lazy_wrapper(ResponsePayload)
    def on_response(self, peer: Peer, payload: ResponsePayload) -> None:
        print(f"Response from {peer.address}: {payload.success} {payload.message}")

def build_ipv8_config() -> dict:
    builder = ConfigBuilder().clear_keys().clear_overlays()
    builder.add_key("lab identity", "curve25519", "ec_multichain.pem")
    builder.add_overlay(LAB_COMMUNITY_NAME, "lab identity",
                        [WalkerDefinition(Strategy.RandomWalk,
                                            10, {"timeout": 3.0})],
                        default_bootstrap_defs, {}, [])
    return builder.finalize()

async def find_server_peer(overlay: LabCommunity) -> Peer:
    while True:
        print(f"Looking for server peer... {len(overlay.get_peers())} peers found")
        for peer in overlay.get_peers():
            if peer.public_key.key_to_bin() == SERVER_PUBLIC_KEY_BIN:
                return peer
        await asyncio.sleep(3)

async def start_communities(nonce: int) -> None:
    ipv8_config = build_ipv8_config()
    ipv8 = IPv8(ipv8_config, extra_communities={LAB_COMMUNITY_NAME: LabCommunity})

    await ipv8.start()
    print("Community started")

    overlay = ipv8.get_overlay(LabCommunity)
    if overlay is None:
        raise RuntimeError("Lab overlay failed to initialize")
    print("Overlay initialized")
    
    server_peer = await find_server_peer(overlay)
    print(f"Server peer found: {server_peer.address}")

    print(overlay.get_peers())

    overlay.ez_send(server_peer, SubmissionPayload(email=EMAIL, github_url=GITHUB_URL, nonce=nonce))

    await run_forever()

def has_28_leading_zero_bits(hash_bytes: bytes) -> bool:
    return (
        len(hash_bytes) >= 4
        and hash_bytes[0] == 0
        and hash_bytes[1] == 0
        and hash_bytes[2] == 0
        and (hash_bytes[3] >> 4) == 0
    )

def mine_nonce() -> int:
    nonce = 0
    print("Start mining nonce...")
    while True:
        data = MESSAGE.encode("utf-8") + nonce.to_bytes(8, "big", signed=False)
        h = sha256(data).digest()

        if nonce % 25_000_000 == 0 and nonce > 0:
            print(f"Mined {nonce} nonces...")

        if has_28_leading_zero_bits(h):
            print("Found nonce:", nonce)
            print("Hash:", h.hex())
            break

        nonce += 1
    return nonce 

if __name__ == "__main__":
    nonce = mine_nonce()
    asyncio.run(start_communities(nonce))