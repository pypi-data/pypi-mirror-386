from copy import deepcopy
from datetime import date, datetime
import sys
from typing import Dict, Optional, Tuple, TypeVar

import click
import colorama

from anyscale._private.workload import WorkloadConfig
from anyscale.cli_logger import BlockLogger


logger = BlockLogger()


class AnyscaleCommand(click.Command):
    """
    AnyscaleCommand is a subclass of click.Command that allows for the addition of
    CLI examples.

    :param __doc_cli_example__: A string that represents CLI examples.
    """

    def __init__(self, *args, **kwargs):
        self.__doc_cli_example__ = kwargs.pop("example", None)
        self.__is_alpha__ = kwargs.pop("is_alpha", False)
        self.__is_beta__ = kwargs.pop("is_beta", False)
        super().__init__(*args, **kwargs)

    @property
    def is_alpha(self) -> bool:
        return self.__is_alpha__

    @property
    def is_beta(self) -> bool:
        return self.__is_beta__


class LegacyAnyscaleCommand(click.Command):
    """
    LegacyAnyscaleCommand is a subclass of click.Command that allows for the addition of
    upgrade information.

    :param __doc_new_cli__: The CLI command that the legacy command should be upgraded to.
    :param __doc_new_prefix__ : The prefix of the new CLI command.
    """

    def __init__(self, *args, **kwargs):
        self.__doc_new_cli__ = kwargs.pop("new_cli", None)
        self.__doc_new_prefix__ = kwargs.pop("new_prefix", None)
        self.__doc_legacy_prefix__ = kwargs.pop("legacy_prefix", None)
        self.__is_limited_support__ = kwargs.pop("is_limited_support", False)
        super().__init__(*args, **kwargs)

    def get_new_cli(self) -> AnyscaleCommand:
        return self.__doc_new_cli__

    def get_new_prefix(self) -> str:
        return self.__doc_new_prefix__

    def get_legacy_prefix(self) -> str:
        return self.__doc_legacy_prefix__

    def is_limited_support(self) -> bool:
        return self.__is_limited_support__


# Take from https://stackoverflow.com/questions/51846634/click-dynamic-defaults-for-prompts-based-on-other-options
class OptionPromptNull(click.Option):
    """
    Option class that allows default values based on previous params
    """

    _value_key = "_default_val"

    def __init__(self, *args, **kwargs):
        self.default_option = kwargs.pop("default_option", None)
        super().__init__(*args, **kwargs)

    def get_default(self, ctx, **kwargs):
        if not hasattr(self, self._value_key):
            if self.default_option is None:
                default = super().get_default(ctx, **kwargs)
            else:
                arg = ctx.params.get(self.default_option)
                if arg is not None:
                    default = self.type_cast_value(ctx, self.default(arg))
                else:
                    default = None
            setattr(self, self._value_key, default)
        return getattr(self, self._value_key)


# Taken from https://stackoverflow.com/questions/44247099/click-command-line-interfaces-make-options-required-if-other-optional-option-is
class NotRequiredIf(click.Option):
    """
    Option class that allows an option to be not required if a separate option is available.
    """

    def __init__(self, *args, **kwargs):
        self.not_required_if = kwargs.pop("not_required_if")
        assert self.not_required_if, "'not_required_if' parameter required"
        kwargs["help"] = (
            kwargs.get("help", "")
            + " NOTE: This argument is mutually exclusive with %s"
            % self.not_required_if
        ).strip()
        super().__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        we_are_present = self.name in opts
        other_present = self.not_required_if in opts

        if other_present:
            if we_are_present:
                raise click.UsageError(
                    "Illegal usage: `%s` is mutually exclusive with `%s`"
                    % (self.name, self.not_required_if)
                )
            else:
                self.prompt = None
                self.default = None

        return super().handle_parse_result(ctx, opts, args)


