#  Copyright Femtosense 2024
#
#  By using this software package, you agree to abide by the terms and conditions
#  in the license agreement found at https://femtosense.ai/legal/eula/
#

import os

B_DATA_ADDR = 16
B_CONF_ADDR = 17
CORE_DATA_MEM_BANKS = 8
CORE_TABLE_MEM_BANKS = 4
B_DATA_WORD = 64
B_TABLE_WORD = 16
DATA_MEM_BANK_WORDS = 8192
TABLE_MEM_BANK_WORDS = 2048
MAX_THREADS = 64
MAX_INSTR = 4096
B_PC = 13
B_INSTR = 64
B_SB = 11
B_TIDX = 6
B_RQ = 2**B_TIDX

ISA = 1.3  # default
if os.getenv("FS_HW_ISA") == "spu1p3v1.dat":
    ISA = 1.3
elif os.getenv("FS_HW_ISA") == "spu1p2v1.dat":
    ISA = 1.2
