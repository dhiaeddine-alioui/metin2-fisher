#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEServer.h>
#include "BLE2902.h"
#include "BLEHIDDevice.h"
#include "HIDTypes.h"
#include "HIDKeyboardTypes.h"
#include <driver/adc.h>
#include "sdkconfig.h"

#include "BleConnectionStatus.h"
#include "BleMouse16.h"

#if defined(CONFIG_ARDUHAL_ESP_LOG)
  #include "esp32-hal-log.h"
  #define LOG_TAG ""
#else
  #include "esp_log.h"
  static const char* LOG_TAG = "BLEDevice";
#endif

#include <Arduino.h>

static const uint8_t _hidReportDescriptor[] = {
  USAGE_PAGE(1),       0x01, // USAGE_PAGE (Generic Desktop)
  USAGE(1),            0x02, // USAGE (Mouse)
  COLLECTION(1),       0x01, // COLLECTION (Application)
  USAGE(1),            0x01, //   USAGE (Pointer)
  COLLECTION(1),       0x00, //   COLLECTION (Physical)
  // ------------------------------------------------- Buttons (Left, Right, Middle, Back, Forward)
  USAGE_PAGE(1),       0x09, //     USAGE_PAGE (Button)
  USAGE_MINIMUM(1),    0x01, //     USAGE_MINIMUM (Button 1)
  USAGE_MAXIMUM(1),    0x05, //     USAGE_MAXIMUM (Button 5)
  LOGICAL_MINIMUM(1),  0x00, //     LOGICAL_MINIMUM (0)
  LOGICAL_MAXIMUM(1),  0x01, //     LOGICAL_MAXIMUM (1)
  REPORT_SIZE(1),      0x01, //     REPORT_SIZE (1)
  REPORT_COUNT(1),     0x05, //     REPORT_COUNT (5)
  HIDINPUT(1),         0x02, //     INPUT (Data, Variable, Absolute) ;5 button bits
  // ------------------------------------------------- Padding
  REPORT_SIZE(1),      0x03, //     REPORT_SIZE (3)
  REPORT_COUNT(1),     0x01, //     REPORT_COUNT (1)
  HIDINPUT(1),         0x03, //     INPUT (Constant, Variable, Absolute) ;3 bit padding
  // ------------------------------------------------- X/Y position, Wheel
  USAGE_PAGE(1),       0x01, //     USAGE_PAGE (Generic Desktop)
  USAGE(1),            0x30, //     USAGE (X)
  USAGE(1),            0x31, //     USAGE (Y)
  USAGE(1),            0x38, //     USAGE (Wheel)
  LOGICAL_MINIMUM(2),  0x01, 0x80, //     Logical Minimum (-32767)
  LOGICAL_MAXIMUM(2),  0xFF, 0x7F, //     Logical Maximum (32767)
  REPORT_SIZE(1),      0x10, //     REPORT_SIZE (16)
  REPORT_COUNT(1),     0x03, //     REPORT_COUNT (3)
  HIDINPUT(1),         0x06, //     INPUT (Data, Variable, Relative) ;3 bytes (X,Y,Wheel)
  // ------------------------------------------------- Horizontal wheel
  USAGE_PAGE(1),       0x0c, //     USAGE PAGE (Consumer Devices)
  USAGE(2),      0x38, 0x02, //     USAGE (AC Pan)
  LOGICAL_MINIMUM(1),  0x81, //     LOGICAL_MINIMUM (-127)
  LOGICAL_MAXIMUM(1),  0x7f, //     LOGICAL_MAXIMUM (127)
  REPORT_SIZE(1),      0x08, //     REPORT_SIZE (8)
  REPORT_COUNT(1),     0x01, //     REPORT_COUNT (1)
  HIDINPUT(1),         0x06, //     INPUT (Data, Var, Rel)
  END_COLLECTION(0),         //   END_COLLECTION
  END_COLLECTION(0)          // END_COLLECTION
};


BleMouse16::BleMouse16(std::string deviceName, std::string deviceManufacturer, uint8_t batteryLevel) : 
    _buttons(0),
    hid(0)
{
  this->deviceName = deviceName;
  this->deviceManufacturer = deviceManufacturer;
  this->batteryLevel = batteryLevel;
  this->connectionStatus = new BleConnectionStatus();
}

void BleMouse16::begin(void)
{
  xTaskCreate(this->taskServer, "server", 20000, (void *)this, 5, NULL);
}

void BleMouse16::end(void)
{
}

void BleMouse16::click(uint8_t b)
{
  _buttons = b;
  move(0,0);
  _buttons = 0;
  move(0,0);
}

