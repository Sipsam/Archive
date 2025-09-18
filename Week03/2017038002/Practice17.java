package test;
import java.util.Random;
import java.util.Scanner;

public class CardGame {
    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        Random random = new Random();

        while (true) {
            int num = random.nextInt(100);
            System.out.println("수를 결정하였습니다. 맞추어 보세요\n0~99");
            int attemps = 1;
            while (true) {
                System.out.print(attemps+">>");
                int guess = scanner.nextInt();
                attemps++;
                if (guess == num) {
                    System.out.println("맞았습니다.");
                    break; 
                } else if (guess > num) {
                    System.out.println("더 낮게");
                } else {
                    System.out.println("더 높게");
                }
            }

            System.out.print("다시하시겠습니까(y/n)>> ");
            String text = scanner.next();

            if (text.equalsIgnoreCase("n")) { // 대소문자 구분 없이 종료
                System.out.println("게임을 종료합니다.");
                break;
            }
        }

        scanner.close();
    }
}
