from omero.cli import BaseControl, CLI, ExceptionHandler

import omero
from omero.rtypes import rlong
from omero.cmd import Delete2

from parse import parse

import signal
from time import time

import importlib

HELP = """Plugin for importing IDR ROIs"""


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
            "--format", help="Specify the format of the HDF5 file "
                             "(e.g. idr0012)")

        parser.add_argument(
            "--dry-run", action="store_true",
            help="Does not write anything to OMERO")

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

    def _getReader(self, args):
        try:
            name = "%sReader" % args.format.upper()
            mod = importlib.import_module(name)
            reader = getattr(mod, name)
            return reader
        except Exception:
            return None

    def importFile(self, args):
        self.ctx.out("Import ROIs from file %s for screen %s" %
                     (args.file, args.screenId))

        conn = self.ctx.conn(args)
        self.sf = conn.sf
        updateService = conn.sf.getUpdateService()
        queryService = conn.sf.getQueryService()

        imgpositions = self._mapImagePositionToId(queryService, args.screenId)
        total = len(imgpositions)
        print("Mapped %d image ids to plate positions" % total)

        done = 0
        start = time()
        readerClass = self._getReader(args)
        if readerClass is None:
            self.ctx.die(1, "No reader found for format %s" % args.format)

        with readerClass(args.file) as reader:
            for imgpos, rois in reader.nextROIs():
                if imgpos in imgpositions:
                    if args.dry_run:
                        self._saveROIs(rois, imgpositions[imgpos],
                                       queryService, None)
                    else:
                        self._saveROIs(rois, imgpositions[imgpos],
                                       queryService, updateService)
                else:
                    self.ctx.err("WARNING: Could not map image %s to"
                                 " an OMERO image id." % imgpos)
                done += 1

                if done % 100 == 0:
                    percDone = int(done * 100 / total)
                    duration = (time() - start) / 100
                    left = duration * (total - done)
                    m, s = divmod(left, 60)
                    h, m = divmod(m, 60)
                    start = time()
                    self.ctx.out("%d %% Done. ETR: %d:%02d:%02d hrs"
                                 % (percDone, h, m, s))

                if self.exitNow:
                    self.ctx.die(0, "")

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
