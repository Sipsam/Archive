import java.io.*;
public class FileReadHangulFail{
  public static void main(String[] args) {
    InputStreamReaderin = null;
    FileInputStreamfin = null;
    try {
      fin = new FileInputStream("c:\\hangul.txt");
      in = new InputStreamReader(fin, "US-ASCII");
      int c;
      System.out.println("인코딩문자집합은" + in.getEncoding());
      while ((c = in.read()) != -1) {
        System.out.print((char)c);
      }
      in.close();
      fin.close();
    } catch (IOExceptione) {
      System.out.println("입출력오류");
    }
  }
}
