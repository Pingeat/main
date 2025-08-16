const fs = require('fs');
const path = require('path');
const csv = require('fast-csv');
const { sendTextMessage, sendTemplate } = require('../services/whatsappService');
const { sendMarketingPromo, sendCatalogSet } = require('../services/marketingService');
const {
  getUserState,
  setUserState,
  getPendingOrder,
  addPendingOrder,
  removePendingOrder,
} = require('../stateHandlers/redisState');
// const { BRANCH_STATUS, BRANCH_BLOCKED_USERS } = require('../config/branchConfig');
const { updateOrderStatus } = require('../services/orderService');
const { findClosestBranch } = require('../utils/locationUtils');
const { isOperationalHours, storeOffHourUser } = require('../utils/timeUtils');
const {
  ADMIN_NUMBERS,
  BRANCH_STATUS,
  BRANCH_DISCOUNTS,
  BRANCH_BLOCKED_USERS,
  USER_LOG_CSV
} = require('../config/settings');

async function handleIncomingMessage(data) {
  for (const entry of data.entry || []) {
    for (const change of entry.changes || []) {
      const value = change.value || {};
      const messages = value.messages || [];
      if (!messages.length) continue;

      const msg = messages[0];
      const sender = msg.from.replace(/^\+/, '');
      const type = msg.type;

      if (type === 'text') {
        const text = msg.text?.body?.trim() || '';

        if (text.toLowerCase().startsWith('message customer')) {
          await handleMarketingMessage(sender, text);
        } else if (isAdmin(sender)) {
          await handleAdminCommand(sender, text);
        } else {
          const match = text.match(/^(open|close)\s+(\w+)/i);
          if (match && ADMIN_NUMBERS.includes(sender)) {
            const action = match[1].toLowerCase();
            const branch = match[2];
            if (action === 'open') {
              BRANCH_STATUS[branch] = true;
              const blocked = BRANCH_BLOCKED_USERS[branch] || [];
              for (const user of blocked) {
                await sendTextMessage(user, `Branch ${branch} is now open.`);
              }
              BRANCH_BLOCKED_USERS[branch] = [];
              await sendTextMessage(sender, `Branch ${branch} opened.`);
            } else {
              BRANCH_STATUS[branch] = false;
              await sendTextMessage(sender, `Branch ${branch} closed.`);
            }
          } else {
            await handleGreeting(sender);
          }
        }
      } else if (type === 'location') {
        const { latitude, longitude } = msg.location;
        await handleLocation(sender, latitude, longitude);
      } else if (type === 'order') {
        const items = msg.order?.product_items || [];
        await handleOrder(sender, items);
      } else if (type === 'interactive') {
        await handleInteractive(sender, msg.interactive);
      }
    }
  }
}


function isAdmin(phone) {
  return ADMIN_NUMBERS.includes(phone);
}

async function handleAdminCommand(sender, text) {
  const branchMatch = text.match(/^(open|close)\s+(\w+)/i);
  if (branchMatch) {
    const action = branchMatch[1].toLowerCase();
    const branch = branchMatch[2];
    if (action === 'open') {
      BRANCH_STATUS[branch] = true;
      const blocked = BRANCH_BLOCKED_USERS[branch] || new Set();
      for (const user of blocked) {
        await sendTextMessage(user, `Branch ${branch} is now open.`);
      }
      BRANCH_BLOCKED_USERS[branch] = new Set();
      await sendTextMessage(sender, `Branch ${branch} opened.`);
    } else {
      BRANCH_STATUS[branch] = false;
      await sendTextMessage(sender, `Branch ${branch} closed.`);
    }
    return;
  }

  const lower = text.toLowerCase();
  const statusMatch = lower.match(/\b(ready|dispatched|ontheway|on the way|delivered)\b/);
  if (!statusMatch) return;
  const statusKey = statusMatch[1];
  const orderId = text.replace(new RegExp(statusMatch[0], 'i'), '').trim().toUpperCase();
  if (!orderId) return;

  let statusMessage;
  let statusValue;
  switch (statusKey) {
    case 'ready':
      statusMessage = 'Your order is ready.';
      statusValue = 'Ready';
      break;
    case 'dispatched':
    case 'ontheway':
    case 'on the way':
      statusMessage = 'Your order is on the way.';
      statusValue = 'On The Way';
      break;
    case 'delivered':
      statusMessage = 'Your order has been delivered.';
      statusValue = 'Delivered';
      break;
    default:
      return;
  }

  await updateOrderStatus(orderId, statusValue);
  const order = await getPendingOrder(orderId);
  if (order) {
    await sendTextMessage(order.customer, `📦 ${statusMessage}`);
    order.status = statusMessage;
    await addPendingOrder(orderId, order);
    if (statusKey === 'delivered') {
      setTimeout(() => sendTemplate(order.customer, 'feedback_2'), 5 * 60 * 1000);
      await removePendingOrder(orderId);
    }
  }
}

