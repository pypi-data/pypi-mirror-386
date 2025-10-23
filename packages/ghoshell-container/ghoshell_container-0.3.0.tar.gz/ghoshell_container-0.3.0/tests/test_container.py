import warnings
from abc import ABCMeta, abstractmethod
from typing import Type, Dict, get_args, get_origin, ClassVar, Optional

from ghoshell_container import Container, Provider, provide, BootstrapProvider, INSTANCE, IoCContainer


def test_type_check():
    container = Container()
    assert isinstance(container, IoCContainer)


def test_container_baseline():
    class Abstract(metaclass=ABCMeta):
        @abstractmethod
        def foo(self) -> int:
            pass

    class Foo(Abstract):
        count = 0

        def foo(self) -> int:
            self.count += 1
            return self.count

    class FooProvider(Provider):

        def __init__(self, singleton: bool):
            self._s = singleton

        def singleton(self) -> bool:
            return self._s

        def contract(self) -> Type[Abstract]:
            return Abstract

        def factory(self, con: Container, params: Dict | None = None) -> Abstract | None:
            return Foo()

    # 初始化
    container = Container()
    container.bootstrap()
    container.set(Abstract, Foo())

    # 获取单例
    foo = container.fetch(Abstract)
    assert foo.foo() == 1
    foo = container.fetch(Abstract)
    assert foo.foo() == 2  # 获取的是单例
    foo = container.fetch(Abstract)
    assert foo.foo() == 3

    # 注册 provider, 销毁了单例.
    container.register(FooProvider(True))

    # 二次取值. 替换了 原始实例, 但还是生成单例.
    foo = container.force_fetch(Abstract)
    assert foo.foo() == 1
    foo = container.force_fetch(Abstract)
    assert foo.foo() == 2

    # 注册 provider, 销毁了单例. 注册的是非单例
    container.register(FooProvider(False))
    foo = container.force_fetch(Abstract)
    assert foo.foo() == 1
    # 每次都是返回新实例.
    foo = container.force_fetch(Abstract)
    assert foo.foo() == 1
    assert foo.foo() == 2


def test_sub_container():
    class Foo:
        def __init__(self, foo: int):
            self.foo = foo

    container = Container()
    container.bootstrap()
    container.set(Foo, Foo(1))
    sub = Container(parent=container)
    sub.bootstrap()
    sub.set(Foo, Foo(2))

    # 验证父子互不污染.
    assert container.force_fetch(Foo).foo == 1
    assert sub.force_fetch(Foo).foo == 2


def test_boostrap():
    container = Container()

    class Foo:
        foo: int = 1

    container.set(Foo, Foo())
    container.bootstrap()
    assert container.force_fetch(Foo).foo == 1


def test_provider_generic_types():
    class SomeProvider(Provider[int]):

        def singleton(self) -> bool:
            return True

        def factory(self, con: Container) -> int:
            return 3

    # baseline
    args = get_args(Provider[int])
    assert args[0] is int
    assert get_origin(Provider[int]) is Provider

    p = SomeProvider()
    con = Container()
    assert p.singleton()
    assert p.factory(con) == 3
    assert p.contract() is int


def test_provide_with_lambda():
    container = Container()
    container.bootstrap()
    container.register(provide(int)(lambda: 10))
    container.register(provide(str)(lambda: "hello"))

    assert container.force_fetch(int) == 10
    assert container.force_fetch(str) == "hello"


def test_provide_in_loop():
    container = Container()
    container.bootstrap()
    for a, fn in {int: lambda: 10, str: lambda: "hello"}.items():
        container.register(provide(a)(fn))

    assert container.force_fetch(int) == 10
    assert container.force_fetch(str) == "hello"


def test_container_set_str():
    container = Container()
    container.set("foo", "bar")
    assert container.get("foo") == "bar"


