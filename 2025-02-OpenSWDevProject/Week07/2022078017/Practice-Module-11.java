package javaPractice05;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.Scanner;

public class AlphabetHistogramApp {
	private int count [] = new int[26];
	
	public AlphabetHistogramApp() {
		
	}
	
	private void makeHistogram(String text) {
		//;를 만날때까지 반복
		//텍스트를 읽어가면서 특정문자의 개수를 카운팅.
		String TrimText = text.trim();
		String arr[] = TrimText.split("");
		
		for (int i = 0; i < arr.length; i++) {
		    if (arr[i].equals("A") || arr[i].equals("a")) {
		        count[0]++;
		    } else if (arr[i].equals("B") || arr[i].equals("b")) {
		        count[1]++;
		    } else if (arr[i].equals("C") || arr[i].equals("c")) {
		        count[2]++;
		    } else if (arr[i].equals("D") || arr[i].equals("d")) {
		        count[3]++;
		    } else if (arr[i].equals("E") || arr[i].equals("e")) {
		        count[4]++;
		    } else if (arr[i].equals("F") || arr[i].equals("f")) {
		        count[5]++;
		    } else if (arr[i].equals("G") || arr[i].equals("g")) {
		        count[6]++;
		    } else if (arr[i].equals("H") || arr[i].equals("h")) {
		        count[7]++;
		    } else if (arr[i].equals("I") || arr[i].equals("i")) {
		        count[8]++;
		    } else if (arr[i].equals("J") || arr[i].equals("j")) {
		        count[9]++;
		    } else if (arr[i].equals("K") || arr[i].equals("k")) {
		        count[10]++;
		    } else if (arr[i].equals("L") || arr[i].equals("l")) {
		        count[11]++;
		    } else if (arr[i].equals("M") || arr[i].equals("m")) {
		        count[12]++;
		    } else if (arr[i].equals("N") || arr[i].equals("n")) {
		        count[13]++;
		    } else if (arr[i].equals("O") || arr[i].equals("o")) {
		        count[14]++;
		    } else if (arr[i].equals("P") || arr[i].equals("p")) {
		        count[15]++;
		    } else if (arr[i].equals("Q") || arr[i].equals("q")) {
		        count[16]++;
		    } else if (arr[i].equals("R") || arr[i].equals("r")) {
		        count[17]++;
		    } else if (arr[i].equals("S") || arr[i].equals("s")) {
		        count[18]++;
		    } else if (arr[i].equals("T") || arr[i].equals("t")) {
		        count[19]++;
		    } else if (arr[i].equals("U") || arr[i].equals("u")) {
		        count[20]++;
		    } else if (arr[i].equals("V") || arr[i].equals("v")) {
		        count[21]++;
		    } else if (arr[i].equals("W") || arr[i].equals("w")) {
		        count[22]++;
		    } else if (arr[i].equals("X") || arr[i].equals("x")) {
		        count[23]++;
		    } else if (arr[i].equals("Y") || arr[i].equals("y")) {
		        count[24]++;
		    } else if (arr[i].equals("Z") || arr[i].equals("z")) {
		        count[25]++;
		    }
		}
	
	}
	
	private void drawHistogram() {
		System.out.println("히스토그램을 그립니다.");
		for(int i =0; i<count.length; i++) {
			char letter = (char) ('A' + i);
			System.out.print(letter);
			for(int j =0; j<count[i]; j++) {
				System.out.print("- ");
			}
			System.out.println("");
		}
	}
	
	
	
	public void run() {
		System.out.println("영문 텍스트를 입력하고 세미콜론을 입력하세요.");
		String realText = readString();
		makeHistogram(realText);
		drawHistogram();
		
	}
	
	
	
	
	private String readString() {
		StringBuffer sb = new StringBuffer();
		Scanner scanner = new Scanner(System.in);
		while(true) {
			String line = scanner.nextLine();
			if(line.equals(";"))
				break;
			sb.append(line);
		}
		return sb.toString();
	}
	
	public static void main(String args[]) {
		AlphabetHistogramApp start = new AlphabetHistogramApp();
		start.run();
	}
}
