package javaPractice05;

public class StringEx {
	public static void main(String[] args) {
		String a = new String("C#");
		String b = new String("C++");
		
		System.out.println(a+"의 길이는 "+a.length());
		System.out.println(a.contains("#"));
		a=a.concat(b);
		System.out.println(a);
		a=a.trim();
		System.out.println(a);
		a=a.replace("C#", "Java");
		System.out.println(a);
		String s[] = a.split(",");
		for(int i = 0; i<s.length; i++) {
			System.out.println("분리된 문자열"+i+":"+s[i]);
			
		}
		a=a.substring(5);
		System.out.println(a);
		char c = a.charAt(1);//인덱스 초과로 불가능한 명령. 앞선 코드에서substring(5)로 앞부분 잘라내서 ++두개만 남음.그래서 1로 변경했습니다.
		System.out.println(c);
		
		
	}
}
