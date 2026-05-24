# Java基础知识 - 20K薪资面试题

> 本文档包含Java基础相关面试题，涵盖语法、面向对象、异常处理、泛型等核心知识点。

---

## 第一部分：语法基础（共10题）

### Q1: Java的基本数据类型有哪些？它们的大小和默认值是什么？

**题目类型**：基础概念类

**问题描述**：Java语言中有哪些基本数据类型？它们占用多少字节？默认值分别是什么？

**答案要点**：

**四类八种数据类型：**

| 数据类型 | 关键字 | 字节数 | 位数 | 默认值 | 取值范围 |
|---------|--------|--------|------|--------|----------|
| 整型 | byte | 1 | 8 | 0 | -128 ~ 127 |
| 整型 | short | 2 | 16 | 0 | -32768 ~ 32767 |
| 整型 | int | 4 | 32 | 0 | -2^31 ~ 2^31-1 |
| 整型 | long | 8 | 64 | 0L | -2^63 ~ 2^63-1 |
| 浮点型 | float | 4 | 32 | 0.0f | ±3.4E38 |
| 浮点型 | double | 8 | 64 | 0.0d | ±1.7E308 |
| 字符型 | char | 2 | 16 | '\u0000' | 0 ~ 65535 |
| 布尔型 | boolean | 1 | 8 | false | true/false |

**注意事项：**
- String是引用类型，不是基本数据类型
- 整型默认是int，浮点型默认是double
- char使用Unicode编码，可以存储中文

---

### Q2: == 和 equals() 方法有什么区别？

**题目类型**：基础概念类

**问题描述**：在Java中，`==`和`equals()`方法在比较对象时有什么区别？什么时候使用哪个？

**答案要点**：

**== 操作符：**
- 比较的是两个对象的引用地址（内存地址）
- 对于基本数据类型，比较的是值
- 引用类型比较的是堆内存地址

**equals() 方法：**
- 是Object类的方法，默认实现和`==`相同
- 可以被重写实现自定义比较逻辑
- String类重写了equals()，比较内容而非地址

**示例说明：**

```java
String s1 = new String("hello");
String s2 = new String("hello");

System.out.println(s1 == s2);        // false，地址不同
System.out.println(s1.equals(s2));  // true，内容相同

Integer a = 127;
Integer b = 127;
System.out.println(a == b);         // true，缓存范围内

Integer c = 128;
Integer d = 128;
System.out.println(c == d);         // false，超出缓存范围
```

**最佳实践：**
- 比较String内容使用equals()
- 比较包装类型值使用equals()
- 避免使用==比较字符串

---

### Q3: String、StringBuilder、StringBuffer的区别是什么？

**题目类型**：技术对比类

**问题描述**：在Java中处理字符串时，String、StringBuilder和StringBuffer三者有什么区别？各自的使用场景是什么？

**答案要点**：

**核心区别：**

| 特性 | String | StringBuilder | StringBuffer |
|------|--------|--------------|--------------|
| 可变性 | 不可变 | 可变 | 可变 |
| 线程安全 | 安全（不可变） | 不安全 | 安全（synchronized） |
| 性能 | 每次修改创建新对象 | 高 | 中等 |
| 使用场景 | 字符串常量 | 单线程字符串拼接 | 多线程字符串操作 |

**源码分析：**

```java
// String 每次拼接都创建新对象
String s = "a" + "b" + "c";  // 产生多个中间对象

// StringBuilder 高效拼接
StringBuilder sb = new StringBuilder();
sb.append("a").append("b").append("c");
String result = sb.toString();

// StringBuffer 线程安全版本
StringBuffer sbf = new StringBuffer();
sbf.append("a").append("b").append("c");
```

**性能对比：**
- String: O(n²) 时间复杂度（每次创建新对象）
- StringBuilder: O(n) 时间复杂度
- StringBuffer: O(n) 时间复杂度（有同步开销）

**使用建议：**
- 字符串常量用String
- 单线程字符串拼接用StringBuilder
- 多线程字符串操作用StringBuffer

---

### Q4: Java中的访问修饰符有哪些？它们的作用范围是什么？

**题目类型**：基础概念类

**问题描述**：Java提供了哪些访问修饰符？它们各自的作用范围是什么？

**答案要点**：

**四种访问修饰符：**

| 修饰符 | 同类 | 同包 | 子类 | 不同包 |
|--------|------|------|------|--------|
| private | ✓ | ✗ | ✗ | ✗ |
| default(无修饰) | ✓ | ✓ | ✗ | ✗ |
| protected | ✓ | ✓ | ✓ | ✗ |
| public | ✓ | ✓ | ✓ | ✓ |

**详细说明：**

