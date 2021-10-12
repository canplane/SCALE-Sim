import trace_gen_wrapper as tg

import os


def run_net(
            array={ 'h': 32, 'w': 32 },
            sram_sz={ 'ifmap': 1024, 'filt': 1024, 'ofmap': 1024 },
            base_addr={ 'ifmap': 0, 'filt': 10000000, 'ofmap': 20000000 },
            dataflow='os',

            net_path=None,
            output_net_dir=None
        ):

    with open(net_path, 'r') as net_file:
        os.system(f"mkdir {output_net_dir}")
        log_file = {
            'avg_bw': open(f"{output_net_dir}/avg_bw.csv", 'w'),
            'max_bw': open(f"{output_net_dir}/max_bw.csv", 'w'),
            'cycles': open(f"{output_net_dir}/cycles.csv", 'w'),
            'detail': open(f"{output_net_dir}/detail.csv", 'w'),
        }

        log_file['avg_bw'].write(
                'Layer,' + \
                '\tIFMAP SRAM Size,\tFilter SRAM Size,\tOFMAP SRAM Size,' + \
                '\tDRAM IFMAP Read BW,\tDRAM Filter Read BW,\tDRAM OFMAP Write BW,' + \
                '\tSRAM Read BW,\tSRAM OFMAP Write BW, \n'
            )
        log_file['max_bw'].write(
                'Layer,' + \
                '\tIFMAP SRAM Size,\tFilter SRAM Size,\tOFMAP SRAM Size,' + \
                '\tMax DRAM IFMAP Read BW,\tMax DRAM Filter Read BW,\tMax DRAM OFMAP Write BW,' + \
                '\tMax SRAM Read BW,\tMax SRAM OFMAP Write BW,\n'
            )
        log_file['cycles'].write('Layer,\tCycles,\t% Utilization,\n')
        log_file['detail'].write(
                'Layer,' + \
                '\tDRAM_IFMAP_start,\tDRAM_IFMAP_stop,\tDRAM_IFMAP_bytes,' + \
                '\tDRAM_Filter_start,\tDRAM_Filter_stop,\tDRAM_Filter_bytes,' + \
                '\tDRAM_OFMAP_start,\tDRAM_OFMAP_stop,\tDRAM_OFMAP_bytes,' + \
                '\tSRAM_read_start,\tSRAM_read_stop,\tSRAM_read_bytes,' + \
                '\tSRAM_write_start,\tSRAM_write_stop,\tSRAM_write_bytes,\n'
            )

        first = True
        for row in net_file:
            if first:
                first = False
                continue
                
            elems = row.strip().split(',')
            
            # Do not continue if incomplete line
            if len(elems) < 9:
                continue

            layer_name = elems[0]

            print('')
            print(f"Commencing run for {layer_name}")

            ifmap = { 'h': int(elems[1]), 'w': int(elems[2]) }
            filt = { 'h': int(elems[3]), 'w': int(elems[4]) }
            ch = int(elems[5])
            num_filt = int(elems[6])
            stride = int(elems[7])

            output_layer_dir = f"{output_net_dir}/{layer_name}"
            os.system(f"mkdir {output_layer_dir}")

            # layerwise
            trace_path = {
                'sram': {
                    'read': f"{output_layer_dir}/sram_read.csv",
                    'write': f"{output_layer_dir}/sram_write.csv"
                },
                'dram': {
                    'ifmap': f"{output_layer_dir}/dram_ifmap_read.csv",
                    'filt': f"{output_layer_dir}/dram_filt_read.csv",
                    'ofmap': f"{output_layer_dir}/dram_ofmap_write.csv"
                }
            }

            # 여기가 오래 걸림 (progress bar)
            avg_bw_log, detail_log, sram_cycles, util = \
                tg.gen_all_traces(
                        array=array,
                        sram_sz=sram_sz, 
                        dataflow=dataflow,

                        word_sz_bytes=1, 

                        ifmap=ifmap, filt=filt, ch=ch,
                        num_filt=num_filt,
                        stride=stride,

                        base_addr=base_addr,
                        trace_path=trace_path
                    )
            max_bw_log = tg.gen_max_bw_numbers(trace_path=trace_path)
            
            log_file['avg_bw'].write(f"{layer_name},\t{sram_sz['ifmap']},\t{sram_sz['filt']},\t{sram_sz['ofmap']},\t" + avg_bw_log + '\n')
            log_file['max_bw'].write(f"{layer_name},\t{sram_sz['ifmap']},\t{sram_sz['filt']},\t{sram_sz['ofmap']},\t" + max_bw_log + '\n')
            log_file['detail'].write(f"{layer_name},\t" + detail_log + '\n')
            log_file['cycles'].write(f"{layer_name},\t{sram_cycles},\t{util}," + '\n')
        #
        for k in log_file:
            log_file[k].close()
    #
    print('')
#