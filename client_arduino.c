#include "WiFiS3.h"
#include "arduino_c_compat.h"
#include "settings.h"

const char* ssid = ARDUINO_WIFI_SSID;
const char* pass = ARDUINO_WIFI_PASSWORD;
const char* server_ip = ARDUINO_SERVER_IP;
const int port = ARDUINO_SERVER_PORT;

WiFiClient client;

char commandBuffer[ARDUINO_COMMAND_BUFFER_SIZE];
int commandIndex = 0;

void connettiAlServer();
void applyCommand(const char* cmd);
void moveForward();
void moveBack();
void turnLeft();
void turnRight();
void stopCar();

// --- PIN MOTORI (Keyestudio 4WD) ---
const int MR_Ctrl = ARDUINO_MR_CTRL_PIN;
const int MR_PWM = ARDUINO_MR_PWM_PIN;
const int ML_Ctrl = ARDUINO_ML_CTRL_PIN;
const int ML_PWM = ARDUINO_ML_PWM_PIN;

void setup() {
  pinMode(MR_Ctrl, OUTPUT); pinMode(MR_PWM, OUTPUT);
  pinMode(ML_Ctrl, OUTPUT); pinMode(ML_PWM, OUTPUT);
  Serial.begin(ARDUINO_SERIAL_BAUD);

  Serial.print("Connessione WiFi...");
  WiFi.begin(ssid, pass);
  while (WiFi.status() != WL_CONNECTED) { delay(ARDUINO_WIFI_RETRY_DELAY_MS); Serial.print("."); }
  
  connettiAlServer();
}

void connettiAlServer() {
  while (!client.connect(server_ip, port)) {
    Serial.println("Tentativo connessione server...");
    delay(ARDUINO_SERVER_RETRY_DELAY_MS);
  }
  Serial.println("Connesso al server!");
}

void loop() {
  if (!client.connected()) {
    stopCar();
    commandIndex = 0;
    connettiAlServer();
  }

  if (client.available()) {
    char c = client.read();

    if (c == '\r') {
      return;
    }

    if (c == '\n') {
      commandBuffer[commandIndex] = '\0';
      if (commandIndex > 0) {
        applyCommand(commandBuffer);
      }
      commandIndex = 0;
      return;
    }

    if (commandIndex < (int)sizeof(commandBuffer) - 1) {
      commandBuffer[commandIndex++] = c;
    }
  }
}

void applyCommand(const char* cmd) {
  Serial.print("Comando: "); Serial.println(cmd);

  if (cstr_equals(cmd, "W")) moveForward();
  else if (cstr_equals(cmd, "S")) moveBack();
  else if (cstr_equals(cmd, "A")) turnLeft();
  else if (cstr_equals(cmd, "D")) turnRight();
  else if (cstr_equals(cmd, "STOP") || cstr_equals(cmd, "X")) stopCar();
}

// --- LOGICA MOTORI ---
void moveForward() {
  digitalWrite(ML_Ctrl, LOW);  analogWrite(ML_PWM, ARDUINO_DRIVE_PWM);
  digitalWrite(MR_Ctrl, LOW);  analogWrite(MR_PWM, ARDUINO_DRIVE_PWM);
}

void moveBack() {
  digitalWrite(ML_Ctrl, HIGH); analogWrite(ML_PWM, ARDUINO_DRIVE_PWM);
  digitalWrite(MR_Ctrl, HIGH); analogWrite(MR_PWM, ARDUINO_DRIVE_PWM);
}

void turnLeft() {
  digitalWrite(ML_Ctrl, HIGH); analogWrite(ML_PWM, ARDUINO_DRIVE_PWM);
  digitalWrite(MR_Ctrl, LOW);  analogWrite(MR_PWM, ARDUINO_DRIVE_PWM);
}

void turnRight() {
  digitalWrite(ML_Ctrl, LOW);  analogWrite(ML_PWM, ARDUINO_DRIVE_PWM);
  digitalWrite(MR_Ctrl, HIGH); analogWrite(MR_PWM, ARDUINO_DRIVE_PWM);
}

void stopCar() {
  analogWrite(ML_PWM, 0); analogWrite(MR_PWM, 0);
}
