public with sharing class TimeParsingController {
    
    @InvocableMethod(label='Parse Time String' description='Converts string (e.g. 08:00 AM) to Time object' category='Utility')
    public static List<Time> parseTime(List<String> checkTimes) {
        List<Time> resultTimes = new List<Time>();
        for(String s : checkTimes) {
            if(String.isBlank(s)) {
                resultTimes.add(null);
                continue;
            }
            try {
                // Normalize
                s = s.trim().toUpperCase();
                Integer hours = 0;
                Integer minutes = 0;
                Boolean isPM = s.contains('PM');
                Boolean isAM = s.contains('AM');
                
                // Remove AM/PM for parsing
                String clean = s.replace('AM', '').replace('PM', '').trim();
                
                List<String> parts = clean.split(':');
                if(parts.size() > 0) hours = Integer.valueOf(parts[0]);
                if(parts.size() > 1) minutes = Integer.valueOf(parts[1]);
                
                // 12-hour adjustment
                if(isPM && hours < 12) hours += 12;
                if(isAM && hours == 12) hours = 0;
                
                resultTimes.add(Time.newInstance(hours, minutes, 0, 0));
            } catch(Exception e) {
                // Fallback or Null? System will fail if we throw. Let's return null to allow flow handling?
                // Or try standard JSON deserialize
                try {
                     resultTimes.add((Time)JSON.deserialize('"' + s + '"', Time.class));
                } catch(Exception e2) {
                     resultTimes.add(null);
                }
            }
        }
        return resultTimes;
    }
}