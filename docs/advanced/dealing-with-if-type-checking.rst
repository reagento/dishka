Dealing with ``if TYPE_CHECKING``
===================================

Sometimes you want to split interdependent models into several files.
This results in some imports being visible only to type checkers.
Analysis of such type hints is not available at runtime.


Let's imagine that we have two files:

.. literalinclude:: examples/dealing_with_type_checking/chat.py
   :caption: File ``chat.py``
   :lines: 2-

.. literalinclude:: examples/dealing_with_type_checking/message.py
   :caption: File ``message.py``
   :lines: 2-

If you try to get type hints at runtime, you will fail:

.. code-block:: python

   from typing import get_type_hints

   from .chat import Chat
   from .message import Message

   try:
      get_type_hints(Chat)
   except NameError as e:
      assert str(e) == "name 'Message' is not defined"


   try:
      get_type_hints(Message)
   except NameError as e:
      assert str(e) == "name 'Chat' is not defined"


At runtime, these imports are not executed, so the builtin analysis function can not resolve forward refs.

Dishka can overcome this via :func:`exec_type_checking`.
It extracts code fragments defined under ``if TYPE_CHECKING`` and ``if typing.TYPE_CHECKING`` constructs
and then executes them in the context of module.
As a result, the module namespace is filled with missing names, and *any* introspection function can acquire types.

You should call ``exec_type_checking`` after all required modules can be imported.
Usually, it must be at ``main`` module.

.. code-block:: python

   from typing import get_type_hints

   from dishka import exec_type_checking

   from . import chat, message

   # You pass the module object
   exec_type_checking(chat)
   exec_type_checking(message)

   # After these types can be extracted
   assert get_type_hints(chat.Chat) == {
      "id": int,
      "name": str,
      "messages": list[message.Message],
   }
   assert get_type_hints(chat.Message) == {
      "id": int,
      "text": str,
      "chat": chat.Chat,
   }