```java
public class AccessModifiers {
    
    public String publicField = "公开";
    protected String protectedField = "受保护";
    String defaultField = "默认";  // default
    private String privateField = "私有";
    
    // public: 任何地方都可访问
    public void publicMethod() {}
    
    // protected: 同包及子类可访问
    protected void protectedMethod() {}
    
    // default: 同包内可访问
    void defaultMethod() {}
    
    // private: 只能在本类访问
    private void privateMethod() {}
}
```

**最佳实践：**
- 成员变量尽量private
- 提供public的getter/setter方法
- 只在需要被继承时使用protected

---

### Q5: 什么是值传递和引用传递？Java是哪种？

**题目类型**：技术原理类

**问题描述**：Java中参数的传递方式是什么？是值传递还是引用传递？有什么区别？

**答案要点**：

**定义区分：**
- **值传递**：传递参数的副本，修改不影响原值
- **引用传递**：传递参数的引用地址，修改会影响原值

**Java是值传递：**

```java
// 基本数据类型 - 值传递
public void changePrimitive(int num) {
    num = 100;  // 不影响原值
}

int a = 10;
changePrimitive(a);
System.out.println(a);  // 仍是10

// 引用数据类型 - 传递的是引用的副本
public void changeObject(StringBuilder sb) {
    sb.append(" world");  // 影响原对象
    sb = new StringBuilder("new");  // 只改变局部引用
}

StringBuilder sb = new StringBuilder("hello");
changeObject(sb);
System.out.println(sb.toString());  // "hello world"
```

**关键理解：**
- Java总是传递值的副本
- 对于引用类型，副本是指向对象的地址
- 在方法内重新赋值引用参数，不会影响原引用

---

### Q6: 重载(Overload)和重写(Override)的区别是什么？

**题目类型**：技术对比类

**问题描述**：Java中的重载和重写有什么区别？各自的规则是什么？

**答案要点**：

**重载(Overload) - 编译时多态：**

```java
public class Calculator {
    // 方法名相同，参数列表不同
    public int add(int a, int b) {
        return a + b;
    }
    
    public double add(double a, double b) {
        return a + b;
    }
    
    public int add(int a, int b, int c) {
        return a + b + c;
    }
}
```

**重写(Override) - 运行时多态：**

```java
public class Parent {
    public void method() {
        System.out.println("Parent method");
    }
}

public class Child extends Parent {
    @Override
    public void method() {
        System.out.println("Child method");
    }
}
```

**核心区别：**

| 区别 | 重载 | 重写 |
|------|------|------|
| 发生位置 | 同一个类 | 父类和子类 |
| 方法名 | 必须相同 | 必须相同 |
| 参数列表 | 必须不同 | 必须相同 |
| 返回类型 | 可以不同 | 必须兼容 |
| 访问修饰符 | 可以不同 | 不能更严格 |
| 异常处理 | 可以不同 | 不能抛出新异常 |
| 关键字 | 无要求 | @Override |

---

### Q7: final关键字有哪些作用？

**题目类型**：基础概念类

**问题描述**：Java中的final关键字可以修饰什么？分别有什么作用？

**答案要点**：

**final修饰的四个场景：**

```java
// 1. 修饰变量 - 变成常量
final int CONSTANT = 100;
// CONSTANT = 200;  // 编译错误

// 2. 修饰方法参数
public void method(final int num) {
    // num = 100;  // 编译错误
}

// 3. 修饰方法 - 不能被重写
public final void finalMethod() {
    System.out.println("Cannot override");
}

// 4. 修饰类 - 不能被继承
public final class FinalClass {
    // String就是final类
}

// class SubClass extends FinalClass {}  // 编译错误
```

**应用场景：**
- 定义常量：`public static final double PI = 3.14159`
- 防止方法被重写：如Object类的getClass()
- 防止类被继承：如String、Integer等

---

### Q8: static关键字有哪些作用？

**题目类型**：基础概念类

**问题描述**：static关键字可以修饰什么？它们的作用是什么？

**答案要点**：

**static修饰的四个场景：**

```java
public class StaticDemo {
    
    // 1. 静态变量 - 类所有对象共享
    static int count = 0;
    
    // 2. 静态方法 - 属于类，可直接调用
    public static void staticMethod() {
        // 不能使用this/super
        // 不能访问实例成员
        System.out.println("Static method");
    }
    
    // 3. 静态代码块 - 类加载时执行一次
    static {
        count = 10;
        System.out.println("Static block");
    }
    
    // 4. 静态内部类
    public static class InnerClass {
        // 只能访问外部类的静态成员
    }
}
```

**执行顺序：**
```
静态变量/代码块 → 构造代码块 → 构造函数
```

**注意事项：**
- 静态方法不能访问非静态成员
- 静态方法不能使用this/super
- 静态变量是线程共享的，需要注意线程安全

---

### Q9: 抽象类(abstract class)和接口(interface)的区别是什么？

**题目类型**：技术对比类

**问题描述**：Java中抽象类和接口有什么区别？各自的使用场景是什么？

