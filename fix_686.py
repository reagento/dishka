# path: reagento/dishka/src/dishka/code_tools/factory_compiler.py

from dishka.code_tools.compilation_key import CompilationKey

def compile_factory(factory: Factory):
    # ...
    # Replace the unique object with a CompilationKey object
    cache_key = CompilationKey(factory)
    # ...