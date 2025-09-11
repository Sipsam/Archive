import java.util.Scanner;

public class Practice09 {	// MultipleOfThree

	public static void main(String[] args) {
		Scanner in = new Scanner(System.in);
		
		System.out.print("수를 입력하시오 : ");
		int number = in.nextInt();
		
		if (number%3==0)
			System.out.println("3의 배수입니다.");
		else
			System.out.println("3의 배수가 아닙니다.");
		
		in.close();	// 앞쪽에서 scanner 대신 in 으로 선언했기 때문에 in.close();가 와야
	}

}
