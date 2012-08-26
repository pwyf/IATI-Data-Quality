from datetime import time

# provide variables from xpath API

def title_exists(activity):
    """
    Description: Title exists
    Group: title
    """
    thetitle = activity.find('title').text
    if (thetitle is None):
        return False
    else:
        return True

def title_greater_than_10_characters(activity):
    """
    Description: Title is greater than 10 characters
    Group: title
    """
    thetitle = activity.find('title').text
    if ((thetitle is not None) and (len(thetitle)>10)):
	    return True
    else:
        return False

def description_exists(activity):
    """
    Description: Description exists
    Group: description
    """
    thedescription = activity.find('description').text
    if (thedescription is None):
        return False
    else:
        return True

def description_greater_than_40_characters(activity):
    """
    Description: Description is greater than 40 characters
    Group: description
    """
    thedescription = activity.find('description').text
    if ((thedescription is not None) and (len(thedescription)>40)):
	    return True
    else:
        return False

def only_one_activity_status(activity):
    """
    Description: there should not be more than one activity status
    Group: activity-status
    """
    thestatus = activity.findall('activity-status')
    if ((thestatus is not None) and (count(thestatus)<=1)):
	    return True
    else:
        return False

def activity_status_exists(activity):
    """
    Description: there should be an activity status
    Group: activity-status
    """
    thestatus = activity.find('activity-status')
    if (thestatus is not None):
	    return True
    else:
        return False

def activity_date_iso_date_exists(activity):
    """
    Description: Activity Date ISO date exists
    Group: activity-date
    """
    # Should also check whether it's in the format YYYY-MM-DD
    thedates = activity.findall('activity-date')
    check = True
    for date in thedates:
        thedate = date.get('iso-date')
        if (thedate is None):
            check = False
        else:
            time.strptime(thedate, "%Y-%m-%d")
    return check

def activity_date_start_planned_exists(activity):
    """
    Description: Activity Date - Planned start date exists
    Group: activity-date
    """
    thedate = activity.xpath("//activity-date[@type='start-planned']")
    if (thedate is None):
        return False
    else:
        return True

def activity_date_end_planned_exists(activity):
    """
    Description: Activity Date - Planned end date exists
    Group: activity-date
    """
    thedate = activity.xpath("//activity-date[@type='end-planned']")
    if (thedate is None):
        return False
    else:
        return True

def activity_date_start_actual_exists(activity):
    """
    Description: Activity Date - Actual start date exists
    Group: activity-date
    """
    thedate = activity.xpath("//activity-date[@type='start-actual']")
    if (thedate is None):
        return False
    else:
        return True

def activity_date_end_actual_exists(activity):
    """
    Description: Activity Date - Actual end date exists
    Group: activity-date
    """
    thedate = activity.xpath("//activity-date[@type='end-actual']")
    if (thedate is None):
        return False
    else:
        return True

def funding_organisation_exists(activity):
    """
    Description: Funding organisation exists
    Group: participating-org
    """
    theorg = activity.xpath("//participating-org[@role='funding']")
    if (theorg is None):
        return False
    else:
        return True

def accountable_organisation_exists(activity):
    """
    Description: Accountable organisation exists
    Group: participating-org
    """
    theorg = activity.xpath("//participating-org[@role='accountable']")
    if (theorg is None):
        return False
    else:
        return True

def extending_organisation_exists(activity):
    """
    Description: Extending organisation exists
    Group: participating-org
    """
    theorg = activity.xpath("//participating-org[@role='extending']")
    if (theorg is None):
        return False
    else:
        return True

def implementing_organisation_exists(activity):
    """
    Description: Implementing organisation exists
    Group: participating-org
    """
    theorg = activity.xpath("//participating-org[@role='implementing']")
    if (theorg is None):
        return False
    else:
        return True

def recipient_region_or_country_exists(activity):
    """
    Description: Either a recipient region or country exists
    Group: recipient-country-region
    """
    thecountry = activity.find('recipient-country')
    theregion = activity.find('recipient-region')
    if (thecountry or theregion):
        return False
    else:
        return True

def recipient_region_and_country_exists(activity):
    """
    Description: Recipient country is not used if recipient region is used, and vice-versa.
    Group: recipient-country-region
    """
    thecountry = activity.find('recipient-country')
    theregion = activity.find('recipient-region')
    if ((thecountry is None) and (theregion is None)):
        return True
    else:
        if (thecountry and theregion):
            return False
        else:
            return True

def recipient_country_percentages_are_valid(activity):
    """
    Description: Recipient country percentages are integers.
    Group: recipient-country-region
    """
    countries = activity.findall('recipient-country')
    check = True
    for country in countries:
        if (country.get('percentage')):
            try:
                int(country.get('percentage'))
                check = True
            except Exception, e:
                check = False
        else:
            check = True
    return check

def recipient_country_percentages_add_up_to_100(activity):
    """
    Description: Recipient country percentages add up to 100%, if they exist.
    Group: recipient-country-region
    """
    countries = activity.findall('recipient-country')
    percentages_exist = False
    check = True
    amount = 0
    for country in countries:
        if (country.get('percentage')):
            percentages_exist = True
            try:
                amount = amount + int(country.get('percentage'))
            # there's some other weird problem, e.g. not integers, so not possible to add up to 100
            except Exception, e:
                check = False
    if ((percentages_exist) and (amount!=100)):
        check = False
    return check

def recipient_region_percentages_are_valid(activity):
    """
    Description: Recipient region percentages are integers.
    Group: recipient-country-region
    """
    regions = activity.findall('recipient-region')
    check = True
    for region in regions:
        if (region.get('percentage')):
            try:
                int(region.get('percentage'))
                check = True
            except Exception, e:
                check = False
        else:
            check = True
    return check

def recipient_region_percentages_add_up_to_100(activity):
    """
    Description: Recipient region percentages add up to 100%, if they exist.
    Group: recipient-country-region
    """
    regions = activity.findall('recipient-region')
    percentages_exist = False
    check = True
    amount = 0
    for region in regions:
        if (region.get('percentage')):
            percentages_exist = True
            try:
                amount = amount + int(region.get('percentage'))
            # there's some other weird problem, e.g. not integers, so not possible to add up to 100
            except Exception, e:
                check = False
    if ((percentages_exist) and (amount!=100)):
        check = False
    return check

def sector_exists(activity):
    """
    Description: At least one sector exists
    Group: sector
    """
    thesector = activity.find('sector')
    if (thesector is None):
        return False
    else:
        return True

def multiple_sectors_exist(activity):
    """
    Description: Multiple sectors exist
    Group: sector
    """
    thesector = activity.findall('sector')
    if (count(thesector)>1):
        return True
    else:
        return False

if __name__ == "__main__":
    print "Ran OK"
