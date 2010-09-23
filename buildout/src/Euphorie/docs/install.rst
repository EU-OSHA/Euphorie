Installation
============

Euphorie is implemented as a set of add-on products for `Plone`_. The
requirements for running an Euphorie site are:

* Plone 3.3 or later. Plone 4 is supported, but not recommended for production
  use at this moment.
* a SQL database

Plone instalation
-----------------
To install Euphorie you will first need to `download`_ and install Plone.
Euphorie requires Plone 3.3 or later.  After installing Plone you can install
Euphorie. To do this you will need to edit the ``buildout.cfg`` file of your
Plone installation. This file is normally located in the ``zinstance``
directory if your Plone install.  Look for an *eggs* line and add Euphorie
there::

  [buildout]
  ...
  eggs =
      Euphorie

This will instruct Plone to install the Euphorie software. Next you will
need to add some *zcml* entries to load the necessary configuration as well::

  [instance]
  ...
  zcml =
      euphorie.deployment-meta
      euphorie.deployment
      euphorie.deployment-overrides

After making these two changes you must (re)run buildout and restart your Zope
instance. Navigate to your ``zinstance`` directory and type::

    $ bin/buildout
    $ bin/plonectl restart

A new *Euphorie website* option should now appear in the list of add-on products
in your Plone control panel. Installing this will setup Euphorie in your site.

For more information on installing add-on products in your Plone site please
see the article `installing an add-on product`_ in the Plone knowledge base.

SQL database
------------

Euphorie uses a SQL database to store information for users of the client. Any
SQL database supported by SQLALchemy_ should work. If you have selected a
database you will need to configure it in ``buildout.cfg``. For example if
you use postgres you will first need to make sure that the psycopg_ driver
is installed by adding it to the *eggs* section::

  [buildout]
  ...
  eggs =
      Euphorie
      psycopg2

next you need to configure the database connection information. This requires
a somewhat verbose statement in the *instance* section of ``buildout.cfg``::

  [instance]
  zcml-additional =
     <configure xmlns="http://namespaces.zope.org/zope"
                xmlns:db="http://namespaces.zope.org/db">
         <include package="z3c.saconfig" file="meta.zcml" />
         <db:engine name="session" url="postgres:///euphorie" />
         <db:session engine="session" />
     </configure>

Make sure The ``url`` parameter is correct for the database you want to use.
It uses the standard SQLAlchemy connection URI format.

To setup the database you must run bulidout and restart the Plone instance
again::

    $ bin/buildout
    $ bin/plonectl restart

.. _Plone: http://plone.org/
.. _download: http://plone.org/download
.. _installing an add-on product: http://plone.org/documentation/kb/third-party-products/installing
.. _SQLAlchemy: http://sqlalchemy.org/
.. _psycopg: http://initd.org/psycopg/