void BleMouse16::move(int16_t x, int16_t y)
{
  if (this->isConnected())
  {
    uint8_t m[8]; // Increase array size to accommodate 16-bit X and Y values
    m[0] = _buttons;
    m[1] = static_cast<uint8_t>(x & 0xFF);       // Extract lower byte of X (LSB)
    m[2] = static_cast<uint8_t>((x >> 8) & 0xFF); // Extract upper byte of X (MSB)
    m[3] = static_cast<uint8_t>(y & 0xFF);       // Extract lower byte of Y (LSB)
    m[4] = static_cast<uint8_t>((y >> 8) & 0xFF); // Extract upper byte of Y (MSB)
	m[5] = 0x00;
	m[6] = 0x00;
	m[7] = 0x00;
    this->inputMouse->setValue(m, 8); // Update array size
    this->inputMouse->notify();
  }
}

void BleMouse16::moveClickMove(int16_t x, int16_t y, int16_t de, int16_t click_duration,  uint8_t b){
    uint8_t m[8]; // Increase array size to accommodate 16-bit X and Y values
    m[0] = 0x00;
    m[1] = static_cast<uint8_t>(x & 0xFF);       // Extract lower byte of X (LSB)
    m[2] = static_cast<uint8_t>((x >> 8) & 0xFF); // Extract upper byte of X (MSB)
    m[3] = static_cast<uint8_t>(y & 0xFF);       // Extract lower byte of Y (LSB)
    m[4] = static_cast<uint8_t>((y >> 8) & 0xFF); // Extract upper byte of Y (MSB)
	m[5] = 0x00;
	m[6] = 0x00;
	m[7] = 0x00;
    this->inputMouse->setValue(m, 8); // Update array size
    this->inputMouse->notify();
	delay(de);
	m[0] = b;
    m[1] = 0x00;
    m[2] = 0x00;
    m[3] = 0x00;
    m[4] = 0x00;
    this->inputMouse->setValue(m, 8); // Update array size
    this->inputMouse->notify();
	delay(click_duration);
    m[0] = 0x00;
    this->inputMouse->setValue(m, 8); // Update array size
    this->inputMouse->notify();
	delay(10);
	int16_t _x = -x;
	int16_t _y = -y;
    m[1] = static_cast<uint8_t>(_x & 0xFF);       // Extract lower byte of X (LSB)
    m[2] = static_cast<uint8_t>((_x >> 8) & 0xFF); // Extract upper byte of X (MSB)
    m[3] = static_cast<uint8_t>(_y & 0xFF);       // Extract lower byte of Y (LSB)
    m[4] = static_cast<uint8_t>((_y >> 8) & 0xFF); // Extract upper byte of Y (MSB)
    this->inputMouse->setValue(m, 8); // Update array size
    this->inputMouse->notify();
}


void BleMouse16::buttons(uint8_t b)
{
  if (b != _buttons)
  {
    _buttons = b;
    move(0,0);
  }
}

void BleMouse16::press(uint8_t b)
{
  buttons(_buttons | b);
}

void BleMouse16::release(uint8_t b)
{
  buttons(_buttons & ~b);
}

bool BleMouse16::isPressed(uint8_t b)
{
  if ((b & _buttons) > 0)
    return true;
  return false;
}

bool BleMouse16::isConnected(void) {
  return this->connectionStatus->connected;
}

void BleMouse16::setBatteryLevel(uint8_t level) {
  this->batteryLevel = level;
  if (hid != 0)
      this->hid->setBatteryLevel(this->batteryLevel);
}

void BleMouse16::taskServer(void* pvParameter) {
  BleMouse16* bleMouseInstance = (BleMouse16 *) pvParameter; //static_cast<BleMouse *>(pvParameter);
  BLEDevice::init(bleMouseInstance->deviceName);
  BLEServer *pServer = BLEDevice::createServer();
  pServer->setCallbacks(bleMouseInstance->connectionStatus);

  bleMouseInstance->hid = new BLEHIDDevice(pServer);
  bleMouseInstance->inputMouse = bleMouseInstance->hid->inputReport(0); // <-- input REPORTID from report map
  bleMouseInstance->connectionStatus->inputMouse = bleMouseInstance->inputMouse;

  bleMouseInstance->hid->manufacturer()->setValue(bleMouseInstance->deviceManufacturer);

  bleMouseInstance->hid->pnp(0x02, 0xe502, 0xa111, 0x0210);
  bleMouseInstance->hid->hidInfo(0x00,0x02);

  BLESecurity *pSecurity = new BLESecurity();

  pSecurity->setAuthenticationMode(ESP_LE_AUTH_BOND);

  bleMouseInstance->hid->reportMap((uint8_t*)_hidReportDescriptor, sizeof(_hidReportDescriptor));
  bleMouseInstance->hid->startServices();

  bleMouseInstance->onStarted(pServer);

  BLEAdvertising *pAdvertising = pServer->getAdvertising();
  pAdvertising->setAppearance(HID_MOUSE);
  pAdvertising->addServiceUUID(bleMouseInstance->hid->hidService()->getUUID());
  pAdvertising->start();
  bleMouseInstance->hid->setBatteryLevel(bleMouseInstance->batteryLevel);

  ESP_LOGD(LOG_TAG, "Advertising started!");
  vTaskDelay(portMAX_DELAY); //delay(portMAX_DELAY);
}
