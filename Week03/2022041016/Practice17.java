import java.util.Scanner;
public class GuessNumberGame{
  public static void main(String[] args){
    Scanner s = new Scanner(System.in);
    S: while(true){
      int rand = (int)(Math.random()*100);
      System.out.println("수를 결정하였습니다. 맞추어 보세요.");
      int sp = 0; int ep = 99;
      int c = 1;
      I: while(true){
        System.out.println(sp+"-"+ep);
        System.out.print((c++)+">>");
        int t = s.nextInt();
        if(t<sp || t > ep){
          System.out.println("범위를 벗어났습니다. 다시 입력해주세요("+sp+"-"+ep+")");
          continue I;
        }
        if(t == rand){
          System.out.println("맞았습니다.");
          System.out.print("다시하시겠습니까(y/n)>>");
          String text = s.next();
          if(text.equals("n"))
            break S;
          else continue S;
        }else if(t < rand){
          System.out.println("더 높게");
          sp = t;
        }else if(t > rand){
          System.out.println("더 낮게");
          ep = t;
        }
      }
    }
    s.close();
  }
}
