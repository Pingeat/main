const cron = require('node-cron');
const moment = require('moment-timezone');
const fs = require('fs');
const path = require('path');
const { sendCartReminderOnce } = require('../services/orderService');
const { getAllCarts, getPendingOrders, removePendingOrder } = require('../stateHandlers/redisState');
const { sendTextMessage } = require('../services/whatsappService');
const { OPEN_TIME, OFF_HOUR_USERS_CSV } = require('../config/settings');

function startJobs() {
  cron.schedule('*/10 * * * *', sendCartReminders, { timezone: 'Asia/Kolkata' });
  cron.schedule('* * * * *', checkPendingOrders, { timezone: 'Asia/Kolkata' });
  cron.schedule(`0 ${OPEN_TIME} * * *`, notifyOpenUsers, { timezone: 'Asia/Kolkata' });
}

async function sendCartReminders() {
  const carts = await getAllCarts();
  const now = moment.tz('Asia/Kolkata');
  for (const [phone, cart] of Object.entries(carts)) {
    if (!cart.last_interaction_time || cart.reminder_sent) continue;
    const last = moment.tz(cart.last_interaction_time, 'YYYY-MM-DD HH:mm:ss', 'Asia/Kolkata');
    if (now.diff(last, 'minutes') >= 5) {
      await sendCartReminderOnce(phone);
    }
  }
}

async function checkPendingOrders() {
  const orders = await getPendingOrders();
  const now = moment.utc();
  for (const [orderId, order] of Object.entries(orders)) {
    if (order.status !== 'Pending') continue;
    const created = moment.utc(order.created_at);
    if (now.diff(created, 'minutes') >= 3) {
      await sendTextMessage(order.customer, `❌ Your order ${orderId} has been cancelled due to inactivity.`);
      await removePendingOrder(orderId);
    }
  }
}

async function notifyOpenUsers() {
  const filePath = path.resolve(OFF_HOUR_USERS_CSV || 'offhour_users.csv');
  if (!fs.existsSync(filePath)) return;
  const content = fs.readFileSync(filePath, 'utf8').trim();
  if (!content) return;
  const lines = content.split('\n');
  if (lines.length <= 1) return;
  const header = lines[0];
  const now = moment.tz('Asia/Kolkata');
  const remaining = [header];
  for (let i = 1; i < lines.length; i++) {
    const [phone, timestamp] = lines[i].split(',');
    const ts = moment(timestamp);
    if (now.diff(ts, 'days') >= 30) {
      continue; // prune old entries
    }
    await sendTextMessage(phone, "🌞 We're open now! Feel free to place your order.");
    // remove after notifying
  }
  fs.writeFileSync(filePath, remaining.join('\n') + '\n');
}

module.exports = { startJobs };
