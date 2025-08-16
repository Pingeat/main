const fs = require('fs');
const path = require('path');
const csv = require('fast-csv');
const moment = require('moment-timezone');
const products = require('../data/products.json');
const logger = require('../utils/logger');
const {
  sendTextMessage,
  sendTemplate,
  sendPayOnlineTemplate,
  sendKitchenBranchAlertTemplate
} = require('./whatsappService');
const { generatePaymentLink } = require('./paymentService');
const { getUserCart, setUserCart, deleteUserCart, addPendingOrder } = require('../stateHandlers/redisState');
const { ORDERS_CSV, ADMIN_NUMBERS } = require('../config/settings');

async function logOrder(order) {
  try {
    const filePath = path.resolve(ORDERS_CSV || 'orders.csv');
    const exists = fs.existsSync(filePath);
    await new Promise((resolve, reject) => {
      const ws = fs.createWriteStream(filePath, { flags: 'a' });
      csv
        .write([order], { headers: !exists })
        .pipe(ws)
        .on('finish', resolve)
        .on('error', reject);
    });
  } catch (err) {
    logger.error('Failed to log order', { error: err.message });
  }
}

function generateOrderId() {
  return `ORD-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8).toUpperCase()}`;
}

async function buildCart(phone, items = {}) {
  try {
    const summaryLines = [];
    let total = 0;
    for (const [id, qty] of Object.entries(items)) {
      const product = products[id];
      if (!product) continue;
      const itemTotal = product.price * qty;
      total += itemTotal;
      summaryLines.push(`${product.name} x${qty} = ₹${itemTotal}`);
    }
    const cart = { items, summary: summaryLines.join('\n'), total };
    await setUserCart(phone, cart);
    return cart;
  } catch (err) {
    logger.error('Failed to build cart', { error: err.message });
    throw err;
  }
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
  try {
    const cart = await getUserCart(phone);
    if (!cart.summary || cart.reminder_sent) return;
    await sendTextMessage(
      phone,
      `🛒 Just a reminder! You still have items in your cart.\n${cart.summary}`
    );
    await sendTemplate(phone, 'delivery_takeaway');
    const orderId = cart.order_id || `ORD-${Date.now()}`;
    const finalTotal = cart.final_total || cart.total || 0;
    const link = await generatePaymentLink(phone, finalTotal, orderId);
    if (link) {
      await sendPayOnlineTemplate(phone, link);
    }
    cart.reminder_sent = true;
    await setUserCart(phone, cart);
  } catch (err) {
    logger.error('Failed to send cart reminder', { error: err.message });
  }
}

async function confirmOrder(to, paymentMode, orderId = generateOrderId(), paid = false) {
  try {
    const cart = await getUserCart(to);
    const finalTotal = cart.final_total || cart.total || 0;
    const orderData = {
      customer: to,
      order_id: orderId,
      payment_mode: paymentMode,
      summary: cart.summary || '',
      total: finalTotal,
      status: 'Pending',
      created_at: moment.utc().toISOString()
    };
    await logOrder({
      'Order ID': orderId,
      'Customer Number': to,
      'Order Time': moment().tz('Asia/Kolkata').format('YYYY-MM-DD HH:mm:ss'),
      'Payment Mode': paymentMode,
      'Paid': paid,
      'Summary': orderData.summary,
      'Total': orderData.total
    });
    await addPendingOrder(orderId, orderData);
    if (!paid) {
      const link = await generatePaymentLink(to, finalTotal, orderId);
      if (link) {
        await sendPayOnlineTemplate(to, link);
      }
    }
    await deleteUserCart(to);
    await sendTemplate(to, 'order_confirmation', [
      {
        type: 'body',
        parameters: [{ type: 'text', text: orderId }]
      }
    ]);
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
        finalTotal,
        cart.branch || 'N/A',
        cart.address || 'N/A',
        cart.location_url || 'N/A'
      );
    }
    return orderId;
  } catch (err) {
    logger.error('Failed to confirm order', { error: err.message });
    throw err;
  }
}

module.exports = {
  logOrder,
  sendCartReminderOnce,
  confirmOrder,
  buildCart,
  generateOrderId,
  updateOrderStatus
};
