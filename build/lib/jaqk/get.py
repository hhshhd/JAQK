import requests
from pyquery import PyQuery as pq
import pandas as _pd
# import re
import time
import datetime as _dtime
import os as _os

# asynchronous coroutine
import asyncio
import aiohttp

# memory cleaning
import gc as _gc

# Internal modules
from .basics.stocks import stock_list

from .getters.get_holders import get_major_holders, get_top_institutional_and_mutual_fund_holders
from .getters.get_financials import get_stats, get_statements, get_reports
from .getters.get_profile import get_executives, get_description
from .getters.get_analysis import get_analysis
from .getters.get_summary import get_summary

from .operations.Save import save_file, save_dfs, save_analysis  # helpful operations
from .operations.Folder import create_folder, exist
from .operations.Open import open_file, open_general

global main_path
main_path = _os.path.abspath(_os.path.dirname(__file__))


async def getter(url, timeout=20, error=True, proxy=None, cnt=0):
    # main get function for all the website getter
    # it would support proxies, multiple user agent
    """
    url - target url
    timeout - default 10 second (recommend >10)
    error - Recursive error handler
    proxy - connect to proxies, should be a dic containing both http/https proxies
    """
    if cnt == 1:
        return

    proxy = proxy  # Connecting to proxy pool
    UA = [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 \
        Safari/537.36']
    headers = {
        'User-Agent': UA[0]  # Select user agent
    }
    try:
        async with aiohttp.ClientSession(headers=headers, connector=aiohttp.TCPConnector(verify_ssl=False)) as session:
            r = await session.get(url, timeout=timeout)
            html = await r.text()
        error = False
    except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
        # bug in catcher
        # print("Exception in MAIN GETTET: "+str(e)) # all clean now
        error = True
    if error == False:
        return html
    else:
        await getter(url, timeout, error, cnt=cnt + 1)


async def parse(c, names, sheets, update=False):
    urls = ['https://finance.yahoo.com/quote/' + c + '/holders?p=' + c,
            'https://finance.yahoo.com/quote/' + c + '/financials?p=' + c,
            'https://finance.yahoo.com/quote/' + c + '/balance-sheet?p=' + c,
            'https://finance.yahoo.com/quote/' + c + '/cash-flow?p=' + c,
            'https://finance.yahoo.com/quote/' + c + '/key-statistics?p=' + c,
            'https://finance.yahoo.com/quote/' + c + '/profile?p=' + c,
            'https://finance.yahoo.com/quote/' + c + '/analysis?p=' + c,
            'https://finance.yahoo.com/quote/' + c + '?p=' + c]
    if isinstance(sheets, str):
        sheets = [sheets] # double check
    
    
    try:
        # get summary needs changes - handle NAN
        # needs bug recorder
        create_folder(c)
        if not exist(c, 'Summary', update) and _is_active('Summary', sheets):
            try:
                html = await getter(urls[7])
                # input("Press enter to continue")
                save_file(get_summary(html, c), c, 'Summary', update)
                # print("Saved summary")
                # input("Press enter to continue")
                del html
                await asyncio.sleep(0.27)
            except Exception:
                pass
        if not exist(c, names[3:6], update) and _is_active(names[3:6], sheets):
            try:
                html = await getter(urls[4])
                save_dfs(get_stats(html), c, names[3:6])
                # print("Saved statistics")
                # input("Press enter to continue")
                del html
                await asyncio.sleep(0.27)
            except Exception:
                pass
        if not exist(c, names[0:3], update) and _is_active(names[0:3], sheets):
            try:
                html = await getter(urls[0])
                save_file(get_major_holders(html), c, names[0], update)
                save_dfs(get_top_institutional_and_mutual_fund_holders(html), c,
                         [names[1], names[2]])
                # print("Saved holders")
                # input("Press enter to continue")
                del html
                await asyncio.sleep(0.27)
            except Exception:
                pass
        if not exist(c, names[6:8], update) and _is_active(names[6:8], sheets):
            try:
                html = await getter(urls[5])
                save_dfs([get_executives(html), get_description(html)], c, names[6:8])
                # print("Saved executives and description")
                # input("Press enter to continue")
                del html
                await asyncio.sleep(0.27)
            except Exception:
                pass
        if not exist(c, names[8:14], update) and _is_active(names[8:14], sheets):
            try:
                html = await getter(urls[6])
                save_analysis(get_analysis(html), c)
                # print("Saved analysis")
                # input("Press enter to continue")
                del html
                await asyncio.sleep(0.27)
            except Exception:
                pass
        if not exist(c, 'income', update) and _is_active('income', sheets):
            try:
                html = await getter(urls[1])
                save_file(get_reports(html), c, 'income', update)
                # print("Saved income statement")
                # input("Press enter to continue")
                del html
                await asyncio.sleep(0.27)
            except Exception:
                pass
        if not exist(c, 'balance', update) and _is_active('balance', sheets):
            try:
                html = await getter(urls[2])
                save_file(get_reports(html), c, 'balance', update)
                # print("Saved balance sheet")
                # input("Press enter to continue")
                del html
                await asyncio.sleep(0.27)
            except Exception:
                pass
        if not exist(c, 'cash_flow', update) and _is_active('balance', sheets):
            try:
                html = await getter(urls[3])
                save_file(get_reports(html), c, 'cash_flow', update)
                # print("Saved cash flow statement")
                # input("Press enter to continue")
                del html
                await asyncio.sleep(0.27)
            except Exception:
                pass
        _gc.collect()
        # print("All saved for "+c)
    except Exception as e:
        bug = [[c, e]]
        # print("Exception on "+c+": ",e)


def get_all_stocks(exchange):  # Get all stocks required using the stock_list operation
    if not (exchange != 'NYSE' or exchange != 'NASDAQ'):
        raise ValueError("Exchange should be either NYSE or NASDAQ, not: '{}'".format(str(exchange)))
    s = stock_list(exchange)['Symbol'].tolist()
    return s


def main(stocks, sheets, update=False, batch=64):
    """
    stocks -- either NYSE or NASDAQ
    sheets - list - retrieve from main_get(), sheets that will get
    update - used for update()
    batch - batch size, retrieve from main_get()
    """
    if stocks in ['NYSE', 'NASDAQ']:  # load all stocks
        stocks = get_all_stocks(stocks)
    assert isinstance(stocks, list)
    # stocks=['BABA'] #for testing
    # s=['BABA','AAPL','AMZN','JD','BIDU','WB','WFC','C','JPM','DPZ','BA','CVX','LUV'] # for sample testing
    NAMES = ['major_holders', 'top_institutional_holders', 'top_mutual_fund_holders',
             'Trading_Information', 'Financial_Highlights', 'Valuation_Measures',
             'Executives', 'Description',
             'Earnings_Estimate', 'Revenue_Estimate', 'Earnings_History',
             'EPS_Trend', 'EPS_Revisions', 'Growth_Estimates',
             'stats', 'statements', 'reports',
             'Executives', 'Description', 'analysis', 'Summary',
             'income', 'balance', 'cash_flow']  # things that'll be updated
    len_temp = int(len(stocks))
    if len_temp < batch:
        batch = len_temp
    for i in range(0, len_temp, batch):  # Yahoo Spyder main; async main loop
        # async in 3.6, different callings in 3.7
        t1 = time.time()
        tasks = [asyncio.ensure_future(parse(c, NAMES, sheets=sheets, update=update)) for c in stocks[i:i + batch]]  # async calling
        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.wait(tasks))
        t2 = time.time()
        print(str(i + batch) + "/" + str(len(stocks)) + " - Total Time: " + str(t2 - t1) + 's')
        # input("Cut point check")


