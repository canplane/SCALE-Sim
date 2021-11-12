import os

from scale_error import *


class Task:
    def __init__(self, 
                arch=None,
                task_id=None, net_name=None, net_path=None,

                priority=None,
                arrival_time=None,

                color=None
            ):
        self.arch = arch
        self.name = net_name
        
        ## Context table
        self.task_id = task_id

        self.executed_time, self.executed_time_per_layer = 0, []
        self.executed_timeline = []
        self.waited_time, self.waited_time_per_layer = 0, []
        self.waited_timeline = []
        # used in PREMA
        self.estimated_time, self.estimated_time_per_layer = 0, []

        self.priority = priority
        self.token = priority
        self.state = 'NEW'  # NEW, READY, RUN, END

        self.arrival_time = arrival_time

        ## Layers
        self.layers = []
        self.current_layer_idx, self.last_executed_layer_idx = 0, -1

        ## Misc
        self.color = color

        self._set_output(f"{self.arch.out_dir}/{self.name}")
        self._load_from_csv(net_path)
    #

    def _set_output(self, out_dir):
        self.out_dir = out_dir
        os.mkdir(self.out_dir)  # 에러 나면 task list 파일에서 task 이름 중복되었는지 살필 것

        self.log_paths = {
            'avg_bw': f"{self.out_dir}/avg_bw.csv",
            'max_bw': f"{self.out_dir}/max_bw.csv",
            'cycles': f"{self.out_dir}/cycles.csv",
            'detail': f"{self.out_dir}/detail.csv",
        }
        with open(self.log_paths['avg_bw'], 'w') as f:
            f.write(
                    'Layer,' + \
                    '\tIFMAP SRAM Size,\tFilter SRAM Size,\tOFMAP SRAM Size,' + \
                    '\tDRAM IFMAP Read BW,\tDRAM Filter Read BW,\tDRAM OFMAP Write BW,' + \
                    '\tSRAM Read BW,\tSRAM OFMAP Write BW, \n'
                )
        with open(self.log_paths['max_bw'], 'w') as f:
            f.write(
                    'Layer,' + \
                    '\tIFMAP SRAM Size,\tFilter SRAM Size,\tOFMAP SRAM Size,' + \
                    '\tMax DRAM IFMAP Read BW,\tMax DRAM Filter Read BW,\tMax DRAM OFMAP Write BW,' + \
                    '\tMax SRAM Read BW,\tMax SRAM OFMAP Write BW,\n'
                )
        with open(self.log_paths['cycles'], 'w') as f:
            f.write('Layer,\tCycles,\t% Utilization,\n')
        with open(self.log_paths['detail'], 'w') as f:
            f.write(
                    'Layer,' + \
                    '\tDRAM_IFMAP_start,\tDRAM_IFMAP_stop,\tDRAM_IFMAP_bytes,' + \
                    '\tDRAM_Filter_start,\tDRAM_Filter_stop,\tDRAM_Filter_bytes,' + \
                    '\tDRAM_OFMAP_start,\tDRAM_OFMAP_stop,\tDRAM_OFMAP_bytes,' + \
                    '\tSRAM_read_start,\tSRAM_read_stop,\tSRAM_read_bytes,' + \
                    '\tSRAM_write_start,\tSRAM_write_stop,\tSRAM_write_bytes,\n'
                )
    #

    def _load_from_csv(self, path):
        with open(path, 'r') as f:
            first = True
            for row in f:
                if first:
                    first = False
                    continue
                elems = row.strip().split(',')
                if len(elems) < 9:      # Do not continue if incomplete line
                    continue

                self.layers.append(self.Layer(
                        parent=self,
                        nth_layer=len(self.layers),
                        layer_name=elems[0].strip().strip("'\""),
                        ifmap={ 'h': int(elems[1]), 'w': int(elems[2]) },
                        filt={ 'h': int(elems[3]), 'w': int(elems[4]) },
                        ch=int(elems[5]),
                        num_filt=int(elems[6]),
                        stride=int(elems[7]),
                    ))
                self.executed_time_per_layer.append(0)
                self.executed_timeline.append([])
                self.waited_time_per_layer.append(0)
                self.waited_timeline.append([])
            #
        #
    #
    
    
    class Layer:
        def __init__(self,
                    parent=None,
                    nth_layer=None, layer_name=None,

                    ifmap=None, filt=None, ch=None,
                    num_filt=None,
                    stride=None,
                ):
            self.parent = parent    # task
            self.nth_layer = nth_layer
            self.name = layer_name

            self.ifmap, self.filt, self.ch = ifmap, filt, ch
            self.num_filt = num_filt
            self.stride = stride

            ## Context
            self._context_vars = {}

            self._set_output()
        #

        def _set_output(self):
            self.out_dir = f"{self.parent.out_dir}/{self.name}"
            os.mkdir(self.out_dir)  # 에러 나면 network 파일에서 레이어 이름 중복되었는지 살필 것

            self.trace_paths = {
                'sram': {
                    'read': f"{self.out_dir}/sram_read.csv",
                    'write': f"{self.out_dir}/sram_write.csv"
                },
                'dram': {
                    'ifmap': f"{self.out_dir}/dram_ifmap_read.csv",
                    'filt': f"{self.out_dir}/dram_filt_read.csv",
                    'ofmap': f"{self.out_dir}/dram_ofmap_write.csv"
                }
            }
        

        # Context variables
        def load_var(self, key: str, init=None):
            if key not in self._context_vars:
                if init == None:
                    raise SCALE_Error("Variable not exists and initial value is not set")

                self._context_vars[key] = init
            return self._context_vars[key]

        def store_var(self, dic: dict):
            for k in dic:
                self._context_vars[k] = dic[k]

        def clear_var(self, li: list):
            for e in li:
                del self._context_vars[e]

        def is_empty_var(self, key: str) -> bool:
            return key not in self._context_vars
        def is_no_vars(self) -> bool:
            return not bool(self._context_vars)
    #
#