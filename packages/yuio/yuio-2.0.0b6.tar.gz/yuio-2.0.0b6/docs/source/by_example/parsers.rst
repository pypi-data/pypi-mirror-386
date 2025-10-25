Parsing user input
==================

Introduction to parsers and :mod:`yuio.parse`.

Parsers control how Yuio interprets user input; they provide hints about which widgets
to use, how to do autocompletion, and so on. Every time you get data from user,
a parser is involved.

By default, Yuio constructs an appropriate parser from type hints. You can customize
this process by using :class:`typing.Annotated`, or you can build a parser on your own.


Creating and using a parser
---------------------------

Parser classes are located in :mod:`yuio.parse`. Let's make a simple parser
for positive integers:

.. code-block:: python

    import yuio.parse

    parser = yuio.parse.Gt(yuio.parse.Int(), 0)

We can now use this parser on our own::

    >>> parser.parse("10")  # Parse text input
    10
    >>> data = 5  # Pretend this was loaded from JSON
    >>> parser.parse_config(data)  # Convert raw JSON data
    5

Or pass it to other Yuio methods:

.. code-block::

    yuio.io.ask("Choose a number", parser=parser)

.. vhs-inline::
    :scale: 40%

    Source "docs/source/_tapes/_config_by_example.tape"
    Type "python -m parsers_code.ask"
    Enter
    Sleep 1s
    Type "-25"
    Sleep 250ms
    Enter
    Sleep 2s
    Backspace 3
    Sleep 250ms
    Type "15"
    Sleep 250ms
    Enter
    Sleep 4s


Creating a parser from type hints
---------------------------------

You can also build a parser from type hint, should you need one::

    >>> parser = yuio.parse.from_type_hint(dict[str, int])
    >>> parser.parse("x:10 y:-5")
    {'x': 10, 'y': -5}


Annotating type hints
---------------------

Type hints offer a more concise way to build a parser. However, they're less expressive
when it comes to constraints or validation. You'll have to use
:class:`typing.Annotated` to inject parsers that don't map directly to types:

.. code-block:: python

    from typing import Annotated

    type_hint = dict[str, Annotated[int, yuio.parse.Gt(0)]]

Here, we've created a parser for dictionaries that map strings to *positive ints*.
Technically, Yuio will derive a parser from ``int``, then it will apply
``yuio.parse.Gt(0)`` on top of it::

    >>> parser = yuio.parse.from_type_hint(type_hint)
    >>> parser.parse("x:-5")
    Traceback (most recent call last):
    ...
    yuio.parse.ParsingError: value should be greater than 0, got -5 instead

Notice that we didn't specify inner parser for :class:`~yuio.parse.Gt`.
This is because its internal parser will be derived from type hint,
so we only care about :class:`~yuio.parse.Gt`'s settings.

Parsers created in such a way are called "partial". You can't use a partial parser
on its own because it doesn't have full information about the object's type.
You can only use partial parsers in type hints::

    >>> partial_parser = yuio.parse.List(delimiter=",")
    >>> partial_parser.parse("1,2,3")  # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    TypeError: List requires an inner parser
    ...


Customizing parsers for CLI arguments and config fields
-------------------------------------------------------

Now that we know how to use parsers, we can customize CLI arguments and config fields:

.. tab-set::
    :sync-group: parser-usage

    .. tab-item:: Parsers
        :sync: parsers

        .. code-block:: python
            :emphasize-lines: 8

            import yuio.app
            import yuio.parse

            @yuio.app.app
            def main(
                n_threads: int | None = yuio.app.field(
                    default = None,
                    parser = yuio.parse.Gt(yuio.parse.Int(), 0),
                )
            ):
                ...

    .. tab-item:: Annotations
        :sync: annotations

        .. code-block:: python
            :emphasize-lines: 6

            import yuio.app
            import yuio.parse

            @yuio.app.app
            def main(
                n_threads: Annotated[int, yuio.parse.Gt(0)] | None = None
            ):
                ...


Enum parser
-----------

A parser that you will use quite often is :class:`yuio.parse.Enum`.
It parses string-based enumerations derived from :class:`enum.Enum`.
We encourage users to use enums over plain strings because they provide
enhanced widgets and autocompletion:

.. vhs:: /_tapes/widget_choice.tape
    :alt: Demonstration of `Choice` widget.
    :scale: 40%

Enum parser has a few useful settings. It can load enumerators by name or by value,
and it also can convert enumerator names to dash case:

.. tab-set::
    :sync-group: parser-usage

    .. tab-item:: Parsers
        :sync: parsers

        .. code-block::

            class Beverage(enum.Enum):
                COFFEE = 1
                TEA = 2
                SODA = 3
                WATER = 4

            yuio.io.ask(
                "Which beverage would you like?",
                parser=yuio.parse.Enum(Beverage, by_name=True, to_dash_case=True),
            )

    .. tab-item:: Annotations
        :sync: annotations

        .. code-block::

            class Beverage(enum.Enum):
                COFFEE = 1
                TEA = 2
                SODA = 3
                WATER = 4

            yuio.io.ask[
                Annotated[
                    Beverage,
                    yuio.parse.Enum(by_name=True, to_dash_case=True),
                ]
            ]("Which beverage would you like?")


