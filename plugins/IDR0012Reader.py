from ROIReader import ROIReader

from math import isnan

import omero
from omero.rtypes import rint, rstring


class IDR0012Reader(ROIReader):

    # Relevant columns in the HDF5 file
    COLUMN_X = "x"
    COLUMN_Y = "y"
    COLUMN_CLASS = "class"
    COLUMN_FIELD = "spot"

    cellClasses = {'AF': 'Actin fibre',
                   'BC': 'Big cell',
                   'C': 'Condensed cell',
                   'D': 'Debris',
                   'LA': 'Lamellipodia',
                   'M': 'Metaphase',
                   'MB': 'Membrane blebbing',
                   'N': 'Normal cell',
                   'P': 'Protrusion/Elongation',
                   'Z': 'Telophase'}

    def nextROIs(self):

        for plate in self.h5f.iter_nodes(self.h5f.root):
            for well in self.h5f.iter_nodes(plate):
                rois = {}
                for row in well.iterrows():
                    x = row[self.COLUMN_X]
                    y = row[self.COLUMN_Y]
                    cl = row[self.COLUMN_CLASS]
                    fld = row[self.COLUMN_FIELD]

                    if not (isnan(x) or isnan(y)):
                        roi = omero.model.RoiI()
                        point = omero.model.PointI()
                        point.x = x
                        point.y = y
                        point.theZ = rint(0)
                        point.theT = rint(0)
                        if cl:
                            if cl in self.cellClasses:
                                point.textValue = rstring(
                                    self.cellClasses[cl])
                            else:
                                point.textValue = rstring(cl)

                        roi.addShape(point)

                        if fld not in rois:
                            rois[fld] = []

                        rois[fld].append(roi)

                for fld in rois:
                    wella = well._v_name[0]
                    wellb = "%d" % int(well._v_name[1:])
                    wellname = wella + wellb
                    imgpos = '%s | %s | %s' % (plate._v_name, wellname, fld)
                    yield imgpos, rois[fld]
