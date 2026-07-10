package Week05;

class Sample{
	public int a;
	private int b;	// private 선언
	int c;
}

public class AccessEx {
	public static void main(String[] args) {
		Sample aClass = new Sample();
		aClass.a = 10;
		aClass.b = 10;	// Sample 클래스 안에서 b를 private로 지정했기 때문에 컴파일 오류가 발생한다.
		aClass.c = 10;
	}

}
