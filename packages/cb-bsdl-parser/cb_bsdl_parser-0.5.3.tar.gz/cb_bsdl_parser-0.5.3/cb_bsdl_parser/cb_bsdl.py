from collections import OrderedDict
from antlr4 import *
from cb_bsdl_parser.CBBsdlLexer import CBBsdlLexer
from cb_bsdl_parser.CBBsdlParser import CBBsdlParser

import logging
log = logging.getLogger(__name__)

class CBBsdl():
    def __init__(self, bsdl_file, check_bsr=True, verbose=False):

        self.bsdl_file = bsdl_file
        self.check_bsr = check_bsr
        self.verbose = verbose

        with open(self.bsdl_file, 'r') as file:
            input_text = file.read()

        lexer = CBBsdlLexer(InputStream(input_text))
        stream = CommonTokenStream(lexer)
        parser = CBBsdlParser(stream)

        self.tree = parser.bsdl()


        if self.check_entity_name() != True:
            raise ValueError("Entity name is not present or malformed in the BSDL content.")

        if self.check_bsr:
            if self.check_bsr_length() != True:
                raise ValueError("BSR length is not present or inconsistent in the BSDL content.")

        self.build_ports_content()
        self.build_pin_map_content()
        self.build_bsr_content()
        self.compile_bsr_ctrl_cells()


    def check_entity_name(self):
        """Checks if the entity name is present in the BSDL content."""
        if len(self.tree.entity().entity_name()) != 2:
            raise ValueError("Entity name is not present or malformed in the BSDL content.")

        if self.tree.entity().entity_name()[0].getText() != \
            self.tree.entity().entity_name()[1].getText():
            raise ValueError("Entity name is not correct the BSDL content.")

        return True

    def check_bsr_length(self):
        """Checks if the BSR length is present in the BSDL content."""


        attr_bsr_len0 = self.get_bsr_len()
        attr_bsr_len1 = len(self.tree.entity().body().attr_bsr()[0].bsr_def())

        if self.verbose:
            log.debug(f'attr_bsr_len0: {attr_bsr_len0}, attr_bsr_len1: {attr_bsr_len1}')

        if attr_bsr_len0 != attr_bsr_len1:
            raise ValueError("BSR length not consistent.")

        return True


    def get_entity_name(self):
        """Extracts the entity name from the BSDL content."""
        return self.tree.entity().entity_name()[0].getText()

    def get_physical_pin_map(self):
        """Extracts the physical pin map from the BSDL content."""
        return self.tree.entity().body().generic_phys_pin_map()[0].phys_pin_map_name().getText()

    def get_bsr_len(self):
        """Extracts the BSR length from the BSDL content."""
        return int(self.tree.entity().body().attr_bsr_len()[0].bsr_len().getText())

    def ports_add(self, port_name_str, port_function, port_type):
        self.ports[port_name_str] = {
            'function': port_function,
            'type': port_type
        }

    def build_ports_content(self):
        """Builds the port declaration content from the BSDL tree."""

        self.ports = {}

        for port_def in self.tree.entity().body().port_dec()[0].port_def():
            for port_name in port_def.port_name():
                if port_def.port_type().getText() == 'bit':
                    port_name_str = port_name.getText()
                    port_function = port_def.port_function().getText()
                    port_type = port_def.port_type().getText()

                    self.ports_add(port_name_str, port_function, port_type)

                elif 'bit_vector' in port_def.port_type().getText():
                    bit_0 = int(port_def.port_type().bit_vector().bit_range().INTEGER()[0].getText())
                    bit_1 = int(port_def.port_type().bit_vector().bit_range().INTEGER()[1].getText())
                    for bit in range(bit_0, bit_1 + 1):
                        port_name_str = f'{port_name.getText()}.{bit}'
                        port_function = port_def.port_function().getText()
                        port_type = 'bit'

                        self.ports_add(port_name_str, port_function, port_type)

                else:
                    log.error(f'Port Type {port_def.port_type().getText()} not supported yet')
                    raise NotImplementedError

    def get_ports(self):
        """Returns the port declaration content."""
        return self.ports

    def build_pin_map_content(self):
        """Builds the pin map content from the BSDL tree."""

        self.pin_map = {}

        pin_map_len = len(self.tree.entity().body().pin_map()[0].pin_def())

        for i in range(pin_map_len):
            port_name = self.tree.entity().body().pin_map()[0].pin_def()[i].port_name().getText()

            if self.tree.entity().body().pin_map()[0].pin_def()[i].pin_num() is not None:
                pin_num = self.tree.entity().body().pin_map()[0].pin_def()[i].pin_num().getText()
                self.pin_map[pin_num] = port_name
            else:
                pin_num_arr_len = len(self.tree.entity().body().pin_map()[0].pin_def()[i].pin_num_arr().pin_num())
                for j in range(pin_num_arr_len):
                    pin_num = self.tree.entity().body().pin_map()[0].pin_def()[i].pin_num_arr().pin_num()[j].getText()
                    self.pin_map[pin_num] = f'{port_name}.{j}'


    def get_pin_map(self):
        """Returns the pin map content."""
        return self.pin_map

    def build_bsr_content(self):
        """Builds the BSR content from the BSDL tree."""

        self.bsr = {}

        for i in range(self.get_bsr_len()):
            bsr_def = self.tree.entity().body().attr_bsr()[0].bsr_def()[i].getText()

            data_cell = int(self.tree.entity().body().attr_bsr()[0].bsr_def()[i].data_cell().getText())

            if self.tree.entity().body().attr_bsr()[0].bsr_def()[i].bsr_cell0() is not None:
                cell_type = self.tree.entity().body().attr_bsr()[0].bsr_def()[i].bsr_cell0().cell_type().getText()
                if self.tree.entity().body().attr_bsr()[0].bsr_def()[i].bsr_cell0().cell_desc() is not None:
                    cell_desc = self.tree.entity().body().attr_bsr()[0].bsr_def()[i].bsr_cell0().cell_desc().getText()
                else:
                    cell_desc = '*'

                cell_func = self.tree.entity().body().attr_bsr()[0].bsr_def()[i].bsr_cell0().cell_func().getText()
                cell_val = self.tree.entity().body().attr_bsr()[0].bsr_def()[i].bsr_cell0().cell_val().getText()
                ctrl_cell = 0
                disval = 0

            elif self.tree.entity().body().attr_bsr()[0].bsr_def()[i].bsr_cell1() is not None:
                cell_type = self.tree.entity().body().attr_bsr()[0].bsr_def()[i].bsr_cell1().cell_type().getText()
                if self.tree.entity().body().attr_bsr()[0].bsr_def()[i].bsr_cell1().cell_desc() is not None:
                    cell_desc = self.tree.entity().body().attr_bsr()[0].bsr_def()[i].bsr_cell1().cell_desc().getText()
                else:
                    cell_desc = '*'

                cell_func = self.tree.entity().body().attr_bsr()[0].bsr_def()[i].bsr_cell1().cell_func().getText()
                cell_val = self.tree.entity().body().attr_bsr()[0].bsr_def()[i].bsr_cell1().cell_val().getText()
                ctrl_cell = int(self.tree.entity().body().attr_bsr()[0].bsr_def()[i].bsr_cell1().ctrl_cell().getText())
                disval = int(self.tree.entity().body().attr_bsr()[0].bsr_def()[i].bsr_cell1().disval().getText())

            else:
                data_cell = 0
                cell_type = 'undef'
                cell_desc = 'undef'
                cell_func = 'undef'
                cell_val = 'undef'
                ctrl_cell = 0
                disval = 0


            bsr_cell = {
                'data_cell': data_cell,
                'cell_type': cell_type,
                'cell_desc': cell_desc,
                'cell_func': cell_func,
                'cell_val': cell_val,
                'ctrl_cell': ctrl_cell,
                'disval': disval
            }


            if cell_desc == '*':
                cell_desc = f'cell_{data_cell}'

            if cell_func.upper() in ['INPUT', 'OBSERVE_ONLY']:
                key_a = 'in'
            elif cell_func.upper() in ['OUTPUT', 'OUTPUT2', 'OUTPUT3']:
                key_a = 'out'
            elif cell_func.upper() in ['CONTROL']:
                key_a = 'ctrl'
            elif cell_func.upper() in ['INTERNAL']:
                key_a = ''
            else:
                key_a = ''
                log.warn(f'Cell_func {cell_func} not recognized for cell_desc {cell_desc}')

            if key_a != '':
                key = f'{cell_desc}_{key_a}'
            else:
                key = cell_desc


            self.bsr[key] = bsr_cell


    def compile_bsr_ctrl_cells(self):
        """Compiles control cells from the BSR content."""

        for i in range(len(self.bsr)):
            cell_desc = list(self.bsr.keys())[i]
            cell = self.bsr[cell_desc]

            ctrl_cell_used = 0

            if cell_desc.endswith('_out'):
                if self.verbose:
                    log.debug(f'Control cell found: {cell_desc}, data_cell: {cell['data_cell']} ctrl_cell: {cell['ctrl_cell']}   ', end='')

                for key, ccell in self.bsr.items():
                    if ccell['ctrl_cell'] != '' and int(ccell['ctrl_cell']) == int(cell['ctrl_cell']):
                        ctrl_cell_used += 1
                        if self.verbose:
                            log.debug(f'  {key} has ctrl_cell {ccell['ctrl_cell']}')

                if ctrl_cell_used == 1:
                    new_key_ctrl_cell = f'{cell['cell_desc']}_ctrl'
                    old_key_ctrl_cell = f'cell_{cell['ctrl_cell']}_ctrl'



                    if self.verbose:
                        log.debug(f'modify key: {old_key_ctrl_cell} -> {new_key_ctrl_cell}  ')

                    if int(cell['data_cell']) != int(cell['ctrl_cell']):
                        self.bsr[new_key_ctrl_cell] = self.bsr.pop(old_key_ctrl_cell)
                    else:
                        log.warning(f'Warning: {cell['cell_desc']} does not have a separate ctrl_cell')


        # Sort the BSR content by data_cell
        self.bsr = OrderedDict(sorted(self.bsr.items(), key=lambda t: t[1]['data_cell']))

    def get_bsr(self):
        """Returns the BSR content."""
        return self.bsr


    def print_bsr_table(self):
        """Prints the BSDL BSR content information."""
        log.info(f'BSDL file: {self.bsdl_file}')
        log.info(f'Entity name: {self.get_entity_name()}')
        log.info(f'Physical pin map: {self.get_physical_pin_map()}')
        log.info(f'BSR length: {self.get_bsr_len()}')
        log.info('BSR content:')
        for bsr_cell in self.bsr.keys():

            if self.bsr[bsr_cell]['cell_func'] != 'internal':
                log.info(f'  {bsr_cell:10s} '\
                         f'{self.bsr[bsr_cell]['data_cell']:3d}   '\
                         f'type: {self.bsr[bsr_cell]['cell_type']:4s}   '\
                         f'desc: {self.bsr[bsr_cell]['cell_desc']:6s}   '\
                         f'func: {self.bsr[bsr_cell]['cell_func']:9s}   '\
                         f'val: {self.bsr[bsr_cell]['cell_val']:1s}   '\
                         f'ctrl_cell: {self.bsr[bsr_cell]['ctrl_cell']:3d}')


    def get_bsr_data_cell(self, bsr_cell):
        """Returns the cell number for a given BSR cell."""
        if bsr_cell in self.bsr:
            return self.bsr[bsr_cell]['data_cell']
        else:
            raise ValueError(f"BSR cell {bsr_cell} not found in BSR content.")

    def get_bsr_cell_type(self, bsr_cell):
        """Returns the cell type for a given BSR cell."""
        if bsr_cell in self.bsr:
            return self.bsr[bsr_cell]['cell_type']
        else:
            raise ValueError(f"BSR cell {bsr_cell} not found in BSR content.")

    def get_bsr_cell_desc(self, bsr_cell):
        """Returns the cell description for a given BSR cell."""
        if bsr_cell in self.bsr:
            return self.bsr[bsr_cell]['cell_desc']
        else:
            raise ValueError(f"BSR cell {bsr_cell} not found in BSR content.")

    def get_bsr_cell_func(self, bsr_cell):
        """Returns the cell function for a given BSR cell."""
        if bsr_cell in self.bsr:
            return self.bsr[bsr_cell]['cell_func']
        else:
            raise ValueError(f"BSR cell {bsr_cell} not found in BSR content.")

    def get_bsr_cell_val(self, bsr_cell):
        """Returns the cell value for a given BSR cell."""
        if bsr_cell in self.bsr:
            return self.bsr[bsr_cell]['cell_val']
        else:
            raise ValueError(f"BSR cell {bsr_cell} not found in BSR content.")

    def get_bsr_ctrl_cell(self, bsr_cell):
        """Returns the control cell for a given BSR cell."""
        if bsr_cell in self.bsr:
            return self.bsr[bsr_cell]['ctrl_cell']
        else:
            raise ValueError(f"BSR cell {bsr_cell} not found in BSR content.")

    def get_bsr_disval(self, bsr_cell):
        """Returns the disable value for a given BSR cell."""
        if bsr_cell in self.bsr:
            return self.bsr[bsr_cell]['disval']
        else:
            raise ValueError(f"BSR cell {bsr_cell} not found in BSR content.")