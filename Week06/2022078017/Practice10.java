package javapractice4;

import java.util.Scanner;
import java.util.Random;


abstract class Player {
   
    protected String[] bet = {"묵", "찌", "빠"};

    protected String name;
  
    protected String lastBet = null;

  
    public Player(String name) {
        this.name = name;
    }

  
    public String getName() {
        return name;
    }

   
    public String getLastBet() {
        return lastBet;
    }

    abstract public String next();
}


class Human extends Player {
    private Scanner scanner;

    public Human(String name) {
        super(name);
        scanner = new Scanner(System.in);
    }

    @Override
    public String next() {
        System.out.print(name + ">>");
        while (true) {
            String input = scanner.next();
            boolean isValid = false;
            for (String s : bet) {
                if (s.equals(input)) {
                    isValid = true;
                    break;
                }
            }
            if (isValid) {
                lastBet = input; // 유효한 입력이면 최근 패로 저장
                return lastBet;
            } else {
                System.out.println("잘못된 입력입니다. '묵', '찌', '빠' 중에서 다시 입력하세요.");
                System.out.print(name + ">>");
            }
        }
    }
}

class Computer extends Player {
    private Random random;

    public Computer(String name) {
        super(name);
        random = new Random();
    }

    @Override
    public String next() {
        int index = random.nextInt(3); 
        lastBet = bet[index]; 
        System.out.println("결정하였습니다.");
        return lastBet;
    }
}

class Game {
    private Player[] players = new Player[2]; 
    private Scanner scanner = new Scanner(System.in);

    public Game() {
        createPlayer();
    }

    public void createPlayer() {
        System.out.println("***** 묵찌빠 게임을 시작합니다. *****");
        System.out.print("선수 이름 입력>>");
        String humanName = scanner.next();
        System.out.print("컴퓨터 이름 입력>>");
        String computerName = scanner.next();
        System.out.println("2명의 선수를 생성 완료하였습니다...");
        
        players[0] = new Human(humanName);
        players[1] = new Computer(computerName);
    }

    public void run() {
     
        Player owner = players[0];
        
        while (true) {
            System.out.println(owner.getName() + "이/가 오너입니다.");
            
            String humanBet = players[0].next();
            String computerBet = players[1].next();

            System.out.println(players[0].getName() + " : " + humanBet + ", " + players[1].getName() + " : " + computerBet);

            if (humanBet.equals(computerBet)) {
                System.out.println(owner.getName() + "이/가 이겼습니다...");
                System.out.println("게임을 종료합니다.");
                break; 
            } 
            else {
                if ((humanBet.equals("찌") && computerBet.equals("빠")) ||
                    (humanBet.equals("묵") && computerBet.equals("찌")) ||
                    (humanBet.equals("빠") && computerBet.equals("묵"))) {
                    owner = players[0];
                } 
                else {
                    owner = players[1];
                }
            }
        }
        scanner.close();
    }
}

public class MGPApp {
    public static void main(String[] args) {
        new Game().run();
    }
}