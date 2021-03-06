import datetime
import re

from . import dqcodelists
from functools import reduce


def fixVal(value):
    try:
        return float(value)
    except ValueError:
        pass
    try:
        value = value.replace(',','')
        return float(value)
    except ValueError:
        pass
    return float(value.replace('.0',''))

def date_later_than_now(date):
    try:
        if datetime.datetime.strptime(date, "%Y-%m-%d") > datetime.datetime.utcnow():
            return True
    except Exception:
        # Some dates are not real dates...
        pass
    return False

def budget_within_year_scope(budget_end, year):

    # Check that the budget ends at least N years ahead, but not
    # N+1 years ahead (because then it counts as the following year,
    # so out of scope).

    # Budgets are now within scope if they run until the end of
    # 2015 (maximum 203 days).

    try:
        now = datetime.datetime.now()
        date_budget_end = datetime.datetime.strptime(budget_end, "%Y-%m-%d")

        future = datetime.timedelta(days=180+(365*(year-1)))
        future_plus_oneyear = future+datetime.timedelta(days=365)

        if ((date_budget_end > (now+future)) and
            (date_budget_end < (now+future_plus_oneyear))):
            return True
    except Exception:
        # Some dates are not real dates...
        pass

    return False

def total_future_budgets(doc):

    # Checks if total budgets are available for each of
    # the next three years.

    total_budgets = doc.xpath("//total-budget[period-end/@iso-date]")
    years = [0, 1, 2, 3]
    out = {}

    def get_budget_per_year(year, out, total_budget):
        budget_start = total_budget.find('period-start').get('iso-date')
        budget_end = total_budget.find('period-end').get('iso-date')

        if budget_within_year_scope(budget_end, year):
            out[year] = {
                'available': True,
                'amount': fixVal(total_budget.find('value').text)
            }
        return out

    def get_budgets(total_budgets, year, out):
        out[year] = {'available': False,
                     'amount': 0 }
        out = [get_budget_per_year(year, out, total_budget) for total_budget in total_budgets]
        return out

    [get_budgets(total_budgets, year, out) for year in years]

    return out

def total_country_budgets(doc, totalbudgets):

    # Checks if country budgets are available for each
    # of the next three years and what % published
    # recipient country budgets are of the total
    # published budget.
    # Will return 0 if no total budget could be found.

    rb_xpath = "//recipient-country-budget[period-end/@iso-date]"
    recipient_country_budgets = doc.xpath(rb_xpath)
    budgetdata = {
        'summary': {
            'num_countries': 0,
            'total_amount': {0:0, 1:0, 2:0, 3:0},
            'total_pct': {0:0.00, 1:0.00,2:0.00,3:0.00},
            'total_pct_all_years': 0.00
        },
        'countries': {}
    }
    years = [0, 1, 2, 3]

    def get_country_data(budget, budgetdata, year):
        country_el = budget.find('recipient-country')
        if country_el is not None:
            country = country_el.get('code')
            country_name = country_el.text
        else:
            country = None
            country_name = None
        country_budget_end = budget.find('period-end').get('iso-date')
        if budget_within_year_scope(country_budget_end, year):
            if country in budgetdata['countries']:
                budgetdata['countries'][country][year] = budget.find('value').text
            else:
                budgetdata['countries'][country] = {
                    year: budget.find('value').text,
                    'name': country_name
                }
            budgetdata['summary']['total_amount'][year]+=fixVal(budget.find('value').text)
        return budgetdata

    def make_country_budget(year, budgetdata,
            recipient_country_budgets):
        return [get_country_data(budget, budgetdata,
            year) for budget in recipient_country_budgets]

    [make_country_budget(year, budgetdata,
        recipient_country_budgets) for year in years]

    def getCPAAdjustedPercentage(total_countries, total_year):
        cpa = 0.2136
        total_cpa_adjusted = float(total_year)*cpa

        percentage = (float(total_countries)/float(total_cpa_adjusted))*100
        if percentage > 100:
            return 100.00
        else:
            return percentage

    def get_a_total_budget_over_zero(totalbudgets):
        years = [0, 1, 2, 3]
        for year in years:
            if totalbudgets[year]['amount'] > 0:
                return totalbudgets[year]['amount']
        return 0.00

    def generate_total_years_data(budgetdata, year):
        total_countries = budgetdata['summary']['total_amount'][year]
        total_all = totalbudgets[year]['amount']
        try:
            budgetdata['summary']['total_pct'][year] = getCPAAdjustedPercentage(total_countries, total_all)
        except ZeroDivisionError:
            # Use current year's budget
            try:
                budgetdata['summary']['total_pct'][year] = getCPAAdjustedPercentage(total_countries,
                                get_a_total_budget_over_zero(totalbudgets))
            except ZeroDivisionError:
                budgetdata['summary']['total_pct'][year] = 0.00
        budgetdata['summary']['num_countries'] = len(budgetdata['countries'])
        return budgetdata

    data = [generate_total_years_data(budgetdata, year) for year in years]

    total_pcts = list(budgetdata['summary']['total_pct'].items())

    # For scoring, restrict to forward years (year >=1)
    total_pcts = dict([x for x in total_pcts if x[0]>=1])
    total_pcts = list(total_pcts.values())

    # Return average of 3 forward years
    budgetdata['summary']['total_pct_all_years'] = (reduce(lambda x, y: float(x) + float(y), total_pcts) / float(len(total_pcts)))
    return budgetdata

