package javapratice2;
import java.util.Random;
import java.util.Scanner;

public class Practice17 {
	public static void main(String [] args) {
		Scanner scanner = new Scanner(System.in);
		
		int low;
		int high;
		while(true) {
			low=0;
			high=99;
			int RanNum = (int)(Math.random()*100);
			System.out.println("수를 결정하였습니다. 맞추어 보세요.");
			for(int i = 0; ; i++) {
				System.out.println(low+"-"+high);
				System.out.print(i+1+">>");
				int ChoiceNum = scanner.nextInt();
				if(ChoiceNum == RanNum) {
					System.out.println("맞았습니다.");
					break;
				}
				else if(ChoiceNum > RanNum) {
					high = ChoiceNum;
					System.out.println("더 낮게");
				}
				else if(ChoiceNum < RanNum) {
					low = ChoiceNum;
					System.out.println("더 높게");
				}
				
			}
			
			System.out.print("다시 하시겠습니까(y/n)>>");
			String text = scanner.next();
			if(text.equals("n"))
				break;
		}
		scanner.close();
	}
}
