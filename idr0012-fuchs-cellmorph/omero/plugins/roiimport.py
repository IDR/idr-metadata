from omero.cli import BaseControl, CLI, ExceptionHandler

from tables import open_file
import omero
from omero.rtypes import rint, rstring, rlong
from omero.cmd import Delete2

from parse import parse
from time import time
from math import isnan

import signal

HELP = """Plugin for importing idr0012 ROIs"""

# Relevant columns in the HDF5 file
COLUMN_X = "x"
COLUMN_Y = "y"
COLUMN_CLASS = "class"
COLUMN_FIELD = "spot"


class ROIImportControl(BaseControl):

    exitNow = False
    cellClasses = {}

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

        self.cellClasses = {'AF': 'Actin fibre',
                            'BC': 'Big cell',
                            'C': 'Condensed cell',
                            'D': 'Debris',
                            'LA': 'Lamellipodia',
                            'M': 'Metaphase',
                            'MB': 'Membrane blebbing',
                            'N': 'Normal cell',
                            'P': 'Protrusion/Elongation',
                            'Z': 'Telophase'}

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

    def _getROICount(self, queryService, imgId):
        try:
            params = omero.sys.Parameters()
            params.map = {"imageId": rlong(imgId)}
            query = "select count(*) from Roi as roi " \
                    "where roi.image.id = :imageId"
            count = queryService.projection(query, params)
            return count[0][0]._val

        except Exception:
            self.ctx.err("Could not get ROI count for image %s" % str(imgId))
            return 0

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

        except Exception:
            self.ctx.err("WARNING: Could not save the ROIs for Image %s" %
                         imgId)

    def importFile(self, args):
        self.ctx.out("Import ROIs from file %s for screen %s" %
                     (args.file, args.screenId))

        conn = self.ctx.conn(args)
        self.sf = conn.sf
        updateService = conn.sf.getUpdateService()
        queryService = conn.sf.getQueryService()

        imgpos = self._mapImagePositionToId(queryService, args.screenId)
        total = len(imgpos)

        h5f = open_file(args.file, "r")
        try:
            done = 0
            start = time()
            for plate in h5f.iter_nodes(h5f.root):
                for well in h5f.iter_nodes(plate):
                    rois = {}
                    for row in well.iterrows():
                        x = row[COLUMN_X]
                        y = row[COLUMN_Y]
                        cl = row[COLUMN_CLASS]
                        fld = row[COLUMN_FIELD]

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
                        done += 1
                        # remove leading zeros
                        wella = well._v_name[0]
                        wellb = "%d" % int(well._v_name[1:])
                        wellname = wella + wellb
                        posid = '%s | %s | %s' % (plate._v_name, wellname, fld)

                        if posid in imgpos:
                            if args.dry_run:
                                self._saveROIs(rois[fld], imgpos[posid],
                                               queryService, None)
                            else:
                                self._saveROIs(rois[fld], imgpos[posid],
                                               queryService, updateService)
                        else:
                            self.ctx.err("WARNING: Could not map image %s to"
                                         " an OMERO image id." % posid)

                        if self.exitNow:
                            h5f.close()
                            self.ctx.die(0, "")

                        self.ctx.out("%d of %d images (%d %%) processed." %
                                     (done, total, done * 100 / total))

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
        cli.invoke(omero.sys.argv[1:])
