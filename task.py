import os


class Task:
    name: str = None

    ## Context table
    task_id: int = None
    execution_time: dict = {
        'executed': 0,
        'waited': 0,
        'estimated': None
    }
    priority: int = None
    token: int = None
    state: str = "NEW"      # NEW, READY, RUN, END
    ##

    arrival_time: int = None

    layers: list = None
    current_layer_idx: int = None

    out_dir: str = None
    log_paths: dict = None

    def __init__(self, 
                task_id=None, net_name=None, net_path=None, priority=None, arrival_time=None,
                out_parent_dir=None,
            ):
        self.name = net_name
        
        self.task_id = task_id
        self.priority = priority
        self.arrival_time = arrival_time

        self._set_output(out_parent_dir)
        self._load_from_csv(net_path)
    #

    def _set_output(self, parent_dir):
        self.out_dir = f"{parent_dir}/{self.name}"
        os.system(f"mkdir {self.out_dir}")

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
        self.layers, self.current_layer_idx = [], 0
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
                        layer_name=elems[0].strip().strip("'\""),
                        ifmap={ 'h': int(elems[1]), 'w': int(elems[2]) },
                        filt={ 'h': int(elems[3]), 'w': int(elems[4]) },
                        ch=int(elems[5]),
                        num_filt=int(elems[6]),
                        stride=int(elems[7]),

                        out_parent_dir=self.out_dir
                    ))
            #
        #
    #
    
    
    class Layer:
        name: str = None
        ifmap: dict = None
        filt: dict = None
        ch: int = None
        num_filt: int = None
        stride: int = None

        out_dir: str = None
        trace_paths: dict = None

        def __init__(self,
                    layer_name=None, 
                    ifmap=None, filt=None, ch=None,
                    num_filt=None,
                    stride=None,
                    
                    out_parent_dir=None,
                ):
            self.name = layer_name
            self.ifmap, self.filt, self.ch = ifmap, filt, ch
            self.num_filt = num_filt
            self.stride = stride

            self._set_output(out_parent_dir)
        #

        def _set_output(self, parent_dir):
            self.out_dir = f"{parent_dir}/{self.name}"
            os.system(f"mkdir {self.out_dir}")

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
    #
#