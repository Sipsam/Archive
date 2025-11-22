package Week07;

import java.util.InputMismatchException;
import java.util.Scanner;
import java.util.Vector;
import java.util.Collections;
import java.util.ArrayList;

//영어 단어와 그에 해당하는 한글 뜻을 저장하는 클래스
class Word {
	private String english;
	private String korean;

	public Word(String english, String korean) {
		this.english = english;
		this.korean = korean;
	}

 public String getEnglish() {
     return english;
 }

 public String getKorean() {
     return korean;
 }
}

// 퀴즈의 이름과 단어 목록(Vector)을 관리하며, 퀴즈를 실행
public class WordQuiz {
    private String name; // 퀴즈 프로그램의 이름
    private Vector<Word> v; // 단어 목록 벡터
    private Scanner scanner;

    // 생성자: 프로그램 이름을 받고, 단어 벡터를 초기화
    public WordQuiz(String name) {
        this.name = name;
        v = new Vector<Word>();
        // 제공된 'WordQuiz class.txt' 파일 [source 1-4] 및 PDF [source 108-109] 기반으로 단어 추가
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

        scanner = new Scanner(System.in);
    }

    // 배열에 특정 index가 존재하는지 확인하는 메소드
    private boolean exists(int n, int[] arr) {
        for (int i = 0; i < arr.length; i++) {
            if (arr[i] == n) {
                return true;
            }
        }
        return false;
    }

    // 4개의 보기 인덱스를 생성하고, 그 중 한 위치에 정답 인덱스를 심는 메소드
    private int[] makeExample(int excludeIndex) {
        int[] options = new int[4];
        
        for (int i = 0; i < 4; i++) {
            int randIndex;
            do {
                randIndex = (int) (Math.random() * v.size());
            } while (randIndex == excludeIndex || exists(randIndex, options)); // 중복 및 정답 제외
            options[i] = randIndex;
        }
        return options;
    }

    // 퀴즈 실행 메소드, 사용자와 상호작용하며 문제를 출제하고 정답을 확인.
    public void run() {
        System.out.println("\"" + name + "\"의 단어 테스트를 시작합니다. -1을 입력하면 종료합니다.");
        System.out.println("현재 " + v.size() + "개의 단어가 들어 있습니다.");

        while (true) {
            try {
                // 문제(정답) 단어 랜덤 선택
                int questionIndex = (int) (Math.random() * v.size());
                Word questionWord = v.get(questionIndex);

                // 4개의 보기 생성 (이때는 모두 오답)
                int[] optionIndices = makeExample(questionIndex);

                // 4개의 보기 중 랜덤한 위치에 정답 삽입
                int answerPos = (int) (Math.random() * 4); // 0~3
                optionIndices[answerPos] = questionIndex; // 정답 인덱스로 교체

                // 문제 출력
                System.out.println(questionWord.getEnglish() + "?");

                // 보기 출력
                for (int i = 0; i < 4; i++) {
                    System.out.print("(" + (i + 1) + ")" + v.get(optionIndices[i]).getKorean() + " ");
                }
                System.out.print(">");

                // 사용자 입력
                int choice = scanner.nextInt();

                if (choice == -1) {
                    System.out.println("\"" + name + "\"를 종료합니다...");
                    break;
                }

                // 정답 확인
                if (choice == (answerPos + 1)) {
                    System.out.println("Excellent !!");
                } else {
                    System.out.println("No. !!");
                }
            } catch (InputMismatchException e) {
                System.out.println("숫자를 입력하세요!");
                scanner.next(); // 잘못된 입력(문자열 등)을 비움
            }
        }
    }

    // 프로그램의 시작점. WordQuiz 객체 생성 후 실행
    public static void main(String[] args) {
        WordQuiz quiz = new WordQuiz("명품영어");
        quiz.run();
    }
}

/*
"명품영어"의 단어 테스트를 시작합니다. -1을 입력하면 종료합니다.
현재 17개의 단어가 들어 있습니다.
trade?
(1)곰 (2)거래 (3)인형 (4)눈 >2
Excellent !!
eye?
(1)사회 (2)눈 (3)오류 (4)꿀 >2
Excellent !!
picture?
(1)곰 (2)거래 (3)인형 (4)사진 >4
Excellent !!
statue?
(1)조각상 (2)오류 (3)곰 (4)감정 >1
Excellent !!
honey?
(1)인형 (2)꿀 (3)동물 (4)곰 >2
Excellent !!
stock?
(1)주식 (2)동물 (3)아기 (4)감정 >1
Excellent !!
stock?
(1)오류 (2)인간 (3)주식 (4)아기 >3
Excellent !!
doll?
(1)사진 (2)인간 (3)인형 (4)감정 >3
Excellent !!
animal?
(1)꿀 (2)주식 (3)그림 (4)동물 >-1
"명품영어"를 종료합니다...
*/
