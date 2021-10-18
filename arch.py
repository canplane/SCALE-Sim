import configparser as cp


class Architecture:
    ## load from cfg
    def __init__(self, path):
        cfg = cp.ConfigParser()
        cfg.read(path)
        
        ## Read the run_name
        section = 'general'
        self.run_name = cfg.get(section, 'run_name')

        ## Read the architecture_presets
        section = 'architecture_presets'
        self.array = {
            'h': int(cfg.get(section, 'ArrayHeight')),
            'w': int(cfg.get(section, 'ArrayWidth'))
        }
        self.sram_sz = {
            'ifmap': 1024 * int(cfg.get(section, 'IfmapSramSzkB')),
            'filt': 1024 * int(cfg.get(section, 'FilterSramSzkB')),
            'ofmap': 1024 * int(cfg.get(section, 'OfmapSramSzkB'))
        }
        self.base_addr = {
            'ifmap': int(cfg.get(section, 'IfmapOffset')),
            'filt': int(cfg.get(section, 'FilterOffset')),
            'ofmap': int(cfg.get(section, 'OfmapOffset'))
        }
        self.dataflow = cfg.get(section, 'Dataflow')
    #
#
