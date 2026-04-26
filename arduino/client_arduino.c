#include "WiFiS3.h"
#include "settings.h"

const char* ssid = ARDUINO_WIFI_SSID;
const char* pass = ARDUINO_WIFI_PASSWORD;
const char* server_ip = ARDUINO_SERVER_IP;
const int port = ARDUINO_SERVER_PORT;

const int MR_Ctrl = ARDUINO_MR_CTRL_PIN;
const int MR_PWM = ARDUINO_MR_PWM_PIN;
const int ML_Ctrl = ARDUINO_ML_CTRL_PIN;
const int ML_PWM = ARDUINO_ML_PWM_PIN;

const int TRIG_PIN = ARDUINO_TRIG_PIN;
const int ECHO_PIN = ARDUINO_ECHO_PIN;
const int DISTANZA_EMERGENZA = ARDUINO_EMERGENCY_DISTANCE_CM;

WiFiClient client;
String inputString = "";
String ultimaAzione = "STOP";

void executeCommand(String data);
int getDistance();
void eseguiManovraEvasiva();
void moveForward(int s);
void moveBack(int s);
void turnLeft(int s);
void turnRight(int s);
void moveForwardLeft(int s);
void moveForwardRight(int s);
void moveBackLeft(int s);
void moveBackRight(int s);
void stopCar();

void setup() {
  Serial.begin(ARDUINO_SERIAL_BAUD);

  pinMode(MR_Ctrl, OUTPUT);
  pinMode(MR_PWM, OUTPUT);
  pinMode(ML_Ctrl, OUTPUT);
  pinMode(ML_PWM, OUTPUT);

  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  Serial.println("Avvio Rover... Connessione al WiFi: " + String(ssid));
  WiFi.begin(ssid, pass);
  while (WiFi.status() != WL_CONNECTED) {
    delay(ARDUINO_WIFI_RETRY_DELAY_MS);
    Serial.print(".");
  }
  Serial.println("\nWiFi Connesso! IP Rover: " + WiFi.localIP().toString());
}

void loop() {
  int distanzaOstacolo = getDistance();

  if (distanzaOstacolo > 0 && distanzaOstacolo < DISTANZA_EMERGENZA && ultimaAzione != "S") {
    eseguiManovraEvasiva();
  }

  if (!client.connected()) {
    stopCar();
    if (client.connect(server_ip, port)) {
      Serial.println("Connesso al Server Python!");
    } else {
      delay(ARDUINO_SERVER_RETRY_DELAY_MS);
      return;
    }
  }

  bool commandReady = false;
  String latestCommand = "";

  while (client.available()) {
    char inChar = (char)client.read();
    if (inChar == '\n') {
      latestCommand = inputString;
      inputString = "";
      commandReady = true;
    } else {
      inputString += inChar;
      if (inputString.length() > ARDUINO_COMMAND_BUFFER_SIZE) {
        inputString = "";
      }
    }
  }

  if (commandReady) {
    executeCommand(latestCommand);
  }
}

int getDistance() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  long duration = pulseIn(ECHO_PIN, HIGH, 30000);
  if (duration == 0) {
    return 999;
  }
  return duration * 0.034 / 2;
}

void eseguiManovraEvasiva() {
  Serial.println("OSTACOLO RILEVATO! Freno di emergenza!");
  stopCar();
  delay(ARDUINO_EMERGENCY_STOP_DELAY_MS);

  if (ultimaAzione == "W" || ultimaAzione == "WD" || ultimaAzione == "WA") {
    moveBack(ARDUINO_EMERGENCY_PWM);
    delay(ARDUINO_BACK_STRAIGHT_MS);
  } else if (ultimaAzione == "A") {
    moveBackRight(ARDUINO_EMERGENCY_PWM);
    delay(ARDUINO_BACK_TURN_MS);
  } else if (ultimaAzione == "D") {
    moveBackLeft(ARDUINO_EMERGENCY_PWM);
    delay(ARDUINO_BACK_TURN_MS);
  }

  stopCar();
  ultimaAzione = "STOP";

  while (client.available()) {
    client.read();
  }
}

void executeCommand(String data) {
  data.trim();
  int firstComma = data.indexOf(',');
  int secondComma = data.indexOf(',', firstComma + 1);

  if (firstComma != -1 && secondComma != -1) {
    String cmd = data.substring(0, firstComma);
    float v_mult = data.substring(firstComma + 1, secondComma).toFloat();

    int speed = (int)(v_mult * 255);
    if (speed < 0) {
      speed = 0;
    }
    if (speed > 255) {
      speed = 255;
    }

    ultimaAzione = cmd;

    if (cmd == "W") {
      moveForward(speed);
    } else if (cmd == "S") {
      moveBack(speed);
    } else if (cmd == "A") {
      turnLeft(speed);
    } else if (cmd == "D") {
      turnRight(speed);
    } else if (cmd == "WA") {
      moveForwardLeft(speed);
    } else if (cmd == "WD") {
      moveForwardRight(speed);
    } else {
      stopCar();
    }
  }
}

void moveForward(int s) {
  digitalWrite(ML_Ctrl, LOW);
  analogWrite(ML_PWM, s);
  digitalWrite(MR_Ctrl, HIGH);
  analogWrite(MR_PWM, s);
}

void moveBack(int s) {
  digitalWrite(ML_Ctrl, HIGH);
  analogWrite(ML_PWM, s);
  digitalWrite(MR_Ctrl, LOW);
  analogWrite(MR_PWM, s);
}

void turnLeft(int s) {
  digitalWrite(ML_Ctrl, HIGH);
  analogWrite(ML_PWM, s);
  digitalWrite(MR_Ctrl, HIGH);
  analogWrite(MR_PWM, s);
}

void turnRight(int s) {
  digitalWrite(ML_Ctrl, LOW);
  analogWrite(ML_PWM, s);
  digitalWrite(MR_Ctrl, LOW);
  analogWrite(MR_PWM, s);
}

void moveForwardLeft(int s) {
  digitalWrite(ML_Ctrl, LOW);
  analogWrite(ML_PWM, s / 3);
  digitalWrite(MR_Ctrl, HIGH);
  analogWrite(MR_PWM, s);
}

void moveForwardRight(int s) {
  digitalWrite(ML_Ctrl, LOW);
  analogWrite(ML_PWM, s);
  digitalWrite(MR_Ctrl, HIGH);
  analogWrite(MR_PWM, s / 3);
}

void moveBackLeft(int s) {
  digitalWrite(ML_Ctrl, HIGH);
  analogWrite(ML_PWM, s / 3);
  digitalWrite(MR_Ctrl, LOW);
  analogWrite(MR_PWM, s);
}

void moveBackRight(int s) {
  digitalWrite(ML_Ctrl, HIGH);
  analogWrite(ML_PWM, s);
  digitalWrite(MR_Ctrl, LOW);
  analogWrite(MR_PWM, s / 3);
}

void stopCar() {
  analogWrite(ML_PWM, 0);
  analogWrite(MR_PWM, 0);
}
