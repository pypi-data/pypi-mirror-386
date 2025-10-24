import uuid, concurrent.futures, asyncio
from typing import Callable, Iterable, overload, Literal
from collections import OrderedDict

class Receiver:
    __slots__ = ('_key', 'fn', 'runType', '_receiveNum_expected', 'autoRemove', '_receiveNum')

    def __init__(self, fn: Callable, key: str | None = None, *, runType: Literal['SEQUENTIAL', 'PARALLEL', 'NO_BLOCK'] = 'SEQUENTIAL', receiveNum_expected: int = 0, autoRemove: bool = False):
        '''
        - Args
            - fn: 接收函数
            - key: 若不设置则自动生成一个uuid格式的字符串
            - runType: 运行方式
                - SEQUENTIAL: 顺序执行，等待函数执行完成后再执行下一个函数
                - PARALLEL: 并行执行，等待所有函数执行完成后再继续
                - NO_BLOCK: 非阻塞执行，函数在后台执行，不等待函数执行完成
            - receiveNum_expected: 期望接收总数
            - autoRemove: 是否在达到期望接收总数后自动移除接收器
        '''

        self._key: str = key or str(uuid.uuid4())
        self.fn: Callable = fn
        self.runType: Literal['SEQUENTIAL', 'PARALLEL', 'NO_BLOCK'] = runType
        '''
        运行方式
        - SEQUENTIAL: 顺序执行，等待函数执行完成后再执行下一个函数
        - PARALLEL: 并行执行，等待所有函数执行完成后再继续
        - NO_BLOCK: 非阻塞执行，函数在后台执行，不等待函数执行完成
        '''
        self._receiveNum_expected: int = receiveNum_expected
        ''' 期望接收总数 '''
        self.autoRemove: bool = autoRemove
        ''' 是否在达到期望接收总数后自动移除接收器 '''

        self._receiveNum: int = 0
        ''' 接收总数 '''

    def reset(self):
        ''' 重置统计数据 '''

        self._receiveNum = 0

    @property
    def key(self) -> str:
        return self._key

    @property
    def receiveNum(self) -> int:
        ''' 接收总数 '''

        return self._receiveNum

    @property
    def receiveNum_expected(self) -> int:
        ''' 期望接收总数 '''

        return self._receiveNum_expected

    @property
    def receiveNum_remaining(self) -> int | None:
        ''' 剩余接收总数 '''

        return self._receiveNum_expected - self._receiveNum if self._receiveNum_expected > 0 else None

    @property
    def is_active(self) -> bool:
        ''' 是否处于激活状态 '''

        return self._receiveNum_expected == 0 or self.receiveNum_remaining > 0

