.. SplatNet 3 Scraper documentation master file, created by
   sphinx-quickstart on Mon Feb  6 22:45:28 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to SplatNet 3 Scraper's documentation!
==============================================

**SplatNet 3 Scraper** is a Python library for scraping data from the Splatoon 3
SplatNet 3 API. It is designed to be as lightweight as possible, with minimal
external dependencies to make it easy to use in any project.

**SplatNet 3 Scraper** started as a fork of `s3s 
<https://github.com/frozenpandaman/s3s>`_ but has since been rewritten from
scratch while incorporating much of the login flow logic of s3s. As a result, I
am deeply indebted to the authors of s3s for their work. This project would not
have been possible without their efforts.

See the :doc:`misc/quickstart` page for more information on how to use this library,
including how to :ref:`install <installation>` it. If you are interested in
contributing to this project, see the :doc:`misc/contributing` page.


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

Contents
========

.. toctree::
   :maxdepth: 1

   misc/quickstart
   misc/session_token
   misc/login_flow
   misc/queries
   misc/contributing
   api/scraper/scraper
   api/query/query
   api/auth/auth
   api/utils