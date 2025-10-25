package Week07;

import java.util.*;

public class HashMapScoreEx{
	public static void main(String[] args) {
		// 사용자이름과점수를기록하는HashMap 컬렉션생성
		HashMap<String, Integer> javaScore= new HashMap<String, Integer>();
		
		// 5 개의점수저장 scoreMap.put("김성동", 97);
		// scoreMap -> javaScore 로 변경해서 작
		javaScore.put("황기태", 88);
		javaScore.put("김남윤", 98);
		javaScore.put("이재문", 70);
		javaScore.put("한원선", 99);
		
		System.out.println("HashMap의요소개수:" + javaScore.size());
		
		// 모든사람의점수출력.
		// javaScore에들어있는모든(key, value) 쌍출력
		// key 문자열을가진집합Set 컬렉션리턴
		Set<String> keys = javaScore.keySet();
		
		// key 문자열을순서대로접근할수 있는Iterator 리턴
		Iterator<String> it = keys.iterator();
		while(it.hasNext()) {
			String name = it.next();
			int score = javaScore.get(name);
			System.out.println(name + " : " + score);
		}
	}
}