**答案要点**：

**核心区别对比：**

| 特性 | 抽象类 | 接口 |
|------|--------|------|
| 关键字 | abstract class | interface |
| 继承/实现 | extends（单继承） | implements（多实现） |
| 方法 | 可以有抽象和普通方法 | JDK7：全是抽象；JDK8+：default/static |
| 变量 | 可以有任何类型 | 只能是public static final |
| 构造方法 | 可以有 | 不能有 |
| 静态方法 | 可以有 | JDK8+可以有 |
| 使用场景 | "是什么"关系 | "能做什么"关系 |

**代码示例：**

```java
// 抽象类 - 描述"是什么"
abstract class Animal {
    String name;
    
    public Animal(String name) {
        this.name = name;
    }
    
    abstract void eat();
}

// 接口 - 描述"能做什么"
interface Flyable {
    void fly();
}

interface Swimmable {
    void swim();
}

// 企鹅是动物，但也会游泳
class Penguin extends Animal implements Swimmable {
    public Penguin(String name) {
        super(name);
    }
    
    @Override
    void eat() {
        System.out.println("吃鱼");
    }
    
    @Override
    public void swim() {
        System.out.println("企鹅游泳");
    }
}
```

**JDK8+接口新特性：**
```java
interface Calculator {
    // 抽象方法
    int add(int a, int b);
    
    // 默认方法 - 有默认实现
    default int subtract(int a, int b) {
        return a - b;
    }
    
    // 静态方法
    static int multiply(int a, int b) {
        return a * b;
    }
}
```

---

### Q10: 什么是多态？Java中如何实现多态？

**题目类型**：技术原理类

**问题描述**：什么是多态？Java中多态的实现原理是什么？

**答案要点**：

**多态的定义：**
同一类型的引用指向不同对象时，表现出不同的行为特征。

**多态的三个必要条件：**
1. 继承（或有实现关系）
2. 重写
3. 父类引用指向子类对象

**代码示例：**

```java
// 父类
abstract class Shape {
    abstract void draw();
}

// 子类
class Circle extends Shape {
    @Override
    void draw() {
        System.out.println("画圆形");
    }
}

class Rectangle extends Shape {
    @Override
    void draw() {
        System.out.println("画矩形");
    }
}

// 使用
public class Test {
    public static void main(String[] args) {
        // 父类引用指向子类对象
        Shape s1 = new Circle();
        Shape s2 = new Rectangle();
        
        s1.draw();  // 输出：画圆形
        s2.draw();  // 输出：画矩形
    }
}
```

**多态的两种形式：**
1. **编译时多态（静态绑定）**：方法重载
2. **运行时多态（动态绑定）**：方法重写

**向上转型与向下转型：**
```java
// 向上转型 - 自动转换
Animal animal = new Dog();  // 子类转父类

// 向下转型 - 需要强制转换
Dog dog = (Dog) animal;  // 父类转子类（可能抛出ClassCastException）

// instanceof 运算符进行安全检查
if (animal instanceof Dog) {
    Dog dog = (Dog) animal;
}
```

---

## 第二部分：核心概念（共10题）

### Q11: 什么是反射(reflection)？它的应用场景有哪些？

**题目类型**：技术原理类

**问题描述**：Java的反射机制是什么？它有哪些应用场景？

**答案要点**：

**反射的定义：**
在运行时动态获取类的信息（属性、方法、构造器）和动态调用对象方法的能力。

**反射的核心API：**

```java
public class ReflectionDemo {
    public static void main(String[] args) throws Exception {
        // 获取Class对象的三种方式
        Class<?> clazz1 = Class.forName("com.example.User");
        Class<?> clazz2 = User.class;
        Class<?> clazz3 = new User().getClass();
        
        // 获取类信息
        String className = clazz1.getName();  // 包名+类名
        String simpleName = clazz1.getSimpleName();  // 类名
        
        // 获取成员变量
        Field[] fields = clazz1.getDeclaredFields();
        for (Field field : fields) {
            field.setAccessible(true);  // 访问私有成员
            Object value = field.get(obj);  // 获取值
        }
        
        // 获取方法
        Method[] methods = clazz1.getDeclaredMethods();
        for (Method method : methods) {
            method.setAccessible(true);
            method.invoke(obj, args);  // 调用方法
        }
        
        // 获取构造器
        Constructor<?> constructor = clazz1.getDeclaredConstructor(String.class);
        Object instance = constructor.newInstance("参数");
    }
}
```

**应用场景：**

| 场景 | 说明 |
|------|------|
| Spring IOC | 通过反射创建和管理Bean |
| JDBC | 加载驱动，创建Connection |
| 注解处理器 | 读取和处理注解 |
| 序列化 | 如Jackson、Gson的ObjectMapper |
| 框架通用性 | 通用处理不同类型的对象 |

