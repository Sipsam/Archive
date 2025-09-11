package test;
import java.util.Scanner;
 public class GbbGame{
	 public static void main(String[] args) {
		 Scanner scanner= new Scanner(System.in);
		 System.out.print("가위바위보 게임 입니다. 가위, 바위, 보 중에서 입력하세요. ");
		 System.out.print("철수>>");
		 String cheolsoo = scanner.next();
		 System.out.print("영희>>");
		 String younghee = scanner.next();
		 if(cheolsoo.equals("가위")) {
			 if(younghee.equals("가위")) {
				 System.out.print("비겼습니다.");
			 }
			 else if(younghee.equals("바위")) {
				 System.out.print("영희가 이겼습니다." );
			 }
			 else if(younghee.equals("보")) {
				 System.out.print("철수가 이겼습니다.");
			 }
		 }
		 if(cheolsoo.equals("바위")) {
			 if(younghee.equals("가위")) {
				 System.out.print("철수가 이겼습니다.");
			 }
			 else if(younghee.equals("바위")) {
				 System.out.print("비겼습니다.");
			 }
			 else if(younghee.equals("보")) {
				 System.out.print("영희가 이겼습니다.");
			 }
		 }
		 if(cheolsoo.equals("보")) {
			 if(younghee.equals("가위")) {
				 System.out.print("영희가 이겼습니다.");
			 }
			 else if(younghee.equals("바위")) {
				 System.out.print("철수가 이겼습니다.");
			 }
			 else if(younghee.equals("보")) {
				 System.out.print("비겼습니다.");
			 }
		 }
		 scanner.close();
 }
 }
