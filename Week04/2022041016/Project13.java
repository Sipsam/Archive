import java.util.Scanner;
public class WordGameApp{
  Player[] players;
  String nowWord;
  public WordGameApp(){
    this.nowWord = "아버지";
  }
  private void createPlayers(Scanner s){
    System.out.print("게임에 참가하는 인원은 몇명입니까>>");
    int num = s.nextInt();
    s.nextLine();
    this.players = new Player[num];
    for(int i=0;i<num;i++){
      System.out.print("참가자의 이름을 입력하세요>>");
      String name = s.nextLine();
      this.players[i] = new Player(name);
    }
  }
  public Boolean checkSuccess(char lastWord, char newWord){
     return lastWord == newWord;
  }
  public void run(){
    Scanner s = new Scanner(System.in);
    System.out.println("끝말잇기 게임을 시작합니다...");
    this.createPlayers(s);
    System.out.println("시작하는 단어는 "+this.nowWord+"입니다.");
    int nextP = 0;
    while(true){
      if(nextP >= this.players.length) nextP = 0;
      String word = this.players[nextP].getWordFromUser(s);
      if(!checkSuccess(this.nowWord.charAt(nowWord.length()-1), word.charAt(0))){
        System.out.println(this.players[nextP].name+"이(가) 졌습니다.");
        break;
      }
      this.nowWord = word;
      nextP++;
    }
    s.close();
  }
  public static void main(String[] args){
    WordGameApp app = new WordGameApp();
    app.run();
  }
}
class Player{
  public String name;
  public Player(String name){
    this.name = name;
  }
  public String getWordFromUser(Scanner s){
    System.out.print(this.name+">>");
    String word = s.nextLine();
    return word;
  }
}
