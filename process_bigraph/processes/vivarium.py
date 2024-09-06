import numpy as np

from vivarium.processes.mass_adaptor import CountsToConcentration
from vivarium.processes.toy_gillespie import StochasticTSC, TRL, TrlConcentration, StochasticTscTrl
from bigraph_schema.protocols import local_lookup_module
from process_bigraph import Process, Step, ProcessTypes, Composite


def convert_apply(schema, updater):
    if updater == 'accumulate':
        return None
    elif updater == 'set':
        return 'set'
    elif updater == 'merge':
        return 'apply_merge'
    elif updater == 'null':
        return 'apply_constant'
    elif updater == 'nonnegative_accumulate':
        return 'nonnegative_accumulate'
    elif updater == 'dict_value':
        return 'apply_dictionary'
    else:
        # TODO: support other updater methods
        return None


def convert_default(default):
    if isinstance(default, int):
        return 'integer'

    elif isinstance(default, float):
        return 'float'

    elif isinstance(default, bool):
        return 'boolean'

    elif isinstance(default, str):
        return 'string'

    elif isinstance(default, np.array):
        shape = list(default.shape)
        index = tuple([0 for _ in shape])
        datum = default[index]
        return {
            '_type': 'array',
            '_shape': shape,
            '_data': convert_default(datum)}

    elif instance(default, list):
        element = 'any'
        if len(default) > 0:
            element = convert_default(
                default[0])

        return {
            '_type': 'list',
            '_element': element}

    # TODO: deal with units

    elif isinstance(default, dict):
        return 'tree[any]'


def convert_ports(core, vivarium_schema):
    schema = {}
    if isinstance(vivarium_schema, dict):
        if '_default' in vivarium_schema:
            default = vivarium_schema['_default']
            default_schema = convert_default(default)
            schema['_type'] = default_schema
            schema['_default'] = core.serialize(
                default_schema,
                default)

            if '_updater' in vivarium_schema:
                updater = vivarium_schema['_updater']
                apply_schema = convert_apply(updater)
                if apply_schema:
                    schema['_apply'] = apply_schema

        else:
            for key, subschema in vivarium_schema.keys():
                schema[key] = convert_ports(
                    core,
                    subschema)

        return schema

            # TODO: deal with emit?
            #   perhaps return an emit configuration?
    else:
        raise Exception(f'vivarium ports must be a dict, not {vivarium_schema}')


class VivariumProcess(Process):
    config_schema = {
        'address': 'string',
        'parameters': 'tree[any]'}


    def __init__(self, config, core=None):
        super().__init__(config, core)

        self.process_class = local_lookup_module(
            self.config['address'])

        self.instance = self.process_class(
            parameters=self.config['parameters'])

        self.ports_schema = convert_ports(
            self.instance.ports_schema())


    def inputs(self):
        return self.ports_schema


    def outputs(self):
        return self.ports_schema
