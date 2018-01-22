from ROIReader import ROIReader

import sys
from math import isnan

import omero
from omero.rtypes import rint, rstring

from tables import open_file


class IDR0016Reader(ROIReader):

    # Relevant columns in the HDF5 file
    COLUMN_IMAGENUMBER = "ImageNumber"
    COLUMN_WELLPOSITION = "Image_Metadata_CPD_WELL_POSITION"
    COLUMN_PLATEID = "Image_Metadata_PlateID"
    COLUMN_FIELD = "Image_Metadata_Site"

    NUCLEI_LOCATION_X = "Nuclei_Location_Center_X"
    NUCLEI_LOCATION_Y = "Nuclei_Location_Center_Y"
    CELLS_LOCATION_X = "Cells_Location_Center_X"
    CELLS_LOCATION_Y = "Cells_Location_Center_Y"
    CYTOPLASM_LOCATION_X = "Cytoplasm_Location_Center_X"
    CYTOPLASM_LOCATION_Y = "Cytoplasm_Location_Center_Y"

    def __init__(self, hdfFile):
        try:
            h5f = open_file(hdfFile, "a")
            objs = h5f.get_node("/Objects")
            imgnoColumn = objs.colinstances[self.COLUMN_IMAGENUMBER]
            if not imgnoColumn.is_indexed:
                sys.stdout.write("Create index for the image number column...")
                imgnoColumn.create_index()
        except Exception:
            sys.stderr.write("Could not create index. This will significantly "
                             "slow down reading performance!")
        finally:
            h5f.close()

        ROIReader.__init__(self, hdfFile)

    def _mapImageNumberToPosition(self):
        """
        Maps the ImageNumber in the HDF5 file to plate positions
        :param args: The arguments array
        :return: A dictionary mapping the ImageNumber in the HDF5 file to
                 plate positions (in form 'PlateName | Well | Field')
        """
        imgdict = {}
        try:
            imgs = self.h5f.get_node("/Images")

            # Map image number to image position (in form
            # 'PlateName | Well | Field')
            for row in imgs:
                well = row[self.COLUMN_WELLPOSITION]
                # Wells can have leading zero, e.g. A03, have to strip the zero
                # to match e.g. A3
                wella = well[0]
                wellb = "%d" % int(well[1:])
                well = wella + wellb
                imgpos = "%s | %s | %s" % (row[self.COLUMN_PLATEID], well,
                                           row[self.COLUMN_FIELD])
                imgdict[row[self.COLUMN_IMAGENUMBER]] = imgpos
        except Exception:
            sys.stderr.write("Could not map image numbers to plate positions.")
        return imgdict

    def nextROIs(self):
        imgNumbers = self._mapImageNumberToPosition()

        objs = self.h5f.get_node("/Objects")
        for imgNumber in imgNumbers:
            imgpos = imgNumbers[imgNumber]
            rois = []
            query = self.COLUMN_IMAGENUMBER + " == " + str(imgNumber)
            for row in objs.where(query):
                x = row[self.NUCLEI_LOCATION_X]
                y = row[self.NUCLEI_LOCATION_Y]
                if not (isnan(x) or isnan(y)):
                    roi = omero.model.RoiI()
                    point = omero.model.PointI()
                    point.x = x
                    point.y = y
                    point.theZ = rint(0)
                    point.theT = rint(0)
                    point.textValue = rstring("Nucleus")
                    roi.addShape(point)
                    rois.append(roi)

                x = row[self.CELLS_LOCATION_X]
                y = row[self.CELLS_LOCATION_Y]
                if not (isnan(x) or isnan(y)):
                    roi = omero.model.RoiI()
                    point = omero.model.PointI()
                    point.x = x
                    point.y = y
                    point.theZ = rint(0)
                    point.theT = rint(0)
                    point.textValue = rstring("Cell")
                    roi.addShape(point)
                    rois.append(roi)

                x = row[self.CYTOPLASM_LOCATION_X]
                y = row[self.CYTOPLASM_LOCATION_Y]
                if not (isnan(x) or isnan(y)):
                    roi = omero.model.RoiI()
                    point = omero.model.PointI()
                    point.x = x
                    point.y = y
                    point.theZ = rint(0)
                    point.theT = rint(0)
                    point.textValue = rstring("Cytoplasm")
                    roi.addShape(point)
                    rois.append(roi)

            yield imgpos, rois
