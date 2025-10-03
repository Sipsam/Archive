package javapractice3;

import java.util.Scanner;

class Player {
    private String name; // 참가자 이름을 저장할 필드
    private Scanner scanner;

    public Player(String name) {
        this.name = name;
        scanner = new Scanner(System.in);
    }

    public String getName() {
        return name;
    }
    
    // Hint2: 사용자로부터 단어를 입력받는 메소드
    public String getWordFromUser() {
        System.out.print(name + ">>");
        return scanner.next(); // 키보드로부터 단어 입력받기
    }
}

public class WordGameApp {
    private Scanner scanner;
    private Player[] players; // 참가자들을 저장할 Player 객체 배열
    private String lastWord = "아버지"; // Hint1: 시작 단어

    public WordGameApp() {
        scanner = new Scanner(System.in);
    }
    
    // 게임 참가자들을 생성하는 메소드
    private void createPlayers() {
        System.out.print("게임에 참가하는 인원은 몇명입니까>>");
        int n = scanner.nextInt();
        players = new Player[n]; // 입력받은 인원수만큼 Player 배열 생성

        for (int i = 0; i < n; i++) {
            System.out.print("참가자의 이름을 입력하세요>>");
            String name = scanner.next();
            players[i] = new Player(name); // Player 객체를 생성하여 배열에 저장
        }
    }
    
    // Hint2: 끝말잇기 성공 여부를 판별하는 메소드
    public Boolean checkSuccess(String lastWord, String newWord) {
        // Hint3: 문자열의 마지막 문자와 첫 번째 문자를 알아내는 방법
        int lastIndex = lastWord.length() - 1;
        char lastChar = lastWord.charAt(lastIndex); // 이전 단어의 마지막 문자
        char firstChar = newWord.charAt(0);       // 새로 입력된 단어의 첫 문자

        if (lastChar == firstChar) {
            return true; // 끝말잇기 성공
        } else {
            return false; // 끝말잇기 실패
        }
    }

    // Hint1: 게임을 전체적으로 진행하는 run 메소드
    public void run() {
        System.out.println("끝말잇기 게임을 시작합니다...");
        createPlayers(); // 참가자 생성
        System.out.println("시작하는 단어는 " + lastWord + "입니다");
        
        int currentPlayerIndex = 0; // 현재 게임 차례인 참가자의 인덱스

        while (true) {
            Player currentPlayer = players[currentPlayerIndex];
            String newWord = currentPlayer.getWordFromUser(); // 현재 참가자로부터 단어 입력받기

            if (!checkSuccess(lastWord, newWord)) { // 끝말잇기 규칙을 어겼다면
                System.out.print(currentPlayer.getName() + "이 졌습니다.");
                break; // 게임 종료
            }

            lastWord = newWord; // 다음 차례를 위해 현재 단어를 이전 단어로 설정
            currentPlayerIndex++; // 다음 참가자로 순서 넘기기
            if (currentPlayerIndex == players.length) { // 모든 참가자가 한 번씩 다 했다면
                currentPlayerIndex = 0; // 다시 첫 번째 참가자부터 시작
            }
        }
    }
    
    // Hint1: main 메소드
    public static void main(String[] args) {
        // WordGameApp 객체를 생성하고 run() 메소드를 호출하여 게임을 시작
        WordGameApp game = new WordGameApp();
        game.run();
    }
}