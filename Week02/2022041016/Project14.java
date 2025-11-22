import java.util.Scanner;
import java.util.Arrays;
public class Project14{
    public static void main(String[] args){
        Scanner s = new Scanner(System.in);
        System.out.println("가위바위보 게임입니다. 가위, 바위, 보 중에서 입력하세요");
        System.out.print("철수 >> ");
        String cheol = s.next();
        System.out.print("영희 >> ");
        String young = s.next();
        String arr[] = {"가위", "바위", "보"};
        int c = Arrays.asList(arr).indexOf(cheol);
        int y = Arrays.asList(arr).indexOf(young);
        switch (c-y){
            case -2:
            case 1:
                System.out.println("철수가 이겼습니다!");
                break;
            case 2:
            case -1:
                System.out.println("영희가 이겼습니다!");
                break;
            case 0:
                System.out.println("비겼습니다!");
                break;
            default:
                System.out.println("가위바위보 승패를 알 수 없습니다!");
                break;
        }
    }
}
