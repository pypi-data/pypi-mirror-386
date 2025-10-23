import logging
import socket

from stompest.config import StompConfig
from stompest.protocol import StompSpec
from stompest.sync import Stomp

from ...utils.log_utils import basic_config

logger = logging.getLogger("STOMP PUBLISHER")


def read_socket(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    buffer = b""
    try:
        while True:
            buffer += sock.recv(16384)
            if buffer:
                out, sep, buffer = buffer.rpartition(b"\n")
                if sep:
                    for bdata in out.split(b"\n"):
                        yield bdata
    finally:
        sock.close()


def main(host=None, port=60001, queue=None, port_in=0):
    if not host:
        host = "localhost"
    if not queue:
        queue = "/queue/icatIngest"

    queue_urls = [f"{host}:{port}"]
    cfg_url = "failover:(tcp://" + ",tcp://".join(queue_urls) + ")"
    cfg_url += (
        "?maxReconnectAttempts=3,initialReconnectDelay=250,maxReconnectDelay=1000"
    )
    client = Stomp(StompConfig(cfg_url, version=StompSpec.VERSION_1_1))
    client.connect(
        versions=[StompSpec.VERSION_1_1], heartBeats=(0, 0), connectedTimeout=1
    )
    header = {
        "persistent": "true",
        StompSpec.ACK_HEADER: StompSpec.ACK_CLIENT_INDIVIDUAL,
    }
    if port_in:
        for body in read_socket("localhost", port_in):
            client.send(queue, body=body, headers=header)
    else:
        while True:
            body = input(f"Message to send to '{queue}': ")
            client.send(queue, body=body.encode(), headers=header)


if __name__ == "__main__":
    import argparse

    basic_config(
        logger=logger,
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="Redirect socket input to a STOMP queue"
    )
    parser.add_argument(
        "--host", default="localhost", type=str, help="STOMP server host"
    )
    parser.add_argument("--port", default=60001, type=int, help="STOMP server port")
    parser.add_argument(
        "--queue", default="/queue/icatIngest", type=str, help="STOMP queue"
    )
    parser.add_argument("--port_in", default=0, type=int, help="input socket")
    args = parser.parse_args()

    main(host=args.host, port=args.port, port_in=args.port_in, queue=args.queue)