def convert_kv_strings_to_dict(strings: Tuple[str]) -> Dict[str, str]:
    """Convert args/env_vars of the form "key=val" into a dictionary of {key: val}.

    NOTE(edoakes): this mimics the functionality of the `serve run` CLI and should be
    kept in sync with it.
    """
    ret_dict = {}
    for s in strings:
        split = s.split("=", maxsplit=1)
        if len(split) != 2 or len(split[1]) == 0:
            raise click.ClickException(
                f"Invalid key-value string '{s}'. Must be of the form 'key=value'."
            )

        ret_dict[split[0]] = split[1]

    return ret_dict


T = TypeVar("T", bound=WorkloadConfig)


def override_env_vars(config: T, overrides: Dict[str, str]) -> T:
    """Returns a new copy of the WorkloadConfig with env vars overridden.

    This is a per-key override, so keys already in the config that are not specified in
    overrides will not be updated.
    """
    if not overrides:
        return config

    final_env_vars = deepcopy(config.env_vars) if config.env_vars else {}
    final_env_vars.update(overrides)
    return config.options(env_vars=final_env_vars)


class DeprecatedAnyscaleCommand(click.Command):
    """
    DeprecatedAnyscaleCommand is a subclass of click.Command that shows deprecation warnings.

    Similar to LegacyAnyscaleCommand but focuses on deprecation with dates and alternatives.
    """

    def __init__(self, *args, **kwargs):
        self.__removal_date__ = kwargs.pop("removal_date", None)
        self.__deprecation_message__ = kwargs.pop("deprecation_message", None)
        self.__alternative__ = kwargs.pop("alternative", None)
        super().__init__(*args, **kwargs)

    def get_help(self, ctx):
        """Override get_help to show deprecation warning when help is displayed."""
        self._show_deprecation_warning()
        return super().get_help(ctx)

    def invoke(self, ctx):
        """Override invoke to show deprecation warning before executing."""
        self._show_deprecation_warning()
        return super().invoke(ctx)

    def _show_deprecation_warning(self):
        """Show the deprecation warning."""

        # Visual separator for attention
        print("\n" + "=" * 80, file=sys.stderr)
        print(
            f"{colorama.Style.BRIGHT}{colorama.Fore.YELLOW}⚠️  DEPRECATION WARNING ⚠️{colorama.Style.RESET_ALL}",
            file=sys.stderr,
        )
        print("=" * 80, file=sys.stderr)

        # Build deprecation message
        base_msg = (
            self.__deprecation_message__
            if self.__deprecation_message__
            else f"Command '{self.name}' is deprecated"
        )

        # Removal date information with grammar-aware connector
        date_msg = None
        if self.__removal_date__:
            date_str = self._format_removal_date(self.__removal_date__)
            if date_str:
                ends_with_punct = base_msg.strip().endswith((".", "!", "?"))
                if ends_with_punct:
                    date_msg = f"It will be removed on {date_str}"
                else:
                    date_msg = f"and will be removed on {date_str}"

        # Alternative suggestion
        alternative_msg = None
        if self.__alternative__:
            alternative_msg = f"\n\n➡️  {colorama.Style.BRIGHT}Please {self.__alternative__}{colorama.Style.RESET_ALL}"

        main_line_parts = [part for part in (base_msg, date_msg) if part]
        deprecation_msg = " ".join(main_line_parts)
        if alternative_msg:
            deprecation_msg += alternative_msg

        # Logger warning but also print directly for visibility
        print(
            f"\n{colorama.Fore.YELLOW}{deprecation_msg}{colorama.Style.RESET_ALL}",
            file=sys.stderr,
        )
        print("=" * 80 + "\n", file=sys.stderr)

    def _format_removal_date(self, removal_date) -> Optional[str]:
        """Format the removal date for display."""
        try:
            if isinstance(removal_date, str):
                parsed_date = datetime.strptime(removal_date, "%Y-%m-%d").date()
            elif isinstance(removal_date, datetime):
                parsed_date = removal_date.date()
            elif isinstance(removal_date, date):
                parsed_date = removal_date
            else:
                return None

            return parsed_date.strftime("%Y-%m-%d")
        except (ValueError, AttributeError):
            return str(removal_date)
