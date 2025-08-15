const { sendTextMessage } = require('../services/whatsappService');
const { getUserState, setUserState } = require('../stateHandlers/redisState');

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
  const state = await getUserState(to);
  state.location = { latitude, longitude };
  await setUserState(to, state);
  await sendTextMessage(to, '📍 Location received.');
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
