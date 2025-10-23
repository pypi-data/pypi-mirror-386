# SPDX-License-Identifier: Apache-2.0
# Copyright 2024 Mike Schultz

from pjk.base import Pipe, Usage, UsageError, ParsedToken, KeyedSource
from pjk.progress import papi

class FilterPipe(Pipe):
    arity = 2  # left = record stream, right = keyed source

    @classmethod
    def usage(cls):
        usage = Usage(
            name="filter",
            desc="Filters left records based on presence in right keyed source",
            component_class=cls
        )
        usage.def_arg("mode", "'+' to include matches, '-' to exclude matches",
                      valid_values={'+', '-'})
        usage.def_syntax("pjk <left_source> <map_source> [mapby:groupby]:<how>:<key> filter:<mode> <sink>")

        usage.def_example(expr_tokens=
        [
            "[{id:1}, {id:2}, {id:3}, {id:4}, {id:5}]",
            "[{id:1}, {id:3}, {id:5}]",
            'mapby:id',
            "filter:+"
        ],
        expect="[{id:1}, {id:3}, {id:5}]")

        usage.def_example(expr_tokens=
        [
            "[{id:1}, {id:2}, {id:3}, {id:4}, {id:5}]",
            "[{id:1}, {id:3}, {id:5}]",
            'mapby:id',
            "filter:-"
        ],
        expect="[{id:2}, {id:4}]")
        return usage

    def __init__(self, ptok: ParsedToken, usage: Usage):
        super().__init__(ptok)
        self.mode = usage.get_arg('mode')
        self.left = None
        self.right = None
        self.recs_in = papi.get_counter(self, None) # don't display
        self.recs_out = papi.get_percentage_counter(self, 'recs_out', self.recs_in)

    def reset(self):
        pass  # stateless

    def __iter__(self):
        if not isinstance(self.right, KeyedSource):
            raise UsageError("Right input to filter must be a KeyedSource")

        for record in self.left:
            self.recs_in.increment()
            match = self.right.lookup(record)
            exists = match is not None
            if (self.mode == "+" and exists) or (self.mode == "-" and not exists):
                self.recs_out.increment()
                yield record