'''
def _speedtestf():
    import shutil
    stock='NYSE'
    t=[]
    for i in range(16,256,8):
        companies=get_all_stocks(stock)[0:i]
        s=time.time()
        main(stock, batch=i)
        e=time.time()
        t.append(round((e-s)/i, 4))
        print("batch size {}: {}s".format(i, round((e-s)/i,3)))
        for c in companies:
            try:
                shutil.rmtree(os.path.join('./database',c))
            except FileNotFoundError:
                print('FileNotFoundError: '+c)
                continue
        #input('cut point check')
        gc.collect()
        time.sleep(1)
    return t
'''


def main_get(stocks='SP100', sheets='financials', batch=32):
    """
    Main getter for client, MUST be runned after installation of the package (default update all stocks in NYSE and NASDAQ)
    stocks - str - default SP100, can be ALL, NYSE, NASDAQ, list of tickets, load_stock_list() (for client only)
    sheets - list/str - default financials (income, balance, cash_flow), use "ALL" to indicate all sheets; choices include: financials, key-statistics, summary, profile, analysis, holders
    batch - default 32, batch size for loop (recommend to change based on interest status)
    """
    if stocks not in ['NYSE', 'NASDAQ', 'ALL', 'SP100'] and isinstance(stocks, str):
        # when stocks is nonesense
        t = type(stocks)
        if len(stocks) > 10:
            stocks = str(stocks[0:4] + ['......'] + stocks[-2:])
        raise ValueError("Parameter 'stocks' should be one of SP100, NYSE, NASDAQ, and ALL, not {} object: {}"
                         .format(t.__name__, str(stocks)))
    if len(stocks)==0: # empty list
        raise ValueError("Parameter 'stocks' must have something in it.")
    
    if isinstance(sheets, str):
        sheets = [sheets] # str - list
    for i in sheets: # avoird typo
        if i not in ['financials', 'key-statistics', 'summary', 'profile', 'analysis', 'holders']:
            raise ValueError("Parameter 'sheets' should come from: financials, key-statistics, summary, profile, analysis, holders, not {}".format(i))
    if sheets[0] == 'ALL':
        sheets = ['income', 'cash_flow', 'balance', 'Financial_Highlights', 'Valuation_Measures', 'Trading_Information',
                  'Sumary', 'Executives', 'Description', 'Earnings_Estimate', 'Revenue_Estimate', 'Earnings_History', 'EPS_Trend', 'EPS_Revisions', 'Growth_Estimates',
                  'major_holders', 'top_institutional_holders', 'top_mutual_fund_holders']
    else:
        d = {'financials': ['income', 'cash_flow', 'balance'], 'key-statistics': ['Financial_Highlights', 'Valuation_Measures', 'Trading_Information'],
             'summary': ['Summary'], 'profile': ['Executives', 'Description'],
             'analysis': ['Earnings_Estimate', 'Revenue_Estimate', 'Earnings_History', 'EPS_Trend', 'EPS_Revisions', 'Growth_Estimates'],
             'holders': ['major_holders', 'top_institutional_holders', 'top_mutual_fund_holders']}
        sheets = [d[i] for i in sheets] # map webpages to sheets
        sheets = [i[j] for i in sheets for j in range(len(i))] # squeeze
        print("Get includes: ......")
        print(str(sheets))
    with open(_os.path.join(main_path, 'get_sheets_cache.txt'), 'w') as w:
        w.write(','.join(sheets)) # save param sheets to cache for update() to use

    if stocks == 'SP100': # S&P 100 <- default
        stocks = open_general('SP100')['Symbol'].tolist() # read csv
        main(stocks=stocks, sheets=sheets, batch=batch)

    elif stocks == 'ALL':
        main(stocks='NYSE', sheets=sheets, batch=batch)
        print("Updated NYSE data")
        main(stocks='NASDAQ', sheets=sheets, batch=batch)
        print("Updated NASDAQ data")
    else:
        main(stocks=stocks, sheets=sheets, batch=batch) # updated for sheets
        if len(stocks) > 10:
            stocks = str(stocks[0:4] + ['......'] + stocks[-2:]) # avoid print too much
        print("Updated all data for" + str(stocks))


