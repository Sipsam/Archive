package Week07;

import java.io.FileReader;
import java.io.FileNotFoundException;
import java.util.Scanner;
import java.util.Vector;

public class HangManGameApp {
    private Words words;
    private String newWord; // 선택된 단어
    private StringBuffer hiddenWord; // 숨겨진 글자가 포함된 단어
    private int failedCount;
    private Scanner scanner;

    public HangManGameApp() {
        words = new Words("words.txt");
        scanner = new Scanner(System.in);
    }

    // 게임을 시작하는 메소드
    public void run() {
        System.out.println("지금부터 행맨 게임을 시작합니다.");
        
        while (true) {
            newWord = words.getRandomWord();
            if (newWord == null) {
                System.out.println("단어 파일(words.txt)을 읽을 수 없습니다. 게임을 종료합니다.");
                break;
            }
            
            makeHidden(); // 단어의 2글자를 숨김
            go(); // 행맨 게임 진행

            System.out.print("Next(y/n)?");
            String answer = scanner.next();
            if (answer.equalsIgnoreCase("n")) {
                break;
            }
        }
        System.out.println("행맨 게임을 종료합니다.");
        scanner.close();
    }

    // 선택된 단어 newWord에 2개의 글자를 숨긴 단어 hiddenWord를 만든다.
    private void makeHidden() {
        hiddenWord = new StringBuffer(newWord);
        int length = newWord.length();

        // 2개의 서로 다른 랜덤 인덱스 선택 
        int index1 = (int) (Math.random() * length);
        int index2;
        do {
            index2 = (int) (Math.random() * length);
        } while (index1 == index2);

        // 해당 인덱스의 글자를 '-'로 변경
        hiddenWord.setCharAt(index1, '-');
        hiddenWord.setCharAt(index2, '-');
    }

    // 사용자 키를 입력받으면서 행맨 게임을 진행한다. 5번 틀리면 종료.
    private void go() {
        failedCount = 0;

        while (true) {
            System.out.println(hiddenWord);
            System.out.print(">>");
            String guess = scanner.next();
            
            if (guess.length() < 1) { // 빈 입력 방지
                continue;
            }
            char key = guess.charAt(0);

            if (!complete(key)) {
                failedCount++;
            }

            // 단어를 모두 맞춘 경우
            if (hiddenWord.toString().equals(newWord)) {
                System.out.println(newWord);
                break;
            }

            // 5번 틀린 경우 
            if (failedCount == 5) {
                System.out.println("5번 실패 하였습니다.");
                System.out.println(newWord); 
                break;
            }
        }
    }

    // 사용자가 입력한 문자 key가 숨긴 글자와 일치하는지 검사하고 일치하면 true를 리턴
    // hiddenWord의 '-'문자를 key 문자로 변경한다.
    private boolean complete(char key) {
        boolean found = false;
        for (int i = 0; i < newWord.length(); i++) {
            if (newWord.charAt(i) == key && hiddenWord.charAt(i) == '-') {
                hiddenWord.setCharAt(i, key);
                found = true;
            }
        }
        return found;
    }

    public static void main(String[] args) {
        HangManGameApp game = new HangManGameApp();
        game.run();
    }
}

//words.txt 파일을 읽고 벡터에 저장하고 벡터로부터 랜덤하게 단어를 추출하는 클래스
class Words {
 private Vector<String> wordVector;

 public Words(String fileName) {
     wordVector = new Vector<String>();
     try {
         Scanner scanner = new Scanner(new FileReader(fileName));
         while (scanner.hasNext()) { // 파일을 끝까지 반복하여 읽음
             String word = scanner.nextLine(); // 한라인 단위로 읽음
             wordVector.add(word); // 단어를 벡터에 저장
         }
         scanner.close();
         // System.out.println("Word 'words.txt' read successfully. Total " + wordVector.size() + " words.");
     } catch (FileNotFoundException e) {
         System.out.println(fileName + " 파일을 찾을 수 없습니다.");
         // e.printStackTrace();
     }
 }

 // 벡터로부터 랜덤하게 단어 하나를 추출
 public String getRandomWord() {
     if (wordVector.isEmpty()) {
         return null;
     }
     int index = (int) (Math.random() * wordVector.size());
     return wordVector.get(index);
 }
}

/*
지금부터 행맨 게임을 시작합니다.
-x-ision
>>e
ex-ision
>>e
ex-ision
>>c
excision
Next(y/n)?y
sc-oo-work
>>h
schoo-work
>>l
schoolwork
Next(y/n)?y
Ba--ow
>>r
Bar-ow
>>r
Bar-ow
>>e
Bar-ow
>>a
Bar-ow
>>n
Bar-ow
>>m
5번 실패 하였습니다.
Barlow
Next(y/n)?n
행맨 게임을 종료합니다.
*/
