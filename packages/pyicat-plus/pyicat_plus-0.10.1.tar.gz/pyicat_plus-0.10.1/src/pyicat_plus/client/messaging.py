import base64
from typing import List
from typing import Optional

import requests
from stompest.config import StompConfig
from stompest.error import StompConnectionError
from stompest.protocol import StompSession
from stompest.protocol import StompSpec
from stompest.sync import Stomp

from ..utils.url import normalize_url


class IcatMessagingClient:
    """Client for the ICAT message broker.

    The message broker is currently ActiveMQ, a message
    broker using the STOMP protocol. It also has a REST
    server for monitoring the broker status.
    """

    DEFAULT_SCHEME = "tcp"
    DEFAULT_PORT = 61613
    MONITOR_SCHEME = "http"
    DEFAULT_MONITOR_PORT = 8778
    MONITOR_USER = "user"
    MONITOR_PWD = "user"

    def __init__(
        self,
        queue_urls: List[str],
        queue_name: str,
        monitor_port: Optional[int] = None,
        timeout: Optional[float] = None,
    ):
        urls = [
            normalize_url(
                url, default_scheme=self.DEFAULT_SCHEME, default_port=self.DEFAULT_PORT
            )
            for url in queue_urls
        ]
        failover = ",".join(urls)
        url = f"failover:({failover})?maxReconnectAttempts=3,initialReconnectDelay=250,maxReconnectDelay=1000"
        self.__max_version = StompSpec.VERSION_1_1
        self.__client = Stomp(StompConfig(url, version=self.__max_version))
        self._socket_timeout = None
        if timeout is None:
            timeout = 1
        self._connect_timeout = timeout

        self.__send_destination = "/queue/" + queue_name
        self.__send_headers = {
            "persistent": "true",
            StompSpec.ACK_HEADER: StompSpec.ACK_CLIENT_INDIVIDUAL,
        }

        if not monitor_port:
            monitor_port = self.DEFAULT_MONITOR_PORT
        self.__consumer_count_url = f"{self.MONITOR_SCHEME}://{{host}}:{monitor_port}/api/jolokia/read/org.apache.activemq:type=Broker,brokerName=metadata,destinationType=Queue,destinationName={queue_name}/ConsumerCount"
        self.__jolokia_headers = {
            "Authorization": b"Basic "
            + base64.b64encode(f"{self.MONITOR_USER}:{self.MONITOR_PWD}".encode())
        }

    def reconnect(self):
        self.disconnect()
        self._connect()

    def disconnect(self):
        try:
            self.__client.disconnect()
        except StompConnectionError:
            self.__client.close(flush=True)

    def _connect(self):
        self.__client.connect(
            versions=[self.__max_version],
            connectTimeout=self._socket_timeout,
            connectedTimeout=self._connect_timeout,
        )

    @property
    def _connected_client(self):
        if self.__client.session.state != StompSession.CONNECTED:
            self._connect()
        return self.__client

    @property
    def _host(self):
        return self._connected_client._transport.host

    def send(self, data: bytes):
        try:
            self._send(data)
        except StompConnectionError:
            self.reconnect()
            self._send(data)

    def _send(self, data: bytes):
        self._connected_client.send(
            self.__send_destination, body=data, headers=self.__send_headers
        )

    @property
    def _consumer_count(self):
        url = self.__consumer_count_url.format(host=self._host)
        response = requests.get(url, headers=self.__jolokia_headers)
        if not response.ok:
            raise RuntimeError(
                response, "Failed to retrieve the ActiveMQ consumer count"
            )
        response = response.json()
        return response["value"]

    def check_health(self):
        """Raises an exception when:
        - not connected
        - no message consumers
        """
        state = self._connected_client.session.state
        if state != StompSession.CONNECTED:
            raise RuntimeError(
                "The connection with the message broker is " + str(state).upper()
            )
        if self._consumer_count < 1:
            raise RuntimeError("The message broker has no consumers")
