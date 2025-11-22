package test;
import java.util.Scanner;
import java.io.IOException;
import java.io.InputStreamReader;

public class AlphabetHistogramApp {
    private int[] counts = new int[26]; // A~Z 알파벳 빈도 저장 배열

    public AlphabetHistogramApp() {
        for (int i = 0; i < 26; i++)
            counts[i] = 0;
    }

    public void run() {
        System.out.println("문장을 입력하세요. (세미콜론(;)만 입력하면 종료)");
        String text = readString(); // 전체 입력 받기
        makeHistogram(text);        // 카운트 계산
        drawHistogram();            // 히스토그램 출력
    }

    private void makeHistogram(String text) {
        text = text.toUpperCase(); // 대문자로 통일
        for (int i = 0; i < text.length(); i++) {
            char ch = text.charAt(i);
            if (ch >= 'A' && ch <= 'Z') {
                counts[ch - 'A']++;
            }
        }
    }

    private void drawHistogram() {
        System.out.println("\n=== 알파벳 히스토그램 ===");
        for (int i = 0; i < 26; i++) {
            System.out.print((char) ('A' + i) + ": ");
            for (int j = 0; j < counts[i]; j++) {
                System.out.print("*");
            }
            System.out.println();
        }
    }

    private String readString() {
        StringBuffer sb = new StringBuffer();
        Scanner scanner = new Scanner(System.in);

        while (true) {
            String line = scanner.nextLine();
            if (line.equals(";"))  // 세미콜론만 입력되면 종료
                break;
            sb.append(line);
        }
        return sb.toString();
    }

    public static void main(String[] args) {
        AlphabetHistogramApp app = new AlphabetHistogramApp();
        app.run();
    }
}
