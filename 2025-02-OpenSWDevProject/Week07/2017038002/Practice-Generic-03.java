package test;
import java.util.*;

public class ArrayListEx{
	public static void main(String[] args) {
		ArrayList<String> a = new ArrayList<String>(); 
		Scanner scanner= new Scanner(System.in); 
		for(int i=0; i<4; i++) {
			System.out.print("이름을입력하세요>>");
			String s = scanner.next(); // 키보드로부터이름입력
			a.add(s); // ArrayList컬렉션에삽입
		}
		
		for(int i=0; i<a.size(); i++) {
				// ArrayList의i번째문자열얻어오기
			String name = a.get(i); 
			System.out.print(name + " ");
		}
		int longestIndex = 0;
		for(int i=1;i<a.size();i++) {
			if(a.get(longestIndex).length()<a.get(i).length())
				longestIndex = i;
		}
		System.out.println("\n가장 긴 이름은:"+a.get(longestIndex));
	}
}
