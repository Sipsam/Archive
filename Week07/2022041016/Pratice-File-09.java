import java.util.Vector;
import java.util.Scanner;
import java.io.File;
import java.io.FileNotFoundException;

class Words {
    private Vector<String> wordVector;
    private boolean loaded;

    public Words(String fileName) {
        wordVector = new Vector<String>();
        loaded = false;
        try {
            Scanner scanner = new Scanner(new File(fileName));
            while (scanner.hasNext()) {
                String word = scanner.nextLine().trim();
                if (word.length() > 0) {
                    wordVector.add(word);
                }
            }
            scanner.close();
            loaded = true;
        } catch (FileNotFoundException e) {
            System.out.println("파일을 찾을 수 없습니다: " + fileName);
            System.out.println("프로그램을 종료합니다.");
        }
    }

    public boolean isLoaded() {
        return loaded && wordVector.size() > 0;
    }

    public String getRandomWord() {
        int randomIndex = (int)(Math.random() * wordVector.size());
        return wordVector.get(randomIndex);
    }
}

public class HangManGameApp {
    private String newWord;
    private String hiddenWord;
    private Words words;
    private Scanner scanner;

    public HangManGameApp() {
        words = new Words("words.txt");
        scanner = new Scanner(System.in);
    }

    public void run() {
        if (!words.isLoaded()) {
            return;
        }

        System.out.println("지금부터 행맨 게임을 시작합니다.");

        while (true) {
            newWord = words.getRandomWord();
            makeHidden();
            go();

            System.out.print("Next(y/n)?");
            String answer = scanner.next();
            if (answer.equalsIgnoreCase("n")) {
                break;
            }
        }
        System.out.println("게임을 종료합니다...");
        scanner.close();
    }

    private void makeHidden() {
        StringBuffer sb = new StringBuffer(newWord);
        int count = 0;

        while (count < 2) {
            int randomIndex = (int)(Math.random() * newWord.length());
            if (sb.charAt(randomIndex) != '-') {
                sb.setCharAt(randomIndex, '-');
                count++;
            }
        }
        hiddenWord = sb.toString();
    }

    private void go() {
        int failCount = 0;

        while (failCount < 5) {
            System.out.println(hiddenWord);
            System.out.print(">>");
            String input = scanner.next();

            if (input.length() != 1) {
                System.out.println("한 글자만 입력하세요.");
                continue;
            }

            char key = input.charAt(0);

            if (complete(key)) {
                if (hiddenWord.equals(newWord)) {
                    System.out.println(hiddenWord);
                    return;
                }
            } else {
                failCount++;
            }
        }

        System.out.println("5번 실패 하였습니다.");
        System.out.println(newWord);
    }

    private boolean complete(char key) {
        boolean found = false;
        StringBuffer sb = new StringBuffer(hiddenWord);

        for (int i = 0; i < newWord.length(); i++) {
            if (newWord.charAt(i) == key && hiddenWord.charAt(i) == '-') {
                sb.setCharAt(i, key);
                found = true;
            }
        }

        hiddenWord = sb.toString();
        return found;
    }

    public static void main(String[] args) {
        HangManGameApp game = new HangManGameApp();
        game.run();
    }
}
/** 입출력예시
지금부터 행맨 게임을 시작합니다.
-u-
>>s
-us
>>b
-us
>>g
-us
>>p
-us
>>S
Sus
Next(y/n)?y
-eon-
>>a
-eona
>>p
-eona
>>L
Leona
Next(y/n)?y
w-s-ern
>>e
wes-ern
>>h
wes-ern
>>k
wes-ern
>>p
wes-ern
>>d
wes-ern
>>e
5번 실패 하였습니다.
western
Next(y/n)?n
게임을 종료합니다...
  */
