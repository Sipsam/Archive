package test;
public class GarbageEx{
	public static void main(String[] args) {
		String a = new String("Good");
		String b = new String("Bad");
		String c = new String("Normal");
		String d, e;
		a= null;
		d=c; // c에 들어있던 값이 가비지가 된다.
		c= null;
	}
}
