package javaPractice06;
import java.util.InputMismatchException;
import java.util.Scanner;
import java.util.Vector;

class Word {
	private String english;
	private String korean;
	
	public Word(String english, String korean) {
		this.english = english;
		this.korean = korean;
	}
	
	// 영어 단어를 반환
	public String getEnglish() {
		return english;
	}
	
	// 한글 뜻을 반환
	public String getKorean() {
		return korean;
	}
}


public class WordQuiz {
	
	private String name; // 퀴즈 프로그램의 이름
	private Vector<Word> v; // 단어 목록을 저장할 벡터
	private Scanner scanner; 
	
	public WordQuiz(String name) {
		this.name = name;
		scanner= new Scanner(System.in);
		
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
		v.add(new Word("dall", "인형"));
		v.add(new Word("bear", "곰"));
		v.add(new Word("picture", "사진"));
		v.add(new Word("painting", "그림"));
		v.add(new Word("fault", "오류"));
		v.add(new Word("example", "보기"));
		v.add(new Word("eye", "눈"));
		v.add(new Word("statue", "조각상"));
	}
	
	private boolean exists(int exist[], int count, int value) {
		for (int i = 0; i < count; i++) {
			if (exist[i] == value) {
				return true; // 이미 존재함
			}
		}
		return false; // 존재하지 않음
	}
	
	private int makeExample(int ex[], int answerIndex) {
		// 1. 정답의 위치를 4개 보기 중 랜덤하게 결정 (0, 1, 2, 3)
		int answerSpot = (int) (Math.random() * 4);
		ex[answerSpot] = answerIndex; // 정답 인덱스를 해당 위치에 저장
		
		int count = 1; // 현재 채워진 보기의 개수 (정답 포함)
		
		// 2. 나머지 3개의 오답 보기를 채움
		while (count < 4) {
			// v 벡터의 전체 단어 중 랜덤하게 인덱스 하나를 고름
			int wrongIndex = (int) (Math.random() * v.size());
			
			// 고른 인덱스가 정답 인덱스이거나, 이미 보기 배열에 존재한다면 다시 고름
			if (wrongIndex == answerIndex || exists(ex, count, wrongIndex)) {
				continue; 
			}
			
			// 정답 위치(answerSpot)가 아닌 다음 빈 자리를 찾아 오답 인덱스 저장
			for(int i=0; i<4; i++) {
				if(ex[i] == 0 && i != answerSpot) { // 아직 채워지지 않은 오답 자리
					ex[i] = wrongIndex;
					count++;
					break; // 이 오답은 채웠으므로 다음 오답 찾기
				}
			}
		}
		
		// 정답의 위치를 1~4 사이의 값으로 반환
		return answerSpot + 1;
	}
	
	public void run() {
		System.out.println("\"" + this.name + "\"의 단어 테스트를 시작합니다. -1을 입력하면 종료합니다.");
		System.out.println("현재 " + v.size() + "개의 단어가 들어 있습니다.");
		
		while (true) {
			// 1. 문제로 낼 단어 랜덤 선택 (v 벡터의 인덱스)
			int questionIndex = (int) (Math.random() * v.size());
			String questionWord = v.get(questionIndex).getEnglish();
			
			// 2. 4개의 보기 만들기
			int[] example = new int[4]; // 보기 단어 4개의 인덱스가 저장될 배열
			int correctAnswerNum = makeExample(example, questionIndex); // 1~4 중 정답 번호
			
			// 3. 문제 출력
			System.out.println("\n" + questionWord + "?");
			
			// 4. 보기 출력
			for (int i = 0; i < 4; i++) {
				System.out.print("(" + (i + 1) + ")" + v.get(example[i]).getKorean() + " ");
			}
			System.out.print(":> ");
			
			// 5. 사용자 정답 입력
			
				int userAnswer = scanner.nextInt();
				
				// 6. 종료 조건 확인
				if (userAnswer == -1) {
					System.out.println("\"" + this.name + "\"를 종료합니다...");
					scanner.close(); // 스캐너 종료
					break; // while 루프 종료
				}
				
				// 7. 정답 확인
				if (userAnswer == correctAnswerNum) {
					System.out.println("Excellent !!");
				} else {
					System.out.println("No. !!");
				}
			
		}
	}
	public static void main(String[] args) {
		
		WordQuiz quiz = new WordQuiz("명품영어"); 
		quiz.run();
	}
}
