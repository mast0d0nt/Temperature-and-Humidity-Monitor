// REVISION №5

// DIFFERENT ENTITIES DECLARATION (PINS, PARAMETERS RANGES, STRUCTURES ETC.)

#include <DHT.h>

const int SENSOR_PIN = 2;
const int BUZZER_PIN = 3;

const int LED_PIN_TEMPERATURE_HIGH = 4;
const int LED_PIN_TEMPERATURE_LOW = 5;
const int LED_PIN_HUMIDITY_HIGH = 6;
const int LED_PIN_HUMIDITY_LOW = 7;

const float MIN_TEMPERATURE_OK = 18.0;
const float MAX_TEMPERATURE_OK = 35.0;
const float MIN_HUMIDITY_OK = 45.0;
const float MAX_HUMIDITY_OK = 75.0;

const uint8_t SENSOR_TYPE = DHT11;

const unsigned long SENSOR_INTERVAL = 2000;
const unsigned long BUZZER_INTERVAL = 250;

unsigned long lastSensorRead = 0;
unsigned long lastBuzzerToggle = 0;

bool buzzerOn = false;
bool previousAlertActive = false;
bool alertActive = false;

struct SensorData {
  float temperature;
  float humidity;
  bool valid;
};

enum ParameterState {
  BELOW_NORMAL,
  NORMAL,
  ABOVE_NORMAL
};

struct AlertState {
  ParameterState temperature;
  ParameterState humidity;
};

enum LogLevel {
  INFO,
  WARNING,
  ERROR
};

enum WarningCode {
  TEMPERATURE_ABOVE,
  TEMPERATURE_BELOW,
  HUMIDITY_ABOVE,
  HUMIDITY_BELOW,
  NO_WARNING
};

enum ErrorCode {
  DHT_READ_FAILED,
  UNKNOWN_ERROR
};

struct SerialMessage {
  LogLevel level;
  SensorData data;
  AlertState alerts;
  ErrorCode errorCode;
  WarningCode warningCode;
};

DHT dht(SENSOR_PIN, SENSOR_TYPE);

AlertState currentAlerts = { NORMAL, NORMAL };


// MAIN FUNCTIONS

void setup() {
  pinMode(BUZZER_PIN, OUTPUT);

  pinMode(LED_PIN_TEMPERATURE_HIGH, OUTPUT);
  pinMode(LED_PIN_TEMPERATURE_LOW, OUTPUT);
  pinMode(LED_PIN_HUMIDITY_HIGH, OUTPUT);
  pinMode(LED_PIN_HUMIDITY_LOW, OUTPUT);

  Serial.begin(9600);
  dht.begin();

  sendThresholds();

  digitalWrite(BUZZER_PIN, LOW);
  turnOffLEDs();
}


void loop() {
  unsigned long currentTime = millis();

  if (currentTime - lastSensorRead >= SENSOR_INTERVAL) {
    lastSensorRead = currentTime;

    SensorData data = handleSensor();

    if (data.valid) {
      currentAlerts = evaluateParameters(data);

      alertActive =
        currentAlerts.temperature != NORMAL || currentAlerts.humidity != NORMAL;

      SerialMessage message = {
        alertActive ? WARNING : INFO,
        data,
        currentAlerts,
        UNKNOWN_ERROR,
        getWarningCode(currentAlerts)
      };

      handleSerialMonitor(message);

    } else {
      SerialMessage message = {
        ERROR,
        { 0.0, 0.0, false },
        { NORMAL, NORMAL },
        DHT_READ_FAILED,
        NO_WARNING
      };

      handleSerialMonitor(message);
    }
  }

  updateBuzzer(alertActive);
  updateLEDs(currentAlerts);
}


// CUSTOM FUNCTIONS-UTILITIES

SensorData handleSensor() {
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();

  if (isnan(temperature) || isnan(humidity)) {
    return { 0.0, 0.0, false };
  }

  return { temperature, humidity, true };
}

void handleSerialMonitor(const SerialMessage& message) {
  switch (message.level) {
    case INFO:
      Serial.print("INFO|");
      Serial.print(message.data.temperature, 2);
      Serial.print("|");
      Serial.println(message.data.humidity, 2);
      break;

    case WARNING:
      {
        uint8_t abnormalCount = 0;

        if (message.alerts.temperature != NORMAL) {
          abnormalCount++;
        }

        if (message.alerts.humidity != NORMAL) {
          abnormalCount++;
        }

        Serial.print("WARNING|");
        Serial.print(message.data.temperature, 2);
        Serial.print("|");
        Serial.print(message.data.humidity, 2);
        Serial.print("|");
        Serial.print(abnormalCount);
        Serial.print("|");
        Serial.println(getWarningCodeString(message.warningCode));
        break;
      }

    case ERROR:
      Serial.print("ERROR|");
      Serial.println(getErrorCodeString(message.errorCode));
      break;
  }
}


