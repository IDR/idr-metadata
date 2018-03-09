package csv;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.FileReader;
import java.io.FileWriter;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashSet;

public class Parser {

    /**
     * Merges several CSV files into a single CSV file.
     * First line of the CSV files must be a header line!
     */
    
    static final String[] files = {
            "/Users/dlindner/idr0040/idr0000-experimentB-assays_DoseResponsesSupFigs.csv",
            "/Users/dlindner/idr0040/idr0000-experimentB-assays_MatingFig.csv",
            "/Users/dlindner/idr0040/idr0000-experimentB-assays_PheromoneTmtMainFig.csv",
            "/Users/dlindner/idr0040/idr0000-experimentB-assays_PheromoneTmtSupFig.csv"};

    static final String outFile = "/Users/dlindner/idr0040/annotations.csv";

    public static void main(String[] args) throws Exception {
        BufferedWriter out = new BufferedWriter(new FileWriter(outFile));

        // Parse first line of each file to get the headers
        HashSet<String> tmp = new LinkedHashSet<String>();
        for (String file : files) {
            BufferedReader in = new BufferedReader(new FileReader(file));
            String line = in.readLine();
            String[] split = split(line);
            for (String s : split) {
                if (s.length() > 0 && !s.startsWith("#"))
                    tmp.add(s);
            }
            in.close();
        }

        // The headers
        String[] headers = new String[tmp.size()];
        // The headers mapped to their position (column index) in the output file
        HashMap<String, Integer> pos = new HashMap<String, Integer>();
        int i = 0;
        for (String header : tmp) {
            headers[i] = header;
            pos.put(header, new Integer(i));
            i++;
        }

        // write header line
        out.write(join(headers) + "\n");

        // merge the input csv files together
        for (String file : files) {
            BufferedReader in = new BufferedReader(new FileReader(file));
            String line = in.readLine();
            
            // the headers of this particular input csv
            String[] thisHeaders = split(line);

            while ((line = in.readLine()) != null) {
                String[] parts = split(line);
                
                // the assembled output line
                String[] outline = new String[headers.length];
                
                // iterate over each column
                for (int col = 0; col < parts.length; col++) {
                    if (parts[col].startsWith("#"))
                        continue;
                    
                    // get the correct column index for the output
                    Integer outIndex = pos.get(thisHeaders[col]);
                    if (outIndex != null)
                        outline[outIndex.intValue()] = parts[col];
                }
                out.write(join(outline) + "\n");
            }
            in.close();
        }

        out.close();
    }

    /**
     * Split (on comma) and trim a String
     * @param input
     * @return
     */
    private static String[] split(String input) {
        String[] res = input.split(",");
        for (int i = 0; i < res.length; i++)
            res[i] = res[i].trim();
        return res;
    }

    /**
     * Assemble an array of String into an csv String
     * @param input
     * @return
     */
    private static String join(String[] input) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < input.length; i++) {
            sb.append(input[i] == null ? "" : input[i]);
            if (i < input.length - 1)
                sb.append(',');
        }
        return sb.toString();
    }

}
