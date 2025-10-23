# SPDX-License-Identifier: Apache-2.0
# Copyright 2024 Mike Schultz

from typing import Callable
from pjk.base import Source, Sink, ParsedToken
from pjk.common import ComponentFactory
from pjk.sinks.stdout import StdoutSink
from pjk.sinks.json_sink import JsonSink
from pjk.sinks.devnull import DevNullSink
from pjk.sinks.graph import GraphSink
from pjk.sinks.csv_sink import CSVSink
from pjk.sinks.tsv_sink import TSVSink
from pjk.integrations.ddb_sink import DDBSink
from pjk.sinks.expect import ExpectSink
from pjk.sinks.format_sink import FormatSink
from pjk.sinks.create_sink import CreateSink
from pjk.sinks.user_sink_factory import UserSinkFactory

COMPONENTS = {
        '-': StdoutSink,
        'devnull': DevNullSink,
        'graph': GraphSink,
        'ddb': DDBSink,
        'json': JsonSink,
        'csv': CSVSink,
        'tsv': TSVSink,
        'create': CreateSink
        }

class SinkFactory(ComponentFactory):
    def __init__(self):
        super().__init__(COMPONENTS)

    def get_comp_type_name(self):
        return 'sink'

    def create(self, token: str) -> Callable[[Source], Sink]:
        ptok = ParsedToken(token)

        # non-usage sink (bind incompatible)
        if ptok.pre_colon == 'expect':
            return ExpectSink(ptok, None)

        if ptok.pre_colon.endswith('.py'):
            sink = UserSinkFactory.create(ptok)
            if sink:
                return sink
            else:
                return None
        
        sink_cls = self.get_component_class(ptok.pre_colon)
        if sink_cls and not issubclass(sink_cls, FormatSink):
            usage = sink_cls.usage()
            usage.bind(ptok)
            return sink_cls(ptok, usage)
    
        return FormatSink.create(ptok, COMPONENTS)
