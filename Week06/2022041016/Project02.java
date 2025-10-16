class Person{
  private int weight;
  int age;
  protected int height;
  public String name;

  public void setWeight(int weight){
    this.weight = weight;
  }
  public int getWeight(){
    return weight;
  }
}
class Student extends Person{
  public vodi set(){
    age = 30;
    name = "홍길동";
    height = 175;
    // weight = 99; // weight는 Person의 private, 자식인 Student에서 접근 불가
    setWeight(99); // 부모의 private member weight 간접 접근
  }
}
public class InheritanceEx{
  public static void main(String[] args){
    Student s = new Student();
    s.set();
  }
}
