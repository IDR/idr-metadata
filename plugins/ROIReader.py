from tables import open_file


class ROIReader:

    def __init__(self, hdfFile):
        self.h5f = open_file(hdfFile, "r")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.h5f.close()

    def nextROIs(self):
        """
        Get the next batch of ROIs for an Image
        :return: Image position in form 'PlateName | Well | Field'
                 and a list of ROIs for this image
        """
        raise NotImplementedError("Not implemented yet")
