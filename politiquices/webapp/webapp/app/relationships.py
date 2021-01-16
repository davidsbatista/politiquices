from collections import defaultdict, Counter
from datetime import datetime

from politiquices.webapp.webapp.app.sparql_queries import (
    get_person_rels_by_month_year,
    get_person_rels_by_year,
)


def month_list_fast(start, end):
    """
    Generate a sequence of year-month, based on a starting and ending year-month
    """
    # https://stackoverflow.com/questions/34898525/generate-list-of-months-between-interval-in-python
    total_months = lambda dt: dt.month + 12 * dt.year
    months_list = []
    for tot_m in range(total_months(start) - 1, total_months(end)):
        y, m = divmod(tot_m, 12)
        months_list.append(datetime(y, m + 1, 1).strftime("%Y-%b"))
    return months_list


def find_maximum_interval(*args):
    """
    Finds a the maximum and minimum date from a several list of (date, freq) pairs

    :param args: a list of pairs of (date, freq)
    :return:
    """
    min_date = min([list(freq.keys())[0] for freq in args if freq])
    max_date = max([list(freq.keys())[-1] for freq in args if freq])
    return min_date, max_date


def get_all_months(few_months_freq, months_lst):
    year_months_values = defaultdict(int)
    for m in months_lst:
        x = datetime.strptime(m, "%Y-%b")
        key = x.strftime("%Y-%m")
        if key in few_months_freq:
            year_months_values[m] = few_months_freq[key]
        else:
            year_months_values[m] = 0

    return year_months_values


def build_relationships_year_month_freq(wiki_id: str):

    # supports
    supported_freq_one = get_person_rels_by_month_year(wiki_id, "ent1_supports_ent2", ent="ent1")
    supported_freq_two = get_person_rels_by_month_year(wiki_id, "ent2_supports_ent1", ent="ent2")
    supported_freq_sum = Counter(supported_freq_one) + Counter(supported_freq_two)
    supported_freq = {k: supported_freq_sum[k] for k in sorted(supported_freq_sum)}

    # opposes
    opposed_freq_one = get_person_rels_by_month_year(wiki_id, "ent1_opposes_ent2", ent="ent1")
    opposed_freq_two = get_person_rels_by_month_year(wiki_id, "ent2_opposes_ent1", ent="ent2")
    opposed_freq_sum = Counter(opposed_freq_one) + Counter(opposed_freq_two)
    opposed_freq = {k: opposed_freq_sum[k] for k in sorted(opposed_freq_sum)}

    # supported_by
    supported_by_freq_one = get_person_rels_by_month_year(wiki_id, "ent2_supports_ent1", ent="ent1")
    supported_by_freq_two = get_person_rels_by_month_year(wiki_id, "ent1_supports_ent2", ent="ent2")
    supported_by_freq_sum = Counter(supported_by_freq_one) + Counter(supported_by_freq_two)
    supported_by_freq = {k: supported_by_freq_sum[k] for k in sorted(supported_by_freq_sum)}

    # opposed_by
    opposed_by_freq_one = get_person_rels_by_month_year(wiki_id, "ent2_opposes_ent1", ent="ent1")
    opposed_by_freq_two = get_person_rels_by_month_year(wiki_id, "ent1_opposes_ent2", ent="ent2")
    opposed_by_freq_sum = Counter(opposed_by_freq_one) + Counter(opposed_by_freq_two)
    opposed_by_freq = {k: opposed_by_freq_sum[k] for k in sorted(opposed_by_freq_sum)}

    if (
        len(opposed_freq)
        == len(supported_freq)
        == len(opposed_by_freq)
        == len(supported_by_freq)
        == 0
    ):
        max_date = "2019-01"
        min_date = "2001-01"
    else:
        min_date, max_date = find_maximum_interval(
            opposed_freq, supported_freq, opposed_by_freq, supported_by_freq
        )

    min_date_obj = datetime.strptime(min_date, "%Y-%m")
    max_date_obj = datetime.strptime(max_date, "%Y-%m")
    months_lst = month_list_fast(min_date_obj, max_date_obj)

    opposed_freq_month = get_all_months(opposed_freq, months_lst)
    supported_freq_month = get_all_months(supported_freq, months_lst)
    opposed_by_freq_month = get_all_months(opposed_by_freq, months_lst)
    supported_by_freq_month = get_all_months(supported_by_freq, months_lst)

    year_month_labels = list(opposed_by_freq_month.keys())
    opposed_freq = list(opposed_freq_month.values())
    supported_freq = list(supported_freq_month.values())
    opposed_by_freq = list(opposed_by_freq_month.values())
    supported_by_freq = list(supported_by_freq_month.values())

    return year_month_labels, opposed_freq, supported_freq, opposed_by_freq, supported_by_freq


