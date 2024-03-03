from .component import DEFAULT_COMPONENT, Component


class FromDishka:
    def __init__(self, component: Component = DEFAULT_COMPONENT):
        self.component = component
