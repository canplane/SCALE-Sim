import trace_gen_wrapper as tg

from misc import set_style, set_color


def run_slot(arch, task, scheduler):
    print("")
    print(f"Network: \t{set_style(set_color(task.name, key=task.color), key='BOLD')}")
    print("----------------------------------------------------")
    
    while task.current_layer_idx < len(task.layers):
        layer = task.layers[task.current_layer_idx]

        print(f"Commencing run for {set_color(layer.name, key=task.color)}")

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

        ####
        task.current_layer_idx += 1
        if task.current_layer_idx < len(task.layers):
            scheduler.refresh()
        ####

        print("")
    #
    task.state = 'END'
#