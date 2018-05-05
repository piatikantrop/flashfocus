"""Handle window-specific flash rules."""
from logging import info
import re

from flashfocus.flasher import Flasher
from flashfocus.misc import list_param
from flashfocus.xutil import get_wm_class


class Rule:
    """A rule for matching a window's id and class to a set of criteria.

    If no parameters are passed, the rule will match any window.

    Parameters
    ----------
    id_regex, class_regex: regex
        Window ID and class match criteria

    """
    def __init__(self, id_regex=None, class_regex=None):
        self.id_regex = id_regex
        self.class_regex = class_regex

    def match(self, window_id, window_class):
        """Match a window id and class.

        Parameters
        ----------
        window_id, window_class: str
            ID and class of a window

        """
        if self.id_regex:
            if not re.match(self.id_regex, window_id):
                return False
        if self.class_regex:
            if not re.match(self.class_regex, window_class):
                return False
        return True


class RuleMatcher:
    """Matches a set of window match criteria to a set of flash parameters.

    This is used for determining which flash parameters should be used for a
    given window. If no rules match the window, a default set of parameters is
    used.

    Parameters
    ----------
    defaults: Dict[str, Any]
        Set of default parameters. Must include all `Flasher` parameters and
        `flash_on_focus` setting.
    rules: Dict[str, Any]
        Set of rule parameters from user config. Must include all `Flasher`
        parameters, `flash_on_focus` setting and `window_id` and/or
        `window_class`.

    """
    def __init__(self, defaults, rules):
        self.rules = []
        self.flashers = []
        self.flash_on_focus = []
        flasher_param = list_param(Flasher.__init__)
        for rule in rules:
            self.rules.append(
                Rule(id_regex=rule.get('window_id'),
                     class_regex=rule.get('window_class')))
            self.flashers.append(Flasher(**{k: rule[k] for k in flasher_param}))
            self.flash_on_focus.append(rule['flash_on_focus'])
        self.rules.append(Rule())
        self.flash_on_focus.append(defaults['flash_on_focus'])
        self.flashers.append(Flasher(**{k: defaults[k] for k in flasher_param}))
        self.iter = list(zip(self.rules, self.flash_on_focus, self.flashers))

    def flash(self, window, request_type=None):
        """Flash a window using matching rule criteria.

        Parameters
        ----------
        window: int
            A Xorg window id
        request_type: str
            One of ['focus_shift', 'client_request'], if 'focus_shift' and
            flash_on_focus is set for the matching rule, the window will not be
            flashed.

        """
        flasher = self.match(window, request_type)[1]
        if flasher:
            flasher.flash_window(window)

    def match(self, window, request_type=None):
        """Find a flash rule which matches `window`

        Parameters
        ----------
        window: int
            A Xorg window id
        request_type: str
            One of ['focus_shift', 'client_request']

        Returns
        -------
        Tuple[Rule, Flasher]
            The matching rule and flasher. Returns None if
            request_type=='focus_shift' and flash_on_focus is False for the rule

        """
        window_id, window_class = get_wm_class(window)
        i = 1
        for rule, focus_flash, flasher in self.iter:
            if rule.match(window_id, window_class):
                info('Window %s matches criteria of rule %s', window, i)
                if request_type == 'focus_shift' and not focus_flash:
                    return None
                return rule, flasher
            i += 1
        raise RuntimeError('No rule matched the window, this is a bug!')