JSON parser
-----------

While Yuio supports parsing collections, it doesn't provide a fully capable
context-free parser; instead, it relies on splitting string by delimiters,
which can be limiting.

To enable parsing more complex structures, Yuio provides a :class:`yuio.parse.Json`.

It can be used on its own:

.. tab-set::
    :sync-group: parser-usage

    .. tab-item:: Parsers
        :sync: parsers

        ::

            >>> parser = yuio.parse.Json()
            >>> parser.parse('{"key": "value"}')
            {'key': 'value'}

    .. tab-item:: Annotations
        :sync: annotations

        ::

            >>> parser = yuio.parse.from_type_hint(yuio.parse.JsonValue)
            >>> parser.parse('{"key": "value"}')
            {'key': 'value'}

Or with a nested parser:

.. tab-set::
    :sync-group: parser-usage

    .. tab-item:: Parsers
        :sync: parsers

        ::

            >>> parser = yuio.parse.Json(yuio.parse.List(yuio.parse.Int()))
            >>> parser.parse("[1, 2, 3]")
            [1, 2, 3]

    .. tab-item:: Annotations
        :sync: annotations

        ::

            >>> parser = yuio.parse.from_type_hint(Annotated[list[int], yuio.parse.Json()])
            >>> parser.parse("[1, 2, 3]")
            [1, 2, 3]

.. vhs-inline::
    :scale: 40%

    Source "docs/source/_tapes/_config_by_example.tape"
    Type "python -m parsers_code.json "
    Sleep 100ms
    Type "--data "
    Sleep 250ms
    Type "'[]'"
    Sleep 100ms
    Left 2
    Sleep 250ms
    Type "1, 2,"
    Sleep 100ms
    Type " 3"
    Right 2
    Sleep 1s
    Enter
    Sleep 6s


Validating parsers
------------------

Yuio provides :ref:`a variety <validating-parsers>` of parsers that validate
user input. If' however, you need a more complex validating procedure,
you can use :class:`yuio.parse.Apply` with a custom function that throws
:class:`yuio.parse.ParsingError` if validation fails.

For example, let's make a parser that checks if the input is even:

.. tab-set::
    :sync-group: parser-usage

    .. tab-item:: Parsers
        :sync: parsers

        .. code-block:: python

            def assert_is_even(value: int):
                if value % 2 != 0:
                    raise yuio.parse.ParsingError(
                        f"expected an even value, got {value}"
                    )

            parser = yuio.parse.Apply(yuio.parse.Int(), assert_is_even)

    .. tab-item:: Annotations
        :sync: annotations

        .. code-block:: python

            def assert_is_even(value: int):
                if value % 2 != 0:
                    raise yuio.parse.ParsingError("expected an even value")

            parser = yuio.parse.from_type_hint(
                Annotated[int, yuio.parse.Apply(assert_is_even)]
            )

The parser will apply our ``assert_is_even`` to all values that it returns::

    >>> parser.parse("2")
    2
    >>> parser.parse("3")
    Traceback (most recent call last):
    ...
    yuio.parse.ParsingError: expected an even value


Mutating parsers
----------------

In addition to validation, you can mutate the input. For example:

.. tab-set::
    :sync-group: parser-usage

    .. tab-item:: Parsers
        :sync: parsers

        ::

            >>> parser = yuio.parse.Lower(yuio.parse.Str())
            >>> parser.parse("UPPER")
            'upper'

    .. tab-item:: Annotations
        :sync: annotations

        ::

            >>> parser = yuio.parse.from_type_hint(
            ...     Annotated[str, yuio.parse.Lower()]
            ... )
            >>> parser.parse("UPPER")
            'upper'

You can also use :class:`yuio.parse.Map` to implement a custom mutation.

Note that parsers need to convert parsed values back to their original form
when printing them, building documentation, or converting to JSON. For this reason,
:class:`yuio.parse.Map` allows specifying a function to undo the change:

.. invisible-code-block: python

    import math

.. tab-set::
    :sync-group: parser-usage

    .. tab-item:: Parsers
        :sync: parsers

        ::

            >>> parser = yuio.parse.Map(
            ...     yuio.parse.Int(),
            ...     lambda x: 2 ** x,
            ...     lambda x: int(math.log2(x)),
            ... )
            >>> parser.parse("10")
            1024
            >>> parser.describe_value_or_def(1024)
            '10'

    .. tab-item:: Annotations
        :sync: annotations

        ::

            >>> parser = yuio.parse.from_type_hint(Annotated[
            ...     int,
            ...     yuio.parse.Map(lambda x: 2 ** x, lambda x: int(math.log2(x))),
            ... ])
            >>> parser.parse("10")
            1024
            >>> parser.describe_value_or_def(1024)
            '10'