**反射的优缺点：**
- 优点：灵活、可扩展、通用性强
- 缺点：性能损耗、安全检查、破坏封装性

---

### Q12: 什么是注解(Annotation)？自定义注解如何实现？

**题目类型**：技术原理类

**问题描述**：Java注解是什么？如何自定义注解？注解有哪些应用场景？

**答案要点**：

**注解的定义：**
一种代码元数据，为程序提供编译时和运行时的附加信息。

**元注解（注解的注解）：**

```java
@Target(ElementType.METHOD)           // 作用目标
@Retention(RetentionPolicy.RUNTIME)  // 生命周期
@Documented                           // 包含在Javadoc中
@Inherited                            // 可继承
public @interface MyAnnotation {
    // 注解属性
    String value() default "default";
    int priority() default 0;
}
```

**生命周期对比：**

| RetentionPolicy | 说明 | 使用场景 |
|-----------------|------|----------|
| SOURCE | 只在源代码中 | @Override、@SuppressWarnings |
| CLASS | 编译时保留 | Lombok等字节码增强 |
| RUNTIME | 运行时常驻 | Spring注解、数据库映射 |

**注解处理器示例：**

```java
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
@interface Log {
    String value() default "";
}

// 使用注解
public class UserService {
    @Log("保存用户")
    public void saveUser(User user) {
        // 业务逻辑
    }
}

// 解析注解
public class AnnotationProcessor {
    public static void process(Object obj) {
        Method[] methods = obj.getClass().getDeclaredMethods();
        for (Method method : methods) {
            if (method.isAnnotationPresent(Log.class)) {
                Log log = method.getAnnotation(Log.class);
                System.out.println("执行方法: " + method.getName() + ", 描述: " + log.value());
            }
        }
    }
}
```

**常见框架注解：**
- Spring: @Component, @Service, @Autowired, @RequestMapping
- JPA: @Entity, @Table, @Column, @Id
- MyBatis: @Select, @Insert, @Update, @Delete

---

### Q13: 什么是泛型(Generic)？为什么要使用泛型？

**题目类型**：技术原理类

**问题描述**：Java泛型是什么？使用泛型有什么好处？

**答案要点**：

**泛型的定义：**
一种参数化类型机制，允许在定义类、接口、方法时使用类型参数。

**使用泛型的原因：**
1. 编译时类型检查
2. 避免类型转换
3. 代码复用

**泛型类、接口、方法：**

```java
// 泛型类
public class Box<T> {
    private T content;
    
    public T getContent() {
        return content;
    }
    
    public void setContent(T content) {
        this.content = content;
    }
}

// 泛型接口
public interface Comparable<T> {
    int compareTo(T o);
}

// 泛型方法
public static <T> void printArray(T[] array) {
    for (T element : array) {
        System.out.println(element);
    }
}

// 使用
Box<String> stringBox = new Box<>();
stringBox.setContent("Hello");
// 不需要强制类型转换
String value = stringBox.getContent();
```

**泛型通配符：**

| 通配符 | 说明 | 特点 |
|--------|------|------|
| <?> | 无限制通配符 | 可以接收任何类型 |
| <? extends T> | 上界通配符 | 只能读取（T的子类） |
| <? super T> | 下界通配符 | 只能写入（T的父类） |

```java
// PECS原则：Producer-Extends, Consumer-Super
public void read(List<? extends Number> list) {
    Number num = list.get(0);  // 可以读
    // list.add(1);  // 编译错误，不能写
}

public void write(List<? super Integer> list) {
    list.add(1);  // 可以写
    // Number num = list.get(0);  // 编译错误，不能确定类型
}
```

**类型擦除：**
- 泛型信息在编译时会被擦除
- 运行时无法获取泛型类型信息
- 需要通过TypeToken等方式保留泛型信息

---

### Q14: 什么是异常处理？try-catch-finally的执行顺序是什么？

**题目类型**：技术原理类

**问题描述**：Java异常处理机制是什么？try-catch-finally块的执行顺序如何？

**答案要点**：

**异常体系：**

```
Throwable
├── Error (系统错误，不能捕获)
│   ├── OutOfMemoryError
│   └── StackOverflowError
└── Exception
    ├── RuntimeException (非检查异常)
    │   ├── NullPointerException
    │   ├── IndexOutOfBoundsException
    │   └── ClassCastException
    └── 其他Exception (检查异常)
        ├── IOException
        └── SQLException
```

**try-catch-finally执行顺序：**

```java
public class ExceptionDemo {
    public static void main(String[] args) {
        try {
            System.out.println("1. try块开始");
            int result = 10 / 0;  // 抛出 ArithmeticException
            System.out.println("2. try块结束");  // 不会执行
        } catch (ArithmeticException e) {
            System.out.println("3. catch块 - 处理异常");
        } finally {
            System.out.println("4. finally块 - 始终执行");
        }
    }
}
// 输出: 1 -> 3 -> 4
```

