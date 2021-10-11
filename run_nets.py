import trace_gen_wrapper as tg

import os


def run_net(
            array_h=32, array_w=32,
            ifmap_sram_sz_kb=1, filter_sram_sz_kb=1, ofmap_sram_sz_kb=1,
            offset_list=[0, 10000000, 20000000],
            dataflow='os',
            topology_filepath='./topologies/yolo_v2.csv', net_name='yolo_v2',
            output_net_dir=''
        ):
    ifmap_sram_sz = 1024 * ifmap_sram_sz_kb
    filter_sram_sz = 1024 * filter_sram_sz_kb
    ofmap_sram_sz = 1024 * ofmap_sram_sz_kb

    topology_file = open(topology_filepath, 'r')

    os.system(f'mkdir {output_net_dir}')
    fname = f'{output_net_dir}/avg_bw.csv'; bw = open(fname, 'w')
    f2name = f'{output_net_dir}/max_bw.csv'; maxbw = open(f2name, 'w')
    f3name = f'{output_net_dir}/cycles.csv'; cycl = open(f3name, 'w')
    f4name = f'{output_net_dir}/detail.csv'; detail = open(f4name, 'w')

    bw.write('IFMAP SRAM Size,\tFilter SRAM Size,\tOFMAP SRAM Size,\tConv Layer Num,\tDRAM IFMAP Read BW,\tDRAM Filter Read BW,\tDRAM OFMAP Write BW,\tSRAM Read BW,\tSRAM OFMAP Write BW, \n')
    maxbw.write('IFMAP SRAM Size,\tFilter SRAM Size,\tOFMAP SRAM Size,\tConv Layer Num,\tMax DRAM IFMAP Read BW,\tMax DRAM Filter Read BW,\tMax DRAM OFMAP Write BW,\tMax SRAM Read BW,\tMax SRAM OFMAP Write BW,\n')
    cycl.write('Layer,\tCycles,\t% Utilization,\n')
    detailed_log = 'Layer,' + \
            '\tDRAM_IFMAP_start,\tDRAM_IFMAP_stop,\tDRAM_IFMAP_bytes,' + \
            '\tDRAM_Filter_start,\tDRAM_Filter_stop,\tDRAM_Filter_bytes,' + \
            '\tDRAM_OFMAP_start,\tDRAM_OFMAP_stop,\tDRAM_OFMAP_bytes,' + \
            '\tSRAM_read_start,\tSRAM_read_stop,\tSRAM_read_bytes,' + \
            '\tSRAM_write_start,\tSRAM_write_stop,\tSRAM_write_bytes,\n'

    detail.write(detailed_log)


    first = True
    for row in topology_file:
        if first:
            first = False
            continue
            
        elems = row.strip().split(',')
        
        # Do not continue if incomplete line
        #print(len(elems))
        if len(elems) < 9:
            continue

        layer_name = elems[0]
        output_layer_dir = f'{output_net_dir}/{layer_name}'
        os.system(f'mkdir {output_layer_dir}')

        print('')
        print(f'Commencing run for {layer_name}')

        ifmap_h, ifmap_w = int(elems[1]), int(elems[2])

        filt_h, filt_w = int(elems[3]), int(elems[4])

        num_channels = int(elems[5])
        num_filters = int(elems[6])

        strides = int(elems[7])
        
        ifmap_base, filter_base, ofmap_base = offset_list

        bw_log = f'{ifmap_sram_sz},\t{filter_sram_sz},\t{ofmap_sram_sz},\t{layer_name},\t'
        max_bw_log = bw_log
        detailed_log = f'{layer_name},\t'

        # 여기가 오래 걸림 (progress bar)
        bw_str, detailed_str, util, clk = \
                tg.gen_all_traces(
                        array_h=array_h, array_w=array_w,
                        ifmap_h=ifmap_h, ifmap_w=ifmap_w, num_channels=num_channels,
                        filt_h=filt_h, filt_w=filt_w, num_filt=num_filters,
                        strides=strides, dataflow=dataflow,

                        ifmap_sram_size=ifmap_sram_sz, filter_sram_size=filter_sram_sz, ofmap_sram_size=ofmap_sram_sz,
                        word_size_bytes=1,
                        ifmap_base=ifmap_base, filt_base=filter_base, ofmap_base=ofmap_base,
                        
                        sram_read_trace_file=f'{output_layer_dir}/sram_read.csv',
                        sram_write_trace_file=f'{output_layer_dir}/sram_write.csv',
                        dram_ifmap_trace_file=f'{output_layer_dir}/dram_ifmap_read.csv',
                        dram_filter_trace_file=f'{output_layer_dir}/dram_filter_read.csv',
                        dram_ofmap_trace_file=f'{output_layer_dir}/dram_ofmap_write.csv'
                    )

        bw_log += bw_str
        bw.write(bw_log + '\n')

        detailed_log += detailed_str
        detail.write(detailed_log + '\n')

        max_bw_log += \
                tg.gen_max_bw_numbers(
                        sram_read_trace_file=f'{output_layer_dir}/sram_read.csv',
                        sram_write_trace_file=f'{output_layer_dir}/sram_write.csv',
                        dram_ifmap_trace_file=f'{output_layer_dir}/dram_ifmap_read.csv',
                        dram_filter_trace_file=f'{output_layer_dir}/dram_filter_read.csv',
                        dram_ofmap_trace_file=f'{output_layer_dir}/dram_ofmap_write.csv'
                    )

        maxbw.write(max_bw_log + '\n')

        # Anand: This is not needed, sram_traffic() returns this
        #last_line = subprocess.check_output(['tail','-1', f'{net_name}_{layer_name}_sram_write.csv'] )
        #clk = str(last_line).split(',')[0]
        #clk = str(clk).split("'")[1]

        cycl.write(f'{layer_name},\t{clk},\t{util},\n')

    bw.close()
    maxbw.close()
    cycl.close()
    topology_file.close()
#

#if __name__ == '__main__':
#    sweep_parameter_space_fast()
