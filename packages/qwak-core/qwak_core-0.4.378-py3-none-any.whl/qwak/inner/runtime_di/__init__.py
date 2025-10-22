from qwak.inner.runtime_di.containers import QwakRuntimeContainer, ContainerLock


def wire_runtime():
    container = QwakRuntimeContainer()
    from qwak.model import decorators

    container.wire(
        packages=[
            decorators,
        ]
    )
    return container
