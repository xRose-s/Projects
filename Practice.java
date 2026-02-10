//Class and Data Mebers 

class student {
    int id;
    String name;
    student s1 = new student();

    void display() {
        System.out.println(id + " " + name);

    }
}

// Making a syntax --

public class Main {
    public static void main(String[] args) {
        System.out.println("Hello WOrld ");

    }
}

// this keyword --
class teacher {
    int id;
    String name;

    teacher(int roll, String name) {
        this.id = roll;
        this.name = name;
    }

}

// Method overriding

class AnimalSound {
    void sound() {
        System.out.println("Animal sound");
    }
}

class Dog extends AnimalSound {
    void sound() {
        System.out.println("Dog Barks");
    }
}
