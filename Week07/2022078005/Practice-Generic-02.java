package Week07;

import java.util.Vector;

class Point {
	private int x, y;
	public Point(int x, int y) {
		this.x= x; this.y= y;
	}
	public String toString() {
		return "(" + x + "," + y + ")";
	}
}

public class PointVectorEx{
	public static void main(String[] args) {
		Vector<Point> v = new Vector<Point>();	// Point 객체를요소로만가지는벡터생성
		v.add(new Point(2, 3));		// 3 개의Point 객체삽입
		v.add(new Point(-5, 20));
		v.add(new Point(30, -8));
		v.remove(1); // 인덱스1의Point(-5, 20) 객체삭제
		for(int i=0; i<v.size(); i++) { // 벡터에 있는 Point 객체모두검색하여출력
			Point p = v.get(i); // 벡터에서 i번째 Point 객체얻어내기
			System.out.println(p); // p.toString()을 이용하여 객체 p 출력
		}
	}
}
