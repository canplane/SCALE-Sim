import trace_gen_wrapper as tg


def run_slot(arch, task, scheduler):
    print("")
    print(f"Network: \t{task.name}")
    print("----------------------------------------------------")
    
    first = True
    for i in range(task.current_layer_idx, len(task.layers)):
        ####
        if not first:
            scheduler.refresh()
        else:
            first = False
        ####

        layer = task.layers[i]

        print("Commencing run for " + layer.name)

        avg_bw_log, detail_log, sram_cycles, util = tg.gen_all_traces(arch, layer, scheduler)
        max_bw_log = tg.gen_max_bw_numbers(trace_paths=layer.trace_paths)
        
        with open(task.log_paths['avg_bw'], 'a') as f:
            f.write(f"{layer.name},\t{arch.sram_sz['ifmap']},\t{arch.sram_sz['filt']},\t{arch.sram_sz['ofmap']},\t" + avg_bw_log + '\n')
        with open(task.log_paths['max_bw'], 'a') as f:
            f.write(f"{layer.name},\t{arch.sram_sz['ifmap']},\t{arch.sram_sz['filt']},\t{arch.sram_sz['ofmap']},\t" + max_bw_log + '\n')
        with open(task.log_paths['detail'], 'a') as f:
            f.write(f"{layer.name},\t" + detail_log + '\n')
        with open(task.log_paths['cycles'], 'a') as f:
            f.write(f"{layer.name},\t{sram_cycles},\t{util}," + '\n')

        print("")
    #
    
    task.state = 'END'
#