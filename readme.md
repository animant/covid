
About
======
The program downloads actual COVID-19 statistic from https://github.com/CSSEGISandData/COVID-19/ and visualize according to
given countries and datasets.


Installation
=============
Install python3
Install pyhton3 modules: requests, matplotlib, csv

Usage
=====
Print `./covid_visual.py -h` for help.

Print `./covid_visual.py -l` to list all countries names and dataset formats

Examples
========
    python3 ./covid_visual.py -l  #show country names
    python3 ./covid_visual.py -c 'China,Italy'  -f 'D' #show for China and Italy deaths cases
    python3 ./covid_visual.py -c 'China,Italy'  -f 'CD,R' #show for China and Italy confirmed-per-day and recovered
    python3 ./covid_visual.py -c 'China'  #show for China confirmed, deaths and recovered

