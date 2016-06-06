# -*- coding: UTF-8 -*-
from euphorie.client import model
from sqlalchemy.engine.reflection import Inspector
from z3c.saconfig import Session
from zope.sqlalchemy import datamanager
import logging

log = logging.getLogger(__name__)


def add_column_for_always_present_risks(context):
    session = Session()
    inspector = Inspector.from_engine(session.bind)
    columns = [c['name']
               for c in inspector.get_columns(model.Risk.__table__.name)]
    if 'always_present' not in columns:
        log.info('Adding always_present column for risks')
        session.execute(
            "ALTER TABLE %s ADD always_present BOOL NOT NULL DEFAULT FALSE" %
            model.Risk.__table__.name)
        datamanager.mark_changed(session)
