# tests/conftest.py
import asyncio
import pytest
from kagura.core.memory import MemoryBackend


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for entire test session"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def cleanup_after_test():
    """Cleanup after each test"""
    yield

    # クリーンアップの実行
    await MemoryBackend.cleanup_all()

    # 残っているタスクのキャンセル
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()

    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


@pytest.fixture(scope="session", autouse=True)
async def cleanup_on_session_end():
    """Cleanup at the end of test session"""
    yield

    # 全インスタンスのクリーンアップ
    await MemoryBackend.cleanup_all()

    # イベントループのクリーンアップ
    try:
        loop = asyncio.get_event_loop()
        if not loop.is_closed():
            # 保留中のコールバックを処理
            await asyncio.sleep(0.1)
    except Exception:
        pass