**try-with-resources语法：**

```java
// 自动关闭资源
try (FileInputStream fis = new FileInputStream("file.txt");
     BufferedReader br = new BufferedReader(new InputStreamReader(fis))) {
    String line = br.readLine();
    System.out.println(line);
} catch (IOException e) {
    e.printStackTrace();
}
// 无需手动关闭，finally也不需要
```

**注意事项：**
1. finally块始终执行，即使try/catch中有return
2. 如果finally中有return，会覆盖try/catch中的return
3. 抛出异常时，先执行finally再抛出

---

### Q15: throw和throws的区别是什么？

**题目类型**：基础概念类

**问题描述**：Java中throw和throws有什么区别？各自的使用场景是什么？

**答案要点**：

**核心区别：**

| 区别 | throw | throws |
|------|-------|--------|
| 作用位置 | 方法内部 | 方法签名 |
| 含义 | 抛出异常对象 | 声明可能抛出的异常 |
| 数量 | 一次抛出一个 | 声明多个可能抛出的异常 |
| 类型 | Throwable对象 | 异常类型 |

**代码示例：**

```java
// throws - 声明可能抛出的异常
public void readFile() throws IOException, SQLException {
    // 方法实现
}

// throw - 抛出具体异常
public void validate(int age) {
    if (age < 0) {
        throw new IllegalArgumentException("年龄不能为负数");
    }
}

// 实际使用
public void process() {
    try {
        readFile();
    } catch (IOException | SQLException e) {  // 多异常捕获
        e.printStackTrace();
    }
}
```

**自定义异常示例：**

```java
public class BusinessException extends RuntimeException {
    private int errorCode;
    
    public BusinessException(String message) {
        super(message);
    }
    
    public BusinessException(int errorCode, String message) {
        super(message);
        this.errorCode = errorCode;
    }
    
    public int getErrorCode() {
        return errorCode;
    }
}
```

---

### Q16: 什么是序列化？Java中如何实现序列化？

**题目类型**：技术原理类

**问题描述**：什么是对象序列化？如何实现Java对象的序列化？

**答案要点**：

**序列化的定义：**
将对象转换为字节流的过程，用于持久化或网络传输。

**实现序列化：**

```java
// 实现Serializable接口
public class User implements Serializable {
    private static final long serialVersionUID = 1L;
    
    private String name;
    private transient int password;  // transient - 不序列化
    
    // 序列化
    public static void serialize(User user) throws Exception {
        ObjectOutputStream oos = new ObjectOutputStream(
            new FileOutputStream("user.ser"));
        oos.writeObject(user);
        oos.close();
    }
    
    // 反序列化
    public static User deserialize() throws Exception {
        ObjectInputStream ois = new ObjectInputStream(
            new FileInputStream("user.ser"));
        User user = (User) ois.readObject();
        ois.close();
        return user;
    }
}
```

**serialVersionUID的作用：**
- 版本控制，确保序列化/反序列化兼容
- 不定义会由编译器自动生成
- 建议手动定义，防止类修改后不兼容

**transient关键字：**
- 标记的字段不参与序列化
- 适用于敏感信息或不需要持久化的数据
- 静态变量也不参与序列化

**注意事项：**
1. 如果父类实现了Serializable，子类自动序列化
2. 如果父类没实现，子类需要单独处理父类字段
3. 使用Externalizable可自定义序列化逻辑

---

### Q17: 什么是内部类？有哪些类型？

**题目类型**：基础概念类

**问题描述**：Java中的内部类有哪些类型？各自的特点是什么？

**答案要点**：

**内部类的四种类型：**

| 类型 | 定义位置 | 特点 |
|------|----------|------|
| 成员内部类 | 类的方法外 | 属于外部类实例 |
| 静态内部类 | 类的方法外 | 属于外部类本身 |
| 局部内部类 | 方法内部 | 作用域在方法内 |
| 匿名内部类 | 表达式内部 | 没有名字的类 |

**代码示例：**

```java
public class Outer {
    private String outerField = "外部";
    
    // 1. 成员内部类
    public class Inner {
        public void method() {
            System.out.println(outerField);  // 可访问外部类成员
        }
    }
    
    // 2. 静态内部类
    public static class StaticInner {
        public void method() {
            // System.out.println(outerField);  // 不能访问外部实例成员
        }
    }
    
    public void test() {
        // 3. 局部内部类
        class LocalInner {
            public void method() {
                System.out.println(outerField);
            }
        }
        
        // 4. 匿名内部类
        Runnable runnable = new Runnable() {
            @Override
            public void run() {
                System.out.println(outerField);
            }
        };
    }
}

// 使用
Outer outer = new Outer();
Outer.Inner inner = outer.new Inner();
Outer.StaticInner staticInner = new Outer.StaticInner();
```

