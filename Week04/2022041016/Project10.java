class Sample{
  public int a;
  private int b;
  int c; // 디폴트 접근 지정
}
public class AccessEx{
  public static void main(String[] args){
    Sample aClass = new Sample();
    aClass.a = 10;
    aClass.b = 10; // Error: could not access to private in other class
    aClass.c = 10;
  }
}