def get_chart_labels(opposed_by_freq, opposed_freq, supported_by_freq, supported_freq):
    if (
            len(opposed_freq)
            == len(supported_freq)
            == len(opposed_by_freq)
            == len(supported_by_freq)
            == 0
    ):
        max_date = "1994"
        min_date = "2019"
    else:
        min_date, max_date = find_maximum_interval(
            opposed_freq, supported_freq, opposed_by_freq, supported_by_freq
        )
    all_years = []
    current_date = int(min_date)
    while current_date <= int(max_date):
        all_years.append(current_date)
        current_date += 1
    return [str(year) for year in all_years]


def fill_zero_values(labels, input_freq):
    """
    Make sures that 'input_freq' has as many entries as labels,
    by setting to 0 the every non-existent 'label' in input_freq
    """
    zero_filled_values = [0] * len(labels)
    for idx, label in enumerate(labels):
        if label in input_freq.keys():
            zero_filled_values[idx] = input_freq[label]
    return zero_filled_values


def build_relationships_by_year(wiki_id: str):
    """

    """

    # some personality can support another personality in two different relationship directions
    supported_freq_one = get_person_rels_by_year(wiki_id, "ent1_supports_ent2", ent="ent1")
    supported_freq_two = get_person_rels_by_year(wiki_id, "ent2_supports_ent1", ent="ent2")
    supported_freq_sum = Counter(supported_freq_one) + Counter(supported_freq_two)
    supported_freq = {k: supported_freq_sum[k] for k in sorted(supported_freq_sum)}

    # opposes
    opposed_freq_one = get_person_rels_by_year(wiki_id, "ent1_opposes_ent2", ent="ent1")
    opposed_freq_two = get_person_rels_by_year(wiki_id, "ent2_opposes_ent1", ent="ent2")
    opposed_freq_sum = Counter(opposed_freq_one) + Counter(opposed_freq_two)
    opposed_freq = {k: opposed_freq_sum[k] for k in sorted(opposed_freq_sum)}

    # supported_by
    supported_by_freq_one = get_person_rels_by_year(wiki_id, "ent2_supports_ent1", ent="ent1")
    supported_by_freq_two = get_person_rels_by_year(wiki_id, "ent1_supports_ent2", ent="ent2")
    supported_by_freq_sum = Counter(supported_by_freq_one) + Counter(supported_by_freq_two)
    supported_by_freq = {k: supported_by_freq_sum[k] for k in sorted(supported_by_freq_sum)}

    # opposed_by
    opposed_by_freq_one = get_person_rels_by_year(wiki_id, "ent2_opposes_ent1", ent="ent1")
    opposed_by_freq_two = get_person_rels_by_year(wiki_id, "ent1_opposes_ent2", ent="ent2")
    opposed_by_freq_sum = Counter(opposed_by_freq_one) + Counter(opposed_by_freq_two)
    opposed_by_freq = {k: opposed_by_freq_sum[k] for k in sorted(opposed_by_freq_sum)}

    # normalize intervals considering the 4 data points and fill in zero values
    labels = get_chart_labels(opposed_by_freq, opposed_freq, supported_by_freq, supported_freq)
    opposed_freq = fill_zero_values(labels, opposed_freq)
    supported_freq = fill_zero_values(labels, supported_freq)
    opposed_by_freq = fill_zero_values(labels, opposed_by_freq)
    supported_by_freq = fill_zero_values(labels, supported_by_freq)

    return labels, opposed_freq, supported_freq, opposed_by_freq, supported_by_freq



