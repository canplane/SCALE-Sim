from arch import Architecture
from context_table import ContextTable
import prema

import run_nets

import os
import datetime
import argparse


def t_str():
    dt = datetime.datetime.now(datetime.timezone.utc)
    return dt.astimezone().strftime('%Y%m%d_%H%M%S')

def df_string(df_str):
    ret = 'Output Stationary'  # os
    if df_str == 'ws':
        ret = 'Weight Stationary'
    elif df_str == 'is':
        ret = 'Input Stationary'
    return ret


class Scale:
    def __init__(self, a='', t=''):
        if a == '':
            a = './configs/google.cfg'
        if t == '':
            t = './task_list.csv'

        #print(f"Using Architecture from {self.config_path}")
        self.arch = Architecture(a)
        self.context_table = ContextTable(t)
    #

    def run(self):
        ## Set output directory
        if not os.path.exists('./outputs/'):
            os.system('mkdir ./outputs')
        self.arch.output_dir = f"./outputs/{self.arch.run_name}-{t_str()}"
        os.system(f"mkdir {self.arch.output_dir}")


        print("====================================================")
        print("******************* SCALE SIM **********************")
        print("====================================================")
        print(f"Array Size: \t{self.arch.array['h']}x{self.arch.array['w']}")
        print(f"SRAM IFMAP: \t{self.arch.sram_sz['ifmap']}")
        print(f"SRAM Filter: \t{self.arch.sram_sz['filt']}")
        print(f"SRAM OFMAP: \t{self.arch.sram_sz['ofmap']}")
        print(f"Dataflow: \t{df_string()}")
        print("====================================================")

        TIME_QUOTA = 0.25
        while True:
            next_task = prema.select(self.context_table)
            if next_task == None:
                break
            run_nets.run_slot(self.arch, next_task, TIME_QUOTA)
        
        print("************ SCALE SIM Run Complete ****************")
    #
#


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', metavar='filename', type=str,
                default='',
                help='path to the architecture config file (.cfg)'
            )
    parser.add_argument('-t', metavar='filename', type=str,
                default='',
                help='path to the task config file (.csv)'
            )
    
    args = parser.parse_args()
    s = Scale(a=args.a, t=args.t)
    s.run()
#
