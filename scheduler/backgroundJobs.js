const cron = require('node-cron');
const moment = require('moment-timezone');
const { sendCartReminderOnce } = require('../services/orderService');
const { getAllCarts, getPendingOrders, removePendingOrder } = require('../stateHandlers/redisState');
const { sendTextMessage } = require('../services/whatsappService');

function startJobs() {
  cron.schedule('*/10 * * * *', sendCartReminders, { timezone: 'Asia/Kolkata' });
  cron.schedule('* * * * *', checkPendingOrders, { timezone: 'Asia/Kolkata' });
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

module.exports = { startJobs };
