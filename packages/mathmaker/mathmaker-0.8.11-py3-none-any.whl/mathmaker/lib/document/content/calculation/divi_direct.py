# -*- coding: utf-8 -*-

# Mathmaker creates automatically maths exercises sheets
# with their answers
# Copyright 2006-2017 Nicolas Hainaux <nh.techn@gmail.com>

# This file is part of Mathmaker.

# Mathmaker is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# any later version.

# Mathmaker is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Mathmaker; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import random

from mathmakerlib import required
from mathmakerlib.calculus import Fraction, Number

from mathmaker.lib import shared
from mathmaker.lib.constants.latex import COLORED_QUESTION_MARK
from mathmaker.lib.core.root_calculus import Value
from mathmaker.lib.document.content import component
from mathmaker.lib.tools.wording import post_process


class sub_object(component.structure):

    def __init__(self, build_data, **options):
        super().setup("minimal", **options)
        super().setup("division", nb=build_data, **options)
        self.auto_hint = True
        if 'auto_hint' in options:
            if options['auto_hint'] == 'false':
                self.auto_hint = False
        self.transduration = 15
        if self.divisor > 9 and self.divisor % 10 != 0:
            self.transduration = 20

        if self.context == 'mini_problem':
            self.transduration = 25
            self.nb1 = self.dividend
            self.nb2 = self.divisor
            super().setup('mini_problem_wording', **options)

    def q(self, **options):
        if self.context == 'how_many_times':
            return _('How many times does {divisor} go into {dividend}?')\
                .format(divisor=self.divisor, dividend=self.dividend)
        elif self.context == 'mini_problem':
            return post_process(self.wording.format(**self.wording_format))
        elif self.context == 'one_nth_of':
            return _(r'How much is $\dfrac{{1}}{{{divisor}}}$ of {dividend}?')\
                .format(divisor=self.divisor, dividend=self.dividend)
        elif self.context == 'one_nth_times':
            if random.choice([True, False]):
                math_expr = r'$\dfrac{{1}}{{{divisor}}} \times {dividend}$'
            else:
                math_expr = r'${dividend} \times \dfrac{{1}}{{{divisor}}}$'
            math_expr = math_expr.format(divisor=self.divisor,
                                         dividend=self.dividend)
            return math_expr + f' = {COLORED_QUESTION_MARK}'

        else:
            auto_hint = ''
            sep = ' \\newline '
            if self.x_layout_variant == 'tabular':
                sep = r' \hfill '
            if (self.nb_source.startswith('decimal_and_10_100_1000')
                and self.auto_hint):
                if Number(self.dividend).fracdigits_nb() == 0:
                    hint_text = _('(as a decimal number)')
                    auto_hint = sep + r'\small{\textcolor{Silver!90!Black}{' \
                        + hint_text + r'}}'
                    required.options['xcolor'].add('svgnames')
            self.substitutable_question_mark = True
            return _('{math_expr} = {q_mark}{auto_hint}')\
                .format(
                math_expr=shared.machine.write_math_style2(self.quotient_str),
                q_mark=COLORED_QUESTION_MARK,
                auto_hint=auto_hint)

    def a(self, **options):
        # This is actually meant for self.preset == 'mental calculation'
        v = None
        if hasattr(self, 'hint'):
            v = Value(self.result, unit=self.hint)\
                .into_str(display_SI_unit=True)
        else:
            if isinstance(self.result, Fraction):
                v = shared.machine.write_math_style2(self.result.printed)
                deciv = self.result.evaluate()
                if deciv.fracdigits_nb() <= 2:
                    v += _(' (or {})').format(deciv.printed)
            else:
                v = Value(self.result).into_str()
        return v

    def js_a(self, **kwargs):
        if isinstance(self.result, Fraction):
            v = [self.result.uiprinted]
            deciv = self.result.evaluate()
            if deciv.fracdigits_nb() <= 5:
                v.append(deciv.printed)
        else:
            v = [Value(self.result).jsprinted]
        return v
