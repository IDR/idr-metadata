package csv;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.FileReader;
import java.io.FileWriter;
import java.util.HashSet;

public class RemoveDuplicateRows {

    public static void main(String[] args) throws Exception {
        /**
         * The original annotations.csv contains a row for every timepoint, i.e. many rows like
         * YSP692_AGA1y_FIG1r_bar1D_DoseResponsePheromoneTreatment, 3105/Pos0, ...
         * YSP692_AGA1y_FIG1r_bar1D_DoseResponsePheromoneTreatment, 3105/Pos0, ...
         * YSP692_AGA1y_FIG1r_bar1D_DoseResponsePheromoneTreatment, 3105/Pos0, ...
         * ...
         * YSP692_AGA1y_FIG1r_bar1D_DoseResponsePheromoneTreatment, 3105/Pos1, ...
         * YSP692_AGA1y_FIG1r_bar1D_DoseResponsePheromoneTreatment, 3105/Pos1, ...
         * YSP692_AGA1y_FIG1r_bar1D_DoseResponsePheromoneTreatment, 3105/Pos1, ...
         * ...
         * 
         * This script creates a new annotations.csv which only contains one row per DatasetName/ImageName 
         * combination, i.e. will create something like:
         * YSP692_AGA1y_FIG1r_bar1D_DoseResponsePheromoneTreatment, 3105/Pos0, ...
         * YSP692_AGA1y_FIG1r_bar1D_DoseResponsePheromoneTreatment, 3105/Pos1, ...
         * ...
         */
        
        String in = "/Users/dlindner/Repositories/idr-metadata/idr0040-aymoz-singlecell/experimentA/idr0040-experimentA-annotation.csv";
        String out = "/Users/dlindner/Repositories/idr-metadata/idr0040-aymoz-singlecell/experimentA/idr0040-experimentA-annotation2.csv";
        
        BufferedReader r = new BufferedReader(new FileReader(in));
        BufferedWriter w = new BufferedWriter(new FileWriter(out));
        
        // Holds the already processed 'keys'
        // (A 'key' is just a concatenation of the Dateset/Imagename, e. g.
        // YSP692_AGA1y_FIG1r_bar1D_DoseResponsePheromoneTreatment3105/Pos0)
        HashSet<String> unique = new HashSet<String>();
        
        String line = null;
        while((line = r.readLine())!=null) {
            String[] tmp = line.split(",");
            String key = tmp[0].trim()+tmp[1].trim();
            if(!unique.contains(key)) {
                unique.add(key);
                w.write(line+"\n");
            }
        }
        r.close();
        w.close();
    }

}
