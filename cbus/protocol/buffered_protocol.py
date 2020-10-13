#!/usr/bin/env python
# cbus/protocol/buffered_protocol.py
# Buffered protocol receiver for asyncio
# Copyright 2019 Michael Farrell <micolous+git@gmail.com>
#
# This library is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.

import abc
import asyncio
import threading
import warnings


__all__ = ['BufferedProtocol', 'BufferedProtocolWarning']


class BufferedProtocolWarning(RuntimeWarning):
    pass


class BufferedProtocol(asyncio.Protocol, abc.ABC):
    """
    A generic buffered Protocol for asyncio.

    """
    def __init__(self, size_limit=1024):
        self._buf = bytearray()
        self._buf_lock = threading.Lock()
        self._size_limit = size_limit

    @abc.abstractmethod
    def handle_data(self, buf: bytes) -> int:
        """
        Called when there is data to process.

        ``buf`` contains the entire buffer.

        Return values are interpreted as follows:

        ``r > 0``
            ``r`` bytes were consumed from the buffer. This method will be
            called again, immediately.
        ``r == 0``
            There is no complete message to interpret in the buffer, and this
            should not be called again until more data is in the buffer.
        ``r == -1``
            The buffer will be deleted.

        Return values less than ``-1`` are invalid, and will cause
        ``_process_buffer`` to raise an exception.

        :param buf: Receive buffer
        :type buf: bytes
        """
        raise NotImplementedError('frame_received')

    def data_received(self, data: bytes) -> None:
        """
        Adds new data to the buffer, and then starts processing it.

        If the data is larger than the buffer size limit, the data will be
        dropped and a BufferedProtocolWarning raised.

        If the data would cause the buffer to exceed the size limit, the data
        and existing buffer will be dropped, and a BufferedProtocolWarning
        raised.

        :param data: new data to add to the buffer
        :return: None
        """
        data_size = len(data)
        if data_size > self._size_limit:
            warnings.warn(f'Received {data_size} bytes > size limit of '
                          f'{self._size_limit} bytes, data dropped!',
                          BufferedProtocolWarning)
            return

        # Add the data to the buffer
        with self._buf_lock:
            buf_size = len(self._buf)
            if buf_size + data_size > self._size_limit:
                self._buf = bytearray()
                warnings.warn(
                    f'Received {data_size} bytes + {buf_size} bytes already '
                    f'in buffer > size limit of {self._size_limit} bytes, '
                    f'buffer dropped!', BufferedProtocolWarning)
                return

            self._buf.extend(data)

        # Handle any messages that may be in the buffer.
        self._process_buffer()

    def _process_buffer(self):
        with self._buf_lock:
            while True:
                if len(self._buf) == 0:
                    break

                # TODO: replace with non-copy architecture
                r = self.handle_data(bytes(self._buf))

                if r < 0:
                    # < 0, clear buffer
                    self._buf = bytearray()

                    if r != -1:
                        # Only "correct" way to clear buffer is with -1.
                        # But we clear anyway to avoid loops.
                        raise ValueError(
                            f'Invalid return from frame_received: {r}')

                if r > 0:
                    self._buf = self._buf[r:]
                else:
                    break
