#!/usr/bin/python3
import csv
import difflib
try:
    import matplotlib.pyplot as plt
    IS_MPL = True
except:
    print("Package 'matplotlib' isn't installed. Try to install or change python version (3.7->3.6?)")
    IS_MPL = False
import math
import requests
import sys
import os

from datetime import date, timedelta

COL_NUM = 4
AXIS_SPARSE = 10

COVID_PATH = ".covid"
COVID_LOCK = ".covid.lock"

#DAILY_SET = set(['CD','DD','RD'])
DAILY_SET = set(['CD','DD'])
FMTS = {'C':'Confirmed','D':'Deaths','CD':'Confirmed (daily)','DD':'Deaths (daily)'}
#FMTS = {'C':'Confirmed','D':'Deaths','R':'Recovered','CD':'Confirmed (daily)','DD':'Deaths (daily)','RD':'Recovered (daily)'}

def parse_raw(raw_file):
    reader = csv.reader(open(raw_file))
    datestamps = next(reader)[4:]
    statistic_dups = [(r[1].upper().replace(',',''), list(map(lambda x:int(x) if x!='' else 0, r[4:]))) for r in reader]
    statistic = dict([(country, (lambda x:[sum(y) for y in zip(*x)])([s[1] for s in statistic_dups if s[0] == country])) for country in set(next(zip(*statistic_dups)))])
    statistic["TOTAL"] = [sum([j[i] for j in statistic.values()]) for i in range(len(datestamps))]
    return (statistic, datestamps)

def parse_population(raw_file):
    def _patch_country_name(data):
        patch = [("United States","US")]
        p_data = data
        for p in patch:
            p_data = p_data.replace(p[0],p[1])
        return p_data

    reader = csv.reader(open(raw_file))
    header = next(reader)
    full_dum = [(_patch_country_name(x[0]),x[2],x[3]) for x in reader]
    latest_count = [sorted([item for item in full_dum if item[0]==ctr], key=lambda x:x[1])[-1] for ctr in set(next(zip(*full_dum)))]
    return dict([(lc[0].upper(), lc[2]) for lc in latest_count])

def get_country_size(db_population, country_name, verbose = False):
    country_names = sorted(list(db_population.keys()))
    country_name = country_name.upper()
    ctr_result = difflib.get_close_matches(country_name, country_names)
    if ctr_result == []:
        if verbose:
            print(f"\033[91mError! The country {country_name} or similar was not found!")
        return None
    elif ctr_result[0] == country_name:
        return int(db_population[country_name])
    else:
        if verbose:
            print(f"\033[91mWarning! The country {country_name} was not found! The closest name is {ctr_result[0]}\033[0m")
        int(db_population[ctr_result[0]])

def load_raw_data(path, lock_filename):
    print("Update raw data....")
    res = requests.get("https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv")
    open(f"{path}/Confirmed.csv","w").write(res.text)
    res = requests.get("https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv")
    open(f"{path}/Deaths.csv","w").write(res.text)
    res = requests.get("https://raw.githubusercontent.com/datasets/population/master/data/population.csv")
    open(f"{path}/population.csv","w").write(res.text)
    #res = requests.get("https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Recovered.csv")
    #open(f"{path}/Recovered.csv","w").write(res.text)
    open(lock_filename,"w").write(str(date.today()))

def init_update():
    lock_filename = f"{COVID_PATH}/{COVID_LOCK}"
    load_raw_data(COVID_PATH, lock_filename)
#disable updating once per day
    #if not os.path.exists(COVID_PATH):
    #    os.mkdir(COVID_PATH)
    #    load_raw_data(COVID_PATH, lock_filename)
    #if not os.path.exists(lock_filename):
    #    load_raw_data(COVID_PATH, lock_filename)
    #else:
    #    last_date = open(lock_filename).read()
    #    if last_date != str(date.today()):
    #        load_raw_data(COVID_PATH, lock_filename)


def load_statistic(in_persentage=False, log_schem=False):
    def diff_array(ar):
        return [0]+[ar[i]-ar[i-1] for i in range(1,len(ar))]
    def diff_db(db):
        db2 = ({}, db[1])
        for d in db[0]:
            db2[0][d] = diff_array(db[0][d])
        return db2

    db_confirmed = parse_raw(f"{COVID_PATH}/Confirmed.csv")
    db_death = parse_raw(f"{COVID_PATH}/Deaths.csv")
    #db_recovered = parse_raw(f"{COVID_PATH}/Recovered.csv")
    db_population = parse_population(f"{COVID_PATH}/population.csv")
    #print(get_country_size(db_population, "ukraine"))
    for db in [db_confirmed, db_death]:
        if in_persentage:
            for d in db[0]:
                population = get_country_size(db_population, d)
                if population == None:
                    db[0][d] = [0]*len(db[0][d])
                else:
                    db[0][d] = [val/population*100 for val in db[0][d]]
        if log_schem:
            for d in db[0]:
                db[0][d] = [math.log(val) if val!=0 else 0 for val in db[0][d]]


    db_confirmed_diff = diff_db(db_confirmed)
    db_death_diff = diff_db(db_death)
    #db_recovered_diff = diff_db(db_recovered)
    return {"C":db_confirmed, "D":db_death, "CD":db_confirmed_diff, "DD":db_death_diff}
    #return {"C":db_confirmed, "D":db_death, "R":db_recovered, "CD":db_confirmed_diff, "DD":db_death_diff, "RD":db_recovered_diff}
    

