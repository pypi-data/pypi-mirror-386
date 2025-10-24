"""
可以直接在此写测试脚本。而无须每次都打包和安装finosdk。
注意，运行此测试的python 环境不能是finosdk的安装环境。
如果finosdk安装在虚拟环境中，建议uninstall finosdk，再运行此测试脚本。
"""
import pandas as pd
from datetime import datetime
from pandas import Timestamp
from finosdk import APIError
import finosdk as fino

fino.init(base_url="http://127.0.0.1:8003/data_api")

# df = fino.get_fac_position(
#     start_date="20250102",               
#     end_date="20250130",                 
#     code_list=["A", "AL"],
#     factor=[],
#     section=[]
# )
# print(df)


# df = fino.get_fac_trend(
#     start_date='20250102',               
#     end_date='20250205',                 
#     code_list=["A"],
#     factor=[],
#     section=['农产品']
# )
# print(df)


# df_test_data = fino.get_csft_test_data(
#     start_date="20250829",
#     end_date="20250912",
#     factor=[],
# )
# print(df_test_data)

# df_test_perf =  fino.get_csft_test_perf(
#     start_date="20250829",
#     end_date="20250912",
#     factor=[],
# )
# print(df_test_perf.head())


# df_test_dcp =  fino.get_csft_test_dcp(
#     start_date="20250503",
#     end_date="20250510",
#     factor=[],
# )
# print(df_test_dcp.head())

# df_bkt_data = fino.get_csft_bkt_data(
#     start_date="20250829",
#     end_date="20250912",
#     factor=[],
# )
# print(df_bkt_data.head())

# df_bkt_perf =  fino.get_csft_bkt_perf(
#     start_date="20250829",
#     end_date="20250912",
#     factor=[],
# )
# print(df_bkt_perf.head())


df_bkt_dcp =  fino.get_csft_bkt_dcp(
    start_date="20250901",
    end_date="20250912",
    factor=[],
)
print(df_bkt_dcp.head(30))


