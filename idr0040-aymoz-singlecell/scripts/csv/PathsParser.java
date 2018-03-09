package csv;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.FileReader;
import java.io.FileWriter;

public class PathsParser {

    public static void main(String[] args) throws Exception {
        
        /**
         * The filepaths.tsv needs another column for the image name.
         * 
         * This scripts takes the original filePaths.tsv containing lines like:
         * Dataset:name:YSP692_AGA1y_FIG1r_bar1D_DoseResponsePheromoneTreatment /uod/idr/filesets/idr0040-aymoz-singlecell/20180215/3105/Pos0 
         * 
         * ...and writes another filePath.tsv with an additional column for the image name:
         * Dataset:name:YSP692_AGA1y_FIG1r_bar1D_DoseResponsePheromoneTreatment /uod/idr/filesets/idr0040-aymoz-singlecell/20180215/3105/Pos0   Pos0
         * 
         * ... which is simply the last part of the file path 'PosX'.
         */
        
        String in = "/Users/dlindner/idr0040/idr0040-experimentB-filePaths.tsv";
        String out = "/Users/dlindner/idr0040/idr0040-experimentB-filePaths2.tsv";
        
        BufferedReader r = new BufferedReader(new FileReader(in));
        BufferedWriter w = new BufferedWriter(new FileWriter(out));
        
        String line = null;
        while((line = r.readLine())!=null) {
            String[] tmp = line.split("\t");
            String[] tmp2 = tmp[1].split("/");
            w.write(line+"\t"+tmp2[tmp2.length-1]+"\n");
        }
        r.close();
        w.close();
    }

}
