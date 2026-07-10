import java.util.Scanner;
import java.util.Random;

abstract class Player{
	protected String bet[] = {"묵", "찌", "빠"};
	protected String name;
	protected String lastBet = null;
	
	public Player(String name) {
		this.name = name;
	}
	
	public String getName() {
		return name;
	}
	
	public String getBet() {
		return lastBet;
	}
	
	abstract public String next();
}

class Human extends Player{
	private Scanner scanner;
	
	public Human(String name) {
		super(name);
		scanner = new Scanner(System.in);
	}
	@Override
	public String next() {
		while(true) {
			System.out.print(name + ">>");
			String input = scanner.next();
			if(input.equals("묵") || input.equals("찌") || input.equals("빠")) {
				lastBet = input;
				return lastBet;
			} else {
				System.out.println("잘못된 입력입니다. '묵', '찌', '빠' 중에서 다시 입력해주세요.");
			}
		}
	}
}

class Computer extends Player{
	private Random random;
	
	public Computer(String name) {
		super(name);
		random = new Random();
	}
	@Override
	public String next() {
		System.out.println(name + ">> 결정하였습니다.");
		int index = random.nextInt(3);
		lastBet = bet[index];
		return lastBet;
	}
}

class Game{
	private Player[] players = new Player[2];
	private Scanner scanner = new Scanner(System.in);
	
	private void createPlayers() {
		System.out.println("***** 묵찌빠 게임을 시작합니다. *****");
		System.out.print("선수 이름 입력 >>");
		String humanName = scanner.next();
		players[0] = new Human(humanName);
		
		System.out.print("컴퓨터이름 입력 >>");
		String computerName = scanner.next();
		players[1] = new Computer(computerName);
		System.out.println("2명의 선수를 생성 완료했습니다...");
	}
	
	public void run() {
		createPlayers();
		int ownerIndex = 0;
		
		while (true) {
			String humanBet = players[0].next();
			String computerBet = players[1].next();
			
			System.out.println(players[0].getName() + " : " + humanBet + ", " + players[1].getName() + " : " + computerBet);
			
			if(humanBet.equals(computerBet)) {
				System.out.println(players[ownerIndex].getName() + "이 이겼습니다.");
				break;
			} else if ((humanBet.equals("묵") && computerBet.equals("찌")) ||
					   (humanBet.equals("찌") && computerBet.equals("빠")) ||
					   (humanBet.equals("빠") && computerBet.equals("묵"))) {
				ownerIndex = 0;
				System.out.println("오너가 " + players[ownerIndex].getName() + "로 변경되었습니다.");
			} else {
				ownerIndex = 1;
				System.out.println("오너가 " + players[ownerIndex].getName() + "로 변경되었습니다.");
			}
		}
		System.out.println("게임을 종료합니다...");
		scanner.close();
	}
}

public class MGPapp{
	public static void main(String[] args) {
		new Game().run();
	}
}
