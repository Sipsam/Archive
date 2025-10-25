package test;
import java.util.*;
import java.io.*;

class Words {
    private Vector<String> wordVector = new Vector<String>();
    private Random random = new Random();

    public Words(String fileName) {
        try {
            Scanner scanner = new Scanner(new FileReader(fileName));
            while (scanner.hasNext()) {
                String word = scanner.nextLine().trim();
                if (!word.isEmpty()) {
                    wordVector.add(word);
                }
            }
            scanner.close();
        } catch (IOException e) {
            System.out.println("파일을 읽을 수 없습니다: " + fileName);
            System.exit(0);
        }
    }

    public String getRandomWord() {
        if (wordVector.isEmpty()) return null;
        int index = random.nextInt(wordVector.size());
        return wordVector.get(index);
    }
}

public class HangManGameApp {
    private Words words;
    private String newWord;
    private char[] hiddenWord;
    private Scanner scanner = new Scanner(System.in);

    public HangManGameApp(String fileName) {
        words = new Words(fileName);
    }

    public void run() {
        System.out.println("지금부터 행맨 게임을 시작합니다.");

        while (true) {
            newWord = words.getRandomWord();
            if (newWord == null) {
                System.out.println("단어 목록이 비어 있습니다.");
                break;
            }

            makeHidden();
            go();

            System.out.print("다시 하시겠습니까? (y/n): ");
            String ans = scanner.next();
            if (ans.equalsIgnoreCase("n")) {
                System.out.println("게임을 종료합니다.");
                break;
            }
        }
    }

    private void makeHidden() {
        hiddenWord = newWord.toCharArray();
        Random r = new Random();
        int len = newWord.length();

        if (len <= 2) {
            int index = r.nextInt(len);
            hiddenWord[index] = '-';
            return;
        }

        int first = r.nextInt(len);
        int second;
        do {
            second = r.nextInt(len);
        } while (second == first);

        hiddenWord[first] = '-';
        hiddenWord[second] = '-';
    }

    private void go() {
        int wrong = 0;

        while (true) {
            System.out.println("\n" + String.valueOf(hiddenWord));
            System.out.print(">>");
            char key = scanner.next().charAt(0);

            if (complete(key)) {
                System.out.println("정답입니다!");
            } else {
                wrong++;
                System.out.println("오답입니다! (" + wrong + "번째 실패)");
            }

            if (String.valueOf(hiddenWord).equals(newWord)) {
                System.out.println("단어 완성! 정답은 '" + newWord + "' 입니다.");
                break;
            }

            if (wrong >= 5) {
                System.out.println("5번 실패 히였습니다.\n" + newWord);
                break;
            }
        }
    }

    private boolean complete(char key) {
        boolean found = false;
        for (int i = 0; i < newWord.length(); i++) {
            if (newWord.charAt(i) == key && hiddenWord[i] == '-') {
                hiddenWord[i] = key;
                found = true;
            }
        }
        return found;
    }

    public static void main(String[] args) {
        HangManGameApp game = new HangManGameApp("words.txt");
        game.run();
    }
}
