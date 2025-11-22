import java.util.InputMismatchException;
import java.util.Scanner;
import java.util.Vector;
class Word {
    private String english;
    private String korean;
    public Word(String en, String ko) {
        this.english = en;
        this.korean = ko;
    }
    public String getEnglish() {
        return english;
    }
    public String getKorean() {
        return korean;
    }
}
public class WordQuiz {
    private String name;
    private Vector<Word> v;
    public WordQuiz(String name) {
        this.name = name;
        v = new Vector<Word>();
        v.add(new Word("love", "사랑"));
        v.add(new Word("animal", "동물"));
        v.add(new Word("emotion", "감정"));
        v.add(new Word("human", "인간"));
        v.add(new Word("stock", "주식"));
        v.add(new Word("trade", "거래"));
        v.add(new Word("society", "사회"));
        v.add(new Word("baby", "아기"));
        v.add(new Word("honey", "꿀"));
        v.add(new Word("doll", "인형"));
        v.add(new Word("bear", "곰"));
        v.add(new Word("picture", "사진"));
        v.add(new Word("painting", "그림"));
        v.add(new Word("fault", "오류"));
        v.add(new Word("example", "보기"));
        v.add(new Word("eye", "눈"));
        v.add(new Word("statue", "조각상"));
    }
    private int makeExample(int[] ex, int answerIndex) {
        int answerPosition = (int)(Math.random() * 4);
        ex[answerPosition] = answerIndex;
        for (int i = 0; i < 4; i++) {
            if (i == answerPosition) continue;
            int randomIndex;
            do {
                randomIndex = (int)(Math.random() * v.size());
            } while (exists(ex, randomIndex));
            ex[i] = randomIndex;
        }
        return answerPosition;
    }
    private boolean exists(int[] n, int index) {
        for (int i = 0; i < n.length; i++) {
            if (n[i] == index) return true;
        }
        return false;
    }
    public void run() {
        System.out.println(name + "의 단어 테스트를 시작합니다. -1을 입력하면 종료합니다.");
        System.out.println("현재 " + v.size() + "개의 단어가 들어 있습니다.");
        Scanner scanner = new Scanner(System.in);
        while (true) {
            int answerIndex = (int)(Math.random() * v.size());
            Word answerWord = v.get(answerIndex);
            System.out.println(answerWord.getEnglish() + "?");
            int[] examples = new int[4];
            int correctPosition = makeExample(examples, answerIndex);
            for (int i = 0; i < 4; i++) {
                System.out.print("(" + (i + 1) + ")" + v.get(examples[i]).getKorean()+" ");
            }
            System.out.print(":>");
            int answer;
            try{
                answer = scanner.nextInt();
            }catch(InputMismatchException e){
                System.out.println("No. !!");
                continue;
            }
            if (answer == -1) {
                System.out.println("\""+name+"\"을(를) 종료합니다...");
                break;
            }
            if (answer - 1 == correctPosition) {
                System.out.println("Excellent !!");
            } else {
                System.out.println("No. !!");
            }
        }
        scanner.close();
    }
    public static void main(String[] args) {
        WordQuiz quiz = new WordQuiz("명품영어");
        quiz.run();
    }
}
