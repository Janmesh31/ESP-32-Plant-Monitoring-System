#define BLYNK_TEMPLATE_ID "TMPL30xsuVis"
#define BLYNK_TEMPLATE_NAME "ESP 32 Plant Monitor"
#define BLYNK_AUTH_TOKEN "PaupTiIM-UqYBxjKzv0HoLIqQN6IMhIp"

#include <WiFi.h>
#include <WiFiClient.h>
#include <BlynkSimpleEsp32.h>
#include <DHT.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <AceButton.h>
using namespace ace_button;

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

#define SensorPin       34
#define DHTPin          14
#define RelayPin        35
#define wifiLed         2
#define RelayButtonPin  32
#define ModeSwitchPin   33
#define BuzzerPin       26
#define ModeLed         15

#define DHTTYPE DHT11
DHT dht(DHTPin, DHTTYPE);

#define VPIN_MoistPer    V1
#define VPIN_TEMPERATURE V2
#define VPIN_HUMIDITY    V3
#define VPIN_MODE_SWITCH V4
#define VPIN_RELAY       V5

int wetSoilVal = 930;
int drySoilVal = 3000;
int moistPerLow = 20;
int moistPerHigh = 80;
int sensorVal, moisturePercentage, temperature1, humidity1;
bool toggleRelay = LOW, prevMode = true;
String currMode = "A";

char auth[] = BLYNK_AUTH_TOKEN;
char ssid[] = "Redmi 9a";
char pass[] = "12345678";

ButtonConfig config1, config2;
AceButton button1(&config1), button2(&config2);

void button1Handler(AceButton*, uint8_t, uint8_t);
void button2Handler(AceButton*, uint8_t, uint8_t);

BlynkTimer timer;

void checkBlynkStatus() {
  digitalWrite(wifiLed, Blynk.connected() ? HIGH : LOW);
}

BLYNK_CONNECTED() {
  Blynk.syncVirtual(VPIN_MoistPer, VPIN_RELAY, VPIN_TEMPERATURE, VPIN_HUMIDITY);
  Blynk.virtualWrite(VPIN_MODE_SWITCH, prevMode);
}

BLYNK_WRITE(VPIN_RELAY) {
  if (!prevMode) {
    toggleRelay = param.asInt();
    digitalWrite(RelayPin, toggleRelay);
  } else {
    Blynk.virtualWrite(VPIN_RELAY, toggleRelay);
  }
}

BLYNK_WRITE(VPIN_MODE_SWITCH) {
  prevMode = param.asInt();
  currMode = prevMode ? "A" : "M";
  digitalWrite(ModeLed, prevMode);
  controlBuzzer(500);
  if (!prevMode && toggleRelay) {
    digitalWrite(RelayPin, LOW);
    toggleRelay = LOW;
    Blynk.virtualWrite(VPIN_RELAY, toggleRelay);
  }
}

void controlBuzzer(int duration) {
  digitalWrite(BuzzerPin, HIGH);
  delay(duration);
  digitalWrite(BuzzerPin, LOW);
}

void getMoisture() {
  sensorVal = analogRead(SensorPin);
  moisturePercentage = map(sensorVal, drySoilVal, wetSoilVal, 0, 100);
}

void getWeather() {
  float h = dht.readHumidity(), t = dht.readTemperature();
  if (!isnan(h) && !isnan(t)) {
    humidity1 = int(h);
    temperature1 = int(t);
  }
}

void sendSensor() {
  getMoisture();
  getWeather();
  Blynk.virtualWrite(VPIN_MoistPer, moisturePercentage);
  Blynk.virtualWrite(VPIN_TEMPERATURE, temperature1);
  Blynk.virtualWrite(VPIN_HUMIDITY, humidity1);
  updateDisplay();
}

void controlPump() {
  if (prevMode) {
    if (moisturePercentage < moistPerLow && !toggleRelay) {
      controlBuzzer(500);
      digitalWrite(RelayPin, HIGH);
      toggleRelay = HIGH;
      Blynk.virtualWrite(VPIN_RELAY, toggleRelay);
    }
    if (moisturePercentage > moistPerHigh && toggleRelay) {
      controlBuzzer(500);
      digitalWrite(RelayPin, LOW);
      toggleRelay = LOW;
      Blynk.virtualWrite(VPIN_RELAY, toggleRelay);
    }
  } else {
    button1.check();
  }
}

void updateDisplay() {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(WHITE);
  display.setCursor(0, 0);
  display.print("Temp: "); display.print(temperature1); display.println(" C");
  display.print("Humidity: "); display.print(humidity1); display.println(" %");
  display.print("Moisture: "); display.print(moisturePercentage); display.println(" %");
  display.print("Mode: "); display.println(currMode);
  display.print("Pump: "); display.println(toggleRelay ? "ON" : "OFF");
  display.display();
}

void setup() {
  Serial.begin(115200);
  pinMode(RelayPin, OUTPUT);
  pinMode(wifiLed, OUTPUT);
  pinMode(ModeLed, OUTPUT);
  pinMode(BuzzerPin, OUTPUT);
  pinMode(RelayButtonPin, INPUT_PULLUP);
  pinMode(ModeSwitchPin, INPUT_PULLUP);

  digitalWrite(RelayPin, LOW);
  digitalWrite(wifiLed, LOW);
  digitalWrite(ModeLed, LOW);
  digitalWrite(BuzzerPin, LOW);

  dht.begin();
  Wire.begin();
  display.begin(SSD1306_SWITCHCAPVCC, 0x3C);
  display.clearDisplay();
  display.display();

  config1.setEventHandler(button1Handler);
  config2.setEventHandler(button2Handler);
  button1.init(RelayButtonPin);
  button2.init(ModeSwitchPin);

  WiFi.begin(ssid, pass);
  timer.setInterval(2000L, checkBlynkStatus);
  timer.setInterval(3000L, sendSensor);
  Blynk.config(auth);
  controlBuzzer(1000);
  digitalWrite(ModeLed, prevMode);
}

void loop() {
  Blynk.run();
  timer.run();
  button2.check();
  controlPump();
}

void button1Handler(AceButton* button, uint8_t eventType, uint8_t buttonState) {
  if (eventType == AceButton::kEventReleased) {
    digitalWrite(RelayPin, !digitalRead(RelayPin));
    toggleRelay = digitalRead(RelayPin);
    Blynk.virtualWrite(VPIN_RELAY, toggleRelay);
  }
}

void button2Handler(AceButton* button, uint8_t eventType, uint8_t buttonState) {
  if (eventType == AceButton::kEventReleased) {
    prevMode = !prevMode;
    Blynk.virtualWrite(VPIN_MODE_SWITCH, prevMode);
    digitalWrite(ModeLed, prevMode);
    controlBuzzer(500);
  }
}