# -*- coding: utf-8 -*-
import base64
import json
import logging
import re
import os
import threading
import time

from Levenshtein import distance
from datetime import datetime
from difflib import SequenceMatcher
from fastDamerauLevenshtein import damerauLevenshtein
from odoo.osv.expression import OR
from operator import itemgetter
from pprint import pprint

_logger = logging.getLogger(__name__)

try:
    import xlrd

    try:
        from xlrd import xlsx
    except ImportError:
        xlsx = None
except ImportError:
    xlrd = xlsx = None

import math
import werkzeug
import logging
from odoo import fields as odoo_fields, http, _
from odoo.http import request
from odoo.exceptions import AccessError, MissingError, ValidationError, UserError
from odoo.http import request as req, local_redirect, Controller, content_disposition
from werkzeug import urls

_logger = logging.getLogger(__name__)