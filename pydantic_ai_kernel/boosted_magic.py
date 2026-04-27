from metakernel import Magic
from metakernel.magic import (
    _indent,
    _split_args,
)
from typing import Any, TypeVar, Callable
import inspect
import traceback
import argparse
from statikomand import KomandParser

_F = TypeVar("_F", bound=Callable[..., Any])


class BoostedMagic(Magic):
    """
    Subclass of metakernel Magics, that provides additional
    features :
        - completion for options names and values, based
            on custom completer objects
        - parsing based on argparse

    To implement custom parser for magic line, the get_args
    and call_magic had to be reimplemented.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    def get_args(self, mtype: str, name: str, code: str, args: Any) -> Any:
        self.code = code
        old_args = args
        mtype = mtype.replace("sticky", "cell")

        func = getattr(self, mtype + "_" + name)

        if "-h" in args or "--help" in args:
            # --help flag of argparse writes to stdout,
            # which break kernels (do_is_complete message is
            # unanswered, which makes the kernel to crash).
            return ["help"], dict(), list()

        try:
            args, kwargs = _boosted_parse_args(
                func, args, usage=self.get_help(mtype, name)
            )
        except Exception as e:
            self.kernel.Error(str(e))
            return self
        arg_spec = inspect.getfullargspec(func)
        fargs = arg_spec.args
        if fargs[0] == "self":
            fargs = fargs[1:]

        fargs = [f for f in fargs if f not in kwargs.keys()]
        if len(args) > len(fargs) and not arg_spec.varargs:
            extra = " ".join(str(s) for s in (args[len(fargs) - 1 :]))
            args = args[: len(fargs) - 1] + [extra]

        return (args, kwargs, old_args)

    def call_magic(self, mtype: str, name: str, code: str, args: Any) -> Magic:
        self.code = code
        old_args = args
        mtype = mtype.replace("sticky", "cell")

        func = getattr(self, mtype + "_" + name)
        try:
            args, kwargs = _boosted_parse_args(
                func, args, usage=self.get_help(mtype, name)
            )
        except Exception as e:
            self.kernel.Error(str(e))
            return self

        arg_spec = inspect.getfullargspec(func)
        fargs = arg_spec.args
        if fargs[0] == "self":
            fargs = fargs[1:]

        fargs = [f for f in fargs if f not in kwargs.keys()]
        if len(args) > len(fargs) and not arg_spec.varargs:
            extra = " ".join(str(s) for s in (args[len(fargs) - 1 :]))
            args = args[: len(fargs) - 1] + [extra]

        try:
            try:
                func(*args, **kwargs)
            except TypeError:
                func(old_args)
        except Exception as exc:
            msg = f"Error in calling magic '{name}' on {mtype}:\n    {exc!s}\n    args: {args}\n    kwargs: {kwargs}"
            self.kernel.Error(msg)
            self.kernel.Error(traceback.format_exc())
            self.kernel.Error(self.get_help(mtype, name))
            # return dummy magic to end processing:
            return Magic(self.kernel)
        return self

    def get_completions(self, info: dict[str, Any]) -> list[str]:
        """
        Uses statikomand argparse subclass to complete the current magic.
        """
        self.kernel.log.info(f"Info boosted magic : {info}")
        func = None
        for each_attr in dir(self):
            if each_attr.startswith("line"):
                func = getattr(self, each_attr)
                break
            # for now, info does not contains magic type
            # if each_attr.startswith("cell"):
            #     func = getattr(self, each_attr)
            #     break
        if func is None:
            self.kernel.log.warning("Could not find any magic to complete.")
            return []
        if not getattr(func, "has_boosted_options", False):
            self.kernel.log.debug(
                "No boosted options found for magic, hence not completing."
            )
            return []
        boosted_parser: KomandParser | bool = getattr(func, "boosted_parser", False)
        if not boosted_parser:
            self.kernel.log.warning(
                "Could not find boosted parser for magic, but has_boosted_options is True. Not completing."
            )
            return []
        args = info["code"]
        if isinstance(args, list):
            args = " ".join(args)

        args = _split_args(args)
        if not isinstance(boosted_parser, KomandParser):
            raise TypeError(
                f"boosted_parser parameter of magic method must be a KomandParser, not {type(boosted_parser)}."
            )

        # finally calls complete method of boosted parser
        try:
            completed = boosted_parser.complete(args)
        except Exception:
            self.kernel.log.debug(
                f"Error when completing option : {traceback.format_exc()}"
            )
            return []

        if len(args) > 0:
            self.kernel.log.info(f"Modifying -- and - tokens : {completed}")
            result = []
            last_token = args[-1]
            self.kernel.log.info(f"last token : {last_token}")
            for each_match in completed:
                if each_match == last_token:
                    continue
                # for option tokens (starting with '-'), metakernel does
                # not replace the full token, but adds the completion.
                # so we need to truncate it. Somehow, tokens starting
                # with '-' are not treated as others.
                # For other tokens, it works as statikomand.
                if last_token.startswith("--") and each_match.startswith("--"):
                    each_match = each_match[2:]
                elif last_token.startswith("-") and each_match.startswith("-"):
                    each_match = each_match[1:]

                result.append(each_match)
        else:
            result = completed
        self.kernel.log.debug(f"Boosted magic completion : {result}")
        return result


def boosted_option(*args: Any, **kwargs: Any) -> Callable[[_F], _F]:
    """
    Return decorator that adds a boosted magic option to a function.
    The boosted magic uses argparse instead of optparse, and
    allows for tab completion among options names and values.
    """

    def decorator(func: _F) -> _F:
        help_text = ""
        if not getattr(func, "has_boosted_options", False):
            func.has_boosted_options = True  # type:ignore[attr-defined]
            func.boosted_parser = KomandParser(prog=func.__name__, add_help=False)  # type:ignore[attr-defined]
            # boosted_parser is an instance of argparse.ArgumentParser
            # add_help is set to False because argparse help writes to stdout, which
            # breaks kernel machinery
            help_text += "Options:\n-------\n"

        try:
            action = func.boosted_parser.add_argument(*args, **kwargs)  # type:ignore[attr-defined]
        except AttributeError:
            pass
        except argparse.ArgumentError:
            help_text += args[0] + "\n"
        else:
            help_text += _format_action(action) + "\n"
        if func.__doc__:
            func.__doc__ += _indent(func.__doc__, help_text)
        else:
            func.__doc__ = help_text
        return func

    return decorator


def _boosted_parse_args(
    func, args: str | list[str], usage
) -> tuple[list[Any], dict[str, Any]]:

    if isinstance(args, list):
        args = " ".join(args)
    args = _split_args(args)

    # raise ValueError(f"dajkbz {args}")
    if getattr(func, "has_boosted_options", False) and getattr(
        func, "boosted_parser", False
    ):
        if not isinstance(func.boosted_parser, argparse.ArgumentParser):
            return list(), dict()
        parsed_args = func.boosted_parser.parse_args(args)
        return parsed_args._get_args(), parsed_args.__dict__
    return list(), dict()


def _format_action(action: argparse.Action):
    out = ""
    out = ", ".join(action.option_strings) + f" : {action.help}"
    return out


def complete_from_list(
    list_of_reference: list[str],
    word: str,
    rank: int = 0,
):
    """
    Completes a word from a given list_of_reference.
    Return all occurences of list_of_reference whose
    beginning matches word.
    Can be used as within a lambda function with a custom list:

    ```python
    my_list = ["bobo", "baba"]
    completer = lambda w,r : complete_from_list(my_list, w, r)
    ```

    """
    all_matches = []

    for each_word in list_of_reference:
        if len(each_word) < len(word):
            continue
        potential_match = each_word[: len(word)]
        if potential_match == word:
            all_matches.append(each_word)
    return all_matches
