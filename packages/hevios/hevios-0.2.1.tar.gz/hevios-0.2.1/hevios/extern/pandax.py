import pandas as pd
import warnings

class Pandax:
    def __init__(self, log):
        self.log = log
    warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')
    def load_files(self,files,sheetname):
        dfs = []
        for file in files:
            dfs.append(pd.read_excel(file, sheet_name=sheetname ))
        return pd.concat(dfs)