def show_countires(statistic):
    print("-"*(30*(COL_NUM+1)))
    print("Countries:")
    print("="*(30*(COL_NUM+1)))
    print("   TOTAL - overall statistic")
    country_list = sorted(list(map(lambda x:"{:<35s}".format(x), statistic["C"][0].keys())))
    country_list = country_list
    for i in range(len(country_list)//COL_NUM + 1):
        print('   '+''.join(country_list[i::len(country_list)//COL_NUM + 1]))
    print("-"*(30*(COL_NUM+1)))
    print("Formats:")
    print("C - confirmed, CD - confirmed daily")
    print("D - deaths,    DD - deaths daily")
    #print("R - recovered, RD - recovered daily")
    print("-"*(30*(COL_NUM+1)))

def plot_subgraph(plt, statistic, countries, fmt):
    #[plt.plot(statistic[f][0][c]) for c in countries for f in formats]
    #plt.legend([f"{c}: {FMTS[f]}" for c in countries for f in formats])
    [plt.plot(statistic[fmt][0][c]) for c in countries]
    plt.legend([f"{c}: {FMTS[fmt]}" for c in countries])
    plt.grid(which='minor', alpha=0.3)
    plt.grid(which='major', alpha=0.5)
    plt.minorticks_on()
    plt.xticks(range(0,len(statistic['C'][1]),AXIS_SPARSE), statistic['C'][1][::AXIS_SPARSE])
    plt.xlabel("Date")
    plt.ylabel("People")

def main():
    if "-h" in sys.argv or '--help' in sys.argv or len(sys.argv)==1:
        print("Show Corona statistic") 
        print("Usage: python3 %s [-l] [-c <COUNTRIES> [-f <FORMATS>]] "%sys.argv[0])
        print("      -l              - show country names")
        print("      -c <COUNTRIES>  - set counties (coma separated)")
        print("      -f <FORMATS>    - set formats (coma separated)")
        print("      -p              - all values in population persentage (betta)")
        print("      -n              - log schema (betta)")
        print("     Formats: [C]onfirmed , [D]eaths")
        print("              +[D]aily")
        print("---------------------------------------------------")
        print("Examples:")
        print("    python3 %s -l  #show country names"%sys.argv[0])
        print("    python3 %s -c 'China,Italy'  -f 'D' #show for China and Italy deaths cases"%sys.argv[0])
        print("    python3 %s -c 'China,Italy'  -f 'CD,R' #show for China and Italy confirmed-per-day and recovered"%sys.argv[0])
        print("    python3 %s -c 'China'  #show for China confirmed, deaths and recovered"%sys.argv[0])
        exit(0)
    init_update()
    statistic = load_statistic('-p' in sys.argv, '-n' in sys.argv)
    if '-l' in sys.argv:
        show_countires(statistic)
        exit(0)

    if not '-c' in sys.argv:
        print("Error: '-c' option isn't set")
        exit(-1)
    countries = sys.argv[sys.argv.index('-c')+1].upper().split(',')
    formats = ('C,D' if not '-f' in sys.argv else sys.argv[sys.argv.index('-f')+1]).upper().split(',')
    print("Timeline:")
    print("    "+str(statistic['C'][1]))
    print()
    for c in countries:
        for f in formats:
            print("Country: "+c)
            print("    Dataset: "+FMTS[f])
            print("        "+str(statistic[f][0][c]))
        print()
    if IS_MPL:
        #if (DAILY_SET & set(formats) == set([])) or (set(formats) - DAILY_SET == set([])):
        #    plot_subgraph(plt, statistic, countries, formats)
        #else:
        #    plt.subplot(211)
        #    plot_subgraph(plt, statistic, countries, set(formats)-DAILY_SET)
        #    plt.subplot(212)
        #    plot_subgraph(plt, statistic, countries, set(formats)&DAILY_SET)
        if len(formats) == 1:
            plot_subgraph(plt, statistic, countries, formats[0])
        elif len(formats) == 2:
            plt.subplot(211)
            plot_subgraph(plt, statistic, countries, formats[0])
            plt.subplot(212)
            plot_subgraph(plt, statistic, countries, formats[1])
        elif len(formats) == 3:
            plt.subplot(311)
            plot_subgraph(plt, statistic, countries, formats[0])
            plt.subplot(312)
            plot_subgraph(plt, statistic, countries, formats[1])
            plt.subplot(313)
            plot_subgraph(plt, statistic, countries, formats[2])
        elif len(formats) == 4:
            plt.subplot(221)
            plot_subgraph(plt, statistic, countries, formats[0])
            plt.subplot(222)
            plot_subgraph(plt, statistic, countries, formats[1])
            plt.subplot(223)
            plot_subgraph(plt, statistic, countries, formats[2])
            plt.subplot(224)
            plot_subgraph(plt, statistic, countries, formats[3])
        else:
            print("Error, duplicated formats?")
        plt.show()



main()
