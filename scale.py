import run_nets as r

import os
import datetime
import configparser as cp
import argparse


class scale:
    def __init__(self, c='', n=''):
        if c == '':
            c = './configs/google.cfg'
        self.config_path = c

        if n == '':
            n = './networks/conv_nets/alexnet.csv'
        self.net_path = n
    #

    def run_scale(self):
        self.parse_config()
        self.run_once()
    #

    def parse_config(self):
        print(f"Using Architechture from {self.config_path}")

        CONFIG = cp.ConfigParser()
        CONFIG.read(self.config_path)

        ## Read the run_name
        SECTION = 'general'

        self.run_name = CONFIG.get(SECTION, 'run_name')

        ## Read the architecture_presets
        SECTION = 'architecture_presets'

        self.array = {
            'h': int(CONFIG.get(SECTION, 'ArrayHeight')),
            'w': int(CONFIG.get(SECTION, 'ArrayWidth'))
        }
        self.sram_sz = {
            'ifmap': 1024 * int(CONFIG.get(SECTION, 'IfmapSramSzkB')),
            'filt': 1024 * int(CONFIG.get(SECTION, 'FilterSramSzkB')),
            'ofmap': 1024 * int(CONFIG.get(SECTION, 'OfmapSramSzkB'))
        }
        self.base_addr = {
            'ifmap': int(CONFIG.get(SECTION, 'IfmapOffset')),
            'filt': int(CONFIG.get(SECTION, 'FilterOffset')),
            'ofmap': int(CONFIG.get(SECTION, 'OfmapOffset'))
        }
        self.dataflow = CONFIG.get(SECTION, 'Dataflow')

        ## Set output path
        if not os.path.exists('./outputs/'):
            os.system('mkdir ./outputs')

        dt = datetime.datetime.now(datetime.timezone.utc)
        t_str = dt.astimezone().strftime('%Y%m%d_%H%M%S')

        self.output_conf_dir = f"./outputs/{self.run_name}-{t_str}"
        os.system(f"mkdir {self.output_conf_dir}")
    #

    def run_once(self):
        print("====================================================")
        print("******************* SCALE SIM **********************")
        print("====================================================")

        ## Print network_presets
        df_string = 'Output Stationary'  # os
        if self.dataflow == 'ws':
            df_string = 'Weight Stationary'
        elif self.dataflow == 'is':
            df_string = 'Input Stationary'

        print(f"Array Size: \t{self.array['h']}x{self.array['w']}")
        print(f"SRAM IFMAP: \t{self.sram_sz['ifmap']}")
        print(f"SRAM Filter: \t{self.sram_sz['filt']}")
        print(f"SRAM OFMAP: \t{self.sram_sz['ofmap']}")
        print(f"Dataflow: \t{df_string}")
        print("====================================================")

        ## Print network_presets
        net_name = self.net_path.split('/')[-1].split('.')[0]
        output_net_dir = f"{self.output_conf_dir}/{net_name}"

        print(f"CSV filepath: \t{self.net_path}")
        print(f"Net name: \t{net_name}")
        print("====================================================")

        r.run_net(
                array=self.array,
                sram_sz=self.sram_sz,
                base_addr=self.base_addr,
                dataflow=self.dataflow,
                
                net_path=self.net_path,
                output_net_dir=output_net_dir
            )
        print("************ SCALE SIM Run Complete ****************")
    #
#

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', metavar='filename', type=str,
                default='',
                help='path to the config file'
            )
    parser.add_argument('-n', metavar='filename', type=str,
                default='',
                help='path to the network file'
            )
    
    args = parser.parse_args()
    s = scale(c=args.c, n=args.n)
    s.run_scale()
#