class Signal:
    __slots__ = ('receivers', '_sendNum')

    def __init__(self):
        '''
        - Examples
```python
""" 基础用法 """
from CheeseSignal import Signal

signal = Signal()

def handle_1():
    print('Handler 1 executed')
signal.connect(handle_1)

@signal.connect()
def handle_2():
    print('Handler 2 executed')

if __name__ == '__main__':
    signal.send()


""" 异步用法 """
import asyncio

from CheeseSignal import Signal

signal = Signal()

async def handle_1():
    print('Handler 1 executed')
signal.connect(handle_1)

@signal.connect()
async def handle_2():
    print('Handler 2 executed')

if __name__ == '__main__':
    asyncio.run(signal.async_send())


""" 期望接收数与自动删除 """
from CheeseSignal import Signal

signal = Signal()

@signal.connect(receiveNum_expected = 3)
def handle_1():
    print('Handler 1 executed')

@signal.connect(receiveNum_expected = 3, autoRemove = True)
def handle_2():
    print('Handler 2 executed')

if __name__ == '__main__':
    for i in range(5):
        signal.send()
        print(list(signal.receivers.keys()))
```
'''

        self.receivers: OrderedDict[str, Receiver] = OrderedDict()
        ''' 连接的接收器'''
        self._sendNum: int = 0
        ''' 发送总数 '''

    @overload
    def getReceiver(self, key: str) -> Receiver | None:
        ''' 获取接收器 '''

    @overload
    def getReceiver(self, fn: Callable) -> Receiver | None:
        ''' 获取接收器 '''

    def getReceiver(self, arg: str | Callable) -> Receiver | None:
        if type(arg) == str:
            return self.receivers.get(arg, None)
        elif callable(arg):
            for receiver in self.receivers.values():
                if receiver.fn == arg:
                    return receiver

    def _connect(self, fn: Callable, key: str | None = None, *, index: int = -1, insert: tuple[str | Callable | Receiver, Literal['BEFORE', 'AFTER']] | None = None, runType: Literal['SEQUENTIAL', 'PARALLEL', 'NO_BLOCK'] = 'SEQUENTIAL', receiveNum_expected: int = 0, autoRemove: bool = False):
        if key in self.receivers:
            raise ValueError(f'Receiver "{key}" already exists')

        receiver = Receiver(fn, key, runType = runType, receiveNum_expected = receiveNum_expected, autoRemove = autoRemove)
        items = list(self.receivers.items())
        if index > -1:
            items.insert(index, (receiver.key, receiver))
            self.receivers.clear()
            self.receivers.update(items)
        elif insert:
            if isinstance(insert[0], Receiver):
                key = insert[0].key
                if key not in self.receivers:
                    raise ValueError(f'Receiver "{key}" does not exist')
            elif callable(insert[0]):
                _receiver = self.getReceiver(insert[0])
                if not _receiver:
                    raise ValueError(f'Receiver "{insert[0]}" does not exist')
                key = _receiver.key
            elif isinstance(insert[0], str):
                key = insert[0]
                if key not in self.receivers:
                    raise ValueError(f'Receiver "{key}" does not exist')

            for i, (_key, _) in enumerate(items):
                if _key == key:
                    if insert[1] == 'BEFORE':
                        items.insert(i, (receiver.key, receiver))
                    elif insert[1] == 'AFTER':
                        items.insert(i + 1, (receiver.key, receiver))
                    break
        else:
            self.receivers[receiver.key] = receiver

    @overload
    def connect(self, fn: Callable, key: str | None = None, *, index: int = -1, insert: tuple[str | Callable | Receiver, Literal['BEFORE', 'AFTER']] | None = None, runType: Literal['SEQUENTIAL', 'PARALLEL', 'NO_BLOCK'] = 'SEQUENTIAL', receiveNum_expected: int = 0, autoRemove: bool = False):
        '''
        连接接收器

        - Args
            - key: 接收器键值，若不设置则自动生成一个uuid格式的字符串
            - runType: 运行类型
                - SEQUENTIAL: 顺序执行，等待函数执行完成后再执行下一个函数
                - PARALLEL: 并行执行，等待所有函数执行完成后再继续
                - NO_BLOCK: 非阻塞执行，函数在后台执行，不等待函数执行完成
            - receiveNum_expected: 期望接收总数
            - autoRemove: 是否在达到期望接收总数后自动移除接收器
            - index: 插入位置索引（仅对runType为SEQUENTIAL的接收器有效）
            - insert: 插入位置；若设置index，则忽略此参数（仅对runType为SEQUENTIAL的接收器有效）
                - BEFORE: 插入到指定接收器之前
                - AFTER: 插入到指定接收器之后

        - Examples
```python
from CheeseSignal import Signal

signal = Signal()

def handler():
    print('Handler executed')
signal.connect(handler)
```
        '''

    @overload
    def connect(self, key: str | None = None, *, index: int = -1, insert: tuple[str | Callable | Receiver, Literal['BEFORE', 'AFTER']] | None = None, runType: Literal['SEQUENTIAL', 'PARALLEL', 'NO_BLOCK'] = 'SEQUENTIAL', receiveNum_expected: int = 0, autoRemove: bool = False):
        '''
        连接接收器

        - Args
            - key: 接收器键值，若不设置则自动生成一个uuid格式的字符串
            - runType: 运行类型
                - SEQUENTIAL: 顺序执行，等待函数执行完成后再执行下一个函数
                - PARALLEL: 并行执行，等待所有函数执行完成后再继续
                - NO_BLOCK: 非阻塞执行，函数在后台执行，不等待函数执行完成
            - receiveNum_expected: 期望接收总数
            - autoRemove: 是否在达到期望接收总数后自动移除接收器
            - index: 插入位置索引（仅对runType为SEQUENTIAL的接收器有效）
            - insert: 插入位置；若设置index，则忽略此参数（仅对runType为SEQUENTIAL的接收器有效）
                - BEFORE: 插入到指定接收器之前
                - AFTER: 插入到指定接收器之后

        - Examples
```python
from CheeseSignal import Signal

signal = Signal()

@signal.connect()
def handler():
    print('Handler executed')
```
        '''

    def connect(self, arg1: Callable | str | None = None, *args, index: int = -1, insert: tuple[str | Callable | Receiver, Literal['BEFORE', 'AFTER']] | None = None, runType: Literal['SEQUENTIAL', 'PARALLEL', 'NO_BLOCK'] = 'SEQUENTIAL', receiveNum_expected: int = 0, autoRemove: bool = False):
        def decorator(fn: Callable):
            self._connect(fn, arg1, index = index, insert = insert, runType = runType, receiveNum_expected = receiveNum_expected, autoRemove = autoRemove)
            return fn

        if callable(arg1):
            self._connect(arg1, *args, index = index, insert = insert, runType = runType, receiveNum_expected = receiveNum_expected, autoRemove = autoRemove)
        else:
            return decorator

    @overload
    def disconnect(self, key: str):
        ''' 断开接收器 '''

    @overload
    def disconnect(self, fn: Callable):
        ''' 断开接收器 '''

    @overload
    def disconnect(self, receiver: Receiver):
        ''' 断开接收器 '''

    def disconnect(self, arg):
        if isinstance(arg, str):
            key = arg
            if key in self.receivers:
                del self.receivers[key]
        elif callable(arg):
            for key in [key for key, receiver in self.receivers.items() if receiver.fn == arg]:
                del self.receivers[key]
        elif isinstance(arg, Receiver):
            if arg.key in self.receivers:
                del self.receivers[arg.key]

    def disconnectAll(self):
        ''' 断开所有接收器 '''

        self.receivers.clear()

    def reset(self):
        ''' 重置统计数据 '''

        self._sendNum = 0
        for receiver in self.receivers.values():
            receiver.reset()

    @overload
    def send(self, key: str, *, args: tuple[any, ...], kwargs: dict[str, any]):
        '''
        发送信号

        - Args
            - args: *args参数
            - kwargs: **kwargs参数
        '''

    @overload
    def send(self, keys: Iterable[str], *, args: tuple[any, ...], kwargs: dict[str, any]):
        '''
        发送信号

        - Args
            - args: *args参数
            - kwargs: **kwargs参数
        '''

    @overload
    def send(self, *, args: tuple[any, ...], kwargs: dict[str, any]):
        '''
        发送信号

        - Args
            - args: *args参数
            - kwargs: **kwargs参数
        '''

    def send(self, arg: str | list[str] | None = None, **kwargs):
        if type(arg) == str:
            self.send([arg], **kwargs)
        elif isinstance(arg, Iterable):
            sequential_receivers = [self.receivers[key] for key in arg if key in self.receivers and self.receivers[key].runType == 'SEQUENTIAL' and self.receivers[key].is_active]
            if sequential_receivers:
                for receiver in sequential_receivers:
                    self._sendHandle(receiver, **kwargs)

            parallel_receivers = [self.receivers[key] for key in arg if key in self.receivers and self.receivers[key].runType == 'PARALLEL' and self.receivers[key].is_active]
            if parallel_receivers:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    concurrent.futures.as_completed([executor.submit(self._sendHandle, receiver, **kwargs) for receiver in parallel_receivers])

            noBlock_receivers = [self.receivers[key] for key in arg if key in self.receivers and self.receivers[key].runType == 'NO_BLOCK' and self.receivers[key].is_active]
            if noBlock_receivers:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    for receiver in noBlock_receivers:
                        executor.submit(self._sendHandle, receiver, **kwargs)
        else:
            self.send(self.receivers.keys(), **kwargs)

    def _sendHandle(self, receiver: Receiver, **kwargs):
        receiver.fn(*kwargs.get('args', ()), **kwargs.get('kwargs', {}))
        receiver._receiveNum += 1
        if receiver.autoRemove and not receiver.is_active:
            self.disconnect(receiver.key)

    @overload
    def async_send(self, key: str, *, args: tuple[any, ...], kwargs: dict[str, any]):
        '''
        发送信号

        - Args
            - args: *args参数
            - kwargs: **kwargs参数
        '''

    @overload
    def async_send(self, keys: Iterable[str], *, args: tuple[any, ...], kwargs: dict[str, any]):
        '''
        发送信号

        - Args
            - args: *args参数
            - kwargs: **kwargs参数
        '''

    @overload
    def async_send(self, *, args: tuple[any, ...], kwargs: dict[str, any]):
        '''
        发送信号

        - Args
            - args: *args参数
            - kwargs: **kwargs参数
        '''

    async def async_send(self, arg: str | list[str] | None = None, **kwargs):
        if type(arg) == str:
            await self.async_send([arg], **kwargs)
        elif isinstance(arg, Iterable):
            sequential_receivers = [self.receivers[key] for key in arg if key in self.receivers and self.receivers[key].runType == 'SEQUENTIAL' and self.receivers[key].is_active]
            if sequential_receivers:
                for receiver in sequential_receivers:
                    await self._async_sendHandle(receiver, **kwargs)

            parallel_receivers = [self.receivers[key] for key in arg if key in self.receivers and self.receivers[key].runType == 'PARALLEL' and self.receivers[key].is_active]
            if parallel_receivers:
                await asyncio.gather(*[asyncio.create_task(self._async_sendHandle(receiver, **kwargs)) for receiver in parallel_receivers])

            noBlock_receivers = [self.receivers[key] for key in arg if key in self.receivers and self.receivers[key].runType == 'NO_BLOCK' and self.receivers[key].is_active]
            if noBlock_receivers:
                for receiver in noBlock_receivers:
                    asyncio.create_task(self._async_sendHandle(receiver, **kwargs))
        else:
            await self.async_send(self.receivers.keys(), **kwargs)

    async def _async_sendHandle(self, receiver: Receiver, **kwargs):
        await receiver.fn(*kwargs.get('args', ()), **kwargs.get('kwargs', {}))
        receiver._receiveNum += 1
        if receiver.autoRemove and receiver.receiveNum_remaining == 0:
            self.disconnect(receiver.key)

    @property
    def sendNum(self) -> int:
        ''' 发送总数 '''

        return self._sendNum
