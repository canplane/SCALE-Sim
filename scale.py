import run_nets as r

import os
import time
import configparser as cp
from absl import flags, app

FLAGS = flags.FLAGS
# name of flag | default | explanation
flags.DEFINE_string('config', './configs/scale.cfg', 'file where we are getting our architechture from')
flags.DEFINE_string('network', './topologies/conv_nets/alexnet.csv', 'topology that we are reading')


class scale:
    def __init__(self, sweep=False, save=False):
        self.sweep = sweep
        self.save_space = save
    #

    def parse_config(self):
        config_filepath = FLAGS.config
        print(f'Using Architechture from {config_filepath}')

        config = cp.ConfigParser()
        config.read(config_filepath)

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

        ## Read network_presets
        self.topology_filepath = FLAGS.network
        self.net_name = self.topology_filepath.split('/')[-1].split('.')[0]
    #

    def run_scale(self):
        self.parse_config()

        if self.sweep == False:
            self.run_once()
        else:
            self.run_sweep()
    #

    def run_once(self):
        df_string = 'Output Stationary'  # os
        if self.dataflow == 'ws':
            df_string = 'Weight Stationary'
        elif self.dataflow == 'is':
            df_string = 'Input Stationary'

        print('====================================================')
        print('******************* SCALE SIM **********************')
        print('====================================================')
        print(f'Array Size: \t{self.array_h}x{self.array_w}')
        print(f'SRAM IFMAP: \t{self.ifmap_sram_sz_kb}')
        print(f'SRAM Filter: \t{self.filter_sram_sz_kb}')
        print(f'SRAM OFMAP: \t{self.ofmap_sram_sz_kb}')
        print(f'CSV filepath: \t{self.topology_filepath}')
        #print(f'Net name: \t{self.net_name}')
        print(f'Dataflow: \t{df_string}')
        print('====================================================')

        r.run_net(
                array_h=self.array_h, array_w=self.array_w,
                ifmap_sram_sz_kb=self.ifmap_sram_sz_kb, filter_sram_sz_kb=self.filter_sram_sz_kb, ofmap_sram_sz_kb=self.ofmap_sram_sz_kb,
                offset_list=[self.ifmap_offset, self.filter_offset, self.ofmap_offset],
                dataflow=self.dataflow,
                topology_filepath=self.topology_filepath, net_name=self.net_name,
            )
        self.cleanup()
        print('************ SCALE SIM Run Complete ****************')
    #

    def cleanup(self):
        if not os.path.exists('./outputs/'):
            os.system('mkdir ./outputs')

        if self.run_name == '':
            path = f'./outputs/{self.net_name}_{self.dataflow}'
        else:
            path = f'./outputs/{self.run_name}'

        if not os.path.exists(path):
            os.system(f'mkdir {path}')
        else:
            t = time.time()
            new_path = f'{path}_{t}'
            os.system(f'mv {path} {new_path}')
            os.system(f'mkdir {path}')

        os.system(f'mv *.csv {path}')
        os.system(f'mkdir {path}/layer_wise')
        os.system(f'mv {path}/*sram* {path}/layer_wise')
        os.system(f'mv {path}/*dram* {path}/layer_wise')

        if self.save_space == True:
            os.system(f'rm -rf {path}/layer_wise')
    #

    def run_sweep(self):
        all_dataflow_list = ['os', 'ws', 'is']
        all_arr_dim_list = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384]
        all_sram_sz_list = [256, 512, 1024]

        ## User defined list
        dataflow_list = all_dataflow_list[1:]
        arr_h_list = all_arr_dim_list[3:8]
        arr_w_list = all_arr_dim_list[3:8]
        #arr_w_list = list(reversed(arr_h_list))
        #

        for df in dataflow_list:
            self.dataflow = df

            for i in range(len(arr_h_list)):
                self.array_h = arr_h_list[i]
                self.array_w = arr_w_list[i]

                self.run_name = f'{self.net_name}_{df}_{self.array_h}x{self.array_w}'

                self.run_once()
    #
#

def main(argv):
    s = scale(save=False, sweep=False)
    s.run_scale()
#

if __name__ == '__main__':
  app.run(main)
