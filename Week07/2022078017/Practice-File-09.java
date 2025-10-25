package javaPractice07; 

import java.util.*;
import java.io.*;


public class HangManGameApp {
	private Words words; 
	private Scanner scanner; 
	private String newWord; 
	private StringBuffer hiddenWord;  
	

	public HangManGameApp() {
		words = new Words("words.txt"); 
		scanner = new Scanner(System.in); 
	}

	
	public void run() {
		System.out.println("지금부터 행맨 게임을 시작합니다.");
		
		while(true) {
			newWord = words.getRandomWord(); 
			
			makeHidden(); 
			go(); 
			
			System.out.print("Next(y/n)? ");
			String answer = scanner.next();
			if(answer.equalsIgnoreCase("n")) {
				break; 
			}
		}
		System.out.println("게임을 종료합니다.");
		scanner.close();
	}

	
	private void makeHidden() {
		hiddenWord = new StringBuffer(newWord);
		
		int index1 = (int) (Math.random() * newWord.length());
		int index2;
		do {
			index2 = (int) (Math.random() * newWord.length());
		} while (index1 == index2);
		
		hiddenWord.setCharAt(index1, '-');
		hiddenWord.setCharAt(index2, '-');
	}

	private void go() {
		int failCount = 0;
		System.out.println(hiddenWord);
		
		while(true) {
			System.out.print(">>");
			String keyStr = scanner.next(); 
			char key = keyStr.charAt(0); 
			
			
			if (!complete(key)) { 
				failCount++;
				System.out.println(failCount + "번 실패. (5번 실패 시 종료)");
			}
			
			System.out.println(hiddenWord); 
			
			
			if(hiddenWord.toString().indexOf('-') == -1) {
				System.out.println("성공! 정답은 \"" + newWord + "\"입니다.");
				break; 
			}
			
		
			if(failCount == 5) {
				System.out.println("5번 실패 하였습니다. 정답은 \"" + newWord + "\"입니다.");
				break; 
			}
		}
	}

	private boolean complete(char key) {
		boolean found = false;
		
		for(int i=0; i<newWord.length(); i++) {
			
			if(newWord.charAt(i) == key && hiddenWord.charAt(i) == '-') {
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

class Words {
	private Vector<String> wordVector = new Vector<String>();

	public Words(String fileName) {
		try {
			Scanner fileScanner = new Scanner(new FileReader(fileName));
			while(fileScanner.hasNext()) { 
				String word = fileScanner.nextLine(); 
				wordVector.add(word); 
			}
			fileScanner.close();
		} catch (FileNotFoundException e) {
			
			System.out.println("오류: " + fileName + " 파일을 찾을 수 없습니다.");
			
		}
	}
	
	public String getRandomWord() {
		if(wordVector.size() == 0) {
			return null; 
		}
		int index = (int)(Math.random() * wordVector.size());
		return wordVector.get(index);
	}
}