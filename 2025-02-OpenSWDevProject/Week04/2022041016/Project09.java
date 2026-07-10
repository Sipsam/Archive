public class GarbageEx{
  public static void main(String[] args){
    String a = new String("Good");
    String b = new String("Bad");
    String c = new String("Normal");
    String d, e;
    a = null; // String("Good") is garbage
    d = c;
    c = null;
  } // after finishing this main func, all objects, "Good", "Bad", and "Normal" are garbages
}
