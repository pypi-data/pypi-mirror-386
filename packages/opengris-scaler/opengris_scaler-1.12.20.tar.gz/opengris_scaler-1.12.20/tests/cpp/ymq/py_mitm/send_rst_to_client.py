"""
This MITM inserts an unexpected TCP RST
"""

from typing import Optional

from tests.cpp.ymq.py_mitm.types import IP, TCP, AbstractMITM, TCPConnection, TunTapInterface


class MITM(AbstractMITM):
    def __init__(self):
        # count the number of psh-acks sent by the client
        self._client_pshack_counter = 0

    def proxy(
        self,
        tuntap: TunTapInterface,
        pkt: IP,
        sender: TCPConnection,
        client_conn: Optional[TCPConnection],
        server_conn: TCPConnection,
    ) -> bool:
        if sender == client_conn or client_conn is None:
            if pkt[TCP].flags == "PA":
                self._client_pshack_counter += 1

                # on the second psh-ack, send a rst instead
                if self._client_pshack_counter == 2:
                    rst_pkt = IP(src=client_conn.local_ip, dst=client_conn.remote_ip) / TCP(
                        sport=client_conn.local_port, dport=client_conn.remote_port, flags="R", seq=pkt[TCP].ack
                    )
                    print(f"<- [{rst_pkt[TCP].flags}] (simulated)")
                    tuntap.send(rst_pkt)
                    return False

            tuntap.send(server_conn.rewrite(pkt))
        elif sender == server_conn:
            tuntap.send(client_conn.rewrite(pkt))
        return True