**使用场景：**
- 回调函数：匿名内部类
- 事件监听：成员内部类
- 逻辑封装：静态内部类

---

### Q18: 什么是代码块？有哪些类型？执行顺序是什么？

**题目类型**：基础概念类

**问题描述**：Java中有哪些代码块？它们的执行顺序是什么？

**答案要点**：

**四种代码块：**

| 类型 | 语法 | 执行时机 | 作用 |
|------|------|----------|------|
| 静态代码块 | static {} | 类加载时执行 | 初始化静态资源 |
| 构造代码块 | {} | 每次创建对象执行 | 抽取构造方法公共代码 |
| 构造方法 | 类名() {} | 创建对象时执行 | 初始化实例 |
| 局部代码块 | {} | 作用域内执行 | 控制变量生命周期 |

**执行顺序演示：**

```java
public class ExecutionOrder {
    static {
        System.out.println("1. 静态代码块");
    }
    
    {
        System.out.println("2. 构造代码块");
    }
    
    public ExecutionOrder() {
        System.out.println("3. 构造方法");
    }
    
    public static void main(String[] args) {
        new ExecutionOrder();
        new ExecutionOrder();
    }
}

// 输出：
// 1. 静态代码块
// 2. 构造代码块
// 3. 构造方法
// 2. 构造代码块
// 3. 构造方法
```

**执行顺序总结：**
```
父类静态代码块 → 子类静态代码块
         ↓
父类构造代码块 → 父类构造方法
         ↓
子类构造代码块 → 子类构造方法
```

---

### Q19: this和super关键字的作用是什么？

**题目类型**：基础概念类

**问题描述**：Java中的this和super关键字分别有什么作用？

**答案要点**：

**this关键字：**
指向当前对象，用于区分成员变量和局部变量。

**super关键字：**
指向父类对象，用于调用父类的方法和构造器。

```java
public class Person {
    private String name;
    
    public Person(String name) {
        this.name = name;  // 区分局部变量和成员变量
    }
    
    public void method() {
        System.out.println("Person method");
    }
}

public class Student extends Person {
    private String name;
    
    public Student(String personName, String studentName) {
        super(personName);  // 调用父类构造方法
        this.name = studentName;
    }
    
    public void method() {
        super.method();  // 调用父类方法
        
        System.out.println("Student method");
        System.out.println(super.getClass().getName());  // 父类信息
    }
}
```

**使用场景：**
- this() 调用本类其他构造方法
- super() 调用父类构造方法
- this.成员 访问本类成员
- super.成员 访问父类成员

---

### Q20: 什么是Lambda表达式？它的语法是什么？

**题目类型**：技术原理类

**问题描述**：Java中的Lambda表达式是什么？它的语法和使用场景是什么？

**答案要点**：

**Lambda表达式定义：**
一种简洁的表示可传递匿名函数的方式。

**语法格式：**

```java
// 完整语法
(参数列表) -> { 方法体 }

// 简化过程
// 1. 参数类型可以省略
(a, b) -> { return a + b; }

// 2. 只有一个参数时，括号可以省略
x -> { return x * 2; }

// 3. 方法体只有一行时，{}和return可以省略
x -> x * 2

// 4. 方法引用
String::length
System.out::println
```

**使用示例：**

```java
// 1. 线程
new Thread(() -> System.out.println("Hello")).start();

// 2. 集合排序
List<String> names = Arrays.asList("Tom", "Jerry", "Mike");
names.sort((a, b) -> a.compareTo(b));
// 或使用方法引用
names.sort(String::compareTo);

// 3. 遍历
list.forEach(item -> System.out.println(item));
list.forEach(System.out::println);

// 4. Stream API
List<Integer> numbers = Arrays.asList(1, 2, 3, 4, 5);
List<Integer> result = numbers.stream()
    .filter(n -> n > 2)
    .map(n -> n * 2)
    .collect(Collectors.toList());
```

**函数式接口：**
- 只包含一个抽象方法的接口
- @FunctionalInterface注解标识
- Lambda表达式只能用于函数式接口

```java
@FunctionalInterface
interface Calculator {
    int calculate(int a, int b);
}

// 使用
Calculator add = (a, b) -> a + b;
System.out.println(add.calculate(1, 2));  // 3
```

---

## 第三部分：高级特性（共5题）

### Q21: 什么是Stream API？它有哪些常用操作？

**题目类型**：技术原理类

**问题描述**：Java 8引入的Stream API是什么？它有哪些常用操作？

**答案要点**：

**Stream API定义：**
处理集合数据的函数式编程接口，提供声明式的数据处理能力。

**创建Stream：**

```java
// 从集合创建
List<String> list = Arrays.asList("a", "b", "c");
Stream<String> stream = list.stream();

// 从数组创建
int[] arr = {1, 2, 3};
IntStream stream2 = Arrays.stream(arr);

// 直接创建
Stream<String> stream3 = Stream.of("a", "b", "c");
```