async function handleGreeting(to) {
  await sendTextMessage(to, '👋 Hello! How can we help you today?');
  await setUserState(to, { step: 'greeted' });
}

async function handleLocation(to, latitude, longitude) {
  const branchInfo = findClosestBranch(latitude, longitude);
  if (!branchInfo) {
    await sendTextMessage(to, '🚫 Sorry, we do not serve your location yet.');
    return;
  }

  const branchKey = branchInfo.name.toLowerCase();
  if (!BRANCH_STATUS[branchKey]) {
    if (!BRANCH_BLOCKED_USERS[branchKey]) {
      BRANCH_BLOCKED_USERS[branchKey] = new Set();
    }
    BRANCH_BLOCKED_USERS[branchKey].add(to);
    await sendTextMessage(to, `🚫 ${branchInfo.name} branch is currently unavailable.`);
    return;
  }

  const state = await getUserState(to);
  state.branch = branchKey;
  state.location = { latitude, longitude };
  state.discount = BRANCH_DISCOUNTS[branchKey] || 0;
  await setUserState(to, state);

  await sendTextMessage(to, `📍 Closest branch: ${branchInfo.name}\n${branchInfo.map_link}`);
  await sendTemplate(to, 'delivery_takeaway');
}

async function handleOrder(to, items) {
  if (!isOperationalHours()) {
    await sendTextMessage(
      to,
      "⏰ We are currently closed. We'll notify you when we're open."
    );
    await storeOffHourUser(to);
    return;
  }
  await sendTextMessage(to, '🛒 Order received.');
}

async function handleInteractive(to, interactive) {
  await sendTextMessage(to, '🔘 Option selected.');
}

async function handleMarketingMessage(sender, text) {
  const match = text.match(/to=(.*?)\s+message_text="(.*?)"(?:\s+item_set=(\S+))?/);
  if (!match) {
    await sendTextMessage(sender, '❗ Invalid format. Use:\nmessage customer to=... message_text="your message here"');
    return;
  }

  const toValue = match[1].trim();
  const messageText = match[2].trim();
  const itemSet = (match[3] || '').replace(/"/g, '').trim();

  let recipients = [];
  if (['log', 'all'].includes(toValue)) {
    recipients = await readNumbersFromLog();
    if (!recipients.length) {
      await sendTextMessage(sender, '❌ No active customers found in log');
      return;
    }
    await sendTextMessage(sender, `📢 Sending promo to ${recipients.length} customers from log...`);
  } else {
    recipients = toValue.split(',').map(n => n.trim()).filter(Boolean);
    if (!recipients.length) {
      await sendTextMessage(sender, '❌ No valid phone numbers provided');
      return;
    }
  }

  let successful = 0;
  for (const num of recipients) {
    await sendMarketingPromo(num, messageText);
    if (itemSet && itemSet.toLowerCase() !== 'none') {
      await sendCatalogSet(num, itemSet);
    }
    successful += 1;
  }

  await sendTextMessage(sender, `✅ Sent marketing message to ${successful}/${recipients.length} customers`);
}

function readNumbersFromLog() {
  return new Promise((resolve) => {
    const numbers = new Set();
    const filePath = path.resolve(USER_LOG_CSV || 'user_activity_log.csv');
    if (!fs.existsSync(filePath)) return resolve([]);
    fs.createReadStream(filePath)
      .pipe(csv.parse({ headers: true }))
      .on('data', row => {
        const num = (row['Customer Number'] || '').replace(/[^0-9]/g, '');
        if (num.length >= 10) numbers.add(num);
      })
      .on('end', () => resolve(Array.from(numbers)))
      .on('error', () => resolve([]));
  });
}

module.exports = {
  handleIncomingMessage,
  handleGreeting,
  handleLocation,
  handleOrder,
  handleInteractive
};