def test_container_inherit():
    class Foo:
        def __init__(self, foo: int):
            self.foo = foo

    class Bar:
        def __init__(self, foo: Foo):
            self.foo = foo

        bar: str = "hello"

    # parent register bar, bar depend on foo; so bar can not fetch from parent container.
    container = Container()
    container.bootstrap()

    def make_bar(_foo: Foo) -> Bar:
        return Bar(_foo)

    bar_provider = provide(Bar, singleton=False)(make_bar)
    assert bar_provider.inheritable()
    container.factory(Bar, singleton=False)(make_bar)

    sub_container = Container(container)
    # sub container register Foo that Bar needed
    sub_container.register(provide(Foo, singleton=False)(lambda: Foo(2)))
    sub_container.bootstrap()
    # the parent's providers are inherited by sub container.
    bar = sub_container.force_fetch(Bar)
    assert bar.bar == "hello"
    assert isinstance(bar.foo, Foo)
    assert bar.foo.foo == 2


def test_bloodline():
    container = Container()
    container.bootstrap()
    assert container.bloodline is not None
    sub = Container(parent=container, name="hello")
    assert len(sub.bloodline) == 2


def test_container_shutdown():
    class Foo:
        instance_count: ClassVar[int] = 0

        def __init__(self):
            Foo.instance_count += 1

        def shutdown(self):
            Foo.instance_count -= 1

    container = Container()
    f = Foo()
    container.set(Foo, f)
    container.add_shutdown(f.shutdown)
    assert Foo.instance_count == 1
    container.shutdown()
    assert Foo.instance_count == 0


def test_container_make_baseline():
    class Foo:

        def __init__(self, a: int = 0):
            self.a = a

    class Bar:
        def __init__(self, foo: Foo, b: int = 0):
            self.foo = foo
            self.b = b

    class Zoo:
        def __init__(
                self,
                a: int = 123,
                b: int = 456,
        ):
            self.a = a
            self.b = b

    container = Container()
    container.bootstrap()
    container.set(Foo, Foo(123))
    bar = container.make(Bar, b=1)
    assert bar.b == 1
    assert bar.foo.a == 123

    bar2 = container.make(Bar, b=456)
    assert bar2.b == 456

    zoo = container.make(Zoo, a=123, b=456)
    assert zoo.a == 123
    assert zoo.b == 456

    def zoo(_bar: Bar, c: int) -> int:
        return _bar.foo.a + _bar.b + c

    container = Container()
    container.bootstrap()
    v = container.call(zoo, c=3)
    assert v > 0


def test_bootstrap_after_bootstrapped():
    class Foo:
        def __init__(self):
            self.foo: int = 0

        def shutdown(self):
            self.foo += 1

    class FooProvider(BootstrapProvider):

        def contract(self) -> Type[Foo]:
            return Foo

        def singleton(self) -> bool:
            return True

        def factory(self, con: Container) -> Optional[INSTANCE]:
            foo = Foo()
            assert foo.foo == 0
            foo.foo += 1
            return foo

        def bootstrap(self, container: Container) -> None:
            f = container.force_fetch(Foo)
            f.foo += 1
            container.add_shutdown(f.shutdown)

    warnings.filterwarnings("ignore", category=UserWarning)

    foo = Foo()
    assert foo.foo == 0
    container = Container()
    container.register(FooProvider())
    foo = container.force_fetch(Foo)
    assert foo.foo == 1
    container.bootstrap()
    assert foo.foo == 2
    container.shutdown()
    assert foo.foo == 3

    container = Container()
    container.bootstrap()
    container.register(FooProvider())
    foo = container.force_fetch(Foo)
    # bootstrap and factory
    assert foo.foo == 2
    container.shutdown()
    assert foo.foo == 3


def test_container_force_fetch_protocol():
    from typing import Protocol

    class Foo(Protocol):
        foo: int

    class Bar:
        foo: int = 123

    container = Container()
    container.bind(Foo, Bar())
    assert container.force_fetch(Foo).foo == 123
