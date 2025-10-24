import java.util.Scanner;
public class AlphabetHistogramApp {
    private int[] histogram;
    public AlphabetHistogramApp() {
        histogram = new int[26];
    }
    public void run() {
        System.out.println("영문 텍스트를 입력하고, 세미콜론을 입력하세요.");
        System.out.println();
        String text = readString();
        makeHistogram(text);
        drawHistogram();
    }
    private void makeHistogram(String text) {
        text = text.toUpperCase();
        for (int i = 0; i < text.length(); i++) {
            char c = text.charAt(i);
            if (c >= 'A' && c <= 'Z') {
                int index = c - 'A';
                histogram[index]++;
            }
        }
    }
    private void drawHistogram() {
        System.out.println("\n히스토그램을 그립니다.");
        for (int i = 0; i < 26; i++) {
            char alphabet = (char) ('A' + i);
            int count = histogram[i];
            System.out.print(alphabet + "");
            for (int j = 0; j < count; j++) System.out.print("-");
            System.out.println();
        }
    }
    private String readString() {
        StringBuffer sb = new StringBuffer();
        Scanner scanner = new Scanner(System.in);
        while (true) {
            String line = scanner.nextLine();
            if (line.equals(";")) break;
            sb.append(line);
        }
        return sb.toString();
    }
    public static void main(String[] args) {
        AlphabetHistogramApp app = new AlphabetHistogramApp();
        app.run();
    }
}
/* 입력/출력
  영문 텍스트를 입력하고, 세미콜론을 입력하세요.

Lady Gaga. Bradley Cooper - Shallow (from A Star Is Born)
Tell mew something, girl
Are you happy in this modern world?
Or do you need more?
Is there something else you're searchin' for?
I'm falling
In all the good times, I find myself longin' for change
And in the bad tiems, I fear myself
Tell me something, boy
Aren't you tired trying to fill that void?
Or do you need more?
Ain't it hard keeping it so hardcore?
I'm falling
In all the good times, I find myself longing for change
And in the bad times, I fear myself
I'm off the deep end, watch as I dive in
I'll never meet the ground
Crash through the surface, where they can't hurt us
We're far from the shallow now
Int the sha-ha, sh-ha-llow
In the sha-ha-sha-la-la-la-llow
In the sha-ha, sha-ha-llow
We're far from the shallow now
Oh, ha-ah-ah
Ah, ha-ah-ah, oh, ah
Ha-ah-ah-ah
I'm off the deep end, watch as I dive in
I'll never meet the ground
Crash through the surface, where they can't hurt us
We're far from the shallow now
Int the sha-ha, sha-ha-llow
In the sha-ha-sha-la-la-la-llow
In the sha-ha, sha-ha-llow
;

히스토그램을 그립니다.
A----------------------------------------------------------------------------------
B-----
C-------------
D----------------------------
E-----------------------------------------------------------------------------------------
F---------------------------
G---------------------
H-------------------------------------------------------------------------------------
I-----------------------------------------------------
J
K-
L-------------------------------------------------------
M--------------------------
N------------------------------------------------
O----------------------------------------------------------
P------
Q
R--------------------------------------------------
S------------------------------------------
T------------------------------------------------------
U---------------
V-----
W----------------------
X
Y----------------
Z
  */