def _getBetweenDay(begin_date):  # tested
    # Got from csdn.com, minor changes have made
    begin_date = _dtime.datetime.strptime(begin_date, "%Y-%m-%d") + _dtime.timedelta(days=1)
    today = time.strftime('%Y-%m-%d', time.localtime(time.time()))
    end_date = _dtime.datetime.strptime(today, "%Y-%m-%d")
    print("Current date: " + today)
    while begin_date <= end_date:  # doesn't include today
        date_str = begin_date.strftime("%Y-%m-%d")
        yield date_str  # to reduce memory usage
        begin_date += _dtime.timedelta(days=1)


def getLastUpdate():  # get last update date of the database
    # client can access this
    """
    get last update time
    prints out the date and returns the date(str)
    """
    last_update = open(_os.path.join(main_path, 'datefile.txt')).readlines()[0]
    print("Last update time: " + last_update)
    return last_update


async def update_getter(day):  # util
    url = 'https://finance.yahoo.com/calendar/earnings?from=2019-05-12&to=2019-05-18&day={}'
    html = await getter(url.format(day), timeout=15)
    updates = [i.text()
               for i in pq(html)('.simpTblRow a').items()
               ]
    df = _pd.DataFrame(updates)
    df.to_csv('dates_temp.csv', mode='a', header=False)  # csv as a tranducer


