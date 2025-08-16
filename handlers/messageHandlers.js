const { sendTextMessage, sendTemplate } = require('../services/whatsappService');
const { getUserState, setUserState } = require('../stateHandlers/redisState');
const { BRANCH_STATUS, BRANCH_DISCOUNTS, BRANCH_BLOCKED_USERS } = require('../config/settings');
const { findClosestBranch } = require('../utils/locationUtils');

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
        await handleGreeting(sender);
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
  await sendTextMessage(to, '🛒 Order received.');
}

async function handleInteractive(to, interactive) {
  await sendTextMessage(to, '🔘 Option selected.');
}

module.exports = {
  handleIncomingMessage,
  handleGreeting,
  handleLocation,
  handleOrder,
  handleInteractive
};
