import java.util.Scanner;

public class WordGameApp{
	private Player[] players;
	private Scanner scanner;
	
	public WordGameApp() {		// 생성자 메소드
		scanner = new Scanner(System.in);
	}
	
	private void createPlayers() {		// 게임 참가자 수를 입력받고 Player[]을 생성하는 메소
		System.out.print("게임에 참가하는 인원은 몇명입니까 >> ");
		int numPlayers = scanner.nextInt();
		players = new Player[numPlayers];
		
		for(int i=0; i<numPlayers; i++) {
			System.out.print("참가자의 이름을 입력하세요 >> ");
			String name = scanner.next();
			players[i] = new Player(name, scanner);
		}
	}
	
	public Boolean checkSuccess(String lastWord, String newWord) {	// lastWord와 newWord를 비교하는 메소
		int lastIndex = lastWord.length() - 1;
		char lastChar = lastWord.charAt(lastIndex);
		char firstChar = newWord.charAt(0);
		
		return lastChar == firstChar;
	}
	
	public void run() {		// 게임을 진행하는 메소드
		System.out.println("끝말잇기 게임을 시작합니다...");
		createPlayers();
		String lastWord = "아버지";
		System.out.println("시작하는 단어는 아버지입니다");
		
		int turn = 0;
		while(true) {			
			Player currentPlayer = players[turn % players.length];
			
			String newWord = currentPlayer.getWordFromUser();
			
			if(!checkSuccess(lastWord, newWord)) {
				System.out.println(currentPlayer.getName() + "이 졌습니다.");
				break;
			}
			lastWord = newWord;
			turn++;
		}
	}
	public static void main(String[] args) {	// 메인 메소드
		WordGameApp game = new WordGameApp();
		game.run();
	}
}

class Player {
	private String name;
	private Scanner scanner;
	
	public Player(String name, Scanner scanner) {
		this.name = name;
		this.scanner = scanner;
	}
	
	public String getName() {
		return name;
	}
	
	public String getWordFromUser() {	// 사용자로부터 단어를 입력받는 메소드
		System.out.print(name + ">>");
		return this.scanner.next();
	}
}