# problem: the connection between async and normal functions
# update getter can't be connected well to the normal loop, and the current solution
# is to use a csv file as a transducer, but the method of running a singlar
# coroutine is not identified and developed, which needs to be done


async def update_stock_list(day):
    await update_getter(day)


def update_all_days():
    # Dates that need to be updated
    # Date format - YYYY-MM-DD

    # input('Cut-point check') # for checking
    # df.tolist() is depreciated... use df.values.tolist() instead
    try:
        with open(_os.path.join(main_path, 'get_sheets_cache.txt'), mode='r') as w:
            sheets = w.read().split(',') # read sheets parameter
    except FileNotFoundError:
        print("Exception FileNotFoundError")
    updates = _pd.read_csv('dates_temp.csv', index_col=0).values.tolist()  # read dates
    updates = set([i[j] for i in updates for j in range(len(i))])  # for set operation AND
    needs_update_list = list(updates.intersection(stocksss))
    company_list_length = len(needs_update_list)
    print("Total update companies: {}".format(company_list_length))
    if company_list_length == 0:
        return
    try:
        main(needs_update_list, sheets=sheets, update=True)  # no syntax error here
        # working smoothly now (not fast enough)
    except Exception as e:
        print("Exception in update each day: " + str(e))


def update():
    """
    update function for JAQK package
    this automatically catches days and companies need to be updated, and update
    recommend to update every day
    """
    df = _pd.DataFrame()
    df.to_csv('dates_temp.csv')  # clear up cache
    global stocksss
    stocksss = set(_os.listdir(datapath()))  # set of stocks in database
    last_update = getLastUpdate()
    days = _getBetweenDay(last_update)
    tasks = [asyncio.ensure_future(update_stock_list(day)) for day in days]  # async calling
    temp = asyncio.get_event_loop()
    temp.run_until_complete(asyncio.wait(tasks))
    print("Company list retrieved")
    update_all_days()
    #    with open('datefile.txt', mode='w') as d:
    #        d.write(time.strftime('%Y-%m-%d', time.localtime(time.time())))
    print("Update completed")


def load_stock_list():
    """
    for specific stock_list only (client's stock list: KWHS Investment Competition Approved Securities)
    """
    import PySimpleGUI as sg
    form_rows = [[sg.Text('Choose the excel path')],
                 [sg.Text('Choose path: ', size=(15, 1)), sg.InputText(key='Choose'),
                  sg.FileBrowse(file_types=(('Excel Spreadsheet', '*.xlsx'), ('Excel Spreadsheet', '*.xls')))],
                 [sg.Submit(), sg.Cancel()]]
    window = sg.Window('Choose excel from path')
    _, values = window.Layout(form_rows).Read()
    window.Close()
    path = values['Choose']  # file path chosen

    import openpyxl as xl
    wb = xl.load_workbook(path)
    sheet_names = wb.get_sheet_names()  # openpyxl for getting all sheet_names

    r = [_pd.read_excel(path, i)['TICKER'].tolist() for i in
         sheet_names]  # header of stocks is TICKER in client's stock list
    r = [i[j] for i in r for j in range(len(i))]
    return r


def _is_global(): # resolve datapath scrope problem
    try:
        type(datapath())
        return True
    except NameError:
        return False


