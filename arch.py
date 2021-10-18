import os
import datetime
import configparser as cp


def _t_str():
    dt = datetime.datetime.now(datetime.timezone.utc)
    return dt.astimezone().strftime("%Y%m%d_%H%M%S")


class Architecture:
    name: str = None
    array: dict = None
    sram_sz: dict = None
    base_addr: dict = None
    dataflow: str = None

    out_dir: str = None

    def __init__(self, cfg_path=None):
        self._load_from_cfg(cfg_path)

        if not os.path.exists("./outputs/"):
            os.system("mkdir ./outputs")
        ####
        os.system("rm -rf ./outputs/*")
        ####
        self.out_dir = f"./outputs/{self.name}-{_t_str()}"
        os.system(f"mkdir {self.out_dir}")
    #

    def _load_from_cfg(self, path):
        cfg = cp.ConfigParser()
        cfg.read(path)
        
        ## Read the run_name
        section = 'general'
        self.name = cfg.get(section, 'run_name').strip().strip("'\"")

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
