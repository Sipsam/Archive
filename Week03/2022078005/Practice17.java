package Week03;
import java.util.Scanner;
import java.util.Random;

public class Practice17 {	// RandomCardGame(Class)

	public static void main(String[] args) {
		Scanner scanner = new Scanner(System.in);
		Random rand = new Random();
		
		int random = rand.nextInt(100);
		int start = 0;
		int finish = 99;
		int count = 1;
		System.out.println("수를 결정하였습니다. 맞추어 보세요.");

		while(true) {
			System.out.println(start+"~"+finish);
			System.out.print(count+">>");
			count++;
			int number = scanner.nextInt();
			
			if(number == random) {
				random = rand.nextInt(100);
				start = 0;
				finish = 99;
				count = 1;
				
				System.out.println("맞았습니다.");
				System.out.print("다시하시겠습니까(y/n) >> ");
				String text = scanner.next();
				System.out.println("");
				
				if(text.equals("n")) {
					System.out.println("게임이 종료됩니다...");
					break;
				}
				else
					System.out.println("수를 결정하였습니다. 맞추어 보세요.");
			}
			else if(number > random) {
				System.out.println("더 낮게");
				finish = number;
			}
			else {
				System.out.println("더 높게");
				start = number;
			}
		}
	}

}
