package test;
import java.util.Scanner;

public class WordGameApp {
    private Player[] players;
    private Scanner scanner;
    private String startWord = "아버지";

    public WordGameApp() {
        scanner = new Scanner(System.in);
    }

    private void createPlayers() {
        System.out.print("참가자 수를 입력하세요: ");
        int n = scanner.nextInt();
        scanner.nextLine(); // 버퍼 비우기
        players = new Player[n];

        for (int i = 0; i < n; i++) {
            System.out.print("참가자 이름을 입력하세요: ");
            String name = scanner.nextLine();
            players[i] = new Player(name);
        }
    }

    public boolean checkSuccess(String lastWord, String newWord) {
        char lastChar = lastWord.charAt(lastWord.length() - 1);
        char firstChar = newWord.charAt(0);
        return lastChar == firstChar;
    }

    public void run() {
        createPlayers();
        String currentWord = startWord;
        System.out.println("시작 단어는 \"" + currentWord + "\" 입니다.");

        int turn = 0;
        while (true) {
            Player currentPlayer = players[turn % players.length];
            System.out.print(currentPlayer.getName() + " >> ");
            String newWord = currentPlayer.getWordFromUser();

            if (!checkSuccess(currentWord, newWord)) {
                System.out.println(currentPlayer.getName() + "이(가) 졌습니다.");
                break;
            }

            currentWord = newWord;
            turn++;
        }
    }

    public static void main(String[] args) {
        WordGameApp game = new WordGameApp();
        game.run();
    }
}

class Player {
    private String name;
    private Scanner scanner;

    public Player(String name) {
        this.name = name;
        scanner = new Scanner(System.in);
    }

    public String getName() {
        return name;
    }

    public String getWordFromUser() {
        return scanner.nextLine().trim();
    }
}