**中间操作：**

| 操作 | 说明 | 示例 |
|------|------|------|
| filter | 过滤 | filter(x -> x > 0) |
| map | 转换 | map(String::toUpperCase) |
| flatMap | 扁平化 | flatMap(List::stream) |
| distinct | 去重 | distinct() |
| sorted | 排序 | sorted((a,b) -> b-a) |
| limit | 限制数量 | limit(10) |
| skip | 跳过 | skip(5) |

**终端操作：**

| 操作 | 说明 | 示例 |
|------|------|------|
| collect | 收集结果 | collect(Collectors.toList()) |
| forEach | 遍历 | forEach(System.out::println) |
| count | 计数 | count() |
| max/min | 最值 | max(Integer::compareTo) |
| reduce | 归约 | reduce(0, Integer::sum) |
| anyMatch | 任意匹配 | anyMatch(x -> x > 0) |
| allMatch | 全部匹配 | allMatch(x -> x > 0) |
| findFirst | 获取首个 | findFirst().orElse(null) |

**示例代码：**

```java
List<Student> students = getStudents();

// 复杂查询示例
List<String> names = students.stream()
    .filter(s -> s.getScore() >= 90)
    .sorted(Comparator.comparing(Student::getScore).reversed())
    .map(Student::getName)
    .distinct()
    .limit(10)
    .collect(Collectors.toList());

// 统计
IntSummaryStatistics stats = students.stream()
    .mapToInt(Student::getScore)
    .summaryStatistics();
System.out.println("平均分: " + stats.getAverage());
```

---

### Q22: 什么是Optional类？如何使用它避免空指针？

**题目类型**：技术原理类

**问题描述**：Java 8的Optional类是什么？如何使用它来避免空指针异常？

**答案要点**：

**Optional的创建：**

```java
// 创建Optional
Optional<String> empty = Optional.empty();
Optional<String> name = Optional.of("Tom");  // 不能传null
Optional<String> nullable = Optional.ofNullable(null);  // 可以传null
```

**常用方法：**

```java
Optional<String> opt = Optional.ofNullable(getName());

// 1. 判断并获取
if (opt.isPresent()) {
    String name = opt.get();
}

// 2. 使用orElse提供默认值
String name = opt.orElse("Unknown");
String name = opt.orElseGet(() -> getDefaultName());  // 延迟计算
String name = opt.orElseThrow(() -> new RuntimeException("No name"));

// 3. map转换
Optional<Integer> length = opt.map(String::length);

// 4. flatMap - 用于返回Optional的方法
Optional<String> result = opt.flatMap(this::findByName);

// 5. ifPresent
opt.ifPresent(name -> System.out.println(name));

// 6. filter过滤
Optional<String> filtered = opt.filter(s -> s.length() > 3);
```

**实战示例：**

```java
// 链式调用避免嵌套判断
String cityName = Optional.ofNullable(user)
    .flatMap(User::getAddress)
    .flatMap(Address::getCity)
    .map(City::getName)
    .orElse("未知城市");

// Stream结合使用
List<String> cities = users.stream()
    .flatMap(u -> Optional.ofNullable(u.getAddress()).stream())
    .map(Address::getCity)
    .collect(Collectors.toList());
```

---

### Q23: 什么是函数式接口？请列举常见的函数式接口。

**题目类型**：技术原理类

**问题描述**：什么是函数式接口？Java标准库中有哪些常用的函数式接口？

**答案要点**：

**函数式接口定义：**
只包含一个抽象方法的接口，可以用Lambda表达式表示。

**Java 8内置函数式接口：**

| 接口 | 方法签名 | 说明 |
|------|----------|------|
| Supplier<T> | T get() | 生产者，无输入，返回T |
| Consumer<T> | void accept(T t) | 消费者，输入T，无返回 |
| Function<T,R> | R apply(T t) | 函数，输入T，返回R |
| Predicate<T> | boolean test(T t) | 断言，输入T，返回boolean |
| BiFunction<T,U,R> | R apply(T t, U u) | 二元函数 |
| BiConsumer<T,U> | void accept(T t, U u) | 二元消费者 |
| UnaryOperator<T> | T apply(T t) | 一元运算 |
| BinaryOperator<T> | T apply(T t1, T t2) | 二元运算 |

**基本类型专用接口：**
- IntSupplier, IntConsumer, IntFunction
- LongSupplier, LongConsumer, LongFunction
- DoubleSupplier, DoubleConsumer, DoubleFunction

**使用示例：**