WarningCode getWarningCode(const AlertState& alerts) {
  if (alerts.temperature != NORMAL && alerts.humidity != NORMAL) {
    return NO_WARNING;
  }

  if (alerts.temperature == ABOVE_NORMAL) {
    return TEMPERATURE_ABOVE;
  }

  if (alerts.temperature == BELOW_NORMAL) {
    return TEMPERATURE_BELOW;
  }

  if (alerts.humidity == ABOVE_NORMAL) {
    return HUMIDITY_ABOVE;
  }

  if (alerts.humidity == BELOW_NORMAL) {
    return HUMIDITY_BELOW;
  }

  return NO_WARNING;
}


ParameterState checkParameter(float value, float minValue, float maxValue) {
  if (value < minValue) {
    return BELOW_NORMAL;
  }

  if (value > maxValue) {
    return ABOVE_NORMAL;
  }

  return NORMAL;
}


AlertState evaluateParameters(const SensorData& data) {
  AlertState state;

  state.temperature = checkParameter(
    data.temperature,
    MIN_TEMPERATURE_OK,
    MAX_TEMPERATURE_OK);

  state.humidity = checkParameter(
    data.humidity,
    MIN_HUMIDITY_OK,
    MAX_HUMIDITY_OK);

  return state;
}


void updateLEDs(const AlertState& state) {
  digitalWrite(
    LED_PIN_TEMPERATURE_LOW,
    buzzerOn && state.temperature == BELOW_NORMAL ? HIGH : LOW);

  digitalWrite(
    LED_PIN_TEMPERATURE_HIGH,
    buzzerOn && state.temperature == ABOVE_NORMAL ? HIGH : LOW);

  digitalWrite(
    LED_PIN_HUMIDITY_LOW,
    buzzerOn && state.humidity == BELOW_NORMAL ? HIGH : LOW);

  digitalWrite(
    LED_PIN_HUMIDITY_HIGH,
    buzzerOn && state.humidity == ABOVE_NORMAL ? HIGH : LOW);
}


void turnOffLEDs() {
  digitalWrite(LED_PIN_TEMPERATURE_HIGH, LOW);
  digitalWrite(LED_PIN_TEMPERATURE_LOW, LOW);
  digitalWrite(LED_PIN_HUMIDITY_HIGH, LOW);
  digitalWrite(LED_PIN_HUMIDITY_LOW, LOW);
}


void updateBuzzer(bool shouldAlert) {
  unsigned long currentTime = millis();

  if (shouldAlert && !previousAlertActive) {
    buzzerOn = false;
    lastBuzzerToggle = currentTime;
  }

  if (!shouldAlert) {
    buzzerOn = false;

    digitalWrite(BUZZER_PIN, LOW);

    previousAlertActive = false;
    return;
  }

  if (currentTime - lastBuzzerToggle >= BUZZER_INTERVAL) {
    lastBuzzerToggle = currentTime;
    buzzerOn = !buzzerOn;
  }

  digitalWrite(
    BUZZER_PIN,
    buzzerOn ? HIGH : LOW);

  previousAlertActive = true;
}


const char* getWarningCodeString(WarningCode warningCode) {
  switch (warningCode) {
    case TEMPERATURE_ABOVE:
      return "TEMPERATURE_ABOVE";

    case TEMPERATURE_BELOW:
      return "TEMPERATURE_BELOW";

    case HUMIDITY_ABOVE:
      return "HUMIDITY_ABOVE";

    case HUMIDITY_BELOW:
      return "HUMIDITY_BELOW";

    default:
      return "";
  }
}


const char* getErrorCodeString(ErrorCode errorCode) {
  switch (errorCode) {
    case DHT_READ_FAILED:
      return "DHT_READ_FAILED";

    default:
      return "UNKNOWN_ERROR";
  }
}


void sendThresholds() {
  Serial.print("CONFIG|");
  Serial.print(MIN_TEMPERATURE_OK);
  Serial.print("|");
  Serial.print(MAX_TEMPERATURE_OK);
  Serial.print("|");
  Serial.print(MIN_HUMIDITY_OK);
  Serial.print("|");
  Serial.println(MAX_HUMIDITY_OK);
}