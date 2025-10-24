"""基本情報技術者試験 科目B Python想定問題 (令和2年度 秋季相当)

ネットワーク機器でのパケット転送を簡易シミュレーションするサンプルです。
固定レートで到着するパケットをキューに蓄積し、優先度の高いパケットから送信します。
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import List, Sequence


@dataclass(order=True)
class Packet:
    priority: int
    arrival_time: int
    payload: str = field(compare=False)


@dataclass
class TransmissionResult:
    time: int
    packet: Packet


def simulate_scheduler(arrivals: Sequence[Packet], link_rate: int) -> List[TransmissionResult]:
    """優先度付きキューを用いてパケット送信順序を決定する。"""

    queue: List[Packet] = []
    results: List[TransmissionResult] = []
    current_time = 0

    for packet in sorted(arrivals, key=lambda p: p.arrival_time):
        while current_time < packet.arrival_time and queue:
            current_time += link_rate
            sent = heapq.heappop(queue)
            results.append(TransmissionResult(time=current_time, packet=sent))
        current_time = max(current_time, packet.arrival_time)
        heapq.heappush(queue, packet)

    while queue:
        current_time += link_rate
        sent = heapq.heappop(queue)
        results.append(TransmissionResult(time=current_time, packet=sent))

    return results


if __name__ == "__main__":  # pragma: no cover - manual study aid
    arrivals = [
        Packet(priority=2, arrival_time=0, payload="INIT"),
        Packet(priority=1, arrival_time=2, payload="ALERT"),
        Packet(priority=3, arrival_time=3, payload="LOG"),
        Packet(priority=1, arrival_time=5, payload="UPDATE"),
    ]
    sent = simulate_scheduler(arrivals, link_rate=2)
    for record in sent:
        packet = record.packet
        print(f"t={record.time}: priority={packet.priority} payload={packet.payload}")
