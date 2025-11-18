# 1. JDK 이미지 사용
FROM eclipse-temurin:17-jdk

# 2. 빌드된 JAR 파일 복사
ARG JAR_FILE=build/libs/*.jar
COPY ${JAR_FILE} app.jar

# 3. 컨테이너 실행 시 JAR 실행
ENTRYPOINT ["java", "-jar", "/app.jar"]
