from ghoshell_container.containers import Container
import asyncio


def test_container_call_async_func():
    class Foo:
        def __init__(self, foo: int):
            self.foo = foo

    c = Container()
    c.set(Foo, Foo(2))

    ok = []

    async def bar(foo: Foo):
        ok.append(foo.foo)

    async def main():
        await c.call(bar)

    asyncio.run(main())
    assert ok[0] == 2
