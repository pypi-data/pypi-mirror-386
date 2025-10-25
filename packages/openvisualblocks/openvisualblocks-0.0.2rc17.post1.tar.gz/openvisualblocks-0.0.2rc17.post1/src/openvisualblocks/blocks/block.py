class Block:
    def __init__(self, *, name: str, category: str, title: str, description: str, inputs: list, outputs: list, properties: list, callback: callable):
        self.name = name
        self.category = category
        self.title = title
        self.description = description
        self.inputs = inputs
        self.outputs = outputs
        self.properties = properties
        self.callback = callback

    def __call__(self, *args, **kwargs):
        return self.callback(*args, **kwargs)