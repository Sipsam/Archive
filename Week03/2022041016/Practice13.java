public class Calc{
  public static void main(String[] args){
    double sum = 0.0;
    for(int i=0;i<args.length;i++)
      sum += double.parseDouble(args[i]);
    System.out.println("합계 : "+sum);
  }
}
