#!/usr/bin/env python

# -*- coding: utf-8 -*-

# Copyright (C) 2018 University of Dundee & Open Microscopy Environment.
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

# Suggests OMERO.cli commands to fix the idr0004 field-image mapping.
# author: m.t.b.carroll@dundee.ac.uk

from omero.gateway import BlitzGateway
from omero.rtypes import wrap
from omero.sys import ParametersI
import os

conn = BlitzGateway(
    os.environ.get('IDR_USER', 'root'),
    os.environ.get('IDR_PASSWORD', 'omero'),
    host=os.environ.get('IDR_HOST', 'localhost'))
conn.connect()
conn.setGroupForSession(3)  # Public

query_service = conn.getQueryService()

# Find the plates of idr0004.

query = """
SELECT child.id
  FROM ScreenPlateLink
  WHERE parent.name LIKE :name
"""

params = ParametersI()
params.add('name', wrap('idr0004-%'))

rows = query_service.projection(query, params)

plate_ids = [row[0].val for row in rows]

assert plate_ids

# Loop through each field of those plates.

query = """
SELECT id, image.name, image.fileset.id, well.row, well.column, well.plate.name
  FROM WellSample
  WHERE well.plate.id IN (:ids)
"""

params = ParametersI()
params.addIds(plate_ids)

rows = query_service.projection(query, params)

for row in rows:
    field_id = row[0].val
    image_name = row[1].val
    fileset_id = row[2].val
    well_row = row[3].val
    well_column = row[4].val
    plate_name = row[5].val

    # Figure the expected image name for this field.

    image_name_expected = '{} [Well {}{}, Field 1]' \
        .format(plate_name, chr(65 + well_row), 1 + well_column)

    if image_name == image_name_expected:
        continue

    # Wrong image, so find the correct image for this field.

    query = "SELECT id FROM Image WHERE name = :name AND fileset.id = :id"

    params = ParametersI()
    params.add('name', wrap(image_name_expected))
    params.addId(fileset_id)

    rows = query_service.projection(query, params)

    assert len(rows) == 1

    image_id_corrected = rows[0][0].val

    print('omero obj update WellSample:{} image=Image:{}'
          .format(field_id, image_id_corrected))

conn._closeSession()
