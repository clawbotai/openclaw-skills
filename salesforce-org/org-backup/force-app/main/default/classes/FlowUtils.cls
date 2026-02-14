public class FlowUtils {
    @InvocableMethod(label='Split String to Collection' description='Splits a string by a separator')
    public static List<List<String>> splitString(List<Requests> requests) {
        List<List<String>> results = new List<List<String>>();
        for (Requests req : requests) {
            if (req.inputString != null) {
                results.add(req.inputString.split(req.separator));
            } else {
                results.add(new List<String>());
            }
        }
        return results;
    }

    public class Requests {
        @InvocableVariable(label='Input String' required=true)
        public String inputString;
        @InvocableVariable(label='Separator' required=true)
        public String separator;
    }
}