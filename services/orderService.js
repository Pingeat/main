const fs = require('fs');
const path = require('path');
const csv = require('fast-csv');
const moment = require('moment-timezone');
const { sendTextMessage, sendTemplate, sendKitchenBranchAlertTemplate } = require('./whatsappService');
const { getUserCart, setUserCart, deleteUserCart, addPendingOrder } = require('../stateHandlers/redisState');
const { ORDERS_CSV, ADMIN_NUMBERS } = require('../config/settings');

function logOrder(order) {
  const filePath = path.resolve(ORDERS_CSV || 'orders.csv');
  const exists = fs.existsSync(filePath);
  const ws = fs.createWriteStream(filePath, { flags: 'a' });
  csv.write([order], { headers: !exists }).pipe(ws);
}

async function updateOrderStatus(orderId, status) {
  const filePath = path.resolve(ORDERS_CSV || 'orders.csv');
  if (!fs.existsSync(filePath)) return;
  const lines = fs.readFileSync(filePath, 'utf8').split(/\r?\n/);
  if (!lines.length) return;
  const headers = lines[0].split(',');
  const idIdx = headers.indexOf('Order ID');
  const statusIdx = headers.indexOf('Status');
  if (idIdx === -1 || statusIdx === -1) return;
  for (let i = 1; i < lines.length; i++) {
    if (!lines[i]) continue;
    const cols = lines[i].split(',');
    if (cols[idIdx] === orderId) {
      cols[statusIdx] = status;
      lines[i] = cols.join(',');
      break;
    }
  }
  fs.writeFileSync(filePath, lines.join('\n'));
}

async function sendCartReminderOnce(phone) {
  const cart = await getUserCart(phone);
  if (!cart.summary || cart.reminder_sent) return;
  await sendTextMessage(phone, `🛒 Just a reminder! You still have items in your cart.\n${cart.summary}`);
  await sendTemplate(phone, 'delivery_takeaway');
  cart.reminder_sent = true;
  await setUserCart(phone, cart);
}

async function confirmOrder(to, paymentMode, orderId, paid = false) {
  const cart = await getUserCart(to);
  const orderData = {
    customer: to,
    order_id: orderId,
    payment_mode: paymentMode,
    summary: cart.summary || '',
    total: cart.total || 0,
    status: 'Pending',
    created_at: moment.utc().toISOString()
  };
  logOrder({
    'Order ID': orderId,
    'Customer Number': to,
    'Order Time': moment().tz('Asia/Kolkata').format('YYYY-MM-DD HH:mm:ss'),
    'Payment Mode': paymentMode,
    'Paid': paid,
    'Status': 'Pending'
  });
  await addPendingOrder(orderId, orderData);
  await deleteUserCart(to);
  await sendTextMessage(to, `✅ Order confirmed. Your order ID is ${orderId}.`);
  const orderTime = moment().tz('Asia/Kolkata').format('YYYY-MM-DD HH:mm:ss');
  for (const admin of ADMIN_NUMBERS) {
    await sendKitchenBranchAlertTemplate(
      admin,
      paymentMode,
      orderId,
      to,
      orderTime,
      cart.summary || '',
      cart.total || 0,
      cart.branch || 'N/A',
      cart.address || 'N/A',
      cart.location_url || 'N/A'
    );
  }
}

module.exports = { logOrder, sendCartReminderOnce, confirmOrder, updateOrderStatus };
