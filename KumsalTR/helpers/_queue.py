# @The_Team_kumsal tarafından yasal olarak geliştirildi keyifli kullanımlar #kumsalteam
# Copyright (c) 2025 TheHamkerAlone
# Licensed under the MIT License.
# This file is part of KumsalTR


import random
from collections import defaultdict, deque
from typing import Union

from ._dataclass import Media, Track

MediaItem = Union[Media, Track]


class Queue:
    def __init__(self):
        self.queues: dict[int, deque[MediaItem]] = defaultdict(deque)
        # Döngü: 0 = kapalı, -1 = sonsuz, n = kalan tekrar sayısı
        self.loops: dict[int, int] = {}
        # Otomatik oynatma (sıra bitince benzer şarkı) açık olan gruplar
        self.autoplay: set[int] = set()
        # Otomatik oynatmada aynı şarkılar tekrar gelmesin diye son çalınanlar
        self.history: dict[int, deque] = defaultdict(lambda: deque(maxlen=30))

    def toggle_autoplay(self, chat_id: int) -> bool:
        if chat_id in self.autoplay:
            self.autoplay.discard(chat_id)
            return False
        self.autoplay.add(chat_id)
        return True

    def get_loop(self, chat_id: int) -> int:
        return self.loops.get(chat_id, 0)

    def set_loop(self, chat_id: int, count: int) -> None:
        if count:
            self.loops[chat_id] = count
        else:
            self.loops.pop(chat_id, None)

    def use_loop(self, chat_id: int) -> bool:
        """Döngü aktifse bir tekrar harcar ve True döner."""
        count = self.get_loop(chat_id)
        if not count:
            return False
        if count > 0:
            self.set_loop(chat_id, count - 1)
        return True

    def shuffle(self, chat_id: int) -> int:
        """Çalan şarkı hariç sırayı karıştırır, karıştırılan şarkı sayısını döner."""
        items = list(self.queues[chat_id])
        if len(items) < 3:
            return 0
        current, rest = items[0], items[1:]
        random.shuffle(rest)
        self.queues[chat_id] = deque([current] + rest)
        return len(rest)

    def remove_at(self, chat_id: int, pos: int) -> MediaItem | None:
        """Sıradaki şarkıyı numarasıyla siler (1 = sıradaki ilk şarkı)."""
        items = list(self.queues[chat_id])
        if pos < 1 or pos >= len(items):
            return None
        removed = items.pop(pos)
        self.queues[chat_id] = deque(items)
        return removed

    def clear_upcoming(self, chat_id: int) -> int:
        """Çalan şarkıyı bırakıp sıradakilerin hepsini siler."""
        items = list(self.queues[chat_id])
        if len(items) <= 1:
            return 0
        self.queues[chat_id] = deque(items[:1])
        return len(items) - 1

    def add(self, chat_id: int, item: MediaItem) -> int:
        """Add an item to the queue and return its position (1-based)."""
        self.queues[chat_id].append(item)
        self.history[chat_id].append(item.id)
        return len(self.queues[chat_id]) - 1

    def check_item(self, chat_id: int, item_id: str) -> tuple[int, MediaItem | None]:
        """Check if an item with the given ID exists in the queue."""
        pos, track = next(
            (
                (i, track)
                for i, track in enumerate(list(self.queues[chat_id]))
                if track.id == item_id
            ),
            (-1, None),
        )
        return pos, track

    def force_add(
        self, chat_id: int, item: MediaItem, remove: int | bool = False
    ) -> None:
        """Replace the currently playing item with a new one."""
        items = list(self.queues[chat_id])
        if isinstance(remove, int) and 0 <= remove < len(items):
            items.pop(remove)
        if items:
            items.pop(0)
        items.insert(0, item)
        self.queues[chat_id] = deque(items)
        self.history[chat_id].append(item.id)

    def get_current(self, chat_id: int) -> MediaItem | None:
        """Return the currently playing item (first in queue), if any."""
        return self.queues[chat_id][0] if self.queues[chat_id] else None

    def get_next(self, chat_id: int, check: bool = False) -> MediaItem | None:
        """Remove current item and return the next one, or None if empty."""
        if not self.queues[chat_id]:
            return None
        if check:
            return self.queues[chat_id][1] if len(self.queues[chat_id]) > 1 else None

        self.queues[chat_id].popleft()
        return self.queues[chat_id][0] if self.queues[chat_id] else None

    def get_queue(self, chat_id: int) -> list[MediaItem]:
        """Return the full queue including the currently playing item."""
        return list(self.queues[chat_id])

    def remove_current(self, chat_id: int) -> None:
        """Remove the currently playing item only (if exists)."""
        if self.queues[chat_id]:
            self.queues[chat_id].popleft()

    def clear(self, chat_id: int) -> None:
        """Clear the entire queue."""
        self.queues[chat_id].clear()
        self.loops.pop(chat_id, None)
