import java.util.Scanner;

public class Practice14 {	// RockCissorsPaper

	public static void main(String[] args) {
		Scanner scanner = new Scanner(System.in);
		System.out.println("가위바위보 게임입니다. 가위, 바위, 보 중에서 입력하세요.");
		System.out.print("철수 >> ");
		String player1 = scanner.next();
		System.out.print("영희 >> ");
		String player2 = scanner.next();
		
		switch (player1) {
			case "가위":
				if (player2.equals("가위"))
					System.out.print("비겼습니다.");
				else if (player2.equals("바위"))
					System.out.print("영희가 이겼습니다.");
				else if (player2.equals("보"))
					System.out.print("철수가 이겼습니다.");
				break;
			case "바위":
				if (player2.equals("가위"))
					System.out.print("철수가 이겼습니다.");
				else if (player2.equals("바위"))
					System.out.print("비겼습니다.");
				else if (player2.equals("보"))
					System.out.print("영희가 이겼습니다.");
				break;
			case "보":
				if (player2.equals("가위"))
					System.out.print("영희가 이겼습니다.");
				else if (player2.equals("바위"))
					System.out.print("철수가 이겼습니다.");
				else if (player2.equals("보"))
					System.out.print("비겼습니다.");
				break;
			default:
				System.out.println("잘못된 입력입니다.");
		}
		
		scanner.close();
	}

}

// String 문자열 비교는 player2 == "XX"로 하는 것이 아니고,
// player2.equals("XX") 같은 방식으로 해야함.