```java
// Supplier - 延迟计算
Supplier<Date> dateSupplier = Date::new;
Date date = dateSupplier.get();

// Consumer - 消费数据
Consumer<String> print = System.out::println;
print.accept("Hello");

// Function - 转换数据
Function<String, Integer> length = String::length;
int len = length.apply("Hello");

// Predicate - 条件判断
Predicate<Integer> isEven = n -> n % 2 == 0;
boolean result = isEven.test(10);

// 组合使用
Function<String, Integer> parseAndDouble = 
    FunctionBuilder.<String, Integer>identity()
        .andThen(Integer::parseInt)
        .andThen(n -> n * 2);
```

---

### Q24: 什么是方法引用？有哪些类型？

**题目类型**：技术原理类

**问题描述**：Java中的方法引用是什么？有哪些类型？如何使用？

**答案要点**：

**方法引用的四种类型：**

| 类型 | 语法 | 示例 |
|------|------|------|
| 静态方法引用 | Class::staticMethod | String::valueOf |
| 实例方法引用(特定对象) | object::instanceMethod | System.out::println |
| 实例方法引用(任意对象) | Class::instanceMethod | String::toUpperCase |
| 构造方法引用 | Class::new | User::new |

**代码示例：**

```java
List<String> names = Arrays.asList("tom", "jerry", "mike");

// 1. 静态方法引用
Function<String, Integer> parser = Integer::parseInt;
Integer result = parser.apply("123");

// 2. 特定对象的实例方法引用
Consumer<String> printer = System.out::println;
names.forEach(printer);

// 3. 任意对象的实例方法引用
Function<String, String> upper = String::toUpperCase;
List<String> upperNames = names.stream()
    .map(String::toUpperCase)
    .collect(Collectors.toList());

// 4. 构造方法引用
Supplier<ArrayList<String>> listSupplier = ArrayList::new;
List<String> newList = listSupplier.get();

// 带参数的构造方法
Function<String, User> userFactory = User::new;
User user = userFactory.apply("Tom");
```

**与Lambda表达式对比：**

```java
// Lambda表达式
list.forEach(s -> System.out.println(s));

// 方法引用 - 更简洁
list.forEach(System.out::println);

// 构造方法引用
List<String> names = Arrays.asList("Tom", "Jerry");
List<User> users = names.stream()
    .map(User::new)  // 使用User(String name)构造方法
    .collect(Collectors.toList());
```

---

### Q25: 什么是日期时间API？Java 8有哪些新的日期时间类？

**题目类型**：技术原理类

**问题描述**：Java 8引入了哪些新的日期时间API？它们与旧的Date/Calendar有什么区别？

**答案要点**：

**新API核心类：**

| 类 | 说明 | 示例 |
|------|------|------|
| LocalDate | 日期（年-月-日） | 2024-01-15 |
| LocalTime | 时间（时:分:秒） | 14:30:00 |
| LocalDateTime | 日期时间 | 2024-01-15T14:30:00 |
| Instant | 时间戳 | 2024-01-15T06:30:00Z |
| Duration | 时间段 | Duration.ofHours(2) |
| Period | 日期段 | Period.ofDays(5) |
| ZonedDateTime | 带时区的日期时间 | |

**使用示例：**

```java
// 获取当前日期时间
LocalDate today = LocalDate.now();
LocalTime now = LocalTime.now();
LocalDateTime dateTime = LocalDateTime.now();

// 解析和格式化
LocalDate date = LocalDate.parse("2024-01-15");
DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy年MM月dd日");
String formatted = date.format(formatter);

// 日期计算
LocalDate nextWeek = today.plusWeeks(1);
LocalDate lastMonth = today.minusMonths(1);
boolean isBefore = date.isBefore(anotherDate);

// 日期时间解析
Instant instant = Instant.now();
long timestamp = instant.toEpochMilli();

// Duration计算
LocalTime start = LocalTime.of(9, 0);
LocalTime end = LocalTime.of(17, 30);
Duration duration = Duration.between(start, end);
long hours = duration.toHours();

// Zone时区处理
ZonedDateTime tokyoTime = ZonedDateTime.now(ZoneId.of("Asia/Tokyo"));
```

**与旧API对比：**

```java
// 旧API - 线程不安全
Date date = new Date();
SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd");

// 新API - 线程安全，不可变
LocalDate localDate = LocalDate.now();
localDate.format(DateTimeFormatter.ofPattern("yyyy-MM-dd"));
```

---

## 附录：知识点总结

**Java基础核心知识点：**

| 类别 | 关键知识点 |
|------|----------|
| 基础语法 | 数据类型、运算符、控制流程 |
| 面向对象 | 封装、继承、多态、抽象类、接口 |
| 核心概念 | 异常、泛型、注解、反射 |
| 高级特性 | Lambda、Stream、Optional |
| API使用 | 字符串处理、日期时间、集合操作 |

**推荐阅读：**
1. 《Effective Java》- Joshua Bloch
2. 《Java核心技术卷I》
3. Oracle官方Java教程

---

*本文档共计25道Java基础面试题，涵盖Java核心语法和基础概念。*
