package Week05;
public class GarbageEx {
	public static void main(String[] args) {
		String a = new String("Good");
		String b = new String("Bad");
		String c = new String("Soso");
		String d,e;
		a = null;	// a가 참조하고 있던 데이터 "Good"이 가비지가 된다.
		d = c;
		c = null;
	}

}
