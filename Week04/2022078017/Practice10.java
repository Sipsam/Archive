package javapractice3;

class Sample{
	public int a;
	private int b;
	int c;
}




public class AccessEx {
	public static void main(String []args) {
		Sample aClass = new Sample();
		aClass.a = 10;//컴파일 오류가 나는 이유는 private접근 지정자로 지정된 멤버 변수에 다른 클래스에서 접근하려고 했기 때문이다.
		aClass.b = 10;
		aClass.c = 10;
	}
}