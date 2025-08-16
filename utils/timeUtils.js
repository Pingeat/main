const fs = require('fs');
const path = require('path');
const moment = require('moment-timezone');
const { OPEN_TIME, CLOSE_TIME, OFF_HOUR_USERS_CSV } = require('../config/settings');

function isOperationalHours() {
  const hour = moment().tz('Asia/Kolkata').hour();
  return hour >= OPEN_TIME && hour < CLOSE_TIME;
}

async function storeOffHourUser(phone) {
  const filePath = path.resolve(OFF_HOUR_USERS_CSV || 'offhour_users.csv');
  const record = `${phone},${moment().tz('Asia/Kolkata').toISOString()}\n`;
  try {
    await fs.promises.access(filePath);
    await fs.promises.appendFile(filePath, record);
  } catch (err) {
    const header = 'phone,timestamp\n';
    await fs.promises.writeFile(filePath, header + record);
  }
}

module.exports = { isOperationalHours, storeOffHourUser };
