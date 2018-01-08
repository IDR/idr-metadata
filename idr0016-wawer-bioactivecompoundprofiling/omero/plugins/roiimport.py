from omero.cli import BaseControl, CLI, ExceptionHandler

import tables
import omero
from omero.rtypes import rint, rstring, rlong
from omero.cmd import Delete2

import parse
from time import time
from math import isnan

import signal

HELP = """Plugin for importing idr0016 ROIs"""

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


class ROIImportControl(BaseControl):

    exitNow = False

    def _configure(self, parser):
        signal.signal(signal.SIGINT, self._exitGracefully)
        signal.signal(signal.SIGTERM, self._exitGracefully)

        self.exc = ExceptionHandler()

        parser.add_login_arguments()

        parser.add_argument(
            "command", nargs="?",
            choices=("import", "remove"),
            help="The operation to be performed. CAUTION: 'remove' "
                 "will delete all ROIs of the screen!")

        parser.add_argument(
            "file",
            help="The HDF5 file")

        parser.add_argument(
            "screenId",
            help="The screen id")

        parser.add_argument(
            "--dry-run", action="store_true", help="Does not write anything "
                                                   "to OMERO")

        parser.set_defaults(func=self.process)

    def process(self, args):
        if not args.command:
            self.ctx.die(100, "No command provided")

        if args.command == "import":
            self.importFile(args)

        if args.command == "remove":
            self.remove(args)

    def _exitGracefully(self, signum, frame):
        self.ctx.out("Caught exit signal, will stop when current transaction "
                     "is finished.")
        self.exitNow = True

    def _mapImagePositionToId(self, queryService, screenid):
        """
        Map all image names (in form 'PlateName | Well | Field')
        to their OMERO image ids
        :param queryService: Reference to the query service
        :param screenid: The screen id
        :return: A dictionary mapping 'PlateName | Well | Field'
                to the image ID
        """
        params = omero.sys.Parameters()
        params.map = {"sid": rlong(screenid)}
        query = "select i.id, i.name from Screen s " \
                "right outer join s.plateLinks as pl " \
                "join pl.child as p " \
                "right outer join p.wells as w " \
                "right outer join w.wellSamples as ws " \
                "join ws.image as i " \
                "where s.id = :sid"
        imgdic = {}
        for e in queryService.projection(query, params):
            imgId = e[0].val
            imgName = e[1].val
            p = parse("{} [Well {}, Field {}]", imgName)
            imgName = "%s | %s | %s" % (p[0], p[1], p[2])
            imgdic[imgName] = imgId

        return imgdic

    def _mapImageNumberToPosition(self, args):
        """
        Maps the ImageNumber in the HDF5 file to plate positions
        :param args: The arguments array
        :return: A dictionary mapping the ImageNumber in the HDF5 file to
                 plate positions (in form 'PlateName | Well | Field')
        """
        imgdict = {}
        h5f = open_file(args.file, "r")
        try:
            imgs = h5f.get_node("/Images")

            # Map image number to image position (in form
            # 'PlateName | Well | Field')
            for row in imgs:
                well = row[COLUMN_WELLPOSITION]
                # Wells can have leading zero, e.g. A03, have to strip the zero
                # to match e.g. A3
                wella = well[0]
                wellb = "%d" % int(well[1:])
                well = wella + wellb
                imgpos = "%s | %s | %s" % (row[COLUMN_PLATEID], well,
                                           row[COLUMN_FIELD])
                imgdict[row[COLUMN_IMAGENUMBER]] = imgpos

        finally:
            h5f.close()

        return imgdict

    def _getROICount(self, queryService, imgId):
        try:
            params = omero.sys.Parameters()
            params.map = {"imageId": rlong(imgId)}
            query = "select count(*) from Roi as roi " \
                    "where roi.image.id = :imageId"
            count = queryService.projection(query, params)
            return count[0][0]._val

        except:
            self.ctx.err("Could not get ROI count for image %s" % str(imgId))
            return 1

    def _saveROIs(self, rois, imgId, queryService, updateService):
        """
        Save the ROIs back to OMERO
        :param rois: A list of ROIs
        :param imgId: The image ID to attach the ROIs to
        :param queryService: Reference to the query service
        :param updateService: Reference to the update service
               (can be None to simulate a 'dry-run')
        :return:
        """
        try:
            if self._getROICount(queryService, imgId) > 0:
                self.ctx.out("Skipping image %s, already has "
                             "ROIs attached." % imgId)

            else:
                image = queryService.get("Image", imgId)
                for roi in rois:
                    roi.setImage(image)

                if updateService:
                    updateService.saveCollection(rois)
                    self.ctx.out("Saved %d ROIs for Image %s" %
                                 (len(rois), imgId))
                else:
                    self.ctx.out("Dry run - Would save %d ROIs for Image %s" %
                                 (len(rois), imgId))

        except:
            self.ctx.err("WARNING: Could not save the ROIs for Image %s" %
                         imgId)

    def importFile(self, args):
        self.ctx.out("Import ROIs from file %s for screen %s" %
                     (args.file, args.screenId))

        conn = self.ctx.conn(args)
        self.sf = conn.sf
        updateService = conn.sf.getUpdateService()
        queryService = conn.sf.getQueryService()

        imgIds = self._mapImagePositionToId(queryService, args.screenId)
        self.ctx.out("Mapped %d OMERO image ids to plate positions" %
                     len(imgIds))

        imgNumbers = self._mapImageNumberToPosition(args)
        total = len(imgNumbers)
        self.ctx.out("Found %d images in HDF5 file" % total)

        h5f = open_file(args.file, "a")
        try:
            objs = h5f.get_node("/Objects")
            self.ctx.out("Found %d objects in HDF5 file" % len(objs))
            done = 0

            imgnoColumn = objs.colinstances[COLUMN_IMAGENUMBER]
            if not imgnoColumn.is_indexed:
                self.ctx.out("Create index for the image number column...")
                imgnoColumn.create_index()

            start = time()
            for imgNumber in imgNumbers:
                pos = imgNumbers[imgNumber]
                done += 1
                if pos in imgIds:
                    imgId = imgIds[pos]
                    rois = []
                    query = COLUMN_IMAGENUMBER+" == "+str(imgNumber)
                    for row in objs.where(query):
                        x = row[NUCLEI_LOCATION_X]
                        y = row[NUCLEI_LOCATION_Y]
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

                        x = row[CELLS_LOCATION_X]
                        y = row[CELLS_LOCATION_Y]
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

                        x = row[CYTOPLASM_LOCATION_X]
                        y = row[CYTOPLASM_LOCATION_Y]
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

                    if args.dry_run:
                        self._saveROIs(rois, imgId, queryService, None)
                    else:
                        self._saveROIs(rois, imgId, queryService,
                                       updateService)

                else:
                    self.ctx.err("WARNING: Could not map image %s to"
                                 " an OMERO image id." % pos)

                self.ctx.out("%d of %d images (%d %%) processed." %
                             (done, total, done * 100 / total))

                if self.exitNow:
                    h5f.close()
                    exit(0)

                if done % 100 == 0:
                    duration = (time() - start) / 100
                    left = duration * (total - done)
                    m, s = divmod(left, 60)
                    h, m = divmod(m, 60)
                    start = time()
                    self.ctx.out("ETR: %d:%02d:%02d hrs" % (h, m, s))

        finally:
            h5f.close()

    def remove(self, args):
        self.ctx.out("Delete ROIs for screen %s" % args.screenId)

        conn = self.ctx.conn(args)
        queryService = conn.sf.getQueryService()

        params = omero.sys.Parameters()
        params.map = {"sid": rlong(args.screenId)}
        query = "select r.id from Screen s " \
                "right outer join s.plateLinks as pl " \
                "join pl.child as p " \
                "right outer join p.wells as w " \
                "right outer join w.wellSamples as ws " \
                "join ws.image as i " \
                "join i.rois as r " \
                "where s.id = :sid"
        roiIds = []
        for e in queryService.projection(query, params):
            roiIds.append(e[0].val)

        delete = Delete2(targetObjects={'Roi': roiIds})
        conn.sf.submit(delete)


try:
    register("roiimport", ROIImportControl, HELP)
except NameError:
    if __name__ == "__main__":
        cli = CLI()
        cli.register("roiimport", ROIImportControl, HELP)
        cli.invoke(sys.argv[1:])
