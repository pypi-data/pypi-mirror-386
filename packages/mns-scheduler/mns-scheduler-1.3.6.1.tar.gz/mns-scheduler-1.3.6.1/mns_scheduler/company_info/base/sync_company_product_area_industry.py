import os
import sys

file_path = os.path.abspath(__file__)
end = file_path.index('mns') + 17
project_path = file_path[0:end]
sys.path.append(project_path)
import mns_common.component.em.em_stock_info_api as em_stock_info_api
import mns_common.component.common_service_fun_api as common_service_fun_api
import mns_common.api.ths.company.company_product_area_industry_index_query as company_product_area_industry_index_query
from loguru import logger
import pandas as pd
from mns_common.db.MongodbUtil import MongodbUtil
import mns_common.constant.db_name_constant as db_name_constant

mongodb_util = MongodbUtil('27017')


def sync_company_product_area_industry(symbol):
    real_time_quotes_all_stocks = em_stock_info_api.get_a_stock_info()
    real_time_quotes_all_stocks = common_service_fun_api.classify_symbol(real_time_quotes_all_stocks)
    if symbol is not None:
        real_time_quotes_all_stocks = real_time_quotes_all_stocks.loc[real_time_quotes_all_stocks['symbol'] == symbol]
    for stock_one in real_time_quotes_all_stocks.itertuples():
        try:
            symbol = stock_one.symbol
            classification = stock_one.classification
            if classification in ['H', 'K']:
                market = '17'
            elif classification in ['S', 'C']:
                market = '33'
            elif classification in ['X']:
                market = '151'

            company_product_area_industry_list = company_product_area_industry_index_query.company_product_area_industry(
                symbol, market)
            for company_one in company_product_area_industry_list:
                analysis_type = company_one['analysis_type']
                time_operate_index_item_list = company_one['time_operate_index_item_list']
                time_operate_index_item_df = pd.DataFrame(time_operate_index_item_list)
                time_operate_index_item_df['symbol'] = symbol
                time_operate_index_item_df['analysis_type'] = analysis_type

                time_operate_index_item_df['_id'] = symbol + '_' + time_operate_index_item_df['time']
                mongodb_util.save_mongo(time_operate_index_item_df, db_name_constant.COMPANY_BUSINESS_INFO)

        except BaseException as e:
            logger.error("同步经营数据:{},{}", stock_one.symbol, e)

    return None


if __name__ == '__main__':
    sync_company_product_area_industry('600805')
    sync_company_product_area_industry('002323')
    sync_company_product_area_industry('300901')
    sync_company_product_area_industry('603225')
    sync_company_product_area_industry('688039')
    sync_company_product_area_industry('600849')
    sync_company_product_area_industry('000508')
    sync_company_product_area_industry('810011')
    # sync_company_product_area_industry()