def setup():
    """
    setup the database; this should be done before anything
    choose the directory to place the database (~100M)
    """
    assert _is_global()==True

    # choose path for setup database
    import PySimpleGUI as sg 
    form_rows = [[sg.Text('Choose the setup path')],
                 [sg.Text('Setup path: ', size=(15, 1)), sg.InputText(key='setup'), sg.FolderBrowse()],
                 [sg.Submit(), sg.Cancel()]]
    window = sg.Window('Choose a path for setup database')
    _, values = window.Layout(form_rows).Read()
    window.Close()
    globals()['setup_path'] = values['setup'] # global setup_path
    with open(_os.path.join(main_path, 'setup_cache.txt'), mode='w') as w:
        w.write(setup_path) # setup cache for setup directory
    # choose a specific path for database folder

    # setup starts
    companies = ['AAPL', 'AMZN']
    [create_folder(i, setup_path, True) for i in companies]
    dirs = [_os.listdir(_os.path.join(datapath(setup=False), c)) for c in companies]
    #if not('.csv' in dirs[0][2] and '.csv' in dirs[0][5]):
    dirs2 = dirs[:]
    del dirs
    try:
        [dirs2[i].remove('__init__.py') for i in range(2)] # remove __init__.py
    except ValueError:
        pass
    if '.py' in ''.join(dirs2[0])+''.join(dirs2[1]): # AAPL and AMZN
        # convert .py into .csv
        [open_file(companies[c], dirs2[c][d], setup=True).to_csv(_os.path.join(setup_path, companies[c], dirs2[c][d].split('.')[0]+'.csv'), index=False)
        for c in range(len(companies)) for d in range(len(dirs2[c])) if dirs2[c][d]!='__init__.py' and dirs2[c][d]!='__pycache__']
        
        # delete original .py files
        [_os.remove(_os.path.join(datapath(setup=False), companies[i], dirs2[i][j])) for i in range(len(companies)) for j in range(len(dirs2[i])) if dirs2[i][j]!='__init__.py' and ('.csv' not in dirs2[i][j]) and dirs2[i][j]!='__pycache__']

    # setup general stock lists
    dirs_general2 = _os.listdir(_os.path.join(datapath(setup=False), 'general'))
    dirs_general = dirs_general2[:] # avoid mutable list
    del dirs_general2
    try:
        dirs_general.remove('__init__.py') # list_dir for 'general'
    except ValueError:
        pass
    
    if '.py' in ''.join(dirs_general): # NYSE and NASDAQ
        # setup stock_list general
        exc = ['NYSE', 'NASDAQ', 'SP100']
        create_folder('general', setup_path, True)
        [open_general(ex, setup=True).to_csv(_os.path.join(setup_path, 'general', ex+'.csv'), index=False)
         for ex in exc]
        [_os.remove(_os.path.join(datapath(setup=False), 'general', ex+'.py')) for ex in exc]

    if 'dates_temp.py' in _os.listdir(main_path): # dates_temp
        _pd.read_csv(_os.path.join(main_path, 'dates_temp.py')).to_csv(_os.path.join(main_path, 'dates_temp.csv'), index=False)
        _os.remove(_os.path.join(main_path, 'dates_temp.py')) # delete original\

    if 'datefile.py' in _os.listdir(main_path): # datefile
        with open(_os.path.join(main_path, 'datefile.py')) as d:
            d = d.read() # read
        with open(_os.path.join(main_path, 'datefile.txt'), mode='w') as w:
            w.write(d) # write
        _os.remove(_os.path.join(main_path, 'datefile.py')) # delete
        
    _gc.collect()
    print("Database has been setup on path: {}".format(setup_path))
    

def _is_active(names, sheets):
    if isinstance(names, str):
        names = [names]
    return set(names).issubset(set(sheets)) # [] in [] regardless of order


def datapath(setup=True):
    """
    The global datapath for all other file. It sets your selected path in jaqk.setup() as the main datapath, and all data will be added/deleted from there.
    """
    try:
        with open(_os.path.join(main_path, 'setup_cache.txt')) as w:
            path = w.read()
        if setup==True:
            return path
        else:
            return _os.path.join(_os.path.dirname(__file__), 'database')
    except FileNotFoundError:
        return _os.path.join(_os.path.dirname(__file__), 'database')



    

