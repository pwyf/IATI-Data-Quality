
#  IATI Data Quality, tools for Data QA on IATI-formatted  publications
#  by Mark Brough, Martin Keegan, Ben Webb and Jennifer Smith
#
#  Copyright (C) 2013  Publish What You Fund
#
#  This programme is free software; you may redistribute and/or modify
#  it under the terms of the GNU Affero General Public License v3.0

from flask import Flask, render_template, flash, request, Markup, \
    session, redirect, url_for, escape, Response, abort, send_file
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import login_required, current_user

from iatidataquality import app
from iatidataquality import db
import usermanagement 

from iatidq import dqusers, util, dqorganisations, dqtests, dqindicators, \
    dqcodelists

import unicodecsv
import json

import lxml.etree

import os
from sqlite3 import dbapi2 as sqlite
from sample_work import sample_work
from sample_work import db as sample_db
from sample_work import test_mapping

def memodict(f):
    """ Memoization decorator for a function taking a single argument """
    class memodict(dict):
        def __missing__(self, key):
            ret = self[key] = f(key)
            return ret 
    return memodict().__getitem__

@memodict
def get_test_info(test_id):
    return dqtests.tests(test_id)

@memodict
def get_test_indicator_info(test_id):
    return dqindicators.testIndicator(test_id)

@memodict
def get_org_info(organisation_id):
    return dqorganisations.organisation_by_id(organisation_id)

def get_response(kind, response):
    kind_data = test_mapping.kind_to_status[kind]
    response_data = kind_data.get(response)
    if response_data is not None:
        return response_data
    return {
              "text:": "not yet sampled",
              "button": "not yet sampled",
              "icon": "info-sign",
              "class": "warning",
            }

def kind_to_list(kind):
    kind_data = test_mapping.kind_to_status[kind]
    kind_data = map(lambda x: (x[1]), kind_data.items())
    return kind_data

def make_sample_json(work_item):
    document_category_codes = dqcodelists.reformatCodelist('DocumentCategory')
    document_links = sample_work.DocumentLinks(work_item["xml_data"], 
                                               document_category_codes)
    results = sample_work.Results(work_item["xml_data"])
    locations = sample_work.Locations(work_item["xml_data"])
    docs = [ dl.to_dict() for dl in document_links.get_links() ]

    if work_item["test_kind"] == "location":
        locs = [ ln.to_dict() for ln in locations.get_locations() ]
    else:
        locs = []

    if work_item["test_kind"] == "result":
        res = [ ln.to_dict() for ln in results.get_results() ]
    else:
        res = []

    activity_info = sample_work.ActivityInfo(work_item["xml_data"])

    work_item_test = get_test_info(work_item["test_id"])
    work_item_indicator = get_test_indicator_info(work_item["test_id"])
    work_item_org = get_org_info(work_item["organisation_id"])

    ## this should be done in the driver, not the webserver!
    xml = lxml.etree.tostring(lxml.etree.fromstring(work_item['xml_data']), 
                              method='xml', pretty_print=True)

    data = { "sample": {
                "iati-identifier": work_item["activity_id"],
                "documents": docs,
                "locations": locs,
                "results": res,
                "sampling_id": work_item["uuid"],
                "test_id": work_item["test_id"],
                "organisation_id": work_item["organisation_id"],
                "activity_title": activity_info.title,
                "activity_description": activity_info.description,
                "test_kind": work_item["test_kind"],
                "xml": xml,
            },
            "headers": {
                "test_name": work_item_test.name,
                "test_description": work_item_test.description,
                "indicator_name": work_item_indicator.description,
                "indicator_description": work_item_indicator.longdescription,
                "organisation_name": work_item_org.organisation_name,
                "organisation_code": work_item_org.organisation_code,
            },
            "buttons": kind_to_list(work_item["test_kind"]),
        }
    if 'response' in work_item:
        data['response'] = get_response(work_item["test_kind"], 
					work_item['response'])

    return data


@app.route("/api/sampling/process/<response>", methods=['POST'])
def api_sampling_process(response):
    data = request.form
    try:
        assert 'sampling_id' in data
        work_item_uuid = data["sampling_id"]
        response = int(response)
        sample_db.save_response(work_item_uuid, response)
        return 'OK'
    except Exception as e:
        return 'ERROR'


work_items = sample_db.work_item_generator(make_sample_json)

@app.route("/api/sampling/")
def api_sampling():
    try:
        results = work_items.next()
    except StopIteration:
        results = {
            "error": "Finished"
            }
    except:
        results = {
            "error": "Unknown"
            }
    return json.dumps(results, indent=2)
                          

@app.route("/sampling/")
#@usermanagement.perms_required()
def sampling():
    return render_template("sampling.html",
         admin=usermanagement.check_perms('admin'),
         loggedinuser=current_user)

@app.route("/sampling/list/")
#@usermanagement.perms_required()
def sampling_list():
    samples = []
    for wi in sample_db.read_db_response():
        samples.append(make_sample_json(wi))
    return render_template("sampling_list.html",
         admin=usermanagement.check_perms('admin'),
         loggedinuser=current_user,
         samples=samples)