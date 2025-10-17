package test;

import java.util.Random;
import java.util.Scanner;

abstract class Player {
    protected String[] bet = {"묵", "찌", "빠"};
    protected String name;
    protected String lastBet = null;

    protected Player(String name) {
        this.name = name;
    }

    public String getName() { return name; }
    public String getBet() { return lastBet; }

    abstract public String next();
}

class Human extends Player {
    private Scanner scanner = new Scanner(System.in);

    public Human(String name) {
        super(name);
    }

    @Override
    public String next() {
        System.out.print(name + ">>");
        lastBet = scanner.next();

        while (!lastBet.equals("묵") && !lastBet.equals("찌") && !lastBet.equals("빠")) {
            System.out.print("잘못 입력했습니다. 다시 입력하세요: ");
            lastBet = scanner.next();
        }
        return lastBet;
    }
}

class Computer extends Player {
    private Random random = new Random();

    public Computer(String name) {
        super(name);
    }

    @Override
    public String next() {
        System.out.println(name + ">> 결정하였습니다.");
        lastBet = bet[random.nextInt(3)];
        return lastBet;
    }
}

class Game {
    private Player[] players = new Player[2];
    private Player owner;
    private Scanner scanner = new Scanner(System.in);

    public Game() {
        createPlayers();
        owner = players[0];
    }

    private void createPlayers() {
        System.out.print("선수이름 입력>>");
        String humanName = scanner.next();
        System.out.print("컴퓨터이름 입력>>");
        String computerName = scanner.next();

        players[0] = new Human(humanName);
        players[1] = new Computer(computerName);

        System.out.println("2명의 선수를 생성 완료하였습니다...\n");
    }

    private int judge(String p1, String p2) {
        if (p1.equals(p2)) return 0;
        if ((p1.equals("묵") && p2.equals("찌")) ||
            (p1.equals("찌") && p2.equals("빠")) ||
            (p1.equals("빠") && p2.equals("묵"))) {
            return 1;
        }
        return -1;
    }
    public void run() {
        System.out.println("***** 묵찌빠 게임을 시작합니다. *****");

        while (true) {
            if (owner == players[0]) {
                String humanBet = players[0].next();
                String computerBet = players[1].next();
                System.out.println(players[0].getName() + " : " + humanBet + ", " +
                                   players[1].getName() + " : " + computerBet + "\n");

                int result = judge(humanBet, computerBet);

                if (result == 0) {
                    System.out.println(owner.getName() + "이 이겼습니다.");
                    System.out.println("게임을 종료합니다...");
                    break;
                } else if (result == 1) {
                } else {
                    owner = players[1];
                    System.out.println("오너가 " + owner.getName() + "로 변경되었습니다.\n");
                }
            } 
            else {
                String computerBet = players[1].next();
                String humanBet = players[0].next();
                System.out.println(players[1].getName() + " : " + computerBet + ", " +
                                   players[0].getName() + " : " + humanBet + "\n");

                int result = judge(computerBet, humanBet);

                if (result == 0) {
                    System.out.println(owner.getName() + "이 이겼습니다.");
                    System.out.println("게임을 종료합니다...");
                    break;
                } else if (result == 1) {
                } else {
                    owner = players[0];
                    System.out.println("오너가 " + owner.getName() + "로 변경되었습니다.\n");
                }
            }
        }
    }
}
public class MGPapp {
    public static void main(String[] args) {
        new Game().run();
    }
}

