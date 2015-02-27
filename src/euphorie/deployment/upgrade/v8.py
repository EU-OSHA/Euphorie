# -*- coding: UTF-8 -*-
from euphorie.client import model
from euphorie.content.user import IUser
from euphorie.deployment import setuphandlers
from plone import api
from plone.dexterity import utils
from sqlalchemy.engine.reflection import Inspector
from z3c.form.interfaces import IDataManager
from z3c.saconfig import Session
from zope.sqlalchemy import datamanager
import logging
import zope.component

log = logging.getLogger(__name__)


def hash_passwords(context):
    """ Make sure IUser passwords are hashed before they're stored in the ZODB.
    """
    catalog = api.portal.get_tool('portal_catalog')
    ps = catalog(object_provides='euphorie.content.user.IUser')
    for p in ps:
        o = p.getObject()
        password = o.password
        if type(password) == str and len(password) == 60:
            log.info('Not hashing password for "%s". Appears to be hashed '
                     'already.' %  p.getPath())
            continue
        elif password is None:
            log.info('Not hashing password for "%s". No password set'
                    %  p.getPath())
            continue

        for schema in utils.iterSchemata(o):
            field = schema.get('password')
            if field and field.interface == IUser:
                dm = zope.component.getMultiAdapter(
                    (o, field), IDataManager).set(password)


def register_password_policy(context):
    setuphandlers.registerPasswordPolicy(context)


def add_column_for_custom_risks(context):
    session = Session()
    inspector = Inspector.from_engine(session.bind)
    columns = [c['name']
               for c in inspector.get_columns(model.Risk.__table__.name)]
    if 'is_custom_risk' not in columns:
        log.info('Adding is_custom_risk column for risks')
        session.execute(
            "ALTER TABLE %s ADD is_custom_risk BOOL NOT NULL DEFAULT FALSE" %
            model.Risk.__table__.name)
        datamanager.mark_changed(session)
