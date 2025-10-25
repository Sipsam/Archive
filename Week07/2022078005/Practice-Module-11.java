package Week07;

import java.util.Scanner;

public class AlphabetHistogramApp {

    private int[] alphaCounts = new int[26]; // 알파벳 개수를 저장할 배열
    private Scanner scanner;

    public AlphabetHistogramApp() {
        scanner = new Scanner(System.in);
    }

    // 키보드로부터 텍스트를 입력받아 하나의 문자열로 리턴
    private String readString() {
        StringBuffer sb = new StringBuffer(); // 키 입력을 받을 스트링버퍼 생성
        System.out.println("영문 텍스트를 입력하고 세미콜론(;)을 입력하세요.");

        while (true) {
            String line = scanner.nextLine(); // 텍스트 한 라인을 읽는다.
            if (line.equals(";")) { // ; 만 있는 라인이면
                break; // 입력 끝
            }
            sb.append(line); // 읽은 라인 문자열을 스트링버퍼에 추가한다.
        }
        return sb.toString(); // 스트링버퍼의 문자열을 스트링으로 리턴
    }

    // 입력받은 문자들로부터 히스토그램의 데이터를 생성
    private void makeHistogram(String text) {
        // 모든 문자를 소문자로 변환
        text = text.toLowerCase();

        for (int i = 0; i < text.length(); i++) {
            char c = text.charAt(i);
            if (Character.isLetter(c)) { // 알파벳인 경우에만
                int index = c - 'a'; // 'a'로부터의 오프셋 계산
                alphaCounts[index]++;
            }
        }
    }

    // 히스토그램을 그림
    private void drawHistogram() {
        System.out.println("\n히스토그램을 그립니다.");
        for (int i = 0; i < alphaCounts.length; i++) {
            char alphabet = (char) ('A' + i); // 대문자로 출력
            System.out.print(alphabet);
            
            for (int j = 0; j < alphaCounts[i]; j++) {
                System.out.print("-"); // 카운트만큼 '-' 출력
            }
            System.out.println();
        }
    }

    // 프로그램 실행
    public void run() {
        // 키보드로부터 알파벳 문자를 읽고
        String text = readString();
        
        // 입력받은 문자들로부터 히스토그램의 데이터를 생성
        makeHistogram(text);
        
        // 히스토그램을 그림
        drawHistogram();
        
        scanner.close();
    }

    // main 메소드
    public static void main(String[] args) {
        AlphabetHistogramApp app = new AlphabetHistogramApp();
        app.run();
    }
}

/*
영문 텍스트를 입력하고 세미콜론(;)을 입력하세요.
Alice was beginning to get very tired of sitting by her sister on the bank, and of having nothing to do: once or twice she had peeped into the book her sister was reading, but it had no pictures or conversations in it, and what is the use of a book, thought Alice without pictures or conversations?

So she was considering in her own mind (as well as she could, for the hot day made her feel very sleepy and stupid), whether the pleasure of making a daisy-chain would be worth the trouble of getting up and picking the daisies, when suddenly a White Rabbit with pink eyes ran close by her.

There was nothing so very remarkable in that; nor did Alice think it so very much out of the way to hear the Rabbit say to itself, Oh dear! Oh dear! I shall be late! (when she thought it over afterwards, it occurred to her that she ought to have wondered at this, but at the time it all seemed quite natural); but when the Rabbit actually took a watch out of its waistcoat-pocket, and looked at it, and then hurried on, Alice started to her feet, for it flashed across her mind that she had never before seen a rabbit with either a waistcoat-pocket, or a watch to take out of it, and burning with curiosity, she ran across the field after it, and fortunately was just in time to see it pop down a large rabbit-hole under the hedge.
;

히스토그램을 그립니다.
A---------------------------------------------------------------------------------------
B-------------------------
C----------------------------
D--------------------------------------------
E-----------------------------------------------------------------------------------------------------------------------------
F-------------------
G-------------------
H-------------------------------------------------------------------------
I------------------------------------------------------------------------------
J-
K-------------
L------------------------------
M---------
N------------------------------------------------------------
O-------------------------------------------------------------------------------
P--------------
Q-
R------------------------------------------------------------------
S-----------------------------------------------------------
T----------------------------------------------------------------------------------------------------------------------
U-------------------------------
V----------
W----------------------------
X
Y----------------
Z
*/
