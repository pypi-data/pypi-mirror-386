# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015, 2016 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Custom errors for classifier."""


class ClassifierException(Exception):
    """Base exception for Invenio Classifier."""


class TaxonomyError(ClassifierException):
    """Error related to the Taxonomy parsing."""


class IncompatiblePDF2Text(ClassifierException):
    """Error raised when pdf2text program is incompatible."""


class OntologyError(ClassifierException):
    """Error with the classifier ontology."""
