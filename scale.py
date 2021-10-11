import run_nets as r

import os
import datetime
import configparser as cp
import argparse


class scale:
    def __init__(self, config='', topology=''):
        if config == '':
            config = './configs/google.cfg'
        self.config_path = config

        if topology == '':
            topology = './topologies/conv_nets/alexnet_part.csv'
        self.topology_path = topology
    #

    def run_scale(self):
        self.parse_config()
        self.run_once()
    #

    def parse_config(self):
        print(f'Using Architechture from {self.config_path}')

        config = cp.ConfigParser()
        config.read(self.config_path)

        ## Read the run_name
        section = 'general'

        self.run_name = config.get(section, 'run_name')

        ## Read the architecture_presets
        section = 'architecture_presets'

        self.array_h = int(config.get(section, 'ArrayHeight'))
        self.array_w = int(config.get(section, 'ArrayWidth'))

        self.ifmap_sram_sz_kb = int(config.get(section, 'IfmapSramSzkB'))
        self.filter_sram_sz_kb = int(config.get(section, 'FilterSramSzkB'))
        self.ofmap_sram_sz_kb = int(config.get(section, 'OfmapSramSzkB'))
        
        self.ifmap_offset = int(config.get(section, 'IfmapOffset'))
        self.filter_offset = int(config.get(section, 'FilterOffset'))
        self.ofmap_offset = int(config.get(section, 'OfmapOffset'))

        self.dataflow = config.get(section, 'Dataflow')

        ## Set output path
        if not os.path.exists('./outputs/'):
            os.system('mkdir ./outputs')

        dt = datetime.datetime.now(datetime.timezone.utc)
        t_str = dt.astimezone().strftime('%Y%m%d_%H%M%S')

        self.output_conf_dir = f'./outputs/{self.run_name}-{t_str}'
        os.system(f'mkdir {self.output_conf_dir}')
    #

    def run_once(self):
        print('====================================================')
        print('******************* SCALE SIM **********************')
        print('====================================================')

        ## Print network_presets
        df_string = 'Output Stationary'  # os
        if self.dataflow == 'ws':
            df_string = 'Weight Stationary'
        elif self.dataflow == 'is':
            df_string = 'Input Stationary'

        print(f'Array Size: \t{self.array_h}x{self.array_w}')
        print(f'SRAM IFMAP: \t{self.ifmap_sram_sz_kb}')
        print(f'SRAM Filter: \t{self.filter_sram_sz_kb}')
        print(f'SRAM OFMAP: \t{self.ofmap_sram_sz_kb}')
        print(f'Dataflow: \t{df_string}')
        print('====================================================')

        ## Print network_presets
        net_name = self.topology_path.split('/')[-1].split('.')[0]
        output_net_dir = f'{self.output_conf_dir}/{net_name}'

        print(f'CSV filepath: \t{self.topology_path}')
        print(f'Net name: \t{net_name}')
        print('====================================================')

        r.run_net(
                array_h=self.array_h, array_w=self.array_w,
                ifmap_sram_sz_kb=self.ifmap_sram_sz_kb, filter_sram_sz_kb=self.filter_sram_sz_kb, ofmap_sram_sz_kb=self.ofmap_sram_sz_kb,
                offset_list=[self.ifmap_offset, self.filter_offset, self.ofmap_offset],
                dataflow=self.dataflow,
                topology_filepath=self.topology_path, net_name=net_name,
                output_net_dir=output_net_dir
            )
        print('************ SCALE SIM Run Complete ****************')
    #
#

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', metavar='filename', type=str,
                default='',
                help='path to the config file'
            )
    parser.add_argument('-t', metavar='filename', type=str,
                default='',
                help='path to the topology file'
            )
    
    args = parser.parse_args()
    config, topology = args.c, args.t
    s = scale(config=config, topology=topology)
    s.run_scale()
#