def total_country_budgets_single_result(doc):
    cbs = total_country_budgets(doc, total_future_budgets(doc))['summary']['total_pct_all_years']
    if cbs > 0: return cbs
    return total_sector_budgets_single_result(doc)

def country_strategy_papers(doc):
    countries = all_countries(doc)

    # Is there a country strategy paper for each
    # country? (Based on the list of countries that
    # have an active country budget.)

    if len(countries)==0:
        return total_sector_strategy_papers(doc)

    total_countries = len(countries)
    strategy_papers = doc.xpath("//document-link[category/@code='B03']")

    countrycodelist = dqcodelists.reformatCodelist("countriesbasic")

    for code, name in list(countries.items()):
        # Some donors have not provided the name of the country; the
        # country code could theoretically be looked up to find the
        # name of the country
        name = getCountryName(code, name, countrycodelist)
        for strategy_paper in strategy_papers:
            recipient = strategy_paper.find('recipient-country')
            if recipient is not None:
                if recipient.get('code').lower() == code.lower():
                    try:
                        countries.pop(code)
                    except Exception:
                        pass
                    continue
            if name is not None:
                title = strategy_paper.find('title')
                if not title.text or not title.text.strip():
                    title = title.find('narrative')
                if re.search(name, title.text, flags=re.IGNORECASE):
                    try:
                        countries.pop(code)
                    except Exception:
                        pass
    print("Remaining countries are", countries)
    csp = 100-(float(len(countries))/float(total_countries))*100
    if csp > 0: return csp
    print(doc)
    return total_sector_strategy_papers(doc)

def getCountryName(code, name, countrycodelist):
    if name is not None:
        return name
    else:
        try:
            return countrycodelist[code]
        except Exception:
            return None

def budget_has_value(recipient_country_budget):
    try:
        value = recipient_country_budget.xpath('value')[0].text
        assert int(float(value))>0
    except Exception:
        return False
    return True

def all_countries(doc):

    # Get all countries that have any budget data at all,
    # as long as the country is active (budget end
    # date later than today).

    countries = {}
    recipient_country_budgets = doc.xpath("//recipient-country-budget[period-end/@iso-date]")
    for recipient_country_budget in recipient_country_budgets:
        country_budget_date = recipient_country_budget.find('period-end').get('iso-date')

        # Check if the country is still active: if there is
        # an end date later than today, then include it
        if (date_later_than_now(country_budget_date) and budget_has_value(recipient_country_budget)):
            country_el = recipient_country_budget.find('recipient-country')
            if country_el is not None:
                code = country_el.get('code')
                if country_el.find('narrative') is not None:
                    name = country_el.find('narrative').text
                else:
                    name = country_el.text
            else:
                code = None
                name = None
            countries[code] = name
    return countries

def total_budgets_available(doc):
    future_years = total_future_budgets(doc)
    # Only look for future years >=1, i.e. exclude
    # current year.
    future_years = dict([x for x in list(future_years.items()) if x[0]>=1])

    available = 0
    for year, data in list(future_years.items()):
        if data['available'] == True:
            available+=1
    return (float(available)/3.0)*100

def total_sector_budgets(doc):
    # Get budgets for each sector in each year
    totalbudgets = doc.xpath("//total-budget")
    years = [0,1,2,3]
    sout = {}
    for year in years:
        sout[year] = {"budget-lines": {},
                      "budget_total": 0.0,
                      "budgetlines_total": 0.0,
                      "budgetlines_pct": 0.0}
        for tb in totalbudgets:
            budget_end = tb.xpath("period-end/@iso-date")[0]
            if budget_within_year_scope(budget_end, year):
                budget_total = tb.xpath("value/text()")[0]
                sout[year]["budget_total"] = float(budget_total)
                budgetlines = tb.xpath("budget-line")
                for bl in budgetlines:
                    budget_ref = bl.get("ref")
                    budget_name = bl.xpath("narrative/text()")[0]
                    budget_value = bl.xpath("value/text()")[0]
                    sout[year]["budget-lines"][budget_ref] = {
                        "budget_name": budget_name,
                        "budget_value": float(budget_value)
                    }
                    sout[year]["budgetlines_total"] += float(budget_value)
                sout[year]["budgetlines_pct"] = min(
                    (sout[year]["budgetlines_total"] /
                     sout[year]["budget_total"] * 100),
                     100)
    return sout

def total_sector_budgets_single_result(doc):
    result = total_sector_budgets(doc)
    return sum(by["budgetlines_pct"] for by in list(result.values())) / len(result)

def total_sector_strategy_papers(doc):
    all_budgets = total_sector_budgets(doc)
    sector_names = set(sum(list([list([b['budget_name'] for b in list(x['budget-lines'].values())]) for x in list(all_budgets.values())]), []))

    all_sector_document_titles = doc.xpath("//document-link[category/@code='B11']/title/narrative/text()|document-link[category/@code='B12']/title/narrative/text()")
    found = 0.0
    for sn in sector_names:
        for asdt in all_sector_document_titles:
            if asdt.find(sn) >= 0:
                found +=1
                break

    return found/len(sector_names)*100

"""print "Total budgets..."
print total_budgets_available(doc)

print "Total country budgets..."    
print total_country_budgets_single_result(doc)

print "Country strategy papers"
print country_strategy_papers(doc)"""
