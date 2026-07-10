import java.util.Scanner;
import java.util.Random;
abstract class Player {
  protected String bet[] = {"묵","찌","빠"};
  protected String name;
  protected String lastBet= null;
  protected Player(String name) { this.name = name; }
  public String getName() { return name; }
  public String getBet() { return lastBet; }
  public void setBet(int index) { lastBet = bet[index]; }
  public void setBet(String bet) { lastBet = bet; }
  abstract public String next();
}
class Human extends Player {
  private Scanner scanner = new Scanner(System.in);
  public Human(String name) {
    super(name);
  }
  @Override
  public String next() {
    System.out.print(this.getName()+">>");
    String bet = scanner.next();
    setBet(bet);
    return getBet();
  }
}
class Computer extends Player {
  public Computer(String name) {
    super(name);
  }
  @Override
  public String next() {
    int index = new Random().nextInt(3);
    setBet(index);
    System.out.println(this.getName()+">> 결정하였습니다.");
    return getBet();
  }
}
class Game {
  private Player [] players = new Player[2];
  private Scanner scanner = new Scanner(System.in);
  public Game() { }
  private void createPlayer() {
    System.out.print("선수이름 입력>>");
    String name = scanner.next();
    players[0] = new Human(name);
    System.out.print("컴퓨터 입력>>");
    name = scanner.next();
    players[1] = new Computer(name);
    System.out.println("2명의 선수를 생성 완료하였습니다...\n");
    System.out.println();
  }
  public void run() {
    System.out.println("***** 묵찌빠 게임을 시작합니다. *****");
    createPlayer();
    int owner = 0; // 0 = Human, 1 = Computer
    int winner = -1;
    do{
      String ob = players[owner].next();
      String nob = players[Math.abs(owner-1)].next();
      System.out.println(players[owner].getName()+" : "+ob+", "+players[Math.abs(owner-1)].getName()+" : "+nob);
      if((ob.equals("묵") && nob.equals("빠")) || (ob.equals("빠") && nob.equals("찌")) || (ob.equals("찌") && nob.equals("묵"))){
        owner = Math.abs(owner-1);
        System.out.println("오너가 "+players[owner].getName()+"로(으로) 변경되었습니다.");
      }
      System.out.println();
    }while(!players[owner].getBet().equals(players[Math.abs(owner-1)].getBet()));
    System.out.println(players[owner].getName()+"이(가) 이겼습니다.");
    System.out.println("게임을 종료합니다...");
  }
}
public class MGPApp{
  public static void main(String[] args) {
    new Game().run();
  }
}
